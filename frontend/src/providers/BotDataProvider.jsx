import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from 'react-query';
import { getBackendBaseUrl } from '@/lib/api';
import {
  BOT_PERFORMANCE_QUERY_KEY,
  BOT_STATUS_QUERY_KEY,
  BOT_STREAM_STATE_KEY,
} from '@/hooks/queryKeys';

const DEFAULT_STREAM_STATE = 'idle';

const BotStreamContext = createContext({
  streamState: DEFAULT_STREAM_STATE,
});

export const BotDataProvider = ({ children }) => {
  const queryClient = useQueryClient();
  const [streamState, setStreamState] = useState(DEFAULT_STREAM_STATE);
  const eventSourceRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const baseUrl = getBackendBaseUrl();
    if (!baseUrl) {
      setStreamState('unavailable');
      queryClient.setQueryData(BOT_STREAM_STATE_KEY, 'unavailable');
      return undefined;
    }

    const connect = () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      setStreamState('connecting');
      queryClient.setQueryData(BOT_STREAM_STATE_KEY, 'connecting');

      const streamUrl = `${baseUrl}/api/stream`;
      const es = new EventSource(streamUrl, { withCredentials: false });
      eventSourceRef.current = es;

      es.onopen = () => {
        setStreamState('open');
        queryClient.setQueryData(BOT_STREAM_STATE_KEY, 'open');
      };

      es.onmessage = (event) => {
        if (!event?.data) {
          return;
        }

        try {
          const payload = JSON.parse(event.data);

          if (payload?.status) {
            queryClient.setQueryData(BOT_STATUS_QUERY_KEY, payload.status);
            if (typeof window !== 'undefined') {
              window.sessionStorage?.setItem('bot:isRunning', payload.status?.is_running ? '1' : '0');
            }
          }

          if (payload?.performance) {
            queryClient.setQueryData(BOT_PERFORMANCE_QUERY_KEY, payload.performance);
          }
        } catch (error) {
          console.error('SSE payload parse error', error);
        }
      };

      es.onerror = () => {
        setStreamState('closed');
        queryClient.setQueryData(BOT_STREAM_STATE_KEY, 'closed');
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }

        if (!reconnectTimerRef.current) {
          reconnectTimerRef.current = window.setTimeout(() => {
            reconnectTimerRef.current = null;
            connect();
          }, 5000);
        }
      };
    };

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [queryClient]);

  const value = useMemo(
    () => ({
      streamState,
    }),
    [streamState]
  );

  return (
    <BotStreamContext.Provider value={value}>
      {children}
    </BotStreamContext.Provider>
  );
};

export const useBotStream = () => useContext(BotStreamContext);
