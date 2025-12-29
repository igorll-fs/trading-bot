import { useEffect, useState, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Settings, ExternalLink, X } from 'lucide-react';

const RemoteSetup = ({ onConfigured }) => {
  const [backendUrl, setBackendUrl] = useState('');
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const initialized = useRef(false);
  
  useEffect(() => {
    // Evitar múltiplas execuções
    if (initialized.current) return;
    initialized.current = true;
    
    const stored = localStorage.getItem('remote_backend_url');
    if (stored) {
      setBackendUrl(stored);
      onConfigured?.(stored);
    } else {
      setIsConfiguring(true);
    }
  }, []); // Removido onConfigured das dependências para evitar loop
  
  const handleSave = () => {
    const trimmed = backendUrl.trim();
    if (trimmed && trimmed.startsWith('http')) {
      localStorage.setItem('remote_backend_url', trimmed);
      setIsConfiguring(false);
      window.location.reload();
    }
  };
  
  if (!isConfiguring && backendUrl) {
    // Versão minificada para mobile
    if (isMinimized) {
      return (
        <button
          onClick={() => setIsMinimized(false)}
          className="fixed bottom-2 right-2 z-50 w-10 h-10 bg-emerald-500/20 border border-emerald-500/30 rounded-full flex items-center justify-center touch-manipulation"
        >
          <ExternalLink className="w-4 h-4 text-emerald-400" />
        </button>
      );
    }
    
    return (
      <div className="fixed bottom-2 right-2 z-50 touch-manipulation">
        <div className="bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl p-3 shadow-2xl max-w-[200px]">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <ExternalLink className="w-3 h-3 text-emerald-400" />
              <p className="text-xs font-medium text-white">Remoto</p>
            </div>
            <button onClick={() => setIsMinimized(true)} className="text-slate-400 p-1">
              <X className="w-3 h-3" />
            </button>
          </div>
          <p className="text-[10px] text-slate-400 mb-2 truncate">{backendUrl.replace('https://', '')}</p>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsConfiguring(true)}
            className="w-full text-[10px] h-7"
          >
            <Settings className="w-3 h-3 mr-1" />
            Config
          </Button>
        </div>
      </div>
    );
  }
  
  if (isConfiguring) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 touch-manipulation">
        <div className="bg-slate-900 border border-white/10 rounded-2xl p-4 sm:p-8 max-w-md w-full shadow-2xl">
          <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
            <Settings className="w-5 sm:w-6 h-5 sm:h-6 text-blue-400" />
            <h2 className="text-base sm:text-xl font-bold text-white">Configurar Backend</h2>
          </div>
          
          <p className="text-xs sm:text-sm text-slate-400 mb-3 sm:mb-4">
            Cole a URL do backend (API):
          </p>
          
          <Input
            type="url"
            placeholder="https://xxx.trycloudflare.com"
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
            className="mb-3 sm:mb-4 text-base"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck="false"
          />
          
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-2 sm:p-3 mb-3 sm:mb-4">
            <p className="text-[10px] sm:text-xs text-amber-400">
              💡 Copie a URL do backend do PC
            </p>
          </div>
          
          <div className="flex gap-2">
            {backendUrl && (
              <Button
                variant="ghost"
                onClick={() => {
                  setIsConfiguring(false);
                }}
                className="flex-1 h-10 sm:h-11"
              >
                Cancelar
              </Button>
            )}
            <Button
              onClick={handleSave}
              disabled={!backendUrl.trim() || !backendUrl.startsWith('http')}
              className="flex-1 h-10 sm:h-11"
            >
              Conectar
            </Button>
          </div>
        </div>
      </div>
    );
  }
  
  return null;
};

export default RemoteSetup;
