"""
Rotas de Health Check e Diagnósticos.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter(tags=["Health"])


async def get_health_status(db, get_bot_func) -> Dict[str, Any]:
    """
    Verifica status de saúde dos serviços.
    Retorna: MongoDB, Binance API, Bot status.
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
            health["services"]["binance"] = {
                "status": "ok", 
                "testnet": binance_manager.use_testnet
            }
        else:
            health["services"]["binance"] = {"status": "not_initialized"}
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["binance"] = {"status": "error", "message": str(e)[:100]}
        health["status"] = "degraded"
    
    # Check Bot
    try:
        bot = await get_bot_func(db)
        health["services"]["bot"] = {
            "status": "ok",
            "is_running": bot.is_running,
            "open_positions": len(bot.positions),
        }
    except Exception as e:
        health["services"]["bot"] = {"status": "error", "message": str(e)[:100]}
        health["status"] = "degraded"
    
    return health


def create_health_router(db, get_bot_func, sanitize_config_func):
    """Factory function para criar router com dependências injetadas."""
    
    @router.get("/health")
    async def health_check():
        """
        Health check completo com verificação de todos os serviços.
        """
        return await get_health_status(db, get_bot_func)
    
    @router.get("/healthz")
    async def healthz():
        """Lightweight healthcheck (não toca serviços externos)."""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    
    @router.get("/diagnostics")
    async def diagnostics():
        """Snapshot de configuração (sem segredos), posições e último sizing."""
        from bot.config import load_bot_config
        
        try:
            config = await load_bot_config(db)
            bot = await get_bot_func(db)
            status = await bot.get_status()
            return {
                "config": sanitize_config_func(config),
                "positions_open": len(status.get("positions", []) if isinstance(status, dict) else []),
                "is_running": status.get("is_running") if isinstance(status, dict) else False,
                "balance": status.get("balance") if isinstance(status, dict) else 0,
                "last_risk_snapshot": getattr(bot, "last_risk_snapshot", None),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
