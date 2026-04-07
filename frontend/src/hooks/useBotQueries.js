import {
  BOT_PERFORMANCE_QUERY_KEY,
  BOT_STATUS_QUERY_KEY,
  BOT_TRADES_QUERY_KEY,
  LLM_STATUS_QUERY_KEY,
} from "@/hooks/queryKeys";
import { apiClient } from "@/lib/api";
import { useQuery } from "react-query";

const defaultQueryOptions = {
  refetchOnWindowFocus: false,
  retry: 1,
};

export const useBotStatus = (options = {}) => {
  return useQuery(
    BOT_STATUS_QUERY_KEY,
    async () => {
      const response = await apiClient.get("/bot/status", {
        skipGlobalErrorHandler: true,
      });
      return response.data;
    },
    {
      staleTime: 10_000,
      refetchInterval: 30_000,
      ...defaultQueryOptions,
      ...options,
      onSuccess: (data) => {
        if (typeof window !== "undefined") {
          window.sessionStorage?.setItem(
            "bot:isRunning",
            data?.is_running ? "1" : "0",
          );
        }
        options?.onSuccess?.(data);
      },
    },
  );
};

export const useBotPerformance = (options = {}) => {
  return useQuery(
    BOT_PERFORMANCE_QUERY_KEY,
    async () => {
      const response = await apiClient.get("/performance", {
        skipGlobalErrorHandler: true,
      });
      return response.data;
    },
    {
      staleTime: 10_000,
      refetchInterval: 45_000,
      ...defaultQueryOptions,
      ...options,
    },
  );
};

export const useBotTrades = (options = {}) => {
  return useQuery(
    BOT_TRADES_QUERY_KEY,
    async () => {
      const response = await apiClient.get("/trades", {
        params: { limit: 100 },
        skipGlobalErrorHandler: true,
      });
      return response.data;
    },
    {
      staleTime: 15_000,
      refetchInterval: 60_000,
      ...defaultQueryOptions,
      ...options,
    },
  );
};

/**
 * Hook para obter status e métricas do LLM Analyzer (Ollama)
 *
 * Retorna:
 * - enabled: Se LLM está ativado
 * - available: Se Ollama está rodando
 * - metrics: { requests_total, cache_hits, cache_hit_rate, avg_latency_ms }
 * - last_analysis: { opinion, confidence, reasoning, symbol, timestamp }
 */
export const useLLMStatus = (options = {}) => {
  return useQuery(
    LLM_STATUS_QUERY_KEY,
    async () => {
      const response = await apiClient.get("/llm/status", {
        skipGlobalErrorHandler: true,
      });
      return response.data;
    },
    {
      staleTime: 10_000,
      refetchInterval: 15_000, // 15s - matching bot loop interval
      ...defaultQueryOptions,
      ...options,
    },
  );
};

/**
 * Hook para obter status e métricas do LLM Market Analyzer (sistema avançado)
 *
 * Retorna:
 * - enabled: Se Market Analyzer está ativado
 * - available: Se Ollama está rodando
 * - metrics: { market_analyses, trade_recommendations, avg_latency_ms }
 * - recent_analyses: Array com análises de regime recentes
 * - trade_history_size: Quantidade de trades no histórico de aprendizado
 */
export const useMarketAnalyzerStatus = (options = {}) => {
  return useQuery(
    ["llm", "market-analyzer", "status"],
    async () => {
      const response = await apiClient.get("/llm/market-analyzer/status", {
        skipGlobalErrorHandler: true,
      });
      return response.data;
    },
    {
      staleTime: 10_000,
      refetchInterval: 15_000, // 15s - matching bot loop interval
      ...defaultQueryOptions,
      ...options,
    },
  );
};
