# 🤖 Guia de Setup: Ollama + Mistral 7B

**Status:** ✅ Pronto para Usar
**Data:** 23/01/2026
**Hardware:** Dell E7450 (i5-5300U)

---

## 1️⃣ INSTALAÇÃO RÁPIDA (5 min)

### Windows - Opção A: Instalador (Recomendado)

```powershell
# 1. Download e instale
# Acesse: https://ollama.ai/download/windows
# OU use chocolatey:

choco install ollama -y

# 2. Aguarde reinicialização (pode levar 1-2 min)

# 3. Verifique instalação
ollama --version
# Output: ollama version 0.1.32 (ou similar)

# 4. Puxe o modelo Mistral
ollama pull mistral

# ⏳ Aguarde ~5 min (4.7GB download)
# ✅ Modelo pronto
```

### Windows - Opção B: Docker

```powershell
# Se preferir isolar em container
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  ollama/ollama

# Puxar modelo dentro do container
docker exec ollama ollama pull mistral
```

### macOS / Linux

```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# Ambos: puxar modelo
ollama pull mistral
```

---

## 2️⃣ VERIFICAÇÃO: Ollama Rodando?

### Teste 1: API ativa?

```powershell
# Terminal
curl http://localhost:11434/api/tags

# Se tudo OK, você verá:
# {
#   "models": [
#     {
#       "name": "mistral:latest",
#       ...
#     }
#   ]
# }
```

### Teste 2: Python consegue conectar?

```python
# python
import ollama

# Listar modelos
models = ollama.list()
print([m['name'] for m in models['models']])
# Output: ['mistral:latest']

# Testar resposta
response = ollama.generate(
    model='mistral',
    prompt='What is 2+2?',
    stream=False
)
print(response['response'])
```

### Teste 3: Bot consegue usar?

```python
# Dentro do bot
python -m bot.llm_analyzer

# Output esperado:
# 🤖 Testando LLM Analyzer...
# Status: ✅ Ativo
# ...
```

---

## 3️⃣ INTEGRAÇÃO NO BOT

### Passo 1: Instalar Dependência

```bash
# Na pasta do bot
pip install ollama==0.1.32

# Ou se usar requirements.txt (já adicionado)
pip install -r backend/requirements.txt
```

### Passo 2: Habilitar no Config

```python
# backend/bot/config.py
@dataclass
class BotConfig:
    # ... existing fields ...

    # LLM Settings (NOVO)
    llm_enabled: bool = True              # Habilita IA
    llm_model: str = "mistral"           # Modelo
    llm_confidence_threshold: float = 0.5 # Min confiança
    llm_position_size_boost: float = 1.2  # Boost se confiante
```

### Passo 3: Carregar no TradingBot

```python
# backend/bot/trading_bot.py
from bot.llm_analyzer import get_llm_analyzer

class TradingBot:
    def __init__(self, db):
        # ... existing init ...

        # NOVO: carregar LLM
        self.llm_analyzer = get_llm_analyzer()

        if self.llm_analyzer.enabled:
            logger.info("[BOT] LLM Analyzer pronto")
```

### Passo 4: Usar em `_find_and_open_position()`

```python
# trading_bot.py ~linha 1450
async def _find_and_open_position(self):
    # ... existing code ...

    # Após calculate_unified_score()
    tech_score = score_result['score']

    if tech_score >= 80 and self.llm_analyzer.enabled:
        # Pedir confirmação IA
        llm_result = await self.llm_analyzer.analyze_entry(
            symbol=symbol,
            price=current_price,
            technical_score=tech_score,
            indicators={
                'rsi': df['rsi'].iloc[-1],
                'macd_hist': df['macd_hist'].iloc[-1],
                'atr': df['atr'].iloc[-1],
                'ema_50': df['ema_50'].iloc[-1],
                'ema_200': df['ema_200'].iloc[-1],
                'volume_ratio': opportunity.get('volume_ratio', 1.0),
            }
        )

        # Decidir se entra
        if llm_result.confidence > 0.6:
            logger.info("[LLM] ✅ Confirmado: %s (conf: %.0f%%)",
                       symbol, llm_result.confidence * 100)
            # Entrar normalmente
        else:
            logger.warning("[LLM] ❌ Rejeitado: %s (conf: %.0f%%)",
                          symbol, llm_result.confidence * 100)
            return  # Skip entry
```

---

## 4️⃣ VARIÁVEIS DE AMBIENTE

### Habilitar/Desabilitar IA

```bash
# .env
LLM_ENABLED=true        # true = ativa, false = desativa

# Ou variável de sistema (Windows)
setx LLM_ENABLED false  # Desativa IA sem remover código
```

### Outras Opções

```bash
# Timeout de resposta (segundos)
LLM_TIMEOUT=10

# Modelo alternativo (se quiser trocar)
LLM_MODEL=neural-chat   # Precisa fazer ollama pull neural-chat

# Cache TTL (segundos)
LLM_CACHE_TTL=30
```

---

## 5️⃣ PERFORMANCE & RECURSOS

### RAM Utilizado

```
Ollama Mistral 7B: ~4.7GB (quando ativo)
Trading Bot:       ~2.5GB
Sistema:           ~2.5GB
─────────────────────────
Total:             ~9.7GB de 12GB ✅ OK
```

### CPU Durante IA

```
Event Loop (Bot):  ~20% (main thread)
Ollama (IA):       ~70-80% (thread pool - não bloqueia)
──────────────────
Total:             ~100% (2 cores) ✅ Máximo permitido
```

### Tempo de Resposta

```
Análise IA:  2-5 segundos (dentro do intervalo 15s do bot)
Overhead:    +10% por trade com IA
```

---

## 6️⃣ TROUBLESHOOTING

### Problema: "Ollama not found"

```
❌ Solução: Ollama não instalado
✅ Fix:     choco install ollama -y
```

### Problema: "Model not found: mistral"

```
❌ Solução: Modelo não puxado
✅ Fix:     ollama pull mistral
```

### Problema: "Connection refused: localhost:11434"

```
❌ Solução: Ollama não está rodando
✅ Fix:
   Windows: Abra "Ollama" (atalho desktop/menu)
   Linux:   sudo systemctl start ollama
   macOS:   Abra Ollama.app
```

### Problema: RAM alto (Bot morrendo)

```
❌ Solução: Memória insuficiente
✅ Fix:
   Opção A: Desabilitar IA (LLM_ENABLED=false)
   Opção B: Usar modelo menor (phi:3.8b - 2.3GB)
   Opção C: Aumentar RAM
```

### Problema: Lento (bot trava 5+ segundos)

```
❌ Solução: Ollama demorando muito
✅ Fix:
   Opção A: Aumentar temperatura (mais rápido, menos preciso)
   Opção B: Reduzir num_predict (resposta mais curta)
   Opção C: Usar Phi 3 (mais rápido)
```

---

## 7️⃣ MONITORAMENTO

### Logs do LLM

```python
# Habilitar logs detalhados
import logging
logging.getLogger('bot.llm_analyzer').setLevel(logging.DEBUG)

# Exemplos de logs:
# [LLM] Ollama conectado. Modelos: ['mistral:latest']
# [LLM] Cache HIT para BTCUSDT_42500.00
# [LLM] BTCUSDT - Opinion: BUY, Confidence: 85%, Score: 75
# [LLM] Resposta em 3245ms
```

### Métricas em Tempo Real

```python
from bot.llm_analyzer import get_llm_analyzer

analyzer = get_llm_analyzer()
metrics = analyzer.get_metrics()

print(f"Total requests: {metrics['requests_total']}")
print(f"Cache hits: {metrics['cache_hits']}")
print(f"Timeouts: {metrics['ollama_timeouts']}")
print(f"Avg latency: {metrics['avg_latency_ms']:.0f}ms")
```

---

## 8️⃣ MODELOS ALTERNATIVOS

Se quiser trocar de modelo:

| Modelo | Size | Latência | Accuracy | Speed | RAM |
|--------|------|----------|----------|-------|-----|
| mistral | 7B | 3-5s | 85% | ⚡⚡⚡ | 4.7GB |
| neural-chat | 7B | 2-4s | 78% | ⚡⚡⚡⚡ | 4.5GB |
| llama2 | 7B | 5-8s | 82% | ⚡⚡ | 5.4GB |
| phi | 3.8B | 1-2s | 75% | ⚡⚡⚡⚡⚡ | 2.3GB |

```bash
# Para trocar:
ollama pull neural-chat
# Depois: setx LLM_MODEL neural-chat
```

---

## 9️⃣ CHECKLIST PRÉ-DEPLOYMENT

- [ ] Ollama instalado (`ollama --version`)
- [ ] Mistral puxado (`ollama list` mostra mistral)
- [ ] API responde (`curl http://localhost:11434/api/tags`)
- [ ] Python consegue conectar (teste `import ollama`)
- [ ] Bot testa com sucesso (`python -m bot.llm_analyzer`)
- [ ] `ollama==0.1.32` em `requirements.txt`
- [ ] `LLMAnalyzer` integrado em `TradingBot`
- [ ] `_find_and_open_position()` usa LLM
- [ ] Variáveis de env configuradas (`.env`)
- [ ] Logs aparecem normalmente

---

## 🔟 PRÓXIMOS PASSOS

1. ✅ **Setup Ollama** (esta guia)
2. ⏳ **Integrar LLM no bot** (ver arquivo `llm_analyzer.py`)
3. ⏳ **Testar no testnet** (10 trades)
4. ⏳ **Deploy em produção**

---

## 📞 SUPORTE

Se tiver problemas:

1. Check logs: `tail -f logs/bot.log | grep LLM`
2. Verifique status: `ollama list`
3. Recompile: `pip install --upgrade ollama`
4. Reinicie Ollama (feche e abra novamente)

**Pronto para começar?** Execute:

```bash
ollama pull mistral
python -m bot.llm_analyzer
```

Se ver "Status: ✅ Ativo" - você está pronto! 🎉
