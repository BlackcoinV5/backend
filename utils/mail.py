import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

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

    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(message)
        server.quit()
        print(f"📧 Code envoyé à {to_email}")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'envoi de l'email : {e}")
        raise
