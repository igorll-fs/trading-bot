import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { BookOpen, AlertTriangle, CheckCircle2, Info } from 'lucide-react';

const Instructions = () => {
  return (
    <div className="p-4 sm:p-8 space-y-6 animate-fade-in max-w-5xl">
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold gradient-text">Instrucoes de Uso</h1>
        <p className="text-white/50 mt-1">Guia completo para configurar e usar o bot</p>
      </div>

      {/* Testnet Alert - Premium Styled */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-cyan-500/10 border border-emerald-500/30 p-6">
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-emerald-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-cyan-500/20 rounded-full blur-3xl" />
        <div className="relative">
          <div className="flex items-start gap-3 mb-4">
            <div className="p-2 rounded-xl bg-emerald-500/20">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" aria-hidden="true" />
            </div>
            <div>
              <p className="font-bold text-emerald-400 text-lg">Testnet Disponivel - Opere SEM RISCO!</p>
              <p className="text-white/60 mt-1">
                <strong className="text-white/80">Novo aqui?</strong> Use o <strong className="text-emerald-400">Binance Testnet</strong> para testar o bot com <strong className="text-cyan-400">$100.000 USDT virtuais</strong> - totalmente gratuito e sem risco financeiro!
              </p>
            </div>
          </div>
          <div className="mt-4 space-y-2 text-sm text-white/60 ml-12">
            <p className="flex items-center gap-2"><span className="text-emerald-400">&#10003;</span> <strong className="text-white/80">Gratuito</strong> - Dinheiro 100% virtual</p>
            <p className="flex items-center gap-2"><span className="text-emerald-400">&#10003;</span> <strong className="text-white/80">Ambiente real</strong> - Mesma API da Binance</p>
            <p className="flex items-center gap-2"><span className="text-emerald-400">&#10003;</span> <strong className="text-white/80">Login rapido</strong> - Use GitHub ou Google</p>
          </div>
          <a
            href="https://testnet.binance.vision"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 mt-5 ml-12 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-emerald-500/30 transition-all duration-300 font-semibold text-sm hover:scale-[1.02]"
          >
            Acessar Testnet Agora
          </a>
        </div>
      </div>

      {/* Installation */}
      <Card className="glass-card hover:shadow-glow-violet transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 shadow-lg shadow-violet-500/30">
                <BookOpen size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">1. Instalacao (Primeira Execucao)</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2 text-white/80">No Windows:</h3>
            <div className="bg-white/5 border border-white/10 p-4 rounded-xl font-mono text-sm text-white/70">
              <p>1. Execute install.bat (instala dependencias)</p>
              <p>2. Execute start.bat (inicia o sistema)</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Configuration */}
      <Card className="glass-card hover:shadow-glow-cyan transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-600 shadow-lg shadow-cyan-500/30">
                <CheckCircle2 size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">2. Configuracao das APIs</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">A. Binance API (Obrigatório)</h3>
            
            <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-3">
              <p className="font-bold text-green-700 dark:text-green-400 mb-2">🧪 Opção 1: Testnet (Recomendado)</p>
              <ol className="list-decimal list-inside space-y-2 text-sm text-green-800 dark:text-green-300">
                <li>Acesse <a href="https://testnet.binance.vision" target="_blank" rel="noopener noreferrer" className="text-green-600 dark:text-green-400 underline font-semibold">testnet.binance.vision</a></li>
                <li>Entre com sua conta Binance ou crie um acesso gratuito para o ambiente Spot Testnet</li>
                <li>Em <strong>Dashboard &gt; API Keys</strong>, gere uma nova <strong>Spot Testnet API Key</strong></li>
                <li>Copie a <strong>API Key</strong> e o <strong>Secret</strong> e cole na página de <strong>Configurações</strong></li>
                <li>Mantenha o toggle <strong>Testnet ATIVO</strong> para operar com USDT virtuais</li>
              </ol>
              <p className="text-xs text-green-700 dark:text-green-400 mt-2 italic">
                ✅ Zero riscos, zero custos, mesmo ambiente real da Binance!
              </p>
            </div>

            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <p className="font-bold text-amber-700 dark:text-amber-400 mb-2">💰 Opção 2: Mainnet (Dinheiro Real)</p>
              <p className="text-sm text-amber-800 dark:text-amber-300 mb-2">⚠️ Só use após dominar o bot no Testnet!</p>
              <ol className="list-decimal list-inside space-y-2 text-sm text-amber-800 dark:text-amber-300">
                <li>Acesse <a href="https://www.binance.com/en/my/settings/api-management" target="_blank" rel="noopener noreferrer" className="text-amber-600 dark:text-amber-400 underline font-semibold">Binance API Management</a></li>
                <li>Crie uma nova API Key dedicada para operações Spot</li>
                <li><strong>CRÍTICO:</strong> Ative APENAS <strong>&quot;Enable Spot &amp; Margin Trading&quot;</strong></li>
                <li>Configure restrições de IP (recomendado)</li>
                <li>Cole na página de Configurações e <strong>DESATIVE</strong> o toggle Testnet</li>
              </ol>
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-2">B. Telegram Bot (Obrigatório)</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Abra o Telegram e busque por <strong>@BotFather</strong></li>
              <li>Envie o comando <code className="bg-muted px-2 py-1 rounded">/newbot</code></li>
              <li>Siga as instruções e copie o <strong>Bot Token</strong></li>
              <li>Busque por <strong>@userinfobot</strong> no Telegram</li>
              <li>Inicie uma conversa e copie seu <strong>Chat ID</strong></li>
              <li>Cole ambos na página de Configurações</li>
            </ol>
          </div>
        </CardContent>
      </Card>

      {/* How it Works */}
      <Card className="glass-card hover:shadow-glow-violet transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-500/30">
                <Info size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">3. Como Funciona</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2 text-sm">
            <p><strong>Estratégia:</strong> Combina EMAs (12/26/50/200), MACD, RSI, VWAP, OBV e ATR em múltiplos timeframes (15m + 1h) para confirmar tendências antes de operar.</p>
            <p><strong>Seleção de Criptos:</strong> Prioriza pares com volume crescente, volatilidade saudável e força de tendência, atribuindo uma pontuação dinâmica a cada oportunidade.</p>
            <p><strong>Gestão de Risco:</strong> Stop-loss e take-profit automáticos ajustados por ATR e machine learning. Limite padrão de 3 posições simultâneas.</p>
            <p><strong>Notificações:</strong> Você receberá notificações no Telegram quando posições forem abertas ou fechadas.</p>
          </div>
        </CardContent>
      </Card>

      {/* Risk Management */}
      <Card className="glass-card hover:shadow-glow-emerald transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-500/30">
                <CheckCircle2 size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">4. Parametros de Risco</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p><strong>Risco por Trade:</strong> Padrão 2% do saldo (configurável)</p>
          <p><strong>Alavancagem:</strong> 1x (operações Spot sem margem)</p>
          <p><strong>Stop-Loss:</strong> Calculado com ATR e ajustado pelo sistema de aprendizado</p>
          <p><strong>Take-Profit:</strong> Dinâmico para manter razão risco/retorno positiva</p>
          <p><strong>Máximo de Posições:</strong> 3 simultâneas (configurável)</p>
        </CardContent>
      </Card>

      {/* Warnings */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-rose-500/10 via-rose-500/5 to-amber-500/10 border border-rose-500/30 p-6">
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-rose-500/20 rounded-full blur-3xl" />
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-rose-500/20">
            <AlertTriangle className="h-5 w-5 text-rose-400" aria-hidden="true" />
          </div>
          <div className="space-y-3">
            <p className="font-bold text-rose-400 text-lg">Avisos Importantes</p>
            <ul className="space-y-2 text-sm text-white/60">
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span><strong className="text-white/80">SEMPRE teste primeiro no Testnet</strong> antes de usar dinheiro real</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Trading de criptomoedas envolve risco significativo de perda</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Nao invista mais do que voce pode perder</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>O bot nao garante lucros - use por sua conta e risco</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Monitore regularmente as operacoes do bot</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Mantenha suas API Keys seguras e nunca compartilhe</span></li>
            </ul>
          </div>
        </div>
      </div>

      {/* Support */}
      <Card className="glass-card hover:shadow-glow-violet transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="text-xl">
            <h2 className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/30">
                <span className="text-white font-bold text-sm">5</span>
              </div>
              <span className="text-white">Iniciando o Bot</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <ol className="space-y-3 text-white/60">
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400 text-xs font-bold shrink-0">1</span>
              <span>Configure todas as APIs obrigatorias na pagina <strong className="text-white/80">Configuracoes</strong></span>
            </li>
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400 text-xs font-bold shrink-0">2</span>
              <span>Clique em <strong className="text-white/80">Salvar Configuracoes</strong></span>
            </li>
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400 text-xs font-bold shrink-0">3</span>
              <span>Va para o <strong className="text-white/80">Dashboard</strong></span>
            </li>
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 rounded-lg bg-violet-500/20 flex items-center justify-center text-violet-400 text-xs font-bold shrink-0">4</span>
              <span>Clique no botao <strong className="text-cyan-400">Iniciar Bot</strong></span>
            </li>
            <li className="flex items-start gap-3">
              <span className="w-6 h-6 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 text-xs font-bold shrink-0">5</span>
              <span>Monitore o bot atraves do Dashboard e receba notificacoes no Telegram</span>
            </li>
          </ol>
        </CardContent>
      </Card>
    </div>
  );
};

export default Instructions;