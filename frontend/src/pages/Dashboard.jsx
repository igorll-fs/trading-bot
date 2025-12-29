import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Play, Square, TrendingUp, TrendingDown, Wallet, RefreshCw,
  Activity, Target, Award, BarChart3, ArrowUpRight, ArrowDownRight,
  Sparkles, Clock, Zap, Flame, Shield, DollarSign, Percent,
  AlertTriangle, Calculator, LineChart, Brain, Signal, Radio,
  ChevronDown, ChevronUp, Maximize2, Minimize2, Eye, Newspaper,
  ExternalLink, Globe, Bitcoin, Cpu, MemoryStick
} from 'lucide-react';
import { notify } from '@/lib/notify';
import { formatCurrency, formatPercent, formatDateTime } from '@/lib/formatters';
import { Skeleton } from '@/components/ui/skeleton';
import { apiClient } from '@/lib/api';
import { useQueryClient } from 'react-query';
import { useBotPerformance, useBotStatus } from '@/hooks/useBotQueries';
import { useBotStream } from '@/providers/BotDataProvider';
import { BOT_PERFORMANCE_QUERY_KEY, BOT_STATUS_QUERY_KEY } from '@/hooks/queryKeys';
import { useMarketPrices, useActiveSignals, useMarketRegime, useMLStatus, useMonitoredCoins } from '@/hooks/useMarketData';
import { useDashboardPerformance } from '@/hooks/usePerformance';
import { SparklineChart } from '@/components/ui/sparkline-chart';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts';

// Skeleton moderno com shimmer - Premium Theme
const DashboardSkeleton = () => (
  <div className="min-h-screen p-3 sm:p-6">
    <div className="max-w-7xl mx-auto space-y-4 sm:space-y-8">
      <div className="flex justify-between items-center">
        <Skeleton className="h-8 sm:h-10 w-32 sm:w-48 bg-violet-500/10" />
        <Skeleton className="h-10 sm:h-12 w-24 sm:w-32 bg-violet-500/10 rounded-2xl" />
      </div>
      <div className="grid grid-cols-2 gap-3 sm:gap-6">
        {[1,2,3,4].map(i => (
          <Skeleton key={i} className="h-28 sm:h-36 rounded-2xl sm:rounded-3xl bg-white/5 border border-white/10" />
        ))}
      </div>
      <Skeleton className="h-48 sm:h-80 rounded-2xl sm:rounded-3xl bg-white/5 border border-white/10" />
    </div>
  </div>
);

// Componente de card premium com glassmorphism
const GlassCard = ({ children, className = '', gradient = false, hover = true, glow = '' }) => (
  <div className={`
    relative overflow-hidden rounded-2xl sm:rounded-3xl
    bg-white/5 backdrop-blur-xl
    border border-white/10
    ${hover ? 'hover:bg-white/10 hover:border-violet-500/30 hover:shadow-lg hover:shadow-violet-500/10 hover:scale-[1.02]' : ''}
    transition-all duration-500 ease-out
    ${gradient ? 'before:absolute before:inset-0 before:bg-gradient-to-br before:from-violet-500/5 before:via-transparent before:to-cyan-500/5 before:pointer-events-none' : ''}
    ${glow ? `shadow-lg shadow-${glow}-500/20` : ''}
    ${className}
  `}>
    {children}
  </div>
);

// Stat Card premium - Violet/Cyan Theme com Sparkline
const StatCard = ({ label, value, prefix = '', icon: Icon, trend, color, subtext, compact = false, glowColor = 'violet', sparklineData }) => (
  <GlassCard gradient glow={glowColor}>
    <div className={`${compact ? 'p-3 sm:p-4' : 'p-4 sm:p-6'} relative`}>
      {/* Glow effect */}
      <div className={`absolute -top-8 sm:-top-12 -right-8 sm:-right-12 w-20 sm:w-32 h-20 sm:h-32 rounded-full blur-2xl sm:blur-3xl opacity-20 ${color}`} />

      <div className="flex items-start justify-between mb-2 sm:mb-4">
        <div className={`p-2 sm:p-3 rounded-xl sm:rounded-2xl bg-gradient-to-br ${color} shadow-lg`}>
          <Icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-[10px] sm:text-xs font-medium px-1.5 sm:px-2 py-0.5 sm:py-1 rounded-full border ${
            trend >= 0
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
          }`}>
            {trend >= 0 ? <ArrowUpRight className="w-2.5 h-2.5 sm:w-3 sm:h-3" /> : <ArrowDownRight className="w-2.5 h-2.5 sm:w-3 sm:h-3" />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>

      <p className="text-[10px] sm:text-sm font-medium text-white/50 mb-0.5 sm:mb-1 truncate">{label}</p>
      <div className="flex items-end justify-between gap-2">
        <p className="text-lg sm:text-2xl lg:text-3xl font-bold text-white tracking-tight truncate animate-counter">
          {prefix}<span className="tabular-nums">{value}</span>
        </p>
        {sparklineData && sparklineData.length > 0 && (
          <div className="flex-shrink-0">
            <SparklineChart
              data={sparklineData}
              width={60}
              height={24}
              strokeWidth={1.5}
            />
          </div>
        )}
      </div>
      {subtext && <p className="text-[10px] sm:text-xs text-white/40 mt-1 sm:mt-2 truncate hidden sm:block">{subtext}</p>}
    </div>
  </GlassCard>
);

// Custom Tooltip para o grafico - Premium Theme
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const value = payload[0].value;
    return (
      <div className="bg-[#111111]/95 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-2xl shadow-violet-500/20">
        <p className="text-xs text-white/50 mb-1 font-mono">{label}</p>
        <p className={`text-lg font-bold ${value >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
          {value >= 0 ? '+' : ''}{formatCurrency(value)}
        </p>
      </div>
    );
  }
  return null;
};

const Dashboard = () => {
  const queryClient = useQueryClient();
  const { streamState } = useBotStream();
  const [controlLoading, setControlLoading] = useState(false);
  const [chartExpanded, setChartExpanded] = useState(false);
  const [insightsExpanded, setInsightsExpanded] = useState(true);
  const [signalsExpanded, setSignalsExpanded] = useState(true);

  const statusQuery = useBotStatus();
  const performanceQuery = useBotPerformance();

  // Novos hooks para dados de mercado (TODOS DADOS REAIS)
  const { data: marketPrices } = useMarketPrices();
  const { data: activeSignals } = useActiveSignals();
  const { data: marketRegime } = useMarketRegime();
  const { data: mlStatus } = useMLStatus();
  const { data: monitoredCoinsData } = useMonitoredCoins(); // NOVO: Dados reais do backend

  // Hook para sparkline e realtime stats (SessionA endpoints)
  const { sparkline, realtime, isLoading: performanceIsLoading } = useDashboardPerformance();

  const status = statusQuery.data;
  const performance = performanceQuery.data;

  // Moedas monitoradas REAIS do backend (não hardcoded)
  const monitoredCoins = monitoredCoinsData?.coins || [];

  const isInitialLoading = statusQuery.isLoading || performanceQuery.isLoading;
  const isOffline = streamState === 'closed' || streamState === 'unavailable' || statusQuery.isError;

  // Preparar dados do grafico de PnL
  const chartData = useMemo(() => {
    if (!performance?.trades_by_date || performance.trades_by_date.length === 0) {
      return [];
    }

    let cumulativePnl = 0;
    return performance.trades_by_date
      .filter(trade => trade.status === 'closed')
      .map((trade, index) => {
        cumulativePnl += trade.pnl || 0;
        const date = new Date(trade.closed_at);
        return {
          name: `#${index + 1}`,
          date: date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
          pnl: trade.pnl,
          cumulative: parseFloat(cumulativePnl.toFixed(2)),
          symbol: trade.symbol?.replace('USDT', ''),
          side: trade.side,
        };
      });
  }, [performance?.trades_by_date]);

  const handleControl = async (action) => {
    setControlLoading(true);
    try {
      await apiClient.post('/bot/control', { action }, { skipGlobalErrorHandler: true });
      notify.success(action === 'start' ? 'Bot iniciado com sucesso' : 'Bot encerrado');
      await Promise.all([
        queryClient.invalidateQueries(BOT_STATUS_QUERY_KEY),
        queryClient.invalidateQueries(BOT_PERFORMANCE_QUERY_KEY),
      ]);
    } catch (error) {
      notify.error(error.response?.data?.detail || 'Erro ao controlar bot');
    } finally {
      setControlLoading(false);
    }
  };

  const handleSync = async () => {
    try {
      await apiClient.post('/bot/sync', {}, { skipGlobalErrorHandler: true });
      notify.success('Dados sincronizados');
      queryClient.invalidateQueries(BOT_STATUS_QUERY_KEY);
      queryClient.invalidateQueries(BOT_PERFORMANCE_QUERY_KEY);
    } catch {
      notify.error('Erro ao sincronizar');
    }
  };

  const isRunning = status?.is_running ?? false;
  const balance = status?.balance ?? 0;
  const positions = status?.positions ?? [];
  const totalPnl = performance?.total_pnl ?? 0;
  const winRate = performance?.win_rate ?? 0;
  const totalTrades = performance?.total_trades ?? 0;
  const pnlPositive = totalPnl >= 0;

  if (isInitialLoading && !status) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="min-h-screen">
      {/* Ambient background effects - Premium */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-violet-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[128px]" />
        {isRunning && (
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/5 rounded-full blur-[128px] animate-pulse" />
        )}
      </div>

      {/* Header Premium */}
      <header className="relative border-b border-white/10 bg-black/40 backdrop-blur-2xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-20">
            {/* Logo & Status */}
            <div className="flex items-center gap-2 sm:gap-6">
              <div className="flex items-center gap-2 sm:gap-3">
                <div className="relative">
                  <div className={`w-2.5 sm:w-3 h-2.5 sm:h-3 rounded-full ${
                    isOffline ? 'bg-amber-500' : isRunning ? 'bg-emerald-400' : 'bg-white/30'
                  }`} />
                  {isRunning && !isOffline && (
                    <div className="absolute inset-0 w-2.5 sm:w-3 h-2.5 sm:h-3 rounded-full bg-emerald-400 animate-ping opacity-75" />
                  )}
                </div>
                <div>
                  <h1 className="text-sm sm:text-lg font-semibold text-white">Trading Bot</h1>
                  <p className="text-[10px] sm:text-xs text-white/40 hidden sm:block font-mono">
                    {isOffline ? 'Desconectado' : isRunning ? 'Em operacao' : 'Aguardando'}
                  </p>
                </div>
              </div>

              {status?.testnet_mode && (
                <div className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30">
                  <Sparkles className="w-3 sm:w-3.5 h-3 sm:h-3.5 text-cyan-400" />
                  <span className="text-[10px] sm:text-xs font-medium text-cyan-400">Testnet</span>
                </div>
              )}
            </div>

            {/* Controls - Premium Styled */}
            <div className="flex items-center gap-2 sm:gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleSync}
                disabled={isOffline}
                className="w-8 sm:w-10 h-8 sm:h-10 rounded-lg sm:rounded-xl text-white/50 hover:text-white hover:bg-white/10 border border-transparent hover:border-violet-500/30"
              >
                <RefreshCw className="w-3.5 sm:w-4 h-3.5 sm:h-4" />
              </Button>

              <Button
                onClick={() => handleControl(isRunning ? 'stop' : 'start')}
                disabled={controlLoading || isOffline}
                className={`
                  h-9 sm:h-12 px-3 sm:px-6 rounded-xl sm:rounded-2xl font-medium gap-1.5 sm:gap-2 text-sm sm:text-base
                  transition-all duration-300 ease-out
                  ${isRunning
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30 hover:bg-rose-500/20 hover:shadow-lg hover:shadow-rose-500/20'
                    : 'bg-gradient-to-r from-violet-500 to-cyan-500 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 hover:scale-[1.02]'
                  }
                `}
              >
                {isRunning ? <Square className="w-3.5 sm:w-4 h-3.5 sm:h-4" /> : <Play className="w-3.5 sm:w-4 h-3.5 sm:h-4" />}
                <span className="hidden sm:inline">{isRunning ? 'Parar' : 'Iniciar'}</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Premium Theme */}
      <main className="relative max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-10 space-y-4 sm:space-y-10">

        {/* Stats Grid - 2 colunas sempre, responsivo */}
        <section className="grid grid-cols-2 gap-3 sm:gap-6 stagger-children">
          <StatCard
            label="Saldo Total"
            value={formatCurrency(balance)}
            icon={Wallet}
            color="from-violet-500 to-violet-600 bg-violet-500"
            subtext="Disponivel para trading"
            glowColor="violet"
            compact
            sparklineData={sparkline?.points}
          />
          <StatCard
            label="PnL Total"
            value={formatCurrency(Math.abs(totalPnl))}
            prefix={pnlPositive ? '+' : '-'}
            icon={pnlPositive ? TrendingUp : TrendingDown}
            color={pnlPositive ? 'from-emerald-500 to-emerald-600 bg-emerald-500' : 'from-rose-500 to-rose-600 bg-rose-500'}
            subtext={pnlPositive ? 'Lucro acumulado' : 'Prejuizo acumulado'}
            glowColor={pnlPositive ? 'emerald' : 'rose'}
            compact
            sparklineData={sparkline?.points}
          />
          <StatCard
            label="Win Rate"
            value={formatPercent(winRate, { digits: 1 })}
            icon={Target}
            color={winRate >= 50 ? 'from-emerald-500 to-teal-600 bg-emerald-500' : 'from-amber-500 to-orange-600 bg-amber-500'}
            subtext={`${performance?.winning_trades || 0} de ${totalTrades} trades`}
            glowColor={winRate >= 50 ? 'emerald' : 'amber'}
            compact
          />
          <StatCard
            label="ROI"
            value={`${performance?.roi?.toFixed(1) || '0.0'}%`}
            icon={Percent}
            color={performance?.roi >= 0 ? 'from-cyan-500 to-blue-600 bg-cyan-500' : 'from-rose-500 to-rose-600 bg-rose-500'}
            subtext="Retorno sobre investimento"
            glowColor="cyan"
            compact
          />
        </section>

        {/* System Stats - CPU/RAM em tempo real */}
        {realtime && (
          <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <GlassCard gradient>
              <div className="p-3 sm:p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 rounded-lg bg-violet-500/20">
                    <Cpu className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-violet-400" />
                  </div>
                  <span className="text-[10px] sm:text-xs font-medium text-white/40">CPU Usage</span>
                </div>
                <p className="text-lg sm:text-2xl font-bold text-white">{realtime.cpu?.toFixed(1) || '0'}%</p>
                <div className="mt-2 w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ${
                      (realtime.cpu || 0) > 70 ? 'bg-rose-500' : (realtime.cpu || 0) > 50 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${Math.min(realtime.cpu || 0, 100)}%` }}
                  />
                </div>
              </div>
            </GlassCard>

            <GlassCard gradient>
              <div className="p-3 sm:p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 rounded-lg bg-cyan-500/20">
                    <MemoryStick className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-cyan-400" />
                  </div>
                  <span className="text-[10px] sm:text-xs font-medium text-white/40">RAM Usage</span>
                </div>
                <p className="text-lg sm:text-2xl font-bold text-white">{realtime.ram_percent?.toFixed(1) || '0'}%</p>
                <p className="text-[9px] sm:text-xs text-white/40 mt-1">
                  {((realtime.ram_used_mb || 0) / 1024).toFixed(1)} GB
                </p>
              </div>
            </GlassCard>

            <GlassCard gradient>
              <div className="p-3 sm:p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 rounded-lg bg-emerald-500/20">
                    <Activity className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-emerald-400" />
                  </div>
                  <span className="text-[10px] sm:text-xs font-medium text-white/40">Latency</span>
                </div>
                <p className="text-lg sm:text-2xl font-bold text-white">{realtime.latency_ms?.toFixed(0) || '0'}ms</p>
                <p className={`text-[9px] sm:text-xs mt-1 ${
                  (realtime.latency_ms || 0) < 100 ? 'text-emerald-400' : (realtime.latency_ms || 0) < 300 ? 'text-amber-400' : 'text-rose-400'
                }`}>
                  {(realtime.latency_ms || 0) < 100 ? 'Excelente' : (realtime.latency_ms || 0) < 300 ? 'Normal' : 'Alto'}
                </p>
              </div>
            </GlassCard>

            <GlassCard gradient>
              <div className="p-3 sm:p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 rounded-lg bg-amber-500/20">
                    <Zap className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-amber-400" />
                  </div>
                  <span className="text-[10px] sm:text-xs font-medium text-white/40">Trades/Min</span>
                </div>
                <p className="text-lg sm:text-2xl font-bold text-white">{realtime.tpm?.toFixed(1) || '0'}</p>
                <p className="text-[9px] sm:text-xs text-white/40 mt-1">
                  {realtime.positions_open || 0} posições abertas
                </p>
              </div>
            </GlassCard>
          </section>
        )}

        {/* PnL Chart - Expandable - Premium Theme */}
        {chartData.length > 0 && (
          <section>
            <GlassCard className={`transition-all duration-500 ${chartExpanded ? 'ring-2 ring-violet-500/30' : ''}`}>
              <div className="p-3 sm:p-6">
                <div className="flex items-center justify-between mb-3 sm:mb-6">
                  <div className="flex items-center gap-2 sm:gap-3">
                    <div className="p-1.5 sm:p-2.5 rounded-lg sm:rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-500/30">
                      <LineChart className="w-4 sm:w-5 h-4 sm:h-5 text-white" />
                    </div>
                    <div>
                      <h2 className="text-sm sm:text-lg font-semibold text-white">Evolucao do PnL</h2>
                      <p className="text-[10px] sm:text-xs text-white/40 hidden sm:block font-mono">Lucro/Prejuizo acumulado por trade</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setChartExpanded(!chartExpanded)}
                    className="text-white/50 hover:text-white hover:bg-white/10 rounded-lg sm:rounded-xl p-1.5 sm:p-2 border border-transparent hover:border-violet-500/30"
                  >
                    {chartExpanded ? (
                      <><Minimize2 className="w-3.5 sm:w-4 h-3.5 sm:h-4" /><span className="hidden sm:inline ml-2">Minimizar</span></>
                    ) : (
                      <><Maximize2 className="w-3.5 sm:w-4 h-3.5 sm:h-4" /><span className="hidden sm:inline ml-2">Expandir</span></>
                    )}
                  </Button>
                </div>

                <div className={`transition-all duration-500 ${chartExpanded ? 'h-[250px] sm:h-[400px]' : 'h-[150px] sm:h-[200px]'}`}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorPnlPositive" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorPnlNegative" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis
                        dataKey="name"
                        stroke="rgba(255,255,255,0.3)"
                        fontSize={9}
                        tickLine={false}
                        axisLine={false}
                        hide={!chartExpanded}
                      />
                      <YAxis
                        stroke="rgba(255,255,255,0.3)"
                        fontSize={9}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `$${value}`}
                        width={40}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeDasharray="3 3" />
                      <Area
                        type="monotone"
                        dataKey="cumulative"
                        stroke={totalPnl >= 0 ? "#10b981" : "#f43f5e"}
                        strokeWidth={2}
                        fill={totalPnl >= 0 ? "url(#colorPnlPositive)" : "url(#colorPnlNegative)"}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Trade markers - Responsivo */}
                {chartExpanded && (
                  <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-white/5">
                    <div className="flex flex-wrap gap-1.5 sm:gap-2">
                      {chartData.slice(-10).map((trade, idx) => (
                        <div
                          key={`trade-marker-${trade.symbol}-${trade.date}-${idx}`}
                          className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full text-[10px] sm:text-xs font-medium ${
                            trade.pnl >= 0
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          <span className="font-bold">{trade.symbol}</span>
                          <span>{trade.pnl >= 0 ? '+' : ''}{formatCurrency(trade.pnl)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </GlassCard>
          </section>
        )}

        {/* Market Insights - Moedas Monitoradas - RESPONSIVO */}
        <section>
          <GlassCard>
            <div className="p-3 sm:p-6">
              <button
                type="button"
                className="flex items-center justify-between cursor-pointer w-full text-left"
                onClick={() => setInsightsExpanded(!insightsExpanded)}
              >
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="p-1.5 sm:p-2.5 rounded-lg sm:rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 shadow-lg shadow-amber-500/30">
                    <Eye className="w-4 sm:w-5 h-4 sm:h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-sm sm:text-lg font-semibold text-white">Moedas Monitoradas</h2>
                    <p className="text-[10px] sm:text-xs text-white/40">
                      {monitoredCoins.length} ativos {monitoredCoinsData?.source === 'bot_selector' ? 'do bot' : 'padrão'}
                    </p>
                  </div>
                </div>
                <div className="text-white/40 hover:text-white hover:bg-white/5 rounded-lg sm:rounded-xl p-1.5 sm:p-2">
                  {insightsExpanded ? (
                    <ChevronUp className="w-4 sm:w-5 h-4 sm:h-5" />
                  ) : (
                    <ChevronDown className="w-4 sm:w-5 h-4 sm:h-5" />
                  )}
                </div>
              </button>

              {insightsExpanded ? (
                <div className="mt-4 sm:mt-6 space-y-3 sm:space-y-4">
                  {/* Grid de moedas - Responsivo com precos em tempo real DO BACKEND */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 sm:gap-3">
                    {monitoredCoins.map((coin) => {
                      // Verificar se temos posicao aberta nesta moeda
                      const hasPosition = positions.some(p => p.symbol?.includes(coin.symbol));
                      const position = positions.find(p => p.symbol?.includes(coin.symbol));

                      // Buscar preco em tempo real (DADOS REAIS da Binance)
                      const priceData = marketPrices?.prices?.[coin.full_symbol];
                      const price = priceData?.price;
                      const change24h = priceData?.change_24h;
                      const isPositive = change24h >= 0;

                      return (
                        <div
                          key={`coin-${coin.symbol}`}
                          className={`relative p-2.5 sm:p-4 rounded-xl sm:rounded-2xl border transition-all duration-300 ${
                            hasPosition
                              ? 'bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border-emerald-500/30'
                              : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.05] hover:border-violet-500/20'
                          }`}
                        >
                          {hasPosition ? (
                            <div className="absolute top-1.5 sm:top-2 right-1.5 sm:right-2">
                              <div className="w-1.5 sm:w-2 h-1.5 sm:h-2 rounded-full bg-emerald-400 animate-pulse" />
                            </div>
                          ) : null}
                          <div className="flex items-center gap-1.5 sm:gap-2 mb-1 sm:mb-2">
                            <div
                              className="w-6 sm:w-8 h-6 sm:h-8 rounded-md sm:rounded-lg flex items-center justify-center text-[9px] sm:text-xs font-bold"
                              style={{ backgroundColor: coin.color + '20', color: coin.color }}
                            >
                              {coin.symbol.slice(0, 2)}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-xs sm:text-sm font-semibold text-white truncate">{coin.symbol}</p>
                              <p className="text-[8px] sm:text-[10px] text-white/40 truncate">{coin.name}</p>
                            </div>
                          </div>

                          {/* Preco em tempo real */}
                          {price !== undefined ? (
                            <div className="mb-1 sm:mb-2">
                              <p className="text-xs sm:text-sm font-bold text-white">
                                ${price >= 1000 ? price.toFixed(0) : price >= 1 ? price.toFixed(2) : price.toFixed(4)}
                              </p>
                              <div className={`flex items-center gap-0.5 ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {isPositive ? <ArrowUpRight className="w-2.5 h-2.5" /> : <ArrowDownRight className="w-2.5 h-2.5" />}
                                <span className="text-[9px] sm:text-[10px] font-medium">
                                  {isPositive ? '+' : ''}{change24h?.toFixed(2)}%
                                </span>
                              </div>
                            </div>
                          ) : (
                            <p className="text-[9px] sm:text-[10px] text-white/30 leading-relaxed hidden sm:block line-clamp-2">{coin.description}</p>
                          )}

                          {hasPosition && position ? (
                            <div className="mt-1.5 sm:mt-2 pt-1.5 sm:pt-2 border-t border-emerald-500/20">
                              <p className="text-[9px] sm:text-[10px] text-emerald-400 truncate">
                                {position.side} @ ${position.entry_price?.toFixed(2)}
                              </p>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>

                  {/* Links uteis - Responsivo, oculto em mobile - CORRIGIDOS PARA TESTNET/MAINNET */}
                  <div className="hidden sm:flex items-center justify-center gap-4 pt-4 border-t border-white/5">
                    <a
                      href={status?.testnet_mode ? "https://testnet.binance.vision/" : "https://www.binance.com/en/markets"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-xs text-white/40 hover:text-white transition-colors"
                      title={status?.testnet_mode ? "Binance Testnet" : "Binance Markets"}
                    >
                      <Globe className="w-3.5 h-3.5" />
                      {status?.testnet_mode ? 'Testnet' : 'Binance Markets'}
                      <ExternalLink className="w-3 h-3" />
                    </a>
                    <span className="text-white/20">|</span>
                    <a
                      href="https://www.coingecko.com/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-xs text-white/40 hover:text-white transition-colors"
                    >
                      <Newspaper className="w-3.5 h-3.5" />
                      CoinGecko
                      <ExternalLink className="w-3 h-3" />
                    </a>
                    <span className="text-white/20">|</span>
                    <a
                      href="https://cryptopanic.com/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-xs text-white/40 hover:text-white transition-colors"
                    >
                      <Bitcoin className="w-3.5 h-3.5" />
                      Crypto News
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              ) : null}
            </div>
          </GlassCard>
        </section>

        {/* Sinais Ativos + Regime de Mercado + Status ML */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4">
          {/* Sinais Ativos */}
          <GlassCard>
            <div className="p-3 sm:p-5">
              <button
                type="button"
                className="flex items-center justify-between cursor-pointer w-full text-left mb-3"
                onClick={() => setSignalsExpanded(!signalsExpanded)}
              >
                <div className="flex items-center gap-2">
                  <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-500/30">
                    <Signal className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xs sm:text-sm font-semibold text-white">Sinais Ativos</h3>
                    <p className="text-[9px] sm:text-[10px] text-white/40">{activeSignals?.count || 0} oportunidades</p>
                  </div>
                </div>
                {signalsExpanded ? (
                  <ChevronUp className="w-4 h-4 text-white/40" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/40" />
                )}
              </button>

              {signalsExpanded ? (
                activeSignals?.signals?.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {activeSignals.signals.slice(0, 5).map((signal, idx) => (
                      <div
                        key={`signal-${signal.symbol}-${idx}`}
                        className={`flex items-center justify-between p-2 rounded-lg border ${
                          signal.signal === 'BUY'
                            ? 'bg-emerald-500/5 border-emerald-500/20'
                            : 'bg-rose-500/5 border-rose-500/20'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`text-xs font-bold ${signal.signal === 'BUY' ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {signal.signal}
                          </span>
                          <span className="text-xs text-white font-medium">{signal.symbol?.replace('USDT', '')}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-white/40">Score</span>
                          <span className={`text-xs font-bold ${
                            signal.score >= 70 ? 'text-emerald-400' :
                            signal.score >= 50 ? 'text-amber-400' : 'text-white/40'
                          }`}>
                            {signal.score}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-white/40 text-center py-4">Nenhum sinal forte no momento</p>
                )
              ) : null}
            </div>
          </GlassCard>

          {/* Regime de Mercado */}
          <GlassCard>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className={`p-1.5 sm:p-2 rounded-lg ${
                  marketRegime?.regime === 'trending' ? 'bg-emerald-500/20' :
                  marketRegime?.regime === 'volatile' ? 'bg-amber-500/20' :
                  marketRegime?.regime === 'ranging' ? 'bg-rose-500/20' :
                  'bg-white/10'
                }`}>
                  <Radio className={`w-3.5 sm:w-4 h-3.5 sm:h-4 ${
                    marketRegime?.regime === 'trending' ? 'text-emerald-400' :
                    marketRegime?.regime === 'volatile' ? 'text-amber-400' :
                    marketRegime?.regime === 'ranging' ? 'text-rose-400' :
                    'text-white/40'
                  }`} />
                </div>
                <div>
                  <h3 className="text-xs sm:text-sm font-semibold text-white">Regime de Mercado</h3>
                  <p className="text-[9px] sm:text-[10px] text-white/40">Analise do BTC</p>
                </div>
              </div>

              <div className={`text-lg sm:text-xl font-bold capitalize mb-2 ${
                marketRegime?.regime === 'trending' ? 'text-emerald-400' :
                marketRegime?.regime === 'volatile' ? 'text-amber-400' :
                marketRegime?.regime === 'ranging' ? 'text-rose-400' :
                'text-white/40'
              }`}>
                {marketRegime?.regime || 'Analisando...'}
              </div>

              <p className="text-[10px] sm:text-xs text-white/40 mb-3">
                {marketRegime?.description || 'Carregando dados...'}
              </p>

              <div className="flex items-center gap-3 text-[10px] sm:text-xs">
                <div>
                  <span className="text-white/40">ADX:</span>
                  <span className="text-white ml-1 font-medium">{marketRegime?.adx || '-'}</span>
                </div>
                <div>
                  <span className="text-white/40">Volatilidade:</span>
                  <span className="text-white ml-1 font-medium">{marketRegime?.volatility_ratio || '-'}x</span>
                </div>
              </div>
            </div>
          </GlassCard>

          {/* Status do ML */}
          <GlassCard>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 sm:p-2 rounded-lg bg-gradient-to-br from-violet-500 to-purple-500 shadow-lg shadow-violet-500/30">
                  <Brain className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-white" />
                </div>
                <div>
                  <h3 className="text-xs sm:text-sm font-semibold text-white">Machine Learning</h3>
                  <p className="text-[9px] sm:text-[10px] text-white/40">Sistema de aprendizado</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] sm:text-xs text-white/40">Trades Analisados</span>
                    <span className="text-xs sm:text-sm font-bold text-white">
                      {mlStatus?.statistics?.total_analyzed_trades || 0}/50
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 transition-all duration-500"
                      style={{ width: `${Math.min((mlStatus?.statistics?.total_analyzed_trades || 0) / 50 * 100, 100)}%` }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-[10px] sm:text-xs text-white/40">Status</span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    (mlStatus?.statistics?.total_analyzed_trades || 0) >= 50
                      ? 'bg-emerald-500/10 text-emerald-400'
                      : 'bg-amber-500/10 text-amber-400'
                  }`}>
                    {(mlStatus?.statistics?.total_analyzed_trades || 0) >= 50 ? 'Otimizando' : 'Coletando dados'}
                  </span>
                </div>

                {mlStatus?.statistics?.win_rate !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] sm:text-xs text-white/40">Win Rate</span>
                    <span className={`text-xs font-bold ${mlStatus.statistics.win_rate >= 50 ? 'text-emerald-400' : 'text-amber-400'}`}>
                      {mlStatus.statistics.win_rate?.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </GlassCard>
        </section>

        {/* Metricas Avancadas - RESPONSIVO */}
        <section className="grid grid-cols-2 gap-3 sm:gap-4">
          <GlassCard>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <Calculator className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-white/40" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Profit Factor</span>
              </div>
              <p className={`text-lg sm:text-2xl font-bold ${(performance?.profit_factor || 0) >= 1 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {(performance?.profit_factor || 0).toFixed(2)}
              </p>
              <p className="text-[9px] sm:text-xs text-white/40 mt-1 hidden sm:block">
                {(performance?.profit_factor || 0) >= 1.5 ? 'Excelente' : (performance?.profit_factor || 0) >= 1 ? 'Positivo' : 'Negativo'}
              </p>
            </div>
          </GlassCard>

          <GlassCard>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <LineChart className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-white/40" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Expectancy</span>
              </div>
              <p className={`text-lg sm:text-2xl font-bold ${(performance?.expectancy || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {formatCurrency(performance?.expectancy || 0)}
              </p>
              <p className="text-[9px] sm:text-xs text-white/40 mt-1 hidden sm:block">Esperado por trade</p>
            </div>
          </GlassCard>

          <GlassCard>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <AlertTriangle className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-white/40" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Max Drawdown</span>
              </div>
              <p className="text-lg sm:text-2xl font-bold text-amber-400">
                {formatCurrency(performance?.max_drawdown || 0)}
              </p>
              <p className="text-[9px] sm:text-xs text-white/40 mt-1 hidden sm:block">Maior perda sequencial</p>
            </div>
          </GlassCard>

          <GlassCard>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <Flame className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-white/40" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Streak</span>
              </div>
              <p className={`text-lg sm:text-2xl font-bold ${performance?.streak_type === 'win' ? 'text-emerald-400' : performance?.streak_type === 'loss' ? 'text-rose-400' : 'text-white/40'}`}>
                {performance?.current_streak || 0}
              </p>
              <p className="text-[9px] sm:text-xs text-white/40 mt-1 hidden sm:block">
                {performance?.streak_type === 'win' ? 'Vitorias' : performance?.streak_type === 'loss' ? 'Derrotas' : 'Sem trades'}
              </p>
            </div>
          </GlassCard>
        </section>

        {/* Performance Cards - RESPONSIVO */}
        <section className="grid grid-cols-2 gap-3 sm:gap-4">
          <GlassCard gradient>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <Award className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-emerald-400" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Melhor Trade</span>
              </div>
              <p className="text-base sm:text-xl font-bold text-emerald-400 truncate">
                +{formatCurrency(performance?.best_trade || 0)}
              </p>
            </div>
          </GlassCard>

          <GlassCard gradient>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <TrendingDown className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-rose-400" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Pior Trade</span>
              </div>
              <p className="text-base sm:text-xl font-bold text-rose-400 truncate">
                {formatCurrency(performance?.worst_trade || 0)}
              </p>
            </div>
          </GlassCard>

          <GlassCard gradient>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <DollarSign className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-emerald-400" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Media Ganho</span>
              </div>
              <p className="text-base sm:text-xl font-bold text-emerald-400 truncate">
                +{formatCurrency(performance?.avg_win || 0)}
              </p>
            </div>
          </GlassCard>

          <GlassCard gradient>
            <div className="p-3 sm:p-5">
              <div className="flex items-center gap-1.5 sm:gap-2 mb-2 sm:mb-3">
                <Shield className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-rose-400" />
                <span className="text-[9px] sm:text-xs font-medium text-white/40 uppercase tracking-wider truncate">Media Perda</span>
              </div>
              <p className="text-base sm:text-xl font-bold text-rose-400 truncate">
                -{formatCurrency(performance?.avg_loss || 0)}
              </p>
            </div>
          </GlassCard>
        </section>

        {/* Posicoes Ativas & Total Trades - RESPONSIVO */}
        <section className="grid grid-cols-1 gap-3 sm:gap-6">
          <GlassCard gradient>
            <div className="p-3 sm:p-6">
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="p-1.5 sm:p-2.5 rounded-lg sm:rounded-xl bg-violet-500/10">
                    <Activity className="w-4 sm:w-5 h-4 sm:h-5 text-violet-400" />
                  </div>
                  <span className="text-xs sm:text-sm font-medium text-white/50">Posicoes Ativas</span>
                </div>
                <span className="text-xl sm:text-2xl font-bold text-white">
                  {positions.length}<span className="text-white/30 text-base sm:text-lg font-normal">/{status?.max_positions || 3}</span>
                </span>
              </div>
              <div className="w-full h-1.5 sm:h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-violet-500 to-cyan-500 transition-all duration-500"
                  style={{ width: `${(positions.length / (status?.max_positions || 3)) * 100}%` }}
                />
              </div>
            </div>
          </GlassCard>

          <GlassCard gradient>
            <div className="p-3 sm:p-6">
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="p-1.5 sm:p-2.5 rounded-lg sm:rounded-xl bg-cyan-500/10">
                    <BarChart3 className="w-4 sm:w-5 h-4 sm:h-5 text-cyan-400" />
                  </div>
                  <span className="text-xs sm:text-sm font-medium text-white/50">Total Trades</span>
                </div>
                <span className="text-xl sm:text-2xl font-bold text-white">{totalTrades}</span>
              </div>
              <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm">
                <span className="text-emerald-400">
                  <span className="font-semibold">{performance?.winning_trades || 0}</span> wins
                </span>
                <span className="text-white/20 hidden sm:inline">|</span>
                <span className="text-rose-400">
                  <span className="font-semibold">{performance?.losing_trades || 0}</span> losses
                </span>
                <span className="text-white/20 hidden sm:inline">|</span>
                <span className="text-white/40 hidden sm:inline">
                  Media: <span className="font-semibold">{formatCurrency(performance?.average_pnl || 0)}</span>
                </span>
              </div>
            </div>
          </GlassCard>
        </section>

        {/* Posicoes Abertas - RESPONSIVO */}
        {positions.length > 0 && (
          <section>
            <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-6">
              <div className="p-1.5 sm:p-2 rounded-lg sm:rounded-xl bg-white/5">
                <Zap className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-amber-400" />
              </div>
              <h2 className="text-sm sm:text-lg font-semibold text-white">Posicoes Abertas</h2>
            </div>

            <div className="space-y-3 sm:space-y-4">
              {positions.map((pos, idx) => {
                const pnlEstimado = pos.unrealized_pnl || 0;
                const isPosPositive = pnlEstimado >= 0;
                const pnlPercent = pos.entry_price ? ((pos.current_price || pos.entry_price) - pos.entry_price) / pos.entry_price * 100 : 0;

                return (
                  <GlassCard key={`position-${pos.symbol}-${pos.opened_at || idx}`}>
                    <div className="p-3 sm:p-5">
                      <div className="flex items-center justify-between mb-3 sm:mb-4">
                        <div className="flex items-center gap-2 sm:gap-4">
                          <div className={`w-9 sm:w-12 h-9 sm:h-12 rounded-xl sm:rounded-2xl flex items-center justify-center font-bold text-sm sm:text-lg ${
                            isPosPositive
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : 'bg-rose-500/10 text-rose-400'
                          }`}>
                            {pos.symbol?.replace('USDT', '').slice(0, 3)}
                          </div>
                          <div>
                            <p className="font-semibold text-white text-sm sm:text-lg">{pos.symbol?.replace('USDT', '')}</p>
                            <div className="flex items-center gap-1.5 sm:gap-2 mt-0.5">
                              <span className={`text-[10px] sm:text-xs font-medium px-1.5 sm:px-2 py-0.5 rounded-full ${
                                pos.side === 'BUY'
                                  ? 'bg-emerald-500/10 text-emerald-400'
                                  : 'bg-rose-500/10 text-rose-400'
                              }`}>
                                {pos.side === 'BUY' ? 'LONG' : 'SHORT'}
                              </span>
                              <span className="text-[10px] sm:text-xs text-white/40 hidden sm:inline">
                                @ {formatCurrency(pos.entry_price, { digits: 4 })}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="text-right">
                          <p className={`text-base sm:text-xl font-bold ${isPosPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {isPosPositive ? '+' : ''}{formatCurrency(pnlEstimado)}
                          </p>
                          <p className={`text-xs sm:text-sm ${isPosPositive ? 'text-emerald-400/60' : 'text-rose-400/60'}`}>
                            {isPosPositive ? '+' : ''}{pnlPercent.toFixed(2)}%
                          </p>
                        </div>
                      </div>

                      {/* Barra de progresso com gradiente */}
                      <div className="relative h-1.5 sm:h-2 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className={`absolute left-0 top-0 h-full rounded-full transition-all duration-500 ${
                            isPosPositive
                              ? 'bg-gradient-to-r from-emerald-500 to-emerald-400'
                              : 'bg-gradient-to-r from-rose-500 to-rose-400'
                          }`}
                          style={{ width: `${Math.min(Math.abs(pnlPercent) * 5, 100)}%` }}
                        />
                      </div>

                      {/* SL & TP - Responsivo */}
                      <div className="flex items-center justify-between mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-white/5">
                        <div className="flex items-center gap-1.5 sm:gap-2">
                          <span className="text-[10px] sm:text-xs text-white/40">SL</span>
                          <span className="text-xs sm:text-sm font-medium text-rose-400">
                            {formatCurrency(pos.stop_loss, { digits: 2 })}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 sm:gap-2">
                          <span className="text-[10px] sm:text-xs text-white/40">TP</span>
                          <span className="text-xs sm:text-sm font-medium text-emerald-400">
                            {formatCurrency(pos.take_profit, { digits: 2 })}
                          </span>
                        </div>
                      </div>
                    </div>
                  </GlassCard>
                );
              })}
            </div>
          </section>
        )}

        {/* Performance Summary - RESPONSIVO */}
        {(performance?.winning_trades > 0 || performance?.losing_trades > 0) && (
          <section>
            <div className="flex items-center gap-2 sm:gap-3 mb-3 sm:mb-6">
              <div className="p-1.5 sm:p-2 rounded-lg sm:rounded-xl bg-white/5">
                <BarChart3 className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-cyan-400" />
              </div>
              <h2 className="text-sm sm:text-lg font-semibold text-white">Resumo de Performance</h2>
            </div>

            <GlassCard>
              <div className="p-3 sm:p-6">
                <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-6">
                  {/* Win/Loss Bar */}
                  <div className="flex-1 w-full">
                    <div className="flex h-3 sm:h-4 rounded-full overflow-hidden bg-white/10">
                      <div
                        className="bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-700"
                        style={{ width: `${winRate}%` }}
                      />
                      <div
                        className="bg-gradient-to-r from-rose-500 to-rose-400 transition-all duration-700"
                        style={{ width: `${100 - winRate}%` }}
                      />
                    </div>
                    <div className="flex justify-between mt-2 sm:mt-3">
                      <span className="text-xs sm:text-sm text-white/40">
                        <span className="text-emerald-400 font-semibold">{performance?.winning_trades || 0}</span> wins
                      </span>
                      <span className="text-xs sm:text-sm text-white/40">
                        <span className="text-rose-400 font-semibold">{performance?.losing_trades || 0}</span> losses
                      </span>
                    </div>
                  </div>

                  {/* Win Rate Circle - Menor em mobile */}
                  <div className="relative w-16 h-16 sm:w-24 sm:h-24">
                    <svg className="w-16 h-16 sm:w-24 sm:h-24 transform -rotate-90">
                      <circle
                        cx="50%"
                        cy="50%"
                        r="35%"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        className="text-white/10"
                      />
                      <circle
                        cx="50%"
                        cy="50%"
                        r="35%"
                        stroke="url(#gradientCircle)"
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={`${winRate * 2.2} 220`}
                        strokeLinecap="round"
                        className="transition-all duration-700"
                      />
                      <defs>
                        <linearGradient id="gradientCircle" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#8b5cf6" />
                          <stop offset="100%" stopColor="#22d3ee" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-sm sm:text-xl font-bold text-white">{winRate.toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </GlassCard>
          </section>
        )}

        {/* Footer - Responsivo */}
        <footer className="pt-4 sm:pt-8 pb-4 border-t border-white/5">
          <div className="flex items-center justify-center gap-1.5 sm:gap-2 text-[10px] sm:text-xs text-white/30">
            <Clock className="w-3 sm:w-3.5 h-3 sm:h-3.5" />
            <span>Atualizado: {formatDateTime(new Date())}</span>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default Dashboard;
