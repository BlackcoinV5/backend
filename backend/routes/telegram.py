from fastapi import APIRouter, Request
from backend.utils.telegram import send_message  # 👈 à créer
import logging

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    logging.info("📨 Reçu de Telegram : %s", payload)

    message = payload.get("message")
    if message:
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text == "/start":
            await send_message(chat_id, "👋 Bienvenue sur Blackcoin ! Envoie ton nom d'utilisateur pour commencer.")
        else:
            await send_message(chat_id, f"Tu as dit : {text}")

    return {"status": "ok"}
