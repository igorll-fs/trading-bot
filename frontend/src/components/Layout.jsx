import { useMemo, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useTheme } from '@/components/ThemeProvider';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { LayoutDashboard, Settings, History, BookOpen, Moon, Sun, Wifi, WifiOff, Activity, AlertTriangle, CircleDot, FlaskConical, ShieldCheck, ExternalLink, Menu } from 'lucide-react';
import { useBotStatus } from '@/hooks/useBotQueries';
import { useBotStream } from '@/providers/BotDataProvider';
import { formatDateTime } from '@/lib/formatters';

const Layout = () => {
  const location = useLocation();
  const { theme, setTheme } = useTheme();
  const { streamState } = useBotStream();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { data: status, isFetching: statusFetching } = useBotStatus({
    staleTime: 30_000,
    refetchInterval: 45_000,
  });

  const navItems = useMemo(() => (
    [
      { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { path: '/settings', icon: Settings, label: 'Configuracoes' },
      { path: '/trades', icon: History, label: 'Historico' },
      { path: '/instructions', icon: BookOpen, label: 'Instrucoes' },
    ]
  ), []);

  const connectionMeta = useMemo(() => ({
    open: {
      label: 'Conectado',
      Icon: Wifi,
      className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    },
    connecting: {
      label: 'Reconectando...',
      Icon: Activity,
      className: 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse',
    },
    closed: {
      label: 'Offline',
      Icon: WifiOff,
      className: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    },
    unavailable: {
      label: 'Backend indisponivel',
      Icon: AlertTriangle,
      className: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    },
    idle: {
      label: 'Aguardando conexao',
      Icon: CircleDot,
      className: 'bg-white/5 text-white/50 border-white/10',
    },
  }[streamState] || {
    label: 'Aguardando conexao',
    Icon: CircleDot,
    className: 'bg-white/5 text-white/50 border-white/10',
  }), [streamState]);

  const modeMeta = useMemo(() => ((status?.testnet_mode ?? true)
    ? {
        label: 'Modo Testnet',
        Icon: FlaskConical,
        className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
      }
    : {
        label: 'Modo Real',
        Icon: ShieldCheck,
        className: 'bg-violet-500/10 text-violet-400 border-violet-500/30',
      }), [status?.testnet_mode]);

  const runningMeta = useMemo(() => (status?.is_running
    ? {
        label: 'Bot em execucao',
        className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      }
    : {
        label: 'Bot parado',
        className: 'bg-white/5 text-white/50 border-white/10',
      }), [status?.is_running]);

  const lastUpdateIso = status?.last_update;
  const lastUpdateLabel = useMemo(
    () => formatDateTime(lastUpdateIso),
    [lastUpdateIso]
  );

  const isDataStale = useMemo(() => {
    if (!lastUpdateIso) return false;
    const elapsedMs = Date.now() - new Date(lastUpdateIso).getTime();
    return elapsedMs > 60_000; // consider stale after 60s
  }, [lastUpdateIso]);

  // Componente reutilizavel para sidebar/drawer
  const SidebarContent = ({ onNavigate }) => (
    <div className="flex flex-col h-full">
      {/* Gradient glow effects */}
      <div className="absolute -top-20 -left-20 w-40 h-40 bg-violet-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-20 -left-10 w-32 h-32 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

      {/* Logo Section */}
      <div className="p-6 border-b border-white/10 relative">
        <h1 className="text-2xl font-bold gradient-text">Trading Bot</h1>
        <p className="text-sm text-white/40 mt-1 font-mono">Binance Spot</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2" aria-label="Navegacao principal">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              aria-current={isActive ? 'page' : undefined}
              onClick={onNavigate}
            >
              <Button
                data-testid={`nav-${item.label.toLowerCase()}`}
                variant="ghost"
                className={`w-full justify-start gap-3 transition-all duration-300 rounded-xl h-12 group/nav ${
                  isActive
                    ? 'bg-gradient-to-r from-violet-500/15 to-cyan-500/10 border-l-2 border-l-violet-500 text-violet-400 font-semibold shadow-lg shadow-violet-500/10'
                    : 'text-white/60 hover:text-white hover:bg-white/5 border-l-2 border-l-transparent hover:border-l-violet-500/50'
                }`}
              >
                <Icon
                  size={24}
                  aria-hidden="true"
                  className={`transition-all duration-300 ${
                    isActive
                      ? 'text-violet-400'
                      : 'text-white/50 group-hover/nav:text-violet-400 group-hover/nav:scale-110'
                  }`}
                />
                <span className={`transition-all duration-300 ${!isActive && 'group-hover/nav:translate-x-1'}`}>
                  {item.label}
                </span>
              </Button>
            </Link>
          );
        })}
      </nav>

      {/* Theme Toggle */}
      <div className="p-4 border-t border-white/10">
        <Button
          data-testid="theme-toggle"
          variant="outline"
          size="sm"
          className="w-full gap-2 border-white/10 text-white/60 hover:text-white hover:bg-white/5 hover:border-violet-500/30 rounded-xl h-10 transition-all duration-300"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          aria-pressed={theme === 'dark'}
          aria-label={theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'}
        >
          {theme === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
          {theme === 'dark' ? 'Modo Claro' : 'Modo Escuro'}
        </Button>
      </div>

      {/* Igor Credits Footer */}
      <div className="p-4 border-t border-white/10">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-violet-500/10 via-transparent to-cyan-500/10 p-3 border border-white/10 hover:border-violet-500/30 transition-all duration-300 group hover:shadow-lg hover:shadow-violet-500/10">
          <div className="absolute -top-10 -left-10 w-20 h-20 bg-violet-500/20 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <div className="absolute -bottom-10 -right-10 w-20 h-20 bg-cyan-500/20 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

          <div className="relative flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 blur-sm opacity-50 group-hover:opacity-80 transition-opacity" />
              <div className="relative w-10 h-10 rounded-full p-[2px] bg-gradient-to-br from-violet-500 to-cyan-500 group-hover:scale-105 transition-transform duration-300">
                <div className="w-full h-full rounded-full bg-[#0A0A0A] flex items-center justify-center">
                  <span className="text-sm font-bold bg-gradient-to-br from-violet-400 to-cyan-400 bg-clip-text text-transparent">
                    IL
                  </span>
                </div>
              </div>
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-[10px] text-white/40 uppercase tracking-wider">Desenvolvido por</p>
              <p className="text-sm font-semibold text-white truncate">Igor Luiz</p>
            </div>

            <a
              href="https://www.instagram.com/__igor.l_/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center w-9 h-9 rounded-xl bg-white/5 border border-white/10 hover:border-violet-500/50 hover:bg-violet-500/10 transition-all duration-300 group/ig"
              aria-label="Seguir Igor no Instagram (abre em nova aba)"
            >
              <ExternalLink size={16} className="text-white/60 group-hover/ig:text-violet-400 transition-colors" />
            </a>
          </div>

          <a
            href="https://www.instagram.com/__igor.l_/"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-2 flex items-center gap-1.5 text-xs text-white/40 hover:text-violet-400 transition-colors"
            aria-label="Instagram @__igor.l_ (abre em nova aba)"
          >
            <span>@__igor.l_</span>
          </a>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#0A0A0A]">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-violet-500 focus:px-4 focus:py-2 focus:text-sm focus:text-white"
      >
        Pular para o conteudo principal
      </a>

      {/* Desktop Sidebar - Hidden on Mobile */}
      <aside className="hidden md:flex w-64 bg-black/40 backdrop-blur-xl border-r border-white/10 flex-col relative overflow-hidden">
        <SidebarContent />
      </aside>

      {/* Mobile Drawer */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent
          side="left"
          className="w-64 p-0 bg-black/40 backdrop-blur-xl border-white/10"
        >
          <SidebarContent onNavigate={() => setMobileMenuOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Main Content */}
      <main id="main-content" className="flex-1 overflow-y-auto flex flex-col bg-[#0A0A0A] mesh-bg" role="main">
        {/* Header - Glassmorphism */}
        <header className="sticky top-0 z-20 border-b border-white/10 bg-black/60 backdrop-blur-xl">
          <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-3">
            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg hover:bg-white/5 transition-colors mr-3"
              aria-label="Abrir menu de navegacao"
            >
              <Menu size={24} className="text-white" />
            </button>
            <div className="flex flex-wrap items-center gap-2" aria-live="polite" aria-atomic="true">
              <Badge
                variant="outline"
                className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium border ${connectionMeta.className}`}
                title={
                  isDataStale
                    ? `Dados desatualizados - Atualizado em ${lastUpdateLabel}`
                    : `Atualizado em ${lastUpdateLabel}`
                }
              >
                <connectionMeta.Icon size={14} aria-hidden="true" />
                {connectionMeta.label}
                {lastUpdateLabel && (
                  <span className="text-[10px] text-white/40">- {lastUpdateLabel}</span>
                )}
                {isDataStale && (
                  <span className="text-[10px] text-amber-400">(desatualizado)</span>
                )}
              </Badge>
              <Badge
                variant="outline"
                className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium border ${modeMeta.className}`}
              >
                <modeMeta.Icon size={14} aria-hidden="true" />
                {modeMeta.label}
              </Badge>
              <Badge
                variant="outline"
                className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium border ${runningMeta.className}`}
              >
                <CircleDot
                  size={14}
                  aria-hidden="true"
                  className={status?.is_running ? 'text-emerald-400 animate-pulse' : 'text-white/40'}
                />
                {runningMeta.label}
              </Badge>
              {statusFetching && (
                <Activity aria-hidden="true" className="h-4 w-4 animate-spin text-violet-400" />
              )}
            </div>
            <div className="text-xs text-white/40 font-mono">
              {lastUpdateLabel}
            </div>
          </div>
        </header>
        <div className="flex-1 p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
