from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
from backend.database import get_db
from backend.models import User, VerificationCode
from backend.schemas import UserCreate, UserVerify
from backend.utils.email_utils import send_verification_email, generate_verification_code
import os
import httpx

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ------------------------------
# 🔐 Vérification username Telegram
# ------------------------------
class TelegramCheckResponse(BaseModel):
    telegram_id: int
    photo_url: str | None

@router.get("/telegram/verify", response_model=TelegramCheckResponse)
async def verify_telegram_username(username: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(status_code=500, detail="Bot token not configured")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.telegram.org/bot{token}/getChat",
            params={"chat_id": f"@{username}"}
        )
    data = response.json()
    if not data.get("ok"):
        raise HTTPException(status_code=404, detail="register.errors.invalidTelegramUsername")

    chat = data["result"]
    return {
        "telegram_id": chat["id"],
        "photo_url": chat.get("photo", {}).get("small_file_id")  # facultatif
    }

# ------------------------------
# 📝 Inscription utilisateur
# ------------------------------
@router.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Vérifie si l'e-mail est déjà utilisé
    existing_email = await db.execute(select(User).where(User.email == user.email))
    if existing_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Vérifie si le username Telegram est déjà pris
    existing_username = await db.execute(select(User).where(User.telegram_username == user.telegram_username))
    if existing_username.scalars().first():
        raise HTTPException(status_code=400, detail="Username Telegram déjà utilisé")

    # Hash du mot de passe
    hashed_password = pwd_context.hash(user.password)

    # Création de l'utilisateur
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        birth_date=user.birthdate,
        phone=user.phone,
        telegram_username=user.telegram_username,
        email=user.email,
        password_hash=hashed_password,
        is_active=False
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Génération du code de vérification
    code = generate_verification_code()
    verification = VerificationCode(
        user_id=new_user.id,
        code=code,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(verification)
    await db.commit()

    # Envoi du code par e-mail
    await send_verification_email(user.email, code)

    return {"message": "Utilisateur créé. Vérifie ton email pour valider ton compte."}

# ------------------------------
# ✅ Vérification du compte
# ------------------------------
@router.post("/verify")
async def verify_user(data: UserVerify, db: AsyncSession = Depends(get_db)):
    # Recherche de l'utilisateur
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Recherche du code valide
    result = await db.execute(
        select(VerificationCode).where(
            VerificationCode.user_id == user.id,
            VerificationCode.code == data.code,
            VerificationCode.expires_at > datetime.utcnow()
        )
    )
    code_entry = result.scalars().first()
    if not code_entry:
        raise HTTPException(status_code=400, detail="Code invalide ou expiré")

    # Activation du compte
    user.is_active = True
    await db.commit()

    return {"message": "Compte vérifié avec succès."}
