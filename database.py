import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupération de l'URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("⚠️ DATABASE_URL n'est pas défini dans .env")

# Conversion en format asyncpg si nécessaire
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Création de l'engine asynchrone
engine = create_async_engine(DATABASE_URL, echo=True)

# Création de la session asynchrone
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Déclaration de la base pour les modèles
Base = declarative_base()

# Fonction pour initialiser la base de données (création des tables)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)