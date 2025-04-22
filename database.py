import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
from typing import AsyncGenerator

# === Chargement des variables d'environnement ===
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# === Vérification de DATABASE_URL ===
if not DATABASE_URL:
    raise ValueError("DATABASE_URL manquant dans le fichier .env")

# === Adaptation du driver pour asyncpg (requis pour async SQLAlchemy avec PostgreSQL) ===
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# === Création du moteur SQLAlchemy en mode asynchrone ===
engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # Passe à True pour le debug (affiche les requêtes SQL)
    pool_pre_ping=True   # Teste la connexion avant chaque requête
)

# === Création d’un sessionmaker asynchrone ===
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# === Base déclarative pour les modèles SQLAlchemy ===
Base = declarative_base()

# === Fonction d'initialisation de la base de données ===
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# === Dépendance pour injection dans les routes FastAPI ===
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
