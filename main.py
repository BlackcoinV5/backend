import os
import asyncio
import logging
import hashlib
import hmac
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from telegram import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import models
import schemas
from database import init_db, SessionLocal

# === Chargement des variables d'environnement ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not FRONTEND_URL or not WEBHOOK_URL:
    raise ValueError("⚠️ Vérifie .env : TELEGRAM_BOT_TOKEN, FRONTEND_URL, WEBHOOK_URL manquants")

# === Logs ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Initialisation de l'app FastAPI ===
app = FastAPI()

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sécuriser plus tard avec l'URL du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dépendance DB ===
async def get_db():
    async with SessionLocal() as session:
        yield session

# === Authentification Telegram (vérification du hash) ===
def verify_telegram_auth(data: dict) -> bool:
    auth_date = int(data.get("auth_date", "0"))
    if (auth_date + 86400) < int(time.time()):
        return False

    received_hash = data.get("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted((k, v) for k, v in data.items() if k != "hash"))

    secret_key = hashlib.sha256(TOKEN.encode()).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(received_hash, computed_hash)

# === Bot Telegram ===
application = Application.builder().token(TOKEN).build()

# === Commandes du bot ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Ouvrir l'app", web_app=WebAppInfo(url=FRONTEND_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bienvenue sur BlackCoin 🎉 !", reply_markup=reply_markup)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as db:
        user_id = update.effective_user.id
        result = await db.execute(select(models.User).filter(models.User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            await update.message.reply_text(f"💰 Points: {user.points}\n🔐 Wallet: {user.wallet}")
        else:
            await update.message.reply_text("❌ Utilisateur introuvable.")

async def send_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        return await update.message.reply_text("❗ Format: /send_points <ID> <montant>")

    try:
        recipient_id = int(args[0])
        amount = int(args[1])
    except ValueError:
        return await update.message.reply_text("❌ Entrez un ID et un montant valides.")

    async with SessionLocal() as db:
        sender_result = await db.execute(select(models.User).filter(models.User.id == update.effective_user.id))
        sender = sender_result.scalar_one_or_none()

        recipient_result = await db.execute(select(models.User).filter(models.User.id == recipient_id))
        recipient = recipient_result.scalar_one_or_none()

        if not sender or not recipient or sender.points < amount:
            return await update.message.reply_text("⚠️ Erreur : utilisateur ou solde invalide.")

        sender.points -= amount
        recipient.points += amount

        db.add(models.Transaction(user_id=sender.id, amount=amount, type="debit"))
        db.add(models.Transaction(user_id=recipient.id, amount=amount, type="credit"))
        await db.commit()

        await update.message.reply_text(f"✅ {amount} points envoyés à {recipient.username or recipient_id}")

# === Gestion des erreurs du bot ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Bot Error: {context.error}")
    if update.message:
        await update.message.reply_text("⚠️ Erreur inattendue.")

# === Ajout des handlers ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("balance", balance))
application.add_handler(CommandHandler("send_points", send_points))
application.add_error_handler(error_handler)

# === Lancement du bot avec webhook ===
async def start_bot():
    await application.initialize()
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook Telegram prêt : {WEBHOOK_URL}")
    await application.start()

# === FastAPI - Événement au démarrage ===
@app.on_event("startup")
async def on_startup():
    await init_db()
    asyncio.create_task(start_bot())

# === Endpoint Webhook Telegram ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# === Authentification Telegram depuis le frontend ===
@app.post("/auth/telegram", response_model=schemas.UserBase)
async def auth_telegram(user_data: dict, db: AsyncSession = Depends(get_db)):
    print("📩 Données reçues :", user_data)

    if not verify_telegram_auth(user_data):
        raise HTTPException(status_code=403, detail="Authentification Telegram invalide")

    user_id = user_data["id"]
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = models.User(
            id=user_id,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            username=user_data.get("username", ""),
            photo_url=user_data.get("photo_url", ""),
            points=0,
            wallet=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user

# === Liste des utilisateurs ===
@app.get("/user-data", response_model=list[schemas.UserBase])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User))
    return result.scalars().all()

# === Page d'accueil ===
@app.get("/")
def root():
    return {"message": "✅ Backend BlackCoin opérationnel"}
