# backend/utils/email_utils.py

import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


def generate_verification_code(length: int = 6) -> str:
    """Génère un code de validation numérique de longueur donnée."""
    return ''.join(random.choices(string.digits, k=length))


def send_verification_email(receiver_email: str, code: str) -> bool:
    """Envoie un email HTML contenant un code de validation."""
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        print("❌ Erreur : EMAIL_HOST_USER ou EMAIL_HOST_PASSWORD manquant dans .env")
        return False

    if "@" not in receiver_email or "." not in receiver_email:
        print("❌ Erreur : adresse email invalide")
        return False

    subject = "🎉 Blackcoin - Code de validation de votre compte"
    logo_url = "https://i.ibb.co/G9XYp5T/logo-blackcoin.png"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <div style="text-align: center;">
                    <img src="{logo_url}" alt="Blackcoin" style="width: 120px; margin-bottom: 20px;" />
                </div>
                <h2 style="color: #222; text-align: center;">Bienvenue sur <span style="color: #4CAF50;">Blackcoin</span> !</h2>
                <p style="text-align: center;">Merci pour votre inscription.</p>
                <p style="font-size: 18px; text-align: center;">Voici votre <strong>code de validation</strong> :</p>
                <div style="font-size: 26px; font-weight: bold; color: #4CAF50; text-align: center; margin: 20px 0;">{code}</div>
                <p style="text-align: center;">Veuillez entrer ce code dans l'application pour activer votre compte.</p>
                <hr style="margin: 30px 0;">
                <p style="font-size: 12px; color: #777; text-align: center;">Si vous n’êtes pas à l’origine de cette demande, ignorez ce message.</p>
                <p style="font-size: 14px; color: #333; text-align: center;">— L’équipe Blackcoin</p>
            </div>
        </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["From"] = EMAIL_HOST_USER
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.sendmail(EMAIL_HOST_USER, receiver_email, message.as_string())
            print(f"✅ Email envoyé avec succès à {receiver_email}")
            return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi à {receiver_email} :", str(e))
        return False
