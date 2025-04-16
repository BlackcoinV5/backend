import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupération de l'URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL manquant dans le fichier .env")

# Remplacement du préfixe pour asyncpg si nécessaire
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Création de l'engine SQLAlchemy pour asyncpg
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Mettre à True pour le debug des requêtes SQL
    pool_pre_ping=True
)

# Création du session maker async
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base pour les modèles SQLAlchemy
Base = declarative_base()

# Fonction pour initialiser la base de données (créer les tables)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dépendance pour obtenir une session de base de données
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

