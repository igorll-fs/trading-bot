# 🔒 GUIA COMPLETO DE SEGURANÇA PARA GITHUB
## Como Subir Projetos de Forma Segura e Profissional

**Data:** 15/01/2026  
**Versão:** 2.0 - Enterprise Grade Security

---

## 📑 ÍNDICE

1. [Checklist de Segurança Obrigatória](#1-checklist-de-segurança-obrigatória)
2. [Dados Sensíveis - O Que NUNCA Commitar](#2-dados-sensíveis---o-que-nunca-commitar)
3. [Estrutura de Arquivos .env](#3-estrutura-de-arquivos-env)
4. [Limpeza de Histórico Git](#4-limpeza-de-histórico-git)
5. [Boas Práticas de Commits](#5-boas-práticas-de-commits)
6. [Segurança em Scripts](#6-segurança-em-scripts)
7. [Revisão Antes do Push](#7-revisão-antes-do-push)
8. [Proteção de Branches](#8-proteção-de-branches)
9. [Secrets Management](#9-secrets-management)
10. [Auditoria e Monitoramento](#10-auditoria-e-monitoramento)

---

## 1. CHECKLIST DE SEGURANÇA OBRIGATÓRIA

### ✅ Antes de Criar o Repositório

```powershell
# 1. Verificar se .gitignore existe e está completo
Test-Path .gitignore

# 2. Verificar se arquivos .env estão protegidos
git check-ignore backend/.env frontend/.env

# 3. Buscar por credenciais no código
git grep -i "password\|secret\|token\|api_key" -- ':!*.md' ':!SECURITY_GUIDE.md'

# 4. Verificar histórico git (se já existe)
git log --all --full-history --source -- backend/.env frontend/.env

# 5. Listar arquivos que serão commitados
git status
```

### ✅ Categorias de Dados Sensíveis

| Categoria | Exemplos | Risco |
|-----------|----------|-------|
| **Credenciais API** | Binance API Key/Secret, Google API | ⛔ CRÍTICO |
| **Tokens** | JWT, Bearer tokens, Session tokens | ⛔ CRÍTICO |
| **Senhas** | Senhas de banco, admin passwords | ⛔ CRÍTICO |
| **Chaves Privadas** | SSH keys, SSL certificates, PGP keys | ⛔ CRÍTICO |
| **Dados Pessoais** | Nomes reais, endereços, CPF, telefones | 🔴 ALTO |
| **Histórico de Trades** | Trades reais, saldos, lucros/perdas | 🔴 ALTO |
| **Caminhos do Sistema** | `C:\Users\igor\...`, paths hardcoded | 🟡 MÉDIO |
| **IPs e Portas** | IPs públicos, portas específicas | 🟡 MÉDIO |
| **Logs Detalhados** | Stack traces com dados sensíveis | 🟡 MÉDIO |

---

## 2. DADOS SENSÍVEIS - O QUE NUNCA COMMITAR

### ❌ NUNCA Commitar

```plaintext
# Credenciais
*.env
.env*
!.env.example
*secret*
*credentials*
*token.json
*auth.json

# Chaves e Certificados
*.key
*.pem
*.p12
*.pfx
*.crt (privados)
id_rsa
id_rsa.pub (se contém comentário com email)

# Dados de Trading
trades_backup*.json
positions_*.json
balance_*.json
history_*.csv
*_real_data.json

# Logs com Informações Sensíveis
*.log
*.err
logs/
error.log
access.log

# Dados de Configuração Local
config_local.py
settings_override.py
local_settings.py

# Cache e Temporários
__pycache__/
*.pyc
*.pyo
.pytest_cache/
node_modules/
.venv/
*.tmp
*.bak
```

### ✅ PODE Commitar (com cuidado)

```plaintext
# Templates e Exemplos
.env.example
config.example.py
settings.template.yaml

# Documentação
README.md
docs/*.md
SECURITY.md

# Configurações de Desenvolvimento
.vscode/extensions.json (sem credenciais)
.editorconfig
prettier.config.js

# Testes (sem dados reais)
tests/fixtures/*.json (mock data)
tests/test_*.py
```

---

## 3. ESTRUTURA DE ARQUIVOS .env

### 📝 Template Seguro (.env.example)

**backend/.env.example:**
```env
# ===========================
# BINANCE API
# ===========================
# Obter em: https://www.binance.com/en/my/settings/api-management
BINANCE_API_KEY=your_binance_api_key_here_32_characters
BINANCE_API_SECRET=your_binance_secret_here_64_characters

# Ambiente (true para testnet, false para produção)
USE_TESTNET=true

# ===========================
# MONGODB
# ===========================
MONGO_URL=mongodb://localhost:27017
DB_NAME=trading_bot

# ===========================
# TELEGRAM NOTIFICATIONS
# ===========================
# Bot Token: Obter com @BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
# Chat ID: Obter com @userinfobot
TELEGRAM_CHAT_ID=123456789

# ===========================
# TRADING SETTINGS
# ===========================
CAPITAL_INICIAL=1000.0
MAX_POSITIONS=3
RISK_PER_TRADE=0.02

# ===========================
# SECURITY (OPCIONAL)
# ===========================
# Secret para JWT (gerar com: openssl rand -hex 32)
JWT_SECRET=your_jwt_secret_here_64_characters_minimum

# Rate limiting
MAX_REQUESTS_PER_MINUTE=60
```

**frontend/.env.example:**
```env
# ===========================
# BACKEND API
# ===========================
REACT_APP_BACKEND_URL=http://localhost:8000

# ===========================
# ENVIRONMENT
# ===========================
NODE_ENV=development

# ===========================
# FEATURES (OPCIONAL)
# ===========================
REACT_APP_ENABLE_MOCK_DATA=false
REACT_APP_DEBUG_MODE=false
```

### 🔒 Proteger .env no .gitignore

```gitignore
# ===========================
# NUNCA COMMITAR ARQUIVOS .env
# ===========================
*.env
.env
.env.*
!.env.example
!.env.template

# Verificar sempre com:
# git check-ignore *.env
```

---

## 4. LIMPEZA DE HISTÓRICO GIT

### 🔍 Verificar Se Dados Sensíveis Foram Commitados

```powershell
# Buscar por arquivo específico no histórico
git log --all --full-history --source -- backend/.env

# Buscar por padrão no histórico (API keys, senhas)
git log -S "BINANCE_API_KEY" --all

# Ver conteúdo de arquivo deletado
git show COMMIT_HASH:backend/.env

# Listar todos os arquivos já commitados
git log --pretty=format: --name-only --diff-filter=A | sort -u
```

### 🧹 Remover Arquivo do Histórico (BFG ou git-filter-repo)

#### Método 1: BFG Repo-Cleaner (Recomendado)

```powershell
# Instalar BFG
# Download de: https://rtyley.github.io/bfg-repo-cleaner/

# Fazer backup
git clone --mirror https://github.com/user/repo.git repo-backup.git

# Remover arquivo específico
bfg --delete-files .env repo.git

# Remover senhas/tokens
bfg --replace-text passwords.txt repo.git

# Limpar e fazer push forçado
cd repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

#### Método 2: git-filter-repo (Mais Poderoso)

```powershell
# Instalar (Python 3.5+)
pip install git-filter-repo

# Remover arquivo específico
git filter-repo --invert-paths --path backend/.env

# Remover por padrão (regex)
git filter-repo --path-glob '*.env' --invert-paths

# Substituir strings sensíveis
echo "BINANCE_API_KEY==>REDACTED" > replacements.txt
git filter-repo --replace-text replacements.txt
```

### ⚠️ IMPORTANTE: Após Limpar Histórico

```powershell
# 1. Avisar colaboradores (se houver)
# 2. Todos devem fazer fresh clone
git clone https://github.com/user/repo.git

# 3. Revogar credenciais expostas
# - Regenerar API Keys no Binance
# - Mudar senhas do MongoDB
# - Criar novos tokens Telegram

# 4. Verificar se limpeza funcionou
git log --all --full-history --source -- backend/.env
```

---

## 5. BOAS PRÁTICAS DE COMMITS

### 📝 Formato de Mensagens (Conventional Commits)

```plaintext
<tipo>(<escopo>): <descrição curta>

<corpo opcional>

<rodapé opcional>
```

**Tipos:**
- `feat`: Nova feature
- `fix`: Correção de bug
- `docs`: Apenas documentação
- `style`: Formatação, sem mudança de lógica
- `refactor`: Refatoração de código
- `test`: Adicionar/corrigir testes
- `chore`: Tarefas de manutenção
- `perf`: Melhorias de performance
- `ci`: Mudanças em CI/CD
- `security`: Correções de segurança

**Exemplos:**
```bash
git commit -m "feat(bot): add momentum breakout strategy"
git commit -m "fix(api): resolve MongoDB connection timeout"
git commit -m "docs: update installation guide"
git commit -m "security: remove hardcoded API keys"
git commit -m "chore: prepare project for github"
```

### 🚫 Evitar

```bash
# ❌ Mensagens vagas
git commit -m "fix"
git commit -m "update"
git commit -m "changes"

# ❌ Commits muito grandes
git add .  # (100+ arquivos modificados)

# ❌ Commitar .env acidentalmente
git add .  # sem verificar antes
```

### ✅ Fazer

```bash
# ✅ Commits pequenos e focados
git add backend/bot/strategy.py
git commit -m "feat(strategy): implement RSI indicator"

# ✅ Verificar antes de commitar
git status
git diff --cached
git commit

# ✅ Usar staging seletivo
git add -p  # escolher hunks individualmente
```

---

## 6. SEGURANÇA EM SCRIPTS

### ❌ Problemas Comuns em Scripts

```powershell
# ❌ ERRADO: Caminhos hardcoded
$ProjectRoot = "C:\Users\igor\Desktop\projeto"

# ✅ CORRETO: Caminhos dinâmicos
$ProjectRoot = $PSScriptRoot\..
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# ❌ ERRADO: Credenciais no script
$ApiKey = "abc123xyz456"
Invoke-RestMethod -Uri "https://api.com" -Headers @{"API-Key"=$ApiKey}

# ✅ CORRETO: Ler de .env ou variáveis de ambiente
$ApiKey = $env:API_KEY
if (-not $ApiKey) {
    Write-Error "API_KEY not set"
    exit 1
}

# ❌ ERRADO: Senhas em texto plano
$Password = "minha_senha_123"

# ✅ CORRETO: SecureString ou prompt
$Password = Read-Host "Enter password" -AsSecureString
```

### ✅ Scripts Seguros - Checklist

```yaml
- [ ] Sem credenciais hardcoded
- [ ] Sem caminhos absolutos com nomes de usuário
- [ ] Usa variáveis de ambiente
- [ ] Valida inputs
- [ ] Trata erros adequadamente
- [ ] Não loga informações sensíveis
- [ ] Documentação de uso incluída
```

### 🔧 Exemplo de Script Seguro

```powershell
# script_seguro.ps1
param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = ".env"
)

$ErrorActionPreference = "Stop"

# Caminho dinâmico
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Verificar arquivo de config
if (-not (Test-Path $ConfigPath)) {
    Write-Error "Config file not found: $ConfigPath"
    Write-Host "Copy .env.example to .env and configure"
    exit 1
}

# Ler variáveis de ambiente
Get-Content $ConfigPath | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}

# Validar credenciais
$ApiKey = $env:API_KEY
if (-not $ApiKey -or $ApiKey -eq "your_api_key_here") {
    Write-Error "API_KEY not configured properly"
    exit 1
}

# Usar credenciais (sem logar)
try {
    $result = Invoke-RestMethod -Uri "https://api.com" `
        -Headers @{"API-Key"=$ApiKey}
    
    Write-Host "Success!" -ForegroundColor Green
} catch {
    Write-Error "Failed: $($_.Exception.Message)"
    # Não logar $ApiKey
}
```

---

## 7. REVISÃO ANTES DO PUSH

### 🔍 Checklist de Revisão Obrigatória

```powershell
# 1. Ver todos os arquivos que serão commitados
git status

# 2. Ver diff completo
git diff --cached

# 3. Verificar se .env está sendo ignorado
git check-ignore *.env backend/.env frontend/.env

# 4. Buscar por padrões sensíveis nos arquivos staged
git diff --cached | grep -i "password\|secret\|token\|api_key"

# 5. Verificar tamanho do commit
git diff --cached --stat

# 6. Ver lista de todos os arquivos rastreados
git ls-files

# 7. Simular push (ver o que será enviado)
git push --dry-run
```

### ⚠️ Red Flags (Parar se encontrar)

```plaintext
❌ Arquivo .env ou .env.local sendo commitado
❌ Strings como "password=", "api_key=", "secret="
❌ Caminhos com C:\Users\[nome]
❌ IPs públicos ou domínios privados
❌ Arquivos de log (*.log, *.err)
❌ Arquivos muito grandes (>10MB)
❌ Binários desnecessários (.exe, .dll)
❌ node_modules/ ou .venv/ sendo commitados
```

### ✅ Safe to Push

```plaintext
✓ Apenas código-fonte
✓ Documentação atualizada
✓ Arquivos .example sem credenciais reais
✓ Configurações de IDE (sem credenciais)
✓ Scripts com caminhos dinâmicos
✓ Testes com dados mock
✓ .gitignore completo e validado
```

---

## 8. PROTEÇÃO DE BRANCHES

### 🔒 Configurar Branch Protection Rules (GitHub)

#### Repository Settings → Branches → Add Rule

```yaml
Branch name pattern: main

Protect matching branches:
  ✓ Require a pull request before merging
    - Required approvals: 1 (se equipe)
  ✓ Require status checks to pass before merging
    - CI/CD tests
    - Code scanning (CodeQL)
  ✓ Require conversation resolution before merging
  ✓ Do not allow bypassing the above settings
  ✓ Restrict who can push to matching branches
```

### 🚀 Workflow Recomendado (Git Flow Simplificado)

```plaintext
main (produção, protegida)
  ↑
develop (desenvolvimento, protegida)
  ↑
feature/nome-da-feature (branches de trabalho)

# Criar feature
git checkout develop
git checkout -b feature/momentum-strategy

# Trabalhar na feature
git add .
git commit -m "feat: implement momentum strategy"

# Push para review
git push origin feature/momentum-strategy

# Criar Pull Request no GitHub
# Após aprovação → Merge para develop
# Release → Merge develop para main
```

---

## 9. SECRETS MANAGEMENT

### 🔐 GitHub Secrets (para CI/CD)

#### Repository Settings → Secrets and Variables → Actions

```yaml
Adicionar secrets:
- BINANCE_API_KEY
- BINANCE_API_SECRET
- TELEGRAM_BOT_TOKEN
- MONGO_PASSWORD

Usar em workflows (.github/workflows/deploy.yml):
```

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy Backend
        env:
          BINANCE_API_KEY: ${{ secrets.BINANCE_API_KEY }}
          BINANCE_API_SECRET: ${{ secrets.BINANCE_API_SECRET }}
        run: |
          python deploy.py
```

### 🔑 Alternativas para Secrets Management

#### 1. AWS Secrets Manager
```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='trading-bot/api-keys')
```

#### 2. Azure Key Vault
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://my-vault.vault.azure.net/", credential=credential)
secret = client.get_secret("api-key")
```

#### 3. HashiCorp Vault
```python
import hvac

client = hvac.Client(url='http://localhost:8200')
secret = client.secrets.kv.v2.read_secret_version(path='api-keys')
```

#### 4. Doppler (Recomendado para Startups)
```bash
# Instalar
curl -Ls https://cli.doppler.com/install.sh | sh

# Configurar
doppler setup

# Rodar app com secrets
doppler run -- python backend/server.py
```

---

## 10. AUDITORIA E MONITORAMENTO

### 🔍 Ferramentas de Auditoria

#### 1. GitGuardian (Detecta Secrets)
```bash
# Instalar
pip install ggshield

# Scan do repositório
ggshield scan repo .

# Hook pre-commit
ggshield install -m global
```

#### 2. TruffleHog (Busca Secrets no Histórico)
```bash
# Instalar
pip install truffleHog

# Scan completo
trufflehog filesystem . --json

# Scan apenas recent commits
trufflehog git file://. --since_commit HEAD~10
```

#### 3. git-secrets (AWS)
```bash
# Instalar (Linux/Mac)
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets && make install

# Configurar
git secrets --install
git secrets --register-aws

# Scan
git secrets --scan
```

#### 4. Gitleaks (GitHub Action)
```yaml
# .github/workflows/gitleaks.yml
name: Gitleaks

on: [push, pull_request]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: gitleaks/gitleaks-action@v2
```

### 📊 Métricas de Segurança

```yaml
KPIs de Segurança:
  - Secrets expostos: 0 (ZERO TOLERANCE)
  - Tempo para remediar secret exposto: < 1 hora
  - Cobertura de .gitignore: 100%
  - Arquivos sensíveis no histórico: 0
  - Branches protegidas: main, develop
  - Aprovações de PR: min 1
  - Scan de segurança: semanal
```

---

## 🚨 INCIDENTE: SECRET EXPOSTO - PLANO DE AÇÃO

### Se Você Acidentalmente Commitou e Fez Push de um Secret:

#### 1️⃣ IMEDIATO (< 5 minutos)

```powershell
# 1. Revogar credencial IMEDIATAMENTE
# Binance: https://www.binance.com/en/my/settings/api-management
# Telegram: Falar com @BotFather e revogar token

# 2. Gerar novas credenciais
# Anotar em local seguro (Password Manager)
```

#### 2️⃣ CURTO PRAZO (< 1 hora)

```powershell
# 3. Remover do histórico git
git filter-repo --invert-paths --path backend/.env
git push --force

# 4. Atualizar .env local com novas credenciais

# 5. Atualizar GitHub Secrets (se usar CI/CD)

# 6. Notificar equipe (se houver)
```

#### 3️⃣ MÉDIO PRAZO (< 24 horas)

```powershell
# 7. Auditoria completa
git log --all --source -- "*.env"
trufflehog filesystem .

# 8. Implementar prevenção
git secrets --install
ggshield install -m global

# 9. Documentar incidente
# - O que aconteceu
# - Como foi detectado
# - Ações tomadas
# - Prevenção futura
```

#### 4️⃣ LONGO PRAZO (< 1 semana)

```powershell
# 10. Review de processos
# - Treinamento de equipe
# - Automação de checks
# - Monitoring contínuo

# 11. Implementar rotação de secrets
# - Mudar API keys mensalmente
# - Usar secrets manager

# 12. Configurar alertas
# - GitHub Advanced Security
# - Email em case de secret detectado
```

---

## 📚 RECURSOS ADICIONAIS

### 🔗 Links Úteis

- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Git Security](https://git-scm.com/book/en/v2/Git-Tools-Signing-Your-Work)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

### 📦 Ferramentas Recomendadas

```yaml
Segurança:
  - GitGuardian (secrets detection)
  - Snyk (vulnerabilidades em dependências)
  - Dependabot (auto-update de deps)
  - CodeQL (code scanning)

Qualidade:
  - SonarQube (code quality)
  - pre-commit (hooks automáticos)
  - Black/Prettier (formatação)
  - Pylint/ESLint (linting)

CI/CD:
  - GitHub Actions
  - GitLab CI
  - CircleCI
  - Jenkins
```

---

## ✅ CHECKLIST FINAL - PRONTO PARA GITHUB

```yaml
Segurança:
  - [ ] .gitignore completo e testado
  - [ ] .env.example criado (sem credenciais reais)
  - [ ] Nenhum secret no código-fonte
  - [ ] Caminhos hardcoded removidos
  - [ ] Histórico git limpo (sem secrets)
  - [ ] Scan de segurança executado
  - [ ] Branch protection configurada

Código:
  - [ ] README.md completo
  - [ ] Documentação atualizada
  - [ ] Dependências documentadas
  - [ ] Instruções de instalação claras
  - [ ] Testes rodando
  - [ ] Código formatado

Legal:
  - [ ] LICENSE definida (MIT, GPL, etc)
  - [ ] Sem código de terceiros sem licença
  - [ ] Atribuições de autoria corretas

Operacional:
  - [ ] CI/CD configurado
  - [ ] Scripts testados
  - [ ] Logs sem informações sensíveis
  - [ ] Backup realizado antes do push
```

---

## 🎯 RESUMO EXECUTIVO

### ⛔ NUNCA FAÇA
1. Commitar arquivos .env
2. Incluir API keys, tokens ou senhas no código
3. Fazer push sem revisar git diff
4. Usar caminhos hardcoded com nomes de usuário
5. Commitar node_modules, .venv, ou arquivos binários
6. Ignorar avisos de secret detection
7. Fazer push direto para main sem review

### ✅ SEMPRE FAÇA
1. Usar .env.example como template
2. Adicionar .gitignore ANTES do primeiro commit
3. Revisar git diff antes de commit
4. Usar caminhos dinâmicos em scripts
5. Scan de segurança regularmente
6. Revocar credenciais se expostas
7. Documentar processos de segurança

---

**Criado por:** GitHub Copilot  
**Baseado em:** OWASP, GitHub Security Best Practices, NIST Guidelines  
**Versão:** 2.0  
**Data:** 15/01/2026

---

## 📞 SUPORTE

Se você encontrou um secret exposto:
1. **NÃO ENTRE EM PÂNICO**
2. Siga o [Plano de Ação para Secrets Expostos](#-incidente-secret-exposto---plano-de-ação)
3. Documente o incidente
4. Aprenda e implemente prevenção

**Lembre-se:** Erros acontecem. O importante é reagir rapidamente e aprender com eles.
