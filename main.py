import os
import asyncio
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from fastapi.middleware.cors import CORSMiddleware

# ✅ Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ Initialiser FastAPI
app = FastAPI()

# ✅ Activer CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permet toutes les origines (à restreindre en prod)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise GET, POST, etc.
    allow_headers=["*"],  # Autorise tous les headers
)

# ✅ Initialiser le bot Telegram
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# ✅ Stockage temporaire des joueurs
users = {}

# ✅ Commande /start
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in users:
        users[user_id] = {"points": 0, "wallet": 0}
    await update.message.reply_text("Bienvenue sur BlackCoin 🎉 !\nUtilise /balance pour voir ton solde.")

# ✅ Commande /balance
async def balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in users:
        await update.message.reply_text(
            f"💰 Solde: {users[user_id]['points']} pts\n🔹 Wallet: {users[user_id]['wallet']} pts"
        )
    else:
        await update.message.reply_text("Tu n'es pas encore inscrit. Utilise /start d'abord !")

# ✅ Commande /send_points
async def send_points(update: Update, context: CallbackContext):
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

# ✅ Fonction pour lancer le bot Telegram
async def start_bot():
    """Démarre le bot Telegram"""
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

# ✅ Lancer le bot en parallèle de FastAPI
@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())

# ✅ Webhook pour recevoir les mises à jour Telegram
@app.post("/webhook")
async def webhook(request: Request):
    """Gère les mises à jour de Telegram via Webhook"""
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return {"status": "ok"}

# ✅ API pour récupérer les données des utilisateurs
@app.get("/user-data")
async def get_user_data():
    """Renvoie les données de tous les utilisateurs"""
    return users

# ✅ Page d'accueil
@app.get("/")
async def home():
    return {"message": "Bot connecté à BlackCoin"}
