# 🚀 Quick Start - Trading Bot

## Inicialização Rápida

### 1️⃣ Instalar Dependências
```powershell
.\scripts\install.bat
```

### 2️⃣ Iniciar Sistema
```powershell
.\scripts\start.bat
```

O sistema vai abrir:
- **Backend**: http://localhost:8001
- **Dashboard**: http://localhost:3000

### 3️⃣ Parar Sistema
```powershell
.\scripts\stop.bat
```

---

## 📊 Monitoramento

```powershell
# Monitorar bot em tempo real
.\scripts\monitor_bot.ps1 -Interval 15 -Duration 600
```

---

## 🔧 Configuração

### Modo Testnet (Recomendado para Testes)
1. Acesse: http://localhost:3000/settings
2. Ative "Testnet Mode"
3. Configure suas credenciais da Binance Testnet

### Parâmetros de Risco
- **Risk per Trade**: 1-2% (iniciante), 2-5% (experiente)
- **Max Leverage**: 5x (conservador), 10x (moderado), 20x (agressivo)
- **Max Positions**: 3 (recomendado para diversificação)

---

## 📁 Estrutura do Projeto

```
17-10-2025-main/
├── backend/           # API FastAPI + Bot Python
├── frontend/          # Dashboard React
├── scripts/           # Scripts de inicialização
├── docs/              # Documentação completa
├── tests/             # Testes automatizados
└── QUICK_START.md     # Este arquivo
```

---

## 📚 Documentação Completa

Todos os guias estão em `docs/`:
- **TESTNET_GUIDE.md** - Como usar testnet
- **MACHINE_LEARNING.md** - Sistema de ML
- **COMO_INICIAR.md** - Guia detalhado
- **RELATORIO_MONITORAMENTO.md** - Métricas do bot

---

## ⚡ Configurações do Bot

- **Scan Interval**: 15 segundos (ideal para futures)
- **Timeframes**: 1m, 5m, 15m, 1h
- **Indicadores**: RSI, MACD, Bollinger Bands, Volume
- **ML**: Aprendizado contínuo com trades históricos

---

## 🆘 Problemas Comuns

### Backend não inicia
```powershell
# Verificar se porta 8001 está em uso
netstat -ano | findstr "8001"

# Matar processo se necessário
Stop-Process -Id <PID> -Force
```

### Frontend não carrega
```powershell
# Verificar se porta 3000 está em uso
netstat -ano | findstr "3000"

# Reinstalar dependências
cd frontend
npm install
```

### Bot não negocia
- ✅ Verifique se está em Testnet ou Mainnet
- ✅ Confirme que as credenciais da Binance estão corretas
- ✅ Verifique saldo disponível (mínimo $100 USDT)
- ✅ Monitore logs do backend para erros

---

## 🔒 Segurança

⚠️ **ATENÇÃO**:
- Sempre teste em **Testnet** primeiro
- Nunca compartilhe suas API keys
- Use apenas fundos que pode perder
- Configure stop-loss adequados

---

## 📞 Suporte

Para mais informações, consulte a documentação em `docs/` ou os logs:
- Backend: Terminal onde rodou `scripts\start.bat`
- Frontend: Console do navegador (F12)
