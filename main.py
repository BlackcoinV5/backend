# Fichier : main.py
import os
import asyncio
import logging
import hashlib
import hmac
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from telegram import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import models
import schemas
from database import get_db, async_session
from utils import send_telegram_message

# === Chargement des variables d'environnement ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

if not TOKEN or not FRONTEND_URL or not WEBHOOK_URL:
    raise ValueError("⚠️ Configuration .env manquante. Vérifiez TELEGRAM_BOT_TOKEN, FRONTEND_URL et WEBHOOK_URL.")

# === Logger ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('blackcoin.log')]
)
logger = logging.getLogger(__name__)

# === Initialisation FastAPI ===
app = FastAPI(
    title="BlackCoin API",
    description="Backend pour l'application BlackCoin",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Authentification OAuth2 simplifiée ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# === Telegram Bot ===
application = Application.builder().token(TOKEN).build()

# === Vérification Telegram Auth ===
def verify_telegram_auth(data: dict) -> bool:
    try:
        data_copy = data.copy()
        received_hash = data_copy.pop('hash')

        data_check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(data_copy.items())
        )
        secret_key = hashlib.sha256(TOKEN.encode()).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        auth_date = datetime.fromtimestamp(int(data_copy.get('auth_date', 0)))
        return computed_hash == received_hash and (datetime.now() - auth_date) < timedelta(days=1)
    except Exception as e:
        logger.error(f"Erreur vérification auth Telegram: {e}")
        return False

# === Commande /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        async with async_session() as session:
            result = await session.execute(select(models.User).where(models.User.id == user.id))
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                new_user = models.User(
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name or "",
                    username=user.username or "",
                    points=100,
                    wallet=0,
                    level=1
                )
                session.add(new_user)
                await session.commit()

                await send_telegram_message(
                    user.id,
                    "🎉 Bienvenue sur BlackCoin ! Vous avez reçu 100 points de bienvenue !"
                )

        keyboard = [[
            InlineKeyboardButton("🚀 Lancer l'application", web_app=WebAppInfo(url=FRONTEND_URL))
        ]]

        await update.message.reply_text(
            "Bienvenue sur BlackCoin !\n\n"
            "Utilisez notre application pour gagner des points, "
            "monter en niveau et échanger avec vos amis.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Erreur /start: {e}")
        await update.message.reply_text("⚠️ Une erreur est survenue. Veuillez réessayer plus tard.")

# === Authentification via frontend ===
@app.post("/auth/telegram", response_model=schemas.UserResponse)
async def telegram_auth(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        data = await request.json()
        if not verify_telegram_auth(data):
            raise HTTPException(status_code=403, detail="Authentification Telegram invalide")

        user_id = int(data['id'])
        result = await db.execute(select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            user = models.User(
                id=user_id,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                username=data.get('username', ''),
                photo_url=data.get('photo_url', ''),
                points=100,
                wallet=0,
                level=1
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return {
            "user": user,
            "token": str(user.id)  # À remplacer plus tard par un vrai JWT
        }
    except Exception as e:
        logger.error(f"Erreur authentification Telegram: {e}")
        raise HTTPException(500, detail="Erreur serveur")

# === Récupération des données utilisateur ===
@app.get("/user-data/{user_id}", response_model=schemas.UserResponse)
async def get_user_data(user_id: int, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    if int(token) != user_id:
        raise HTTPException(403, detail="Accès non autorisé")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, detail="Utilisateur non trouvé")

    return {"user": user}

# === Mise à jour utilisateur ===
@app.post("/update-user", response_model=schemas.UserResponse)
async def update_user(update_data: schemas.UserUpdate, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        user_id = int(token)
        result = await db.execute(select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(404, detail="Utilisateur non trouvé")

        if update_data.points is not None:
            user.points = update_data.points
        if update_data.wallet is not None:
            user.wallet = update_data.wallet
        if update_data.level is not None:
            user.level = update_data.level

        await db.commit()
        await db.refresh(user)
        return {"user": user}
    except Exception as e:
        await db.rollback()
        logger.error(f"Erreur mise à jour utilisateur: {e}")
        raise HTTPException(500, detail="Erreur serveur")

# === Répondre aux messages texte ===
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# === Ajout des handlers ===
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# === Initialisation base de données ===
async def init_db():
    async with async_session() as session:
        try:
            await session.execute(select(1))
            logger.info("✅ Connexion à la base de données réussie.")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion à la base de données: {e}")
            raise

        from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    web_app_url = "https://blackcoin-v5-frontend.vercel.app"
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton(
            text="Lancer BLACKCOIN",
            web_app=WebAppInfo(url=web_app_url)
        )
    )

    await message.answer("Bienvenue sur BLACKCOIN !", reply_markup=markup)


# === Startup & Shutdown ===
@app.on_event("startup")
async def startup_event():
    await init_db()
    await application.initialize()
    await application.start()
    # await application.updater.start_polling()  # À utiliser en local si pas de webhook

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
