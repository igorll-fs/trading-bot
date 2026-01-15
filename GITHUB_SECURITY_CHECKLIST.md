# 🔒 CHECKLIST DE SEGURANÇA - GitHub Upload

**Data**: 14/01/2026
**Status**: ⏳ Em Progresso

---

## ✅ FASE 1: Arquivos Sensíveis

### Arquivos .env (NÃO ENVIAR)
- [ ] `backend/.env` - **BLOQUEADO no .gitignore**
- [ ] `frontend/.env` - **BLOQUEADO no .gitignore**  
- [ ] `frontend/.env.development.local` - **BLOQUEADO no .gitignore**

**Verificado**: Todos os .env estão no .gitignore ✅

### Templates .env.example (ENVIAR)
- [ ] `backend/.env.example` - **OK para enviar** (sem credenciais)
- [ ] `frontend/.env.example` - **OK para enviar** (sem credenciais)

---

## ✅ FASE 2: Dados Sensíveis em Código

### Buscar e Remover:
- [ ] API Keys hardcoded
- [ ] Tokens hardcoded
- [ ] Senhas hardcoded
- [ ] IPs privados (192.168.x.x)
- [ ] URLs do MongoDB com credenciais

**Ação**: Executar `prepare_for_github.ps1 -DryRun` para verificar

---

## ✅ FASE 3: Logs e Histórico de Trading

### Logs a Deletar:
- [ ] `backend/*.log`
- [ ] `backend/*.err`
- [ ] `backend/uvicorn*.log`
- [ ] `backend/uvicorn*.err`
- [ ] `frontend/*.log`

### Histórico de Trades:
- [ ] Verificar se `trades.json` existe (NÃO ENVIAR)
- [ ] Verificar se `positions.json` existe (NÃO ENVIAR)
- [ ] Verificar dumps do MongoDB (NÃO ENVIAR)

**Status**: Script irá deletar automaticamente ✅

---

## ✅ FASE 4: Arquivos Temporários

### Deletar:
- [ ] `query` (raiz, backend/)
- [ ] `nul` (se existir)
- [ ] `-w` (frontend/-w)
- [ ] `temp_*` (todos arquivos temporários)
- [ ] `*.tmp`
- [ ] `__pycache__/` (todos)
- [ ] `.pytest_cache/`

**Status**: Script irá deletar automaticamente ✅

---

## ✅ FASE 5: Diretórios Grandes (Reconstruíveis)

### Node.js:
- [ ] `frontend/node_modules/` - **BLOQUEADO** (yarn install reconstrói)
- [ ] `frontend/build/` - **BLOQUEADO** (yarn build reconstrói)
- [ ] `frontend/dist/` - **BLOQUEADO**

### Python:
- [ ] `.venv/` - **BLOQUEADO** (poetry/pip install reconstrói)
- [ ] `venv/` - **BLOQUEADO**
- [ ] `__pycache__/` - **BLOQUEADO**

### Relatórios:
- [ ] `frontend/playwright-report/` - **BLOQUEADO**
- [ ] `frontend/lhci-report/` - **BLOQUEADO**
- [ ] `frontend/test-results/` - **BLOQUEADO**

**Status**: Todos no .gitignore ✅

---

## ✅ FASE 6: Correção do Problema Roff (81.4%)

### Arquivos a Criar/Atualizar:
- [ ] `.gitignore` - **Atualizado** com todos os patterns
- [ ] `.gitattributes` - **Criado** para forçar detecção correta
  - `*.py linguist-language=Python`
  - `*.js linguist-language=JavaScript`
  - `node_modules/ linguist-vendored`

### Arquivos a Deletar (causam Roff):
- [ ] `query` (sem extensão)
- [ ] `nul` (sem extensão)
- [ ] `frontend/-w` (arquivo inválido)

**Status**: Script criará .gitattributes automaticamente ✅

---

## ✅ FASE 7: Verificação de Dados Pessoais

### Documentação:
- [ ] README.md - **Revisar** (remover IPs, nomes, emails?)
- [ ] AI_CHAT.md - **OK** (sem dados sensíveis)
- [ ] *.md em docs/ - **OK**

### Comentários em Código:
- [ ] Buscar "igor" em comentários (opcional, não crítico)
- [ ] Buscar "192.168" em comentários
- [ ] Buscar emails em comentários

**Ação**: Revisão manual recomendada

---

## ✅ FASE 8: Teste de Build

### Backend:
```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/
```
- [ ] Backend instala sem erros
- [ ] Testes passam

### Frontend:
```bash
cd frontend
yarn install
yarn build
```
- [ ] Frontend instala sem erros
- [ ] Build compila sem erros

**Status**: ⏳ Executar após limpeza

---

## ✅ FASE 9: Git Status Limpo

### Verificação Final:
```bash
git status
```

**Deve mostrar**:
- ✅ Apenas arquivos tracked (código-fonte)
- ✅ .gitignore atualizado
- ✅ .gitattributes criado
- ❌ Nenhum .env
- ❌ Nenhum .log
- ❌ Nenhum arquivo sensível

---

## ✅ FASE 10: Push para GitHub

### Comandos:
```bash
# 1. Adicionar mudanças
git add .gitignore .gitattributes
git commit -m "chore: Preparar projeto para GitHub (remover dados sensíveis)"

# 2. Remover arquivos sensíveis do cache (se existirem)
git rm --cached backend/.env frontend/.env -f 2>/dev/null || true
git rm --cached backend/*.log frontend/*.log -f 2>/dev/null || true
git commit -m "chore: Remover arquivos sensíveis do histórico Git" || true

# 3. Push
git push origin main

# 4. Force Linguist recalculation (se Roff não sumir em 48h)
# git commit --allow-empty -m "chore: Force GitHub Linguist recalculation"
# git push origin main
```

---

## 📊 RESULTADO ESPERADO NO GITHUB

### Estatísticas de Linguagem:
- **Python**: ~80% (principal)
- **JavaScript**: ~20% (secundário)
- **Roff**: ~~81.4%~~ → **0%** (corrigido)

### Arquivos:
- Total: ~300 arquivos (era 3,600+)
- Sem logs, sem .env, sem node_modules

### Segurança:
- ✅ Nenhuma credencial exposta
- ✅ Nenhum histórico de trades
- ✅ Nenhum IP privado
- ✅ Projeto limpo e profissional

---

## 🚀 COMANDOS RÁPIDOS

### Executar limpeza (simulação):
```powershell
.\scripts\prepare_for_github.ps1 -DryRun
```

### Executar limpeza (real):
```powershell
.\scripts\prepare_for_github.ps1
```

### Executar limpeza (sem confirmação):
```powershell
.\scripts\prepare_for_github.ps1 -Force
```

---

## ⚠️ AVISOS IMPORTANTES

1. **Backup**: Faça backup do projeto antes de executar
2. **.env**: Recrie manualmente no servidor de produção
3. **MongoDB**: Dados locais NÃO são enviados (apenas código)
4. **node_modules**: Será reconstruído com `yarn install`
5. **Credenciais**: NUNCA commite diretamente no código

---

**Última atualização**: 14/01/2026 por SessionA
