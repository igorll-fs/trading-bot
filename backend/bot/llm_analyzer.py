"""
LLM Analyzer - Integração de IA (Ollama) para Confirmação de Setups de Trading

Especificações:
- Modelo: Mistral 7B (4.7GB, latência 2-5s)
- Execução: Async (thread pool, non-blocking)
- Hardware Target: Dell E7450 (i5-5300U, 12GB RAM, 2 cores)
- Propósito: Confirmar sinais técnicos com análise IA

Fluxo:
    Technical Score >= 80
        ↓
    LLM Confirmation (async)
        ↓
    Final Decision + Position Size Adjustment
"""

import asyncio
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Resposta estruturada do LLM"""

    opinion: str  # 'STRONG_BUY', 'BUY', 'WEAK_BUY', 'NEUTRAL'
    confidence: float  # 0.0-1.0
    reasoning: str  # Justificativa em 1-2 linhas
    score: int  # 0-100 (compatível com technical score)
    raw_response: str  # Resposta bruta do Ollama


class LLMAnalyzer:
    """
    Analisador de IA para confirmação de setups de trading.

    ✅ Características:
    - Non-blocking (executa em thread separada)
    - Cache de respostas recentes (30s TTL)
    - Fallback gracioso se Ollama indisponível
    - Logging detalhado
    - Type hints completos

    ❌ O que NÃO faz:
    - Não bloqueia o event loop
    - Não substitui risk management
    - Não modifica stops/targets
    """

    def __init__(
        self,
        model: str = "mistral",
        enabled: bool = True,
        cache_ttl: int = 30,
        max_workers: int = 1,
        timeout: int = 10,
    ):
        """
        Inicializa o analisador LLM.

        Args:
            model: Modelo Ollama a usar (default: mistral 7B)
            enabled: Habilitar IA (pode ser desabilitado com env var)
            cache_ttl: TTL do cache de respostas em segundos
            max_workers: Threads no pool (1 = non-blocking total)
            timeout: Timeout de resposta em segundos
        """
        # Permitir desabilitação via env var
        self.enabled = enabled and os.getenv("LLM_ENABLED", "true").lower() == "true"
        self.model = model if self.enabled else None
        self.model_name = model  # Alias para compatibilidade
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = timeout

        # Thread pool: max 1 worker = não bloqueia event loop
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Cache simples: símbolo -> (response, timestamp)
        self.cache: dict[str, tuple] = {}
        self.cache_ttl = cache_ttl

        # Métricas
        self.metrics = {
            "requests_total": 0,
            "cache_hits": 0,
            "ollama_timeouts": 0,
            "ollama_errors": 0,
            "avg_latency_ms": 0.0,
        }

        self.loaded = False
        self.last_error: str | None = None

        if self.enabled:
            self._verify_ollama()

    def _verify_ollama(self) -> None:
        """Verifica se Ollama está rodando e modelo disponível"""
        try:
            import ollama

            # Test connection
            response = ollama.list()
            logger.info(
                "[LLM] Ollama conectado. Modelos disponíveis: %s",
                [m.get("name", "unknown") for m in response.get("models", [])],
            )

            # Check if mistral is available
            models = [m.get("name", "") for m in response.get("models", [])]
            if self.model not in models:
                logger.warning(
                    "[LLM] Modelo '%s' não encontrado. Puxando... (pode levar 5-10 min)", self.model
                )
                # Note: Pull é sincronous, mas só faz na primeira vez
                try:
                    ollama.pull(self.model)
                    logger.info("[LLM] Modelo '%s' puxado com sucesso", self.model)
                except Exception as e:
                    logger.error("[LLM] Erro ao puxar modelo: %s", e)
                    self.enabled = False
                    self.last_error = f"Failed to pull model: {e}"
                    return

            self.loaded = True
            logger.info("[LLM] ✅ Sistema LLM pronto para usar")

        except ImportError:
            logger.error("[LLM] ❌ 'ollama' não instalado. Execute: pip install ollama")
            self.enabled = False
            self.last_error = "ollama package not installed"
        except Exception as e:
            logger.error("[LLM] ❌ Erro ao conectar Ollama: %s", e)
            self.enabled = False
            self.last_error = str(e)

    def _get_cache_key(self, symbol: str, price: float) -> str:
        """Gera chave de cache única para símbolo+preço"""
        return f"{symbol}_{price:.2f}"

    def _check_cache(self, cache_key: str) -> LLMResponse | None:
        """Verifica se há resposta em cache (válida)"""
        if cache_key not in self.cache:
            return None

        cached_response, timestamp = self.cache[cache_key]
        elapsed = time.time() - timestamp

        if elapsed < self.cache_ttl:
            self.metrics["cache_hits"] += 1
            logger.debug("[LLM] Cache HIT para %s (idade: %.1fs)", cache_key, elapsed)
            return cached_response
        else:
            # Expirou
            del self.cache[cache_key]
            return None

    def _build_entry_prompt(self, data: dict[str, Any]) -> str:
        """Constrói prompt customizado para análise de entry"""
        symbol = data.get("symbol", "UNKNOWN")
        price = data.get("price", 0)
        rsi = data.get("rsi", 50)
        macd_hist = data.get("macd_hist", 0)
        atr = data.get("atr", 0)
        ema_trend = "BUY" if data.get("ema_50", 0) > data.get("ema_200", 0) else "SELL"
        tech_score = data.get("technical_score", 0)
        volume_ratio = data.get("volume_ratio", 1.0)
        market_regime = data.get("market_regime", "unknown")

        prompt = f"""Você é um analista de trading quantitativo especializado em crypto. Analyze este setup:

DADOS DO SETUP:
- Símbolo: {symbol}
- Preço: ${price:.4f}
- RSI(14): {rsi:.1f}
- MACD Histogram: {macd_hist:.6f}
- ATR: {atr:.4f}
- Trend (EMA 50 > 200): {ema_trend}
- Score Técnico: {tech_score}/100
- Volume Ratio: {volume_ratio:.2f}
- Regime: {market_regime}

PERGUNTA: Este é um setup de COMPRA confiável em crypto?

RESPONDA com UMA destas opções:
1. STRONG_BUY - Setup excelente (confiança 85-100%)
2. BUY - Setup bom (confiança 65-85%)
3. WEAK_BUY - Setup moderado (confiança 50-65%)
4. NEUTRAL - Sem confiança (<50%)

Formato: [OPINION] - [Razão em 1 linha]
Exemplo: BUY - RSI oversold + MACD bullish divergence
"""
        return prompt

    def _parse_ollama_response(self, raw_response: str) -> LLMResponse:
        """
        Parse resposta do Ollama e converte para estrutura padrão.

        Espera formato: "OPINION - Razão em 1 linha"
        Exemplo: "BUY - RSI oversold + MACD bullish"
        """
        try:
            lines = raw_response.strip().split("\n")
            first_line = lines[0] if lines else ""

            # Parse opinion
            if "STRONG_BUY" in first_line.upper():
                opinion = "STRONG_BUY"
                confidence = 0.92
                score = 92
            elif "BUY" in first_line.upper():
                opinion = "BUY"
                confidence = 0.75
                score = 75
            elif "WEAK_BUY" in first_line.upper():
                opinion = "WEAK_BUY"
                confidence = 0.58
                score = 58
            else:
                opinion = "NEUTRAL"
                confidence = 0.35
                score = 35

            # Extract reasoning
            reasoning = first_line.split("-", 1)[1].strip() if "-" in first_line else "LLM analysis"

            return LLMResponse(
                opinion=opinion,
                confidence=confidence,
                reasoning=reasoning,
                score=score,
                raw_response=raw_response,
            )
        except Exception as e:
            logger.warning("[LLM] Erro ao fazer parse resposta: %s", e)
            return LLMResponse(
                opinion="NEUTRAL",
                confidence=0.5,
                reasoning="Parse error - neutral",
                score=50,
                raw_response=raw_response,
            )

    def _sync_analyze(self, prompt: str) -> str:
        """
        Chamada síncrona ao Ollama (roda em thread pool).

        ⚠️ NÃO chamar diretamente - usar analyze_entry() async
        """
        try:
            import ollama

            if not self.loaded or not self.enabled:
                return "NEUTRAL - LLM not available"

            start = time.perf_counter()

            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                options={
                    "num_predict": 50,  # Resposta curta (rápido)
                    "temperature": 0.3,  # Determinístico (importante)
                    "repeat_penalty": 1.1,  # Avoid repetition
                    "top_p": 0.9,  # Nucleus sampling
                },
            )

            latency_ms = (time.perf_counter() - start) * 1000
            self.metrics["avg_latency_ms"] = latency_ms

            logger.debug("[LLM] Resposta em %.0fms", latency_ms)
            return response.get("response", "NEUTRAL - Empty response")

        except TimeoutError:
            self.metrics["ollama_timeouts"] += 1
            logger.warning("[LLM] Timeout de Ollama (>%ds)", self.timeout)
            self.last_error = "Ollama timeout"
            return "NEUTRAL - Ollama timeout"
        except Exception as e:
            self.metrics["ollama_errors"] += 1
            logger.error("[LLM] Erro Ollama: %s", e)
            self.last_error = str(e)
            return "NEUTRAL - Ollama error"

    async def analyze_entry(
        self,
        symbol: str,
        price: float,
        technical_score: int,
        indicators: dict[str, float],
    ) -> LLMResponse:
        """
        Analisa setup de entry de forma async (non-blocking).

        ✅ Seguro para usar em _trading_loop()

        Args:
            symbol: Símbolo da criptomoeda (ex: BTCUSDT)
            price: Preço current
            technical_score: Score técnico (0-100)
            indicators: Dict com RSI, MACD, ATR, etc

        Returns:
            LLMResponse com opinion, confidence, reasoning
        """

        if not self.enabled:
            logger.debug("[LLM] LLM desabilitado - retornando NEUTRAL")
            return LLMResponse(
                opinion="NEUTRAL",
                confidence=0.5,
                reasoning="LLM disabled",
                score=50,
                raw_response="LLM disabled",
            )

        # Check cache first
        cache_key = self._get_cache_key(symbol, price)
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        try:
            self.metrics["requests_total"] += 1

            # Preparar dados
            data = {
                "symbol": symbol,
                "price": price,
                "technical_score": technical_score,
                "rsi": indicators.get("rsi", 50),
                "macd_hist": indicators.get("macd_hist", 0),
                "atr": indicators.get("atr", 0),
                "ema_50": indicators.get("ema_50", 0),
                "ema_200": indicators.get("ema_200", 0),
                "volume_ratio": indicators.get("volume_ratio", 1.0),
                "market_regime": indicators.get("market_regime", "unknown"),
            }

            # Build prompt
            prompt = self._build_entry_prompt(data)

            # Run in executor (thread pool) - non-blocking!
            loop = asyncio.get_running_loop()
            raw_response = await loop.run_in_executor(self.executor, self._sync_analyze, prompt)

            # Parse response
            result = self._parse_ollama_response(raw_response)

            # Cache result
            self.cache[cache_key] = (result, time.time())

            logger.info(
                "[LLM] %s - Opinion: %s, Confidence: %.0f%%, Score: %d",
                symbol,
                result.opinion,
                result.confidence * 100,
                result.score,
            )

            return result

        except Exception as e:
            logger.error("[LLM] Erro em analyze_entry: %s", e)
            self.last_error = str(e)
            return LLMResponse(
                opinion="NEUTRAL",
                confidence=0.5,
                reasoning="Analysis error",
                score=50,
                raw_response=str(e),
            )

    async def analyze_exit(
        self,
        symbol: str,
        price: float,
        entry_price: float,
        profit_pct: float,
        indicators: dict[str, float],
    ) -> bool:
        """
        Analisa se deve sair de posição aberta.

        Args:
            symbol: Símbolo
            price: Preço atual
            entry_price: Preço de entrada
            profit_pct: Lucro percentual atual
            indicators: Indicadores técnicos

        Returns:
            True = deve sair, False = manter
        """
        if not self.enabled or profit_pct < 0.5:
            # Sem lucro suficiente, manter
            return False

        try:
            prompt = f"""Você é um trader profissional. Setup de SAÍDA:

Símbolo: {symbol}
Entry: ${entry_price:.4f}
Atual: ${price:.4f}
Lucro: +{profit_pct:.2f}%
RSI: {indicators.get('rsi', 50):.1f}
MACD Trend: {'Positivo' if indicators.get('macd_hist', 0) > 0 else 'Negativo'}

Responda: "SIM sair" ou "NÃO manter"?
"""

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(self.executor, self._sync_analyze, prompt)

            should_exit = "SIM" in response.upper()
            logger.info(
                "[LLM] Exit signal para %s: %s", symbol, "SAIR" if should_exit else "MANTER"
            )
            return should_exit

        except Exception as e:
            logger.warning("[LLM] Erro em analyze_exit: %s - mantendo posição", e)
            return False

    def get_metrics(self) -> dict[str, Any]:
        """Retorna métricas de uso do LLM"""
        return {
            **self.metrics,
            "enabled": self.enabled,
            "loaded": self.loaded,
            "model": self.model,
            "last_error": self.last_error,
            "cache_size": len(self.cache),
        }

    async def is_available(self) -> bool:
        """
        Verifica se o LLM Analyzer está disponível e funcional.

        Returns:
            True se o Ollama está rodando e o modelo está carregado.
        """
        if not self.enabled:
            return False

        try:
            # Testa conexão com Ollama em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            is_ok = await loop.run_in_executor(self.executor, self._check_ollama_sync)
            return is_ok and self.loaded
        except Exception as e:
            logger.warning("[LLM] Erro ao verificar disponibilidade: %s", e)
            return False

    def _check_ollama_sync(self) -> bool:
        """Verificação síncrona do Ollama (roda em thread)"""
        try:
            import ollama

            # Tenta listar modelos - se funcionar, Ollama está OK
            response = ollama.list()
            return len(response.get("models", [])) > 0
        except Exception:
            return False

    async def shutdown(self):
        """Desliga thread pool gracefully"""
        try:
            self.executor.shutdown(wait=True)
            logger.info("[LLM] Thread pool encerrado")
        except Exception as e:
            logger.warning("[LLM] Erro ao desligar: %s", e)


# ============================================================================
# Factory function para criar instância global
# ============================================================================

_llm_instance: LLMAnalyzer | None = None


def get_llm_analyzer(force_new: bool = False) -> LLMAnalyzer:
    """
    Factory para obter instância global do LLMAnalyzer.

    Args:
        force_new: Se True, cria nova instância (útil para testes)

    Returns:
        Instância LLMAnalyzer
    """
    global _llm_instance

    if force_new or _llm_instance is None:
        _llm_instance = LLMAnalyzer()

    return _llm_instance


if __name__ == "__main__":
    """
    Script de teste/verificação do LLM.

    Uso: python -m bot.llm_analyzer
    """
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    async def test_llm():
        analyzer = get_llm_analyzer()

        # Test data
        test_data = {
            "symbol": "BTCUSDT",
            "price": 42500.0,
            "technical_score": 82,
            "rsi": 35,
            "macd_hist": 0.00012,
            "atr": 150.0,
            "ema_50": 42200,
            "ema_200": 41500,
            "volume_ratio": 1.8,
            "market_regime": "trending",
        }

        print("\n🤖 Testando LLM Analyzer...")
        print(f"Status: {'✅ Ativo' if analyzer.enabled else '❌ Inativo'}")

        if analyzer.enabled:
            result = await analyzer.analyze_entry(**test_data)
            print("\nResultado:")
            print(f"  Opinion: {result.opinion}")
            print(f"  Confidence: {result.confidence * 100:.0f}%")
            print(f"  Score: {result.score}/100")
            print(f"  Reasoning: {result.reasoning}")

        metrics = analyzer.get_metrics()
        print(f"\nMétricas: {json.dumps(metrics, indent=2)}")

        await analyzer.shutdown()

    asyncio.run(test_llm())
