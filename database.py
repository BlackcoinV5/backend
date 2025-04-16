import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer l'URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL")

# Vérification de la présence de DATABASE_URL
if not DATABASE_URL:
    raise ValueError("DATABASE_URL manquant dans .env")

# Conversion automatique vers asyncpg si nécessaire
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Création du moteur SQLAlchemy en mode asynchrone
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Met à True pour activer les logs SQL (utile en développement)
    pool_pre_ping=True  # Vérifie la connexion avant de l'utiliser
)

# Création du sessionmaker asynchrone
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base de données déclarative pour SQLAlchemy
Base = declarative_base()

# Fonction pour initialiser la base (ex : créer les tables à partir des modèles)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dépendance FastAPI pour obtenir une session de base de données
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
