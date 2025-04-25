import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from database import Base

load_dotenv()

logger = logging.getLogger(__name__)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_verification_email(to_email: str, code: str):
    subject = "🎯 Votre code de vérification BlackCoin"
    body = f"""
    Bonjour 👋,

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
