import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Charger .env
load_dotenv()
print(".env path used:", os.path.abspath(".env"))

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

def send_validation_email_html(receiver_email: str, code: str):
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
        print("❌ Erreur : Adresse email ou mot de passe manquant dans le fichier .env")
        return

    sender_email = EMAIL_HOST_USER
    subject = "🎉 Blackcoin - Code de validation de votre compte"

    logo_url = "https://i.ibb.co/G9XYp5T/logo-blackcoin.png"

    html_body = f"""
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
                <p style="text-align: center;">Veuillez entrer ce code dans l'application Telegram pour activer votre compte.</p>
                <hr style="margin: 30px 0;">
                <p style="font-size: 12px; color: #777; text-align: center;">Si vous n’êtes pas à l’origine de cette demande, ignorez simplement ce message.</p>
                <p style="font-size: 14px; color: #333; text-align: center;">— L’équipe Blackcoin</p>
            </div>
        </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, EMAIL_HOST_PASSWORD)
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("✅ Email HTML envoyé avec succès !")
    except Exception as e:
        print("❌ Erreur lors de l'envoi :", str(e))


if __name__ == "__main__":
    send_validation_email_html(receiver_email=EMAIL_HOST_USER, code="432178")
