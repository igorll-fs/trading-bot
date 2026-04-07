import {
  Activity,
  AlertCircle,
  Loader2,
  Target,
  TrendingUp,
  Wind,
} from "lucide-react";

const GlassCard = ({
  children,
  gradient = false,
  glow = null,
  className = "",
}) => (
  <div
    className={`
    relative overflow-hidden rounded-2xl
    bg-gradient-to-br from-white/[0.07] to-white/[0.02]
    backdrop-blur-2xl border border-white/10
    ${gradient ? "bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/10 via-white/5 to-transparent" : ""}
    ${className}
  `}
  >
    {glow && (
      <div
        className={`absolute -inset-0.5 bg-gradient-to-r from-${glow}-500 via-${glow}-400 to-${glow}-500 opacity-20 blur-xl`}
      />
    )}
    <div className="relative">{children}</div>
  </div>
);

/**
 * MarketRegimeCard - Mostra análise de regime de mercado do LLM Market Analyzer
 *
 * Props:
 * - enabled: Se Market Analyzer está habilitado
 * - available: Se Ollama está rodando
 * - metrics: { market_analyses, trade_recommendations, avg_latency_ms }
 * - recentAnalyses: Array de análises recentes
 * - tradeHistorySize: Quantidade de trades no histórico
 * - isLoading: Estado de loading
 * - error: Mensagem de erro
 */
const MarketRegimeCard = ({
  enabled = false,
  available = false,
  metrics = {},
  recentAnalyses = [],
  tradeHistorySize = 0,
  isLoading = false,
  error = null,
}) => {
  // Configuração visual por regime
  const regimeConfig = {
    bull_trending: {
      label: "Bull Trending",
      icon: TrendingUp,
      color: "emerald",
      description: "Tendência de alta forte",
      glowColor: "emerald",
    },
    bear_trending: {
      label: "Bear Trending",
      icon: TrendingUp,
      color: "red",
      description: "Tendência de baixa forte",
      glowColor: "red",
      rotate: true,
    },
    ranging: {
      label: "Ranging",
      icon: Activity,
      color: "blue",
      description: "Mercado lateral",
      glowColor: "blue",
    },
    high_volatility: {
      label: "Alta Volatilidade",
      icon: Wind,
      color: "orange",
      description: "Movimentos fortes",
      glowColor: "orange",
    },
    low_volatility: {
      label: "Baixa Volatilidade",
      icon: Target,
      color: "cyan",
      description: "Mercado calmo",
      glowColor: "cyan",
    },
    uncertain: {
      label: "Incerto",
      icon: AlertCircle,
      color: "gray",
      description: "Aguardando definição",
      glowColor: "gray",
    },
  };

  // Se está carregando
  if (isLoading) {
    return (
      <GlassCard className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 backdrop-blur-xl">
            <Activity className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white/90">
              Análise de Mercado
            </h3>
            <p className="text-xs text-white/50">LLM Market Analyzer</p>
          </div>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-purple-400 animate-spin" />
        </div>
      </GlassCard>
    );
  }

  // Se não está habilitado
  if (!enabled) {
    return (
      <GlassCard className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl">
            <Activity className="w-5 h-5 text-white/40" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white/90">
              Análise de Mercado
            </h3>
            <p className="text-xs text-white/50">LLM Market Analyzer</p>
          </div>
        </div>
        <div className="text-center py-6">
          <AlertCircle className="w-12 h-12 text-white/20 mx-auto mb-3" />
          <p className="text-sm text-white/60">Market Analyzer Desativado</p>
          <p className="text-xs text-white/30 mt-1">
            Configure LLM_ENABLED=true
          </p>
        </div>
      </GlassCard>
    );
  }

  // Se não está disponível
  if (!available) {
    return (
      <GlassCard className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-orange-500/20 to-orange-600/20 backdrop-blur-xl">
            <Activity className="w-5 h-5 text-orange-400" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white/90">
              Análise de Mercado
            </h3>
            <p className="text-xs text-white/50">LLM Market Analyzer</p>
          </div>
        </div>
        <div className="text-center py-6">
          <AlertCircle className="w-12 h-12 text-orange-400/40 mx-auto mb-3" />
          <p className="text-sm text-orange-400/80">Ollama Indisponível</p>
          <p className="text-xs text-white/40 mt-1">
            Verifique se Ollama está rodando
          </p>
        </div>
      </GlassCard>
    );
  }

  // Pegar análise mais recente
  const latestAnalysis =
    recentAnalyses && recentAnalyses.length > 0 ? recentAnalyses[0] : null;
  const regime = latestAnalysis
    ? regimeConfig[latestAnalysis.regime] || regimeConfig["uncertain"]
    : regimeConfig["uncertain"];

  const RegimeIcon = regime.icon;

  return (
    <GlassCard className="p-6" glow={regime.glowColor}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div
          className={`p-2.5 rounded-xl bg-gradient-to-br from-${regime.color}-500/20 to-${regime.color}-600/20 backdrop-blur-xl`}
        >
          <Activity className={`w-5 h-5 text-${regime.color}-400`} />
        </div>
        <div className="flex-1">
          <h3 className="text-base font-semibold text-white/90">
            Análise de Mercado
          </h3>
          <p className="text-xs text-white/50">LLM Market Analyzer</p>
        </div>
        <div
          className={`px-2.5 py-1 rounded-lg bg-${regime.color}-500/10 border border-${regime.color}-500/20`}
        >
          <span className={`text-xs font-medium text-${regime.color}-400`}>
            {available ? "Online" : "Offline"}
          </span>
        </div>
      </div>

      {/* Regime Atual */}
      {latestAnalysis && (
        <div className="mb-6">
          <div
            className={`flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-${regime.color}-500/10 to-${regime.color}-600/5 border border-${regime.color}-500/20`}
          >
            <div
              className={`p-3 rounded-xl bg-gradient-to-br from-${regime.color}-500/30 to-${regime.color}-600/20`}
            >
              <RegimeIcon
                className={`w-8 h-8 text-${regime.color}-400 ${regime.rotate ? "rotate-180" : ""}`}
              />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-white/70 mb-1">
                Regime Detectado
              </p>
              <p className={`text-xl font-bold text-${regime.color}-400 mb-1`}>
                {regime.label}
              </p>
              <p className="text-xs text-white/50">{regime.description}</p>
            </div>
          </div>
        </div>
      )}

      {/* Métricas */}
      {latestAnalysis && (
        <div className="grid grid-cols-3 gap-3 mb-6">
          {/* Volatilidade */}
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-white/50 mb-1">Volatilidade</p>
            <p className="text-lg font-bold text-white/90">
              {latestAnalysis.volatility_percentile}º
            </p>
            <p className="text-xs text-white/40">percentil</p>
          </div>

          {/* Força da Tendência */}
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-white/50 mb-1">Tendência</p>
            <p className="text-lg font-bold text-white/90">
              {latestAnalysis.trend_strength}/100
            </p>
            <p className="text-xs text-white/40">força</p>
          </div>

          {/* Histórico */}
          <div className="p-3 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-white/50 mb-1">Histórico</p>
            <p className="text-lg font-bold text-white/90">
              {tradeHistorySize}
            </p>
            <p className="text-xs text-white/40">trades</p>
          </div>
        </div>
      )}

      {/* Estatísticas */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <p className="text-xs text-white/50 mb-1">Análises</p>
          <p className="text-sm font-semibold text-white/90">
            {metrics.market_analyses || 0}
          </p>
        </div>
        <div className="p-3 rounded-xl bg-white/5 border border-white/10">
          <p className="text-xs text-white/50 mb-1">Recomendações</p>
          <p className="text-sm font-semibold text-white/90">
            {metrics.trade_recommendations || 0}
          </p>
        </div>
      </div>

      {/* Latência */}
      {metrics.avg_latency_ms > 0 && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-white/50">Latência Média</span>
            <span className="text-white/70 font-medium">
              {metrics.avg_latency_ms}ms
            </span>
          </div>
        </div>
      )}
    </GlassCard>
  );
};

export default MarketRegimeCard;
