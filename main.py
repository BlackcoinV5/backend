
import os
import logging
import asyncio
from dotenv import load_dotenv
load_dotenv()  # va chercher .env dans le dossier backend

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from telegram import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

import models
import schemas
from models import User
from database import init_db, async_session as SessionLocal
from utils.mail import send_verification_email
 # Assure-toi qu'elle fonctionne bien

# === Chargement des variables d'environnement ===
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TOKEN or not FRONTEND_URL or not WEBHOOK_URL:
    raise ValueError("⚠️ .env mal configuré. Vérifie TELEGRAM_BOT_TOKEN, FRONTEND_URL et WEBHOOK_URL.")

# === Configuration des logs ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Initialisation FastAPI ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Initialisation du bot Telegram ===
application = Application.builder().token(TOKEN).build()

# === Dépendance base de données ===
async def get_db():
    async with SessionLocal() as session:
        yield session

# === Vérification Telegram Auth ===
def verify_telegram_auth(data):
    data_copy = data.copy()
    check_hash = data_copy.pop("hash", None)
    sorted_data = "\n".join([f"{k}={v}" for k, v in sorted(data_copy.items())])
    secret_key = hashlib.sha256(TOKEN.encode()).digest()
    expected_hash = hmac.new(secret_key, sorted_data.encode(), hashlib.sha256).hexdigest()
    auth_time_ok = (int(data_copy.get("auth_date", "0")) + 86400) > int(time.time())
    return check_hash == expected_hash and auth_time_ok

# === Commande /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚀 Lancer l'app", web_app=WebAppInfo(url=FRONTEND_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Bienvenue sur BlackCoin 🎉 !\nClique sur le bouton ci-dessous pour ouvrir l'application :",
        reply_markup=reply_markup
    )

# === Commande /balance ===
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with SessionLocal() as db:
        user_id = update.effective_user.id
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            await update.message.reply_text(f"💰 Solde: {user.points} pts\n🔹 Wallet: {user.wallet} pts")
        else:
            await update.message.reply_text("⚠️ Utilisateur non trouvé.")

# === Commande /send_points ===
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

            sender_result = await db.execute(select(User).filter(User.id == user_id))
            sender = sender_result.scalar_one_or_none()

            recipient_result = await db.execute(select(User).filter(User.id == recipient_id))
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
            await update.message.reply_text("⚠ Erreur : Veuillez entrer un ID valide et un montant.")

# === Gestion des erreurs ===
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erreur bot : {context.error}")
    if update.message:
        await update.message.reply_text("⚠ Une erreur est survenue. Merci de réessayer plus tard.")

# === Ajout des Handlers ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("balance", balance))
application.add_handler(CommandHandler("send_points", send_points))
application.add_error_handler(error_handler)

# === Lancement Webhook ===
async def start_bot():
    await application.initialize()
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook activé sur {WEBHOOK_URL}")
    await application.start()

@app.on_event("startup")
async def on_startup():
    await init_db()
    asyncio.create_task(start_bot())

# === Endpoint Telegram Webhook ===
@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erreur Webhook: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# === Authentification depuis le frontend ===
@app.post("/auth/telegram", response_model=schemas.UserBase)
async def auth_telegram(user_data: dict, db: AsyncSession = Depends(get_db)):
    if not verify_telegram_auth(user_data):
        raise HTTPException(status_code=403, detail="Données Telegram invalides")

    user_id = user_data["id"]
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=user_id,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            username=user_data.get("username", ""),
            photo_url=user_data.get("photo_url", "")
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user

# === Inscription : Envoi du code de vérification ===
@app.post("/register/send-code")
async def send_verification_code(email: str, db: AsyncSession = Depends(get_db)):
    code = str(random.randint(100000, 999999))
    result = await db.execute(select(models.EmailVerification).filter(models.EmailVerification.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        existing.code = code
        existing.expires_at = datetime.utcnow() + timedelta(minutes=10)
    else:
        verification = models.EmailVerification(email=email, code=code)
        db.add(verification)

    await db.commit()
    await send_verification_email(email, code)
    return {"message": "📧 Code envoyé par email"}

@app.post("/register/verify-code")
async def verify_code(email: str, code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.EmailVerification).filter(models.EmailVerification.email == email))
    verification = result.scalar_one_or_none()

    if not verification or verification.code != code:
        raise HTTPException(status_code=400, detail="❌ Code incorrect")
    if verification.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="⏰ Code expiré")

    return {"message": "✅ Code vérifié avec succès"}

# === Liste utilisateurs (pour affichage admin) ===
@app.get("/user-data", response_model=list[schemas.UserBase])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# === Admin : liste des utilisateurs avec détails ===
@app.get("/admin/users")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).options(
            selectinload(User.transactions),
            selectinload(User.activities)
        )
    )
    users = result.scalars().all()

    return [{
        "id": u.id,
        "name": f"{u.first_name} {u.last_name}",
        "username": u.username,
        "points": u.points,
        "is_active": u.is_active,
        "is_restricted": u.is_restricted,
        "transactions": [{"amount": t.amount, "type": t.type, "date": t.timestamp} for t in u.transactions],
        "activities": [{"description": a.description, "date": a.date} for a in u.activities]
    } for u in users]

@app.put("/admin/users/{user_id}")
async def update_user(user_id: int, payload: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    for key, value in payload.items():
        setattr(user, key, value)

    await db.commit()
    return {"message": "✅ Utilisateur mis à jour"}

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    await db.delete(user)
    await db.commit()
    return {"message": "🗑️ Utilisateur supprimé"}

# === Accueil ===
@app.get("/")
def root():
    return {"message": "✅ Backend BlackCoin opérationnel"}
