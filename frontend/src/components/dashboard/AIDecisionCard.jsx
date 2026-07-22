import { AlertCircle, Brain, CheckCircle, Loader2, Minus, TrendingDown, TrendingUp } from 'lucide-react';

const GlassCard = ({ children, gradient = false, glow = null, className = '' }) => (
  <div className={`
    relative overflow-hidden rounded-2xl
    bg-gradient-to-br from-white/[0.07] to-white/[0.02]
    backdrop-blur-2xl border border-white/10
    ${gradient ? 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/10 via-white/5 to-transparent' : ''}
    ${className}
  `}>
    {glow && (
      <div className={`absolute -inset-0.5 bg-gradient-to-r from-${glow}-500 via-${glow}-400 to-${glow}-500 opacity-20 blur-xl`} />
    )}
    <div className="relative">{children}</div>
  </div>
);

/**
 * AIDecisionCard - Mostra a última decisão da IA (Ollama LLM)
 *
 * Props:
 * - enabled: Se LLM está habilitado
 * - available: Se Ollama está rodando
 * - metrics: { requests_total, cache_hits, cache_hit_rate, avg_latency_ms }
 * - lastAnalysis: { opinion, confidence, reasoning, symbol, timestamp }
 * - isLoading: Estado de loading
 * - error: Mensagem de erro
 */
const AIDecisionCard = ({
  enabled = false,
  available = false,
  metrics = {},
  lastAnalysis = null,
  isLoading = false,
  error = null
}) => {
  // Mapear opinions para UI
  const opinionConfig = {
    'STRONG_BUY': {
      label: 'Compra Forte',
      icon: TrendingUp,
      color: 'emerald',
      bgColor: 'from-emerald-500 to-emerald-600 bg-emerald-500',
      glowColor: 'emerald'
    },
    'BUY': {
      label: 'Compra',
      icon: TrendingUp,
      color: 'cyan',
      bgColor: 'from-cyan-500 to-cyan-600 bg-cyan-500',
      glowColor: 'cyan'
    },
    'WEAK_BUY': {
      label: 'Compra Fraca',
      icon: TrendingUp,
      color: 'blue',
      bgColor: 'from-blue-500 to-blue-600 bg-blue-500',
      glowColor: 'blue'
    },
    'NEUTRAL': {
      label: 'Neutro',
      icon: Minus,
      color: 'amber',
      bgColor: 'from-amber-500 to-amber-600 bg-amber-500',
      glowColor: 'amber'
    },
    'WEAK_SELL': {
      label: 'Venda Fraca',
      icon: TrendingDown,
      color: 'orange',
      bgColor: 'from-orange-500 to-orange-600 bg-orange-500',
      glowColor: 'orange'
    },
    'SELL': {
      label: 'Venda',
      icon: TrendingDown,
      color: 'rose',
      bgColor: 'from-rose-500 to-rose-600 bg-rose-500',
      glowColor: 'rose'
    },
    'STRONG_SELL': {
      label: 'Venda Forte',
      icon: TrendingDown,
      color: 'red',
      bgColor: 'from-red-500 to-red-600 bg-red-500',
      glowColor: 'red'
    }
  };

  const opinion = lastAnalysis?.opinion || 'NEUTRAL';
  const config = opinionConfig[opinion] || opinionConfig['NEUTRAL'];
  const Icon = config.icon;

  // Calcular cor da confidence gauge
  const confidence = lastAnalysis?.confidence || 0;
  const confidenceColor = confidence >= 0.7 ? 'emerald' : confidence >= 0.4 ? 'amber' : 'rose';

  // Formatar timestamp
  const formatTimestamp = (isoString) => {
    if (!isoString) return 'Aguardando análise';
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now - date;
      const diffSecs = Math.floor(diffMs / 1000);
      const diffMins = Math.floor(diffSecs / 60);

      if (diffSecs < 60) return `${diffSecs}s atrás`;
      if (diffMins < 60) return `${diffMins}m atrás`;
      return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'Tempo inválido';
    }
  };

  // Estados de erro/loading
  if (error) {
    return (
      <GlassCard gradient glow="rose" className="col-span-2">
        <div className="p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 sm:p-3 rounded-xl bg-rose-500/20">
              <AlertCircle className="w-5 h-5 text-rose-400" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-white">IA Indisponível</h3>
              <p className="text-xs text-white/40">Erro ao conectar</p>
            </div>
          </div>
          <p className="text-xs text-rose-400">{error}</p>
        </div>
      </GlassCard>
    );
  }

  if (isLoading) {
    return (
      <GlassCard gradient glow="violet" className="col-span-2">
        <div className="p-4 sm:p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 sm:p-3 rounded-xl bg-violet-500/20">
              <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-white">IA Analisando</h3>
              <p className="text-xs text-white/40">Carregando...</p>
            </div>
          </div>
        </div>
      </GlassCard>
    );
  }

  if (!enabled) {
    return (
      <GlassCard gradient className="col-span-2">
        <div className="p-4 sm:p-6">
          <div className="flex items-center gap-3">
            <div className="p-2 sm:p-3 rounded-xl bg-white/10">
              <Brain className="w-5 h-5 text-white/40" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-white/60">IA Desativada</h3>
              <p className="text-xs text-white/30">LLM Analyzer não inicializado</p>
            </div>
          </div>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard gradient glow={config.glowColor} className="col-span-2">
      <div className="p-4 sm:p-6 relative">
        {/* Glow effect */}
        <div className={`absolute -top-12 -right-12 w-32 h-32 rounded-full blur-3xl opacity-20 ${config.bgColor}`} />

        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 sm:p-3 rounded-xl sm:rounded-2xl bg-gradient-to-br ${config.bgColor} shadow-lg`}>
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-semibold text-white">Análise da IA</h3>
              <p className="text-xs text-white/40">
                {available ? 'Ollama Ativo' : 'Ollama Offline'}
              </p>
            </div>
          </div>

          {/* Status indicator */}
          {available && (
            <div className="flex items-center gap-2 px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30">
              <CheckCircle className="w-3 h-3 text-emerald-400" />
              <span className="text-xs font-medium text-emerald-400">Online</span>
            </div>
          )}
        </div>

        {/* Opinion Badge */}
        {lastAnalysis && (
          <div className="flex items-center gap-3 mb-4">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-xl bg-${config.color}-500/10 border border-${config.color}-500/30`}>
              <Icon className={`w-4 h-4 text-${config.color}-400`} />
              <span className={`text-sm font-semibold text-${config.color}-400`}>{config.label}</span>
            </div>
            {lastAnalysis.symbol && (
              <span className="text-xs font-mono text-white/60">{lastAnalysis.symbol}</span>
            )}
          </div>
        )}

        {/* Confidence Gauge */}
        {lastAnalysis && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-white/50">Confiança</span>
              <span className={`text-sm font-bold text-${confidenceColor}-400`}>
                {(confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 bg-gradient-to-r from-${confidenceColor}-500 to-${confidenceColor}-400`}
                style={{ width: `${confidence * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Reasoning */}
        {lastAnalysis?.reasoning && (
          <div className="mb-4 p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-white/70 leading-relaxed">
              {lastAnalysis.reasoning}
            </p>
          </div>
        )}

        {/* Metrics Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-white/10">
          <div className="flex items-center gap-4">
            <div>
              <p className="text-[10px] text-white/40">Cache</p>
              <p className="text-sm font-semibold text-white">
                {(metrics.cache_hit_rate * 100).toFixed(0)}%
              </p>
            </div>
            <div>
              <p className="text-[10px] text-white/40">Latência</p>
              <p className="text-sm font-semibold text-white">
                {metrics.avg_latency_ms?.toFixed(0) || 0}ms
              </p>
            </div>
            <div>
              <p className="text-[10px] text-white/40">Requests</p>
              <p className="text-sm font-semibold text-white">
                {metrics.requests_total || 0}
              </p>
            </div>
          </div>
          <p className="text-[10px] text-white/30">
            {formatTimestamp(lastAnalysis?.timestamp)}
          </p>
        </div>
      </div>
    </GlassCard>
  );
};

export default AIDecisionCard;
