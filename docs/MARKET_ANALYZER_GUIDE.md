# 🧠 Como o LLM Market Analyzer Funciona

## 📊 Visão Geral

O Market Analyzer é um sistema de IA que **analisa em tempo real** e **aprende continuamente**. Ele não precisa de treinamento prévio, mas se beneficia do histórico de trades.

---

## 🔄 Fluxo de Análise (Tempo Real)

### 1️⃣ **COLETA DE DADOS** (Automática - Cada Loop do Bot)

```
Bot detecta oportunidade de trade
         ↓
Market Analyzer é chamado
         ↓
Coleta dados em tempo real:
```

**Dados Coletados:**

- ✅ **BTC (Líder de Mercado)**
  - Preço atual
  - Mudança 24h
  - Volume
  - RSI, MACD

- ✅ **Altcoin Candidata**
  - Preço
  - Volume ratio (volume atual / média)
  - Indicadores técnicos
  - Volatilidade (ATR)

- ✅ **Histórico do Bot**
  - Últimos 50 trades (se disponíveis)
  - Win rate por regime
  - Tempo médio de hold
  - Drawdown atual

---

### 2️⃣ **ANÁLISE DE REGIME** (Ollama Mistral 7B)

O Market Analyzer envia um **prompt especializado** para o Ollama:

```
EXEMPLO DE PROMPT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Você é um trader profissional quantitativo especializado em crypto.
Analise o regime atual do mercado.

DADOS DE BTC (líder de mercado):
- Preço: $87,630.00
- Mudança 24h: +3.5%
- Volume 24h: $42,500,000,000
- RSI: 62.3

DADOS DA ALTCOIN:
- Símbolo: ETHUSDT
- Preço: $2916.17
- Mudança 24h: +2.8%
- Volume Ratio: 1.4x (volume acima da média)
- Volatilidade (ATR): 0.0012

HISTÓRICO DE PERFORMANCE:
- Win Rate: 75% (15W / 5L nos últimos 20 trades)
- Ganho Médio: +2.3%
- Perda Média: -1.2%
- Tempo Médio de Hold: 42 minutos

DRAWDOWN ATUAL: 0.5%

PERGUNTA: Qual o regime de mercado atual e como devemos operar?

RESPONDA com UMA linha no formato:
[REGIME] | Stop:[X]x | Target:[Y]x | Size:[Z]% | Razão

Exemplos:
BULL_TRENDING | Stop:1.2x | Target:2.5x | Size:100% | BTC rallying + alt volume strong
HIGH_VOLATILITY | Stop:2.0x | Target:1.5x | Size:50% | ATR elevated + erratic price action

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Ollama Responde em ~2-5 segundos:**

```
BULL_TRENDING | Stop:1.3x | Target:2.0x | Size:100% | BTC momentum strong, ETH volume confirming
```

---

### 3️⃣ **PARSE E APLICAÇÃO** (Bot)

O Market Analyzer interpreta a resposta e cria uma recomendação:

```python
LLMTradeRecommendation(
    action="OPEN_LONG",           # Ou SKIP, WAIT
    confidence=0.85,              # 85% confiança
    reasoning="BTC momentum strong, ETH volume confirming",

    # Multiplicadores adaptativos:
    suggested_stop_multiplier=1.3,    # Stop 30% mais largo
    suggested_target_multiplier=2.0,  # Target 2x maior
    position_size_adjustment=1.0,     # Size normal (100%)
    max_hold_time_minutes=60          # Máximo 1h
)
```

**Bot aplica os ajustes:**

```
Stop Loss Original: $2850 (2.5% do entry)
         ↓
Stop Ajustado: $2835 (1.3x mais largo = 3.25%)

Take Profit Original: $2990 (2.5% de lucro)
         ↓
Target Ajustado: $3050 (2.0x maior = 5% de lucro)

Position Size: $100 USDT
         ↓
Size Ajustado: $100 (1.0 = sem mudança)
```

---

### 4️⃣ **FEEDBACK LOOP** (Aprendizado Contínuo)

Quando o trade fecha:

```
Trade Fecha → Resultado:
- Symbol: ETHUSDT
- PnL: +3.8%
- Duração: 42 minutos
- Regime: BULL_TRENDING
         ↓
Market Analyzer armazena no histórico (max 50 trades)
         ↓
Próxima análise usará esse resultado:
"Em BULL_TRENDING, win rate é 80%, avg PnL +2.5%"
```

---

## 🎓 Como Alimentar com Dados Históricos

### Opção 1: Automático (Recomendado)

O Market Analyzer aprende automaticamente conforme o bot opera:

- Cada trade fechado é automaticamente adicionado
- Sem necessidade de configuração

### Opção 2: Feed Manual (Para Start Rápido)

Se você já tem trades no MongoDB, pode alimentar o histórico:

```bash
# Últimos 30 dias
python feed_market_analyzer.py --days 30

# Últimos 100 trades
python feed_market_analyzer.py --limit 100

# Todos os trades (cuidado com quantidade)
python feed_market_analyzer.py --limit 1000
```

**Saída esperada:**

```
🤖 ALIMENTANDO LLM MARKET ANALYZER COM HISTÓRICO
================================================================

📥 Buscando trades históricos...
   • Últimos 30 dias

📊 Encontrados 87 trades históricos
🤖 Inicializando Market Analyzer...
✅ Market Analyzer carregado

📊 Processando 87 trades...

   ✅ [  1/87] ETHUSDT    +2.30% em  45min
   ✅ [  2/87] BTCUSDT    +1.80% em  38min
   ❌ [  3/87] ADAUSDT    -1.20% em  22min
   ...

================================================================
✅ ALIMENTAÇÃO CONCLUÍDA!
================================================================

📊 ESTATÍSTICAS:
   • Trades Processados: 87
   • Falhas: 0
   • Total no Histórico: 50 (limite máximo)

💡 INSIGHTS DO HISTÓRICO:
   • Win Rate: 72.5% (63W / 24L)
   • Ganho Médio: +2.15%
   • Perda Média: -1.03%
   • Risk/Reward: 2.09x

🚀 O Market Analyzer agora usará esse histórico para análises futuras!
```

---

## 🧩 Regimes Identificados

| Regime              | Características              | Ação do Bot                                |
| ------------------- | ---------------------------- | ------------------------------------------ |
| **BULL_TRENDING**   | BTC subindo + volume forte   | Stops 1.2-1.5x, Targets 2-3x, Size 100%    |
| **BEAR_TRENDING**   | Queda consistente            | Stops 1.5-2x, Targets 1-1.5x, Size 50%     |
| **RANGING**         | Lateral, sem direção         | Stops 0.8-1x, Targets 1-1.5x, Quick scalps |
| **HIGH_VOLATILITY** | Movimentos bruscos, ATR alto | Stops 2-3x, Targets 1.5x, Size 25-50%      |
| **LOW_VOLATILITY**  | Calmo, ATR baixo             | Stops 0.8-1x, Targets 1.5-2x, Size 100%    |
| **UNCERTAIN**       | Sinais mistos                | Stops 1x, Targets 1x, SKIP trades          |

---

## 🎯 Exemplos Reais de Adaptação

### Cenário 1: Mercado Calmo (Bull Trending)

```
Entrada: BTC +1.2%, ETH +0.8%, ATR baixo
         ↓
Regime: BULL_TRENDING
         ↓
Ajustes:
- Stop: 1.2x (aceita pullback pequeno)
- Target: 2.5x (ride the trend)
- Size: 100%
         ↓
Resultado: +4.2% em 52min ✅
```

### Cenário 2: Alta Volatilidade (Crash)

```
Entrada: BTC -8.5%, volume extremo, ATR 3x normal
         ↓
Regime: HIGH_VOLATILITY
         ↓
Ajustes:
- Stop: 2.5x (proteger de whipsaw)
- Target: 1.5x (quick profit)
- Size: 30% (reduzir exposição)
         ↓
Resultado: Trade SKIPPED (evitou -6%) ✅
```

### Cenário 3: Ranging Lateral

```
Entrada: BTC oscilando ±0.5%, volume normal
         ↓
Regime: RANGING
         ↓
Ajustes:
- Stop: 0.9x (tight, sair rápido se errar)
- Target: 1.2x (quick scalp)
- Size: 80%
         ↓
Resultado: +1.8% em 18min ✅
```

---

## 💾 Onde os Dados São Armazenados

### Em Memória (Volátil)

```
Market Analyzer mantém em RAM:
- Últimos 50 trades (deque)
- Cache de análise (60s TTL)
- Métricas de performance
```

**⚠️ IMPORTANTE:** Ao reiniciar o bot, o histórico em memória é perdido!

### Persistente (MongoDB)

```
Todos os trades fechados vão para:
database: trading_bot
collection: trades

Campos relevantes:
- symbol
- pnl_percentage
- opened_at / closed_at
- market_regime (adicionado pelo Market Analyzer)
```

Para recuperar histórico após restart:

```bash
python feed_market_analyzer.py --days 7
```

---

## 🔧 Configuração e Tunning

### Variáveis de Ambiente (.env)

```env
LLM_ENABLED=true              # Habilitar Market Analyzer
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral          # Modelo usado (mistral/llama2/etc)
```

### Ajustar Sensibilidade (llm_market_analyzer.py)

```python
# Linha ~131
self.market_cache_ttl = 60  # Cache de análise (segundos)
                            # ↓ Aumentar = menos requisições ao Ollama
                            # ↑ Diminuir = análises mais frequentes

# Linha ~133
self.max_history = 50       # Trades no histórico
                            # ↑ Aumentar = mais contexto (usa mais RAM)
                            # ↓ Diminuir = foca em trades recentes
```

---

## 📈 Métricas e Monitoramento

### No Dashboard

O componente `MarketRegimeCard` mostra:

- Regime atual detectado
- Volatilidade (percentil)
- Força da tendência
- Quantidade de trades no histórico
- Latência média das análises

### Via API

```bash
curl http://localhost:8000/api/llm/market-analyzer/status
```

Resposta:

```json
{
  "enabled": true,
  "available": true,
  "metrics": {
    "market_analyses": 245,
    "trade_recommendations": 312,
    "avg_latency_ms": 2340
  },
  "recent_analyses": [
    {
      "regime": "bull_trending",
      "volatility_percentile": 42,
      "trend_strength": 78,
      "cached": false
    }
  ],
  "trade_history_size": 50
}
```

---

## 🚀 Melhorias Futuras

### Já Implementado ✅

- Análise de regime em tempo real
- Ajustes adaptativos de stops/targets
- Feedback loop com histórico
- Cache inteligente (60s)
- Fallback gracioso se Ollama cair

### Roadmap 🗺️

- [ ] Persistência do histórico em MongoDB
- [ ] Análise multi-timeframe (1m, 5m, 15m)
- [ ] Correlações entre altcoins
- [ ] Detecção de padrões de manipulação (pump/dump)
- [ ] Modo "paper trading" para testar ajustes

---

## ❓ Perguntas Frequentes

### 1. O Market Analyzer precisa ser treinado antes?

**Não!** Ele funciona desde o primeiro trade usando:

- Conhecimento do modelo Mistral 7B (pré-treinado)
- Dados de mercado em tempo real
- À medida que trades acontecem, ele aprende e melhora

### 2. Quanto tempo leva cada análise?

**2-5 segundos** dependendo do hardware:

- Dell E7450 (i5-5300U): ~4s
- CPU moderno (i7): ~2s
- Cache hit: <100ms

### 3. O que acontece se Ollama cair?

O bot continua funcionando normalmente usando:

- Stops/targets padrão (sem multiplicadores)
- Análise técnica tradicional (RSI, MACD)
- Machine Learning Filter

### 4. Posso usar outro modelo além do Mistral?

Sim! Modelos compatíveis:

```bash
ollama pull llama2      # Mais rápido, menos preciso
ollama pull mistral     # Balanceado (recomendado)
ollama pull mixtral     # Mais preciso, mais lento
```

Altere em `.env`:

```env
OLLAMA_MODEL=llama2
```

### 5. Como ver logs detalhados?

```bash
# No terminal do backend:
tail -f logs/trading_bot.log | grep "LLM Market"
```

---

## 📚 Referências

- **Código Fonte:** `backend/bot/llm_market_analyzer.py`
- **Testes:** `test_market_analyzer.py`
- **Alimentação:** `feed_market_analyzer.py`
- **API Route:** `backend/api/routes/llm.py`
- **Frontend:** `frontend/src/components/dashboard/MarketRegimeCard.jsx`

---

**Criado em:** 27/01/2026
**Versão:** 1.0.0
**Hardware Target:** Dell E7450 (i5-5300U, 12GB RAM)
