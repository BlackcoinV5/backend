import os
import asyncio
import logging
import hashlib
import hmac
import time
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

from database import init_db, SessionLocal
import models

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN:
    raise ValueError("⚠️ TELEGRAM_BOT_TOKEN n'est pas défini dans .env")

# Initialisation de FastAPI
app = FastAPI()

# CORS Middleware (à restreindre en production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du bot Telegram
application = Application.builder().token(TOKEN).build()

# Dépendance DB (asynchrone)
async def get_db():
    async with SessionLocal() as session:
        yield session

# Vérification d'authentification Telegram
def verify_telegram_auth(data):
    check_hash = data.pop("hash", None)
    sorted_data = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
    secret_key = hashlib.sha256(TOKEN.encode()).digest()
    expected_hash = hmac.new(secret_key, sorted_data.encode(), hashlib.sha256).hexdigest()
    return check_hash == expected_hash and (int(data["auth_date"]) + 86400) > int(time.time())

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    auth_link = f"{FRONTEND_URL}/auth/telegram?user_id={user_id}"
    await update.message.reply_text(
        f"Bienvenue sur BlackCoin 🎉 !\n"
        f"🔗 Connecte-toi ici : {auth_link}\n\n"
        "Utilise /balance pour voir ton solde."
    )

# Commande /balance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as db:
        user_id = update.effective_user.id
        result = await db.execute(select(models.User).filter(models.User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            await update.message.reply_text(
                f"💰 Solde: {user.points} pts\n🔹 Wallet: {user.wallet} pts"
            )
        else:
            await update.message.reply_text("⚠️ Utilisateur non trouvé.")

# Commande /send_points
async def send_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as db:
        user_id = update.effective_user.id
        args = context.args

        if len(args) < 2:
            await update.message.reply_text("Usage: /send_points <ID> <montant>")
            return

        try:
            recipient_id = int(args[0])
            amount = int(args[1])

            sender_result = await db.execute(select(models.User).filter(models.User.id == user_id))
            sender = sender_result.scalar_one_or_none()

            recipient_result = await db.execute(select(models.User).filter(models.User.id == recipient_id))
            recipient = recipient_result.scalar_one_or_none()

            if sender and recipient and sender.points >= amount:
                sender.points -= amount
                recipient.points += amount

                db.add(models.Transaction(user_id=user_id, amount=amount, type="debit"))
                db.add(models.Transaction(user_id=recipient_id, amount=amount, type="credit"))
                await db.commit()

                await update.message.reply_text(f"✅ {amount} pts envoyés à {recipient_id} !")
            else:
                await update.message.reply_text("⚠ Solde insuffisant ou utilisateur inexistant.")
        except ValueError:
            await update.message.reply_text("⚠ Erreur : Veuillez entrer un ID valide et un montant en nombre.")

# Gestion des erreurs du bot
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erreur bot : {context.error}")
    await update.message.reply_text("⚠ Une erreur est survenue. Merci de réessayer plus tard.")

# Ajout des handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("balance", balance))
application.add_handler(CommandHandler("send_points", send_points))
application.add_error_handler(error_handler)

# Démarrage du bot
async def start_bot():
    await application.initialize()
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook activé sur {WEBHOOK_URL}")
    await application.start()

# Événement de démarrage de FastAPI
@app.on_event("startup")
async def startup_event():
    await init_db()
    asyncio.create_task(start_bot())

# Webhook Telegram
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erreur Webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Authentification Telegram
@app.post("/auth/telegram")
async def auth_telegram(user_data: dict, db: AsyncSession = Depends(get_db)):
    if not verify_telegram_auth(user_data):
        raise HTTPException(status_code=403, detail="Données Telegram invalides")

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

    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "photo_url": user.photo_url,
        "points": user.points,
        "wallet": user.wallet,
    }

# Récupérer tous les utilisateurs
@app.get("/user-data")
async def get_user_data(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User))
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "photo_url": user.photo_url,
            "points": user.points,
            "wallet": user.wallet,
        }
        for user in users
    ]

# Page d'accueil
@app.get("/")
def home():
    return {"message": "Bot connecté à BlackCoin"}