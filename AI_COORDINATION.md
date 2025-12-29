# 🤝 COORDENAÇÃO ENTRE AGENTES IA

**Última Atualização**: 24/12/2025 - Sistema criado

---

## 📋 QUADRO DE TAREFAS (Kanban)

### 🚀 EM ANDAMENTO

#### Sessão A (Atual)
- [ ] **Tarefa**: _Aguardando atribuição_
- **Arquivo(s)**: -
- **Status**: Idle
- **Última ação**: 24/12/2025 - Sistema de coordenação criado

#### Sessão B (Outra Aba)
- [ ] **Tarefa**: _Aguardando atribuição_
- **Arquivo(s)**: -
- **Status**: Idle
- **Última ação**: -

---

### ✅ CONCLUÍDAS HOJE

- ✅ Aplicadas 9 correções cirúrgicas no bot (PF 0.271 → target 1.5+)
- ✅ Validação completa (17/17 checks passed)
- ✅ Testnet ativado ($826.77 USDT)
- ✅ Sistema iniciado (Backend 8000, Frontend 3000)
- ✅ Cloudflared verificado (botrading.uk configurado)
- ✅ Instruções transformadas para padrão elite profissional

---

### 📌 BACKLOG PRIORITÁRIO

#### 🔴 Alta Prioridade
1. **Validação Testnet** (5-7 dias)
   - Monitorar PF, Win Rate, Trades/dia
   - Target: PF > 1.5, WR > 50%, ≤5 trades/dia
   - Responsável: _Não atribuído_

2. **Otimização Dell E7450**
   - Profiling de CPU/RAM/Disk
   - Aplicar asyncio, generators, cache limits
   - Responsável: _Não atribuído_

3. **Verificação Domain Access**
   - Testar botrading.uk após DNS propagation
   - Validar api.botrading.uk endpoints
   - Responsável: _Não atribuído_

#### 🟡 Média Prioridade
4. **Implementar Estratégias Profissionais**
   - Momentum Breakout (código pronto nas instruções)
   - Mean Reversion (código pronto nas instruções)
   - Responsável: _Não atribuído_

5. **Position Sizing Dinâmico**
   - Kelly Criterion implementation
   - Fixed Fractional com ATR
   - Responsável: _Não atribuído_

6. **Dashboard Moderno (2025)**
   - Glassmorphism design
   - Real-time charts optimization
   - Responsável: _Não atribuído_

#### 🟢 Baixa Prioridade
7. **Testes Automatizados**
   - Cobertura > 80% em módulos críticos
   - CI/CD pipeline
   - Responsável: _Não atribuído_

8. **Documentação API**
   - OpenAPI specs completos
   - Postman collection
   - Responsável: _Não atribuído_

---

## 💬 CANAL DE COMUNICAÇÃO

### Protocolo de Mensagens
Cada sessão deve adicionar mensagens aqui ao fazer mudanças importantes:

```markdown
[TIMESTAMP] [SESSÃO] [TIPO] Mensagem

Tipos: INFO, ALERTA, CONCLUÍDO, PERGUNTA, BLOQUEIO
```

### Histórico de Mensagens

```
[24/12/2025 - Sessão A] [INFO] Sistema de coordenação criado
```

---

## 🔄 PROTOCOLO DE SINCRONIZAÇÃO

### Antes de Editar Arquivo
1. ✅ Verificar se arquivo está em "EM ANDAMENTO" pela outra sessão
2. ✅ Marcar arquivo como "EM USO - Sessão X"
3. ✅ Fazer alterações
4. ✅ Atualizar status para "CONCLUÍDO"
5. ✅ Adicionar mensagem no canal

### Em Caso de Conflito
- 🚨 Adicionar mensagem: `[SESSÃO] [BLOQUEIO] Arquivo X em conflito, aguardando`
- 🤝 Coordenar via usuário Igor
- 🔄 Alternar para outra tarefa do backlog

---

## 📁 ARQUIVOS CRÍTICOS (Evitar Conflitos)

### Backend Core
- ❗ `backend/bot/trading_bot.py` - Orquestrador principal
- ❗ `backend/bot/strategy.py` - Lógica de sinais (1015 linhas)
- ❗ `backend/bot/risk_manager.py` - Gestão de risco (312 linhas)
- ⚠️ `backend/bot/selector.py` - Seleção de moedas
- ⚠️ `backend/bot/learning_system.py` - ML adaptativo
- ⚠️ `backend/server.py` - API FastAPI

### Frontend Core
- ⚠️ `frontend/src/pages/*` - Páginas principais
- ⚠️ `frontend/src/components/*` - Componentes reutilizáveis
- ⚠️ `frontend/src/services/api.ts` - Cliente HTTP

### Configuração
- ❗ `backend/.env` - Variáveis de ambiente
- ❗ `backend/bot/config.py` - Configurações centralizadas
- ⚠️ `.github/copilot-instructions.md` - Instruções profissionais

**Legenda**:
- ❗ = Extremamente crítico, coordenar SEMPRE
- ⚠️ = Crítico, verificar antes de editar

---

## 🎯 DIVISÃO DE TRABALHO SUGERIDA

### Sessão A - Backend & Trading Logic
- Otimizações de performance (Dell E7450)
- Implementação de estratégias (Momentum, Mean Reversion)
- Position sizing (Kelly, Fixed Fractional)
- Risk management enhancements
- Backtesting e validação

### Sessão B - Frontend & UX/UI
- Dashboard modernização (Glassmorphism)
- Real-time charts optimization
- Responsividade mobile
- Acessibilidade (WCAG)
- Performance UI (lazy loading, code splitting)

### Ambas - Integração
- Contratos API (sincronizar mudanças)
- Testes end-to-end
- Documentação
- Monitoring e alertas

---

## 📊 MÉTRICAS DE COLABORAÇÃO

### Eficiência
- ⏱️ Tempo médio de resposta: _A medir_
- 🔄 Conflitos de arquivo: 0
- ✅ Tarefas concluídas hoje: 6

### Qualidade
- 🧪 Testes passando: 17/17 (validation checks)
- 📈 Cobertura de código: _A medir_
- 🐛 Bugs encontrados: 0
- 🚀 Features implementadas: 6

---

## 🛠️ COMANDOS ÚTEIS

### Verificar Status do Sistema
```powershell
# Backend
Get-Job | Where-Object {$_.Name -eq "TradingBackend"} | Receive-Job

# Frontend  
Get-Job | Where-Object {$_.Name -eq "TradingFrontend"} | Receive-Job

# Portas
netstat -ano | Select-String ":8000|:3000"
```

### Atualizar Este Arquivo
```powershell
# Ver última versão
Get-Content AI_COORDINATION.md -Tail 50

# Verificar mudanças
git diff AI_COORDINATION.md
```

---

## 🎓 REFERÊNCIAS RÁPIDAS

### Instruções Profissionais
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - 4 personas, 7-step framework, Dell E7450 optimizations

### Documentação do Bot
- [STATUS_ATUAL.md](STATUS_ATUAL.md) - Estado atual do sistema
- [TESTNET_VALIDATION.md](TESTNET_VALIDATION.md) - Período de validação
- [ACESSO_BOTRADING_UK.md](ACESSO_BOTRADING_UK.md) - Acesso remoto

### Correções Aplicadas
- Threshold: 7.0 → 9.0
- Min strength: 75 → 80
- ADX threshold: 25 → 30
- ATR multipliers: reduzidos ~50%
- R/R ratio: 3.0 → 2.5
- Ranging market: bloqueio adicionado

---

**Como Usar Este Arquivo**:
1. Antes de começar trabalho, verificar "EM ANDAMENTO"
2. Atribuir tarefa do backlog para sua sessão
3. Atualizar status conforme progride
4. Adicionar mensagem ao concluir
5. Verificar se outra sessão precisa da sua ajuda
