import os
import ssl
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Chargement du fichier .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Récupération de l'URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Please check backend/.env")

# Création du moteur SQLAlchemy (async) avec SSL pour Neon
ssl_context = ssl.create_default_context()
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"ssl": ssl_context}
)

# Configuration de la session asynchrone
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Base ORM pour les modèles
Base = declarative_base()

# Dépendance pour FastAPI (injection de session)
async def get_db():
    async with SessionLocal() as session:
        yield session

# Création automatique des tables au démarrage
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Exécution si le fichier est lancé directement
if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    print("✅ Tables créées avec succès !")
