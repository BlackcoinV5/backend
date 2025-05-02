from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from database import get_db
from models import User
from schemas import UserCreate, UserResponse
from utils import hash_password, generate_verification_code, send_verification_email

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://blackcoin-v5-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Route santé
@app.get("/")
async def root():
    return {"message": "Backend is running!"}

# ✅ Webhook Telegram
@app.post("/webhook")
async def telegram_webhook(update: dict = Body(...)):
    # à compléter si besoin
    return {"ok": True}

# ✅ Login utilisateur
class LoginRequest(BaseModel):
    email: str
    password: str
    telegramUsername: str

@app.post("/login")
async def login_user(login: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == login.email))
    user = result.scalar_one_or_none()

    if not user or user.password_hash != hash_password(login.password):
        raise HTTPException(status_code=401, detail="Identifiants invalides.")

    if user.telegram_username != login.telegramUsername:
        raise HTTPException(status_code=401, detail="Nom d'utilisateur Telegram incorrect.")

    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "telegram_username": user.telegram_username,
        "is_verified": user.is_verified,
    }

# ✅ Récupération des données utilisateur
@app.get("/user-data/{user_id}")
async def get_user_data(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")

    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "telegram_username": user.telegram_username,
        "wallet": user.wallet,
        "points": user.points,
        "level": user.level,
    }

# ✅ Inscription
@app.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Vérif username Telegram
    if not user_data.telegram_username or user_data.telegram_username.startswith("anonymous"):
        raise HTTPException(status_code=400, detail="Nom d'utilisateur Telegram invalide.")

    # Vérif email déjà utilisé
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé.")

    # Générer code + envoyer mail
    verification_code = generate_verification_code()
    send_verification_email(user_data.email, verification_code)

    # Créer utilisateur
    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        birth_date=user_data.birth_date,
        phone_code=user_data.phone_code,
        phone_number=user_data.phone_number,
        telegram_username=user_data.telegram_username,
        email=user_data.email,
        country=user_data.country,
        country_code=user_data.country_code,
        password_hash=hash_password(user_data.password),
        is_verified=False,
        verification_code=verification_code,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
