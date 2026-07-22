import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import { formatDateTime, formatPercent } from "@/lib/formatters";
import { notify } from "@/lib/notify";
import {
  Activity,
  AlertTriangle,
  Award,
  Brain,
  CheckCircle2,
  Clock,
  RefreshCw,
  Shield,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useQuery } from "react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Glassmorphism Card Component
const GlassCard = ({
  children,
  className = "",
  gradient = false,
  glow = "",
}) => (
  <div
    className={`
    relative overflow-hidden rounded-2xl sm:rounded-3xl
    bg-white/5 backdrop-blur-xl
    border border-white/10
    hover:bg-white/10 hover:border-violet-500/30 hover:shadow-lg hover:shadow-violet-500/10
    transition-all duration-500 ease-out
    ${gradient ? "before:absolute before:inset-0 before:bg-gradient-to-br before:from-violet-500/5 before:via-transparent before:to-cyan-500/5 before:pointer-events-none" : ""}
    ${glow ? `shadow-lg shadow-${glow}-500/20` : ""}
    ${className}
  `}
  >
    {children}
  </div>
);

// Stat Card para métricas-chave
const StatCard = ({ label, value, icon: Icon, color, trend, subtext }) => (
  <GlassCard gradient glow="violet">
    <div className="p-4 sm:p-6 relative">
      <div
        className={`absolute -top-12 -right-12 w-32 h-32 rounded-full blur-3xl opacity-20 ${color}`}
      />

      <div className="flex items-start justify-between mb-4">
        <div className={`p-3 rounded-2xl bg-gradient-to-br ${color} shadow-lg`}>
          <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
        </div>
        {trend !== null && trend !== undefined && (
          <Badge
            variant="secondary"
            className={`${trend > 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-rose-500/20 text-rose-400"} border-0 text-xs`}
          >
            {trend > 0 ? "+" : ""}
            {trend}%
          </Badge>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-xs sm:text-sm text-white/60 font-medium">{label}</p>
        <p className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          {value}
        </p>
        {subtext && <p className="text-xs text-white/50 mt-1">{subtext}</p>}
      </div>
    </div>
  </GlassCard>
);

// Skeleton Loading
const ReflectionsSkeleton = () => (
  <div className="min-h-screen p-3 sm:p-6">
    <div className="max-w-7xl mx-auto space-y-4 sm:space-y-8">
      <Skeleton className="h-10 w-48 bg-violet-500/10" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton
            key={i}
            className="h-36 rounded-3xl bg-white/5 border border-white/10"
          />
        ))}
      </div>
      <Skeleton className="h-80 rounded-3xl bg-white/5 border border-white/10" />
      <Skeleton className="h-96 rounded-3xl bg-white/5 border border-white/10" />
    </div>
  </div>
);

const Reflections = () => {
  const [isTriggering, setIsTriggering] = useState(false);

  // Query: Status do serviço de reflexão
  const {
    data: status,
    isLoading: statusLoading,
    refetch: refetchStatus,
  } = useQuery(
    "reflection-status",
    async () => {
      const response = await apiClient.get("/reflection/status");
      return response.data;
    },
    {
      refetchInterval: 30_000, // Poll a cada 30s
      staleTime: 20_000,
    },
  );

  // Query: Histórico de reflexões
  const { data: history, isLoading: historyLoading } = useQuery(
    "reflection-history",
    async () => {
      const response = await apiClient.get("/reflection/history");
      return response.data;
    },
    {
      refetchInterval: 60_000, // Poll a cada 1min
      staleTime: 45_000,
    },
  );

  // Trigger manual de reflexão
  const handleTriggerReflection = async () => {
    setIsTriggering(true);
    try {
      await apiClient.post("/reflection/trigger");
      notify.success("Reflexão iniciada manualmente");
      setTimeout(() => refetchStatus(), 2000);
    } catch (error) {
      notify.error(
        "Erro ao iniciar reflexão: " +
          (error.response?.data?.detail || error.message),
      );
    } finally {
      setIsTriggering(false);
    }
  };

  // Processar dados para gráfico de win rate
  const winRateChartData = useMemo(() => {
    if (!history?.learnings) return [];
    return history.learnings
      .filter((l) => l.win_rate !== undefined)
      .map((l) => ({
        timestamp: new Date(l.timestamp).getTime(),
        date: formatDateTime(l.timestamp).split(" ")[0],
        winRate: (l.win_rate * 100).toFixed(1),
      }))
      .reverse()
      .slice(-20); // Últimas 20 reflexões
  }, [history]);

  if (statusLoading || historyLoading) {
    return <ReflectionsSkeleton />;
  }

  const lastReflection = history?.learnings?.[0];
  const avgWinRate =
    history?.learnings?.length > 0
      ? history.learnings.reduce((sum, l) => sum + (l.win_rate || 0), 0) /
        history.learnings.length
      : 0;

  return (
    <div className="min-h-screen p-3 sm:p-6 pb-20">
      <div className="max-w-7xl mx-auto space-y-4 sm:space-y-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/30">
              <Brain className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white">
                Auto-Reflexão
              </h1>
              <p className="text-sm text-white/60 mt-1">
                Sistema de aprendizado contínuo
              </p>
            </div>
          </div>

          <Button
            onClick={handleTriggerReflection}
            disabled={isTriggering}
            className="bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white border-0 shadow-lg shadow-violet-500/30 rounded-2xl px-6"
          >
            {isTriggering ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Analisando...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Refletir Agora
              </>
            )}
          </Button>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Reflexões"
            value={status?.total_reflections || 0}
            icon={Activity}
            color="from-violet-500 to-purple-600"
            subtext={`${status?.reflection_count || 0} ciclos completos`}
          />
          <StatCard
            label="Win Rate Médio"
            value={formatPercent(avgWinRate)}
            icon={Target}
            color="from-cyan-500 to-blue-600"
            trend={history?.learnings?.length > 0 ? (lastReflection?.win_rate > avgWinRate ? 5 : -2) : undefined}
            subtext="Últimas 20 reflexões"
          />
          <StatCard
            label="Última Reflexão"
            value={
              lastReflection
                ? formatDateTime(lastReflection.timestamp).split(" ")[1]
                : "--:--"
            }
            icon={Clock}
            color="from-emerald-500 to-teal-600"
            subtext={
              lastReflection
                ? formatDateTime(lastReflection.timestamp).split(" ")[0]
                : "Nenhuma ainda"
            }
          />
          <StatCard
            label="Status"
            value={status?.is_running ? "Ativo" : "Parado"}
            icon={status?.is_running ? CheckCircle2 : XCircle}
            color={
              status?.is_running
                ? "from-emerald-500 to-green-600"
                : "from-gray-500 to-slate-600"
            }
            subtext={`Próxima em ${status?.next_reflection_in || "--"}`}
          />
        </div>

        {/* Win Rate Chart */}
        <GlassCard gradient glow="violet">
          <div className="p-4 sm:p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 shadow-lg">
                  <TrendingUp className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    Evolução Win Rate
                  </h3>
                  <p className="text-xs text-white/60">Últimas 20 reflexões</p>
                </div>
              </div>
            </div>

            {winRateChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={winRateChartData}>
                  <defs>
                    <linearGradient
                      id="winRateGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="rgb(139, 92, 246)"
                        stopOpacity={0.4}
                      />
                      <stop
                        offset="100%"
                        stopColor="rgb(139, 92, 246)"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.05)"
                  />
                  <XAxis
                    dataKey="date"
                    stroke="rgba(255,255,255,0.3)"
                    fontSize={11}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="rgba(255,255,255,0.3)"
                    fontSize={11}
                    tickLine={false}
                    domain={[0, 100]}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(0,0,0,0.9)",
                      border: "1px solid rgba(139, 92, 246, 0.3)",
                      borderRadius: "12px",
                      color: "#fff",
                    }}
                    formatter={(value) => [`${value}%`, "Win Rate"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="winRate"
                    stroke="rgb(139, 92, 246)"
                    strokeWidth={2}
                    fill="url(#winRateGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-64 flex items-center justify-center text-white/50">
                <div className="text-center">
                  <Sparkles className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Nenhum dado de reflexão ainda</p>
                </div>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Histórico de Aprendizados */}
        <GlassCard gradient>
          <div className="p-4 sm:p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg">
                <Award className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Aprendizados Recentes
                </h3>
                <p className="text-xs text-white/60">
                  Insights do sistema de reflexão
                </p>
              </div>
            </div>

            <div className="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar">
              {history?.learnings && history.learnings.length > 0 ? (
                history.learnings.slice(0, 15).map((learning, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-violet-500/30 transition-all duration-300"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge
                            variant="secondary"
                            className={`${
                              learning.win_rate >= 0.5
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-rose-500/20 text-rose-400"
                            } border-0 text-xs`}
                          >
                            {learning.win_rate >= 0.5 ? (
                              <TrendingUp className="w-3 h-3 mr-1" />
                            ) : (
                              <TrendingDown className="w-3 h-3 mr-1" />
                            )}
                            {formatPercent(learning.win_rate)} Win Rate
                          </Badge>
                          <Badge
                            variant="secondary"
                            className="bg-white/5 text-white/70 border-0 text-xs"
                          >
                            <Clock className="w-3 h-3 mr-1" />
                            {formatDateTime(learning.timestamp)}
                          </Badge>
                        </div>

                        {learning.problems && learning.problems.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-xs text-white/50 font-medium flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" />
                              Problemas Detectados:
                            </p>
                            {learning.problems.map((problem, i) => (
                              <p key={i} className="text-sm text-white/80 pl-4">
                                • {problem}
                              </p>
                            ))}
                          </div>
                        )}

                        {learning.action && (
                          <div className="space-y-1">
                            <p className="text-xs text-white/50 font-medium flex items-center gap-1">
                              <Shield className="w-3 h-3" />
                              Ação Tomada:
                            </p>
                            <p className="text-sm text-emerald-400 pl-4">
                              {learning.action}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="h-32 flex items-center justify-center text-white/50">
                  <div className="text-center">
                    <Brain className="w-10 h-10 mx-auto mb-2 opacity-30" />
                    <p>Nenhum aprendizado registrado ainda</p>
                    <p className="text-xs mt-1">
                      O bot começará a refletir após realizar trades
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

export default Reflections;
