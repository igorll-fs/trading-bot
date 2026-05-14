"""
Rotas da API para métricas do LLM Analyzer (Ollama).
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request

from api.rate_limiting import limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["LLM"])


def create_llm_router(db, get_bot_func):
    """Factory function para criar router com dependências injetadas."""

    @router.get("/llm/status")
    @limiter.limit("60/minute")
    async def get_llm_status(request: Request):
        """
        Retorna status e métricas do LLM Analyzer (Ollama).

        Resposta inclui:
        - enabled: Se LLM está ativado
        - available: Se Ollama está rodando e acessível
        - metrics: Estatísticas de uso (requests, cache, latência)
        - last_analysis: Última análise realizada (se disponível)
        """
        try:
            bot = await get_bot_func(db)

            # Verificar se bot tem llm_analyzer
            llm_analyzer = getattr(bot, "llm_analyzer", None)

            if llm_analyzer is None:
                return {
                    "enabled": False,
                    "available": False,
                    "reason": "LLM Analyzer não inicializado no bot",
                    "metrics": {
                        "requests_total": 0,
                        "cache_hits": 0,
                        "cache_hit_rate": 0.0,
                        "avg_latency_ms": 0,
                    },
                    "last_analysis": None,
                }

            # Obter métricas do LLMAnalyzer
            try:
                metrics = llm_analyzer.get_metrics()
                is_available = await llm_analyzer.is_available()

                # Formatar última análise se disponível
                last_analysis = None
                if hasattr(llm_analyzer, "_last_analysis") and llm_analyzer._last_analysis:
                    analysis = llm_analyzer._last_analysis
                    last_analysis = {
                        "opinion": analysis.get("opinion", "NEUTRAL"),
                        "confidence": analysis.get("confidence", 0.0),
                        "reasoning": analysis.get("reasoning", ""),
                        "symbol": analysis.get("symbol", ""),
                        "timestamp": analysis.get(
                            "timestamp", datetime.now(UTC).isoformat()
                        ),
                    }

                return {
                    "enabled": True,
                    "available": is_available,
                    "metrics": {
                        "requests_total": metrics.get("requests_total", 0),
                        "cache_hits": metrics.get("cache_hits", 0),
                        "cache_hit_rate": metrics.get("cache_hit_rate", 0.0),
                        "avg_latency_ms": metrics.get("avg_latency_ms", 0),
                    },
                    "last_analysis": last_analysis,
                }

            except AttributeError as e:
                logger.warning(f"LLMAnalyzer não tem método get_metrics(): {e}")
                return {
                    "enabled": True,
                    "available": False,
                    "reason": "LLMAnalyzer sem suporte a métricas (versão antiga?)",
                    "metrics": {
                        "requests_total": 0,
                        "cache_hits": 0,
                        "cache_hit_rate": 0.0,
                        "avg_latency_ms": 0,
                    },
                    "last_analysis": None,
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting LLM status: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from None

    @router.get("/llm/market-analyzer/status")
    @limiter.limit("60/minute")
    async def get_market_analyzer_status(request: Request):
        """
        Retorna status e métricas do LLM Market Analyzer (sistema avançado).

        Resposta inclui:
        - enabled: Se Market Analyzer está ativado
        - available: Se Ollama está rodando e acessível
        - metrics: Estatísticas de uso
        - recent_analyses: Últimas análises de regime
        - trade_history_size: Quantidade de trades no histórico de aprendizado
        """
        try:
            bot = await get_bot_func(db)

            # Verificar se bot tem market_analyzer
            market_analyzer = getattr(bot, "market_analyzer", None)

            if market_analyzer is None:
                return {
                    "enabled": False,
                    "available": False,
                    "reason": "Market Analyzer não inicializado no bot",
                    "metrics": {},
                    "recent_analyses": [],
                    "trade_history_size": 0,
                }

            # Obter status e métricas
            try:
                is_available = await market_analyzer.is_available()
                metrics = market_analyzer.get_metrics()

                # Obter informações do histórico
                trade_history_size = len(market_analyzer._trade_history)

                # Últimas análises (se disponíveis)
                recent_analyses = []
                if (
                    hasattr(market_analyzer, "_last_market_context")
                    and market_analyzer._last_market_context
                ):
                    ctx = market_analyzer._last_market_context
                    recent_analyses.append(
                        {
                            "regime": ctx.regime.value if hasattr(ctx, "regime") else "unknown",
                            "volatility_percentile": (
                                ctx.volatility_percentile
                                if hasattr(ctx, "volatility_percentile")
                                else 0
                            ),
                            "trend_strength": (
                                ctx.trend_strength if hasattr(ctx, "trend_strength") else 0
                            ),
                            "cached": True,
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )

                return {
                    "enabled": True,
                    "available": is_available,
                    "metrics": {
                        "market_analyses": metrics.get("market_analyses", 0),
                        "trade_recommendations": metrics.get("trade_recommendations", 0),
                        "avg_latency_ms": metrics.get("avg_latency_ms", 0),
                    },
                    "recent_analyses": recent_analyses,
                    "trade_history_size": trade_history_size,
                }

            except Exception as e:
                logger.warning(f"Erro ao obter métricas do Market Analyzer: {e}")
                return {
                    "enabled": True,
                    "available": False,
                    "reason": f"Erro: {e!s}",
                    "metrics": {},
                    "recent_analyses": [],
                    "trade_history_size": 0,
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting Market Analyzer status: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from None

    return router
