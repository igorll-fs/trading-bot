import { useCallback, useEffect, useState } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api';
import { Shield, Brain, Zap, Activity, Wifi } from 'lucide-react';

const CONFIG_GROUPS = [
  {
    icon: Brain,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    title: 'Aprendizado & ML',
    items: [
      { key: 'learning_min_trades', label: 'Trades p/ ativar ML', suffix: ' trades', highlight: (v) => v <= 5 },
      { key: 'learning_min_confidence', label: 'Confiança mínima ML', suffix: '', format: (v) => `${(v * 100).toFixed(0)}%`, highlight: (v) => v >= 0.70 },
    ],
  },
  {
    icon: Shield,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    title: 'Proteções',
    items: [
      { key: 'symbol_sl_cooldown_minutes', label: 'Cooldown pós-Stop Loss', suffix: ' min', highlight: (v) => v >= 30 },
      { key: 'risk_max_hold_hours', label: 'Tempo máximo em posição', suffix: ' horas' },
    ],
  },
  {
    icon: Zap,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    title: 'Performance',
    items: [
      { key: 'api_latency_threshold', label: 'Threshold de latência', suffix: 's', highlight: (v) => v >= 10 },
      { key: 'strategy_min_signal_strength', label: 'Força mínima do sinal', suffix: '/100' },
      { key: 'risk_trailing_activation', label: 'Ativação trailing stop', suffix: '%', format: (v) => `${(v).toFixed(1)}%` },
    ],
  },
  {
    icon: Activity,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    title: 'Modo',
    items: [
      { key: 'paper_trade', label: 'Modo Trading', suffix: '', format: (v) => v ? '📝 Paper (simulado)' : '💰 Live (real)' },
      { key: 'llm_risk_advisor_enabled', label: 'LLM Risk Advisor', suffix: '', format: (v) => v ? '🧠 Ativo (Ollama)' : '⏸️ Desligado' },
      { key: 'trading_time_filter', label: 'Filtro de horário', suffix: '', format: (v) => v ? '🕐 Sim' : '🌐 24/7' },
    ],
  },
];

const RuntimeConfigGrid = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchRuntimeConfig = useCallback(async () => {
    try {
      const response = await apiClient.get('/config/runtime', { skipGlobalErrorHandler: true });
      setConfig(response.data ?? {});
    } catch {
      // Silent fail — card shows empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRuntimeConfig();
    const interval = setInterval(fetchRuntimeConfig, 30000); // Refresh a cada 30s
    return () => clearInterval(interval);
  }, [fetchRuntimeConfig]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (!config) {
    return (
      <div className="text-center py-6 text-white/40">
        <Wifi className="mx-auto mb-2 opacity-50" size={24} />
        <p className="text-sm">Backend indisponível para leitura do .env</p>
      </div>
    );
  }

  const formatValue = (item, value) => {
    if (value === undefined || value === null) return '—';
    if (item.format) return item.format(value);
    return `${value}${item.suffix || ''}`;
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {CONFIG_GROUPS.map((group) => (
        <div
          key={group.title}
          className="p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/[0.07] transition-colors"
        >
          <div className="flex items-center gap-2 mb-3">
            <div className={`p-1.5 rounded-lg ${group.bgColor}`}>
              <group.icon size={14} className={group.color} />
            </div>
            <span className="text-xs font-semibold text-white/60 uppercase tracking-wider">
              {group.title}
            </span>
          </div>
          <div className="space-y-2.5">
            {group.items.map((item) => {
              const value = config[item.key];
              const isHighlighted = item.highlight ? item.highlight(value) : false;

              return (
                <div key={item.key} className="flex flex-col gap-0.5">
                  <span className="text-[11px] text-white/40">{item.label}</span>
                  <span
                    className={`text-sm font-mono font-semibold ${
                      isHighlighted
                        ? 'text-amber-300'
                        : 'text-white/80'
                    }`}
                  >
                    {formatValue(item, value)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default RuntimeConfigGrid;
