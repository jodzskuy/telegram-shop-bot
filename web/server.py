#!/usr/bin/env python3
"""Web admin zero-dependency — langsung baca data dari storage."""
import http.server
import json
import os
import sys
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import storage

PASS = os.getenv("ADMIN_WEB_PASSWORD", "jomok123")
TOKEN = os.getenv("WEB_TOKEN", "rahasia123")
PORT = int(os.getenv("PORT", 5000))


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, data, ct="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.end_headers()
        if isinstance(data, str):
            self.wfile.write(data.encode())
        else:
            self.wfile.write(data)

    def _redirect(self, path):
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def _ok(self):
        t = self._get_token()
        return t == TOKEN

    def _get_token(self):
        q = parse_qs(urlparse(self.path).query)
        return q.get("token", [None])[0]

    def _render(self, template, **kw):
        html = self._load(f"/app/web/templates/{template}")
        for k, v in kw.items():
            html = html.replace("{{ " + k + " }}", str(v))
        return html

    def _load(self, path):
        try:
            with open(path) as f:
                return f.read()
        except:
            return f"<h1>File not found: {path}</h1>"

    def do_GET(self):
        if self.path == "/login" or (self.path.startswith("/login") and "?" not in self.path):
            return self._send(self._load("web/templates/login.html").replace("{{ store_name }}", storage.get_settings()["store_name"]))
        if self.path.startswith("/login?"):
            return self._send(self._load("web/templates/login.html").replace("{{ store_name }}", storage.get_settings()["store_name"]))
        if not self._ok():
            return self._redirect("/login")
        if self.path == "/" or self.path.startswith("/?"):
            return self._send("OK - Web Admin. Use /login")
        if self.path.startswith("/logout"):
            return self._redirect("/login")
        self._send("404 Not Found", code=404)

    def do_POST(self):
        ct = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        
        # parse form data
        params = parse_qs(body)
        form = {k: v[0] for k, v in params.items()}
        
        token = form.get("token", "") or self._get_token()
        if token != TOKEN:
            return self._redirect("/login")
        
        if self.path == "/login":
            if form.get("password") == PASS:
                return self._redirect(f"/?token={TOKEN}")
            return self._redirect("/login")
        
        if self.path == "/settings":
            rate = "".join(c for c in form.get("idr_per_usd","") if c.isdigit())
            storage.update_settings({
                "store_name": form.get("store_name","").strip(),
                "currency_id": form.get("currency_id","Rp").strip() or "Rp",
                "currency_en": form.get("currency_en","$").strip() or "$",
                "idr_per_usd": int(rate) if rate else 16000,
                "welcome_en": form.get("welcome_en",""),
                "welcome_id": form.get("welcome_id",""),
                "payment_info_en": form.get("payment_info_en",""),
                "payment_info_id": form.get("payment_info_id",""),
                "sos_intro_en": form.get("sos_intro_en",""),
                "sos_intro_id": form.get("sos_intro_id",""),
            })
            return self._redirect(f"/settings?token={TOKEN}")
        
        self._send("404", code=404)


if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    s.serve_forever()
