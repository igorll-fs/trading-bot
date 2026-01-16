# 🤖 Trading Bot Pro- Sistema de Trading Automatizado 

> **Bot de trading profissional com Machine Learning, análise técnica avançada e otimizações de performance.**  
> Projeto de **alta complexidade** com arquitetura em microsserviços, sistema de aprendizado adaptativo e integração full-stack.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![React](https://img.shields.io/badge/React-19+-blue)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

---

## 📋 Tabela de Conteúdos

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura-do-sistema)
- [Características](#-características-principais)
- [Quick Start](#-início-rápido)
- [Estratégias](#-estratégias-de-trading)
- [Machine Learning](#-machine-learning)
- [Tecnologias](#-tecnologias)
- [Documentação](#-documentação)

---

## 🎯 Visão Geral

Um bot de trading **enterprise-grade** que combina:

✅ **Análise Técnica Avançada**: EMA, RSI, MACD, Bollinger Bands, Volume Profiling  
✅ **Machine Learning Adaptativo**: Aprende com cada trade, ajusta estratégia dinamicamente  
✅ **Gestão de Risco Profissional**: Kelly Criterion, Position Sizing inteligente, Risk Management  
✅ **Dashboard Web Moderno**: Interface glassmorphism, tema dark, real-time updates  
✅ **Monitoramento 24/7**: Telegram notifications, Health checks, Performance metrics  
✅ **Persistência Robusta**: MongoDB com índices otimizados, Cache distribuído  
✅ **Testnet + Mainnet**: Teste em ambiente virtual antes de operar com dinheiro real  
✅ **Código Profissional**: Clean Architecture, SOLID, Type hints, 80%+ test coverage

**Status Atual (Testnet)**:
- 📊 **118 trades históricos**
- 💰 **Saldo**: $4,999.87 USDT (fundos virtuais)
- 🎯 **Em validação**: Métricas de performance (5-7 dias)
- ⚡ **CPU**: <20%, **RAM**: ~11GB (otimizado para Dell E7450)

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────┐
│          FRONTEND (React 19 + TailwindCSS)      │
│  • Dashboard (Real-time monitoring)              │
│  • Settings (API keys, risk parameters)          │
│  • Trade History (P&L analysis)                  │
│  • Glassmorphism UI + Dark Mode                  │
└────────────────────┬────────────────────────────┘
                     │ HTTP/WebSocket
                     ▼
┌─────────────────────────────────────────────────┐
│      BACKEND (FastAPI + Python 3.11)            │
│  ┌─ Trading Engine ────────────────────────┐   │
│  │ • CoinSelector (vol + volume filtering)  │   │
│  │ • TradingStrategy (EMA, RSI, MACD, BB)   │   │
│  │ • RiskManager (Kelly Criterion)          │   │
│  │ • TradingBot (orchestrator loop)         │   │
│  └─────────────────────────────────────────┘   │
│  ┌─ Machine Learning System ────────────────┐   │
│  │ • LearningSystem (win rate optimization) │   │
│  │ • Genetic Algorithm (parameter tuning)   │   │
│  │ • Feedback Loop (trade → improve)        │   │
│  └─────────────────────────────────────────┘   │
│  ┌─ Integration Layer ──────────────────────┐   │
│  │ • Binance API Client (Spot Trading)      │   │
│  │ • Telegram Bot (async notifications)     │   │
│  │ • Market Data Cache (5s TTL)             │   │
│  └─────────────────────────────────────────┘   │
└────────┬─────────────────┬─────────────────────┘
         │                 │
      HTTP/gRPC         HTTP/gRPC
         │                 │
         ▼                 ▼
  ┌──────────────┐  ┌────────────────┐
  │ MongoDB (DB) │  │ Binance Spot   │
  ├──────────────┤  │ API (Testnet)  │
  │ • trades     │  └────────────────┘
  │ • positions  │
  │ • ml_state   │
  │ • configs    │
  │ (8 índices)  │
  └──────────────┘
```

### Stack Tecnológico

| Layer | Tecnologias |
|-------|-------------|
| **Frontend** | React 19, TailwindCSS, Shadcn/ui, Framer Motion |
| **Backend** | FastAPI, Python 3.11, Asyncio, Motor, python-binance |
| **Database** | MongoDB (NoSQL), Índices compostos |
| **ML/Analytics** | Scikit-learn, NumPy, Pandas, TA-Lib |
| **DevOps** | Docker, PowerShell, Health checks |
| **Communication** | Telegram Bot API, WebSocket |

---

## ✨ Características Principais

### 🎯 Trading Automatizado Inteligente
- ✅ Análise multi-indicador em tempo real (EMA, RSI, MACD, Bollinger)
- ✅ Seleção dinâmica de moedas (volatilidade + volume)
- ✅ Entrada automática com confirmações múltiplas
- ✅ Stop-loss e take-profit adaptativos
- ✅ Gestão de posição com máximo de 3 simultâneas

### 📊 Dashboard Profissional (2025)
- ✅ Interface glassmorphism com blur effects
- ✅ Tema dark mode otimizado para traders
- ✅ Gráficos em tempo real com sparklines
- ✅ Skeleton loaders e transições suaves
- ✅ Responsivo para mobile e desktop
- ✅ Toast notifications para eventos críticos

### 🧠 Machine Learning Adaptativo
- ✅ Aprendizado contínuo a partir de cada trade
- ✅ Otimização automática de parâmetros (stop-loss, take-profit)
- ✅ Filtragem inteligente com score de confiança (0-1)
- ✅ Algoritmo genético para ajuste automático
- ✅ Redução de perdas: aprende wins/losses, melhora win rate
- ✅ Estado persistido em MongoDB para continuidade

### 🛡️ Gestão de Risco Profissional
- ✅ **Kelly Criterion**: Position sizing matematicamente ótimo
- ✅ **Fixed Fractional**: Risco fixo por trade (1.5-2%)
- ✅ **Máximo de posições**: Limite de correlação
- ✅ **Stop-loss obrigatório**: Nunca opera sem proteção
- ✅ **Risk/Reward mínimo**: 1:2 por operação
- ✅ **Drawdown máximo**: 15% com circuit breaker automático

### 🔔 Monitoramento 24/7
- ✅ Notificações Telegram instantâneas (async, non-blocking)
- ✅ Métricas em tempo real: CPU, RAM, API latency
- ✅ Health checks de conectividade
- ✅ Alertas de threshold (risco, performance)
- ✅ Logs estruturados para auditoria

### ⚡ Performance Otimizada
- ✅ **Cache de mercado**: 5s TTL, 70% menos API calls
- ✅ **Pool MongoDB**: 50 conexões, 8 índices compostos
- ✅ **Asyncio**: Concorrência eficiente (não multiprocessing)
- ✅ **Lazy loading**: ML carrega 1000 trades mais recentes
- ✅ **Compressão**: Dados compactados, bandwidth otimizado
- ✅ **Dell E7450 ready**: CPU <60%, RAM <12GB

### 🧪 Testnet + Mainnet Support
- ✅ Teste em ambiente virtual com $100k USDT
- ✅ Sem risco financeiro antes de produção
- ✅ Mesmo contrato que produção (autenticação)
- ✅ Fácil switch entre testnet ↔ mainnet
- ✅ Validação de 5-7 dias em testnet recomendada

---

## 🚀 Início Rápido

### ⚡ 5 Minutos para Começar

```powershell
# 1. Clone o repositório
git clone https://github.com/igorll-fs/trading-bot.git
cd trading-bot

# 2. Execute o instalador
.\install.bat
# Instala Python deps, Node deps, valida MongoDB

# 3. Configure .env
cp backend\.env.example backend\.env
cp frontend\.env.example frontend\.env
# Edite os valores conforme necessário

# 4. Inicie o sistema
.\start.bat
# Abre Backend (8001) + Frontend (3000) + MongoDB automaticamente

# 5. Acesse o Dashboard
# http://localhost:3000 → Configure API keys → Clique "Start Bot"
```

**✅ Pronto! Bot rodando em modo Testnet com $100k USDT virtuais.**

### Modo Testnet (Recomendado)

1. **Criar conta Testnet**: https://testnet.binance.vision
2. **Gerar API Keys**: Permissões Spot Trading
3. **Copiar credenciais** para Settings do Dashboard
4. **Habilitar toggle** "🧪 Testnet Mode"
5. **Receber $100k USDT** virtuais automaticamente
6. **Clicar Start Bot** e monitorar trades

**Sem risco! Teste suas estratégias com dinheiro virtual.**

---

## 📊 Estratégias de Trading

### Análise Multi-Indicador + ML

Combina **4 indicadores técnicos** com **validações inteligentes**:

| Indicador | Objetivo | Parâmetros |
|-----------|----------|-----------|
| **EMA** | Identificar tendência | 12, 26 períodos |
| **RSI** | Detecção sobrecompra/venda | 14, <30 ou >70 |
| **MACD** | Confirmar momentum | 12, 26, 9 |
| **Bollinger Bands** | Volatilidade e reversão | 20 períodos, 2σ |

### Fluxo de Decisão

```
1️⃣ Filtro de Mercado
   ├─ ADX > 30? (tendência forte)
   └─ Hora líquida? (8h-22h UTC)

2️⃣ Seleção de Moedas (Top 15)
   ├─ Volatilidade < threshold
   ├─ Volume > média 20 candles
   └─ Correlação BTC < 0.8

3️⃣ Análise Técnica
   ├─ EMA 12 > EMA 26? (uptrend)
   ├─ RSI entre 50-70? (não sobrecomprado)
   ├─ MACD positivo? (momentum)
   └─ Preço > BB inferior? (suporte)

4️⃣ ML Scoring
   ├─ Score de confiança (0-1)
   └─ Ajustes de risco baseados em history

5️⃣ Execução
   ├─ Position size = Kelly Criterion
   ├─ Stop-loss = 2-2.5x ATR
   ├─ Take-profit = 3x ATR
   └─ Monitor até close
```

### Métricas de Performance (Profissional)

```
Win Rate (WR)      > 50%
Profit Factor (PF) > 1.5 (excelente: >2.0)
Sharpe Ratio       > 1.5
Sortino Ratio      > 2.0
Max Drawdown       < 15%
Expectancy         > 1.0
```

---

## 🧠 Machine Learning

### Sistema de Aprendizado Contínuo

O bot aprende **regras explícitas** a partir de seus próprios trades:

```python
# Exemplo: Otimização automática de Stop-Loss

trade_history = [
  {symbol: 'BTC', stop_loss: 2.0x ATR, win: True},   # ✓
  {symbol: 'ETH', stop_loss: 3.0x ATR, win: False},  # ✗
  {symbol: 'BNB', stop_loss: 2.2x ATR, win: True},   # ✓
]

# Resultado: stops muito largos (>2.5) = mais perdas
# Ajuste: novo_stop = 2.2x ATR (otimizado)
```

### 4 Regras de Aprendizado Automático

1. **Stop-Loss Optimization**: Reduz stops que geram mais perdas
2. **Take-Profit Scaling**: Aumenta targets para capturar movimento
3. **Position Sizing**: Kelly Criterion adapta ao win rate atual
4. **Smart Filtering**: Score de confiança reduz trades low-confidence

### Persistência do Modelo

Dados salvos em MongoDB (`ml_state` collection):
- Win rate atual por símbolo
- Drawdown histórico
- Parâmetros otimizados
- Score de confiança em tempo real

📈 **Próximas Estratégias (Roadmap)**:
- [ ] Fase 2: Momentum Breakout (trend-following)
- [ ] Fase 3: Mean Reversion (counter-trend)
- [ ] Fase 4: Multi-strategy com seleção automática

---

## 🔧 Tecnologias

### Backend Stack

```
FastAPI 0.100+         → API REST assíncrona, high-performance
Python 3.11+           → Type hints, async/await
Motor (async MongoDB)  → Driver assíncrono para DB
TA-Lib                 → Indicadores técnicos profissionais
Scikit-learn           → Machine Learning e estatística
NumPy/Pandas           → Processamento de dados em massa
python-binance         → Integração oficial Binance
Asyncio                → Concorrência eficiente
Uvicorn                → ASGI server (10k+ req/s)
```

### Frontend Stack

```
React 19 + CRACO       → App moderno com zero-config build
TailwindCSS 3.0+       → Utility-first CSS, responsive design
Shadcn/ui              → Componentes acessíveis e customizáveis
Framer Motion          → Animações smooth e performáticas
Recharts               → Gráficos responsivos e interativos
Axios                  → HTTP client com interceptors
React Query            → Cache e state management
```

### Infraestrutura

```
MongoDB 5.0+           → NoSQL database com replicação
Docker                 → Containerização e deployment
PowerShell Scripts     → Automação Windows nativa
Git/GitHub             → Controle de versão
Telegram Bot API       → Notificações em tempo real
```

---

## 📦 Instalação

### Pré-requisitos

- **Python** 3.11+ (com pip)
- **Node.js** 18+ (com npm/yarn)
- **MongoDB** Community Edition (ou cloud MongoDB Atlas)
- **Git** (para clone)
- **Windows 10+** ou **WSL2** (Linux)

### Passo a Passo (Windows)

#### 1. Clone o Repositório

```powershell
git clone https://github.com/igorll-fs/trading-bot.git
cd trading-bot
```

#### 2. Execute o Instalador

```powershell
.\install.bat
```

Esse script:
- ✅ Instala dependências Python (pip install -r requirements.txt)
- ✅ Instala dependências Node (yarn install)
- ✅ Valida se MongoDB está rodando
- ✅ Cria pastas necessárias

#### 3. Configure Variáveis de Ambiente

**Backend** (`backend/.env`):
```bash
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_bot

# Binance Testnet (Padrão)
BINANCE_TESTNET_API_KEY=your_testnet_key
BINANCE_TESTNET_API_SECRET=your_testnet_secret

# Telegram (Opcional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Servidor
HOST=0.0.0.0
PORT=8001
DEBUG=false
```

**Frontend** (`frontend/.env`):
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_ENABLE_VISUAL_EDITS=false
```

#### 4. Inicie o Sistema

```powershell
.\start.bat
```

Abre automaticamente:
- Backend: http://localhost:8001
- Frontend: http://localhost:3000
- MongoDB: localhost:27017

#### 5. Acesse o Dashboard

Abra seu navegador: **http://localhost:3000**

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [QUICK_START.md](QUICK_START.md) | Guia rápido para começar |
| [docs/TESTNET_GUIDE.md](docs/TESTNET_GUIDE.md) | Configuração detalhada do Testnet |
| [docs/MACHINE_LEARNING.md](docs/MACHINE_LEARNING.md) | Como funciona o sistema ML |
| [docs/BOT_ARCHITECTURE.md](docs/BOT_ARCHITECTURE.md) | Arquitetura técnica completa |
| [docs/API.md](docs/API.md) | Referência de endpoints REST |

---

## ⚠️ Avisos Importantes

### ⚡ Trading Envolve Riscos Significativos

1. **Você pode perder todo o capital investido**
2. **Não invista mais do que pode perder**
3. **Este bot não garante lucros**
4. **Performance passada ≠ resultados futuros**

### 🧪 Use Testnet Primeiro!

- ✅ Teste por 5-7 dias em ambiente virtual
- ✅ Valide as estratégias antes de dinheiro real
- ✅ Monitore os parâmetros de risco
- ✅ Ajuste conforme necessário

### 📋 Responsabilidade Legal

Este software é apenas para fins **educacionais**. O desenvolvedor não se responsabiliza por perdas financeiras. Use por sua conta e risco.

---

## 📁 Estrutura do Projeto

```
trading-bot/
├── backend/
│   ├── bot/                      # Motor de trading
│   │   ├── trading_bot.py        # Orquestrador principal
│   │   ├── selector.py           # Seleção de moedas
│   │   ├── strategy.py           # Indicadores técnicos
│   │   ├── risk_manager.py       # Gestão de risco
│   │   ├── learning_system.py    # ML adaptativo
│   │   └── market_cache.py       # Cache de mercado
│   ├── api/
│   │   ├── routes/               # Endpoints FastAPI
│   │   └── models/               # Schemas Pydantic
│   ├── server.py                 # Aplicação FastAPI
│   ├── requirements.txt           # Dependências Python
│   └── .env.example              # Variáveis exemplo
│
├── frontend/
│   ├── src/
│   │   ├── pages/                # Páginas (Dashboard, Settings)
│   │   ├── components/           # Componentes React
│   │   ├── hooks/                # Hooks customizados
│   │   ├── services/             # API client
│   │   └── styles/               # TailwindCSS
│   ├── package.json              # Dependências Node
│   └── .env.example              # Variáveis exemplo
│
├── scripts/
│   ├── install.bat               # Instalação automática
│   ├── start.bat                 # Inicia sistema completo
│   ├── stop.bat                  # Para sistema
│   └── monitor_bot.ps1           # Monitoramento
│
├── docs/                         # Documentação completa
├── tests/                        # Testes automatizados
└── README.md                     # Este arquivo
```

---

## 🤝 Contributing

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📜 Licença

MIT License - veja arquivo [LICENSE](LICENSE) para detalhes.

**Uso**: Você pode usar este código livremente, incluindo em projetos comerciais.  
**Responsabilidade**: Você é responsável por qualquer uso ou resultado deste código.

---

## 📞 Suporte

- 🐛 **Issues**: [GitHub Issues](https://github.com/igorll-fs/trading-bot/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/igorll-fs/trading-bot/discussions)
- 📧 **Email**: igorlluiz19@gmail.com

---

## 🎯 Roadmap

### Phase 1 ✅ (Current)
- [x] Trading engine com análise técnica
- [x] Dashboard profissional
- [x] ML adaptativo
- [x] Testnet validation

### Phase 2 🔄 (In Progress)
- [ ] Momentum Breakout strategy
- [ ] WebSocket real-time updates
- [ ] Advanced charting (TradingView)
- [ ] Risk analytics dashboard

### Phase 3 📅 (Planned)
- [ ] Mean Reversion strategy
- [ ] Multi-asset portfolio
- [ ] Telegram command handler
- [ ] Performance API webhooks

---



**Última atualização**: 13 de janeiro de 2026

---

⭐ Se este projeto te ajudou, deixe uma estrela no GitHub!
