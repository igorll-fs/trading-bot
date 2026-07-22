/**
 * usePerformance - Hook para dados de performance do bot
 * 
 * Criado por: SessionA (Backend)
 * Para: SessionB (Frontend) integrar nos GlassCards
 * 
 * Endpoints utilizados:
 * - GET /api/sparkline - Mini-chart de PnL
 * - GET /api/realtime - Stats em tempo real
 */

import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

/**
 * Hook para obter sparkline de PnL (mini-chart)
 * @param {number} points - Número de pontos (default: 50)
 * @param {number} refreshInterval - Intervalo de refresh em ms (default: 30000)
 */
export function useSparkline(points = 50, refreshInterval = 30000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSparkline = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/sparkline?points=${points}`);
      if (!response.ok) throw new Error('Failed to fetch sparkline');
      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [points]);

  useEffect(() => {
    fetchSparkline();
    const interval = setInterval(fetchSparkline, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchSparkline, refreshInterval]);

  return { data, loading, error, refetch: fetchSparkline };
}

/**
 * Hook para obter stats em tempo real (CPU, RAM, etc)
 * @param {number} refreshInterval - Intervalo de refresh em ms (default: 5000)
 */
export function useRealtimeStats(refreshInterval = 5000) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/realtime`);
      if (!response.ok) throw new Error('Failed to fetch realtime stats');
      const result = await response.json();
      setStats(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchStats, refreshInterval]);

  return { stats, loading, error, refetch: fetchStats };
}

/**
 * Hook combinado para dashboard
 * Retorna sparkline e realtime stats juntos
 */
export function useDashboardPerformance() {
  const sparkline = useSparkline(50, 30000);
  const realtime = useRealtimeStats(5000);

  return {
    sparkline: sparkline.data,
    sparklineLoading: sparkline.loading,
    sparklineError: sparkline.error,
    
    realtime: realtime.stats,
    realtimeLoading: realtime.loading,
    realtimeError: realtime.error,
    
    // Helpers
    isLoading: sparkline.loading || realtime.loading,
    hasError: sparkline.error || realtime.error,
    
    // Actions
    refetchAll: () => {
      sparkline.refetch();
      realtime.refetch();
    }
  };
}

export default useDashboardPerformance;
