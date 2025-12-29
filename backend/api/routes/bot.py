"""
Rotas de Controle do Bot.
"""

import asyncio
import os
import signal
import logging

from fastapi import APIRouter, HTTPException, Request

from api.models import BotControlRequest, SyncResponse
from api.rate_limiting import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Bot"])


def create_bot_router(db, get_bot_func):
    """Factory function para criar router com dependências injetadas."""
    
    @router.post("/bot/control")
    @limiter.limit("10/minute")
    async def control_bot(request: Request, body: BotControlRequest):
        """Inicia ou para o bot."""
        try:
            bot = await get_bot_func(db)
            
            if body.action == "start":
                success = await bot.start()
                if success:
                    return {"status": "success", "message": "Bot started"}
                else:
                    detail = bot.last_error or "Failed to start bot"
                    raise HTTPException(status_code=400, detail=detail)
            
            elif body.action == "stop":
                success = await bot.stop()
                if success:
                    return {"status": "success", "message": "Bot stopped"}
                else:
                    raise HTTPException(status_code=400, detail="Failed to stop bot")
            
            else:
                raise HTTPException(status_code=400, detail="Invalid action")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/bot/status")
    @limiter.limit("60/minute")
    async def get_bot_status(request: Request):
        """Retorna status atual do bot."""
        try:
            bot = await get_bot_func(db)
            status = await bot.get_status()
            return status
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/bot/sync", response_model=SyncResponse)
    @limiter.limit("5/minute")
    async def sync_bot_account(request: Request):
        """Sincroniza/limpa conta manualmente."""
        try:
            bot = await get_bot_func(db)
            result = await bot.sync_account()

            if result.get('status') == 'error':
                raise HTTPException(
                    status_code=500, 
                    detail=result.get('error', 'Failed to synchronize account')
                )

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
    
    @router.post("/shutdown")
    @limiter.limit("2/minute")
    async def shutdown_server(request: Request):
        """Desliga o servidor de forma segura."""
        try:
            bot = await get_bot_func(db)
            if bot.is_running:
                logger.info("Stopping bot before server shutdown...")
                await bot.stop()
                await asyncio.sleep(2)
            
            logger.info("Shutting down server...")
            asyncio.create_task(_shutdown_after_delay())
            
            return {"status": "success", "message": "Server shutting down safely"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return router


async def _shutdown_after_delay():
    """Desliga o servidor após um curto delay."""
    await asyncio.sleep(1)
    os.kill(os.getpid(), signal.SIGTERM)
