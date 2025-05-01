import random
import smtplib
from email.message import EmailMessage
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))

def send_verification_email(email_to: str, code: str):
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # ton adresse Gmail
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # mot de passe de l’app

    msg = EmailMessage()
    msg["Subject"] = "Code de validation Blackcoin"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email_to
    msg.set_content(f"Voici votre code de validation : {code}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
