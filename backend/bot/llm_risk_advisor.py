"""
LLM Risk Advisor - Sistema Inteligente de Ajuste de Risco com Ollama

Implementa 5 funcionalidades avançadas:
1. Adaptive Stop-Loss baseado em ATR + volatilidade
2. Position Sizing inteligente baseado em confiança do setup
3. Análise de sentimento pré-trade (evita eventos de risco)
4. Reasoning explicativo quando não entra em trade
5. Regime adaptativo com feedback (aprende sozinho)

Hardware Target: Dell E7450 (i5-5300U, 12GB RAM)
"""

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Import telegram notifier para enviar decisões
try:
    from bot.telegram_client import telegram_notifier

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("Telegram notifier not available - AI decisions won't be sent")


@dataclass
class AdaptiveStopLoss:
    """Resultado do cálculo de stop-loss adaptativo"""

    stop_loss_price: float
    stop_multiplier: float  # Ex: 2.3 (2.3x ATR)
    reasoning: str
    confidence: float  # 0-1
    volatility_adjusted: bool


@dataclass
class IntelligentPositionSize:
    """Ajuste inteligente de position size"""

    size_multiplier: float  # Ex: 1.5 = 150% do size base, 0.7 = 70%
    confidence_score: int  # 0-10
    reasoning: str
    risk_flags: list[str]  # Alertas de risco


@dataclass
class PreTradeAnalysis:
    """Análise pré-trade com sentimento"""

    should_enter: bool
    sentiment: str  # 'BULLISH', 'NEUTRAL', 'BEARISH', 'CAUTION'
    risk_events: list[str]  # Eventos de risco detectados
    reasoning: str
    urgency: str  # 'IMMEDIATE', 'WAIT_1H', 'WAIT_4H', 'SKIP'


@dataclass
class SkipReasoning:
    """Explicação detalhada de por que não entrou"""

    primary_reason: str
    contributing_factors: list[str]
    suggestion: str
    next_check_in_minutes: int


@dataclass
class RegimeAdaptation:
    """Ajustes adaptativos baseados em performance recente"""

    current_regime: str  # 'trending', 'ranging', 'volatile', 'uncertain'
    score_threshold_adjustment: int  # Ex: +10 = mais rigoroso, -5 = menos
    stop_multiplier_adjustment: float  # Ex: 1.2 = stops 20% mais largos
    size_adjustment: float  # Ex: 0.8 = tamanho 80% do normal
    reasoning: str
    win_rate_last_10: float
    should_trade: bool


class LLMRiskAdvisor:
    """
    Sistema avançado de gestão de risco com IA.

    ✅ Funcionalidades:
    - Stop-loss dinâmico ajustado por IA
    - Position sizing inteligente
    - Análise de sentimento pré-trade
    - Explicações claras quando não opera
    - Auto-adaptação baseada em resultados

    🎯 Filosofia:
    - Defensivo: Preservação de capital > Lucro
    - Explicável: Toda decisão tem justificativa clara
    - Adaptativo: Melhora sozinho com feedback
    """

    def __init__(
        self,
        model: str = "mistral",
        enabled: bool = True,
        ollama_host: str = "http://localhost:11434",
        timeout: int = 8,
        cache_ttl: int = 60,
    ):
        """
        Inicializa o LLM Risk Advisor.

        Args:
            model: Modelo Ollama (default: mistral)
            enabled: Habilita IA (pode desabilitar via env)
            ollama_host: URL do servidor Ollama
            timeout: Timeout em segundos
            cache_ttl: TTL do cache em segundos
        """
        self.enabled = enabled and os.getenv("LLM_RISK_ADVISOR_ENABLED", "true").lower() == "true"
        self.model = model
        self.ollama_host = ollama_host
        self.timeout = timeout

        # Thread pool para não bloquear event loop
        self.executor = ThreadPoolExecutor(max_workers=1)

        # Cache de análises recentes
        self.cache: dict[str, tuple[any, datetime]] = {}
        self.cache_ttl = cache_ttl

        # Histórico de adaptação (últimos 20 trades)
        self.trade_history: list[dict] = []
        self.max_history = 20

        # Métricas
        self.metrics = {
            "requests_total": 0,
            "cache_hits": 0,
            "ollama_timeouts": 0,
            "adaptations_made": 0,
        }

        logger.info(
            f"[LLM Risk Advisor] Initialized - Model: {model}, "
            f"Enabled: {self.enabled}, Cache TTL: {cache_ttl}s"
        )

    # ==========================================================================
    # HELPER: NOTIFICAÇÕES TELEGRAM
    # ==========================================================================

    async def _notify_decision(
        self, decision_type: str, symbol: str, reasoning: str, data: dict | None = None
    ):
        """Envia decisão da IA para o Telegram (non-blocking)"""
        if not TELEGRAM_AVAILABLE:
            return

        try:
            # Fire-and-forget (não aguarda resposta)
            _ = asyncio.create_task(
                telegram_notifier.notify_ai_decision_async(
                    decision_type=decision_type,
                    symbol=symbol,
                    reasoning=reasoning[:500],  # Limita tamanho
                    data=data,
                )
            )
        except Exception as e:
            logger.debug(f"Erro ao enviar notificação Telegram: {e}")

    # ==========================================================================
    # 1. ADAPTIVE STOP-LOSS AJUSTADO POR IA
    # ==========================================================================

    async def calculate_adaptive_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        atr: float,
        base_sl_multiplier: float,
        volatility_percentile: float,  # 0-100
        recent_volatility_trend: str,  # 'increasing', 'stable', 'decreasing'
    ) -> AdaptiveStopLoss:
        """
        Calcula stop-loss adaptativo baseado em ATR + análise IA.

        Lógica:
        - Volatilidade alta + crescente → Stop mais largo
        - Volatilidade baixa + estável → Stop mais apertado
        - IA ajusta fino baseado em contexto

        Args:
            symbol: Par de moedas
            entry_price: Preço de entrada
            atr: Average True Range atual
            base_sl_multiplier: Multiplicador base (ex: 2.0)
            volatility_percentile: Onde está a volatilidade (0-100)
            recent_volatility_trend: Tendência recente

        Returns:
            AdaptiveStopLoss com stop ajustado e reasoning
        """
        if not self.enabled:
            # Fallback: Usa stop base
            sl_price = entry_price - (base_sl_multiplier * atr)
            return AdaptiveStopLoss(
                stop_loss_price=round(sl_price, 4),
                stop_multiplier=base_sl_multiplier,
                reasoning="IA desabilitada - usando stop base",
                confidence=0.5,
                volatility_adjusted=False,
            )

        # Cache key
        cache_key = f"adaptive_sl_{symbol}_{entry_price}_{atr}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self.metrics["cache_hits"] += 1
            return cached

        try:
            # Prompt para Ollama
            prompt = f"""Você é um risk manager quantitativo expert em trading de criptomoedas.

CONTEXTO DO TRADE:
- Símbolo: {symbol}
- Preço de Entrada: ${entry_price:.4f}
- ATR Atual: {atr:.4f}
- Stop Base: {base_sl_multiplier}x ATR
- Volatilidade: {volatility_percentile:.0f}º percentil (0=calmo, 100=caótico)
- Tendência de Volatilidade: {recent_volatility_trend}

PERGUNTA:
Dado o contexto, qual o multiplicador ideal de ATR para o stop-loss?
Considere que:
- Volatilidade alta + crescente = stop mais largo (evita stops falsos)
- Volatilidade baixa + estável = stop mais apertado (maximiza R/R)
- Stop muito largo = risco excessivo
- Stop muito apertado = stops prematuros

RESPONDA APENAS NO FORMATO JSON:
{{
    "stop_multiplier": 2.3,
    "reasoning": "Volatilidade em 78º percentil e crescente. Stop base seria muito apertado (stops falsos prováveis). Recomendo 2.3x ATR para dar espaço.",
    "confidence": 0.85
}}"""

            # Chama Ollama (non-blocking)
            response = await self._call_ollama_async(prompt)

            if response:
                # Parse resposta
                data = json.loads(response)
                adjusted_multiplier = float(data["stop_multiplier"])
                reasoning = data["reasoning"]
                confidence = float(data["confidence"])

                # Segurança: Limita multiplicador entre 1.5x e 4.0x
                adjusted_multiplier = max(1.5, min(4.0, adjusted_multiplier))

                # Calcula stop ajustado
                sl_price = entry_price - (adjusted_multiplier * atr)

                result = AdaptiveStopLoss(
                    stop_loss_price=round(sl_price, 4),
                    stop_multiplier=adjusted_multiplier,
                    reasoning=reasoning,
                    confidence=confidence,
                    volatility_adjusted=True,
                )

                # Cache
                self._save_to_cache(cache_key, result)

                logger.info(
                    f"[Adaptive SL] {symbol}: Base {base_sl_multiplier}x → AI {adjusted_multiplier}x ATR "
                    f"(${sl_price:.4f}) - Confidence: {confidence:.0%}"
                )

                # Notificar decisão no Telegram
                await self._notify_decision(
                    decision_type="adaptive_stop",
                    symbol=symbol,
                    reasoning=reasoning,
                    data={
                        "stop_price": sl_price,
                        "multiplier": adjusted_multiplier,
                        "confidence": confidence,
                    },
                )

                return result
            else:
                # Fallback se Ollama falhar
                raise Exception("Ollama não respondeu")

        except Exception as e:
            logger.warning(f"[Adaptive SL] IA falhou: {e} - usando stop base")
            self.metrics["ollama_timeouts"] += 1

            # Fallback: Ajuste heurístico simples
            if volatility_percentile > 70 and recent_volatility_trend == "increasing":
                adjusted_mult = base_sl_multiplier * 1.3
                reason = "Volatilidade alta e crescente - stop alargado 30%"
            elif volatility_percentile < 30 and recent_volatility_trend == "decreasing":
                adjusted_mult = base_sl_multiplier * 0.85
                reason = "Volatilidade baixa e caindo - stop apertado 15%"
            else:
                adjusted_mult = base_sl_multiplier
                reason = "Volatilidade normal - stop base mantido"

            sl_price = entry_price - (adjusted_mult * atr)

            return AdaptiveStopLoss(
                stop_loss_price=round(sl_price, 4),
                stop_multiplier=adjusted_mult,
                reasoning=f"Heurística: {reason} (IA indisponível)",
                confidence=0.6,
                volatility_adjusted=True,
            )

    # ==========================================================================
    # 2. POSITION SIZING INTELIGENTE
    # ==========================================================================

    async def calculate_intelligent_position_size(
        self,
        symbol: str,
        technical_score: int,  # 0-100
        has_divergence: bool,
        volume_confirmed: bool,
        trend_strength: int,  # 0-100
        btc_correlation: float,  # -1 to 1
    ) -> IntelligentPositionSize:
        """
        Ajusta position size baseado em "confiança do setup".

        Lógica:
        - Setup perfeito (score 90+, divergência, volume) → Aumenta size 1.5x
        - Setup fraco (score <75, sem volume) → Reduz size 0.5x
        - IA avalia contexto macro (BTC correlation, trend)

        Args:
            symbol: Par de moedas
            technical_score: Score técnico (0-100)
            has_divergence: Tem divergência RSI/preço
            volume_confirmed: Volume confirmado
            trend_strength: Força da tendência
            btc_correlation: Correlação com BTC

        Returns:
            IntelligentPositionSize com multiplier e reasoning
        """
        if not self.enabled:
            return IntelligentPositionSize(
                size_multiplier=1.0,
                confidence_score=5,
                reasoning="IA desabilitada - size padrão",
                risk_flags=[],
            )

        # Cache
        cache_key = f"size_{symbol}_{technical_score}_{trend_strength}"
        cached = self._get_from_cache(cache_key)
        if cached:
            self.metrics["cache_hits"] += 1
            return cached

        try:
            prompt = f"""Analise a qualidade deste setup de trading:

SETUP:
- Símbolo: {symbol}
- Score Técnico: {technical_score}/100
- Divergência RSI: {"SIM" if has_divergence else "NÃO"}
- Volume Confirmado: {"SIM" if volume_confirmed else "NÃO"}
- Força da Tendência: {trend_strength}/100
- Correlação BTC: {btc_correlation:.2f} (-1=inversa, 0=independente, 1=segue BTC)

PERGUNTA:
Qual o nível de confiança neste setup? (0-10)
- 8-10: Setup excelente, pode AUMENTAR size (1.3x - 1.5x)
- 5-7: Setup OK, size NORMAL (1.0x)
- 0-4: Setup fraco, REDUZIR size (0.5x - 0.8x)

Considere:
- Divergência + Volume = Alta confiança
- Score alto + Trend fraco = Falso sinal?
- BTC muito correlacionado = Risco sistêmico

JSON:
{{
    "confidence_score": 7,
    "size_multiplier": 1.2,
    "reasoning": "Score bom, divergência presente, mas trend moderado. Leve aumento de size.",
    "risk_flags": ["BTC correlation alta pode causar dump conjunto"]
}}"""

            response = await self._call_ollama_async(prompt)

            if response:
                data = json.loads(response)
                confidence = int(data["confidence_score"])
                size_mult = float(data["size_multiplier"])
                reasoning = data["reasoning"]
                risk_flags = data.get("risk_flags", [])

                # Segurança: Limita entre 0.5x e 1.5x
                size_mult = max(0.5, min(1.5, size_mult))

                result = IntelligentPositionSize(
                    size_multiplier=size_mult,
                    confidence_score=confidence,
                    reasoning=reasoning,
                    risk_flags=risk_flags,
                )

                self._save_to_cache(cache_key, result)

                logger.info(
                    f"[Intelligent Size] {symbol}: Confidence {confidence}/10 → "
                    f"Size {size_mult:.1f}x | {reasoning}"
                )

                # Notificar decisão no Telegram
                await self._notify_decision(
                    decision_type="position_size",
                    symbol=symbol,
                    reasoning=reasoning,
                    data={
                        "size_multiplier": size_mult,
                        "confidence_score": confidence,
                    },
                )

                return result
            else:
                raise Exception("Ollama não respondeu")

        except Exception as e:
            logger.warning(f"[Intelligent Size] IA falhou: {e} - usando heurística")

            # Heurística simples
            score_points = 0
            if technical_score >= 85:
                score_points += 2
            elif technical_score >= 75:
                score_points += 1

            if has_divergence:
                score_points += 2
            if volume_confirmed:
                score_points += 2
            if trend_strength >= 70:
                score_points += 1

            confidence = min(10, score_points + 3)

            if confidence >= 8:
                size_mult = 1.3
            elif confidence >= 6:
                size_mult = 1.0
            else:
                size_mult = 0.7

            return IntelligentPositionSize(
                size_multiplier=size_mult,
                confidence_score=confidence,
                reasoning=f"Heurística: {score_points} pontos positivos",
                risk_flags=[],
            )

    # ==========================================================================
    # 3. ANÁLISE DE SENTIMENTO PRÉ-TRADE (placeholder - requer API de notícias)
    # ==========================================================================

    async def pre_trade_sentiment_analysis(
        self,
        symbol: str,
        current_time: datetime,
    ) -> PreTradeAnalysis:
        """
        Verifica se há eventos de risco iminentes.

        NOTA: Implementação simplificada. Versão completa requer:
        - API de notícias crypto (CoinGecko, CryptoPanic)
        - Scraping de Twitter/Reddit
        - Calendário econômico (Fed, CPI, etc)

        Por hora: Heurística de horários de risco conhecidos.

        Args:
            symbol: Par de moedas
            current_time: Hora atual UTC

        Returns:
            PreTradeAnalysis com sentimento e alertas
        """
        # Horários de alto risco (UTC)
        # - 13:30-14:30: CPI/NFP/FOMC (EUA)
        # - 12:00-13:00: ECB announcements
        hour_utc = current_time.hour

        risk_events = []
        sentiment = "NEUTRAL"
        should_enter = True
        urgency = "IMMEDIATE"

        # Check horários de risco
        if 13 <= hour_utc <= 14:
            risk_events.append("Horário de anúncios macroeconômicos EUA (13:30-14:30 UTC)")
            sentiment = "CAUTION"
            should_enter = False
            urgency = "WAIT_1H"

        if 12 <= hour_utc < 13:
            risk_events.append("Possível anúncio ECB (12:00-13:00 UTC)")
            sentiment = "CAUTION"
            urgency = "WAIT_1H"

        # Fim de semana: Baixa liquidez
        if current_time.weekday() >= 5:  # Sábado/Domingo
            risk_events.append("Fim de semana - liquidez reduzida, spreads maiores")
            sentiment = "NEUTRAL"

        reasoning = (
            f"Análise de horário: {current_time.strftime('%H:%M UTC')}. "
            f"Eventos detectados: {len(risk_events)}. "
            f"{'Aguarde passar horário de risco.' if not should_enter else 'Via livre para operar.'}"
        )

        # Notificar apenas se houver riscos críticos
        if not should_enter:
            await self._notify_decision(
                decision_type="pre_trade",
                symbol=symbol,
                reasoning=reasoning,
                data={
                    "should_enter": should_enter,
                    "sentiment": sentiment,
                    "risk_events": risk_events,
                    "urgency": urgency,
                },
            )

        return PreTradeAnalysis(
            should_enter=should_enter,
            sentiment=sentiment,
            risk_events=risk_events,
            reasoning=reasoning,
            urgency=urgency,
        )

    # ==========================================================================
    # 4. FALLBACK REASONING - POR QUE NÃO ENTROU?
    # ==========================================================================

    async def generate_skip_reasoning(
        self,
        symbol: str,
        technical_score: int,
        filters_failed: list[str],  # Ex: ['ML_CONFIDENCE_LOW', 'VOLUME_WEAK']
        market_regime: str,
        current_drawdown: float,
    ) -> SkipReasoning:
        """
        Gera explicação clara de por que o bot pulou um trade.

        Args:
            symbol: Par que foi pulado
            technical_score: Score técnico (0-100)
            filters_failed: Lista de filtros que falharam
            market_regime: Regime atual do mercado
            current_drawdown: Drawdown atual em %

        Returns:
            SkipReasoning com explicação e sugestão
        """
        # Determina razão principal
        if "ML_CONFIDENCE_LOW" in filters_failed:
            primary = f"Modelo ML deu baixa confiança (score {technical_score} insuficiente)"
        elif "VOLUME_WEAK" in filters_failed:
            primary = "Volume abaixo da média (50% do normal) - sinal fraco"
        elif "TIME_FILTER" in filters_failed:
            primary = "Filtro de horário ativo - baixa liquidez neste período"
        elif "CIRCUIT_BREAKER" in filters_failed:
            primary = f"Circuit breaker ativado (drawdown {current_drawdown:.1f}%)"
        elif technical_score < 75:
            primary = f"Score técnico {technical_score}/100 abaixo do mínimo (75)"
        else:
            primary = "Múltiplos filtros falharam - setup não qualificado"

        # Fatores contribuintes
        contributing = []
        if market_regime == "ranging":
            contributing.append("Mercado lateral dificulta breakouts")
        if current_drawdown > 5:
            contributing.append(f"Drawdown {current_drawdown:.1f}% - operando defensivo")
        if "BTC_HEALTH_BAD" in filters_failed:
            contributing.append("BTC em queda afeta altcoins negativamente")

        # Sugestão
        if "TIME_FILTER" in filters_failed:
            suggestion = "Aguarde liquidez melhorar (após 07:00 UTC ou 16:00 UTC)"
            next_check = 60
        elif "CIRCUIT_BREAKER" in filters_failed:
            suggestion = "Aguarde drawdown reduzir antes de operar novamente"
            next_check = 120
        elif technical_score < 75:
            suggestion = f"Procure setups com score ≥75. Atual: {technical_score}"
            next_check = 15
        else:
            suggestion = "Aguarde próximo scan (15 segundos)"
            next_check = 15

        reasoning = f"""
❌ TRADE PULADO: {symbol}

RAZÃO PRINCIPAL:
{primary}

FATORES ADICIONAIS:
{chr(10).join(f"- {f}" for f in contributing) if contributing else "- Nenhum"}

💡 SUGESTÃO:
{suggestion}

⏰ PRÓXIMA VERIFICAÇÃO: {next_check} minutos
""".strip()

        logger.info(f"[Skip Reasoning] {symbol}: {primary}")

        # Notificar no Telegram
        await self._notify_decision(
            decision_type="skip_trade",
            symbol=symbol,
            reasoning=reasoning,
            data={
                "primary_reason": primary,
                "contributing_factors": contributing,
                "suggestion": suggestion,
            },
        )

        return SkipReasoning(
            primary_reason=primary,
            contributing_factors=contributing,
            suggestion=suggestion,
            next_check_in_minutes=next_check,
        )

    # ==========================================================================
    # 5. REGIME ADAPTATIVO COM FEEDBACK
    # ==========================================================================

    def add_trade_feedback(
        self,
        symbol: str,
        entry_time: datetime,
        regime: str,
        score: int,
        pnl_percent: float,
        duration_minutes: int,
        hit_stop: bool,
    ):
        """
        Adiciona feedback de um trade ao histórico.

        Args:
            symbol: Par operado
            entry_time: Quando entrou
            regime: Regime de mercado quando entrou
            score: Score técnico do setup
            pnl_percent: P&L em %
            duration_minutes: Quanto tempo ficou aberto
            hit_stop: Bateu stop-loss?
        """
        trade = {
            "symbol": symbol,
            "entry_time": entry_time,
            "regime": regime,
            "score": score,
            "pnl_percent": pnl_percent,
            "duration_minutes": duration_minutes,
            "hit_stop": hit_stop,
            "success": pnl_percent > 0,
        }

        self.trade_history.append(trade)

        # Limita histórico
        if len(self.trade_history) > self.max_history:
            self.trade_history.pop(0)

        logger.debug(
            f"[Feedback] Added trade: {symbol} {'+' if trade['success'] else '-'}{abs(pnl_percent):.2f}% "
            f"in {regime} regime (score {score})"
        )

    async def get_regime_adaptation(
        self,
        current_regime: str,
        recent_signals_count: int,  # Sinais detectados na última hora
    ) -> RegimeAdaptation:
        """
        Analisa últimos trades e sugere ajustes nos parâmetros.

        Lógica:
        - Se últimos 5 trades em 'ranging' deram loss → Aumentar score mínimo
        - Se últimos 5 trades em 'trending' deram profit → Reduzir score (mais agressivo)
        - Se muitos stops → Alargar stops
        - Se win rate alta → Aumentar position size

        Args:
            current_regime: Regime atual do mercado
            recent_signals_count: Quantos sinais foram detectados recentemente

        Returns:
            RegimeAdaptation com ajustes sugeridos
        """
        if len(self.trade_history) < 5:
            return RegimeAdaptation(
                current_regime=current_regime,
                score_threshold_adjustment=0,
                stop_multiplier_adjustment=1.0,
                size_adjustment=1.0,
                reasoning="Histórico insuficiente (< 5 trades) - usando padrões",
                win_rate_last_10=0.0,
                should_trade=True,
            )

        # Análise dos últimos trades
        last_10 = self.trade_history[-10:]
        wins = sum(1 for t in last_10 if t["success"])
        win_rate = (wins / len(last_10)) * 100

        # Filtra trades no regime atual
        regime_trades = [t for t in last_10 if t["regime"] == current_regime]

        if len(regime_trades) >= 3:
            regime_wins = sum(1 for t in regime_trades if t["success"])
            regime_wr = (regime_wins / len(regime_trades)) * 100

            # Conta stops
            stops_hit = sum(1 for t in regime_trades if t["hit_stop"])
            stop_rate = (stops_hit / len(regime_trades)) * 100
        else:
            regime_wr = win_rate
            stop_rate = 0

        # Decisão de ajustes
        score_adj = 0
        stop_adj = 1.0
        size_adj = 1.0
        reasoning_parts = []

        # Ajuste 1: Win rate muito baixo no regime atual
        if regime_wr < 30 and len(regime_trades) >= 3:
            score_adj = +10  # Mais rigoroso
            reasoning_parts.append(
                f"Win rate {regime_wr:.0f}% em {current_regime} muito baixo. "
                f"Aumentando score mínimo +10 para filtrar melhor."
            )

        # Ajuste 2: Win rate alto → Ser mais agressivo
        elif regime_wr > 70 and len(regime_trades) >= 4:
            score_adj = -5  # Menos rigoroso
            size_adj = 1.2  # Aumenta size
            reasoning_parts.append(
                f"Win rate {regime_wr:.0f}% excelente! "
                f"Reduzindo score -5 e aumentando size 1.2x."
            )

        # Ajuste 3: Muitos stops → Alargar
        if stop_rate > 60:
            stop_adj = 1.3
            reasoning_parts.append(
                f"Taxa de stops {stop_rate:.0f}% alta. "
                f"Alargando stops 30% para evitar exits prematuros."
            )

        # Ajuste 4: Muitos sinais mas poucos trades → Score muito alto?
        if recent_signals_count > 20 and len(regime_trades) < 2:
            score_adj = max(score_adj, -10)  # Se já tinha aumentado, cancela
            reasoning_parts.append(
                f"Muitos sinais ({recent_signals_count}) mas poucos trades. "
                f"Score pode estar muito restritivo. Reduzindo -10."
            )

        # Ajuste 5: Drawdown detectado (win rate geral < 40%)
        if win_rate < 40:
            size_adj = 0.7
            reasoning_parts.append(
                f"Win rate geral {win_rate:.0f}% baixo. " f"Reduzindo size para 0.7x até melhorar."
            )

        # Decisão final: Operar ou não?
        should_trade = True
        if regime_wr < 20 and len(regime_trades) >= 5:
            should_trade = False
            reasoning_parts.append(
                f"⚠️ CRÍTICO: Win rate {regime_wr:.0f}% em {current_regime} é insustentável. "
                f"PAUSANDO operações neste regime até análise."
            )

        reasoning = (
            " | ".join(reasoning_parts)
            if reasoning_parts
            else "Performance OK - sem ajustes necessários"
        )

        result = RegimeAdaptation(
            current_regime=current_regime,
            score_threshold_adjustment=score_adj,
            stop_multiplier_adjustment=stop_adj,
            size_adjustment=size_adj,
            reasoning=reasoning,
            win_rate_last_10=win_rate,
            should_trade=should_trade,
        )

        if score_adj != 0 or stop_adj != 1.0 or size_adj != 1.0:
            self.metrics["adaptations_made"] += 1
            logger.warning(
                f"[Regime Adaptation] {current_regime}: Score {score_adj:+d}, "
                f"Stop {stop_adj:.1f}x, Size {size_adj:.1f}x | {reasoning}"
            )

            # Notificar adaptações importantes no Telegram
            await self._notify_decision(
                decision_type="regime_adapt",
                symbol=current_regime,  # Usando regime como "symbol"
                reasoning=reasoning,
                data={
                    "win_rate": win_rate,
                    "should_trade": should_trade,
                    "score_adjustment": score_adj,
                    "stop_multiplier_adjustment": stop_adj,
                    "size_adjustment": size_adj,
                },
            )

        return result

    # ==========================================================================
    # MÉTODOS AUXILIARES
    # ==========================================================================

    async def _call_ollama_async(self, prompt: str) -> str | None:
        """Chama Ollama de forma assíncrona (non-blocking)"""
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(self.executor, self._call_ollama_sync, prompt),
                timeout=self.timeout,
            )
            self.metrics["requests_total"] += 1
            return response
        except TimeoutError:
            logger.warning(f"[LLM Risk Advisor] Ollama timeout ({self.timeout}s)")
            self.metrics["ollama_timeouts"] += 1
            return None
        except Exception as e:
            logger.error(f"[LLM Risk Advisor] Ollama error: {e}")
            return None

    def _call_ollama_sync(self, prompt: str) -> str:
        """Chama Ollama de forma síncrona (roda em thread)"""
        import requests

        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Mais determinístico
                "top_p": 0.9,
            },
        }

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()

    def _get_from_cache(self, key: str) -> any | None:
        """Busca item no cache"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            age = (datetime.now() - timestamp).total_seconds()
            if age < self.cache_ttl:
                return value
            else:
                del self.cache[key]
        return None

    def _save_to_cache(self, key: str, value: any):
        """Salva item no cache"""
        self.cache[key] = (value, datetime.now())

        # Limpa cache antigo (max 50 items)
        if len(self.cache) > 50:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

    def get_metrics(self) -> dict:
        """Retorna métricas de uso"""
        cache_hit_rate = (
            self.metrics["cache_hits"] / self.metrics["requests_total"] * 100
            if self.metrics["requests_total"] > 0
            else 0
        )

        return {
            **self.metrics,
            "cache_hit_rate_percent": round(cache_hit_rate, 1),
            "trade_history_count": len(self.trade_history),
            "ollama_available": self.enabled,
        }


# Singleton instance
_risk_advisor_instance = None


def get_risk_advisor() -> LLMRiskAdvisor:
    """Retorna instância singleton do LLM Risk Advisor"""
    global _risk_advisor_instance
    if _risk_advisor_instance is None:
        _risk_advisor_instance = LLMRiskAdvisor()
    return _risk_advisor_instance
