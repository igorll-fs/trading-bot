import os
import asyncio
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


async def main():
    # Load .env from backend folder if python-dotenv is available
    backend_dir = Path(__file__).resolve().parents[1]
    if load_dotenv:
        load_dotenv(backend_dir / '.env')

    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

    # Use motor to test connection
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
    except ImportError as e:
        print('[FAIL] motor (MongoDB driver) nao esta instalado:', e)
        raise SystemExit(1)

    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=3000)

    try:
        # ping admin
        await client.admin.command('ping')
        # optional: list dbs
        dbs = await client.list_database_names()
        print('[OK] Conexao com MongoDB bem-sucedida! Databases:', ', '.join(dbs) if dbs else '(nenhuma)')
    except Exception as e:
        print('[FAIL] Nao foi possivel conectar ao MongoDB:', str(e))
        raise SystemExit(2)
    finally:
        client.close()


if __name__ == '__main__':
    asyncio.run(main())

