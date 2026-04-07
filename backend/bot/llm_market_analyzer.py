"""
LLM Market Analyzer - Sistema Avançado de Análise de Mercado com IA

Características Profissionais:
- Análise de regime de mercado (trending/ranging/volatile)
- Ajuste dinâmico de parâmetros baseado em volatilidade
- Aprendizado com histórico de trades (feedback loop)
- Contexto macro (BTC dominance, correlações)
- Análise multi-timeframe

Hardware Target: Dell E7450 (i5-5300U, 12GB RAM)
"""

import asyncio
import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Regimes de mercado identificados"""

    BULL_TRENDING = "bull_trending"  # Alta clara, ride the trend
    BEAR_TRENDING = "bear_trending"  # Queda clara, cuidado
    RANGING = "ranging"  # Lateral, scalp
    HIGH_VOLATILITY = "high_volatility"  # Volátil, reduzir size
    LOW_VOLATILITY = "low_volatility"  # Calmo, pode aumentar size
    UNCERTAIN = "uncertain"  # Incerto, aguardar


@dataclass
class MarketContext:
    """Contexto completo do mercado para análise IA"""

    regime: MarketRegime
    volatility_percentile: float  # 0-100 (onde está a volatilidade atual)
    trend_strength: float  # 0-100
    btc_correlation: float  # -1 to 1
    recent_trades_winrate: float  # 0-100
    avg_holding_time_minutes: float
    current_drawdown: float  # 0-100

    def to_prompt_context(self) -> str:
        """Converte contexto para texto legível no prompt"""
        return f"""
CONTEXTO DE MERCADO:
- Regime: {self.regime.value.replace('_', ' ').title()}
- Volatilidade: {self.volatility_percentile:.0f}º percentil (0=calmo, 100=caótico)
- Força da Tendência: {self.trend_strength:.0f}/100
- Correlação com BTC: {self.btc_correlation:.2f}
- Win Rate Recente: {self.recent_trades_winrate:.1f}%
- Tempo Médio de Hold: {self.avg_holding_time_minutes:.0f} minutos
- Drawdown Atual: {self.current_drawdown:.1f}%
"""


@dataclass
class LLMTradeRecommendation:
    """Recomendação completa da IA para um trade"""

    action: str  # 'OPEN_LONG', 'SKIP', 'WAIT'
    confidence: float  # 0-1
    reasoning: str
    suggested_stop_multiplier: float  # Ex: 1.5 = 50% mais largo que padrão
    suggested_target_multiplier: float  # Ex: 2.0 = 2x o target padrão
    position_size_adjustment: float  # Ex: 0.5 = metade do size normal
    max_hold_time_minutes: Optional[int]  # Limite de tempo sugerido

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "stop_multiplier": self.suggested_stop_multiplier,
            "target_multiplier": self.suggested_target_multiplier,
            "size_adjustment": self.position_size_adjustment,
            "max_hold_time": self.max_hold_time_minutes,
        }


class LLMMarketAnalyzer:
    """
    Analisador de mercado profissional com IA.

    ✅ Capacidades:
    - Identifica regime de mercado automaticamente
    - Ajusta stops/targets baseado em volatilidade
    - Aprende com histórico de trades (feedback loop)
    - Analisa contexto macro (BTC, correlações)
    - Recomenda ajustes de posição em tempo real

    🎯 Filosofia:
    - Em alta volatilidade: stops mais largos, sizes menores
    - Em baixa volatilidade: stops mais apertados, sizes normais
    - Em tendência forte: ride longer, targets maiores
    - Em ranging: quick scalps, targets menores
    """

    def __init__(
        self,
        model: str = "mistral",
        enabled: bool = True,
        max_workers: int = 1,
        timeout: int = 15,
    ):
        self.enabled = enabled and os.getenv("LLM_ENABLED", "true").lower() == "true"
        self.model = model
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Cache de análises de mercado (TTL 60s - mais longo que trades individuais)
        self.market_context_cache: Optional[Tuple[MarketContext, float]] = None
        self.market_cache_ttl = 60

        # Histórico de trades para feedback loop
        self._trade_history: List[Dict[str, Any]] = []
        self.max_history = 50  # Últimos 50 trades

        # Métricas
        self.metrics = {
            "market_analyses": 0,
            "trade_recommendations": 0,
            "avg_latency_ms": 0.0,
            "regime_changes": 0,
        }

        self.loaded = False
        self.last_error: Optional[str] = None

        if self.enabled:
            self._verify_ollama()

    def _verify_ollama(self) -> None:
        """Verifica Ollama e carrega modelo"""
        try:
            import ollama

            response = ollama.list()
            models = [m.get("name", "") for m in response.get("models", [])]

            if self.model not in models and f"{self.model}:latest" not in models:
                logger.warning("[LLM Market] Modelo '%s' não encontrado, puxando...", self.model)
                ollama.pull(self.model)

            self.loaded = True
            logger.info("[LLM Market] ✅ Sistema de análise de mercado pronto")
        except Exception as e:
            logger.error("[LLM Market] ❌ Erro: %s", e)
            self.enabled = False
            self.last_error = str(e)

    def add_trade_to_history(self, trade_result: Dict[str, Any]) -> None:
        """
        Adiciona resultado de trade ao histórico para aprendizado.

        Args:
            trade_result: {
                'symbol': str,
                'entry_price': float,
                'exit_price': float,
                'pnl_percent': float,
                'hold_time_minutes': int,
                'market_regime': str,
                'setup_used': str,
                'exit_reason': str
            }
        """
        self._trade_history.append({**trade_result, "timestamp": datetime.now().isoformat()})

        # Manter apenas últimos N trades
        if len(self._trade_history) > self.max_history:
            self._trade_history = self._trade_history[-self.max_history :]

        logger.info(
            "[LLM Market] Trade adicionado ao histórico: %s %.2f%% em %dm",
            trade_result["symbol"],
            trade_result["pnl_percent"],
            trade_result["hold_time_minutes"],
        )

    def _get_performance_summary(self) -> str:
        """Gera resumo de performance dos últimos trades"""
        if not self._trade_history:
            return "Sem histórico de trades ainda."

        recent = self._trade_history[-20:]  # Últimos 20
        wins = sum(1 for t in recent if t["pnl_percent"] > 0)
        losses = len(recent) - wins
        winrate = (wins / len(recent)) * 100 if recent else 0
        avg_win = sum(t["pnl_percent"] for t in recent if t["pnl_percent"] > 0) / max(wins, 1)
        avg_loss = sum(t["pnl_percent"] for t in recent if t["pnl_percent"] < 0) / max(losses, 1)

        return f"""
PERFORMANCE RECENTE (últimos {len(recent)} trades):
- Win Rate: {winrate:.1f}% ({wins}W / {losses}L)
- Avg Win: +{avg_win:.2f}%
- Avg Loss: {avg_loss:.2f}%
- R/R Ratio: {abs(avg_win/avg_loss):.2f}x
"""

    async def analyze_market_regime(
        self,
        btc_data: Dict[str, Any],
        alt_data: Dict[str, Any],
        recent_volatility: float,
        recent_trades: List[Dict[str, Any]],
    ) -> MarketContext:
        """
        Analisa regime completo do mercado com IA.

        Args:
            btc_data: Dados de BTC (price, change_24h, volume, etc)
            alt_data: Dados da altcoin sendo analisada
            recent_volatility: ATR ou volatility measure recente
            recent_trades: Últimos trades executados

        Returns:
            MarketContext com análise completa
        """
        if not self.enabled:
            return self._get_default_context()

        # Check cache
        if self.market_context_cache:
            context, timestamp = self.market_context_cache
            if time.time() - timestamp < self.market_cache_ttl:
                return context

        try:
            self.metrics["market_analyses"] += 1
            start = time.perf_counter()

            # Calcular métricas
            winrate = (
                (
                    sum(1 for t in recent_trades if t.get("pnl_percent", 0) > 0)
                    / len(recent_trades)
                    * 100
                )
                if recent_trades
                else 0
            )
            avg_hold = (
                sum(t.get("hold_time_minutes", 0) for t in recent_trades) / len(recent_trades)
                if recent_trades
                else 30
            )
            drawdown = abs(min((t.get("pnl_percent", 0) for t in recent_trades), default=0))

            # Construir prompt especializado
            prompt = self._build_market_analysis_prompt(
                btc_data, alt_data, recent_volatility, winrate, avg_hold, drawdown
            )

            # Executar análise
            loop = asyncio.get_running_loop()
            raw_response = await loop.run_in_executor(self.executor, self._sync_analyze, prompt)

            # Parse resposta
            context = self._parse_market_regime(
                raw_response, recent_volatility, winrate, avg_hold, drawdown
            )

            # Cache
            self.market_context_cache = (context, time.time())

            latency_ms = (time.perf_counter() - start) * 1000
            self.metrics["avg_latency_ms"] = latency_ms

            logger.info(
                "[LLM Market] Regime identificado: %s (%.0fms)", context.regime.value, latency_ms
            )

            return context

        except Exception as e:
            logger.error("[LLM Market] Erro em análise de regime: %s", e)
            return self._get_default_context()

    def _build_market_analysis_prompt(
        self,
        btc_data: Dict[str, Any],
        alt_data: Dict[str, Any],
        volatility: float,
        winrate: float,
        avg_hold: float,
        drawdown: float,
    ) -> str:
        """Constrói prompt especializado para análise de mercado"""

        performance = self._get_performance_summary()

        prompt = f"""Você é um trader profissional quantitativo especializado em crypto. Analise o regime atual do mercado.

DADOS DE BTC (líder de mercado):
- Preço: ${btc_data.get('price', 0):,.2f}
- Mudança 24h: {btc_data.get('change_24h', 0):+.2f}%
- Volume 24h: ${btc_data.get('volume_24h', 0):,.0f}
- RSI: {btc_data.get('rsi', 50):.1f}

DADOS DA ALTCOIN:
- Símbolo: {alt_data.get('symbol', 'UNKNOWN')}
- Preço: ${alt_data.get('price', 0):.6f}
- Mudança 24h: {alt_data.get('change_24h', 0):+.2f}%
- Volume Ratio: {alt_data.get('volume_ratio', 1.0):.2f}x
- Volatilidade (ATR): {volatility:.6f}

{performance}

DRAWDOWN ATUAL: {drawdown:.1f}%

PERGUNTA: Qual o regime de mercado atual e como devemos operar?

RESPONDA com UMA linha no formato:
[REGIME] | Stop:[X]x | Target:[Y]x | Size:[Z]% | Razão

Regimes possíveis:
- BULL_TRENDING: Alta clara, ride the trend
- BEAR_TRENDING: Queda, cuidado
- RANGING: Lateral, scalp rápido
- HIGH_VOLATILITY: Caótico, reduzir risco
- LOW_VOLATILITY: Calmo, pode aumentar size

Exemplos:
BULL_TRENDING | Stop:1.2x | Target:2.5x | Size:100% | BTC rallying + alt volume strong
HIGH_VOLATILITY | Stop:2.0x | Target:1.5x | Size:50% | ATR elevated + erratic price action
"""
        return prompt

    def _parse_market_regime(
        self, raw_response: str, volatility: float, winrate: float, avg_hold: float, drawdown: float
    ) -> MarketContext:
        """Parse resposta da IA sobre regime de mercado"""
        try:
            # Parse formato: "REGIME | Stop:Xx | Target:Yx | Size:Z% | Razão"
            parts = raw_response.strip().split("|")

            regime_str = parts[0].strip().upper()
            regime = MarketRegime.UNCERTAIN

            for r in MarketRegime:
                if r.value.upper() in regime_str or r.name in regime_str:
                    regime = r
                    break

            # Calcular volatility percentile (0-100)
            # ATR típico: 0.0001 (low) to 0.001 (high) para crypto
            vol_percentile = min(100, (volatility / 0.001) * 100)

            # Trend strength baseado no regime
            trend_map = {
                MarketRegime.BULL_TRENDING: 85,
                MarketRegime.BEAR_TRENDING: 80,
                MarketRegime.RANGING: 30,
                MarketRegime.HIGH_VOLATILITY: 50,
                MarketRegime.LOW_VOLATILITY: 40,
                MarketRegime.UNCERTAIN: 25,
            }
            trend_strength = trend_map.get(regime, 50)

            return MarketContext(
                regime=regime,
                volatility_percentile=vol_percentile,
                trend_strength=trend_strength,
                btc_correlation=0.7,  # Placeholder (calcular com dados reais)
                recent_trades_winrate=winrate,
                avg_holding_time_minutes=avg_hold,
                current_drawdown=drawdown,
            )

        except Exception as e:
            logger.warning("[LLM Market] Erro ao fazer parse regime: %s", e)
            return self._get_default_context()

    async def recommend_trade(
        self,
        symbol: str,
        technical_score: int,
        indicators: Dict[str, float],
        market_context: MarketContext,
    ) -> LLMTradeRecommendation:
        """
        Gera recomendação profissional de trade baseada em contexto completo.

        Returns:
            LLMTradeRecommendation com ajustes adaptativos
        """
        if not self.enabled:
            return self._get_default_recommendation()

        try:
            self.metrics["trade_recommendations"] += 1

            prompt = self._build_trade_recommendation_prompt(
                symbol, technical_score, indicators, market_context
            )

            loop = asyncio.get_running_loop()
            raw_response = await loop.run_in_executor(self.executor, self._sync_analyze, prompt)

            recommendation = self._parse_trade_recommendation(raw_response, market_context)

            logger.info(
                "[LLM Market] %s: %s (conf: %.0f%%, size: %.0f%%, stop: %.1fx)",
                symbol,
                recommendation.action,
                recommendation.confidence * 100,
                recommendation.position_size_adjustment * 100,
                recommendation.suggested_stop_multiplier,
            )

            return recommendation

        except Exception as e:
            logger.error("[LLM Market] Erro em recomendação: %s", e)
            return self._get_default_recommendation()

    def _build_trade_recommendation_prompt(
        self, symbol: str, tech_score: int, indicators: Dict[str, float], context: MarketContext
    ) -> str:
        """Constrói prompt para recomendação de trade"""

        performance = self._get_performance_summary()

        prompt = f"""Você é um trader profissional. Avalie este setup de trade:

{context.to_prompt_context()}

SETUP TÉCNICO:
- Símbolo: {symbol}
- Score Técnico: {tech_score}/100
- RSI: {indicators.get('rsi', 50):.1f}
- MACD Hist: {indicators.get('macd_hist', 0):.6f}
- ATR: {indicators.get('atr', 0):.6f}
- EMA 50 vs 200: {'Bullish' if indicators.get('ema_50', 0) > indicators.get('ema_200', 0) else 'Bearish'}
- Volume Ratio: {indicators.get('volume_ratio', 1.0):.2f}x

{performance}

DECISÃO: Devemos entrar neste trade? Como ajustar parâmetros?

RESPONDA no formato (UMA linha):
[ACTION] | Conf:[X]% | Stop:[Y]x | Target:[Z]x | Size:[W]% | Hold:[M]min | Razão

Actions: OPEN_LONG, SKIP, WAIT
Conf: 0-100%
Stop: multiplicador do stop padrão (ex: 1.5 = 50% mais largo)
Target: multiplicador do target padrão (ex: 2.0 = 2x maior)
Size: % do size normal (ex: 50 = metade)
Hold: tempo máximo em minutos

Exemplo:
OPEN_LONG | Conf:85% | Stop:1.3x | Target:2.0x | Size:80% | Hold:45min | Strong trend + low drawdown
SKIP | Conf:70% | Stop:1.0x | Target:1.0x | Size:0% | Hold:0min | High volatility + poor recent performance
"""
        return prompt

    def _parse_trade_recommendation(
        self, raw_response: str, context: MarketContext
    ) -> LLMTradeRecommendation:
        """Parse recomendação de trade da IA"""
        try:
            # Default values
            action = "SKIP"
            confidence = 0.5
            stop_mult = 1.0
            target_mult = 1.0
            size_adj = 1.0
            hold_time = None
            reasoning = "Default recommendation"

            # Parse: "ACTION | Conf:X% | Stop:Yx | Target:Zx | Size:W% | Hold:Mmin | Razão"
            parts = raw_response.strip().split("|")

            if len(parts) >= 2:
                # Action
                action_str = parts[0].strip().upper()
                if "OPEN" in action_str or "LONG" in action_str:
                    action = "OPEN_LONG"
                elif "SKIP" in action_str:
                    action = "SKIP"
                elif "WAIT" in action_str:
                    action = "WAIT"

                # Parse outros campos
                for part in parts[1:]:
                    part = part.strip()
                    if "conf:" in part.lower():
                        confidence = float(part.split(":")[1].replace("%", "")) / 100
                    elif "stop:" in part.lower():
                        stop_mult = float(part.split(":")[1].replace("x", ""))
                    elif "target:" in part.lower():
                        target_mult = float(part.split(":")[1].replace("x", ""))
                    elif "size:" in part.lower():
                        size_adj = float(part.split(":")[1].replace("%", "")) / 100
                    elif "hold:" in part.lower():
                        hold_time = int(part.split(":")[1].replace("min", ""))
                    else:
                        reasoning = part

            # Validações
            confidence = max(0.0, min(1.0, confidence))
            stop_mult = max(0.5, min(3.0, stop_mult))
            target_mult = max(0.5, min(5.0, target_mult))
            size_adj = max(0.25, min(1.0, size_adj))

            return LLMTradeRecommendation(
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                suggested_stop_multiplier=stop_mult,
                suggested_target_multiplier=target_mult,
                position_size_adjustment=size_adj,
                max_hold_time_minutes=hold_time,
            )

        except Exception as e:
            logger.warning("[LLM Market] Erro ao fazer parse recomendação: %s", e)
            return self._get_default_recommendation()

    def _sync_analyze(self, prompt: str) -> str:
        """Executa análise síncrona no Ollama"""
        try:
            import ollama

            if not self.loaded or not self.enabled:
                return "UNCERTAIN | Default response"

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={
                    "num_predict": 100,  # Resposta mais longa para análise
                    "temperature": 0.2,  # Muito determinístico
                    "repeat_penalty": 1.2,
                    "top_p": 0.85,
                },
            )

            return response.get("response", "UNCERTAIN | Empty response")

        except Exception as e:
            logger.error("[LLM Market] Erro Ollama: %s", e)
            return "UNCERTAIN | Error"

    def _get_default_context(self) -> MarketContext:
        """Retorna contexto padrão quando LLM não disponível"""
        return MarketContext(
            regime=MarketRegime.UNCERTAIN,
            volatility_percentile=50,
            trend_strength=50,
            btc_correlation=0.5,
            recent_trades_winrate=50,
            avg_holding_time_minutes=30,
            current_drawdown=0,
        )

    def _get_default_recommendation(self) -> LLMTradeRecommendation:
        """Retorna recomendação padrão quando LLM não disponível"""
        return LLMTradeRecommendation(
            action="SKIP",
            confidence=0.5,
            reasoning="LLM not available - using defaults",
            suggested_stop_multiplier=1.0,
            suggested_target_multiplier=1.0,
            position_size_adjustment=1.0,
            max_hold_time_minutes=None,
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do analisador"""
        return {
            **self.metrics,
            "enabled": self.enabled,
            "loaded": self.loaded,
            "trade_history_size": len(self._trade_history),
            "last_error": self.last_error,
        }

    async def is_available(self) -> bool:
        """Verifica se analisador está disponível"""
        return self.enabled and self.loaded


# Singleton instance
_market_analyzer: Optional[LLMMarketAnalyzer] = None


def get_market_analyzer() -> LLMMarketAnalyzer:
    """Retorna instância singleton do analisador de mercado"""
    global _market_analyzer
    if _market_analyzer is None:
        _market_analyzer = LLMMarketAnalyzer()
    return _market_analyzer
