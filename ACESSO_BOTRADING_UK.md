# 🌐 Seu Sistema Trading Bot - botrading.uk

**Data:** 24 de dezembro de 2025 - 15:25  
**Status:** ✅ Sistema completo rodando

---

## 🎯 SEUS DOMÍNIOS PERSONALIZADOS

### Frontend (Dashboard Principal)
```
https://botrading.uk
```
- Interface completa do trading bot
- Gráficos, configurações, controles
- Acessível de **qualquer lugar**

### API Backend
```
https://api.botrading.uk
```
- API REST completa
- Documentação interativa: https://api.botrading.uk/docs
- WebSocket para dados em tempo real

---

## ⚙️ CONFIGURAÇÃO ATUAL

### Cloudflare Tunnel (Serviço Windows)
- **Status:** ✅ Instalado e rodando automaticamente
- **Configuração:** `C:\Users\igor\.cloudflared\config.yml`
- **Túnel ID:** `9800f7d7-542b-44fe-b173-d38caae02747`

```yaml
ingress:
  - hostname: botrading.uk
    service: http://localhost:3000    # Frontend
    
  - hostname: api.botrading.uk
    service: http://localhost:8000    # Backend
```

### Serviços Locais
| Serviço | Status | Porta | Job/PID |
|---------|--------|-------|---------|
| Backend API | 🟢 Rodando | 8000 | TradingBackend (Job) |
| Frontend Dashboard | 🟢 Rodando | 3000 | TradingFrontend (Job) |
| Cloudflared Service | 🟢 Automático | - | Serviço Windows |
| MongoDB | 🟢 Rodando | 27017 | Serviço Windows |

---

## 📱 COMO ACESSAR

### Do Seu Celular/Tablet
1. Conecte à **qualquer rede Wi-Fi** (não precisa ser a mesma)
2. Abra o navegador
3. Digite: `https://botrading.uk`
4. Pronto! Dashboard completo funcionando

### De Outro Computador
- Mesma URL: `https://botrading.uk`
- API: `https://api.botrading.uk/docs`

### Na Rede Local (mais rápido)
- Frontend: http://192.168.2.105:3000
- Backend: http://192.168.2.105:8000

---

## 🔧 COMANDOS ÚTEIS

### Verificar Status
```powershell
# Verificar serviço Cloudflare
Get-Service cloudflared

# Verificar jobs PowerShell
Get-Job

# Ver logs do backend
Receive-Job -Name "TradingBackend" -Keep | Select-Object -Last 20

# Ver logs do frontend
Receive-Job -Name "TradingFrontend" -Keep | Select-Object -Last 20
```

### Reiniciar Serviços
```powershell
# Reiniciar túnel Cloudflare
Restart-Service cloudflared

# Reiniciar sistema completo
.\scripts\start_system_simple.ps1

# Parar tudo
Get-Job | Stop-Job
Get-Job | Remove-Job
```

### Testar Domínios
```powershell
# Testar API
Invoke-RestMethod https://api.botrading.uk/api/health

# Testar Frontend
Invoke-WebRequest https://botrading.uk -UseBasicParsing

# Testar local
Invoke-RestMethod http://localhost:8000/api/health
```

---

## 🚀 ENDPOINTS PRINCIPAIS

### Health & Status
- `GET /api/health` - Status geral do sistema
- `GET /api/bot/status` - Status do bot de trading

### Configuração
- `GET /api/config` - Obter configuração atual
- `PUT /api/config` - Atualizar configuração
- `POST /api/config/validate` - Validar nova configuração

### Trading
- `POST /api/bot/start` - Iniciar bot
- `POST /api/bot/stop` - Parar bot
- `GET /api/bot/positions` - Posições abertas

### Dados de Mercado
- `GET /api/market/prices` - Preços atuais
- `GET /api/market/signals` - Sinais de trading
- `GET /api/market/regime` - Regime de mercado

### Performance
- `GET /api/performance/metrics` - Métricas gerais
- `GET /api/performance/trades` - Histórico de trades
- `GET /api/stream` - WebSocket para dados em tempo real

---

## ⚠️ TROUBLESHOOTING

### Erro 530 ao acessar botrading.uk
**Causa:** Serviços locais não estão rodando ou Cloudflare não consegue conectar

**Solução:**
```powershell
# 1. Verificar se serviços estão rodando
Get-Job

# 2. Se não estiver, iniciar
.\scripts\start_system_simple.ps1

# 3. Reiniciar Cloudflare
Restart-Service cloudflared

# 4. Aguardar 30 segundos e testar
Start-Sleep -Seconds 30
Invoke-RestMethod https://api.botrading.uk/api/health
```

### Frontend não abre (porta 3000)
```powershell
# Verificar se está rodando
netstat -ano | findstr ":3000"

# Se não estiver, iniciar manualmente
cd frontend
$env:PORT=3000
yarn start
```

### Backend não responde (porta 8000)
```powershell
# Verificar processo
netstat -ano | findstr ":8000"

# Reiniciar
cd backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### Cloudflare Service não inicia
```powershell
# Verificar status
Get-Service cloudflared

# Se estiver parado, iniciar
Start-Service cloudflared

# Ver logs (se houver erro)
Get-EventLog -LogName Application -Source cloudflared -Newest 10
```

---

## 📊 STATUS DO BOT

### Configuração Atual
- **Modo:** Testnet (dinheiro virtual)
- **Exchange:** Binance Spot Testnet
- **Saldo:** $826.77 USDT (virtual)
- **Trades Históricos:** 118
- **Win Rate:** 46.6%
- **Profit Factor:** 0.35
- **Correções:** ✅ Aplicadas (threshold 9.0, stops apertados)

### Parâmetros Otimizados
- activation_threshold: 9.0 (mais seletivo)
- min_signal_strength: 80 (alta qualidade)
- max_positions: 2 (conservador)
- risk_percentage: 1.5% (baixo risco)
- Bloqueio de mercados ranging (ADX < 25)

---

## 🎯 PRÓXIMOS PASSOS

### 1. Validar Túnel Cloudflare
```powershell
# Testar se está acessível
Invoke-WebRequest https://botrading.uk -UseBasicParsing

# Se erro 530, reiniciar
Restart-Service cloudflared
```

### 2. Acessar Dashboard
- Local: http://localhost:3000
- Remoto: https://botrading.uk

### 3. Iniciar Bot (quando validado)
- Via dashboard ou
- Via API: `POST https://api.botrading.uk/api/bot/start`

### 4. Monitorar
```powershell
# Ver logs em tempo real
Receive-Job -Name "TradingBackend" -Keep | Select-Object -Last 50

# Ou usar script de monitoring
cd backend
python monitor_testnet.py
```

---

## 📝 NOTAS IMPORTANTES

### Segurança
- ✅ Domínio usa HTTPS automático (Cloudflare)
- ✅ Túnel criptografado
- ✅ Sem exposição de portas no roteador
- ⚠️ API sem autenticação (considere adicionar se público)

### Performance
- Acesso local (192.168.2.105) é mais rápido
- Acesso remoto (botrading.uk) passa pelo Cloudflare
- WebSocket funciona em ambos

### Manutenção
- Cloudflare Service inicia automaticamente com Windows
- Backend/Frontend precisam ser iniciados manualmente (ou via script de startup)
- MongoDB deve estar sempre rodando

---

## 🆘 SUPORTE RÁPIDO

### Sistema não inicia
```powershell
.\scripts\start_system_simple.ps1
```

### Ver o que está rodando
```powershell
Get-Job | Format-Table Id, Name, State
netstat -ano | findstr ":8000 :3000"
Get-Service cloudflared
```

### Reiniciar tudo do zero
```powershell
# Parar tudo
Get-Job | Stop-Job; Get-Job | Remove-Job
Stop-Process -Name python, node -Force -ErrorAction SilentlyContinue

# Reiniciar
.\scripts\start_system_simple.ps1
```

---

**Configurado por:** Igor  
**Última atualização:** 24/12/2025 15:25  
**Versão Cloudflare Tunnel:** 2025.11.1
