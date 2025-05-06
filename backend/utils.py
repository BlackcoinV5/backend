import random
import string
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Charge les variables d'environnement
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

# 🔐 Génère un code de 6 chiffres aléatoires
def generate_verification_code() -> str:
    return ''.join(random.choices(string.digits, k=6))

# 📧 Envoie un e-mail de vérification
async def send_verification_email(to_email: str, code: str):
    from_email = os.getenv("EMAIL_ADDRESS")
    from_password = os.getenv("EMAIL_PASSWORD")

    if not from_email or not from_password:
        raise ValueError("Les identifiants email ne sont pas configurés dans le fichier .env")

    subject = "Code de vérification Blackcoin"
    body = f"Voici ton code de vérification : {code}"

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(from_email, from_password)
            server.send_message(message)
    except Exception as e:
        print(f"[❌] Erreur lors de l'envoi du mail à {to_email} : {e}")
