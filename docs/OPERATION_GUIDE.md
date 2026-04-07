# 🎮 Guia de Operação - Trading Bot Enterprise

**Versão:** 2.0 (Pós-6-Fases)
**Hardware:** Dell E7450 (i5-5300U, 12GB RAM)
**Target User:** Operador com conhecimento básico de Python/React

---

## 📋 Índice

1. [Setup Inicial](#1-setup-inicial)
2. [Iniciar Sistema](#2-iniciar-sistema)
3. [Monitorar Reflections](#3-monitorar-reflections)
4. [Interpretar Alertas](#4-interpretar-alertas)
5. [Troubleshooting](#5-troubleshooting)
6. [Maintenance](#6-maintenance)

---

## 1. Setup Inicial

### 1.1 Pré-requisitos

**Hardware Mínimo:**

- CPU: 2 cores (i5 ou superior)
- RAM: 8GB (12GB recomendado)
- Storage: 10GB SSD

**Software:**

```bash
# Python 3.11+
python --version
# Output: Python 3.11.x

# Node.js 18+
node --version
# Output: v18.x.x ou v20.x.x

# MongoDB 5.0+ (local ou Atlas)
mongod --version
# Output: db version v5.x.x
```

---

### 1.2 Instalação

#### Backend (Python)

```bash
cd backend

# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows)
.venv\Scripts\activate

# Ativar (Linux/Mac)
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### Frontend (React)

```bash
cd frontend

# Instalar dependências
npm install

# OU com yarn
yarn install
```

---

### 1.3 Configuração (.env)

Criar arquivo `.env` na raiz:

```env
# Binance API (Testnet ou Mainnet)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true  # false para mainnet

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=trading_bot

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Reflection Service
REFLECTION_INTERVAL=60  # minutos
REFLECTION_ACTIVE_HOURS_START=0  # 0-23 (UTC)
REFLECTION_ACTIVE_HOURS_END=24   # 0-24 (UTC)

# ML System
ML_MIN_TRADES_BEFORE_ADJUST=20
ML_EMA_ALPHA=0.3

# Memory Optimizer
MEMORY_OPTIMIZER_ENABLED=true
MEMORY_AUTO_GC_THRESHOLD=0.90  # 90% RAM
```

**⚠️ IMPORTANTE:**

- Nunca commitar `.env` no Git
- Usar **Testnet** primeiro (fundos virtuais)
- Validar API keys em https://testnet.binance.vision/

---

## 2. Iniciar Sistema

### 2.1 Método Rápido (All-in-one)

```bash
# Na raiz do projeto
python start_system.py
```

**Este script:**

1. Inicia MongoDB (se local)
2. Inicia Backend (FastAPI)
3. Inicia Frontend (Vite dev server)
4. Abre browser automaticamente

---

### 2.2 Método Manual (Controle Granular)

#### Terminal 1: Backend

```bash
cd backend
python server.py
```

**Output esperado:**

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
[REFLECTION] Heartbeat iniciado (intervalo: 1:00:00)
[MEMORY] Sistema em 11.31GB (94.2%)
[TRADING] Bot iniciado em modo: TESTNET
```

#### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

**Output esperado:**

```
VITE v4.5.0  ready in 1234 ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

---

### 2.3 Com Hardware Profiling (Recomendado)

```bash
# Terminal 1: Profiler (background)
python profile_hardware.py --duration 3600 --interval 5 > logs/profile.log 2>&1 &

# Terminal 2: Backend + Frontend
python start_system.py
```

**Benefício:** Monitoramento contínuo de CPU/RAM com alertas.

---

## 3. Monitorar Reflections

### 3.1 Acessar Dashboard

1. Abrir http://localhost:3000
2. Clicar no ícone 🧠 (Brain) na navegação
3. OU acessar direto: http://localhost:3000/reflections

---

### 3.2 Entender a UI

**GlassCard 1: Status Overview**

```
┌─────────────────────────────────────┐
│ Total Reflections: 42               │
│ Win Rate: 56.0%                     │
│ Last Reflection: 15 min ago         │
│ Status: ✅ Active                   │
└─────────────────────────────────────┘
```

**Interpretação:**

- **Total Reflections:** Quantas auto-análises já foram feitas
- **Win Rate:** % de trades vencedores (target: >45%)
- **Last Reflection:** Tempo desde última reflexão
- **Status:**
  - ✅ Active: Funcionando normalmente
  - ⚠️ Paused: Bot pausado (win rate crítico)
  - 🚨 Error: Erro detectado

---

**GlassCard 2: Win Rate Chart**

```
Win Rate Trend (últimas 20 reflexões)
┌─────────────────────────────────────┐
│     ╱‾‾╲                            │
│    ╱    ‾╲_                         │
│ __╱        ‾╲_                      │
│               ‾╲___╱                │
└─────────────────────────────────────┘
  0%   25%   50%   75%  100%
```

**Interpretação:**

- **Linha ascendente:** Bot melhorando (bom!)
- **Linha descendente:** Performance caindo (revisar estratégia)
- **Linha estável >50%:** Ótimo, mantém assim
- **Linha estável <40%:** Considerar ajustes

---

**GlassCard 3: Learning History**

```
┌─────────────────────────────────────┐
│ Reflexão #42 (15 min ago)           │
│                                     │
│ Problema Detectado:                 │
│ • Win rate de 42% abaixo do target  │
│ • Loss streak de 6 trades           │
│                                     │
│ Ação Tomada:                        │
│ • Aumentar stop loss em 5%          │
│ • Reduzir confidence score mínimo   │
└─────────────────────────────────────┘
```

**Interpretação:**

- **Problemas:** Issues detectados na análise
- **Ações:** Correções automáticas aplicadas
- **Ausência de ações:** Tudo OK, sem mudanças necessárias

---

### 3.3 Polling & Updates

- **Status:** Atualiza a cada **30 segundos**
- **History:** Atualiza a cada **60 segundos**
- **Manual Refresh:** F5 ou recarregar página

**Indicador de Loading:**

```
┌─────────────────────────────────────┐
│ ⏳ Loading reflections...           │
└─────────────────────────────────────┘
```

---

## 4. Interpretar Alertas

### 4.1 Alertas Críticos (🚨)

#### Win Rate < 30%

```
[REFLECTION] 🚨 CRÍTICO: Win rate de 28% - abaixo do mínimo (30%)
[REFLECTION] AÇÃO: BOT PAUSADO - Requer análise humana
```

**O que fazer:**

1. Verificar logs detalhados: `logs/trading_YYYYMMDD.log`
2. Analisar últimos 50 trades no MongoDB
3. Revisar parâmetros de estratégia
4. Considerar trocar de moeda (volatilidade alta?)
5. **Só reativar após entender a causa**

---

#### RAM Crítico

```
[MEMORY] 🚨 CRÍTICO: Sistema em 11.42GB (95.2%)
[MEMORY] 💡 Fechar Chrome ou outros apps para liberar RAM
```

**O que fazer:**

1. Fechar Chrome/VS Code (principais culpados)
2. Executar GC manual:
   ```python
   from bot.memory_optimizer import get_optimizer
   optimizer = get_optimizer()
   optimizer.force_gc(reason="manual_intervention")
   ```
3. Reiniciar sistema se necessário
4. Considerar usar MongoDB Atlas (offload DB)

---

#### Drawdown Excessivo

```
[RISK] 🚨 CRÍTICO: Drawdown de 16% - limite máximo (15%)
[RISK] AÇÃO: HALT - Trading interrompido
```

**O que fazer:**

1. **NÃO reativar imediatamente**
2. Analisar série de trades que causaram drawdown
3. Revisar estratégia completa (pode estar broken)
4. Considerar período de pausa (1-3 dias)
5. Validar em testnet antes de voltar

---

### 4.2 Alertas de Atenção (⚠️)

#### Win Rate < 40%

```
[REFLECTION] ⚠️ Win rate de 38% - abaixo do target (45%)
[REFLECTION] Revisar sinais de entrada - possível excesso de trades
```

**O que fazer:**

- Aumentar `min_confidence_score` (+0.05)
- Reduzir frequência de trading (menos trades, mais seletivos)
- Monitorar por mais 24h

---

#### Loss Streak > 5

```
[REFLECTION] ⚠️ Loss streak de 6 trades detectado
[REFLECTION] Considerar pause temporário para revisão
```

**O que fazer:**

- Verificar se há evento específico (news, volatilidade)
- Pausar bot por 1-2 horas (deixar mercado acalmar)
- Revisar logs de cada trade do streak

---

### 4.3 Alertas Informativos (ℹ️)

#### Reflexão Completa

```
[REFLECTION] ✅ Reflexão #42 completa
[REFLECTION] Win rate: 56.0% | Avg profit: $1.25
```

**Interpretação:** Tudo OK, sistema funcionando normalmente.

---

#### State Saved

```
[REFLECTION] 💾 Estado salvo: 42 reflexões
```

**Interpretação:** Checkpoint criado, pode reiniciar sem perder progresso.

---

## 5. Troubleshooting

### 5.1 Backend não inicia

**Erro:** `ModuleNotFoundError: No module named 'fastapi'`

**Solução:**

```bash
cd backend
pip install -r requirements.txt
```

---

**Erro:** `pymongo.errors.ServerSelectionTimeoutError`

**Solução:**

1. Verificar MongoDB rodando:

   ```bash
   # Windows
   net start MongoDB

   # Linux/Mac
   sudo systemctl start mongod
   ```

2. Testar conexão:

   ```bash
   mongosh
   # Output: connecting to: mongodb://127.0.0.1:27017/
   ```

3. Se usar MongoDB Atlas, verificar:
   - IP whitelist (0.0.0.0/0 para dev)
   - Connection string correto no .env

---

### 5.2 Frontend não carrega

**Erro:** `npm ERR! missing script: dev`

**Solução:**

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

**Erro:** `Failed to fetch /api/reflections/status`

**Solução:**

1. Backend está rodando? (http://localhost:8000)
2. CORS configurado? (backend permite localhost:3000)
3. Testar endpoint direto:
   ```bash
   curl http://localhost:8000/api/reflections/status
   ```

---

### 5.3 Reflections não atualizam

**Sintoma:** Dashboard mostra dados antigos.

**Verificar:**

1. **Polling ativo?** Abrir DevTools → Network → filtrar "reflections"
2. **Backend respondendo?** Check logs: `logs/trading_*.log`
3. **MongoDB conectado?** Executar: `python test_mongo_connection.py`

**Forçar atualização:**

- F5 (hard reload)
- Limpar cache do browser
- Reiniciar backend

---

### 5.4 RAM usage alto do bot

**Sintoma:** Process RAM >500MB (target: <500MB)

**Diagnóstico:**

```python
from bot.memory_optimizer import get_optimizer

optimizer = get_optimizer()
status = optimizer.get_memory_status()
print(f"Process RAM: {status['process_ram_mb']:.1f}MB")
```

**Solução:**

```python
# Forçar GC
optimizer.force_gc(reason="high_usage")

# Ou reiniciar backend
```

---

### 5.5 Tests falhando

**E2E Tests:**

```bash
cd frontend
npx playwright test --debug
```

**Unit Tests:**

```bash
cd backend
pytest tests/unit/test_ml_guardrails.py -v
```

**Se ainda falhar:**

- Verificar versões (Python 3.11+, Node 18+)
- Reinstalar dependências
- Checar .env (pode ter vars obrigatórias faltando)

---

## 6. Maintenance

### 6.1 Backup MongoDB

**Daily Backup:**

```bash
# Criar backup
mongodump --db trading_bot --out backup/$(date +%Y%m%d)

# Restaurar backup
mongorestore --db trading_bot backup/20260131/trading_bot/
```

**Automatizar (cron/task scheduler):**

```bash
# Linux/Mac crontab
0 3 * * * /path/to/backup_script.sh

# Windows Task Scheduler
# Criar task com: mongodump --db trading_bot --out C:\backups\%date%
```

---

### 6.2 Logs Rotation

**Limpar logs antigos (>30 dias):**

```bash
# Linux/Mac
find logs/ -name "*.log" -mtime +30 -delete

# Windows PowerShell
Get-ChildItem logs\*.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```

---

### 6.3 MongoDB Maintenance

**Verificar índices:**

```bash
python optimize_mongodb_indexes.py
```

**Output esperado:**

```
[TRADES] Indices existentes: 8
[TRADES] - timestamp index: YES
[TRADES] - symbol index: YES
[TRADES] - profit index: YES

[TEST] OK: 50 trades em 2.00ms
```

---

### 6.4 Performance Monitoring

**Executar profiling semanal:**

```bash
python profile_hardware.py --duration 3600 --interval 10
```

**Analisar report:**

```bash
cat logs/profile_YYYYMMDD_HHMMSS_summary.md
```

**KPIs a monitorar:**

- CPU avg <70% ✅
- RAM system <90% ⚠️
- Bot RAM <500MB ✅
- MongoDB queries <50ms ✅

---

### 6.5 Update Dependencies

**Backend (mensal):**

```bash
cd backend
pip list --outdated
pip install --upgrade <package>
pip freeze > requirements.txt
```

**Frontend (mensal):**

```bash
cd frontend
npm outdated
npm update
# OU npm install <package>@latest
```

**⚠️ Testar após updates:**

```bash
# Backend
pytest tests/

# Frontend
npm test
npx playwright test
```

---

## 🎓 Best Practices

1. **Sempre usar Testnet primeiro** (min 7 dias validação)
2. **Monitorar Reflections diariamente** (15min/dia)
3. **Backup MongoDB semanalmente**
4. **Profiling mensal** (detectar degradação)
5. **Nunca desativar ML Guardrails** (safety crítico)
6. **Respeitar circuit breakers** (não forçar reativação)
7. **Documentar mudanças manuais** (em memory/episodic/)

---

## 📚 Recursos Adicionais

- **Arquitetura Completa:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **ML Guardrails:** [memory/procedural/ml_guardrails_safety_limits.md](memory/procedural/ml_guardrails_safety_limits.md)
- **State Persistence:** [memory/procedural/state_persistence_pattern.md](memory/procedural/state_persistence_pattern.md)
- **Bounded Autonomy:** [AUTONOMOUS_EXECUTION.md](AUTONOMOUS_EXECUTION.md)
- **Phase 5 Optimizations:** [memory/episodic/2026-01-31_0840_phase5_e7450_optimizations_complete.md](memory/episodic/2026-01-31_0840_phase5_e7450_optimizations_complete.md)

---

## ❓ Suporte

**Issues comuns:** Ver seção Troubleshooting acima
**Documentação:** [docs/](docs/)
**Logs:** [logs/](logs/)

**Para reportar bugs:**

1. Descrever sintoma
2. Anexar logs relevantes
3. Incluir output de `python --version`, `node --version`
4. Screenshots se aplicável

---

**Guia de Operação v2.0**
_"Operation excellence through documentation"_
_Dell E7450 Optimized_
