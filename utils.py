import logging
from telegram import Bot
from telegram.error import TelegramError
from config import settings
from .user import User
from .wallet import Wallet
from .transaction import Transaction
from .myactivity import Activity
from .status import Status

logger = logging.getLogger(__name__)

# === Envoi de message Telegram ===
async def send_telegram_message(user_id: int, message: str) -> None:
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
            parse_mode="HTML"  # Permet la mise en forme HTML
        )
        logger.info(f"✅ Message envoyé à l'utilisateur {user_id}")
    except TelegramError as e:
        logger.error(f"❌ Erreur d'envoi Telegram pour l'utilisateur {user_id} : {e}")

# === Lien de parrainage personnalisé ===
def generate_referral_link(user_id: int) -> str:
    """
    Génère un lien de parrainage personnalisé.

    Args:
        user_id (int): ID de l'utilisateur.

    Returns:
        str: Lien complet avec paramètre de parrainage.
    """
    return f"{settings.FRONTEND_URL}?ref={user_id}"
