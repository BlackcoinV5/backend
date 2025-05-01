from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import User
from schemas import UserCreate, UserResponse
from utils import hash_password, generate_verification_code, send_verification_email
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://blackcoin-v5-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Route de santé / test de connexion
@app.get("/")
async def root():
    return {"message": "Backend is running!"}

# ✅ Enregistrement d'un utilisateur
@app.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Vérification du nom d'utilisateur Telegram
    if not user_data.telegram_username or user_data.telegram_username.startswith("anonymous"):
        raise HTTPException(status_code=400, detail="Nom d'utilisateur Telegram invalide.")

    # Vérifier si l’email existe déjà
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email déjà utilisé.")

    # Générer code de vérification et envoyer l’email
    verification_code = generate_verification_code()
    send_verification_email(user_data.email, verification_code)

    # Créer le nouvel utilisateur
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
        verification_code=verification_code
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
