# backend/routes/telegram.py
from fastapi import APIRouter, Request
import logging

router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    payload = await request.json()
    logging.info("📨 Message reçu depuis Telegram : %s", payload)
    return {"status": "ok"}
