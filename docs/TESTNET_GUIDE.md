# 🧪 Guia Rápido - Binance Testnet

## Por Que Usar o Testnet?

Se você está sem grana para operar na Binance ou quer testar o bot sem risco, o **Binance Testnet** é a solução perfeita!

### ✅ Vantagens do Testnet

- **100% Gratuito** - Você recebe $100.000 USDT virtuais
- **Sem Risco** - Não usa dinheiro real
- **Ambiente Real** - Mesma API e funcionalidades da Binance
- **Sem Limites** - Pode recarregar fundos quantas vezes quiser
- **Aprenda Tranquilo** - Teste estratégias sem medo de perder dinheiro

## 🚀 Setup em 5 Minutos

### Passo 1: Criar Conta no Testnet

1. Acesse: **https://testnet.binancefuture.com**
2. Clique em **"Log In"** (canto superior direito)
3. Escolha fazer login com:
   - 🐙 GitHub
   - 🔴 Google
   
   > 💡 Não precisa criar conta na Binance!

### Passo 2: Receber Fundos Virtuais

Após o login, você já tem automaticamente:
- 💰 **$100.000 USDT** virtuais
- 🔄 Pode recarregar sempre que quiser (gratuito)
- 📈 Pode operar em todos os pares disponíveis

### Passo 3: Gerar API Key

1. No site do testnet, clique no **ícone de perfil** (canto superior direito)
2. Selecione **"API Key"**
3. Clique em **"Create API Key"**
4. Escolha um nome para sua key (ex: "TradingBot")
5. **COPIE e SALVE:**
   - 🔑 **API Key** - Você vai precisar depois
   - 🔒 **Secret Key** - **ATENÇÃO:** Aparece só uma vez!

⚠️ **IMPORTANTE:** Guarde o Secret Key em local seguro. Se perder, terá que criar uma nova API Key.

### Passo 4: Configurar no Bot

1. Abra o dashboard: **http://localhost:3000**
2. Vá para **"Configurações"** (menu lateral)
3. Na seção **"API Binance Futures"**:
   - Cole sua **API Key**
   - Cole seu **Secret Key**
   - ✅ **MANTENHA o toggle "🧪 Modo Testnet" ATIVADO**
4. Role para baixo e clique em **"Salvar Configurações"**

### Passo 5: Iniciar o Bot

1. Volte para o **Dashboard**
2. Clique no botão **"Iniciar Bot"** (verde)
3. Acompanhe os trades em tempo real
4. Veja seu saldo virtual mudar conforme opera

## 📊 O Que Esperar

Com o Testnet ativo, o bot vai:

- ✅ Conectar na **testnet.binancefuture.com**
- ✅ Usar seus fundos virtuais ($100k USDT)
- ✅ Fazer trades reais (mas com dinheiro virtual)
- ✅ Executar ordens, Stop-Loss, Take-Profit
- ✅ Atualizar seu saldo conforme lucra/perde

**É exatamente como a Binance real, mas SEM RISCO!**

## 🔄 Diferenças Testnet vs Mainnet

| Característica | Testnet 🧪 | Mainnet 💰 |
|----------------|-----------|-----------|
| **Dinheiro** | Virtual ($100k grátis) | Real (seu capital) |
| **Risco** | Zero | Alto |
| **API** | testnet.binancefuture.com | api.binance.com |
| **Trades** | Simulados (dados reais) | Reais |
| **Lucro/Prejuízo** | Virtual | Real |
| **Custo** | Gratuito | Requer depósito |
| **Ideal para** | Aprender, testar | Operar sério |

## ⚙️ Como Alternar Entre Testnet e Mainnet

No dashboard, na página **Configurações**:

### Para Testnet (Recomendado):
- ✅ Toggle "🧪 Modo Testnet" **ATIVADO**
- Use API Keys do https://testnet.binancefuture.com

### Para Mainnet (Apenas se estiver pronto):
- ❌ Toggle "🧪 Modo Testnet" **DESATIVADO**
- Use API Keys do https://www.binance.com
- ⚠️ **CUIDADO:** Vai operar com dinheiro real!

## 🎓 Dicas para Usar o Testnet

1. **Teste Primeiro:** Nunca pule direto para o Mainnet
2. **Experimente Parâmetros:** Ajuste `risk_percentage`, `max_positions`
3. **Entenda a Estratégia:** Veja quais indicadores o bot usa
4. **Observe Erros:** Corrija problemas antes de arriscar dinheiro real
5. **Simule Cenários:** Teste em mercados voláteis e calmos
6. **Documente Resultados:** Anote o que funciona e o que não funciona

## 📈 Quando Passar para Mainnet?

Só migre para o Mainnet quando:

- ✅ Testou o bot por pelo menos 1-2 semanas no testnet
- ✅ Entende completamente como funciona
- ✅ Está consistentemente lucrativo no testnet
- ✅ Conhece os riscos do mercado de criptomoedas
- ✅ Tem capital que pode perder (sem comprometer seu essencial)
- ✅ Configurou Stop-Loss e gerenciamento de risco adequados

## ⚠️ Avisos Importantes

### No Testnet:
- ✅ Pode experimentar à vontade
- ✅ Sem consequências financeiras
- ✅ Perfeito para aprender

### No Mainnet:
- ⚠️ **Riscos reais de perda total do capital**
- ⚠️ Mercado de criptomoedas é extremamente volátil
- ⚠️ Nunca opere com dinheiro que não pode perder
- ⚠️ Trading automatizado não garante lucros
- ⚠️ Comece com valores pequenos

## 🆘 Problemas Comuns

### "API Key inválida"
- ✅ Confirme que copiou corretamente (sem espaços)
- ✅ Verifique se o toggle Testnet está ativo
- ✅ Gere uma nova API Key se necessário

### "Insufficient balance"
- ✅ Recarregue fundos virtuais no testnet
- ✅ Acesse: https://testnet.binancefuture.com/wallet → "Get Test Funds"

### "Connection refused"
- ✅ Confirme que o backend está rodando
- ✅ Verifique se o MongoDB está ativo
- ✅ Reinicie o sistema com `./start.bat`

## 📚 Links Úteis

- **Testnet:** https://testnet.binancefuture.com
- **Documentação Binance Testnet:** https://testnet.binancefuture.com/en/futures/BTCUSDT
- **Binance API Docs:** https://binance-docs.github.io/apidocs/futures/en/

---

## 🎉 Pronto para Começar?

1. **Acesse:** https://testnet.binancefuture.com
2. **Faça login:** GitHub ou Google
3. **Gere API Key:** Menu → API Key → Create
4. **Configure no bot:** Settings → Cole as keys → Toggle Testnet ON
5. **Inicie:** Dashboard → Iniciar Bot

**Boa sorte e bons trades! 🚀📈**

---

*Lembre-se: O testnet é seu ambiente seguro para aprender. Use-o sem medo!*
