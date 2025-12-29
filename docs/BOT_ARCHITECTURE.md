# 🤖 Trading Bot - Arquitetura e Funcionamento

**Última atualização**: 10/12/2025  
**Versão**: 2.0 (Spot Testnet com ML)

---

## 📋 Resumo Executivo

Bot de trading automático para Binance **Spot** (sem alavancagem) com:
- Análise técnica multi-timeframe (EMA, RSI, MACD, Bollinger, ATR)
- Sistema de Machine Learning adaptativo
- Filtros de liquidez (volume, spread)
- Gestão de risco com SL/TP dinâmicos e trailing stop
- Dashboard React para configuração e monitoramento
- Notificações Telegram em tempo real

---

## 🏗️ Arquitetura de Módulos

```
backend/
├── server.py              # FastAPI - expõe /api/* (config, bot, trades, diagnostics)
├── bot/
│   ├── trading_bot.py     # Orquestrador principal (loop, posições, risco)
│   ├── selector.py        # Seleção de pares (trending, liquidez, spread)
│   ├── strategy.py        # Análise técnica e sinais (BUY/SELL/HOLD)
│   ├── risk_manager.py    # Cálculo de posição, SL/TP, trailing
│   ├── learning_system.py # ML: ajuste de parâmetros, score de confiança
│   ├── binance_client.py  # Wrapper Binance com retry e circuit breaker
│   ├── telegram_client.py # Notificações async
│   ├── market_cache.py    # Cache de preços/tickers (TTL 5s)
│   └── config.py          # BotConfig dataclass + persistência Mongo
└── scripts/
    └── backtest_strategy.py

frontend/
├── src/
│   ├── pages/Settings.jsx # Configurações (credenciais, filtros, risco)
│   ├── lib/api.js         # Cliente axios para /api/*
│   └── ...
```

---

## 🔄 Fluxo de Execução

```
1. Bot.start()
   ├── Limpa ordens abertas (sync_account)
   ├── Notifica Telegram "Bot iniciado"
   └── Inicia _trading_loop()

2. _trading_loop() (a cada 15s)
   ├── Circuit breaker check (pausa se muitas falhas)
   ├── _check_positions() → verifica SL/TP/trailing das posições abertas
   └── Se posições < max_positions:
       └── _find_and_open_position()

3. _find_and_open_position()
   ├── selector.select_best_crypto(excluded_symbols)
   │   ├── Atualiza trending (24h ticker)
   │   ├── Filtra por volume mínimo e spread máximo
   │   ├── Para cada par: strategy.analyze_symbol()
   │   └── Retorna melhor oportunidade (maior score)
   ├── learning_system.calculate_opportunity_score()
   ├── learning_system.should_take_trade() → filtro ML
   ├── risk_manager.calculate_position_size()
   ├── learning_system.adjust_stop_loss/take_profit/position_size()
   └── Executa ordem na Binance + salva posição no Mongo

4. _check_positions()
   ├── Busca preço atual
   ├── risk_manager.should_close_position(SL/TP)
   ├── Atualiza trailing stop se ativado
   └── Fecha posição se atingir SL/TP
       └── learning_system.learn_from_trade() → ajusta parâmetros
```

---

## 🧠 Sistema de Machine Learning

### Parâmetros Ajustáveis

| Parâmetro | Default | Range | Descrição |
|-----------|---------|-------|-----------|
| `min_confidence_score` | 0.50 | 0.3-0.9 | Score mínimo para entrar |
| `stop_loss_multiplier` | 1.0 | 0.5-1.2 | Multiplicador do SL base |
| `take_profit_multiplier` | 1.0 | 0.5-1.5 | Multiplicador do TP base |
| `position_size_multiplier` | 1.0 | 0.5-1.5 | Ajuste do tamanho |

### Regras de Aprendizado

1. **Win Rate < 40%** → Aumenta seletividade (confidence +0.05)
2. **Win Rate > 65%** → Diminui seletividade (confidence -0.03)
3. **Perda média > 2%** → Aperta SL (multiplier -0.1)
4. **Ganho médio < 3%** → Alarga TP (multiplier +0.1)

### Modos de Operação

```bash
BOT_LEARNING_MODE=active   # Ajusta parâmetros automaticamente
BOT_LEARNING_MODE=observe  # Apenas sugere, não altera
BOT_LEARNING_MODE=disabled # Desativa ML
```

---

## ⚙️ Configurações Principais

### Via Dashboard (Settings)

| Campo | Default | Descrição |
|-------|---------|-----------|
| `selector_min_quote_volume` | 50000 | Volume mínimo (USDT) para filtrar pares |
| `selector_max_spread_percent` | 0.25 | Spread máximo (%) |
| `strategy_min_signal_strength` | 60 | Força mínima do sinal (0-100) |
| `risk_percentage` | 2.0 | % do saldo arriscado por trade |
| `max_positions` | 3 | Posições simultâneas |
| `daily_drawdown_limit_pct` | 0 | Limite de perda diária (0=off) |

### Via .env (backend/.env)

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_bot
BINANCE_API_KEY=...
BINANCE_API_SECRET=...
BINANCE_TESTNET=true
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

---

## 📊 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/health` | Healthcheck |
| GET | `/api/config` | Configuração atual |
| POST | `/api/config` | Salvar configuração |
| POST | `/api/bot/control` | `{action: "start"\|"stop"}` |
| GET | `/api/bot/status` | Estado do bot + posições |
| GET | `/api/diagnostics` | Config (sem secrets) + último sizing |
| GET | `/api/performance` | Métricas de trades |
| GET | `/api/trades` | Histórico de trades |
| POST | `/api/bot/sync` | Cancelar ordens abertas |

---

## 🚀 Como Iniciar

```powershell
# 1. MongoDB (se não estiver como serviço)
mongod --dbpath C:\data\db

# 2. Backend
cd C:\...\backend
$env:PYTHONPATH="C:\...\backend"
..\.venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8002

# 3. Frontend
cd C:\...\frontend
npm start

# 4. Abrir http://localhost:3000
```

---

## 🛡️ Proteções Implementadas

1. **Circuit Breaker**: Pausa após 5 falhas consecutivas (cooldown 5min)
2. **Drawdown Diário/Semanal**: Para novas entradas se limite atingido
3. **Position Cap**: Divide capital entre max_positions
4. **Retry com Backoff**: Até 3 tentativas em erros transientes Binance
5. **Timestamp Sync**: Ajusta offset para evitar erro -1021
6. **Locks Asyncio**: Protege estado de posições e balanço

---

## 📝 Coleções MongoDB

| Collection | Descrição |
|------------|-----------|
| `configs` | Configuração do bot (type: bot_config) |
| `positions` | Posições abertas |
| `trades` | Histórico de trades fechados |
| `learning_data` | Parâmetros e métricas do ML |
| `ml_state` | Backup de estado ML |

---

## 🔧 Pontos de Melhoria Identificados

1. **Backtest**: Criar script para simular estratégia com dados históricos
2. **Logs estruturados**: Migrar para JSON logs para análise
3. **Métricas Prometheus**: Expor /metrics para monitoramento
4. **Testes E2E**: Cobrir fluxo completo com mocks de Binance
5. **Rate Limiting**: Controlar chamadas à API Binance
6. **Multi-strategy**: Suportar múltiplas estratégias paralelas

---

## ❓ FAQ para IA

**P: Como o bot decide entrar em um trade?**  
R: `selector.select_best_crypto()` → filtra pares por volume/spread → `strategy.analyze_symbol()` calcula indicadores e gera sinal (BUY/SELL/HOLD) + score → `learning_system.should_take_trade()` valida se score >= min_confidence.

**P: Como funciona o trailing stop?**  
R: Quando preço atinge `trailing_activation` % do TP, o SL sobe em `trailing_step` % a cada novo máximo.

**P: Onde ficam os parâmetros do ML?**  
R: `learning_data` collection (type: parameters). Carregados em `learning_system.initialize()`.

**P: Como afrouxar filtros para mais sinais?**  
R: Dashboard > Configurações: Volume mínimo ↓, Spread máx ↑, Força mínima ↓.

**P: O que é o circuit breaker?**  
R: Após 5 erros seguidos na Binance, bot pausa por 5min para evitar loop de falhas.
