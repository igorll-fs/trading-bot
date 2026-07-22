#!/usr/bin/env python3
"""Proxy Threading: frontend + API unificados com autenticação."""
import http.server
import urllib.request
import urllib.error
import os
import base64
import secrets
from datetime import datetime, timedelta

FRONTEND = os.path.expanduser("~/Área de trabalho/bottrading/frontend/build")
BACKEND = "http://localhost:8000"
PORT = 8080
USER = os.environ.get("PROXY_USER", "admin")
PASS = os.environ.get("PROXY_PASS", secrets.token_urlsafe(10))
SESSION_TTL = timedelta(hours=8)
sessions = {}
_started = datetime.now()

LOGIN_HTML = f"""<!DOCTYPE html>
<html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Inter,system-ui;background:#0a0a0a;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh}}
.card{{background:#111;border:1px solid#222;border-radius:16px;padding:40px;width:100%;max-width:380px;text-align:center}}
h1{{font-size:20px;margin-bottom:8px}}p{{color:#888;font-size:13px;margin-bottom:24px}}
input{{width:100%;padding:12px;margin-bottom:12px;background:#1a1a1a;border:1px solid#333;border-radius:8px;color:#fff;font-size:14px}}
input:focus{{outline:none;border-color:#3b82f6}}button{{width:100%;padding:12px;background:#3b82f6;border:none;border-radius:8px;color:#fff;font-size:14px;font-weight:600;cursor:pointer}}
button:hover{{background:#2563eb}}.error{{color:#ef4444;font-size:12px;margin-top:8px}}
</style></head><body><div class="card"><h1>🔐 Trading Bot</h1><p>Dashboard protegido</p>
<form method="post" action="/login"><input type="password" name="pass" placeholder="Senha" autofocus>
<button type="submit">Entrar</button></form></div></body></html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND, **kwargs)

    def _authed(self):
        cookie = self.headers.get("Cookie", "")
        for c in cookie.split(";"):
            if c.strip().startswith("session="):
                tok = c.strip().split("=", 1)[1]
                if tok in sessions and datetime.now() - sessions[tok] < SESSION_TTL:
                    return True
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Basic "):
            try:
                u, p = base64.b64decode(auth[6:]).decode().split(":", 1)
                return u == USER and p == PASS
            except: pass
        return False

    def do_GET(self):
        if self.path.startswith("/api/"):
            if not self._authed():
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="TradingBot"')
                self.end_headers()
                return
            self._proxy()
        elif self.path == "/login":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(LOGIN_HTML.encode())
        elif not self._authed():
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            params = dict(p.split("=", 1) for p in body.split("&") if "=" in p)
            if params.get("pass") == PASS:
                tok = secrets.token_urlsafe(32)
                sessions[tok] = datetime.now()
                expired = [t for t, d in sessions.items() if datetime.now() - d > SESSION_TTL]
                for t in expired: del sessions[t]
                self.send_response(302)
                self.send_header("Set-Cookie", f"session={tok}; Path=/; HttpOnly; SameSite=Lax; Max-Age={int(SESSION_TTL.total_seconds())}")
                self.send_header("Location", "/")
                self.end_headers()
            else:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
        elif self.path.startswith("/api/"):
            if not self._authed():
                self.send_response(401)
                self.end_headers()
                return
            self._proxy()
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _proxy(self):
        try:
            url = f"{BACKEND}{self.path}"
            body = None
            if self.command == "POST":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else None
            req = urllib.request.Request(url, data=body, method=self.command)
            for k, v in self.headers.items():
                if k.lower() not in ("host", "connection", "cookie", "authorization"):
                    req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                self.send_header("Access-Control-Allow-Origin", "*")
                for k, v in resp.headers.items():
                    if k.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            try:
                self.send_error(502, str(e))
            except:
                pass

    def log_message(self, format, *args):
        pass  # silencioso

if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.daemon_threads = True
    print(f"Proxy Threading :{PORT} | {USER}:{PASS}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
