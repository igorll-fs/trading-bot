import { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
    
    // Log para debugging
    if (process.env.NODE_ENV === 'development') {
      console.group('🔴 Error Boundary Details');
      console.error('Error:', error);
      console.error('Component Stack:', errorInfo?.componentStack);
      console.groupEnd();
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Verificar se é erro de extensão de navegador
      const isExtensionError = this.state.error?.message?.includes('insertBefore') ||
        this.state.error?.message?.includes('removeChild') ||
        this.state.error?.message?.includes('appendChild');

      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-500/10 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-amber-400" />
            </div>
            
            <h2 className="text-xl font-semibold text-white mb-2">
              {isExtensionError ? 'Conflito Detectado' : 'Algo deu errado'}
            </h2>
            
            <p className="text-white/60 text-sm mb-4">
              {isExtensionError ? (
                <>
                  Uma extensão do navegador (tradutor automático, ad-blocker, etc.) 
                  pode estar interferindo com a página.
                  <br /><br />
                  <strong className="text-amber-400">Solução:</strong> Desative extensões 
                  de tradução automática ou abra em uma janela anônima.
                </>
              ) : (
                'Ocorreu um erro ao renderizar esta página. Tente recarregar.'
              )}
            </p>

            <div className="flex gap-3 justify-center">
              <Button
                onClick={this.handleReset}
                variant="outline"
                className="gap-2"
              >
                Tentar Novamente
              </Button>
              <Button
                onClick={this.handleReload}
                className="gap-2 bg-violet-500 hover:bg-violet-600"
              >
                <RefreshCw className="w-4 h-4" />
                Recarregar Página
              </Button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-6 text-left">
                <summary className="text-xs text-white/40 cursor-pointer hover:text-white/60">
                  Detalhes técnicos (dev only)
                </summary>
                <pre className="mt-2 p-3 bg-black/50 rounded-lg text-[10px] text-rose-400 overflow-auto max-h-40">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
