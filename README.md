# 🤖 TradingBot Enterprise — IA Auto-Adaptativa para Mercados Cripto

<div align="center">

**Sistema completo de trading automatizado com Machine Learning, análise técnica avançada e auto-aperfeiçoamento contínuo.**

[![License](https://img.shields.io/badge/license-MIT-blue)](#)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Motor%20Async-47A248?logo=mongodb&logoColor=white)](https://mongodb.com)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Ollama](https://img.shields.io/badge/Ollama-LLM%20Local-black?logo=llama&logoColor=white)](https://ollama.ai)
[![Tests](https://img.shields.io/badge/Tests-30%2B%20Passing-brightgreen)](#-testes)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)](#-como-rodar)

<br/>

> 🧠 **IA que aprende com os próprios erros** · ⚡ **Dashboard em tempo real** · 🛡️ **Risk management automático** · 📡 **Notificações via Telegram**

</div>

---

## 📌 O Que É Este Projeto?

Um **sistema end-to-end de trading automatizado** conectado à Binance Testnet, composto por:

| Camada | Tecnologia | Responsabilidade |
|--------|-----------|-----------------|
| **Backend** | Python 3.11 + FastAPI | API REST, lógica de trading, ML, WebSocket |
| **Frontend** | React 18 + TailwindCSS | Dashboard em tempo real, glassmorphism UI |
| **Banco de Dados** | MongoDB (async Motor) | Histórico de trades, modelos ML, reflexões |
| **IA Local** | Ollama + Mistral 7B | Análise de risco contextual com LLM |
| **ML** | Scikit-Learn + RandomForest | Filtro de sinais com auto-treinamento |
| **Integração** | Binance API + Telegram Bot | Execução de ordens + alertas em tempo real |

---

## ✨ Funcionalidades Principais

### 🧠 Motor de Inteligência Artificial

| Feature | Detalhes |
|---------|---------|
| **ML Signal Filter** | RandomForest + GradientBoosting com TimeSeriesSplit CV — filtra sinais antes de executar |
| **Auto-Learning Pipeline** | Loop de 60min: coleta → limpeza → geração de dataset → treino → validação |
| **LLM Risk Advisor** | Ollama (Mistral 7B) analisa contexto de mercado e sugere ajustes de posição |
| **Reflection System** | Bot analisa performance a cada hora, gera *learnings* e ajusta parâmetros automaticamente |
| **Advanced Pattern Analyzer** | Detecta padrões por símbolo, direção, período e ROE histórico |

### 📊 Análise Técnica Avançada

Implementada do zero com `numpy`/`pandas`, sem bibliotecas de indicadores de terceiros:

- **Tendência:** EMA 12/26/50/200, MACD (12/26/9), ADX(14)
- **Volatilidade:** Bollinger Bands (20), ATR (14)
- **Momentum:** RSI (14), Momentum (10), OBV
- **Volume:** VWAP, `buy_volume_pct` (taker buy vs quote volume)
- **Multi-timeframe:** 15m (entrada) + 1h (confirmação de tendência)
- **Correlação:** `calculate_btc_correlation()` — retornos relativos ao BTC
- **Regime de mercado:** `detect_market_regime()` → trending / ranging / volatile via ADX

### 🛡️ Risk Management (Regras Imutáveis)

```
• Stop-Loss: obrigatório em 100% das ordens (hard stop no servidor)
• Position Sizing: Kelly Criterion fracionado (0.25) ou Fixed 2%
• Perda diária > 5%  → SHUTDOWN automático
• Drawdown total > 15% → HALT + notificação Telegram
• Min ROI break-even: 0.27% (cobre todas as taxas Binance)
• Circuit breaker: 10 falhas consecutivas → pausa 120s
```

### 🔒 ML Guardrails (Segurança da IA)

O sistema de ML tem **limites rígidos** que impedem parâmetros financeiramente destrutivos:

```python
HARD_LIMITS = {
    "confidence":    (0.40, 0.70),   # Nunca operar com excesso de certeza
    "stop_loss_pct": (0.70, 1.20),   # Stop-loss nunca muito apertado ou largo
    "take_profit":   (0.60, 1.50),   # R/R mínimo preservado
    "position_size": (0.50, 1.30),   # Sem all-in acidental
}
# Mínimo 20 trades antes de qualquer ajuste (evita overfitting)
# Ajuste máximo: ±5% por ciclo (mudanças graduais)
```

> **Resultado real:** >30 tentativas perigosas bloqueadas em produção durante testes.

### ⚡ Dashboard em Tempo Real

Interface **glassmorphism** (dark mode) com Server-Sent Events (SSE):

- 📈 **PnL Chart** — Área chart com histórico de lucro/perda (Recharts)
- 🎯 **AI Decision Card** — Mostra raciocínio da IA para cada trade
- 🌍 **Market Regime Card** — Trending / Ranging / Volatile em tempo real
- 📋 **Reflections UI** — Histórico de auto-análises com win-rate por período
- ⚙️ **Settings Page** — Configuração de parâmetros com validação ao vivo
- 🔔 **Alertas** — Notificação ao fechar aba com bot ativo

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React 18)                      │
│  Dashboard │ Trades │ Reflections │ Settings │ Instructions   │
│  Recharts  │ SSE Stream │ React-Query │ Glassmorphism UI     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  /health │ /bot/control │ /trades │ /performance │ /stream  │
│  /config │ /market │ /llm │ /reflection │ /learning        │
│  Rate Limiting │ CORS │ Async Motor (MongoDB)               │
└──────┬──────────────┬──────────────┬────────────────────────┘
       │              │              │
┌──────▼──────┐ ┌─────▼─────┐ ┌────▼────────────────────────┐
│  TRADING    │ │    ML     │ │        INTEGRAÇÕES           │
│  ENGINE     │ │ PIPELINE  │ │  Binance API (Testnet)       │
│             │ │           │ │  Telegram Bot                │
│ Strategy    │ │ Collector │ │  Ollama LLM (Mistral 7B)     │
│ Risk Mgr    │ │ Trainer   │ │  MongoDB (Motor Async)       │
│ Selector    │ │ Filter    │ │  Cloudflare Tunnel           │
│ Reflection  │ │ Guardrail │ └─────────────────────────────┘
│ LLM Advisor │ └───────────┘
└─────────────┘
```

### Fluxo de Trading (Ciclo de 15 segundos)

```
1. SCAN      → Coleta preços de ~50 pares (cache TTL 5s, -70% chamadas API)
2. STRATEGY  → Aplica RSI, MACD, BB, EMA, ATR, ADX, VWAP
3. ML FILTER → RandomForest valida sinal (min_confidence=0.5)
4. LLM CHECK → Mistral 7B analisa contexto (só se score técnico ≥ 80)
5. RISK CALC → Kelly Criterion calcula position size
6. EXECUTE   → Abre posição na Binance Testnet
7. MONITOR   → Acompanha stop-loss / take-profit / trailing stop
8. CLOSE     → Fecha posição quando atinge target ou stop
9. LEARN     → Registra resultado → próximo ciclo de treino ML
```

---

## 🛠️ Stack Tecnológica Completa

### Backend (Python 3.11+)

| Biblioteca | Uso |
|-----------|-----|
| `FastAPI 0.110` | API REST assíncrona com tipagem Pydantic |
| `Motor 3.3` | Driver MongoDB assíncrono (pool 10-50 conexões) |
| `python-binance` | Wrapper Binance API com retry automático |
| `scikit-learn 1.6` | RandomForest, GradientBoosting, TimeSeriesSplit |
| `numpy / pandas` | Cálculo vetorizado de indicadores técnicos |
| `asyncio` | Concorrência total em I/O (nunca blocking no event loop) |
| `psutil` | Hardware profiling (CPU, RAM, latência) |
| `python-telegram-bot` | Notificações em tempo real |
| `mypy` | Type checking estrito (100% type hints) |

### Frontend (React 18)

| Biblioteca | Uso |
|-----------|-----|
| `React 18 + Vite` | SPA com code-splitting por rota (lazy loading) |
| `TailwindCSS 3` | Estilização utilitária + glassmorphism customizado |
| `Recharts 3` | PnL charts, Win Rate area charts |
| `React Query 3` | Caching de dados, invalidação automática via SSE |
| `Radix UI` | Componentes acessíveis (22 primitivos) |
| `Framer Motion` | Animações performáticas |
| `react-window` | Virtualização de listas longas de trades |
| `Zod + React Hook Form` | Validação de formulários tipada |

### Banco de Dados e Infraestrutura

| Tecnologia | Detalhes |
|-----------|---------|
| **MongoDB** | Índices em `timestamp`, `symbol`, `profit`, `status` → queries <2ms |
| **Cloudflare Tunnel** | Acesso remoto seguro sem abrir portas |
| **Docker** (opcional) | Containerização para deploy |

---

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- MongoDB rodando localmente
- Conta Binance Testnet ([testnet.binance.vision](https://testnet.binance.vision))
- Ollama instalado (opcional, para análise LLM)

### Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/gameswin010-png/TradingBot.git
cd TradingBot

# 2. Configurar backend
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS
pip install -r backend/requirements.txt

# 3. Configurar variáveis de ambiente
cp backend/.env.example backend/.env
# Editar: BINANCE_API_KEY, BINANCE_SECRET_KEY, MONGODB_URI, TELEGRAM_BOT_TOKEN

# 4. Configurar frontend
cd frontend
npm install

# 5. Iniciar o sistema
# Terminal 1 — Backend:
python backend/server.py

# Terminal 2 — Frontend:
cd frontend && npm start
```

**Acesso:**
- 🖥️ Dashboard: `http://localhost:3000`
- 🔌 API: `http://localhost:8001`
- 📚 Docs Swagger: `http://localhost:8001/docs`

---

## 🧪 Testes

```bash
# Testes unitários (backend)
pytest tests/ -v

# Testes E2E (Playwright)
cd frontend && npx playwright test

# Testes de performance (budget: <3s TTI no Dell E7450)
npx playwright test --project=performance
```

**Cobertura atual:**
- ✅ 20 testes unitários (ML Guardrails, Risk Manager, Strategy, Selector)
- ✅ 10 testes E2E Playwright (Dashboard, Reflections, navegação, acessibilidade)
- ✅ Testes de performance com budget para hardware limitado

---

## 📊 Fases de Desenvolvimento (6 Sprints Autônomos)

| Fase | Nome | Entregável | Resultado |
|------|------|-----------|-----------|
| **1** | Safe Parameters | Sincronização config ↔ learning_params + HARD LIMITS | 100% safety compliance |
| **2** | Reflection Dashboard | UI glassmorphism + Win Rate charts + Polling | Dashboard funcional React 18 |
| **3** | ML Guardrails | Dual-layer validation + 20 unit tests | >30 bloqueios em produção |
| **4** | Network Learning | State persistence + Active Hours + Bounded Autonomy | Memória entre restarts |
| **5** | Hardware Optimization | GC agressivo + MongoDB indexing + Hardware profiler | Queries 2ms (-96%) |
| **6** | E2E Tests & Docs | Playwright tests + Arquitetura consolidada | 30+ testes passando |

---

## 📁 Estrutura do Projeto

```
TradingBot/
├── backend/
│   ├── server.py                    # FastAPI entry point (porta 8001)
│   ├── bot/
│   │   ├── trading_bot.py           # Loop principal (scan a cada 15s)
│   │   ├── strategy.py              # 10+ indicadores técnicos
│   │   ├── risk_manager.py          # Kelly Criterion + Stop-Loss
│   │   ├── learning_system.py       # ML parameter tuning adaptativo
│   │   ├── advanced_learning.py     # Pattern analyzer por símbolo/período
│   │   ├── reflection_service.py    # Auto-análise a cada 60min
│   │   ├── llm_risk_advisor.py      # Ollama (Mistral 7B) integration
│   │   ├── llm_analyzer.py          # Análise de sinais com LLM
│   │   ├── market_cache.py          # Cache TTL 5s (-70% chamadas API)
│   │   ├── selector.py              # Seleção de ativos com filtros
│   │   ├── binance_client.py        # Binance API wrapper (retry + testnet)
│   │   ├── memory_optimizer.py      # GC agressivo para hardware limitado
│   │   ├── telegram_client.py       # Notificações Telegram
│   │   └── config.py                # BotConfig dataclass (from_env)
│   ├── ml/
│   │   ├── model_trainer.py         # RandomForest/GradientBoosting + CV
│   │   ├── data_collector.py        # OHLCV 15m/1h/4h (15 pares, 14 dias)
│   │   ├── dataset_generator.py     # Features técnicas + labels win/loss
│   │   ├── ml_signal_filter.py      # Inferência em tempo real
│   │   ├── auto_learning_pipeline.py # Pipeline completo automático
│   │   └── data_cleaner.py          # Limpeza e normalização
│   └── api/
│       ├── models.py                # Pydantic schemas
│       ├── rate_limiting.py         # Rate limiter por IP
│       └── routes/                  # health, bot, config, performance,
│                                    # learning, market, llm, reflection
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx        # Métricas + PnL chart + AI card
│       │   ├── Trades.jsx           # Histórico com virtualização
│       │   ├── Reflections.jsx      # Auto-análise + Win Rate chart
│       │   ├── Settings.jsx         # Configuração com validação
│       │   └── Instructions.jsx     # Guia de uso
│       ├── components/
│       │   ├── dashboard/           # MetricCard, AIDecisionCard, MarketRegimeCard
│       │   └── ui/                  # 22 componentes Radix UI
│       ├── hooks/                   # useBotQueries (status, performance, trades)
│       └── providers/               # BotDataProvider (SSE stream)
├── tests/
│   ├── test_risk_manager.py
│   ├── test_strategy.py
│   ├── test_selector.py
│   ├── test_learning_system.py
│   └── unit/                        # ML Guardrails tests (20 casos)
├── docs/
│   ├── ARCHITECTURE.md
│   ├── MACHINE_LEARNING.md
│   ├── ESTRATEGIAS.md
│   └── OPERATION_GUIDE.md
└── scripts/                         # PowerShell: monitor, backup, health check
```

---

## 🧩 Destaques de Implementação

### Async-First em Todo I/O

```python
# Nunca bloqueia o event loop — asyncio.to_thread() para código síncrono
async def _run_blocking(self, func, *args):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, func, *args)
    return result

# Motor para MongoDB — queries <2ms com índices cobertos
async def get_trades(self, limit: int = 50) -> list[dict]:
    return await self.db.trades.find(
        {"status": "closed"},
        sort=[("timestamp", -1)],
        limit=limit
    ).to_list(length=limit)
```

### Pipeline de ML com Guardrails

```python
# Dual-layer validation — impede parâmetros suicidas
def _validate_safety(self, params: dict) -> dict:
    for key, (min_val, max_val) in HARD_LIMITS.items():
        if key in params:
            original = params[key]
            params[key] = max(min_val, min(max_val, params[key]))
            if params[key] != original:
                logger.warning(f"⚠️ BLOQUEADO: {key} {original:.3f} → {params[key]:.3f}")
    return params
```

### SSE para Updates em Tempo Real

```python
# Server-Sent Events — frontend sempre atualizado sem polling excessivo
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

## 📈 Métricas de Performance

| Métrica | Valor | Contexto |
|---------|-------|---------|
| CPU average | < 25% | i5-5300U dual-core |
| RAM do bot | 22.6 MB | Sistema com 12GB / 95% uso |
| MongoDB queries | < 2ms | Com índices cobertos (era 50ms) |
| Chamadas Binance API | -70% | Cache TTL 5s |
| Testes passando | 30+ | Unit + E2E Playwright |
| ML Guardrail blocks | > 30 | Parâmetros suicidas bloqueados |
| Scan loop | 15s | 50 pares monitorados simultaneamente |

---

## 🔐 Segurança

- **Variáveis sensíveis** armazenadas em `.env` (nunca commitadas)
- **Rate limiting** por IP em todas as rotas da API
- **JWT Authentication** preparado (`python-jose`)
- **Input validation** via Pydantic em 100% dos endpoints
- **Binance Testnet** — nunca opera com dinheiro real por padrão

---

## 📚 Documentação

| Documento | Conteúdo |
|----------|---------|
| [QUICK_START.md](QUICK_START.md) | Setup em 5 minutos |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diagrama completo da arquitetura |
| [docs/MACHINE_LEARNING.md](docs/MACHINE_LEARNING.md) | Pipeline ML detalhado |
| [docs/ESTRATEGIAS.md](docs/ESTRATEGIAS.md) | Lógica das estratégias de trading |
| [docs/OPERATION_GUIDE.md](docs/OPERATION_GUIDE.md) | Guia de operação diária |
| [docs/SECURITY_GUIDE.md](docs/SECURITY_GUIDE.md) | Guia de segurança |

---

## 💡 Aprendizados do Projeto

Este projeto foi desenvolvido com **constraint-driven architecture** — hardware limitado forçou decisões de engenharia superiores:

- **`asyncio` puro** em vez de multiprocessing → código mais simples e eficiente em dual-core
- **Generators e streams** em vez de DataFrames completos → uso de memória 5x menor
- **Batch inserts** no MongoDB em vez de writes individuais → I/O 10x mais eficiente
- **Cache TTL** para reduzir chamadas de API → 70% menos requests à Binance
- **Bounded Autonomy** → IA com regras explícitas é mais confiável que IA sem limites

> *"Constraints don't limit creativity — they define it."*

---

## 👨‍💻 Autor

Desenvolvido como projeto pessoal para demonstrar competências em:

- Arquitetura de sistemas distribuídos (full-stack assíncrono)
- Machine Learning aplicado a finanças quantitativas
- Integração de LLMs locais (Ollama/Mistral) em sistemas de produção
- Otimização de performance para hardware restrito
- Boas práticas de engenharia: TDD, DDD, SOLID, Clean Architecture

---

<div align="center">

**⭐ Se este projeto foi útil, deixe uma estrela!**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Conecte--se-0077B5?logo=linkedin&logoColor=white)](https://linkedin.com)
[![GitHub](https://img.shields.io/badge/GitHub-gameswin010--png-181717?logo=github&logoColor=white)](https://github.com/gameswin010-png)

</div>
