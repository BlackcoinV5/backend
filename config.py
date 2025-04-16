import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    FRONTEND_URL = os.getenv("FRONTEND_URL")

settings = Settings()
