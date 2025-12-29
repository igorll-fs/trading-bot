import { Suspense, lazy, useEffect, useState } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/components/ThemeProvider';
import { Toaster } from '@/components/ui/sonner';
import Layout from '@/components/Layout';
import ErrorBoundary from '@/components/ErrorBoundary';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BotDataProvider } from '@/providers/BotDataProvider';
import RemoteSetup from '@/components/RemoteSetup';

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Settings = lazy(() => import('@/pages/Settings'));
const Trades = lazy(() => import('@/pages/Trades'));
const Instructions = lazy(() => import('@/pages/Instructions'));

const PageFallback = () => (
  <div className="flex items-center justify-center h-full py-20">
    <div className="text-center space-y-3">
      <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
      <p className="text-sm text-muted-foreground">Carregando conteúdo...</p>
    </div>
  </div>
);

function App() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  useEffect(() => {
    // Handle browser/tab close - rely on latest synced status without async requests
    const handleBeforeUnload = (e) => {
      try {
        const isRunning = window.sessionStorage?.getItem('bot:isRunning') === '1';
        if (isRunning) {
          const warningMessage = '⚠️ O bot está rodando! Fechar pode causar prejuízo. Pare o bot primeiro no Dashboard.';
          e.preventDefault();
          e.returnValue = warningMessage;
          return warningMessage;
        }
      } catch (error) {
        console.debug('Não foi possível verificar o status do bot antes de fechar a aba.', error);
      }
      return undefined;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Detectar acesso remoto (Cloudflare Tunnel)
  const isRemoteAccess = typeof window !== 'undefined' && window.location.hostname.includes('trycloudflare.com');

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BotDataProvider>
          <ThemeProvider defaultTheme="dark" storageKey="trading-bot-theme">
            <div className="App" translate="no">
              {isRemoteAccess && <RemoteSetup />}
              <BrowserRouter>
                <ErrorBoundary>
                  <Suspense fallback={<PageFallback />}>
                    <Routes>
                      <Route path="/" element={<Layout />}>
                        <Route index element={<Dashboard />} />
                        <Route path="settings" element={<Settings />} />
                        <Route path="trades" element={<Trades />} />
                        <Route path="instructions" element={<Instructions />} />
                      </Route>
                    </Routes>
                  </Suspense>
                </ErrorBoundary>
              </BrowserRouter>
              <Toaster position="top-right" />
            </div>
          </ThemeProvider>
        </BotDataProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;