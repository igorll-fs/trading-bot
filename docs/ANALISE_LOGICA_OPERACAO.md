# =============================================================================
# ANÁLISE DA LÓGICA DE OPERAÇÃO - Trading Bot
# =============================================================================
# Documento: Problemas identificados e melhorias sugeridas
# Data: Dezembro 2025
# =============================================================================

## RESUMO EXECUTIVO

O bot possui uma arquitetura sólida com multi-timeframe, trailing stop e ML.
Porém, identificamos 10 áreas de melhoria que podem aumentar a taxa de acerto
e reduzir operações em condições desfavoráveis.

---

## 1. PROBLEMA CRÍTICO: Lógica de Score Fragmentada

### Situação Atual:
- `strategy.py` calcula `strength` (0-100) baseado em indicadores
- `selector.py` calcula `score` próprio baseado em strength + volume + volatility  
- `learning_system.py` calcula `opportunity_score` (0-1) com sua própria lógica
- Resultado: 3 sistemas de pontuação diferentes, desalinhados

### Impacto:
- Um sinal pode ter strength=70, score=85, mas opportunity_score=0.4 e ser rejeitado
- Ou ter strength=40, score=50, opportunity_score=0.6 e ser aceito
- Inconsistência dificulta tuning e entendimento

### SOLUÇÃO PROPOSTA:
Unificar em um único sistema de pontuação normalizado (0-100).

```python
# Em strategy.py - generate_signal()
# ANTES: strength = min(int(buy_score / 10 * 100), 100)
# DEPOIS: usar escala consistente com pesos explícitos

def calculate_unified_score(self, df, market_data):
    """Score unificado de 0-100 com pesos configuráveis."""
    score = 0
    weights = {
        'ema_cross': 15,      # Cruzamento EMA
        'ema_trend': 10,      # EMA 50>200
        'higher_tf': 15,      # Confirmação timeframe maior
        'macd': 10,           # MACD momentum
        'rsi': 15,            # RSI em zona favorável
        'volume': 15,         # Volume acima da média
        'vwap': 10,           # Preço vs VWAP
        'bb_position': 10,    # Posição nas Bollinger Bands
    }
    # ... calcular cada componente e somar com peso
    return min(100, max(0, score))
```

---

## 2. PROBLEMA CRÍTICO: Ausência de Confirmação de Vela

### Situação Atual:
- Sinais são gerados no MEIO da vela (a cada 15s no loop)
- A vela ainda pode mudar antes de fechar
- Isso causa sinais falsos que desaparecem quando a vela fecha

### Impacto:
- Entradas em rompimentos falsos
- Trades abertos em retração que ainda não confirmou

### SOLUÇÃO PROPOSTA:
Aguardar fechamento de vela antes de confirmar sinal.

```python
# Em trading_bot.py - _find_and_open_position()
async def _find_and_open_position(self):
    # Verificar se estamos nos últimos 30s da vela (15m = 900s)
    now = datetime.now(timezone.utc)
    seconds_in_candle = (now.minute % 15) * 60 + now.second
    
    # Se falta mais de 30s para fechar a vela, aguardar
    if seconds_in_candle < 870:  # 900 - 30 = 870
        logger.debug("Aguardando fechamento de vela (%ds restantes)", 900 - seconds_in_candle)
        return
    
    # Continuar com análise normal...
```

---

## 3. PROBLEMA IMPORTANTE: Volume Sem Direção

### Situação Atual:
- Volume é comparado com média dos últimos 20 períodos
- Não diferencia volume de compra vs volume de venda
- Alto volume em queda = sinal de fraqueza, não de força

### Impacto:
- Bot pode entrar em BUY com alto volume de VENDA (capitulação)
- Perde a informação crucial de quem está dominando

### SOLUÇÃO PROPOSTA:
Usar `taker_buy_quote_volume` disponível nas klines da Binance.

```python
# Em strategy.py - calculate_indicators()
def calculate_indicators(self, df):
    # ... indicadores existentes ...
    
    # Adicionar: Volume de compradores vs total
    df['buy_volume_pct'] = (
        pd.to_numeric(df['taker_buy_quote']) / 
        pd.to_numeric(df['quote_volume']).replace(0, 1)
    )
    
    # Média móvel do % de compra
    df['buy_volume_ma'] = df['buy_volume_pct'].rolling(10).mean()

# Em generate_signal()
# Adicionar verificação:
buy_pct = latest.get('buy_volume_pct', 0.5)
if signal == 'BUY' and buy_pct < 0.45:  # Menos de 45% é volume de compra
    buy_score -= 2.0  # Penalizar - vendedores dominando
elif signal == 'BUY' and buy_pct > 0.55:
    buy_score += 1.5  # Bonus - compradores dominando
```

---

## 4. PROBLEMA IMPORTANTE: RSI Sem Divergência

### Situação Atual:
- RSI só verifica se está em zona de sobrevenda/sobrecompra
- Não detecta divergências (preço faz novo low, RSI não)
- Divergências são sinais de reversão muito confiáveis

### SOLUÇÃO PROPOSTA:
Adicionar detecção de divergência bullish/bearish.

```python
# Em strategy.py
def detect_rsi_divergence(self, df, lookback=14):
    """Detecta divergência RSI-Preço."""
    if len(df) < lookback:
        return 'none'
    
    recent = df.tail(lookback)
    price_low_idx = recent['low'].idxmin()
    rsi_low_idx = recent['rsi'].idxmin()
    
    # Divergência Bullish: preço faz novo low, RSI faz higher low
    if price_low_idx == recent.index[-1]:  # Preço no low atual
        prev_low = recent['low'].iloc[:-1].min()
        if recent['low'].iloc[-1] < prev_low:  # Novo low de preço
            if recent['rsi'].iloc[-1] > recent['rsi'].loc[rsi_low_idx]:
                return 'bullish'  # RSI não confirmou - DIVERGÊNCIA BULLISH
    
    # Similar para divergência bearish...
    return 'none'

# No generate_signal():
divergence = self.detect_rsi_divergence(df)
if divergence == 'bullish' and signal != 'SELL':
    buy_score += 3.0  # Forte sinal de reversão
```

---

## 5. PROBLEMA MÉDIO: ATR Estático para SL/TP

### Situação Atual:
- SL = entry - 1.8 * ATR
- TP = entry + 2.2 * ATR
- Multiplicadores fixos, independente do regime de volatilidade

### Impacto:
- Em alta volatilidade, SL pode ser muito próximo (stops frequentes)
- Em baixa volatilidade, TP pode ser muito distante (nunca atinge)

### SOLUÇÃO PROPOSTA:
Ajustar multiplicadores baseado no regime de volatilidade.

```python
# Em strategy.py - generate_signal()
def get_adaptive_atr_multipliers(self, df):
    """Retorna multiplicadores ATR adaptativos baseado em volatilidade."""
    atr = df['atr'].iloc[-1]
    atr_ma = df['atr'].rolling(20).mean().iloc[-1]
    
    if pd.isna(atr_ma) or atr_ma == 0:
        return 1.8, 2.2  # Default
    
    volatility_ratio = atr / atr_ma
    
    if volatility_ratio > 1.5:  # Alta volatilidade
        return 2.5, 3.0  # SL/TP mais distantes
    elif volatility_ratio < 0.7:  # Baixa volatilidade
        return 1.2, 1.5  # SL/TP mais próximos
    else:
        return 1.8, 2.2  # Normal
```

---

## 6. PROBLEMA MÉDIO: Trailing Stop Ativa Tarde

### Situação Atual:
- Trailing ativa após `trailing_activation` % de lucro (default 0.75%)
- Em crypto, 0.75% pode ser atingido e devolvido em minutos
- Não protege lucros intermediários

### SOLUÇÃO PROPOSTA:
Implementar trailing progressivo em patamares.

```python
# Em trading_bot.py - _check_positions()
# Novo sistema de trailing em patamares:
def calculate_progressive_trailing(self, position, current_price):
    """Trailing que aperta conforme lucro aumenta."""
    entry = position['entry_price']
    side = position['side']
    
    if side == 'BUY':
        pnl_pct = ((current_price - entry) / entry) * 100
    else:
        pnl_pct = ((entry - current_price) / entry) * 100
    
    # Patamares de trailing
    if pnl_pct >= 3.0:
        trail_pct = 0.3  # Protege 70% do lucro
    elif pnl_pct >= 2.0:
        trail_pct = 0.5  # Protege 50% do lucro
    elif pnl_pct >= 1.0:
        trail_pct = 0.7  # Protege 30% do lucro
    elif pnl_pct >= 0.5:
        trail_pct = 0.9  # Protege 10% do lucro
    else:
        return None  # Não ativar trailing ainda
    
    if side == 'BUY':
        new_stop = current_price * (1 - trail_pct / 100)
        return max(new_stop, position['stop_loss'])
    else:
        new_stop = current_price * (1 + trail_pct / 100)
        return min(new_stop, position['stop_loss'])
```

---

## 7. PROBLEMA MÉDIO: Sem Filtro de Horário

### Situação Atual:
- Bot opera 24/7 com mesma lógica
- Não considera horários de baixa liquidez (ex: madrugada asiática)
- Não considera eventos conhecidos (ex: fechamento NY)

### SOLUÇÃO PROPOSTA:
Adicionar awareness de sessões de mercado.

```python
# Em config.py - adicionar
TRADING_SESSIONS = {
    'asia': {'start': 0, 'end': 8},      # 00:00 - 08:00 UTC
    'europe': {'start': 7, 'end': 16},   # 07:00 - 16:00 UTC
    'america': {'start': 13, 'end': 22}, # 13:00 - 22:00 UTC
}

# Em trading_bot.py
def _is_optimal_trading_time(self):
    """Verifica se estamos em horário de boa liquidez."""
    hour = datetime.now(timezone.utc).hour
    
    # Evitar: 22:00-00:00 UTC (gap entre sessões)
    if 22 <= hour or hour < 1:
        return False
    
    # Preferir overlap: 13:00-16:00 UTC (Europa + América)
    return True
```

---

## 8. PROBLEMA MÉDIO: Learning System Reativo Demais

### Situação Atual:
- Sistema ajusta parâmetros após CADA trade
- Um único trade ruim pode mudar significativamente os multiplicadores
- Alta variância nos parâmetros

### SOLUÇÃO PROPOSTA:
Implementar janela de aprendizado com suavização.

```python
# Em learning_system.py
class BotLearningSystem:
    def __init__(self, db):
        # ... existente ...
        self.learning_window = 20  # Mínimo de trades para ajustar
        self.smoothing_factor = 0.1  # Ajuste máximo por ciclo
    
    async def learn_from_trade(self, trade):
        # Só ajustar após N trades
        recent_trades = await self._get_recent_trades(self.learning_window)
        if len(recent_trades) < self.learning_window:
            logger.info("Aguardando mais trades para ajustar (%d/%d)",
                       len(recent_trades), self.learning_window)
            return
        
        # Calcular ajustes suavizados
        suggested_change = self._calculate_adjustment(recent_trades)
        actual_change = suggested_change * self.smoothing_factor
        
        # Aplicar ajuste limitado
        self._apply_smooth_adjustment(actual_change)
```

---

## 9. SUGESTÃO: Adicionar Filtro de Correlação BTC

### Situação:
- Altcoins são altamente correlacionadas com BTC
- Comprar ALT quando BTC está em queda livre = alto risco
- Bot não considera o estado do BTC antes de entrar

### SOLUÇÃO:
Verificar tendência do BTC antes de qualquer entrada.

```python
# Em selector.py ou trading_bot.py
async def _check_btc_health(self):
    """Verifica se BTC está em condição favorável para longs em alts."""
    btc_data = self.strategy.analyze_symbol('BTCUSDT')
    if not btc_data:
        return True  # Assumir OK se não conseguir dados
    
    # BTC em queda forte = não entrar em alts
    if btc_data.get('trend') == 'bearish' and btc_data.get('rsi', 50) < 35:
        logger.warning("BTC em queda forte - evitando novas entradas")
        return False
    
    # BTC neutro ou bullish = OK
    return True

# Em _find_and_open_position():
if not await self._check_btc_health():
    await self._notify_observing("BTC em queda - aguardando estabilização")
    return
```

---

## 10. SUGESTÃO: Adicionar Filtro de Funding Rate

### Situação (para referência futura):
- Funding rate negativo = shorts pagando longs = bom para long
- Funding rate muito positivo = longs pagando shorts = crowded trade
- Spot não tem funding, mas perpetual funding indica sentiment

### SOLUÇÃO (quando disponível):
```python
# Buscar funding rate do perpetual como proxy de sentiment
async def _check_market_sentiment(self, symbol):
    """Usa funding rate do futures como indicador de sentiment."""
    perp_symbol = symbol.replace('USDT', 'USDT')  # ou BUSD
    try:
        funding = await self._get_funding_rate(perp_symbol)
        if funding > 0.001:  # 0.1% - muito positivo
            return 'overleveraged_long'  # Cuidado com longs
        elif funding < -0.001:
            return 'overleveraged_short'  # Bom para long
        return 'neutral'
    except:
        return 'unknown'
```

---

## PRIORIZAÇÃO DAS MELHORIAS

| # | Melhoria | Impacto | Esforço | Prioridade |
|---|----------|---------|---------|------------|
| 1 | Score Unificado | Alto | Alto | Alta |
| 2 | Confirmação de Vela | Alto | Baixo | **CRÍTICA** |
| 3 | Volume com Direção | Alto | Médio | Alta |
| 4 | Divergência RSI | Médio | Médio | Média |
| 5 | ATR Adaptativo | Médio | Baixo | Média |
| 6 | Trailing Progressivo | Médio | Médio | Média |
| 7 | Filtro de Horário | Baixo | Baixo | Baixa |
| 8 | Learning Suavizado | Médio | Médio | Média |
| 9 | Filtro BTC | Alto | Baixo | **CRÍTICA** |
| 10 | Funding Rate | Baixo | Alto | Baixa |

---

## IMPLEMENTAÇÃO RECOMENDADA (Ordem)

### Fase 1 - Quick Wins (1-2 dias) ✅ COMPLETA
1. ✅ Filtro de correlação BTC (`_check_btc_health()` em `trading_bot.py`)
2. ✅ Confirmação de fechamento de vela (`_is_near_candle_close()` em `trading_bot.py`)
3. ✅ ATR adaptativo (`_get_adaptive_atr_multipliers()` em `strategy.py`)

### Fase 2 - Core Improvements (3-5 dias) ✅ COMPLETA
4. ✅ Volume com direção - taker buy % (`buy_volume_pct` em `strategy.py`)
5. ✅ Trailing progressivo (`_get_progressive_trail_factor()` em `trading_bot.py`)
6. ✅ Learning suavizado (EMA smoothing + min_trades em `learning_system.py`)

### Fase 3 - Major Refactor (1 semana+) ✅ COMPLETA
7. ✅ Score unificado (`calculate_unified_score()` em `strategy.py`)
8. ✅ Divergência RSI (`detect_rsi_divergence()` em `strategy.py`)
9. ✅ Filtro de horário (`_is_optimal_trading_time()` em `trading_bot.py`)

---

## STATUS DE IMPLEMENTAÇÃO - TODAS AS FASES COMPLETAS ✅

| Melhoria | Status | Arquivo | Método/Feature |
|----------|--------|---------|----------------|
| Filtro BTC | ✅ | `trading_bot.py` | `_check_btc_health()` |
| Confirmação vela | ✅ | `trading_bot.py` | `_is_near_candle_close()` |
| ATR adaptativo | ✅ | `strategy.py` | `_get_adaptive_atr_multipliers()` |
| Volume direção | ✅ | `strategy.py` | `buy_volume_pct` + scoring |
| Trailing progressivo | ✅ | `trading_bot.py` | `_get_progressive_trail_factor()` |
| Learning suavizado | ✅ | `learning_system.py` | EMA smoothing (α=0.15) + min 20 trades |
| Score unificado | ✅ | `strategy.py` | `calculate_unified_score()` - 0-100 com breakdown |
| Divergência RSI | ✅ | `strategy.py` | `detect_rsi_divergence()` - bullish/bearish/none |
| Filtro horário | ✅ | `trading_bot.py` | `_is_optimal_trading_time()` - sessões UTC |

---

## DETALHES DAS IMPLEMENTAÇÕES DA FASE 3

### Score Unificado (0-100)
Componentes do score com pesos:
- **EMA Cross/Trend**: 20 pontos (cross recente + tendência 50/200)
- **Higher TF Confirmation**: 15 pontos (confirmação timeframe maior)
- **MACD Momentum**: 10 pontos (histograma + direção)
- **RSI + Divergência**: 15 pontos (zona + divergência)
- **Volume (ratio + direção)**: 20 pontos (quantidade + taker buy %)
- **VWAP Position**: 10 pontos (preço vs VWAP)
- **Bollinger Position**: 10 pontos (posição nas bandas)

Qualidade do sinal:
- `excellent`: score ≥ 70
- `good`: score ≥ 55
- `fair`: score ≥ 40
- `poor`: score < 40

### Divergência RSI
Detecta divergências entre preço e RSI:
- **Bullish**: Preço faz lower low, RSI faz higher low → sinal de reversão para cima
- **Bearish**: Preço faz higher high, RSI faz lower high → sinal de reversão para baixo
- Adiciona +2.5 ao score quando divergência confirma direção do trade

### Filtro de Horário (UTC)
Sessões de mercado:
- **07:00-08:00**: Overlap Ásia+Europa
- **13:00-16:00**: Overlap Europa+América (MELHOR!)
- **04:00-07:00**: Liquidez reduzida (bloqueado)
- **22:00-00:00**: Gap entre sessões (bloqueado)

---

## CONCLUSÃO

O bot agora possui sistema completo de análise e proteção:
1. **Evitar entradas ruins** ✅ (BTC filter, vela confirmation, volume direction, horário)
2. **Proteger lucros melhor** ✅ (trailing progressivo, ATR adaptativo)
3. **Consistência** ✅ (score unificado, learning suavizado, divergência RSI)

Todos os 74 testes passam. Sistema pronto para testes em produção.

---

## CONFIGURAÇÕES NOVAS (ENV)

```env
# Learning System Suavizado
LEARNING_SMOOTHING_FACTOR=0.15      # Fator EMA (0.1-0.3 recomendado)
LEARNING_MIN_TRADES=20              # Trades mínimos antes de ajustar

# Filtro de Horário
TRADING_TIME_FILTER=true            # Habilitar filtro (default: true)
```

---

## NOVOS CAMPOS NO RETORNO DE analyze_symbol()

```python
{
    'unified_score': 75,              # Score unificado 0-100
    'signal_quality': 'excellent',    # excellent/good/fair/poor
    'score_components': {             # Breakdown do score
        'ema': 18,
        'higher_tf': 15,
        'macd': 8,
        'rsi': 12,
        'volume': 16,
        'vwap': 10,
        'bollinger': 6
    },
    'divergence': 'bullish',          # bullish/bearish/none
    # ... outros campos existentes
}
```
