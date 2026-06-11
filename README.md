# 🤖 TradingBot Enterprise — AI-Powered Crypto Trading System

<div align="center">

**End-to-end automated trading system with Machine Learning, advanced technical analysis, and self-improving AI.**

[![License](https://img.shields.io/badge/license-MIT-blue)](#)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Motor%20Async-47A248?logo=mongodb&logoColor=white)](https://mongodb.com)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Tests](https://img.shields.io/badge/Tests-109%20Passing-brightgreen)](#-tests)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](#-quickstart)

<br/>

> 🧠 **AI that learns from mistakes** · ⚡ **Real-time dashboard** · 🛡️ **Automatic risk management** · 📡 **Telegram notifications**

</div>

---

## 📌 What Is This?

An **end-to-end automated trading system** connected to Kraken (via ccxt multi-exchange), composed of:

| Layer              | Technology                  | Responsibility                              |
| ------------------ | --------------------------- | ------------------------------------------- |
| **Backend**        | Python 3.11 + FastAPI       | REST API, trading logic, ML, SSE streaming  |
| **Frontend**       | React 18 + TailwindCSS      | Real-time dashboard, glassmorphism UI       |
| **Database**       | MongoDB (async Motor)       | Trade history, ML models, reflections       |
| **AI / LLM**       | Ollama + Mistral 7B         | Contextual risk analysis (optional)         |
| **ML**             | Scikit-Learn (RF + GBM)     | Signal filtering + auto-training pipeline   |
| **Integration**    | Kraken + ccxt + Telegram    | Multi-exchange support + real-time alerts   |

---

## ✨ Key Features

### 🧠 AI Engine

| Feature                       | Details                                                                                   |
| ----------------------------- | ----------------------------------------------------------------------------------------- |
| **ML Signal Filter**          | RandomForest + GradientBoosting with TimeSeriesSplit CV — filters signals before execution |
| **Auto-Learning Pipeline**    | 60min loop: collect → clean → generate dataset → train → validate                          |
| **LLM Risk Advisor**          | Ollama (Mistral 7B) analyzes market context and suggests position adjustments              |
| **Reflection System**         | Bot self-analyzes performance hourly, generates learnings, and adjusts parameters          |
| **Advanced Pattern Analyzer** | Detects patterns by symbol, direction, period, and historical ROE                          |

### 📊 Technical Analysis

Built from scratch with `numpy`/`pandas` — no third-party indicator libraries:

- **Trend:** EMA 12/26/50/200, MACD (12/26/9), ADX(14)
- **Volatility:** Bollinger Bands (20), ATR (14)
- **Momentum:** RSI (14), Momentum (10), OBV
- **Volume:** VWAP, `buy_volume_pct` (taker buy vs quote volume)
- **Multi-timeframe:** 15m (entry) + 1h (trend confirmation)
- **Correlation:** `calculate_btc_correlation()` — returns relative to BTC
- **Market Regime:** `detect_market_regime()` → trending / ranging / volatile via ADX

### 🛡️ Risk Management (Hard Rules)

```
• Stop-Loss: mandatory on 100% of orders (hard stop on server)
• Position Sizing: Kelly Criterion (fractional 0.25) or Fixed %
• Daily loss > 5%   → Auto SHUTDOWN
• Total drawdown > 15% → HALT + Telegram notification
• Min ROI break-even: 0.27% (covers all Binance fees)
• Circuit breaker: 10 consecutive failures → 120s pause
• Post-stop-loss cooldown: prevents re-buying assets that just dropped
• BTC health check: blocks all entries when BTC is bearish
```

### 🔒 ML Guardrails (AI Safety)

Hard limits prevent financially destructive parameter drift:

```python
HARD_LIMITS = {
    "min_confidence":  (0.40, 0.70),   # Never trade with excess certainty
    "stop_loss_pct":   (0.70, 1.20),   # Stop-loss never too tight or wide
    "take_profit_pct": (0.60, 1.50),   # Minimum R/R always preserved
    "position_size":   (0.50, 1.30),   # No accidental all-in
}
```

> **Real result:** >30 dangerous parameter changes blocked in testing.

### ⚡ Real-Time Dashboard

Glassmorphism UI (dark mode) with Server-Sent Events (SSE):

- 📈 **PnL Chart** — Area chart with trade history (Recharts)
- 🎯 **AI Decision Card** — Shows AI reasoning for each trade
- 🌍 **Market Regime Card** — Trending / Ranging / Volatile in real-time
- 📋 **Activity Feed** — Live timeline: scanning, regime changes, positions
- 🏦 **Active Positions** — Entry/Qty/Size, SL→TP progress bar, unrealized PnL
- ⚙️ **Settings Page** — Configuration with live validation
- 📊 **Runtime Config Grid** — Real-time .env parameter display

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (React 18)                        │
│  Dashboard · Trades · Reflections · Settings · Instructions │
│  Recharts · SSE Stream · React-Query · Glassmorphism        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────────┐
│                   BACKEND (FastAPI :8000)                    │
│  /health · /bot/control · /trades · /performance · /stream  │
│  /config · /market · /llm · /reflection · /learning         │
│  Rate Limiting · CORS · Async Motor · Pydantic Validation   │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
┌──────▼──────┐ ┌─────▼─────┐ ┌────▼────────────────────────┐
│  TRADING    │ │    ML     │ │        INTEGRATIONS           │
│  ENGINE     │ │ PIPELINE  │ │  Kraken + ccxt (multi-exch)   │
│             │ │           │ │  Telegram Bot                 │
│ Strategy    │ │ Collector │ │  Ollama LLM (Mistral 7B)      │
│ Risk Mgr    │ │ Trainer   │ │  MongoDB (Motor Async)        │
│ Selector    │ │ Filter    │ │  Cloudflare Tunnel            │
│ Reflection  │ │ Guardrail │ └─────────────────────────────┘
│ LLM Advisor │ └───────────┘
└─────────────┘
```

### Trading Cycle (15-second loop)

```
1. SCAN      → Fetches prices for 11 pairs via ccxt (5s TTL cache, -70% API calls)
2. STRATEGY  → Applies RSI, MACD, BB, EMA, ATR, ADX, VWAP
3. ML FILTER → RandomForest validates signal (min_confidence=0.50)
4. LLM CHECK → Mistral 7B analyzes context (disabled — strategy+ML suffice)
5. RISK CALC → Kelly Criterion calculates position size
6. EXECUTE   → Simulates order (Paper Trading mode)
7. MONITOR   → Tracks stop-loss / take-profit / trailing stop
8. CLOSE     → Closes when target or stop is hit
9. LEARN     → Records outcome → feeds next ML training cycle (after 5 trades)
```

---

## 🚀 Quickstart

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
# Edit: EXCHANGE=kraken, KRAKEN_API_KEY, KRAKEN_API_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# 4. Frontend
cd frontend && npm install
npx craco build     # Production build (uses craco, not react-scripts)
```

### Start the System

```bash
# Terminal 1 — MongoDB
mongod --dbpath ~/data/mongodb --fork --logpath ~/data/mongodb/mongod.log

# Terminal 2 — Backend
cd trading-bot && .venv/bin/python backend/server.py

# Terminal 3 — Frontend (serve static build)
cd frontend && python3 -m http.server 3000 --directory build

# Start the bot via API
curl -X POST http://localhost:8000/api/bot/control \
  -H 'Content-Type: application/json' \
  -d '{"action":"start"}'
```

**Access:**
- 🖥️ Dashboard: `http://localhost:3000`
- 🔌 API: `http://localhost:8000`
- 📚 Swagger Docs: `http://localhost:8000/docs`

### Remote Access (Cloudflare Tunnel)

```bash
# Start password-protected tunnel
bash scripts/tunnel.sh
# Default password: botmaster2026
# Custom: PROXY_PASS=mysecret bash scripts/tunnel.sh
```

---

## 🧪 Tests

```bash
pytest tests/ -q
# 109 passed — unit tests + integration + performance budgets
```

**Coverage:**
- ✅ Strategy, Risk Manager, Selector, Learning System
- ✅ ML Guardrails (30+ dangerous parameter blocks verified)
- ✅ BTC health check, post-SL cooldown, circuit breaker
- ✅ API endpoints, config validation, runtime config merge

---

## 📁 Project Structure

```
trading-bot/
├── backend/
│   ├── server.py                    # FastAPI entry point (port 8000)
│   ├── bot/
│   │   ├── trading_bot.py           # Main loop (15s scan cycle)
│   │   ├── strategy.py              # 10+ technical indicators + unified scoring
│   │   ├── risk_manager.py          # Kelly Criterion + ATR stops
│   │   ├── learning_system.py       # ML parameter auto-tuning (EMA smoothed)
│   │   ├── advanced_learning.py     # Pattern analyzer per symbol/period
│   │   ├── reflection_service.py    # Hourly self-analysis
│   │   ├── llm_risk_advisor.py      # Ollama (Mistral 7B) integration
│   │   ├── llm_analyzer.py          # Signal analysis via LLM
│   │   ├── llm_market_analyzer.py   # Market regime detection via LLM
│   │   ├── market_cache.py          # 5s TTL cache (-70% API calls)
│   │   ├── selector.py              # Asset selection with volume filters
│   │   ├── binance_client.py        # Binance API wrapper (retry + testnet)
│   │   ├── memory_optimizer.py      # Aggressive GC for constrained hardware
│   │   ├── telegram_client.py       # Telegram notifications (HTML formatted)
│   │   └── config.py                # BotConfig dataclass (from_env)
│   ├── ml/
│   │   ├── model_trainer.py         # RandomForest/GradientBoosting + CV
│   │   ├── data_collector.py        # OHLCV 15m/1h/4h (15 pairs, 14 days)
│   │   ├── dataset_generator.py     # Technical features + win/loss labels
│   │   ├── ml_signal_filter.py      # Real-time inference
│   │   ├── auto_learning_pipeline.py # Full automated pipeline
│   │   └── data_cleaner.py          # Cleaning and normalization
│   └── api/routes/                  # health, bot, config, performance
│                                    # learning, market, llm, reflection
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx        # Metrics + PnL chart + activity feed
│       │   ├── Trades.jsx           # Trade history with virtualization
│       │   ├── Reflections.jsx      # Self-analysis + win rate chart
│       │   ├── Settings.jsx         # Configuration with validation
│       │   └── Instructions.jsx     # Complete setup guide
│       ├── components/
│       │   ├── dashboard/           # MetricCard, ActivityFeed, PositionsCard
│       │   └── ui/                  # 22 Radix UI components
│       ├── hooks/                   # useBotStatus, usePerformance, useTrades
│       └── providers/               # BotDataProvider (SSE + polling)
├── tests/                           # 109 passing tests
├── scripts/                         # tunnel.sh, proxy2.py, utilities
└── docs/                            # Architecture, ML, Strategy guides
```

---

## 🧩 Implementation Highlights

### Async-First Throughout

```python
# Never blocks the event loop — run_in_executor for sync code
async def _run_blocking(self, func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)

# Motor for MongoDB — queries < 2ms with covered indexes
async def get_trades(self, limit: int = 50) -> list[dict]:
    return await self.db.trades.find(
        {"status": "closed"},
        sort=[("timestamp", -1)],
        limit=limit
    ).to_list(length=limit)
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
                logger.warning(f"⚠️ BLOCKED: {key} {original:.3f} → {params[key]:.3f}")
    return params
```

### SSE for Real-Time Updates

```python
@router.get("/stream")
async def event_stream(request: Request):
    async def generate():
        while True:
            if await request.is_disconnected():
                break
            data = await get_realtime_snapshot(db)
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 📈 Performance Metrics

| Metric             | Value      | Context                              |
| ------------------ | ---------- | ------------------------------------ |
| CPU average        | < 25%      | i5-5300U dual-core                   |
| RAM (bot process)  | ~22 MB     | 12 GB total system memory            |
| MongoDB queries    | < 2ms      | With covered indexes (was 50ms)      |
| Binance API calls  | -70%       | 5s TTL cache                         |
| Tests passing      | 109        | Unit + integration + performance     |
| ML guardrail blocks| > 30       | Dangerous parameters blocked         |
| Scan loop          | 15s        | 50 pairs monitored in parallel       |

---

## 🔐 Security

- **Sensitive variables** in `.env` (never committed)
- **Rate limiting** per IP on all API routes
- **Input validation** via Pydantic on 100% of endpoints
- **Binance Testnet** — never trades real money by default
- **Cloudflare Tunnel** — remote access without opening ports, with password auth

---

## 💡 Engineering Philosophy

Built with **constraint-driven architecture** — limited hardware forced superior engineering decisions:

- **Pure `asyncio`** over multiprocessing → simpler, more efficient on dual-core
- **Generators and streams** over full DataFrames → 5x lower memory usage
- **Batch MongoDB inserts** over individual writes → 10x I/O efficiency
- **TTL cache** for API calls → 70% fewer Binance requests
- **Bounded Autonomy** — AI with explicit rules is more reliable than unconstrained AI

> _"Constraints don't limit creativity — they define it."_

---

## 👨‍💻 Author

Built as a portfolio project demonstrating expertise in:

- Distributed systems architecture (full-stack async)
- Machine Learning applied to quantitative finance
- Local LLM integration (Ollama/Mistral) in production systems
- Performance optimization for constrained hardware
- Engineering best practices: TDD, SOLID, Clean Architecture

---

<div align="center">

**⭐ If this project was useful, leave a star!**

[![GitHub](https://img.shields.io/badge/GitHub-igordev30--ops-181717?logo=github&logoColor=white)](https://github.com/igordev30-ops)

</div>
