import json

from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

from bot.trading_bot import get_bot
from bot.config import (
    BotConfig,
    load_bot_config,
    save_bot_config,
    DEFAULT_SELECTOR_MIN_QUOTE_VOLUME,
    DEFAULT_SELECTOR_MAX_SPREAD_PERCENT,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with optimized pool
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,  # Aumentado de 10 (padrão) para melhor concorrência
    minPoolSize=10,  # Manter conexões ativas
    maxIdleTimeMS=45000,  # Timeout de conexões idle
    serverSelectionTimeoutMS=5000  # Timeout de seleção de servidor
)
db = client[os.environ['DB_NAME']]

# Performance snapshot cache (throttle expensive queries)
_performance_cache: Dict[str, Any] = {"data": None, "ts": 0.0}
_performance_cache_ttl = float(os.environ.get('PERFORMANCE_CACHE_TTL', '5'))
_performance_lock: Optional[asyncio.Lock] = None


def _sanitize_config(config: BotConfig) -> Dict[str, Any]:
    data = config.to_public_dict()
    for secret_key in [
        'binance_api_key',
        'binance_api_secret',
        'telegram_bot_token',
        'telegram_chat_id',
    ]:
        data.pop(secret_key, None)
    return data


async def _get_performance_lock() -> asyncio.Lock:
    """Lazily create and return the shared performance cache lock."""
    global _performance_lock
    if _performance_lock is None:
        _performance_lock = asyncio.Lock()
    return _performance_lock

# Create the main app without a prefix
app = FastAPI(
    title="Trading Bot API",
    description="API para controle do bot de trading",
    version="1.0.0",
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ==================== HEALTH CHECK ====================
@api_router.get("/health")
async def health_check():
    """
    Health check endpoint para monitoramento.
    Verifica: MongoDB, Binance API, Bot status.
    """
    from bot.binance_client import binance_manager
    
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    # Check MongoDB
    try:
        await db.command("ping")
        health["services"]["mongodb"] = {"status": "ok"}
    except Exception as e:
        health["services"]["mongodb"] = {"status": "error", "message": str(e)[:100]}
        health["status"] = "degraded"
    
    # Check Binance API
    try:
        if binance_manager.client:
            binance_manager.client.ping()
            health["services"]["binance"] = {"status": "ok", "testnet": binance_manager.use_testnet}
        else:
            health["services"]["binance"] = {"status": "not_initialized"}
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["binance"] = {"status": "error", "message": str(e)[:100]}
        health["status"] = "degraded"
    
    # Check Bot
    try:
        bot = await get_bot(db)
        health["services"]["bot"] = {
            "status": "ok",
            "is_running": bot.is_running,
            "open_positions": len(bot.positions),
        }
    except Exception as e:
        health["services"]["bot"] = {"status": "error", "message": str(e)[:100]}
        health["status"] = "degraded"
    
    return health


async def ensure_indexes():
    """Create required MongoDB indexes (idempotent)."""
    try:
        await db.trades.create_index([("closed_at", -1)])
        await db.learning_data.create_index([("timestamp", -1)])
        logger.info("Mongo indexes ensured: trades.closed_at, learning_data.timestamp")
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Failed to ensure Mongo indexes: %s", exc)


# Define Models
class ConfigModel(BaseModel):
    binance_api_key: str
    binance_api_secret: str
    binance_testnet: bool = True
    telegram_bot_token: str
    telegram_chat_id: str
    max_positions: int = 3
    risk_percentage: float = 2.0
    leverage: int = 1
    balance_cache_ttl: float = 30.0
    observation_alert_interval: float = 300.0
    risk_use_position_cap: bool = True
    daily_drawdown_limit_pct: float = 0.0
    weekly_drawdown_limit_pct: float = 0.0

    # Novos parâmetros configuráveis via dashboard (filtros de entrada e proteção)
    selector_min_quote_volume: float = DEFAULT_SELECTOR_MIN_QUOTE_VOLUME
    selector_max_spread_percent: float = DEFAULT_SELECTOR_MAX_SPREAD_PERCENT
    strategy_min_signal_strength: int = 60

class ConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    max_positions: int = 3
    risk_percentage: float = 2.0
    leverage: int = 1
    balance_cache_ttl: float = 30.0
    observation_alert_interval: float = 300.0
    risk_use_position_cap: bool = True
    daily_drawdown_limit_pct: float = 0.0
    weekly_drawdown_limit_pct: float = 0.0

    selector_min_quote_volume: float = DEFAULT_SELECTOR_MIN_QUOTE_VOLUME
    selector_max_spread_percent: float = DEFAULT_SELECTOR_MAX_SPREAD_PERCENT
    strategy_min_signal_strength: int = 60

class BotControlRequest(BaseModel):
    action: str  # start or stop

class SyncResponse(BaseModel):
    status: str
    found_orders: int = Field(ge=0)
    canceled_orders: int = Field(ge=0)
    message: Optional[str] = None

class TradeResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    symbol: str
    side: str
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    position_size: float
    leverage: int
    pnl: Optional[float] = None
    roe: Optional[float] = None
    opened_at: str
    closed_at: Optional[str] = None
    status: str

# Routes
@api_router.get("/")
async def root():
    return {"message": "Trading Bot API", "status": "online"}


@api_router.get("/health")
async def healthcheck():
    """Lightweight healthcheck that does not touch external services."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@api_router.get("/diagnostics")
async def diagnostics():
    """Snapshot de configuração (sem segredos), posições e último sizing."""
    try:
        config = await load_bot_config(db)
        bot = await get_bot(db)
        status = await bot.get_status()
        return {
            "config": _sanitize_config(config),
            "positions_open": len(status.get("positions", []) if isinstance(status, dict) else []),
            "is_running": status.get("is_running") if isinstance(status, dict) else False,
            "balance": status.get("balance") if isinstance(status, dict) else 0,
            "last_risk_snapshot": getattr(bot, "last_risk_snapshot", None),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/config")
async def get_config():
    """Get bot configuration"""
    try:
        config = await load_bot_config(db)
        return config.to_public_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/config")
async def save_config(config: ConfigModel):
    """Save bot configuration"""
    try:
        bot_config = BotConfig.from_mapping(config.model_dump())
        await save_bot_config(db, bot_config)

        # Reinitialize bot with new config
        bot = await get_bot(db)
        await bot.initialize(bot_config)
        
        return {"status": "success", "message": "Configuration saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/bot/control")
async def control_bot(request: BotControlRequest):
    """Start or stop the bot"""
    try:
        bot = await get_bot(db)
        
        if request.action == "start":
            success = await bot.start()
            if success:
                return {"status": "success", "message": "Bot started"}
            else:
                detail = bot.last_error or "Failed to start bot"
                raise HTTPException(status_code=400, detail=detail)
        
        elif request.action == "stop":
            success = await bot.stop()
            if success:
                return {"status": "success", "message": "Bot stopped"}
            else:
                raise HTTPException(status_code=400, detail="Failed to stop bot")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/bot/status")
async def get_bot_status():
    """Get bot status"""
    try:
        bot = await get_bot(db)
        status = await bot.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/bot/sync", response_model=SyncResponse)
async def sync_bot_account():
    """Manually trigger account synchronization/cleanup"""
    try:
        bot = await get_bot(db)
        result = await bot.sync_account()

        if result.get('status') == 'error':
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to synchronize account'))

        message = (
            "Conta limpa - nenhuma ordem aberta." if result.get('found_orders') == 0
            else f"Limpeza concluída: {result.get('canceled_orders')} ordens canceladas de {result.get('found_orders')}."
        )

        return SyncResponse(
            status=result.get('status', 'unknown'),
            found_orders=result.get('found_orders', 0),
            canceled_orders=result.get('canceled_orders', 0),
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/trades")
async def get_trades(limit: int = 50):
    """Get trading history"""
    try:
        trades = await db.trades.find(
            {},
            {'_id': 0}
        ).sort('closed_at', -1).limit(limit).to_list(limit)
        
        return trades
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _build_performance_snapshot() -> Dict[str, Any]:
    """Assemble performance metrics with simple in-memory throttling."""
    global _performance_cache

    lock = await _get_performance_lock()
    async with lock:
        loop = asyncio.get_running_loop()
        now = loop.time()

        if _performance_cache["data"] is not None and (now - _performance_cache["ts"]) < _performance_cache_ttl:
            return _performance_cache["data"]

        trades = await db.trades.find(
            {},
            {"_id": 0}
        ).sort('closed_at', 1).to_list(1000)

        if not trades:
            snapshot = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'average_pnl': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'trades_by_date': []
            }
            _performance_cache = {"data": snapshot, "ts": now}
            return snapshot

        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in trades if t.get('pnl', 0) <= 0])

        pnls = [t.get('pnl', 0) for t in trades]
        total_pnl = sum(pnls)
        average_pnl = total_pnl / total_trades if total_trades > 0 else 0

        snapshot = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': round(total_pnl, 2),
            'average_pnl': round(average_pnl, 2),
            'best_trade': round(max(pnls), 2) if pnls else 0,
            'worst_trade': round(min(pnls), 2) if pnls else 0,
            'trades_by_date': trades
        }

        _performance_cache = {"data": snapshot, "ts": now}
        return snapshot


@api_router.get("/performance")
async def get_performance():
    """Get performance metrics"""
    try:
        return await _build_performance_snapshot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/stream")
async def stream_bot_updates(request: Request):
    """Server-Sent Events stream with bot status and performance snapshots."""

    async def event_generator():
        retry_delay = 5
        max_retry_delay = 30

        while True:
            if await request.is_disconnected():
                break

            try:
                bot = await get_bot(db)
                status = await bot.get_status()
                performance = await _build_performance_snapshot()
                payload = {
                    'type': 'snapshot',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': status,
                    'performance': performance
                }
                yield f"data: {json.dumps(payload, default=str)}\n\n"
                retry_delay = 5
            except Exception as exc:  # pragma: no cover - best effort streaming
                error_payload = {
                    'type': 'error',
                    'message': str(exc),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                yield f"data: {json.dumps(error_payload, default=str)}\n\n"
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
                continue

            await asyncio.sleep(int(os.environ.get('STREAM_REFRESH_INTERVAL', 5)))

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@api_router.get("/learning/stats")
async def get_learning_stats():
    """Get machine learning statistics and parameters"""
    try:
        bot = await get_bot(db)
        
        # Get current learned parameters
        params_doc = await db.learning_data.find_one({'type': 'parameters'})
        
        # Get all trade analyses
        analyses = await db.learning_data.find(
            {'type': 'trade_analysis'},
            {"_id": 0}
        ).sort('timestamp', -1).limit(100).to_list(100)
        
        # Calculate statistics
        if not params_doc:
            params = {
                'min_confidence_score': 0.6,
                'stop_loss_multiplier': 1.0,
                'take_profit_multiplier': 1.0,
                'position_size_multiplier': 1.0,
                'total_adjustments': 0
            }
        else:
            params = {
                'min_confidence_score': params_doc.get('min_confidence_score', 0.6),
                'stop_loss_multiplier': params_doc.get('stop_loss_multiplier', 1.0),
                'take_profit_multiplier': params_doc.get('take_profit_multiplier', 1.0),
                'position_size_multiplier': params_doc.get('position_size_multiplier', 1.0),
                'total_adjustments': params_doc.get('total_adjustments', 0),
                'last_updated': params_doc.get('timestamp', 'Never')
            }
        
        # Calculate win rate from analyses
        if analyses:
            total_analyzed = len(analyses)
            winners = len([a for a in analyses if a.get('won', False)])
            win_rate = (winners / total_analyzed * 100) if total_analyzed > 0 else 0
            
            # Average confidence scores
            avg_confidence = sum([a.get('ml_score', 0) for a in analyses]) / total_analyzed if total_analyzed > 0 else 0
            
            # Get adjustments history
            adjustments_history = [
                {
                    'timestamp': a.get('timestamp'),
                    'symbol': a.get('symbol'),
                    'adjustments': a.get('adjustments', [])
                }
                for a in analyses
                if a.get('adjustments')
            ]
        else:
            total_analyzed = 0
            win_rate = 0
            avg_confidence = 0
            adjustments_history = []
        
        return {
            'status': 'success',
            'current_parameters': params,
            'statistics': {
                'total_analyzed_trades': total_analyzed,
                'win_rate': round(win_rate, 2),
                'average_confidence_score': round(avg_confidence, 3),
                'total_parameter_adjustments': params['total_adjustments']
            },
            'recent_adjustments': adjustments_history[:10],  # Last 10 adjustments
            'is_learning': bot.is_running
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/shutdown")
async def shutdown_server():
    """Safely shutdown the backend server"""
    try:
        # First, stop the bot if running
        bot = await get_bot(db)
        if bot.is_running:
            logger.info("Stopping bot before server shutdown...")
            await bot.stop()
            await asyncio.sleep(2)  # Wait for bot to stop
        
        logger.info("Shutting down server...")
        
        # Schedule shutdown after response is sent
        asyncio.create_task(_shutdown_after_delay())
        
        return {"status": "success", "message": "Server shutting down safely"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _shutdown_after_delay():
    """Shutdown server after a short delay"""
    await asyncio.sleep(1)
    import os
    import signal
    os.kill(os.getpid(), signal.SIGTERM)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
