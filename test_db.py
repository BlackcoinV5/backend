import asyncio
import asyncpg

async def test_db():
    try:
        conn = await asyncpg.connect("postgresql://blackcoin_user:F30wil30@localhost:5432/blackcoin")
        print("✅ Connexion réussie à la base de données !")
        await conn.close()
    except Exception as e:
        print("❌ Erreur de connexion :", e)

asyncio.run(test_db())
