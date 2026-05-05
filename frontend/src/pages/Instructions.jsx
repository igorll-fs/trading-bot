import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BookOpen, AlertTriangle, CheckCircle2, Info, Terminal, Globe, Shield, Zap } from 'lucide-react';

const Instructions = () => {
  return (
    <div className="p-4 sm:p-8 space-y-6 animate-fade-in max-w-5xl">
      <div>
        <h1 className="text-3xl sm:text-4xl font-bold gradient-text">Instructions</h1>
        <p className="text-white/50 mt-1">Complete setup guide for TradingBot Enterprise</p>
      </div>

      {/* Testnet Alert */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-cyan-500/10 border border-emerald-500/30 p-6">
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-emerald-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-cyan-500/20 rounded-full blur-3xl" />
        <div className="relative">
          <div className="flex items-start gap-3 mb-4">
            <div className="p-2 rounded-xl bg-emerald-500/20">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" aria-hidden="true" />
            </div>
            <div>
              <p className="font-bold text-emerald-400 text-lg">Testnet Available — Trade with ZERO Risk!</p>
              <p className="text-white/60 mt-1">
                <strong className="text-white/80">New here?</strong> Use the <strong className="text-emerald-400">Binance Spot Testnet</strong> to test the bot with <strong className="text-cyan-400">virtual USDT</strong> — completely free and risk-free.
              </p>
            </div>
          </div>
          <div className="mt-4 space-y-2 text-sm text-white/60 ml-12">
            <p className="flex items-center gap-2"><span className="text-emerald-400">&#10003;</span> <strong className="text-white/80">Free</strong> — 100% virtual money</p>
            <p className="flex items-center gap-2"><span className="text-emerald-400">&#10003;</span> <strong className="text-white/80">Real environment</strong> — Same Binance API endpoints</p>
            <p className="flex items-center gap-2"><span className="text-emerald-400">&#10003;</span> <strong className="text-white/80">Quick login</strong> — Use GitHub or Google</p>
          </div>
          <a
            href="https://testnet.binance.vision"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 mt-5 ml-12 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:shadow-lg hover:shadow-emerald-500/30 transition-all duration-300 font-semibold text-sm hover:scale-[1.02]"
          >
            Access Testnet Now
          </a>
        </div>
      </div>

      {/* Prerequisites */}
      <Card className="glass-card hover:shadow-glow-violet transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-violet-600 shadow-lg shadow-violet-500/30">
                <BookOpen size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">1. Installation</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2 text-white/80">Prerequisites</h3>
            <ul className="space-y-1.5 text-sm text-white/60 ml-4 list-disc">
              <li>Python 3.11+ with venv support</li>
              <li>Node.js 18+ and npm</li>
              <li>MongoDB 7.0+ running locally</li>
              <li>Binance Spot Testnet account</li>
              <li>Ollama (optional — for LLM risk analysis)</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-2 text-white/80">Quick Setup (Linux)</h3>
            <div className="bg-white/5 border border-white/10 p-4 rounded-xl font-mono text-sm text-white/70 space-y-1">
              <p># 1. Clone and install backend</p>
              <p>git clone https://github.com/igordev30-ops/trading-bot.git</p>
              <p>cd trading-bot && python3 -m venv .venv</p>
              <p>.venv/bin/pip install -r backend/requirements.txt</p>
              <p className="mt-2"># 2. Configure environment</p>
              <p>cp backend/.env.example backend/.env</p>
              <p>nano backend/.env  # Set API keys + Telegram tokens</p>
              <p className="mt-2"># 3. Build frontend</p>
              <p>cd frontend && npm install && npx craco build</p>
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
              <span className="text-white">2. API Configuration</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">A. Binance API (Required)</h3>
            <div className="bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-3">
              <p className="font-bold text-green-700 dark:text-green-400 mb-2">🧪 Option 1: Testnet (Recommended)</p>
              <ol className="list-decimal list-inside space-y-2 text-sm text-green-800 dark:text-green-300">
                <li>Go to <a href="https://testnet.binance.vision" target="_blank" rel="noopener noreferrer" className="text-green-600 dark:text-green-400 underline font-semibold">testnet.binance.vision</a></li>
                <li>Log in with GitHub or Google</li>
                <li>Under <strong>Dashboard → API Keys</strong>, generate a <strong>Spot Testnet API Key</strong></li>
                <li>Check <strong>"Enable Spot & Margin Trading"</strong></li>
                <li>Copy <strong>API Key</strong> and <strong>Secret</strong> — paste in the <strong>Settings</strong> page</li>
                <li>Keep <strong>Testnet toggle ON</strong></li>
              </ol>
              <p className="text-xs text-green-700 dark:text-green-400 mt-2 italic">
                ✅ Zero risk, zero cost — same real Binance API!
              </p>
            </div>
            <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
              <p className="font-bold text-amber-700 dark:text-amber-400 mb-2">💰 Option 2: Mainnet (Real Money)</p>
              <p className="text-sm text-amber-800 dark:text-amber-300 mb-2">⚠️ Only use after mastering the bot on Testnet!</p>
              <ol className="list-decimal list-inside space-y-2 text-sm text-amber-800 dark:text-amber-300">
                <li>Go to <a href="https://www.binance.com/en/my/settings/api-management" target="_blank" rel="noopener noreferrer" className="text-amber-600 dark:text-amber-400 underline font-semibold">Binance API Management</a></li>
                <li>Create a new API Key for Spot trading</li>
                <li><strong>CRITICAL:</strong> Only enable <strong>"Enable Spot & Margin Trading"</strong></li>
                <li>Set IP restrictions (recommended)</li>
                <li>Paste in Settings and <strong>TURN OFF</strong> Testnet toggle</li>
              </ol>
            </div>
          </div>
          <div>
            <h3 className="font-semibold mb-2">B. Telegram Bot (Required)</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm text-white/60">
              <li>Open Telegram and search for <strong>@BotFather</strong></li>
              <li>Send <code className="bg-muted px-2 py-1 rounded">/newbot</code></li>
              <li>Follow the instructions and copy the <strong>Bot Token</strong></li>
              <li>Start a chat with your new bot (send <code className="bg-muted px-2 py-1 rounded">/start</code>)</li>
              <li>To get your Chat ID, send a message to the bot and visit:</li>
            </ol>
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl font-mono text-xs text-white/60 mt-2">
              https://api.telegram.org/bot&lt;TOKEN&gt;/getUpdates
            </div>
            <p className="text-sm text-white/60 mt-2">
              Paste both <strong className="text-white/80">Bot Token</strong> and <strong className="text-white/80">Chat ID</strong> in the Settings page.
            </p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">C. Ollama LLM (Optional)</h3>
            <p className="text-sm text-white/60">
              Install Ollama and pull a model for AI-powered risk analysis. The bot works without it — just disable <code className="bg-muted px-2 py-1 rounded">LLM_RISK_ADVISOR_ENABLED</code>.
            </p>
            <div className="bg-white/5 border border-white/10 p-3 rounded-xl font-mono text-xs text-white/60 mt-2">
              curl -fsSL https://ollama.ai/install.sh | sh<br/>
              ollama pull mistral
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Starting the System */}
      <Card className="glass-card hover:shadow-glow-emerald transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-500/30">
                <Zap size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">3. Starting the System</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div>
              <h4 className="font-semibold text-sm text-white/80 mb-1">1. Start MongoDB</h4>
              <div className="bg-white/5 border border-white/10 p-3 rounded-xl font-mono text-xs text-white/60">
                mongod --dbpath ~/data/mongodb --fork --logpath ~/data/mongodb/mongod.log
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-white/80 mb-1">2. Start Backend (FastAPI)</h4>
              <div className="bg-white/5 border border-white/10 p-3 rounded-xl font-mono text-xs text-white/60">
                cd trading-bot && .venv/bin/python backend/server.py
              </div>
              <p className="text-xs text-white/40 mt-1">API available at http://localhost:8000 · Swagger at /docs</p>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-white/80 mb-1">3. Build & Serve Frontend</h4>
              <div className="bg-white/5 border border-white/10 p-3 rounded-xl font-mono text-xs text-white/60">
                cd frontend && npx craco build<br/>
                python3 -m http.server 3000 --directory build
              </div>
              <p className="text-xs text-white/40 mt-1">Dashboard at http://localhost:3000</p>
            </div>
            <div>
              <h4 className="font-semibold text-sm text-white/80 mb-1">4. Start the Bot</h4>
              <div className="bg-white/5 border border-white/10 p-3 rounded-xl font-mono text-xs text-white/60">
                curl -X POST http://localhost:8000/api/bot/control \<br/>
                &nbsp;&nbsp;-H &apos;Content-Type: application/json&apos; \<br/>
                &nbsp;&nbsp;-d &apos;{'{'}&quot;action&quot;: &quot;start&quot;{'}'}&apos;
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Remote Access */}
      <Card className="glass-card hover:shadow-glow-violet transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-500/30">
                <Globe size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">4. Remote Access (Cloudflare Tunnel)</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-white/60">
          <p>
            Expose your dashboard securely without opening ports. The tunnel script starts a
            password-protected proxy + Cloudflare tunnel — access from any device.
          </p>
          <div className="bg-white/5 border border-white/10 p-3 rounded-xl font-mono text-xs text-white/60">
            # Start the tunnel (with authentication)<br/>
            bash scripts/tunnel.sh<br/><br/>
            # Custom password:<br/>
            PROXY_PASS=mysecret123 bash scripts/tunnel.sh
          </div>
          <p>
            Default password: <code className="bg-muted px-2 py-1 rounded">botmaster2026</code>.<br/>
            The script outputs a <code className="bg-muted px-2 py-1 rounded">https://*.trycloudflare.com</code> URL.
          </p>
          <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
            <p className="text-xs text-amber-800 dark:text-amber-300">
              ⚠️ Free tunnels get a random URL that changes on restart. For a fixed URL, register a
              Cloudflare account and create a named tunnel.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* How It Works */}
      <Card className="glass-card hover:shadow-glow-cyan transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-500 shadow-lg shadow-violet-500/30">
                <Terminal size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">5. How the Bot Works</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2 text-sm">
            <p><strong>Strategy:</strong> Combines EMAs (12/26/50/200), MACD, RSI, VWAP, OBV, and ATR across multiple timeframes (15m + 1h) to confirm trends before executing trades. Uses a unified scoring system (0-100) as the entry gate.</p>
            <p><strong>Crypto Selection:</strong> Scans ~50 pairs in parallel, prioritizing volume growth, healthy volatility, and trend strength. Filters by minimum quote volume and spread.</p>
            <p><strong>Risk Management:</strong> Automatic ATR-based stop-loss and take-profit. Dynamic trailing stop activation. Kelly Criterion for position sizing. Daily loss limit halts the bot. Post-stop-loss cooldown prevents re-buying falling assets.</p>
            <p><strong>Machine Learning:</strong> RandomForest + GradientBoosting signal filter. Auto-learning pipeline adjusts parameters every 60 minutes based on trade outcomes. Hard guardrails prevent dangerous parameter drift.</p>
            <p><strong>Notifications:</strong> Real-time Telegram alerts for position opens/closes, circuit breaker events, and daily summaries.</p>
          </div>
        </CardContent>
      </Card>

      {/* Risk Parameters */}
      <Card className="glass-card hover:shadow-glow-emerald transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 shadow-lg shadow-emerald-500/30">
                <Shield size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">6. Default Risk Parameters</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Risk Per Trade</p>
              <p className="font-mono text-white/80">0.5% of balance (configurable)</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Leverage</p>
              <p className="font-mono text-white/80">1x (Spot — no margin)</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Stop-Loss</p>
              <p className="font-mono text-white/80">ATR-based, ML-adjusted</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Max Positions</p>
              <p className="font-mono text-white/80">2 simultaneous (configurable)</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Daily Loss Limit</p>
              <p className="font-mono text-white/80">5% — auto-shutdown</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Total Drawdown Cap</p>
              <p className="font-mono text-white/80">15% — halt + Telegram alert</p>
            </div>
          </div>
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
            <p className="font-bold text-rose-400 text-lg">Important Warnings</p>
            <ul className="space-y-2 text-sm text-white/60">
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span><strong className="text-white/80">ALWAYS test on Testnet first</strong> before using real money</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Cryptocurrency trading involves significant risk of loss</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Never invest more than you can afford to lose</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>The bot does not guarantee profits — use at your own risk</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Monitor the bot regularly and review Telegram alerts</span></li>
              <li className="flex items-start gap-2"><span className="text-rose-400 mt-0.5">!</span> <span>Keep API keys secure — never commit .env to version control</span></li>
            </ul>
          </div>
        </div>
      </div>

      {/* Quick Reference */}
      <Card className="glass-card hover:shadow-glow-violet transition-all duration-300">
        <CardHeader>
          <CardTitle asChild className="flex items-center gap-2 text-xl">
            <h2 className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 shadow-lg shadow-violet-500/30">
                <Info size={18} className="text-white" aria-hidden="true" />
              </div>
              <span className="text-white">Quick Reference</span>
            </h2>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Dashboard</p>
              <p className="font-mono text-cyan-400">http://localhost:3000</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">API</p>
              <p className="font-mono text-cyan-400">http://localhost:8000</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Swagger Docs</p>
              <p className="font-mono text-cyan-400">http://localhost:8000/docs</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">MongoDB</p>
              <p className="font-mono text-cyan-400">mongodb://localhost:27017</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Frontend Build</p>
              <p className="font-mono text-cyan-400">npx craco build</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-3">
              <p className="text-xs text-white/40 mb-1">Run Tests</p>
              <p className="font-mono text-cyan-400">pytest tests/ -q</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Instructions;
