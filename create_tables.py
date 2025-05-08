import asyncio
from backend.database import engine
from backend import models

async def create_all_tables():
    async with engine.begin() as conn:
        print("🛠️ Création des tables...")
        # Supprime les tables existantes (optionnel)
        await conn.run_sync(models.Base.metadata.drop_all)
        # Crée toutes les tables définies dans models.py
        await conn.run_sync(models.Base.metadata.create_all)
        print("✅ Tables créées avec succès !")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
