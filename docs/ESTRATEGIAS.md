# 🎯 Estratégias de Trading - Documentação Técnica

## Visão Geral

Este documento explica as estratégias implementadas no Trading Bot Enterprise, incluindo lógica, parâmetros, backtests e resultados reais.

---

## 📊 Estratégia Atual: Multi-Indicador Adaptativo

### O que é?

Uma estratégia **trend-following** que combina 4 indicadores técnicos com **filtros inteligentes** e **ML adaptativo**.

**Tipo**: Trend-following (segue a tendência)  
**Timeframe**: 15 minutos (candles 15m)  
**Moedas**: Top 15 (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK, ATOM, LTC, UNI, NEAR)  
**Máximo de posições**: 3 simultâneas  
**Alavancagem**: 5x (controlado)  

### Indicadores Utilizados

#### 1. **EMA (Exponential Moving Average)**
```
Objetivo: Identificar tendência
Parâmetros: EMA(12) e EMA(26)
Lógica:
  - EMA 12 > EMA 26 → Tendência de ALTA ✓
  - EMA 12 < EMA 26 → Tendência de BAIXA ✗
  - Usa para confirmar entrada
```

#### 2. **RSI (Relative Strength Index)**
```
Objetivo: Detectar sobrecompra/sobrevenda
Parâmetro: RSI(14)
Lógica:
  - RSI < 30 → Oversold (possível compra)
  - RSI 50-70 → Zona normal (ideal para entrada em uptrend)
  - RSI > 70 → Overbought (cuidado, reversão possível)
```

#### 3. **MACD (Moving Average Convergence Divergence)**
```
Objetivo: Confirmar momentum e mudanças de tendência
Parâmetros: 12, 26, 9
Lógica:
  - MACD > Signal Line → Momentum POSITIVO ✓
  - MACD < Signal Line → Momentum NEGATIVO ✗
  - Histograma positivo e crescente → Força aumentando
```

#### 4. **Bollinger Bands**
```
Objetivo: Volatilidade e níveis de suporte/resistência
Parâmetros: 20 períodos, 2 desvios padrão
Lógica:
  - Preço > Banda Superior → Overbought
  - Preço < Banda Inferior → Oversold (suporte, compra)
  - Banda média = suporte dinâmico
```

### Fluxo de Decisão (Pseudocódigo)

```python
def should_open_trade(symbol):
    # 1️⃣ FILTRO DE MERCADO
    if not is_market_conditions_ok():
        return False  # ADX < 30 (sem tendência) ou hora illíquida
    
    # 2️⃣ FILTRO DE VOLATILIDADE
    if volatility > threshold:
        return False  # Muito volátil agora, esperar
    
    # 3️⃣ ANÁLISE TÉCNICA
    ema12 = calculate_ema(close, 12)
    ema26 = calculate_ema(close, 26)
    rsi = calculate_rsi(close, 14)
    macd, signal = calculate_macd(close)
    bb_upper, bb_middle, bb_lower = calculate_bollinger(close, 20, 2)
    
    # Validação de tendência
    if ema12 <= ema26:
        return False  # Não é uptrend
    
    # Validação de RSI
    if rsi < 50 or rsi > 70:
        return False  # Não está na zona ideal
    
    # Validação de MACD
    if macd <= signal:
        return False  # Momentum não confirmado
    
    # Validação de Bollinger
    if price >= bb_upper:
        return False  # Muito alto (overbought)
    
    # 4️⃣ ML SCORING
    ml_score = calculate_ml_score(symbol)
    if ml_score < 0.5:
        return False  # Confiança baixa
    
    # 5️⃣ TODAS AS VALIDAÇÕES PASSARAM!
    return True
```

### Entrada

**Quando abrir posição:**
```
✅ EMA 12 > EMA 26 (uptrend confirmado)
✅ RSI entre 50-70 (nem sobrevenda, nem sobrecompra)
✅ MACD > Signal (momentum positivo)
✅ Preço > Bollinger Inferior (acima do suporte)
✅ ML Score > 0.5 (confiança suficiente)
✅ ADX > 30 (tendência forte)
✅ Hora entre 8h-22h UTC (liquidez alta)
```

**Tamanho da posição:**
```
position_size = Kelly Criterion
  = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
  = Varia de 0.5% a 3% do capital por trade
```

### Saída (Stop-Loss e Take-Profit)

```python
# Stop-Loss (proteção contra perdas)
atr = average_true_range(14 candles)
stop_loss = entry_price - (2.0 * atr)  # Proteção em 2x ATR
risk = entry_price - stop_loss

# Take-Profit (captura lucros)
take_profit = entry_price + (3.0 * atr)  # Target em 3x ATR
reward = take_profit - entry_price

# Risk/Reward Ratio
rr_ratio = reward / risk  # Deve ser >= 1.5
```

**Regras de Saída:**
- ❌ **Stop-Loss automático** em 2x ATR (proteção obrigatória)
- ✅ **Take-Profit automático** em 3x ATR (captura lucros)
- ⏱️ **Time-based exit** se posição aberta > 4h sem movimento
- 📉 **RSI reversão** (RSI > 70 por 2 candles = vender)

---

## 🧠 Machine Learning Adaptativo

### Como o Bot Aprende

Após cada trade fechado, o sistema **analisa resultado** e **ajusta parâmetros**:

```python
# Exemplo: Bot perdeu 5 trades com stop-loss em 2.5x ATR
# ML detecta: "stops grandes demais"
# Ação: Reduz para 2.0x ATR

# Exemplo: Bot ganhou mais com take-profit 4x ATR
# ML detecta: "targets curtos demais"
# Ação: Aumenta para 3.5x ATR
```

### 4 Regras de Otimização

#### 1. **Stop-Loss Optimization**
```
Analisa: Qual distance de stop (em ATR) resulta em mais wins?
Aprende: Se stops largos causam mais perdas → reduz
Resultado: Stops adaptativos (2.0x a 2.5x ATR)
```

#### 2. **Take-Profit Scaling**
```
Analisa: Em qual altura (em ATR) o mercado faz reversão?
Aprende: Targets muito baixos deixam lucro na mesa
Resultado: Targets adaptativos (3.0x a 4.0x ATR)
```

#### 3. **Position Sizing (Kelly Criterion)**
```
Analisa: Win rate atual do bot
Aprende: Se win rate cai → reduz tamanho da posição
Resultado: Position size varia dinamicamente com performance
```

#### 4. **Smart Filtering**
```
Analisa: Quais moedas resultam em mais wins?
Aprende: Por qual score as wins têm início?
Resultado: ML Score threshold aumenta/diminui automaticamente
```

---

## 📈 Performance & Backtests

### Status Testnet (Atual)

```
Data: 13 de janeiro de 2026
Trades: 118 (históricos)
Saldo: $4,999.87 USDT (fundos virtuais)
Status: EM VALIDAÇÃO (5-7 dias)
```

### Métricas Calculadas

| Métrica | Alvo | Atual | Status |
|---------|------|-------|--------|
| Win Rate | >50% | ? | Validando |
| Profit Factor | >1.5 | ? | Validando |
| Sharpe Ratio | >1.5 | ? | Validando |
| Max Drawdown | <15% | ? | Validando |

### Backtests Históricos

Para validar a estratégia, rode:

```powershell
cd backend
python scripts/backtest_strategy.py --symbol BTCUSDT --days 30
```

**Parâmetros de Backtest:**
- Symbol: BTCUSDT (padrão)
- Days: 30 dias históricos
- Interval: 15m (candles)
- Capital: $1,000 USDT
- Fees: 0.1% (Binance Taker)
- Slippage: 0.05% (estimado)

---

## 🛡️ Gestão de Risco

### Kelly Criterion (Position Sizing)

**Fórmula matemática**:
```
f* = (p × b - q) / b

Onde:
  f* = fração ótima do capital por trade
  p = probabilidade de win (win rate)
  q = probabilidade de loss (1 - p)
  b = razão win/loss
```

**Exemplo**:
```
Win rate = 55%
Avg win = $50
Avg loss = $30

f* = (0.55 × 50/30 - 0.45) / (50/30)
   = (0.55 × 1.67 - 0.45) / 1.67
   = 0.467 / 1.67
   = 0.28 = 28%

Implementação prática:
  - Kelly "puro" é agressivo demais (risco de ruína)
  - Usamos 25% de Kelly = 7% do capital por trade
  - Ainda muito agressivo, limitamos a 2-3% máximo
```

### Limites Rígidos

```python
MAX_RISK_PER_TRADE = 0.02  # 2% do capital por trade
MAX_TOTAL_RISK = 0.06      # 6% total em posições abertas
MAX_POSITIONS = 3          # Máximo 3 posições simultâneas
MIN_RR_RATIO = 1.5         # Mínimo 1:1.5 risk/reward

# Circuit breaker
if daily_loss > capital * 0.05:  # -5% em um dia
    stop_trading_immediately()   # Parar tudo
```

### Correlação Entre Moedas

```python
# Não colocar 2 moedas altamente correlacionadas
# BTC e ETH = correlação 0.85 (muito alta)
# BTC e DOGE = correlação 0.78 (alta)
# BTC e LINK = correlação 0.65 (média, OK)

max_correlation = 0.7
for open_position in positions:
    if correlation(open_position, new_trade) > max_correlation:
        return False  # Rejeitar trade (muito correlacionado)
```

---

## 🔄 Próximas Estratégias (Roadmap)

### Fase 2: Momentum Breakout (TBD)

**Tipo**: Trend-following (similar à atual, mas mais agressivo)  
**Entrada**: Rompimento de resistência com volume alto  
**Saída**: Reversão de momentum  
**Status**: Aguardando validação da Fase 1

### Fase 3: Mean Reversion (TBD)

**Tipo**: Counter-trend (oposto ao atual)  
**Entrada**: Oversold (RSI < 30, preço < BB inferior)  
**Saída**: Volta para o meio (BB média)  
**Status**: Planejado para Q2 2026

### Sistema de Seleção

```python
# Manual (via Dashboard)
strategy = user_selection  # Trader escolhe qual usar

# Automático (futuro)
if market_condition == 'trending':
    strategy = momentum_breakout  # Trend-following
elif market_condition == 'ranging':
    strategy = mean_reversion  # Counter-trend
```

---

## 📊 Como Ler Os Resultados

### Dashboard Metrics

```
Win Rate: 52.5%
  ↳ De 118 trades, 62 foram vencedores

Profit Factor: 1.87
  ↳ Ganhos brutos / Perdas brutas = 1.87x

Sharpe Ratio: 1.54
  ↳ Retorno ajustado por risco (anualizado)

Max Drawdown: 12.3%
  ↳ Maior queda desde o pico
```

### Alertas Automáticos

- 🟢 **Win Rate ↑**: Estratégia melhorando
- 🟡 **Drawdown > 10%**: Possível revisar riscos
- 🔴 **Win Rate < 40%**: Pausar trading, análise necessária
- ⚡ **Sharpe < 1.0**: Retorno não compensa volatilidade

---

## 💡 Dicas Profissionais

### ✅ Fazer

- ✅ Testar em Testnet por **5-7 dias** antes de dinheiro real
- ✅ **Monitorar diariamente** os métricas de performance
- ✅ Ajustar **parâmetros de risco** conforme necessário
- ✅ Manter **máximo 3 posições** abertas
- ✅ Usar **stop-loss em todos** os trades
- ✅ Registrar **motivos de cada decisão** (para ML aprender)

### ❌ Evitar

- ❌ **Mudar parâmetros frequentemente** (deixar ML aprender)
- ❌ **Operar com dinheiro que precisa** (apenas capital especulativo)
- ❌ **Desativar stop-loss** (mesmo se "confiante")
- ❌ **Aumentar risco após perdas** (FOMO)
- ❌ **Trocar de estratégia constantemente** (sem dados suficientes)
- ❌ **Ignorar risco/reward** (sempre validar 1:2 mínimo)

---

## 📚 Referências

- [investopedia.com/indicators](https://www.investopedia.com/indicators)
- [Kelly Criterion - Wikipedia](https://en.wikipedia.org/wiki/Kelly_criterion)
- [TA-Lib Documentation](https://mrjbq7.github.io/ta-lib/)
- [Binance Trading API](https://binance-docs.github.io/apidocs/spot/en/)

---

**Última atualização**: 13 de janeiro de 2026  
**Status**: Em produção (Testnet)
