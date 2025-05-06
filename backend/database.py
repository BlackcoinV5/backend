import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Charge le fichier .env situé dans le dossier backend
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Récupération de la variable d’environnement
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Please check backend/.env")

# Configuration de SQLAlchemy avec async support
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Base pour les modèles ORM
Base = declarative_base()

# Dépendance pour FastAPI
async def get_db():
    async with SessionLocal() as session:
        yield session
