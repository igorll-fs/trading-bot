# MongoDB Optimization Script
# Execute este script para criar indices otimizados

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_indexes():
    """Criar indices otimizados no MongoDB"""

    MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME = os.getenv('DB_NAME', 'trading_bot')

    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    try:
        logger.info("Criando indices otimizados...")

        # Indices para trades (queries por timestamp e symbol)
        await db.trades.create_index([
            ("timestamp", -1),
            ("symbol", 1)
        ], name="trades_timestamp_symbol")

        await db.trades.create_index([
            ("status", 1),
            ("timestamp", -1)
        ], name="trades_status_timestamp")

        logger.info("Indices criados para collection 'trades'")

        # Indices para positions (queries por symbol e status)
        await db.positions.create_index([
            ("symbol", 1),
            ("status", 1)
        ], name="positions_symbol_status")

        await db.positions.create_index([
            ("status", 1),
            ("timestamp", -1)
        ], name="positions_status_timestamp")

        logger.info("Indices criados para collection 'positions'")

        # Indices para learning_data (queries por type e timestamp)
        await db.learning_data.create_index([
            ("type", 1),
            ("timestamp", -1)
        ], name="learning_type_timestamp")

        logger.info("Indices criados para collection 'learning_data'")

        # Indices para configs (queries por type)
        await db.configs.create_index([
            ("type", 1)
        ], name="configs_type")

        logger.info("Indices criados para collection 'configs'")

        # Verificar indices criados
        logger.info("\nIndices ativos:")
        for collection_name in ['trades', 'positions', 'learning_data', 'configs']:
            collection = db[collection_name]
            indexes = await collection.index_information()
            logger.info(f"\n{collection_name}:")
            for idx_name, idx_info in indexes.items():
                logger.info(f"  - {idx_name}: {idx_info.get('key', [])}")

        logger.info("\nOtimizacao do MongoDB concluida!")
        logger.info("Queries agora estao potencialmente mais rapidas.")

    except Exception as e:
        logger.error(f"Erro ao criar indices: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())

