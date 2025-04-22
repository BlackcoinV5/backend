import logging
from telegram import Bot
from telegram.error import TelegramError
from config import settings

logger = logging.getLogger(__name__)

# === Fonction pour envoyer un message Telegram ===
async def send_telegram_message(user_id: int, message: str):
    """
    Envoie un message à un utilisateur Telegram via le bot.
    
    Args:
        user_id (int): ID Telegram de l'utilisateur.
        message (str): Contenu du message à envoyer.
    """
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML"  # Permet de formater le message
        )
        logger.info(f"✅ Message envoyé à {user_id}")
    except TelegramError as e:
        logger.error(f"❌ Erreur lors de l'envoi Telegram à {user_id} : {e}")

# === Fonction pour générer un lien de parrainage personnalisé ===
def generate_referral_link(user_id: int) -> str:
    """
    Génère un lien de parrainage unique pour un utilisateur.
    
    Args:
        user_id (int): ID Telegram de l'utilisateur.
    
    Returns:
        str: URL de parrainage.
    """
    return f"{settings.FRONTEND_URL}?ref={user_id}"
