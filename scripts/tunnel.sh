#!/bin/bash
# Cloudflare Tunnel para Trading Bot Dashboard
# Uso: bash scripts/tunnel.sh
cd "$(dirname "$0")/.."
PASS="${PROXY_PASS:-botmaster2026}"

pkill -f "cloudflared tunnel" 2>/dev/null
pkill -f "proxy2.py" 2>/dev/null
sleep 1

echo "🔐 Iniciando proxy (Threading)..."
PROXY_PASS="$PASS" python3 scripts/proxy2.py > /tmp/proxy2.log 2>&1 &
sleep 2

echo "🔗 Iniciando Cloudflare..."
cloudflared tunnel --url http://localhost:8080 --no-autoupdate > /tmp/cf-tunnel.log 2>&1 &
sleep 8

URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cf-tunnel.log | head -1)
echo ""
echo "═══════════════════════════════════"
echo "  ✅ $URL"
echo "  🔑 admin / $PASS"
echo "═══════════════════════════════════"
