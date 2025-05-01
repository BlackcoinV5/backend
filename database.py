# backend/database.py

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Charger les variables d’environnement
load_dotenv()

# Récupérer l’URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ La variable d’environnement DATABASE_URL est manquante.")

# Vérifier le format pour asyncpg
if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise ValueError("❌ Mauvaise URL pour la base de données. Utilise 'postgresql+asyncpg://...' pour asyncpg.")

print(f">>> ✅ DATABASE_URL utilisé : {DATABASE_URL}")

# Création du moteur asynchrone
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Peut être désactivé en prod
    future=True,
)

# Création du SessionLocal
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base pour les modèles
Base = declarative_base()

# Dépendance pour récupérer la session
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
