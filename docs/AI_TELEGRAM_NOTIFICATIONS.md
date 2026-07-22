# 📱 Notificações Telegram - Decisões da IA

## 🎯 Visão Geral

Todas as **5 funcionalidades do LLM Risk Advisor** agora enviam notificações automáticas para o Telegram sempre que tomam decisões importantes!

---

## 📤 Tipos de Notificações

### 1. 🎯 **Adaptive Stop-Loss**

**Quando é enviada:**

- Sempre que a IA ajusta o stop-loss baseado em volatilidade

**Exemplo de mensagem:**

```
🎯 IA: STOP-LOSS ADAPTATIVO

Par: BTCUSDT
Stop: $48,850.00
Multiplier: 2.3x ATR
Confiança: 85%

Volatilidade em 78º percentil e crescente. Stop base seria muito apertado (stops falsos prováveis). Recomendo 2.3x ATR para dar espaço ao movimento.

⏰ 14:35:22
```

---

### 2. 📊 **Position Sizing Inteligente**

**Quando é enviada:**

- Quando a IA ajusta o tamanho da posição baseado na confiança do setup

**Exemplo de mensagem:**

```
📊 IA: AJUSTE DE POSITION SIZE

Par: ETHUSDT
Ajuste: 1.3x (130% do size base)
Confiança: 8/10

Setup excelente com divergência RSI confirmada e volume acima da média. Score técnico 92/100. Recomendo aumentar size em 30%.

⏰ 14:36:45
```

---

### 3. 📰 **Análise Pré-Trade (Horários de Risco)**

**Quando é enviada:**

- **APENAS** quando detecta eventos de risco críticos (CPI, NFP, ECB)
- **NÃO** envia se estiver tudo OK (para evitar spam)

**Exemplo de mensagem:**

```
📰 IA: ANÁLISE PRÉ-TRADE

Par: SOLUSDT
Status: ⛔ NÃO ENTRAR
Sentimento: CAUTION
Urgência: WAIT_1H

Eventos de Risco:
  • CPI Release (13:30 UTC)
  • Alta volatilidade esperada nos próximos 60 minutos

Horário de alto risco detectado (13:35 UTC). Possível anúncio de CPI/NFP. Aguarde passar o evento para evitar volatilidade extrema.

⏰ 13:35:12
```

---

### 4. ❌ **Trade Rejeitado (Skip Reasoning)**

**Quando é enviada:**

- Sempre que o bot rejeita um trade e você quer saber o motivo

**Exemplo de mensagem:**

```
❌ IA: TRADE REJEITADO

Par: AVAXUSDT
Motivo: Score técnico 68/100 abaixo do mínimo (75)

Fatores Adicionais:
  • Volume 40% abaixo da média
  • Mercado lateral dificulta breakouts

💡 Sugestão: Procure setups com score ≥75 e volume confirmado

Trade pulado devido a múltiplos fatores negativos

⏰ 14:37:08
```

---

### 5. 🧠 **Adaptação de Regime (Auto-Evolução)**

**Quando é enviada:**

- Quando a IA faz ajustes automáticos nos parâmetros baseado em performance

**Exemplo Normal:**

```
🧠 IA: ADAPTAÇÃO DE REGIME

Regime: ranging
Status: 🟢 OPERANDO
Win Rate: 25%
Score: +10 pontos
Stop: 1.3x
Size: 80%

Win rate 25% em ranging muito baixo. Aumentando score mínimo +10 para filtrar melhor. Taxa de stops 65% alta. Alargando stops 30% para evitar exits prematuros.

⏰ 14:38:45
```

**Exemplo Crítico (Trading Pausado):**

```
🧠 IA: ADAPTAÇÃO DE REGIME

Regime: ranging
Status: 🔴 PAUSADO
Win Rate: 15%
Score: +15 pontos
Stop: 1.4x
Size: 70%

⚠️ CRÍTICO: Win rate 15% em ranging é insustentável. PAUSANDO operações neste regime até análise. Win rate geral 35% baixo. Reduzindo size para 0.7x até melhorar.

⏰ 14:39:22
```

---

## 🔧 Configuração

### Pré-requisitos

1. **Telegram Bot configurado** no Dashboard (http://localhost:3000/settings)
2. **Bot rodando** com as funcionalidades da IA ativas
3. **Ollama rodando** (localhost:11434)

### Testar Notificações

```bash
# Teste todas as 6 notificações de uma vez
python test_ai_telegram_notifications.py
```

Você receberá 6 mensagens de teste no Telegram simulando todas as decisões.

---

## 📊 Frequência de Notificações

| Tipo                | Frequência Estimada             | Spam?                     |
| ------------------- | ------------------------------- | ------------------------- |
| Adaptive Stop-Loss  | A cada trade aberto             | ❌ Não (1-10x/dia)        |
| Position Sizing     | A cada trade aberto             | ❌ Não (1-10x/dia)        |
| Pre-Trade Sentiment | **Apenas em horários de risco** | ✅ Muito baixa (0-3x/dia) |
| Skip Reasoning      | A cada trade rejeitado          | ⚠️ Moderada (10-30x/dia)  |
| Regime Adaptation   | **Apenas quando faz ajustes**   | ✅ Muito baixa (0-5x/dia) |

### 🔇 Controle de Spam

**Recursos implementados:**

- ✅ **Cache de 60s**: IA não repete análise idêntica
- ✅ **Pre-Trade**: Só notifica se houver RISCO (não em horários normais)
- ✅ **Regime**: Só notifica quando MUDA parâmetros
- ✅ **Reasoning limitado**: Max 500 caracteres por mensagem

**Estimativa total:** 15-50 mensagens/dia (dependendo da atividade do bot)

---

## 🎛️ Desabilitar Notificações (se necessário)

### Desabilitar TODAS as notificações da IA:

```env
# backend/.env
LLM_RISK_ADVISOR_ENABLED=false
```

### Desabilitar APENAS notificações Telegram (mantém IA ativa):

Edite `backend/bot/llm_risk_advisor.py`:

```python
# Linha ~26
TELEGRAM_AVAILABLE = False  # Mude de True para False
```

---

## 🐛 Troubleshooting

### Não estou recebendo notificações

**1. Verifique configuração Telegram:**

```bash
python backend/check_telegram.py
```

**2. Teste manualmente:**

```bash
python backend/scripts/send_telegram_test.py
```

**3. Verifique logs do bot:**

```bash
# Procure por erros
grep "Telegram" logs/backend.log
```

### Recebendo muitas notificações

**Causa provável:** Muitos trades sendo rejeitados (Skip Reasoning)

**Solução:**

- Ajuste `TECHNICAL_SCORE_MIN` para reduzir sinais
- Aumente `OBSERVATION_ALERT_INTERVAL` para espaçar notificações
- Desabilite Skip Reasoning temporariamente (comente no trading_bot.py)

---

## 📈 Próximas Melhorias

**Planejado para v2.0:**

- [ ] Botões inline para aprovar/rejeitar decisões da IA
- [ ] Gráficos inline com análise técnica
- [ ] Modo silencioso noturno (sem notificações 23h-7h UTC)
- [ ] Resumo diário com estatísticas da IA
- [ ] Alertas apenas para decisões de alta confiança (>80%)

---

## 🎓 Exemplos de Uso

### Dashboard NÃO precisa ser atualizado!

**Por quê?**

- As notificações Telegram são **complementares** ao Dashboard
- Dashboard mostra histórico de trades e posições abertas
- Telegram mostra **decisões em tempo real** da IA
- São sistemas independentes e funcionam simultaneamente

### Workflow Completo:

1. **Bot detecta oportunidade** → Logs no terminal
2. **IA analisa** → Notificação Telegram com decisão
3. **Trade executado** → Dashboard atualiza + Telegram notifica
4. **Trade fechado** → Dashboard + Telegram notificam PnL

---

## ✅ Checklist de Ativação

- [ ] Telegram configurado no Dashboard
- [ ] Bot reiniciado após adicionar código
- [ ] Ollama rodando (`ollama serve`)
- [ ] Teste executado (`python test_ai_telegram_notifications.py`)
- [ ] Mensagens recebidas no Telegram
- [ ] Bot operando com IA ativa

---

**🚀 As notificações estão ativas! A IA vai te avisar de TODAS as decisões importantes em tempo real!**
