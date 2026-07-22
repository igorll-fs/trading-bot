#!/usr/bin/env python3
"""Proxy unificado: frontend + API num único túnel Cloudflare com autenticação."""
import http.server
import urllib.request
import urllib.error
import os
import sys
import base64
import hashlib
import secrets
from datetime import datetime, timedelta

FRONTEND_DIR = os.path.expanduser("~/Área de trabalho/bottrading/frontend/build")
BACKEND_URL = "http://localhost:8000"
PORT = 8080

# Autenticação — defina USER e PASS ou gere automático
USER = os.environ.get("PROXY_USER", "admin")
PASS = os.environ.get("PROXY_PASS", secrets.token_urlsafe(10))
SESSION_TIMEOUT = timedelta(hours=8)
_sessions: dict[str, datetime] = {}

def check_auth(handler) -> bool:
    """Verifica Basic Auth ou token de sessão."""
    # Cookie de sessão
    cookie = handler.headers.get("Cookie", "")
    for c in cookie.split(";"):
        c = c.strip()
        if c.startswith("session="):
            token = c.split("=", 1)[1]
            if token in _sessions:
                if datetime.now() - _sessions[token] < SESSION_TIMEOUT:
                    return True
                del _sessions[token]
            return False

    # Basic Auth
    auth = handler.headers.get("Authorization", "")
    if auth.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth[6:]).decode()
            u, p = decoded.split(":", 1)
            if u == USER and p == PASS:
                return True
        except Exception:
            pass
    return False

LOGIN_PAGE = f"""<!DOCTYPE html>
<html lang="pt">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trading Bot — Login</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:Inter,system-ui;background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh}}
.card{{background:#111;border:1px solid#222;border-radius:16px;padding:40px;width:100%;max-width:380px;text-align:center}}
h1{{font-size:20px;margin-bottom:8px}}
p{{color:#888;font-size:13px;margin-bottom:24px}}
input{{width:100%;padding:12px;margin-bottom:12px;background:#1a1a1a;border:1px solid#333;border-radius:8px;color:#fff;font-size:14px}}
input:focus{{outline:none;border-color:#3b82f6}}
button{{width:100%;padding:12px;background:#3b82f6;border:none;border-radius:8px;color:#fff;font-size:14px;font-weight:600;cursor:pointer}}
button:hover{{background:#2563eb}}
.error{{color:#ef4444;font-size:12px;margin-top:8px}}
</style></head>
<body>
<div class="card">
<h1>🔐 Trading Bot</h1>
<p>Dashboard protegido</p>
<form method="post" action="/login">
<input type="password" name="pass" placeholder="Senha de acesso" autofocus>
<button type="submit">Entrar</button>
<p class="error">{{error}}</p>
</form>
</div></body></html>"""

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/login":
            self._serve_login()
            return
        if not check_auth(self):
            self._redirect_login()
            return
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/login":
            self._handle_login()
            return
        if not check_auth(self):
            self._redirect_login()
            return
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _serve_login(self, error=""):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(LOGIN_PAGE.replace("{{error}}", error).encode())

    def _redirect_login(self):
        self.send_response(302)
        self.send_header("Location", "/login")
        self.end_headers()

    def _handle_login(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        params = dict(p.split("=", 1) for p in body.split("&") if "=" in p)
        password = params.get("pass", "")

        if password == PASS:
            token = secrets.token_urlsafe(32)
            _sessions[token] = datetime.now()
            # Limpa sessões expiradas
            expired = [t for t, d in _sessions.items() if datetime.now() - d > SESSION_TIMEOUT]
            for t in expired:
                del _sessions[t]

            self.send_response(302)
            self.send_header("Set-Cookie", f"session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={int(SESSION_TIMEOUT.total_seconds())}")
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self._serve_login("Senha incorreta")

    def _proxy(self):
        try:
            url = f"{BACKEND_URL}{self.path}"
            body = None
            if self.command == "POST":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else 0

            req = urllib.request.Request(url, data=body, method=self.command)
            for key, val in self.headers.items():
                if key.lower() not in ("host", "connection", "cookie", "authorization"):
                    req.add_header(key, val)

            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                self.send_header("Access-Control-Allow-Origin", "*")
                for key, val in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(resp.read())

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_error(502, str(e))

if __name__ == "__main__":
    print(f"🔀 Proxy: :{PORT} → Frontend + Backend")
    print(f"🔐 User: {USER}  |  Pass: {PASS}")
    print(f"⏰ Sessão: {SESSION_TIMEOUT.total_seconds()/3600:.0f}h")
    http.server.HTTPServer(("0.0.0.0", PORT), ProxyHandler).serve_forever()
