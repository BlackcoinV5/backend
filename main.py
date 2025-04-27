import os
import logging
import logging.config
import asyncio
import hashlib
import hmac
import time
import random
import httpx  # Ajoute cette importation si elle n'est pas encore faite
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Body, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr, validator, field_validator
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

from models import User, EmailVerificationCode, Transaction, Activity
from database import init_db, async_session as SessionLocal
from utils.mail import send_verification_email

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

@app.post("/webhook", tags=["Telegram"])
async def telegram_webhook(request: Request):
    update = await request.json()
    logger.info(f"Received update: {update}")

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            await send_telegram_message(chat_id, "👋 Bienvenue sur BlackCoin !")
        else:
            await send_telegram_message(chat_id, f"🚀 Tu as envoyé: {text}")

    return {"ok": True}

async def send_telegram_message(chat_id, text):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
        )


# Chargement des variables d'environnement
load_dotenv()

# Configuration des logs
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s %(levelname)s %(module)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'blackcoin.log',
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'detailed',
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
})

logger = logging.getLogger(__name__)

# Configuration de l'application
app = FastAPI(
    title="BlackCoin API",
    version="1.0",
    description="API backend pour l'application BlackCoin",
    openapi_tags=[
        {
            "name": "Auth",
            "description": "Authentification et autorisation"
        },
        {
            "name": "Users",
            "description": "Gestion des utilisateurs"
        },
        {
            "name": "Transactions",
            "description": "Opérations financières"
        },
        {
            "name": "Admin",
            "description": "Fonctionnalités administratives"
        }
    ],
    contact={
        "name": "Support BlackCoin",
        "email": "support@blackcoin.com"
    }
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de sécurité
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modèles Pydantic
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    confirm_password: str
    phone: str
    birth_date: str
    telegram_username: str

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v

    @field_validator('telegram_username')
    def validate_telegram_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]{5,32}$", v):
            raise ValueError("Nom d'utilisateur Telegram invalide")
        return v

    @field_validator('birth_date')
    def validate_birth_date(cls, v):
        birth_date = datetime.strptime(v, "%Y-%m-%d").date()
        if birth_date > datetime.now().date() - timedelta(days=365*13):
            raise ValueError("Vous devez avoir au moins 13 ans")
        return v

class UserResponse(UserBase):
    id: int
    points: int
    wallet: int

# Utilitaires
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(SessionLocal)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user

# Gestion des erreurs
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "success": False,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Routes d'authentification
@app.post("/register", response_model=UserResponse, tags=["Auth"])
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(SessionLocal)
):
    try:
        # Vérification existence utilisateur
        existing_user = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if existing_user.scalar():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nom d'utilisateur déjà utilisé"
            )

        # Création utilisateur
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            **user_data.model_dump(exclude={"confirm_password"}),
            hashed_password=hashed_password,
            points=100,  # Bonus de bienvenue
            wallet=0,
            created_at=datetime.utcnow()
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Génération token
        access_token = create_access_token(
            data={"sub": new_user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {
            **new_user.__dict__,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(SessionLocal)
):
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}

# Routes utilisateur
@app.get("/users/me", response_model=UserResponse, tags=["Users"])
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user

# Routes admin
@app.get("/admin/users", tags=["Admin"])
async def get_all_users(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(SessionLocal)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )

    result = await db.execute(
        select(User).options(
            selectinload(User.transactions),
            selectinload(User.activities)
        )
    )
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "name": f"{u.first_name} {u.last_name}",
            "username": u.username,
            "points": u.points,
            "wallet": u.wallet,
            "is_active": u.is_active,
            "transactions": [
                {
                    "amount": t.amount,
                    "type": t.type,
                    "date": t.timestamp.isoformat()
                } for t in u.transactions
            ],
            "activities": [
                {
                    "description": a.description,
                    "date": a.date.isoformat()
                } for a in u.activities
            ]
        }
        for u in users
    ]

# Initialisation
@app.on_event("startup")
async def on_startup():
    await init_db()
    logger.info("Application démarrée")

@app.get("/", tags=["Statut"])
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }