import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';

/**
 * Custom hook for API calls with loading and error states
 * 
 * @param {string} endpoint - API endpoint (e.g., '/bot/status')
 * @param {any} initialData - Initial data state
 * @returns {object} { data, loading, error, fetch, post, put, del }
 * 
 * @example
 * const { data: status, loading, fetch } = useApi('/bot/status');
 * 
 * useEffect(() => {
 *   fetch();
 * }, []);
 */
export function useApi(endpoint, initialData = null) {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * GET request
   * @param {object} params - Query parameters
   */
  const fetch = useCallback(async (params = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await apiClient.get(endpoint, {
        params,
        skipGlobalErrorHandler: true,
      });
      
      setData(res.data);
      return res.data;
    } catch (err) {
      console.error(`❌ Error fetching ${endpoint}:`, err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  /**
   * POST request
   * @param {object} body - Request body
   */
  const post = useCallback(async (body) => {
    try {
      setLoading(true);
      setError(null);
      
  const res = await apiClient.post(endpoint, body, { skipGlobalErrorHandler: true });
      
      setData(res.data);
      return res.data;
    } catch (err) {
      console.error(`❌ Error posting to ${endpoint}:`, err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  /**
   * PUT request
   * @param {object} body - Request body
   */
  const put = useCallback(async (body) => {
    try {
      setLoading(true);
      setError(null);
      
  const res = await apiClient.put(endpoint, body, { skipGlobalErrorHandler: true });
      
      setData(res.data);
      return res.data;
    } catch (err) {
      console.error(`❌ Error putting to ${endpoint}:`, err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  /**
   * DELETE request
   */
  const del = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
  const res = await apiClient.delete(endpoint, { skipGlobalErrorHandler: true });
      
      setData(res.data);
      return res.data;
    } catch (err) {
      console.error(`❌ Error deleting ${endpoint}:`, err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  return { 
    data, 
    loading, 
    error, 
    fetch, 
    post, 
    put, 
    del,
    setData  // Allow manual data updates
  };
}
