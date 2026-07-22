import { useQuery } from 'react-query';
import { apiClient } from '@/lib/api';

// Query keys
export const MARKET_PRICES_KEY = ['market', 'prices'];
export const MARKET_SIGNALS_KEY = ['market', 'signals'];
export const MARKET_BTC_HEALTH_KEY = ['market', 'btc-health'];
export const MARKET_REGIME_KEY = ['market', 'regime'];
export const ML_STATUS_KEY = ['learning', 'status'];
export const MONITORED_COINS_KEY = ['market', 'monitored-coins'];

/**
 * Hook para buscar moedas REALMENTE monitoradas pelo bot
 */
export const useMonitoredCoins = (options = {}) => {
  return useQuery(
    MONITORED_COINS_KEY,
    async () => {
      const { data } = await apiClient.get('/market/monitored-coins');
      return data;
    },
    {
      staleTime: 300000, // 5 minutos (muda pouco)
      cacheTime: 600000, // 10 minutos
      retry: 2,
      ...options,
    }
  );
};

/**
 * Hook para buscar preços em tempo real das moedas monitoradas
 */
export const useMarketPrices = (options = {}) => {
  return useQuery(
    MARKET_PRICES_KEY,
    async () => {
      const { data } = await apiClient.get('/market/prices');
      return data;
    },
    {
      refetchInterval: 30000, // Atualiza a cada 30 segundos
      staleTime: 15000,
      retry: 2,
      ...options,
    }
  );
};

/**
 * Hook para buscar sinais ativos detectados pelo bot
 */
export const useActiveSignals = (options = {}) => {
  return useQuery(
    MARKET_SIGNALS_KEY,
    async () => {
      const { data } = await apiClient.get('/market/signals');
      return data;
    },
    {
      refetchInterval: 60000, // Atualiza a cada minuto
      staleTime: 30000,
      retry: 2,
      ...options,
    }
  );
};

/**
 * Hook para verificar saúde do BTC (tendência macro)
 */
export const useBtcHealth = (options = {}) => {
  return useQuery(
    MARKET_BTC_HEALTH_KEY,
    async () => {
      const { data } = await apiClient.get('/market/btc-health');
      return data;
    },
    {
      refetchInterval: 60000,
      staleTime: 30000,
      retry: 2,
      ...options,
    }
  );
};

/**
 * Hook para detectar regime de mercado
 */
export const useMarketRegime = (options = {}) => {
  return useQuery(
    MARKET_REGIME_KEY,
    async () => {
      const { data } = await apiClient.get('/market/regime');
      return data;
    },
    {
      refetchInterval: 120000, // Atualiza a cada 2 minutos
      staleTime: 60000,
      retry: 2,
      ...options,
    }
  );
};

/**
 * Hook para buscar status do sistema de ML
 */
export const useMLStatus = (options = {}) => {
  return useQuery(
    ML_STATUS_KEY,
    async () => {
      const { data } = await apiClient.get('/learning/stats');
      return data;
    },
    {
      refetchInterval: 60000,
      staleTime: 30000,
      retry: 2,
      ...options,
    }
  );
};
