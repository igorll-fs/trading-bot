# ✅ TESTES PRÉ-PUSH - CHECKLIST OBRIGATÓRIO

**Data:** 15/01/2026  
**Status:** 🟡 EM ANDAMENTO

---

## 🎯 OBJETIVO

Garantir que o projeto funciona corretamente após a limpeza e está 100% seguro para GitHub.

---

## 📋 CHECKLIST DE TESTES

### 1️⃣ SEGURANÇA (CRÍTICO) ⏱️ 5 min

```powershell
# ✅ a) Verificar se .env está protegido
git check-ignore backend/.env frontend/.env

# ✅ b) Simular o que será commitado (SEM fazer commit ainda)
git add --dry-run .
git status

# ✅ c) Buscar por dados sensíveis
git diff --cached | Select-String -Pattern "BINANCE_API_KEY|password|secret|token" -CaseSensitive:$false

# ✅ d) Verificar se caminhos hardcoded foram removidos
Select-String -Path "scripts\*.ps1","scripts\*.bat" -Pattern "C:\\Users\\igor" -SimpleMatch

# ✅ e) Ver tamanho dos arquivos que serão enviados
git ls-files -s | Sort-Object -Property @{Expression={[int]($_ -split '\s+')[3]}} -Descending | Select-Object -First 10
```

**Resultado esperado:**
- ✅ `.env` retorna caminho (está protegido)
- ✅ Nenhum dado sensível encontrado
- ✅ Nenhum caminho hardcoded encontrado
- ✅ Nenhum arquivo > 10MB

---

### 2️⃣ BACKEND (FUNCIONALIDADE) ⏱️ 3 min

```powershell
# ✅ a) Verificar se .env existe
Test-Path backend\.env

# ✅ b) Testar importações Python
cd backend
python -c "import server; print('✅ Imports OK')"

# ✅ c) Verificar se servidor inicia (não deixar rodando)
# Start-Process powershell -ArgumentList "-Command", "cd backend; python -m uvicorn server:app --port 8001" -WindowStyle Hidden
# Start-Sleep 5
# $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -Method GET
# Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
```

**Resultado esperado:**
- ✅ `.env` existe
- ✅ Importações funcionam
- ✅ Servidor inicia sem erro

---

### 3️⃣ FRONTEND (FUNCIONALIDADE) ⏱️ 2 min

```powershell
# ✅ a) Verificar se .env existe
Test-Path frontend\.env.development.local

# ✅ b) Verificar se dependências estão instaladas
cd frontend
Test-Path node_modules

# ✅ c) Testar build (opcional, demora)
# yarn build
```

**Resultado esperado:**
- ✅ Configurações existem
- ✅ node_modules instalado
- ✅ Build funciona (opcional)

---

### 4️⃣ SCRIPTS (PORTABILIDADE) ⏱️ 3 min

```powershell
# ✅ a) Testar script de start (modo dry-run)
.\scripts\start.bat /?

# ✅ b) Verificar se scripts têm caminhos dinâmicos
Select-String -Path "scripts\start_system.ps1" -Pattern '$PSScriptRoot'

# ✅ c) Testar script de limpeza novamente
.\scripts\clean_scripts.ps1 -DryRun
```

**Resultado esperado:**
- ✅ Scripts executam sem erro
- ✅ Caminhos dinâmicos presentes
- ✅ Nenhuma mudança necessária (já limpos)

---

### 5️⃣ DOCUMENTAÇÃO (QUALIDADE) ⏱️ 2 min

```powershell
# ✅ a) Verificar se arquivos importantes existem
@("README.md", "SECURITY_GUIDE.md", "GITHUB_CHECKLIST.md", ".gitignore", ".gitattributes") | ForEach-Object {
    if(Test-Path $_) { Write-Host "✅ $_" -ForegroundColor Green } 
    else { Write-Host "❌ $_" -ForegroundColor Red }
}

# ✅ b) Verificar se .env.example existem
Test-Path backend\.env.example
Test-Path frontend\.env.example

# ✅ c) Verificar se .env.example não têm dados reais
Select-String -Path "backend\.env.example" -Pattern "BINANCE_API_KEY=your_"
```

**Resultado esperado:**
- ✅ Todos os arquivos existem
- ✅ .env.example são templates (não dados reais)

---

### 6️⃣ GIT (INTEGRIDADE) ⏱️ 2 min

```powershell
# ✅ a) Verificar se está em branch main
git branch --show-current

# ✅ b) Ver status limpo
git status

# ✅ c) Verificar histórico (se já tem commits)
git log --oneline -5

# ✅ d) Simular push (ver o que seria enviado)
git push --dry-run origin main 2>&1
```

**Resultado esperado:**
- ✅ Branch: main
- ✅ Status mostra arquivos corretos
- ✅ Histórico limpo (sem secrets)

---

## 🚨 RED FLAGS (PARAR SE ENCONTRAR)

```yaml
⛔ CRÍTICOS (NÃO fazer push):
  - .env ou .env.local aparece no git status
  - Encontrou "BINANCE_API_KEY=abc123" (dado real)
  - Encontrou "C:\Users\igor\" em scripts
  - Arquivo > 50MB sendo commitado
  - node_modules/ ou .venv/ sendo commitados

⚠️ AVISOS (Revisar antes de continuar):
  - Mais de 100 arquivos modificados
  - Backend não inicia
  - Importações Python com erro
  - Scripts com erro de sintaxe
```

---

## ✅ TESTES AUTOMATIZADOS (OPCIONAL)

### Script de Teste Rápido

```powershell
# Criar arquivo: scripts/test_pre_push.ps1

Write-Host "Executando testes pre-push..." -ForegroundColor Cyan

$errors = @()

# Teste 1: .env protegido
if (-not (git check-ignore backend\.env)) {
    $errors += "❌ backend\.env NAO esta protegido!"
}

# Teste 2: Imports Python
try {
    $result = python -c "import sys; sys.path.append('backend'); import server; print('OK')" 2>&1
    if ($result -notmatch "OK") {
        $errors += "❌ Imports Python falharam"
    }
} catch {
    $errors += "❌ Erro ao testar Python: $_"
}

# Teste 3: Caminhos hardcoded
$hardcoded = Select-String -Path "scripts\*.ps1" -Pattern "C:\\Users\\igor" -SimpleMatch
if ($hardcoded) {
    $errors += "❌ Encontrou caminhos hardcoded em scripts"
}

# Resultado
if ($errors.Count -eq 0) {
    Write-Host "`n✅ TODOS OS TESTES PASSARAM!" -ForegroundColor Green
    Write-Host "✅ PRONTO PARA PUSH!" -ForegroundColor Green
} else {
    Write-Host "`n❌ TESTES FALHARAM:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    Write-Host "`n⚠️  CORRIJA OS ERROS ANTES DE FAZER PUSH!" -ForegroundColor Yellow
}
```

---

## 📊 RESULTADO DOS TESTES

### Status Geral

| Categoria | Status | Notas |
|-----------|--------|-------|
| **Segurança** | ⏳ PENDENTE | Executar testes |
| **Backend** | ⏳ PENDENTE | Verificar se inicia |
| **Frontend** | ⏳ PENDENTE | Verificar build |
| **Scripts** | ⏳ PENDENTE | Testar portabilidade |
| **Documentação** | ⏳ PENDENTE | Verificar completude |
| **Git** | ⏳ PENDENTE | Validar status |

### Problemas Encontrados

_Nenhum ainda - executar testes_

---

## 🚀 DECISÃO: PUSH OU NÃO?

### ✅ PODE FAZER PUSH SE:
- ✅ Todos os testes CRÍTICOS passaram
- ✅ .env está protegido
- ✅ Nenhum dado sensível encontrado
- ✅ Backend e frontend funcionam
- ✅ Scripts portáveis

### ❌ NÃO FAZER PUSH SE:
- ❌ Qualquer teste CRÍTICO falhou
- ❌ Encontrou secrets no código
- ❌ Backend/frontend quebrados
- ❌ Scripts com caminhos hardcoded

---

## 📝 APÓS TESTES

### Se TODOS passaram:
```powershell
# 1. Adicionar arquivos
git add .

# 2. Commit
git commit -m "chore: prepare project for github - clean sensitive data"

# 3. Criar repo no GitHub

# 4. Push
git remote add origin https://github.com/USER/REPO.git
git branch -M main
git push -u origin main
```

### Se ALGUM falhou:
```powershell
# 1. Corrigir problemas identificados
# 2. Executar testes novamente
# 3. Repetir até todos passarem
```

---

**Status:** ⏳ Aguardando execução dos testes  
**Próximo passo:** Executar checklist acima  
**Estimativa:** 15-20 minutos total
