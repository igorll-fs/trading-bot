# 📘 Trading Bot - Documentação Completa do Projeto

**Versão**: 2.0  
**Última Atualização**: 15/01/2026  
**Status**: Produção em Testnet

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Como Iniciar](#como-iniciar)
4. [Estratégias de Trading](#estratégias-de-trading)
5. [Machine Learning](#machine-learning)
6. [Validação em Testnet](#validação-em-testnet)
7. [Estrutura de Arquivos](#estrutura-de-arquivos)
8. [Segurança](#segurança)

---

## 🎯 Visão Geral

### O que é este projeto?

Bot de trading automatizado para **Binance Spot** (sem alavancagem) com:
- ✅ Análise técnica multi-indicador (EMA, RSI, MACD, Bollinger, ATR, ADX)
- ✅ Sistema de Machine Learning adaptativo
- ✅ Gestão inteligente de risco (position sizing, SL/TP dinâmicos, trailing stop)
- ✅ Dashboard React para monitoramento em tempo real
- ✅ Notificações Telegram
- ✅ MongoDB para persistência de dados
- ✅ Backtesting e análise de performance

### Tecnologias

**Backend**:
- Python 3.11+
- FastAPI (API REST)
- python-binance (integração Binance)
- MongoDB (persistência)
- NumPy/Pandas (análise técnica)

**Frontend**:
- React 18
- Tailwind CSS
- Recharts (gráficos)
- Axios (HTTP client)

**DevOps**:
- PowerShell (automação Windows)
- Git/GitHub
- Cloudflare Tunnels (acesso remoto)

---

## 🏗️ Arquitetura do Sistema

### Estrutura de Módulos

```
backend/
├── server.py              # FastAPI - API REST (/api/*)
├── bot/
│   ├── trading_bot.py     # Orquestrador principal
│   ├── selector.py        # Seleção de moedas (trending + filtros)
│   ├── strategy.py        # Análise técnica e sinais
│   ├── risk_manager.py    # Gestão de risco e posições
│   ├── learning_system.py # Machine Learning adaptativo
│   ├── binance_client.py  # Cliente Binance com retry
│   ├── telegram_client.py # Notificações
│   ├── market_cache.py    # Cache de dados de mercado
│   └── config.py          # Configurações persistentes
└── scripts/
    └── backtest_strategy.py

frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx  # Painel principal
│   │   ├── Settings.jsx   # Configurações
│   │   ├── Trades.jsx     # Histórico de trades
│   │   └── Instructions.jsx
│   └── lib/api.js         # Cliente HTTP
```

### Fluxo de Execução

```
1. Início do Bot
   ├── Limpa ordens abertas
   ├── Sincroniza account
   ├── Notifica Telegram
   └── Loop principal (15s)

2. Loop de Trading (a cada 15s)
   ├── Circuit breaker check
   ├── Verifica posições abertas (SL/TP/trailing)
   └── Se posições < max:
       └── Busca nova oportunidade

3. Busca de Oportunidade
   ├── selector.select_best_crypto()
   │   ├── Atualiza trending 24h
   │   ├── Filtra: volume > 100k, spread < 0.3%
   │   ├── Analisa cada par
   │   └── Retorna melhor score
   ├── ML: calculate_opportunity_score()
   ├── ML: should_take_trade() → filtro
   ├── Calcula position size (risk 1.5%)
   └── Executa ordem + salva posição

4. Verificação de Posições
   ├── Busca preço atual
   ├── Verifica SL/TP
   ├── Atualiza trailing stop
   └── Fecha se necessário
       └── ML: learn_from_trade()
```

---

## 🚀 Como Iniciar

### Pré-requisitos

1. **Python 3.11+** instalado
2. **Node.js 18+** instalado
3. **MongoDB** rodando (localhost:27017)
4. **Conta Binance** (ou Testnet)

### Instalação Rápida

#### 1️⃣ Instalar Dependências

```powershell
cd C:\Users\SEU_USUARIO\Desktop\17-10-2025-main
.\scripts\install.bat
```

Isso vai:
- Instalar dependências Python (requirements.txt)
- Instalar dependências Node (package.json)
- Criar virtual environment Python

#### 2️⃣ Configurar Credenciais

**Backend**: Editar `backend/.env`

```env
# Binance API (obtenha em https://www.binance.com/pt-BR/my/settings/api-management)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
USE_TESTNET=true

# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_bot

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789
```

**Frontend**: Editar `frontend/.env`

```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

#### 3️⃣ Iniciar Sistema

**Automático (Recomendado)**:
```powershell
.\scripts\start_all.bat
```

**Manual**:

Terminal 1 (Backend):
```powershell
cd backend
python server.py
```

Terminal 2 (Frontend):
```powershell
cd frontend
npm start
```

#### 4️⃣ Acessar Dashboard

Abrir navegador em: **http://localhost:3000**

#### 5️⃣ Configurar Bot

1. Ir em **Settings** (⚙️)
2. Ativar **Testnet Mode** (recomendado para testes)
3. Configurar:
   - **Risk per Trade**: 1.5% (iniciante)
   - **Max Positions**: 2
   - **Min Signal Strength**: 80
4. Clicar em **Save Config**
5. Voltar ao **Dashboard** e clicar **START BOT**

### Parar Sistema

```powershell
.\scripts\stop_all.bat
```

---

## 🎯 Estratégias de Trading

### Estratégia Principal: Multi-Indicador Adaptativo

**Tipo**: Trend-following (segue a tendência)  
**Timeframe**: 15 minutos  
**Moedas**: Top 15 (BTC, ETH, BNB, SOL, XRP, ADA, etc.)  
**Max Posições**: 2-3 simultâneas  

### Indicadores Técnicos

#### 1. EMA (Exponential Moving Average)
- **Parâmetros**: EMA(12) e EMA(26)
- **Lógica**: EMA 12 > EMA 26 = Tendência de alta ✅

#### 2. RSI (Relative Strength Index)
- **Parâmetro**: RSI(14)
- **Zonas**:
  - RSI < 30: Oversold (possível compra)
  - RSI 50-70: Normal (ideal para entrada)
  - RSI > 70: Overbought (cuidado)

#### 3. MACD (Moving Average Convergence Divergence)
- **Parâmetros**: 12, 26, 9
- **Lógica**: MACD > Signal Line = Momentum positivo ✅

#### 4. Bollinger Bands
- **Parâmetros**: 20 períodos, 2 desvios
- **Uso**: Detecção de volatilidade e suporte/resistência

#### 5. ATR (Average True Range)
- **Uso**: Cálculo de stop loss e take profit dinâmicos

#### 6. ADX (Average Directional Index)
- **Uso**: Confirma força da tendência
- **Filtro**: ADX > 30 (tendência forte), bloqueio se < 25

### Lógica de Entrada (BUY)

```
✅ EMA 12 > EMA 26 (tendência de alta)
✅ RSI entre 50-70 (não sobrecomprado)
✅ MACD > Signal Line (momentum positivo)
✅ ADX > 30 (tendência forte)
✅ Volume > 100k USDT (liquidez)
✅ Spread < 0.3% (baixo custo)
✅ Score ML > 80 (confiança alta)
```

### Gestão de Risco

**Position Sizing**:
- Risco por trade: **1.5%** do capital
- Cálculo baseado em ATR para stop loss

**Stop Loss**:
- **Alta volatilidade**: 2.5x ATR
- **Normal**: 2.0x ATR
- **Baixa volatilidade**: 1.8x ATR

**Take Profit**:
- Risk/Reward ratio: **2.5:1**
- Exemplo: Se risco $10, alvo $25 de lucro

**Trailing Stop**:
- Ativa em 0.5% de lucro
- Step de 0.3%

---

## 🤖 Machine Learning

### Sistema Adaptativo

O bot possui um sistema de ML que **aprende com os trades** e ajusta parâmetros automaticamente.

### Ajustes Realizados

**1. Filtros de Seleção**:
- `min_volume`: Se trades recentes com baixo volume falharam, aumenta threshold
- `min_change_24h`: Ajusta baseado em performance

**2. Stop Loss**:
- Se muitos stops atingidos: aumenta SL (mais conservador)
- Se poucos stops: diminui SL (mais agressivo)

**3. Position Size**:
- Aumenta posição em trades vencedores
- Diminui posição em trades perdedores

**4. Confiança (Confidence Score)**:
- Trades bem-sucedidos aumentam confidence
- Trades ruins diminuem confidence
- Usado para filtrar oportunidades fracas

### Persistência

Estado ML salvo em MongoDB:
```json
{
  "parameter_adjustments": { ... },
  "performance_history": [ ... ],
  "learning_stats": { ... }
}
```

---

## 🧪 Validação em Testnet

### Status Atual

**Início**: 20/12/2025  
**Duração**: 5-7 dias  
**Status**: ✅ Em andamento  

### Correções Aplicadas (9 mudanças)

#### strategy.py (6 correções)
- ✅ `activation_threshold`: 7.0 → **9.0** (sinais mais fortes)
- ✅ `min_strength_required`: 75 → **80** (qualidade mínima)
- ✅ `higher_adx`: >25 → **>30** (tendência forte)
- ✅ `volume_delta`: ≥0.05 → **≥0.20** + penalidade <0.10
- ✅ `buy_vol_pct`: >55% → **>58%** + penalidade se <52%
- ✅ **NOVO**: Bloqueio mercado ranging (ADX < 25)

#### risk_manager.py (2 correções)
- ✅ ATR multipliers reduzidos ~50%:
  - Alta vol: 5.0→2.5 (SL), 15.0→7.5 (TP)
  - Normal: 3.5→2.0 (SL), 12.0→6.0 (TP)
  - Baixa vol: 3.0→1.8 (SL), 10.0→5.4 (TP)
- ✅ Risk/Reward: 3.0 → **2.5**

#### config.py (1 correção abrangente)
- ✅ `max_positions`: 3 → **2**
- ✅ `risk_percentage`: 2.0% → **1.5%**
- ✅ `min_signal_strength`: 60 → **80**
- ✅ `min_change_percent`: 0.5% → **1.0%**
- ✅ `min_quote_volume`: 50k → **100k**
- ✅ `stop_loss`: 1.5% → **1.2%**
- ✅ `reward_ratio`: 2.0 → **2.5**

### Metas de Validação

| Métrica | Antes | Meta | Status |
|---------|-------|------|--------|
| **Profit Factor** | 0.271 ❌ | ≥ 1.5 | 🟡 Aguardando |
| **Win Rate** | 33.3% ❌ | ≥ 50% | 🟡 Aguardando |
| **Trades/dia** | 18 ❌ | ≤ 10 | 🟡 Aguardando |
| **Max Drawdown** | -330 USDT ❌ | < 100 USDT | 🟡 Aguardando |

**Critérios de Sucesso**:
- ✅ PF ≥ 1.5 (lucratividade)
- ✅ WR ≥ 50% (consistência)
- ✅ Trades/dia ≤ 10 (evitar overtrading)
- ✅ 7 dias consecutivos sem bugs críticos

---

## 📁 Estrutura de Arquivos

```
17-10-2025-main/
│
├── 📄 README.md              # Visão geral do projeto
├── 📄 .env.example           # Template de configuração
├── 📄 .gitignore             # Arquivos ignorados pelo Git
│
├── 📂 backend/               # Backend Python
│   ├── server.py             # API FastAPI
│   ├── requirements.txt      # Dependências
│   ├── .env                  # Configurações (não versionar!)
│   └── bot/                  # Módulos do bot
│       ├── __init__.py
│       ├── trading_bot.py    # Motor principal
│       ├── strategy.py       # Estratégias e análise
│       ├── selector.py       # Seleção de moedas
│       ├── risk_manager.py   # Gestão de risco
│       ├── learning_system.py # Machine Learning
│       ├── binance_client.py # Cliente Binance
│       ├── telegram_client.py # Notificações
│       ├── market_cache.py   # Cache de dados
│       └── config.py         # Configurações
│
├── 📂 frontend/              # Dashboard React
│   ├── package.json          # Dependências Node
│   ├── .env                  # Config frontend
│   ├── src/
│   │   ├── App.js
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx # Painel principal
│   │   │   ├── Settings.jsx  # Configurações
│   │   │   ├── Trades.jsx    # Histórico
│   │   │   └── Instructions.jsx
│   │   ├── components/       # Componentes UI
│   │   └── lib/api.js        # Cliente HTTP
│   └── public/
│
├── 📂 scripts/               # Automação
│   ├── install.bat           # Instalação completa
│   ├── start_all.bat         # Iniciar tudo
│   ├── stop_all.bat          # Parar tudo
│   ├── monitor_bot.ps1       # Monitoramento
│   └── ...
│
├── 📂 docs/                  # Documentação
│   ├── PROJETO_COMPLETO.md  # Este arquivo
│   ├── BOT_ARCHITECTURE.md  # Arquitetura detalhada
│   ├── MACHINE_LEARNING.md  # Sistema ML
│   ├── ESTRATEGIAS.md       # Estratégias detalhadas
│   └── ...
│
└── 📂 tests/                 # Testes automatizados
    └── __init__.py
```

---

## 🔒 Segurança

### Arquivos Sensíveis (NÃO versionar)

**`.gitignore` protege**:
- `backend/.env` (credenciais API)
- `frontend/.env` (URLs)
- `*.log` (logs)
- `__pycache__/` (cache Python)
- `node_modules/` (dependências Node)
- `.venv/` (virtual environment)

### Boas Práticas

1. **Nunca commitar** credenciais reais
2. **Usar** `.env.example` como template
3. **Testnet primeiro** antes de produção
4. **Backups** regulares do MongoDB
5. **Monitorar** logs de erro
6. **Revogar** API keys antigas

### Proteção de API Keys

**Binance**:
- Restrições de IP (whitelist)
- Permissões mínimas (apenas Spot trading)
- API key separada para testnet

**Telegram**:
- Bot token em `.env`
- Validar chat ID antes de notificar

---

## 📊 Monitoramento

### Logs

**Backend**: `backend/uvicorn.log`  
**Bot**: `backend/bot/logs/trading_bot.log`  
**Erros**: `backend/bot/logs/trading_bot_errors.log`  

### Dashboard

**URL**: http://localhost:3000

**Métricas em tempo real**:
- Posições abertas
- PnL diário
- Win rate
- Trades executados
- Status do bot

### Comandos Úteis

```powershell
# Monitorar bot (15s de intervalo, 10 min de duração)
.\scripts\monitor_bot.ps1 -Interval 15 -Duration 600

# Ver últimas 50 linhas do log
Get-Content backend\bot\logs\trading_bot.log -Tail 50

# Ver erros apenas
Get-Content backend\bot\logs\trading_bot_errors.log
```

---

## 🆘 Troubleshooting

### Bot não inicia

1. **Verificar MongoDB**:
   ```powershell
   sc query MongoDB
   ```

2. **Verificar credenciais** em `backend/.env`

3. **Logs de erro**:
   ```powershell
   Get-Content backend\bot\logs\trading_bot_errors.log
   ```

### Dashboard não salva config

1. **Frontend rodando?**
   ```
   http://localhost:3000
   ```

2. **Backend respondendo?**
   ```
   http://localhost:8000/health
   ```

3. **Console do navegador** (F12) para erros JavaScript

### Trades não executam

1. **Bot está rodando?** (Dashboard: status "Running")
2. **Testnet ativo?** (Settings: Testnet Mode ON)
3. **Saldo suficiente?** (min. 100 USDT)
4. **Filtros muito restritivos?** (diminuir min_signal_strength)

---

## 📞 Contato e Suporte

**GitHub**: https://github.com/igorll-fs/trading-bot  
**Documentação**: `/docs` na raiz do projeto  

---

**Última atualização**: 15/01/2026  
**Versão do documento**: 1.0
