import logging
from telegram import Bot
from telegram.error import TelegramError
from config import settings

logger = logging.getLogger(__name__)

async def send_telegram_message(user_id: int, message: str):
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="HTML"
        )
    except TelegramError as e:
        logger.error(f"Erreur d'envoi Telegram à {user_id}: {e}")

def generate_referral_link(user_id: int) -> str:
    return f"{settings.FRONTEND_URL}?ref={user_id}"