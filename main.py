import os
import asyncio
import logging
import hashlib
import hmac
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sql_update

from telegram import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError
from telegram import Update
from telegram.ext import ContextTypes

import models
import schemas
# Nouvel import
from database import get_db, async_session
from utils import send_telegram_message

# === Configuration initiale ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

if not TOKEN or not FRONTEND_URL or not WEBHOOK_URL:
    raise ValueError("⚠️ Configuration .env manquante. Vérifiez TELEGRAM_BOT_TOKEN, FRONTEND_URL et WEBHOOK_URL.")

# === Configuration des logs ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('blackcoin.log')
    ]
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

# === Configuration CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Initialisation du bot Telegram ===
application = Application.builder().token(TOKEN).build()

# === Schéma d'authentification ===
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# === Helper functions ===
async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> models.User:
    try:
        user_id = int(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return user

# === Vérification authentification Telegram ===
def verify_telegram_auth(data: dict) -> bool:
    try:
        data_copy = data.copy()
        received_hash = data_copy.pop('hash')
        
        # Tri des données par ordre alphabétique
        data_check_string = "\n".join(
    f"{key}={value}" 
    for key, value in sorted(data_copy.items())
)  
        # Calcul du hash secret
        secret_key = hashlib.sha256(TOKEN.encode()).digest()
        computed_hash = hmac.new(
            secret_key, 
            data_check_string.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        # Vérification du hash et de la date
        auth_date = datetime.fromtimestamp(int(data_copy.get('auth_date', 0)))
        return (
            computed_hash == received_hash and
            (datetime.now() - auth_date) < timedelta(days=1)
        )
    except Exception as e:
        logger.error(f"Erreur vérification auth Telegram: {e}")
        return False

# === Commandes Telegram ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        async with async_session() as session:
            # Vérifier si l'utilisateur existe déjà
            result = await db.execute(
                select(models.User).where(models.User.id == user.id))
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Créer un nouvel utilisateur
                new_user = models.User(
                    id=user.id,
                    first_name=user.first_name,
                    last_name=user.last_name or "",
                    username=user.username or "",
                    points=100,  # Bonus de bienvenue
                    wallet=0,
                    level=1
                )
                db.add(new_user)
                await db.commit()
                
                await send_telegram_message(
                    user.id,
                    "🎉 Bienvenue sur BlackCoin ! Vous avez reçu 100 points de bienvenue !"
                )

        # Créer le bouton pour lancer l'application
        keyboard = [[
            InlineKeyboardButton(
                "🚀 Lancer l'application", 
                web_app=WebAppInfo(url=FRONTEND_URL))
        ]]
        
        await update.message.reply_text(
            "Bienvenue sur BlackCoin !\n\n"
            "Utilisez notre application pour gagner des points, "
            "monter en niveau et échanger avec vos amis.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Erreur commande /start: {e}")
        await update.message.reply_text(
            "⚠️ Une erreur est survenue. Veuillez réessayer plus tard.")

# === Endpoints API ===
@app.post("/auth/telegram", response_model=schemas.UserResponse)
async def telegram_auth(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        data = await request.json()
        if not verify_telegram_auth(data):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentification Telegram invalide"
            )

        user_id = int(data['id'])
        result = await db.execute(
            select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            # Créer un nouvel utilisateur
            new_user = models.User(
                id=user_id,
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                username=data.get('username', ''),
                photo_url=data.get('photo_url', ''),
                points=100,  # Points de bienvenue
                wallet=0,
                level=1
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            user = new_user

        # Générer un token JWT (simplifié pour l'exemple)
        token_data = {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        
        return {
            "user": user,
            "token": str(user.id)  # Dans une vraie app, utiliser un vrai JWT
        }

    except Exception as e:
        logger.error(f"Erreur authentification Telegram: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur serveur lors de l'authentification"
        )

@app.get("/user-data/{user_id}", response_model=schemas.UserResponse)
async def get_user_data(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # Vérification simple du token (dans une vraie app, utiliser JWT)
        if int(token) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé"
            )

        result = await db.execute(
            select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )

        return {"user": user}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID utilisateur invalide"
        )
    except Exception as e:
        logger.error(f"Erreur récupération données utilisateur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur serveur"
        )

@app.post("/update-user", response_model=schemas.UserResponse)
async def update_user(
    update_data: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        user_id = int(token)
        result = await db.execute(
            select(models.User).where(models.User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )

        # Mise à jour des champs autorisés
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour"
        )

# === Gestion des erreurs ===
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur non gérée: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Une erreur interne est survenue"},
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# === Handlers Telegram ===
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# === Démarrage de l'application ===
@app.on_event("startup")
async def startup_event():
    await init_db()
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Application démarrée avec webhook: {WEBHOOK_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    await application.shutdown()
    logger.info("Application arrêtée")

# === Webhook Telegram ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erreur webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# == Endpoint de santé ==
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat()  # Ajout de la valeur
    }

# == Route racine ==
@app.get("/")
async def root():
    return {  # Correction des crochets -> accolades
        "message": "BlackCoin Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }