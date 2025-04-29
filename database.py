import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

# === Chargement des variables d'environnement ===
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL manquant dans le fichier .env")

# === Adaptation pour asyncpg si nécessaire ===
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# === Création du moteur SQLAlchemy en mode asynchrone ===
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # Activez en True pour le debug SQL
    pool_pre_ping=True   # Vérifie la connexion avant chaque requête
)

# === Création d'une session asynchrone ===
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# === Base pour les modèles ===
Base = declarative_base()

# === Initialisation de la base de données ===
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# === Dépendance FastAPI pour l'injection de session ===
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
