# 🚀 VS Code Remote Access - Acesse do Celular

## ⚠️ STATUS ATUAL: ERRO 502

**O que significa**: Cloudflare Tunnel está funcionando, mas VS Code não está instalado/rodando.

**Solução**: Baixar e instalar code-server (5 minutos)

---

## 📋 O QUE JÁ ESTÁ PRONTO

✅ **Senha gerada**: `dKjTCQJuqNLanzt1`  
✅ **Configuração criada**: `C:\Users\igor\.code-server\config.yaml`  
✅ **Cloudflare Tunnel configurado**: `https://botrading.uk/vscode` → `localhost:8080`  
✅ **Diretórios criados**: `.code-server\bin` e `.code-server\data`

---

## 🎯 INSTALAÇÃO RÁPIDA (5 minutos)

### 1. Baixar code-server

Acesse: https://github.com/coder/code-server/releases/latest

Baixe o arquivo: **`code-server-X.X.X-windows-amd64.zip`**

### 2. Extrair arquivos

Extraia TODO o conteúdo ZIP para:
```
C:\Users\igor\.code-server\bin
```

Deve ficar assim:
```
C:\Users\igor\.code-server\bin\code-server.exe
C:\Users\igor\.code-server\bin\node.exe
C:\Users\igor\.code-server\bin\lib\
...
```

### 3. Iniciar code-server

Abra PowerShell e execute:
```powershell
cd C:\Users\igor\.code-server\bin
.\code-server.exe
```

**OU** clique duplo em `code-server.exe`

### 4. Restart Cloudflared Tunnel

- Feche a janela atual do cloudflared
- Execute novamente:
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "C:\Users\igor\cloudflared.exe tunnel run 9800f7d7-542b-44fe-b173-d38caae02747" -WindowStyle Normal
```

### 5. Acessar no Navegador/Celular

**URL**: https://code.botrading.uk  
**Senha**: `dKjTCQJuqNLanzt1`

---

## 🔐 CREDENCIAIS

- **URL Local**: http://localhost:8080
- **URL Remota**: https://code.botrading.uk
- **Senha**: `dKjTCQJuqNLanzt1`

*Senha salva em:* `C:\Users\igor\.code-server\password.txt`

---

## 📱 USAR NO CELULAR

1. Abra qualquer navegador (Chrome, Safari, Firefox)
2. Acesse: **https://code.botrading.uk**
3. Digite a senha: **dKjTCQJuqNLanzt1**
4. Pronto! VS Code completo no celular 🎉

---

## ⚙️ CONFIGURAÇÃO (Já está pronto!)

**Arquivo**: `C:\Users\igor\.code-server\config.yaml`

```yaml
bind-addr: 127.0.0.1:8080
auth: password
password: dKjTCQJuqNLanzt1
cert: false
user-data-dir: C:\Users\igor\.code-server\data
```

**Cloudflare Tunnel**: `C:\Users\igor\.cloudflared\config.yml`

```yaml
ingress:
  # VS Code Web
  - hostname: code.botrading.uk
    service: http://localhost:8080

  # Dashboard (Frontend)
  - hostname: botrading.uk
    service: http://localhost:3000

  # API (Backend)
  - hostname: api.botrading.uk
    service: http://localhost:8000
  
  - service: http_status:404
```

---

## 🔧 COMANDOS ÚTEIS

### Iniciar code-server em background
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\igor\.code-server\bin; .\code-server.exe" -WindowStyle Minimized
```

### Parar code-server
```powershell
Stop-Process -Name "code-server" -Force
```

### Ver senha
```powershell
Get-Content C:\Users\igor\.code-server\password.txt
```

### Testar localmente
```powershell
Start-Process "http://localhost:8080"
```

---

## ✅ CHECKLIST

- [ ] Baixar code-server ZIP do GitHub
- [ ] Extrair para `C:\Users\igor\.code-server\bin`
- [ ] Iniciar `code-server.exe`
- [ ] Restart cloudflared tunnel
- [ ] Acessar https://code.botrading.uk
- [ ] Logar com senha: `dKjTCQJuqNLanzt1`

---

## 🎉 PRONTO!

Agora você tem 3 serviços acessíveis remotamente:

1. **Dashboard Trading Bot**: https://botrading.uk
2. **API Backend**: https://api.botrading.uk
3. **VS Code Web**: https://code.botrading.uk ← NOVO!

Todos acessíveis do celular, tablet, qualquer lugar! 🚀
