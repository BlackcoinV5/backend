import os
import smtplib
import logging
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from models import EmailVerificationCode

# Charger les variables d'environnement
load_dotenv()

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configuration de l'email
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def _generate_verification_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def _build_email_message(to_email: str, code: str) -> MIMEMultipart:
    subject = "🎯 Votre code de vérification BlackCoin"
    body = f"""Bonjour 👋,

Voici votre code de vérification pour valider votre inscription sur BlackCoin :

✅ Code : {code}

Ce code est valable pendant 10 minutes. Ne le partagez avec personne !

— L'équipe BlackCoin
"""

    message = MIMEMultipart()
    message["From"] = EMAIL_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", _charset="utf-8"))
    return message


def send_verification_email(to_email: str, code: str):
    message = _build_email_message(to_email, code)
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(message)
        server.quit()
        logger.info(f"📧 Code de vérification envoyé à {to_email}")
    except Exception as e:
        logger.error(f"⚠️ Erreur lors de l'envoi de l'email à {to_email} : {e}")
        raise


async def create_and_send_verification_code(email: str, db: AsyncSession) -> str:
    # Supprimer les anciens codes liés à cet email
    await db.execute(delete(EmailVerificationCode).where(EmailVerificationCode.email == email))

    # Générer un nouveau code
    code = _generate_verification_code()
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=10)

    # Enregistrer le code dans la base de données
    verification_entry = EmailVerificationCode(
        email=email,
        code=code,
        created_at=now,
        expires_at=expires_at
    )
    db.add(verification_entry)
    await db.commit()

    # Envoyer l'e-mail
    send_verification_email(email, code)

    return code
