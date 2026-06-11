# TradingBot Enterprise — AI-Powered Crypto Trading System

End-to-end automated trading system with Machine Learning, advanced technical analysis, and self-improving AI.

- License: MIT
- Python 3.11+
- React 18 + TailwindCSS
- FastAPI + MongoDB (Motor Async)
- Scikit-Learn (RF + GBM)
- Exchange: Kraken via ccxt (multi-exchange)

AI that learns from mistakes | Real-time dashboard | Automatic risk management | Telegram notifications

---

## What Is This?

An end-to-end automated trading system connected to Kraken (via ccxt multi-exchange):

- Backend: Python 3.11 + FastAPI — REST API, trading logic, ML, SSE streaming
- Frontend: React 18 + TailwindCSS — Real-time dashboard, glassmorphism UI
- Database: MongoDB (async Motor) — Trade history, ML models, reflections
- AI/LLM: Ollama + Mistral 7B — Contextual risk analysis (optional)
- ML: Scikit-Learn (RF + GBM) — Signal filtering + auto-training pipeline
- Integration: Kraken + ccxt + Telegram — Multi-exchange + real-time alerts

---

## Key Features

### AI Engine

- ML Signal Filter: RandomForest + GradientBoosting with TimeSeriesSplit CV
- Auto-Learning Pipeline: 60min loop: collect, clean, generate dataset, train, validate
- LLM Risk Advisor: Ollama (Mistral 7B) analyzes market context (optional)
- Reflection System: Self-analyzes performance hourly, generates learnings
- Advanced Pattern Analyzer: Detects patterns by symbol, direction, period, ROE

### Technical Analysis

Built from scratch with numpy/pandas:

- Trend: EMA 12/26/50/200, MACD (12/26/9), ADX(14)
- Volatility: Bollinger Bands (20), ATR (14)
- Momentum: RSI (14), Momentum (10), OBV
- Volume: VWAP, buy_volume_pct (taker buy vs quote volume)
- Multi-timeframe: 15m (entry) + 1h (trend confirmation)
- Market Regime: trending / ranging / volatile via ADX

### Risk Management (Hard Rules)

- Stop-Loss: mandatory on 100% of orders
- Position Sizing: Kelly Criterion (fractional 0.25) or Fixed %
- Daily loss > 5% -> Auto SHUTDOWN
- Total drawdown > 15% -> HALT + Telegram notification
- Circuit breaker: 10 consecutive failures -> 120s pause
- Post-stop-loss cooldown: prevents re-buying assets that just dropped
- BTC health check: blocks all entries when BTC is bearish
- Progressive trailing: tighter stops as profit grows (0.3-1.0 factor)

### ML Guardrails (AI Safety)

Hard limits prevent financially destructive parameter drift:

- min_confidence: (0.40, 0.70) — Never trade with excess certainty
- stop_loss_pct: (0.70, 1.20) — Stop-loss never too tight or wide
- take_profit_pct: (0.60, 1.50) — Minimum R/R always preserved
- position_size: (0.50, 1.30) — No accidental all-in

> 30+ dangerous parameter changes blocked in testing.

---

## Live Performance Analysis (Updated 11/06/2026)

### 37 Trades Analyzed

- Win Rate: 62.16% (23 wins / 14 losses)
- Profit Factor: 0.77 (below 1.0 — losses larger than wins)
- ROI: -7.95% (Paper trade, $8000 initial)
- Best Trade: +$62.00 (ADAUSDT)
- Worst Trade: -$58.75 (LTCUSDT)
- Max Drawdown: $168.35

### Root Cause: TIME_STOP Destroying Profits

- STOP_LOSS: 27 trades, 74% WR, avg +$10.07, total +$271.89
- TIME_STOP: 10 trades, 30% WR, avg -$4.90, total -$49.03

Key Insight: Trailing active = avg +$10.07/trade. Trailing NOT active = avg -$27.60/trade.

### Optimized Parameters Applied

- RISK_STOP_LOSS_PERCENTAGE: 1.5% -> 0.8% (tighter SL cuts losses faster)
- RISK_REWARD_RATIO: 2.0 (TP more realistic at 1.6%)
- RISK_TRAILING_ACTIVATION: 0.50% -> 0.30% (trailing activates 60% faster)
- RISK_TRAILING_STEP: 0.5 -> 0.3 (more granular trailing protection)
- RISK_MAX_HOLD_HOURS: 4h -> 8h (more time for trades to materialize)
- RISK_PERCENTAGE: 0.5% -> 0.8% (compensates tighter SL)
- MAX_POSITIONS: 3 -> 2 (more conservative exposure)
- STRATEGY_MIN_SIGNAL_STRENGTH: 45 -> 55 (more selective entries)
- LEARNING_MIN_CONFIDENCE: 0.50 -> 0.58 (ML more selective)

### Worst Performing Assets (Auto-Blacklisted by ML)

- LTCUSDT: 3 trades, 33% WR, avg -$20.54
- LINKUSDT: 4 trades, 50% WR, avg -$10.37
- AVAXUSDT: 3 trades, 33% WR, avg -$11.21
- DOGEUSDT: 3 trades, 33% WR, avg -$8.70

---

## Architecture

Frontend (React 18) -> HTTP/SSE -> Backend (FastAPI :8000) -> Trading Engine + ML Pipeline + Integrations

### Multi-Strategy Engine

Regime-based strategy selection:

- Trend Following: Strong trends — EMA crossover, ADX, MACD
- Mean Reversion: Ranging markets — Bollinger Bands, RSI extremes
- Breakout: Consolidation — Donchian Channel, ATR expansion
- Grid DCA: High volatility — Grid levels, spacing
- ML Primary: All conditions — ML confidence + technicals

### Trading Cycle (15-second loop)

1. SCAN: Fetches prices for 11 pairs via ccxt (5s TTL cache, -70% API calls)
2. STRATEGY: Applies RSI, MACD, BB, EMA, ATR, ADX, VWAP
3. ML FILTER: RandomForest validates signal (min_confidence=0.58)
4. LLM CHECK: Mistral 7B analyzes context (disabled by default)
5. RISK CALC: Kelly Criterion calculates position size
6. EXECUTE: Simulates order (Paper Trading mode)
7. MONITOR: Tracks stop-loss / take-profit / trailing stop (every 15s)
8. CLOSE: Closes when target, stop, or time limit is hit
9. LEARN: Records outcome -> feeds next ML training cycle (after 5 trades)

### Progressive Trailing Stop

- Profit < 0.5%: Trail factor 1.0 (normal)
- Profit 0.5-1%: Trail factor 0.9 (10% tighter)
- Profit 1-2%: Trail factor 0.7 (30% tighter)
- Profit 2-3%: Trail factor 0.5 (50% tighter)
- Profit > 3%: Trail factor 0.3 (70% tighter — max lock)

---

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 7.0+
- Kraken account + API keys (ccxt multi-exchange ready)
- Ollama (optional — for LLM analysis, disabled by default)

### Installation

```bash
# 1. Clone
git clone https://github.com/igorll-fs/trading-bot.git
cd trading-bot

# 2. Backend
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

# 3. Configure environment
cp backend/.env.example backend/.env
# Edit: EXCHANGE=kraken, KRAKEN_API_KEY, KRAKEN_API_SECRET, TELEGRAM_BOT_TOKEN

# 4. Frontend
cd frontend && npm install
npx craco build
```

### Environment Variables (.env)

```bash
# Exchange
EXCHANGE=kraken
PAPER_TRADE=true
PAPER_TRADE_BALANCE=8000.0

# Risk Parameters (Optimized 11/06/2026)
MAX_POSITIONS=2
RISK_PERCENTAGE=0.8
RISK_STOP_LOSS_PERCENTAGE=0.8
RISK_REWARD_RATIO=2.0
RISK_TRAILING_ACTIVATION=0.30
RISK_TRAILING_STEP=0.3
RISK_MAX_HOLD_HOURS=8

# Signal Selectivity
STRATEGY_MIN_SIGNAL_STRENGTH=55
LEARNING_MIN_CONFIDENCE=0.58
LEARNING_MIN_TRADES=5

# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_bot

# Assets
SELECTOR_BASE_SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,ADAUSDT,DOGEUSDT,DOTUSDT,LINKUSDT,LTCUSDT,AVAXUSDT,ATOMUSDT
```

### Start the System

```bash
# Terminal 1 — MongoDB
mongod --dbpath ~/data/mongodb --fork --logpath ~/data/mongodb/mongod.log

# Terminal 2 — Backend
cd trading-bot && .venv/bin/python backend/server.py

# Terminal 3 — Frontend
cd frontend && python3 -m http.server 3000 --directory build

# Start the bot via API
curl -X POST http://localhost:8000/api/bot/control \
  -H 'Content-Type: application/json' \
  -d '{"action":"start"}'
```

Access:
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

### Remote Access (Cloudflare Tunnel)

```bash
bash scripts/tunnel.sh
# Default password: botmaster2026
```

---

## Tests

```bash
pytest tests/ -q
# 109 passed
```

Coverage:
- Strategy, Risk Manager, Selector, Learning System
- ML Guardrails (30+ dangerous parameter blocks verified)
- BTC health check, post-SL cooldown, circuit breaker
- API endpoints, config validation, runtime config merge

---

## Project Structure

```
trading-bot/
  backend/
    server.py                      # FastAPI entry point (port 8000)
    .env                           # Configuration (NEVER commit)
    bot/
      trading_bot.py               # Main loop (15s scan cycle)
      strategy.py                  # 10+ technical indicators + unified scoring
      strategy_engine.py           # Multi-strategy engine (regime-based)
      risk_manager.py              # Kelly Criterion + ATR stops + trailing
      learning_system.py           # ML parameter auto-tuning (EMA smoothed)
      advanced_learning.py         # Pattern analyzer per symbol/period
      reflection_service.py        # Hourly self-analysis
      llm_risk_advisor.py          # Ollama (Mistral 7B) integration
      llm_analyzer.py              # Signal analysis via LLM
      llm_market_analyzer.py       # Market regime detection via LLM
      market_cache.py              # 5s TTL cache (-70% API calls)
      selector.py                  # Asset selection with volume filters
      exchange_client.py           # Multi-exchange via ccxt
      binance_client.py            # Binance-specific wrapper (legacy)
      memory_optimizer.py          # Aggressive GC for constrained hardware
      telegram_client.py           # Telegram notifications (HTML formatted)
      config.py                    # BotConfig dataclass (from_env)
      strategies/
        trend_following.py         # EMA crossover + ADX + MACD
        mean_reversion.py          # Bollinger Bands + RSI extremes
        breakout.py                # Donchian Channel + ATR expansion
        grid_dca.py                # Grid levels + DCA
        ml_primary.py              # ML confidence + technicals
    ml/
      model_trainer.py             # RandomForest/GradientBoosting + CV
      data_collector.py            # OHLCV 15m/1h/4h
      dataset_generator.py         # Technical features + win/loss labels
      ml_signal_filter.py          # Real-time inference
      auto_learning_pipeline.py    # Full automated pipeline
      data_cleaner.py              # Cleaning and normalization
    backtesting/                   # Backtesting module
    api/routes/                    # health, bot, config, performance, etc.
  frontend/src/
    pages/
      Dashboard.jsx                # Metrics + PnL chart + activity feed
      Trades.jsx                   # Trade history with virtualization
      Reflections.jsx              # Self-analysis + win rate chart
      Settings.jsx                 # Configuration with validation
    components/
      dashboard/                   # MetricCard, ActivityFeed, PositionsCard
      ui/                          # 22 Radix UI components
    hooks/                         # useBotStatus, usePerformance, useTrades
    providers/                     # BotDataProvider (SSE + polling)
  tests/                           # 109 passing tests
  scripts/                         # tunnel.sh, proxy2.py, utilities
  docs/                            # Architecture, ML, Strategy guides
```

---

## Implementation Highlights

### Async-First Throughout

```python
# Never blocks the event loop — run_in_executor for sync code
async def _run_blocking(self, func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
```

### ML Pipeline with Dual-Layer Guardrails

```python
# Hard limits prevent suicidal parameters
def _validate_safety(self, params: dict) -> dict:
    for key, (min_val, max_val) in HARD_LIMITS.items():
        if key in params:
            original = params[key]
            params[key] = max(min_val, min(max_val, params[key]))
            if params[key] != original:
                logger.warning(f"BLOCKED: {key} {original:.3f} -> {params[key]:.3f}")
    return params
```

### Progressive Trailing Stop

```python
def _get_progressive_trail_factor(self, profit_pct: float) -> float:
    """Tighter stops as profit grows — locks in gains."""
    if profit_pct < 0.5:   return 1.0
    elif profit_pct < 1.0: return 0.9
    elif profit_pct < 2.0: return 0.7
    elif profit_pct < 3.0: return 0.5
    else:                  return 0.3
```

### BTC Health Check

```python
async def _check_btc_health(self) -> bool:
    """Blocks ALL entries when BTC is in freefall."""
    btc_change_15m = ((current - price_15m_ago) / price_15m_ago) * 100
    if btc_change_15m < -2.0:
        return False
    if btc_trend == "bearish" and btc_rsi < 35:
        return False
    return True
```

---

## Performance Metrics (Infrastructure)

- CPU average: < 25%
- RAM (bot process): ~274 MB
- MongoDB queries: < 2ms (covered indexes)
- API calls: -70% (5s TTL cache)
- Tests passing: 109
- ML guardrail blocks: > 30
- Scan loop: 15s (11 pairs monitored)

---

## Security

- Sensitive variables in .env (never committed)
- Rate limiting per IP on all API routes
- Input validation via Pydantic on 100% of endpoints
- Paper Trading mode by default
- Cloudflare Tunnel — remote access without opening ports

---

## Engineering Philosophy

Built with constraint-driven architecture:

- Pure asyncio over multiprocessing
- Generators and streams over full DataFrames (5x lower memory)
- Batch MongoDB inserts over individual writes (10x I/O efficiency)
- TTL cache for API calls (70% fewer exchange requests)
- Bounded Autonomy — AI with explicit rules is more reliable than unconstrained AI

---

## Changelog

### v2.1.0 — Performance Optimization (11/06/2026)

Root Cause Analysis:
- TIME_STOP was responsible for 62% of total losses (-$49.03)
- Trailing stop when active: avg +$10.07 (excellent)
- Trailing stop NOT active: avg -$27.60 (problem)

Parameter Optimizations:
- Tighter stop-loss (1.5% -> 0.8%) to cut losses faster
- Faster trailing activation (0.75% -> 0.30%) to lock in gains sooner
- Extended hold time (4h -> 8h) to let trades develop
- More selective signal entry (45 -> 55 strength, 0.50 -> 0.58 ML confidence)
- Reduced max positions (3 -> 2) for more conservative exposure

Architecture:
- Added multi-strategy engine (trend following, mean reversion, breakout, grid DCA, ML primary)
- Added backtesting module
- Improved multi-exchange support via ccxt

### v2.0.0 — Multi-Exchange + ML Pipeline (06/06/2026)

- Switched from Binance to Kraken via ccxt
- Added ML signal filter (RandomForest + GradientBoosting)
- Added reflection service (hourly self-analysis)
- Added LLM risk advisor (Ollama/Mistral, disabled by default)

---

## Author

Built as a portfolio project demonstrating expertise in:

- Distributed systems architecture (full-stack async)
- Machine Learning applied to quantitative finance
- Local LLM integration (Ollama/Mistral) in production systems
- Performance optimization for constrained hardware
- Engineering best practices: TDD, SOLID, Clean Architecture

GitHub: https://github.com/igorll-fs
