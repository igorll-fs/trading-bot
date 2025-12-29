"""
Rotas de Performance, Trades e Streaming.

Endpoints:
- GET /trades - Histórico de trades
- GET /performance - Métricas completas de performance
- GET /sparkline - Últimos 50 pontos PnL (para mini-charts)
- GET /realtime - Stats em tempo real (CPU, RAM, latency)
- GET /stream - SSE stream de updates
"""

import json
import asyncio
import os
import psutil
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["Performance"])

# Cache para realtime stats (update a cada 5s)
_realtime_cache: Dict[str, Any] = {"data": None, "ts": 0.0}
_realtime_cache_ttl = 5.0

# Cache para sparkline (update a cada 30s)
_sparkline_cache: Dict[str, Any] = {"data": None, "ts": 0.0}
_sparkline_cache_ttl = 30.0

# Cache de performance (throttle queries custosas)
_performance_cache: Dict[str, Any] = {"data": None, "ts": 0.0}
_performance_cache_ttl = float(os.environ.get('PERFORMANCE_CACHE_TTL', '5'))
_performance_lock: Optional[asyncio.Lock] = None


async def _get_performance_lock() -> asyncio.Lock:
    """Cria e retorna lock compartilhado para cache de performance."""
    global _performance_lock
    if _performance_lock is None:
        _performance_lock = asyncio.Lock()
    return _performance_lock


async def _build_performance_snapshot(db) -> Dict[str, Any]:
    """Monta métricas de performance com throttling em memória."""
    global _performance_cache

    lock = await _get_performance_lock()
    async with lock:
        loop = asyncio.get_running_loop()
        now = loop.time()

        if _performance_cache["data"] is not None and (now - _performance_cache["ts"]) < _performance_cache_ttl:
            return _performance_cache["data"]

        # Filtrar apenas trades reais (excluir simulados)
        trades = await db.trades.find(
            {"simulated": {"$ne": True}},
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
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'expectancy': 0,
                'max_drawdown': 0,
                'current_streak': 0,
                'streak_type': None,
                'roi': 0,
                'trades_by_date': []
            }
            _performance_cache = {"data": snapshot, "ts": now}
            return snapshot

        # Single-pass calculation for all metrics (otimizado de O(3n) para O(n))
        total_trades = len(trades)
        total_pnl = 0
        winning_trades = 0
        losing_trades = 0
        total_profits = 0
        total_losses = 0
        cumulative = 0
        peak = 0
        max_drawdown = 0
        pnls = []

        for trade in trades:
            pnl = trade.get('pnl', 0)
            pnls.append(pnl)
            total_pnl += pnl

            if pnl > 0:
                winning_trades += 1
                total_profits += pnl
            else:
                losing_trades += 1
                total_losses += abs(pnl)

            # Max drawdown calculation
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        average_pnl = total_pnl / total_trades if total_trades > 0 else 0
        profit_factor = total_profits / total_losses if total_losses > 0 else 0
        avg_win = total_profits / winning_trades if winning_trades > 0 else 0
        avg_loss = total_losses / losing_trades if losing_trades > 0 else 0
        winRate = winning_trades / total_trades if total_trades > 0 else 0
        expectancy = (winRate * avg_win) - ((1 - winRate) * avg_loss)
        
        # Streak atual (sequência de wins ou losses)
        current_streak = 0
        streak_type = None
        for trade in reversed(trades):
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                if streak_type is None:
                    streak_type = 'win'
                if streak_type == 'win':
                    current_streak += 1
                else:
                    break
            elif pnl < 0:
                if streak_type is None:
                    streak_type = 'loss'
                if streak_type == 'loss':
                    current_streak += 1
                else:
                    break
        
        # ROI
        initial_balance = 1000  # Considerando balance inicial padrão testnet
        roi = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0

        snapshot = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            'total_pnl': round(total_pnl, 2),
            'average_pnl': round(average_pnl, 2),
            'best_trade': round(max(pnls), 2) if pnls else 0,
            'worst_trade': round(min(pnls), 2) if pnls else 0,
            'profit_factor': round(profit_factor, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'expectancy': round(expectancy, 2),
            'max_drawdown': round(max_drawdown, 2),
            'current_streak': current_streak,
            'streak_type': streak_type,
            'roi': round(roi, 2),
            'trades_by_date': trades
        }

        _performance_cache = {"data": snapshot, "ts": now}
        return snapshot


def create_performance_router(db, get_bot_func):
    """Factory function para criar router com dependências injetadas."""
    
    @router.get("/trades")
    async def get_trades(limit: int = 50):
        """Retorna histórico de trades (apenas reais, exclui simulados)."""
        try:
            trades = await db.trades.find(
                {"simulated": {"$ne": True}},
                {'_id': 0}
            ).sort('closed_at', -1).limit(limit).to_list(limit)
            return trades
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/performance")
    async def get_performance():
        """Retorna métricas de performance."""
        try:
            return await _build_performance_snapshot(db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/sparkline")
    async def get_sparkline(points: int = 50):
        """
        Retorna últimos N pontos de PnL para mini-charts (sparklines).
        
        Formato: [{timestamp: ISO, value: float}, ...]
        Cache: 30 segundos
        
        Solicitado por: SessionB (msg_006) para dashboard modernização
        """
        global _sparkline_cache
        
        try:
            loop = asyncio.get_running_loop()
            now = loop.time()
            
            # Check cache
            if _sparkline_cache["data"] is not None and (now - _sparkline_cache["ts"]) < _sparkline_cache_ttl:
                return _sparkline_cache["data"]
            
            # Buscar trades reais ordenados por data (excluir simulados)
            trades = await db.trades.find(
                {"closed_at": {"$exists": True}, "simulated": {"$ne": True}},
                {"closed_at": 1, "pnl": 1, "_id": 0}
            ).sort("closed_at", -1).limit(points).to_list(points)
            
            # Formatar para sparkline
            sparkline_data = []
            cumulative_pnl = 0
            
            # Reverse para processar do mais antigo ao mais recente
            for trade in reversed(trades):
                cumulative_pnl += trade.get("pnl", 0)
                sparkline_data.append({
                    "timestamp": trade.get("closed_at", "").isoformat() if hasattr(trade.get("closed_at", ""), "isoformat") else str(trade.get("closed_at", "")),
                    "value": round(cumulative_pnl, 2),
                    "pnl": round(trade.get("pnl", 0), 2)
                })
            
            result = {
                "points": sparkline_data,
                "count": len(sparkline_data),
                "total_pnl": round(cumulative_pnl, 2),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            _sparkline_cache = {"data": result, "ts": now}
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao gerar sparkline: {str(e)}")
    
    @router.get("/realtime")
    async def get_realtime_stats():
        """
        Retorna estatísticas em tempo real do sistema.
        
        Formato: {cpu: float, ram: int, latency_ms: int, tpm: int, ...}
        Cache: 5 segundos
        
        Solicitado por: SessionB (msg_006) para dashboard monitoring
        """
        global _realtime_cache
        
        try:
            loop = asyncio.get_running_loop()
            now = loop.time()
            
            # Check cache
            if _realtime_cache["data"] is not None and (now - _realtime_cache["ts"]) < _realtime_cache_ttl:
                return _realtime_cache["data"]
            
            # CPU e RAM via psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            ram_used_mb = memory.used // (1024 * 1024)
            ram_total_mb = memory.total // (1024 * 1024)
            
            # API Latency (simular medição Binance)
            api_start = time.time()
            try:
                bot = await get_bot_func(db)
                if bot and hasattr(bot, 'client') and bot.client:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, bot.client.ping
                        ),
                        timeout=5.0
                    )
                latency_ms = int((time.time() - api_start) * 1000)
            except Exception:
                latency_ms = -1  # -1 indica erro de conexão
            
            # Trades per minute (últimos 5 minutos) - apenas reais
            five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
            recent_trades_count = await db.trades.count_documents({
                "closed_at": {"$gte": five_min_ago},
                "simulated": {"$ne": True}
            })
            tpm = round(recent_trades_count / 5, 1)  # Média por minuto
            
            # Status do bot
            bot = await get_bot_func(db)
            bot_running = bot.is_running if bot else False
            
            # Posições abertas
            positions_count = await db.positions.count_documents({})
            
            result = {
                "cpu": round(cpu_percent, 1),
                "ram_used_mb": ram_used_mb,
                "ram_total_mb": ram_total_mb,
                "ram_percent": round(memory.percent, 1),
                "latency_ms": latency_ms,
                "tpm": tpm,  # Trades per minute
                "bot_running": bot_running,
                "positions_open": positions_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            _realtime_cache = {"data": result, "ts": now}
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao obter stats: {str(e)}")
    
    @router.get("/stream")
    async def stream_bot_updates(request: Request):
        """Server-Sent Events stream com status do bot e performance."""

        async def event_generator():
            retry_delay = 5
            max_retry_delay = 30

            while True:
                if await request.is_disconnected():
                    break

                try:
                    bot = await get_bot_func(db)
                    status = await bot.get_status()
                    performance = await _build_performance_snapshot(db)
                    payload = {
                        'type': 'snapshot',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'status': status,
                        'performance': performance
                    }
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
                    retry_delay = 5
                except Exception as exc:
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
    
    return router
