import { useQuery } from 'react-query';
import { apiClient } from '@/lib/api';
import {
  BOT_PERFORMANCE_QUERY_KEY,
  BOT_STATUS_QUERY_KEY,
  BOT_TRADES_QUERY_KEY,
} from '@/hooks/queryKeys';

const defaultQueryOptions = {
  refetchOnWindowFocus: false,
  retry: 1,
};

export const useBotStatus = (options = {}) => {
  return useQuery(
    BOT_STATUS_QUERY_KEY,
    async () => {
      const response = await apiClient.get('/bot/status', { skipGlobalErrorHandler: true });
      return response.data;
    },
    {
      staleTime: 10_000,
      refetchInterval: 30_000,
      ...defaultQueryOptions,
      ...options,
      onSuccess: (data) => {
        if (typeof window !== 'undefined') {
          window.sessionStorage?.setItem('bot:isRunning', data?.is_running ? '1' : '0');
        }
        options?.onSuccess?.(data);
      },
    }
  );
};

export const useBotPerformance = (options = {}) => {
  return useQuery(
    BOT_PERFORMANCE_QUERY_KEY,
    async () => {
      const response = await apiClient.get('/performance', { skipGlobalErrorHandler: true });
      return response.data;
    },
    {
      staleTime: 10_000,
      refetchInterval: 45_000,
      ...defaultQueryOptions,
      ...options,
    }
  );
};

export const useBotTrades = (options = {}) => {
  return useQuery(
    BOT_TRADES_QUERY_KEY,
    async () => {
      const response = await apiClient.get('/trades', {
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
    }
  );
};
