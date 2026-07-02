#!/usr/bin/env python3
"""Web admin zero-dep — langsung baca/tulis JSON, ga pake storage.py."""
import http.server
import json
import os
import re
from urllib.parse import parse_qs, urlparse, urlencode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(ROOT, "settings.json")
TEMPLATES = os.path.join(ROOT, "web", "templates")
PASS = os.getenv("ADMIN_WEB_PASSWORD", "jomok123")
TOKEN = os.getenv("WEB_TOKEN", "rahasia123")
PORT = int(os.getenv("PORT", 5000))


def read_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"store_name": "Toko Online Mini", "currency_id": "Rp", "currency_en": "$",
                "idr_per_usd": 16000, "welcome_en": "", "welcome_id": "",
                "payment_info_en": "", "payment_info_id": "", "sos_intro_en": "", "sos_intro_id": ""}
    with open(SETTINGS_FILE) as f:
        return json.load(f)


def write_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)


def load_template(name):
    path = os.path.join(TEMPLATES, name)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return f"<h1>Template {name} not found</h1>"


def render(template, **kw):
    html = load_template(template)
    for k, v in kw.items():
        html = html.replace("{{ " + k + " }}", str(v))
    # Handle {% block %} dan {% extends %} — simple for now
    return html


class Handler(http.server.BaseHTTPRequestHandler):
    def q(self):
        return parse_qs(urlparse(self.path).query)

    def ok(self):
        return self.q().get("token", [None])[0] == TOKEN

    def redirect(self, loc):
        self.send_response(302)
        self.send_header("Location", loc)
        self.end_headers()

    def html(self, text, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode())

    def form(self):
        ct = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        return {k: v[0] for k, v in parse_qs(body).items()}

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/login":
            return self.html(render("login.html", store_name=read_settings()["store_name"]))
        if not self.ok():
            return self.redirect("/login")
        # Settings page
        if p == "/settings":
            s = read_settings()
            h = load_template("settings.html")
            # Simple template rendering
            for k, v in s.items():
                h = h.replace("{{ s." + k + " }}", str(v))
            h = h.replace("{{ token }}", TOKEN)
            h = h.replace("{{ store_name }}", s["store_name"])
            h = h.replace("{{ active }}", "settings")
            return self.html(h)
        # Products page
        if p == "/products":
            return self.html("<h1>Products</h1><p>Coming soon</p>")
        # Home
        return self.html("<h1>Admin</h1><p><a href='/settings?token=" + TOKEN + "'>Settings</a></p>")

    def do_POST(self):
        p = urlparse(self.path).path
        f = self.form()
        t = f.get("token", "") or self.q().get("token", [""])[0]
        if t != TOKEN and p != "/login":
            return self.redirect("/login")
        if p == "/login":
            if f.get("password") == PASS:
                return self.redirect("/?token=" + TOKEN)
            return self.redirect("/login")
        if p == "/settings":
            rate = "".join(c for c in f.get("idr_per_usd", "") if c.isdigit())
            s = read_settings()
            for k in ["store_name", "currency_id", "currency_en", "welcome_en", "welcome_id",
                       "payment_info_en", "payment_info_id", "sos_intro_en", "sos_intro_id"]:
                if k in f:
                    s[k] = f[k].strip()
            if rate:
                s["idr_per_usd"] = int(rate)
            write_settings(s)
            return self.redirect("/settings?token=" + TOKEN)
        self.html("Not found", 404)


if __name__ == "__main__":
    srv = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Web admin at http://0.0.0.0:{PORT}")
    srv.serve_forever()
