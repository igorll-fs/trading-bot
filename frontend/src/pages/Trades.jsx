import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { useBotTrades } from '@/hooks/useBotQueries';
import { notify } from '@/lib/notify';
import { Skeleton } from '@/components/ui/skeleton';
import { formatCurrency, formatPercent, formatDateTime } from '@/lib/formatters';
import { FixedSizeList as List } from 'react-window';
import { useCallback, useMemo } from 'react';

const Trades = () => {
  const tradesQuery = useBotTrades({
    onError: (error) => {
      if (error?.isNetworkError) {
  notify.error('Servidor inacessível ao carregar trades.');
      } else {
  notify.error('Erro ao carregar histórico de trades: ' + (error.message || 'desconhecido'));
      }
    },
  });

  const trades = useMemo(() => tradesQuery.data ?? [], [tradesQuery.data]);
  const loading = tradesQuery.isLoading;

  // Shared grid template keeps header columns aligned with virtualized rows.
  const gridTemplate = 'minmax(160px, 1.5fr) minmax(110px, 1fr) minmax(80px, 0.7fr) repeat(4, minmax(110px, 1fr)) minmax(150px, 1.1fr) minmax(120px, 1fr) minmax(90px, 0.8fr) minmax(170px, 1.2fr)';

  const getRowKey = useCallback((trade, index) => (
    trade?.trade_id || trade?.id || `${trade?.symbol ?? 'trade'}-${trade?.opened_at ?? ''}-${trade?.closed_at ?? ''}-${index}`
  ), []);

  const rowRenderer = useCallback(({ index, style }) => {
    const trade = trades[index];
    if (!trade) return null;

    const isProfit = (trade.pnl || 0) > 0;
    const closeReason = trade.close_reason ? trade.close_reason.replace(/_/g, ' ') : '-';

    const entryPrice = formatCurrency(trade.entry_price, { digits: 4 });
    const exitPrice = trade.exit_price ? formatCurrency(trade.exit_price, { digits: 4 }) : '-';
    const stopLoss = trade.stop_loss ? formatCurrency(trade.stop_loss, { digits: 4 }) : '-';
    const takeProfit = trade.take_profit ? formatCurrency(trade.take_profit, { digits: 4 }) : '-';
    const positionSize = formatCurrency(trade.position_size, { digits: 2 });
    const pnlAmount = formatCurrency(Math.abs(trade.pnl || 0));
    const roePercent = formatPercent(trade.roe, { digits: 2, showPlus: true, fallback: '0.00%' });
    const closedAt = trade.closed_at ? formatDateTime(trade.closed_at) : '-';

    return (
      <div
        data-testid={`trade-row-${index}`}
        style={{
          ...style,
          display: 'grid',
          gridTemplateColumns: gridTemplate,
          alignItems: 'center',
          padding: '0.75rem 0.5rem',
        }}
        className={`border-b border-white/5 transition-all duration-200 hover:bg-white/5 ${index % 2 === 0 ? 'bg-white/[0.02]' : 'bg-transparent'}`}
      >
        <div className="text-sm text-white/60">{closedAt}</div>
        <div className="font-medium text-white">{trade.symbol}</div>
        <div>
          <Badge
            variant="outline"
            className={`${
              trade.side === 'BUY'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
            }`}
          >
            {trade.side === 'BUY' ? 'LONG' : 'SHORT'}
          </Badge>
        </div>
        <div className="text-white/80">{entryPrice}</div>
        <div className="text-white/80">{exitPrice}</div>
        <div className="text-rose-400/80">{stopLoss}</div>
        <div className="text-emerald-400/80">{takeProfit}</div>
        <div className="text-white/60">{positionSize}</div>
        <div>
          <div
            className={`flex items-center gap-1 font-medium ${
              isProfit ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {isProfit ? <TrendingUp size={16} aria-hidden="true" /> : <TrendingDown size={16} aria-hidden="true" />}
            {isProfit ? '+' : '-'}{pnlAmount}
          </div>
        </div>
        <div>
          <span className={`font-medium ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
            {roePercent}
          </span>
        </div>
        <div className="text-sm capitalize text-white/40">
          {closeReason}
        </div>
      </div>
    );
  }, [gridTemplate, trades]);

  const listHeight = useMemo(() => {
    if (trades.length === 0) return 0;
    const rowHeight = 64;
    return Math.min(rowHeight * trades.length, 480);
  }, [trades.length]);

  const itemKey = useCallback((index) => getRowKey(trades[index], index), [getRowKey, trades]);

  const showSkeleton = loading && trades.length === 0;

  return (
    <div className="p-4 sm:p-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold gradient-text">Histórico de Trades</h1>
        <p className="text-white/50 mt-1">{trades.length} trades registrados</p>
      </div>

      <Card className="glass-card hover:shadow-glow-violet transition-all duration-300">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-500/30">
              <Activity size={18} className="text-white" />
            </div>
            <span className="text-white">Todos os Trades</span>
          </CardTitle>
          <CardDescription className="text-white/50">Histórico completo de operações</CardDescription>
        </CardHeader>
        <CardContent>
          {showSkeleton ? (
            <div className="space-y-3">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-56" />
              <div className="space-y-2">
                {[...Array(6)].map((_, idx) => (
                  <Skeleton key={idx} className="h-12 w-full" />
                ))}
              </div>
            </div>
          ) : trades.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20 flex items-center justify-center">
                <Activity className="w-8 h-8 text-violet-400" aria-hidden="true" />
              </div>
              <p className="text-white/60 font-medium">Nenhum trade realizado ainda</p>
              <p className="text-sm text-white/40 mt-2">Os trades aparecerão aqui quando o bot começar a operar</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <div className="min-w-[1100px]">
                <div
                  className="grid gap-2 border-b border-white/10 bg-white/5 backdrop-blur-sm px-2 py-3 text-xs font-semibold uppercase tracking-wider text-white/60 sticky top-0 z-10"
                  style={{ gridTemplateColumns: gridTemplate }}
                >
                  <span>Data/Hora</span>
                  <span>Símbolo</span>
                  <span>Tipo</span>
                  <span>Entrada</span>
                  <span>Saída</span>
                  <span>Stop Loss</span>
                  <span>Take Profit</span>
                  <span>Tamanho (USDT)</span>
                  <span>PnL</span>
                  <span>ROE</span>
                  <span>Motivo</span>
                </div>
                <List
                  height={listHeight || 320}
                  itemCount={trades.length}
                  itemSize={64}
                  width="100%"
                  overscanCount={6}
                  className="!overflow-x-hidden"
                  itemKey={itemKey}
                >
                  {rowRenderer}
                </List>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Trades;