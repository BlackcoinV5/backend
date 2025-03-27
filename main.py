import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fastapi.middleware.cors import CORSMiddleware

# ✅ Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://blackcoin-v5-frontend-j1w3xnv4f-blackcoins-projects.vercel.app")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN n'est pas défini dans .env")

# ✅ Initialiser FastAPI
app = FastAPI()

# ✅ Activer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ En production, restreindre aux domaines de confiance
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Initialiser le bot Telegram
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# ✅ Stockage temporaire des joueurs
users = {}

# ✅ Commande /start → Génère un lien d'authentification unique
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    auth_link = f"{FRONTEND_URL}/auth/telegram?user_id={user_id}"
    
    await update.message.reply_text(
        f"Bienvenue sur BlackCoin 🎉 !\n"
        f"🔗 Connecte-toi ici : {auth_link}\n\n"
        "Utilise /balance pour voir ton solde."
    )

# ✅ Commande /balance → Affiche le solde du joueur
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in users:
        await update.message.reply_text(
            f"💰 Solde: {users[user_id]['points']} pts\n🔹 Wallet: {users[user_id]['wallet']} pts"
        )
    else:
        await update.message.reply_text("Tu n'es pas encore inscrit. Utilise /start d'abord !")

# ✅ Commande /send_points → Permet d'envoyer des points à un autre utilisateur
async def send_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text("Usage: /send_points <ID> <montant>")
        return

    try:
        recipient_id = int(args[0])
        amount = int(args[1])

        if user_id in users and users[user_id]["points"] >= amount:
            users[user_id]["points"] -= amount
            users.setdefault(recipient_id, {"points": 0, "wallet": 0})["points"] += amount
            await update.message.reply_text(f"✅ {amount} pts envoyés à {recipient_id} !")
        else:
            await update.message.reply_text("⚠ Solde insuffisant ou utilisateur inexistant.")
    
    except ValueError:
        await update.message.reply_text("⚠ Erreur : Veuillez entrer un ID valide et un montant en nombre.")

# ✅ Ajouter les handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("balance", balance))
application.add_handler(CommandHandler("send_points", send_points))

# ✅ Fonction pour démarrer le bot en mode Webhook
async def start_bot():
    WEBHOOK_URL = "https://blackcoin-backend-uv43.onrender.com/webhook"
    await application.initialize()
    await application.bot.set_webhook(WEBHOOK_URL)  # ✅ Activer le Webhook
    await application.start()

# ✅ Lancer le bot en parallèle de FastAPI
@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())

# ✅ Webhook pour recevoir les mises à jour Telegram
@app.post("/webhook")
async def webhook(request: Request):
    """Gère les mises à jour de Telegram via Webhook"""
    try:
        data = await request.json()
        update = Update.de_json(data, bot)
        await application.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ API pour récupérer les données des utilisateurs
@app.get("/user-data")
async def get_user_data():
    """Renvoie les données de tous les utilisateurs"""
    return users

# ✅ Route pour générer un lien d'authentification
@app.get("/auth")
async def generate_auth_link(user_id: int):
    """Génère un lien d'authentification pour un utilisateur"""
    auth_link = f"{FRONTEND_URL}/auth/telegram?user_id={user_id}"
    return {"auth_link": auth_link}

# ✅ Page d'accueil
@app.get("/")
async def home():
    return {"message": "Bot connecté à BlackCoin"}
