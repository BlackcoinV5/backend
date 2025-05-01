# backend/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(">>> DATABASE_URL utilisé :", DATABASE_URL)

if not DATABASE_URL.startswith("postgresql+asyncpg://"):
    raise ValueError("❌ Mauvaise URL pour la base de données. Utilise 'postgresql+asyncpg://...' pour asyncpg.")


engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
