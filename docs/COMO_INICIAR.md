# 🚀 Como Iniciar o Trading Bot System

## Problema Resolvido

**Sintoma**: "Não salva as configurações no dashboard"

**Causa**: Frontend (interface web) não estava rodando

**Solução**: Iniciar frontend E backend antes de usar o Dashboard

---

## ⚡ Método 1: Script Automático (RECOMENDADO)

### Uso do `start_system.ps1`

1. **Abrir PowerShell como Administrador** (botão direito > Executar como administrador)

2. **Navegar até a pasta do projeto**:
   ```powershell
   cd C:\Users\igor\Desktop\17-10-2025-main
   ```

3. **Executar o script**:
   ```powershell
   .\start_system.ps1
   ```

4. **O script irá**:
   - ✅ Verificar se MongoDB está rodando
   - ✅ Iniciar o Backend (Python/FastAPI)
   - ✅ Iniciar o Frontend (React)
   - ✅ Abrir o Dashboard no navegador
   - ✅ Mostrar status de todos os serviços

5. **Resultado esperado**:
   ```
   ═══════════════════════════════════════════════════════
       📊 STATUS DO SISTEMA
   ═══════════════════════════════════════════════════════

      MongoDB:  ✅ ATIVO
      Backend:  ✅ ATIVO  (http://localhost:8001)
      Frontend: ✅ ATIVO  (http://localhost:3000)

   ═══════════════════════════════════════════════════════
       ✅ SISTEMA INICIADO COM SUCESSO!
   ═══════════════════════════════════════════════════════
   ```

---

## 🔧 Método 2: Inicialização Manual

### Passo 1: Verificar MongoDB

```powershell
# Verificar se está rodando
sc query MongoDB

# Se não estiver, iniciar
net start MongoDB
```

### Passo 2: Iniciar Backend

Abrir um terminal PowerShell:

```powershell
cd C:\Users\igor\Desktop\17-10-2025-main\backend
python server.py
```

**Aguardar mensagem**:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
```

✅ **Deixar este terminal ABERTO** (não fechar)

### Passo 3: Iniciar Frontend

Abrir **OUTRO** terminal PowerShell:

```powershell
cd C:\Users\igor\Desktop\17-10-2025-main\frontend
npm start
```

**Aguardar mensagem**:
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
```

✅ **Deixar este terminal ABERTO** (não fechar)

### Passo 4: Acessar Dashboard

Abrir navegador em:
```
http://localhost:3000
```

---

## 📝 Como Salvar Configurações Corretamente

Agora que o sistema está rodando, siga estes passos:

### 1. Acessar Settings

1. Abrir http://localhost:3000
2. Clicar em **"Settings"** no menu lateral (ícone de engrenagem)

### 2. Preencher Credenciais

**Binance API**:
- **API Key**: Sua chave da Binance (não pode ter "...")
- **API Secret**: Seu secret da Binance (não pode ter "***")
- **Testnet Mode**: ✅ Ativado (recomendado para testes)

**Telegram**:
- **Bot Token**: Token do BotFather (formato: `123456789:ABC...`)
- **Chat ID**: Seu chat ID (número)

**Parâmetros de Trading**:
- **Max Positions**: 3 (padrão)
- **Risk %**: 2.0 (padrão)
- **Leverage**: 5x (padrão)

### 3. Salvar

1. Clicar no botão **"Salvar Configurações"** (verde, no topo)
2. Aguardar toast de confirmação:
   ```
   ✅ Configurações salvas com sucesso!
   ```

### 4. Verificar

Se salvou corretamente:
- ✅ Toast verde aparece
- ✅ Campos não ficam vazios
- ✅ Pode ir para Dashboard e iniciar o bot

Se deu erro:
- ❌ Toast vermelho aparece
- ❌ Abrir DevTools (F12) e verificar aba Console
- ❌ Verificar se backend está rodando

---

## 🐛 Problemas Comuns

### Erro: "ERR_CONNECTION_REFUSED"

**Causa**: Backend não está rodando

**Solução**:
```powershell
cd C:\Users\igor\Desktop\17-10-2025-main\backend
python server.py
```

---

### Erro: "Cannot GET /"

**Causa**: Frontend não está rodando

**Solução**:
```powershell
cd C:\Users\igor\Desktop\17-10-2025-main\frontend
npm start
```

---

### Erro: "Por favor, preencha a API Key completa"

**Causa**: Campo contém "..." ou está vazio

**Solução**: Colar a API Key **completa** da Binance

---

### Página em Branco

**Causa**: Frontend ainda compilando ou erro de compilação

**Solução**:
1. Verificar terminal onde rodou `npm start`
2. Aguardar mensagem "Compiled successfully!"
3. Recarregar página (F5)

---

### Salvou mas não apareceu

**Causa**: Frontend não recarregou os dados

**Solução**:
1. Recarregar página (F5)
2. Verificar no DevTools (F12) se houve erro

---

## 🔍 Como Verificar se Está Funcionando

### Verificar Backend

```powershell
# Testar endpoint de health
Invoke-RestMethod -Uri "http://localhost:8001/api/"

# Deve retornar:
# {
#   "message": "Trading Bot API",
#   "status": "online"
# }
```

### Verificar Frontend

Abrir navegador em http://localhost:3000 - deve aparecer o Dashboard

### Verificar MongoDB

```powershell
sc query MongoDB
# Deve mostrar: RUNNING
```

---

## 📊 Status dos Serviços

### Verificação Rápida

```powershell
# Backend
Test-NetConnection -ComputerName localhost -Port 8001 -InformationLevel Quiet
# Deve retornar: True

# Frontend
Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet
# Deve retornar: True

# MongoDB
sc query MongoDB | Select-String "RUNNING"
# Deve retornar a linha com RUNNING
```

---

## 🛑 Como Parar o Sistema

### Método 1: Fechar Janelas

Simplesmente fechar as janelas do PowerShell onde estão rodando:
- Backend (python server.py)
- Frontend (npm start)

### Método 2: Ctrl+C

Nas janelas do PowerShell:
1. Pressionar `Ctrl+C`
2. Confirmar com `S` (Sim)

### Método 3: Kill Process

```powershell
# Parar Backend
Get-Process | Where-Object {$_.ProcessName -like '*python*'} | Stop-Process -Force

# Parar Frontend
Get-Process | Where-Object {$_.ProcessName -eq 'node'} | Stop-Process -Force
```

---

## 📚 Arquivos de Documentação

- **DIAGNOSTICO_SALVAR_CONFIG.md**: Análise completa do problema
- **CORRECAO_FECHAMENTO_POSICAO.md**: Correção de erro ao fechar posições
- **README.md**: Instruções gerais do projeto
- **COMO_INICIAR.md**: Este arquivo

---

## ✅ Checklist Rápido

Antes de usar o Dashboard, verificar:

- [ ] MongoDB rodando (`sc query MongoDB`)
- [ ] Backend rodando (terminal aberto com `python server.py`)
- [ ] Frontend rodando (terminal aberto com `npm start`)
- [ ] Dashboard acessível (http://localhost:3000)
- [ ] Settings carrega sem erro
- [ ] Consegue salvar configurações

Se todos estiverem ✅, o sistema está pronto para uso!

---

**Data**: 19/10/2025
**Status**: ✅ Problema Resolvido
**Próxima Ação**: Configurar credenciais e iniciar bot
