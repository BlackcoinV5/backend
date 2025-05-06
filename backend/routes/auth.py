from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models import User, VerificationCode
from backend.schemas import UserCreate, UserVerify
from backend.utils.email_utils import send_verification_email, generate_verification_code

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Vérifie l'unicité de l'e-mail
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Vérifie l'unicité du Telegram username
    result = await db.execute(select(User).where(User.telegram_username == user.telegram_username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username Telegram déjà utilisé")

    hashed_password = pwd_context.hash(user.password)
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

    # Génère et stocke un code de vérification
    code = generate_verification_code()
    verification = VerificationCode(
        user_id=new_user.id,
        code=code,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(verification)
    await db.commit()

    # Envoie le code par e-mail
    await send_verification_email(user.email, code)

    return {"message": "Utilisateur créé. Vérifie ton email pour valider ton compte."}


@router.post("/verify")
async def verify_user(data: UserVerify, db: AsyncSession = Depends(get_db)):
    # Cherche l'utilisateur
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Récupère le code de vérification
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

    # Active le compte
    user.is_active = True
    await db.commit()

    return {"message": "Compte vérifié avec succès."}
