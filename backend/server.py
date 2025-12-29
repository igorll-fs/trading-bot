"""
Trading Bot API - Servidor Principal

Este arquivo foi refatorado para usar módulos separados:
- api/models.py: Modelos Pydantic
- api/routes/health.py: Health checks e diagnósticos
- api/routes/config.py: Configuração do bot
- api/routes/bot.py: Controle do bot (start/stop/sync)
- api/routes/performance.py: Performance, trades e streaming
- api/routes/learning.py: Estatísticas de ML
"""

import os
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from bot.trading_bot import get_bot
from bot.config import BotConfig
from bot.logging_config import setup_logging, get_logger

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure centralized logging
setup_logging()
logger = get_logger(__name__)

# MongoDB connection with optimized pool
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    serverSelectionTimeoutMS=5000
)
db = client[os.environ['DB_NAME']]


def _sanitize_config(config: BotConfig) -> Dict[str, Any]:
    """Remove segredos da configuração para resposta pública."""
    data = config.to_public_dict()
    for secret_key in [
        'binance_api_key',
        'binance_api_secret',
        'telegram_bot_token',
        'telegram_chat_id',
    ]:
        data.pop(secret_key, None)
    return data


async def ensure_indexes():
    """Cria índices MongoDB necessários (idempotente)."""
    try:
        # Trades collection - queries mais frequentes
        await db.trades.create_index([("closed_at", -1)])
        await db.trades.create_index([("simulated", 1), ("closed_at", -1)])

        # Learning data - filtros por tipo e ordenação
        await db.learning_data.create_index([("timestamp", -1)])
        await db.learning_data.create_index([("type", 1), ("timestamp", -1)])

        # Positions - status queries
        await db.positions.create_index([("status", 1)])

        logger.info("Mongo indexes ensured: trades, learning_data, positions")
    except Exception as exc:
        logger.error("Failed to ensure Mongo indexes: %s", exc)


# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="API para controle do bot de trading",
    version="1.0.0",
)

# Create main API router
api_router = APIRouter(prefix="/api")

# Import and configure route modules
from api.routes.health import create_health_router
from api.routes.config import create_config_router
from api.routes.bot import create_bot_router
from api.routes.performance import create_performance_router
from api.routes.learning import create_learning_router
from api.routes.market import create_market_router
from api.rate_limiting import setup_rate_limiting

# Create routers with dependencies
health_router = create_health_router(db, get_bot, _sanitize_config)
config_router = create_config_router(db, get_bot)
bot_router = create_bot_router(db, get_bot)
performance_router = create_performance_router(db, get_bot)
learning_router = create_learning_router(db, get_bot)
market_router = create_market_router(db, get_bot)

# Include all routers
api_router.include_router(health_router)
api_router.include_router(config_router)
api_router.include_router(bot_router)
api_router.include_router(performance_router)
api_router.include_router(learning_router)
api_router.include_router(market_router)


# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Trading Bot API", "status": "online"}


# Include main router
app.include_router(api_router)

# Setup rate limiting
setup_rate_limiting(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Inicialização do servidor."""
    await ensure_indexes()
    logger.info("Server started successfully")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup ao desligar."""
    client.close()
    logger.info("Server shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)