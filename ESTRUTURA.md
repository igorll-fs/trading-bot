# 📁 Estrutura do Projeto

```
17-10-2025-main/
│
├── 📄 README.md                 # Visão geral do projeto
├── 📄 QUICK_START.md            # Guia de início rápido
│
├── 📂 backend/                  # Backend Python
│   ├── server.py                # API FastAPI
│   ├── requirements.txt         # Dependências Python
│   └── bot/                     # Módulos do bot
│       ├── binance_client.py    # Cliente Binance
│       ├── trading_bot.py       # Motor de trading
│       ├── strategy.py          # Estratégias
│       ├── selector.py          # Seleção de ativos
│       ├── risk_manager.py      # Gestão de risco
│       └── telegram_client.py   # Notificações
│
├── 📂 frontend/                 # Dashboard React
│   ├── package.json             # Dependências Node
│   ├── src/
│   │   ├── App.js
│   │   ├── pages/               # Páginas
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Settings.jsx
│   │   │   ├── Trades.jsx
│   │   │   └── Instructions.jsx
│   │   └── components/          # Componentes UI
│   └── public/
│
├── 📂 scripts/                  # Scripts de automação
│   ├── install.bat              # Instalação completa
│   ├── start.bat                # Inicia backend + frontend
│   ├── stop.bat                 # Para sistema
│   ├── stop_backend.bat         # Para só backend
│   ├── start_system.ps1         # Script PS1 completo
│   └── monitor_bot.ps1          # Monitoramento em tempo real
│
├── 📂 docs/                     # Documentação
│   ├── README_ORIGINAL.md       # Doc técnica original
│   ├── TESTNET_GUIDE.md         # Guia de testnet
│   ├── MACHINE_LEARNING.md      # Documentação ML
│   ├── COMO_INICIAR.md          # Guia detalhado
│   ├── RELATORIO_MONITORAMENTO.md
│   └── ... (outros docs)
│
├── 📂 tests/                    # Testes automatizados
│   └── __init__.py
│
└── 📂 .archive/                 # Arquivos antigos
    └── ... (histórico)
```

## 🎯 Arquivos Principais

### Raiz
- **README.md** - Primeiro arquivo a ler
- **QUICK_START.md** - Para começar rapidamente

### Backend
- **server.py** - API REST (porta 8001)
- **bot/trading_bot.py** - Loop principal (15s scan)
- **bot/strategy.py** - Lógica de indicadores

### Frontend
- **src/pages/Dashboard.jsx** - Tela principal
- **src/pages/Settings.jsx** - Configurações

### Scripts
- **scripts/start.bat** - Mais usado
- **scripts/monitor_bot.ps1** - Para debugging

### Documentação
- **docs/TESTNET_GUIDE.md** - Essencial para iniciantes
- **docs/MACHINE_LEARNING.md** - Como funciona a IA
