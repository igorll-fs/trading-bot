"""
Rotas de Configuração do Bot.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from api.models import ConfigModel
from bot.config import BotConfig, load_bot_config, save_bot_config
from pydantic import BaseModel

router = APIRouter(tags=["Config"])


class PartialConfigModel(BaseModel):
    """Modelo para atualização parcial de configuração."""
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    max_positions: Optional[int] = None
    risk_percentage: Optional[float] = None
    leverage: Optional[int] = None
    balance_cache_ttl: Optional[float] = None
    observation_alert_interval: Optional[float] = None
    risk_use_position_cap: Optional[bool] = None
    daily_drawdown_limit_pct: Optional[float] = None
    weekly_drawdown_limit_pct: Optional[float] = None
    selector_min_quote_volume: Optional[float] = None
    selector_max_spread_percent: Optional[float] = None
    strategy_min_signal_strength: Optional[int] = None


def create_config_router(db, get_bot_func):
    """Factory function para criar router com dependências injetadas."""

    @router.get("/config/runtime")
    async def get_runtime_config():
        """Retorna config efetiva (DB + env vars) com parâmetros avançados."""
        try:
            import os
            config = await load_bot_config(db)
            base = config.to_public_dict()
            # Parâmetros runtime do .env (fonte da verdade para tuning avançado)
            base["api_latency_threshold"] = float(os.getenv("API_LATENCY_THRESHOLD", "2.0"))
            base["learning_min_trades"] = int(os.getenv("LEARNING_MIN_TRADES", "15"))
            base["learning_min_confidence"] = float(os.getenv("LEARNING_MIN_CONFIDENCE", "0.50"))
            base["symbol_sl_cooldown_minutes"] = int(os.getenv("SYMBOL_SL_COOLDOWN_MINUTES", "0"))
            base["risk_max_hold_hours"] = int(os.getenv("RISK_MAX_HOLD_HOURS", "4"))
            base["llm_risk_advisor_enabled"] = os.getenv("LLM_RISK_ADVISOR_ENABLED", "false").lower() == "true"
            base["trading_time_filter"] = os.getenv("TRADING_TIME_FILTER", "false").lower() == "true"
            base["capital_inicial"] = float(os.getenv("CAPITAL_INICIAL", "1000.0"))
            base["use_testnet"] = os.getenv("USE_TESTNET", "true").lower() == "true"
            base["paper_trade"] = os.getenv("PAPER_TRADE", "false").lower() == "true"
            return base
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/config")
    async def get_config():
        """Retorna configuração atual do bot."""
        try:
            config = await load_bot_config(db)
            return config.to_public_dict()
        except Exception as e:
            error_str = str(e)
            # Detectar erro de conexão MongoDB e retornar mensagem amigável
            if "10061" in error_str or "ServerSelectionTimeoutError" in error_str or "connection" in error_str.lower():
                raise HTTPException(
                    status_code=503,
                    detail="MongoDB não está disponível. Verifique se o serviço está rodando na porta 27017."
                )
            raise HTTPException(status_code=500, detail=error_str[:200])
    
    @router.post("/config")
    async def save_config(config: ConfigModel):
        """Salva configuração do bot e reinicializa com novos valores."""
        try:
            bot_config = BotConfig.from_mapping(config.model_dump())
            await save_bot_config(db, bot_config)

            # Reinicializa bot com nova config
            bot = await get_bot_func(db)
            await bot.initialize(bot_config)
            
            return {"status": "success", "message": "Configuration saved"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.patch("/config")
    async def update_config(partial_config: PartialConfigModel):
        """Atualiza parcialmente a configuração do bot."""
        try:
            # Carrega config atual
            current_config = await load_bot_config(db)
            current_dict = current_config.to_document()
            
            # Aplica apenas os campos que foram enviados (não-None)
            updates = {k: v for k, v in partial_config.model_dump().items() if v is not None}
            
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            current_dict.update(updates)
            
            # Cria nova config e salva
            bot_config = BotConfig.from_mapping(current_dict)
            await save_bot_config(db, bot_config)
            
            # Reinicializa bot com nova config
            bot = await get_bot_func(db)
            await bot.initialize(bot_config)
            
            return {
                "status": "success", 
                "message": "Configuration updated",
                "updated_fields": list(updates.keys())
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
