# 🤖 Bot de Trading Automatizado - Binance Spot

Bot de trading automatizado com Machine Learning para Binance Spot, com dashboard web profissional, análise técnica avançada e acesso remoto via Cloudflare.

## ✨ Características Principais

- 🎯 **Trading Automatizado** com estratégias adaptativas
- 📊 **Dashboard Moderno** (React + Tailwind CSS)
- 🧠 **Machine Learning** para filtro de sinais (70%+ acurácia)
- 🌐 **Acesso Remoto** via Cloudflare (https://botrading.uk)
- 📱 **Mobile-First** - Acesse de qualquer lugar
- 💾 **MongoDB** para persistência de dados
- 📈 **Análise em Tempo Real** com gráficos interativos
- ⚡ **Performance Otimizada** para Dell Latitude E7450

## 🚀 Início Rápido

```powershell
# 1. Instalar dependências
.\scripts\install.bat

# 2. Configurar .env
# Copie backend/.env.example para backend/.env
# Copie frontend/.env.example para frontend/.env

# 3. Iniciar todos os serviços
.\scripts\start_all.bat

      - `GET /api/` status da API

# 2. Iniciar      - `GET /api/config` e `POST /api/config` para salvar/ler configurações no MongoDB (coleção `configs`)

.\scripts\start.bat      - `POST /api/bot/control` com `{ action: "start" | "stop" }` para iniciar/parar o bot

      - `GET /api/bot/status` status do bot (saldo, posições)

# 3. Acessar Dashboard      - `GET /api/trades` histórico de trades (coleção `trades`)

# http://localhost:3000      - `GET /api/performance` métricas agregadas de performance

```   - O bot roda em loop assíncrono:

      - Seleciona oportunidades com `CryptoSelector` + `TradingStrategy`

👉 **[Ver Guia Completo](QUICK_START.md)**      - Calcula tamanho de posição com `RiskManager`

      - Opera na Binance (Spot) via `python-binance`

---      - Persiste posições/trades no MongoDB (coleções `positions` e `trades`)

      - Notifica eventos via Telegram

## Passo a passo simples para iniciar (modo Testnet)
1. **Backend**
   Abra um PowerShell, execute `cd backend` e depois:
   ```powershell
   set PYTHONPATH=.
   python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
   ```
   Deixe essa janela aberta (pode minimizar, mas não feche).

2. **Frontend**
   Em outra janela:
   ```powershell
   cd frontend
   yarn start   # ou npm start
   ```
   O navegador abrirá em http://localhost:3000. Essa janela também precisa continuar aberta.

3. **Configurar credenciais**
   - No dashboard, abra **Settings** e mantenha o interruptor em **Testnet**.
   - Apague os campos de API Key e Secret e cole o par gerado em https://testnet.binance.vision (Spot Testnet).
   - Clique em **Salvar configurações**; a mensagem de sucesso confirma o registro no MongoDB.

4. **Adicionar fundos virtuais**
   No site do Testnet, use o menu *Wallet > Faucet* para creditar USDT na key criada.

5. **Validar conexão**
   Em um PowerShell, rode:
   ```powershell
   cd backend
   $env:PYTHONDONTWRITEBYTECODE=1
   python test_binance_connection.py
   ```
   O teste precisa mostrar “Ping OK” e o saldo USDT. Se surgir `APIError -2015`, ajuste a key (permissão Spot, IP liberado, etc.) e repita.

6. **Iniciar o bot**
   Volte ao dashboard e clique em **Start Bot**. Enquanto as duas janelas (backend/front) estiverem abertas, o saldo e os sinais ficarão sincronizados com a conta do testnet.

> Dica: sempre que trocar as credenciais ou mudar para modo real, repita o passo 5 para garantir que a Binance aceitou a nova configuração.

## ✨ Características

- Frontend (React + CRACO) em `frontend/`

- ⚡ **Análise Ultra-Rápida**: Escaneamento a cada 15 segundos   - Páginas: Dashboard, Settings, Trades, Instructions

- 🧠 **Machine Learning**: Aprende com cada trade   - Lê `REACT_APP_BACKEND_URL` para chamar o backend

- 🎯 **Multi-Indicadores**: RSI, MACD, Bollinger, Volume   - Flags de build/dev: `REACT_APP_ENABLE_VISUAL_EDITS`, `ENABLE_HEALTH_CHECK`, `DISABLE_HOT_RELOAD`

- 📊 **Dashboard Interativo**: Monitoramento em tempo real   - Scripts: `yarn start` (porta 3000)

- 🧪 **Testnet**: Teste sem riscos com fundos virtuais

- 📱 **Telegram**: Notificações instantâneas (opcional)Diagrama simplificado do fluxo:

- 🛡️ **Risk Management**: Stop-loss e take-profit automáticosFrontend ⟷ Backend (FastAPI) ⟷ MongoDB

                              ⟍

---                     Binance Spot API + Telegram



## 📁 Estrutura## 📋 Características



```### 🎯 Trading Automatizado

├── backend/          # API FastAPI + Bot Engine- Análise técnica avançada usando EMA, RSI, MACD e Bollinger Bands

├── frontend/         # React Dashboard- Seleção inteligente de criptomoedas baseada em volatilidade e volume

├── scripts/          # Automação (start/stop/monitor)- Gestão de risco com Stop-Loss e Take-Profit automáticos

├── docs/             # Documentação completa- Máximo de 3 posições simultâneas

└── tests/            # Testes automatizados- Alavancagem controlada de 5x

```

### 📊 Dashboard Web Moderno

---- Monitoramento em tempo real do bot

- Visualização de performance com gráficos

## 📊 Monitoramento- Histórico completo de trades

- Tema claro e escuro

```powershell- Interface responsiva e moderna

# Monitorar bot em tempo real

.\scripts\monitor_bot.ps1 -Interval 15 -Duration 600### 🔔 Notificações Telegram

```- Notificações de abertura de posição

- Notificações de fechamento com P&L

---- Status do bot em tempo real



## 🔧 Tecnologias### ⚙️ Configuração Fácil

- Interface web para configurar APIs

**Backend**- Suporte para Testnet e Live Trading

- Python 3.11 | FastAPI | Motor (MongoDB)- Parâmetros de risco configuráveis

- Binance API | TA-Lib | Scikit-learn

### 🤖 Machine Learning (Novo!)

**Frontend**- **Aprendizado automático** a partir de cada trade executado

- React 19 | TailwindCSS | Shadcn/ui- **Ajustes dinâmicos** de Stop Loss, Take Profit e tamanho de posição

- Recharts | Axios- **Filtragem inteligente** com score de confiança (0.0 - 1.0)

- **4 regras de aprendizado** que melhoram win rate e reduzem perdas

**Database**- **Parâmetros salvos** no MongoDB para aprendizado contínuo

- MongoDB (trades, ML data, configs)- 📖 [Documentação completa do ML](MACHINE_LEARNING.md)



---## 🚀 Instalação (Windows)



## 📚 Documentação### Pré-requisitos

- Python 3.8+

- 📖 **[Quick Start](QUICK_START.md)** - Comece em 5 minutos- Node.js 16+

- 🧪 **[Testnet Guide](docs/TESTNET_GUIDE.md)** - Teste sem riscos- MongoDB Community Edition

- 🧠 **[Machine Learning](docs/MACHINE_LEARNING.md)** - Como funciona a IA- Git (opcional)

- 📊 **[Monitoramento](docs/RELATORIO_MONITORAMENTO.md)** - Métricas e KPIs

- 🔧 **[README Original](docs/README_ORIGINAL.md)** - Documentação técnica completa### Passos de Instalação



---1. **Clone ou baixe o projeto**



## ⚠️ Aviso Legal2. **Execute o instalador**

```powershell

Este software é apenas para fins educacionais. Trading envolve riscos significativos. ./install.bat

Sempre teste em **Testnet** antes de usar fundos reais.```



---Este script irá:

- Instalar todas as dependências Python

## 📜 Licença- Instalar todas as dependências Node.js

- Verificar se o MongoDB está instalado

MIT License - Use por sua conta e risco

3. **Configure o MongoDB**

Se você ainda não tem o MongoDB instalado:
- Baixe em: https://www.mongodb.com/try/download/community
- Instale com as configurações padrão
- O MongoDB deve iniciar automaticamente como serviço

### Variáveis de Ambiente

Crie e ajuste os arquivos de exemplo:

- Backend: copie `backend/.env.example` para `backend/.env` e configure pelo menos:
   - `MONGO_URL=mongodb://localhost:27017`
   - `DB_NAME=trading_bot`
   - Opcional: preencha credenciais da Binance/Telegram se não quiser usar o Dashboard inicialmente

- Frontend: copie `frontend/.env.example` para `frontend/.env` e confira:
   - `REACT_APP_BACKEND_URL=http://localhost:8001`

## ⚡ Executando o Bot

### Iniciar o Sistema
```powershell
./start.bat
```

Este script irá:
1. Verificar e iniciar o MongoDB (se necessário)
2. Iniciar o backend (FastAPI)
3. Iniciar o frontend (React)
4. Abrir automaticamente o navegador em http://localhost:3000

### Parar o Sistema
```powershell
./stop.bat
```

### Iniciar automaticamente ao ligar o PC (opcional)

Para evitar ter que clicar no `start.bat` após desligar/reiniciar o PC, você pode criar uma tarefa agendada que inicia o bot no logon do usuário:

1. Abra um PowerShell como usuário (não precisa ser admin) e rode:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\auto-start\create-startup-task.ps1
```

2. Na próxima vez que fizer logon, o `start.bat` será executado automaticamente. O script já é idempotente: se backend/frontend já estiverem rodando, ele não cria instâncias duplicadas.

Ou simplesmente feche as janelas do backend e frontend.

## 🔧 Configuração Inicial

### 🧪 Opção 1: Binance Testnet (Recomendado - SEM RISCO!)

**Por que usar o Testnet?**
- ✅ **100% gratuito** - fundos virtuais de $100,000 USDT
- ✅ **Sem risco financeiro** - opera com dinheiro virtual
- ✅ **Ambiente real da Binance** - mesma API, mesmos mercados
- ✅ **Perfeito para aprender** - teste estratégias sem medo
- ✅ **Configuração rápida** - login com GitHub/Google

**Como configurar o Testnet:**

1. **Criar conta no Testnet:**
   - Acesse: https://testnet.binancefuture.com
   - Clique em "Log In" no canto superior direito
   - Faça login com GitHub ou Google (sem necessidade de criar conta Binance)

2. **Obter fundos virtuais:**
   - Após login, você recebe automaticamente **$100,000 USDT** virtuais
   - Pode recarregar quantas vezes quiser (gratuito)

3. **Gerar API Key:**
   - Clique no ícone de perfil → "API Key"
   - Clique em "Create API Key"
   - Dê um nome (ex: "TradingBot")
   - Copie a **API Key** e **Secret Key** (guarde com segurança!)
   - ⚠️ O Secret Key só aparece UMA vez

4. **Configurar no Dashboard:**
   - Abra http://localhost:3000/settings
   - Cole sua API Key e Secret
   - **IMPORTANTE:** Mantenha o toggle "🧪 Modo Testnet" ATIVADO
   - Salve as configurações

**✅ Pronto! Você pode operar sem gastar 1 centavo!**

---

### 💰 Opção 2: Binance Mainnet (Operação Real)

**⚠️ ATENÇÃO: Esta opção usa dinheiro REAL!**

Só use o Mainnet quando:
- ✅ Já testou e entendeu completamente o bot no Testnet
- ✅ Compreende os riscos do mercado de criptomoedas
- ✅ Tem capital que pode perder (nunca opere com dinheiro essencial)

**Como configurar o Mainnet:**

1. **Criar conta Binance:**
   - Acesse: https://www.binance.com/register
   - Complete o cadastro e verificação KYC

2. **Depositar fundos:**
   - Transfira USDT para sua conta Spot
   - Recomendado: Comece com valores pequenos

3. **Gerar API Key:**
   - Acesse: https://www.binance.com/en/my/settings/api-management
   - Crie uma nova API Key
   - **CRÍTICO:** Ative APENAS a permissão "Enable Spot & Margin Trading"
   - Configure restrições de IP (recomendado)
   - Copie a API Key e Secret

4. **Configurar no Dashboard:**
   - Abra http://localhost:3000/settings
   - Cole sua API Key e Secret
   - **IMPORTANTE:** DESATIVE o toggle "🧪 Modo Testnet"
   - Confirme que está ciente dos riscos
   - Salve as configurações

---

### 📱 Opção 3: Telegram Bot (Opcional - Notificações)

Configure um bot do Telegram para receber notificações em tempo real:

1. **Criar o bot:**
   - Abra o Telegram e busque por `@BotFather`
   - Envie o comando `/newbot`
   - Escolha um nome (ex: "Meu Bot de Trading")
   - Escolha um username único (ex: "meu_trading_bot")
   - Copie o **Bot Token** fornecido (formato: `123456789:ABCdefGHI...`)

2. **Obter seu Chat ID:**
   - Busque por `@userinfobot` no Telegram
   - Inicie uma conversa enviando `/start`
   - Copie o número que aparece como "Id" (seu **Chat ID**)

3. **Configurar no Dashboard:**
   - Abra http://localhost:3000/settings
   - Cole o Telegram Bot Token
   - Cole seu Telegram Chat ID
   - Salve as configurações

4. **Testar:**
   - Envie uma mensagem para o seu bot
   - Inicie o Trading Bot
   - Você receberá notificações quando o bot abrir/fechar posições

---

### ✅ Resumo da Configuração

**Configuração Mínima (Testnet):**
1. ✅ Criar conta em https://testnet.binancefuture.com
2. ✅ Gerar API Key no testnet
3. ✅ Colar no Dashboard com toggle Testnet ATIVO
4. ✅ Salvar e iniciar o bot

**Opcional:**
- 📱 Telegram (para notificações)
- ⚙️ Ajustar parâmetros de risco (max_positions, risk_percentage)

## 🎮 Como Usar

### Iniciando o Bot

1. Certifique-se de que todas as configurações estão preenchidas
2. Vá para o **Dashboard**
3. Clique no botão **Iniciar Bot**
4. O bot começará a:
   - Analisar o mercado
   - Procurar oportunidades
   - Abrir e fechar posições automaticamente
   - Enviar notificações no Telegram

### Monitorando

- **Dashboard**: Visão geral em tempo real
- **Histórico**: Veja todos os trades realizados
- **Telegram**: Receba notificações instantâneas
- **Status**: Verifique posições abertas e saldo

### Parando o Bot

1. Vá para o **Dashboard**
2. Clique no botão **Parar Bot**
3. O bot fechará todas as posições abertas (recomendado fazer manualmente)

## 📈 Estratégia de Trading

### Indicadores Utilizados
- **EMA (12, 26)**: Identificação de tendências
- **RSI (14)**: Detecção de sobrecompra/sobrevenda
- **MACD**: Confirmação de tendência e momentum
- **Bollinger Bands**: Volatilidade e pontos de entrada/saída

### Gestão de Risco
- **Risco por Trade**: 2% do saldo (padrão)
- **Alavancagem**: 5x
- **Stop-Loss**: 2% do preço de entrada
- **Take-Profit**: 4% do preço de entrada
- **Máximo de Posições**: 3 simultâneas

### Criptomoedas Analisadas
BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK, ATOM, LTC, UNI, NEAR

## ⚠️ Avisos Importantes

1. **Trading envolve riscos significativos**
   - Você pode perder todo o capital investido
   - Não invista mais do que pode perder

2. **Este bot não garante lucros**
   - Performance passada não indica resultados futuros
   - O mercado de criptomoedas é altamente volátil

3. **Use por sua conta e risco**
   - O desenvolvedor não se responsabiliza por perdas
   - Teste extensivamente antes de usar dinheiro real

4. **SEMPRE teste no Testnet primeiro**

## 📁 Estrutura do Projeto

```
trading-bot/
├── backend/                 # FastAPI backend
│   ├── bot/                # Módulos do bot
│   ├── server.py           # API REST
│   └── .env               # Variáveis de ambiente (copie de .env.example)
├── frontend/               # React frontend
│   ├── src/pages/         # Dashboard, Settings, Trades, Instructions
│   └── src/components/    # UI Components
├── install.bat            # Script de instalação
├── start.bat              # Script de inicialização
└── stop.bat               # Script para parar
```

---

**⚠️ AVISO LEGAL**: Este software é apenas para fins educacionais. O uso em produção é por sua conta e risco. Sempre faça sua própria pesquisa (DYOR) e consulte um consultor financeiro.
## Backtests Rapidos

Precisa validar a estrategia antes de ir para producao? Rode o script em `backend/scripts/backtest_strategy.py` (detalhes em `docs/BACKTEST.md`). Exemplo:

```powershell
cd backend
$env:PYTHONPATH=.
python scripts/backtest_strategy.py --symbol BTCUSDT --interval 15m --days 14
```

O utilitario baixa candles historicos da Binance, aplica a TradingStrategy e imprime win rate, drawdown e lucro liquido do periodo.
