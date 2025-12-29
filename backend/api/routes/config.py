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
    
    @router.get("/config")
    async def get_config():
        """Retorna configuração atual do bot."""
        try:
            config = await load_bot_config(db)
            return config.to_public_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
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
