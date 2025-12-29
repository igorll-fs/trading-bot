# Acesso Remoto ao Trading Bot Dashboard

## Opcao 1: Cloudflare Tunnel (Recomendado - Gratis)

### Instalacao cloudflared

**Windows:**
```powershell
# Baixe de: https://github.com/cloudflare/cloudflared/releases
# Ou via Chocolatey:
choco install cloudflared
```

**Linux/Mac:**
```bash
# Linux
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Mac
brew install cloudflared
```

### Passo a Passo

#### 1. Expor o Backend
```bash
cloudflared tunnel --url http://localhost:8002
```
**Saida:**
```
INFO Connection established
INFO https://abc-def-123.trycloudflare.com
```
Copie essa URL (backend)

#### 2. Expor o Frontend
**Em outro terminal:**
```bash
cloudflared tunnel --url http://localhost:3000
```
**Saida:**
```
INFO https://xyz-uvw-456.trycloudflare.com
```
Copie essa URL (frontend)

#### 3. Acessar no Celular/Tablet
1. Acesse a URL do frontend no navegador: `https://xyz-uvw-456.trycloudflare.com`
2. Popup aparecera solicitando URL do backend
3. Cole a URL do backend: `https://abc-def-123.trycloudflare.com`
4. Clique em "Conectar"
5. Dashboard funcionando remotamente!

---

## Opcao 2: Rede Local (Mesma WiFi)

### Descobrir IP do PC

**Windows:**
```powershell
ipconfig
# Procure por "IPv4 Address" (ex: 192.168.1.100)
```

**Linux/Mac:**
```bash
ifconfig
# ou
ip addr show
# Procure por inet (ex: 192.168.1.100)
```

### Acessar de Outro Dispositivo

**No celular/tablet (mesma rede WiFi):**
```
http://[SEU_IP]:3000
```
**Exemplo:**
```
http://192.168.1.100:3000
```

O backend ja esta configurado para aceitar conexoes externas (`0.0.0.0:8002`)

---

## Opcao 3: ngrok (Alternativa)

### Instalacao
```bash
# Cadastre-se em: https://ngrok.com/
# Baixe e instale ngrok
```

### Uso
```bash
# Terminal 1 - Backend
ngrok http 8002

# Terminal 2 - Frontend
ngrok http 3000
```

Copie as URLs geradas e configure no celular.

---

## Seguranca

- **Cloudflare Tunnel**: URLs sao publicas mas temporarias (mudam a cada execucao)
- **Rede Local**: Apenas dispositivos na mesma WiFi conseguem acessar
- **Producao**: Considere adicionar autenticacao (login/senha)

---

## Troubleshooting

### Dashboard mostra "Offline"
- Verifique se o backend esta rodando: `http://localhost:8002/api/health`
- Confirme que copiou a URL do backend corretamente (com `https://`)

### Cloudflare Tunnel nao inicia
- Firewall pode estar bloqueando. Libere cloudflared
- Verifique se as portas 8002 e 3000 estao livres

### Rede local nao funciona
- Firewall do Windows pode estar bloqueando. Adicione excecao para Node.js e Python
- Confirme que esta na mesma rede WiFi

---

**Desenvolvido por Igor Lacerda** | [@__igor.l_](https://instagram.com/__igor.l_)
