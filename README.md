# 🤖 Trading Bot Enterprise

Bot de trading automatizado com IA auto-adaptativa para mercados crypto (Kraken). Suporta paper trade e live trade, com análise de mercado via ML, gestão de risco dinâmica e dashboard em tempo real.

## 🏗 Stack

| Componente | Tecnologia |
|------------|-----------|
| **Backend** | Python 3.11 + FastAPI |
| **Frontend** | React + Vite + Tailwind |
| **Database** | MongoDB 7 (Motor async) |
| **Exchange** | Kraken (REST + WebSocket) |
| **Server** | Uvicorn (ASGI) |
| **Proxy** | Caddy (HTTPS) |
| **Domain** | `bottrading.dev-works.uk` |

## 📊 Status Atual (Jul 2026)

| Métrica | Valor |
|---------|-------|
| **Total de Trades** | 197 |
| **Win Rate** | 61.4% |
| **ROI** | -30.9% |
| **Profit Factor** | 0.87 |
| **Melhor Trade** | +$133.35 |
| **Pior Trade** | -$86.31 |
| **Média Win** | +$17.84 |
| **Média Loss** | -$32.47 |
| **Max Drawdown** | -$374.08 |
| **Expectancy** | -$1.57/trade |
| **Posições Abertas** | 2 |
| **Streak Atual** | 4 vitórias consecutivas |

## ⚙️ Configuração Principal

### Trading

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `EXCHANGE` | kraken | Exchange utilizada |
| `PAPER_TRADE` | true | Modo simulado |
| `PAPER_TRADE_BALANCE` | $8,000 | Saldo simulado |
| `CAPITAL_INICIAL` | $1,000 | Capital por trade |
| `MAX_POSITIONS` | 2 | Posições simultâneas |
| `RISK_PER_TRADE` | 0.5% | Risco por trade |
| `RISK_STOP_LOSS_PERCENTAGE` | 1.2% | Stop loss fixo |
| `RISK_REWARD_RATIO` | 2.5 | Take profit |
| `RISK_TRAILING_STEP` | 0.5% | Trailing stop |
| `RISK_MAX_HOLD_HOURS` | 12h | Tempo máximo |

### ML / Seleção

| Parâmetro | Valor | Descrição |
|-----------|-------|-----------|
| `STRATEGY_MIN_SIGNAL_STRENGTH` | 55 | Confiança mínima |
| `LEARNING_MIN_CONFIDENCE` | 0.45 | Confiança ML mínima |
| `SELECTOR_BASE_SYMBOLS` | 12 | Moedas monitoradas |
| `SELECTOR_TRENDING_POOL_SIZE` | 20 | Pool de trending |
| `SELECTOR_MIN_QUOTE_VOLUME` | $2,000 | Volume mínimo |

## 🏃 Como Rodar

### Servidor

```bash
# Ativar venv
cd bottrading
source .venv/bin/activate

# Iniciar backend
cd backend && python server.py

# Iniciar frontend (dev)
cd frontend && npm run dev
```

### Systemd (produção)

```bash
# Verificar status
systemctl --user status bottrading

# Logs
journalctl --user -u bottrading -f
tail -f /home/tradingbot/logs/bot.log
```

## 🔌 API Endpoints

| Rota | Método | Descrição |
|------|--------|-----------|
| `/api/health` | GET | Status geral |
| `/api/performance` | GET | Performance e trades |
| `/api/market/prices` | GET | Preços atuais |
| `/api/market/signals` | GET | Sinais do bot |
| `/api/market/regime` | GET | Regime de mercado |
| `/api/market/monitored-coins` | GET | Moedas monitoradas |
| `/api/bot/status` | GET | Status do bot |
| `/api/config` | GET/PUT | Configuração |
| `/api/realtime` | GET | SSE streaming |
| `/api/learning/stats` | GET | Estatísticas ML |
| `/api/trades` | GET | Histórico de trades |
| `/api/sparkline` | GET | Gráfico sparkline |

## 🧪 Testes

```bash
cd bottrading
source .venv/bin/activate
python -m pytest tests/ -v
```

## 🔐 Chaves de API

| Serviço | Uso | Status |
|---------|-----|--------|
| Kraken API Key | Trading | ✅ Ativo |
| Kraken API Secret | Trading | ✅ Ativo |
| Telegram Bot | Notificações | ✅ Ativo |
| MongoDB | Dados | ✅ Local |

## 📁 Estrutura do Projeto

```
bottrading/
├── backend/
│   ├── server.py          # Servidor FastAPI principal
│   ├── api/               # Rotas da API
│   │   ├── routes/
│   │   │   ├── bot.py
│   │   │   ├── config.py
│   │   │   ├── health.py
│   │   │   ├── learning.py
│   │   │   ├── market.py
│   │   │   └── performance.py
│   │   └── models.py
│   ├── bot/               # Lógica do bot
│   │   ├── trading_bot.py
│   │   ├── config.py
│   │   ├── strategy_*.py
│   │   └── risk_manager.py
│   └── scripts/           # Scripts auxiliares
├── frontend/              # Dashboard React
├── tests/                 # Testes
└── logs/                  # Logs (bot.log, bot-error.log)
```

## 📈 Performance

| Métrica | Histórico (65 trades) | Atual (197 trades) |
|---------|----------------------|-------------------|
| Win Rate | 52.3% | 61.4% |
| Profit Factor | ~0.58 | 0.87 |
| Streak Atual | — | **4 vitórias consecutivas** |

## 🚀 Deploy

```bash
# O bot roda como systemd user service na VPS
# IP: 69.197.134.209
# Porta: 8088 (backend), 3000 (frontend dev)

# Atualizar código
rsync -avz -e "ssh -p 2223" ./bottrading/ administrator@69.197.134.209:/home/tradingbot/bottrading/

# Reiniciar
ssh -p 2223 administrator@69.197.134.209 "systemctl --user restart bottrading"
```

## 📝 Licença

Uso pessoal — Igor Luiz
