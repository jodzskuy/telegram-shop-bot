#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin Web — ZERO DEPENDENCY (hanya pustaka bawaan Python 3).
Versi perbaikan dari app.py/server.py yang lama.

Kenapa versi ini:
- Bug lama: tombol "Simpan Perubahan" muter-muter lalu Internal Server Error karena
  app.py (Flask) butuh storage.py + base.html yang tidak ada, dan server.py punya
  fungsi render() yang rusak (placeholder tidak pernah terisi).
- Versi ini TIDAK butuh Flask / file lain. Cukup: python3 admin_web.py
- Tombol Simpan benar-benar menyimpan ke settings.json (atomic write + error handling),
  jadi tidak ada lagi 500 diam-diam.
- Format & kunci settings.json tetap sama -> tetap kompatibel dengan bot Anda.

Jalankan:
    python3 admin_web.py
    buka http://localhost:5000/login   (password default: jomok123)

Konfigurasi lewat environment variable (opsional):
    ADMIN_WEB_PASSWORD  (default: jomok123)
    WEB_TOKEN           (default: ok)
    PORT                (default: 5000)
    SETTINGS_FILE       (default: ./settings.json di folder yang sama)
"""
import html
import json
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BASE_DIR = os.getenv("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.getenv("SETTINGS_FILE", os.path.join(BASE_DIR, "settings.json"))
PASS = os.getenv("ADMIN_WEB_PASSWORD", "jomok123")
TOKEN = os.getenv("WEB_TOKEN", "ok")
PORT = int(os.getenv("PORT", "5000"))

_write_lock = threading.Lock()

DEFAULTS = {
    "store_name": "Toko Online Mini",
    "currency_id": "Rp",
    "currency_en": "$",
    "idr_per_usd": 16000,
    "welcome_en": "",
    "welcome_id": "",
    "payment_info_en": "",
    "payment_info_id": "",
    "sos_intro_en": "",
    "sos_intro_id": "",
}

TEXT_FIELDS = [
    "store_name", "currency_id", "currency_en",
    "welcome_en", "welcome_id",
    "payment_info_en", "payment_info_id",
    "sos_intro_en", "sos_intro_id",
]


def read_settings():
    data = dict(DEFAULTS)
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data.update(loaded)
    except (json.JSONDecodeError, OSError):
        pass  # file rusak -> pakai default, jangan crash
    return data


def write_settings(data):
    """Tulis atomik supaya file tidak korup kalau proses terputus."""
    dir_name = os.path.dirname(SETTINGS_FILE) or "."
    os.makedirs(dir_name, exist_ok=True)
    with _write_lock:
        fd, tmp = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, SETTINGS_FILE)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise


CSS = """<style>
:root{--border:#e2e2e6;--muted:#6b7280;--accent:#2563eb;}
*{box-sizing:border-box;}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f5f6f8;margin:0;color:#111;}
.wrap{max-width:860px;margin:0 auto;padding:28px 18px;}
.card{background:#fff;border:1px solid var(--border);border-radius:12px;}
h1{font-size:22px;}
label{display:block;font-size:13px;color:var(--muted);margin-bottom:5px;}
input,textarea{width:100%;padding:9px 11px;border:1px solid var(--border);border-radius:8px;font:inherit;background:#fff;}
textarea{resize:vertical;}
fieldset{border:1px solid var(--border);border-radius:10px;padding:14px;margin:0;}
legend{padding:0 6px;font-size:13px;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.grid3{display:grid;grid-template-columns:1fr 1fr 1.4fr;gap:12px;}
.muted{color:var(--muted);}
button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:11px 20px;font:inherit;font-weight:600;cursor:pointer;}
button:hover{filter:brightness(1.05);}
.flash{padding:10px 14px;border-radius:8px;margin-bottom:14px;font-size:14px;}
.flash.ok{background:#e7f6ec;color:#116631;border:1px solid #bfe6cb;}
.flash.err{background:#fdecec;color:#a11;border:1px solid #f5c2c2;}
.toolbar{display:flex;gap:6px;margin-bottom:6px;flex-wrap:wrap;}
.tbtn{background:#eef2ff;color:#334;border:1px solid #d5dbf5;border-radius:6px;padding:4px 10px;font-size:12px;font-weight:600;cursor:pointer;}
.tbtn:hover{background:#e0e7ff;}
.pv-label{font-size:12px;margin:8px 0 3px;}
.pv{background:#f8fafc;border:1px dashed var(--border);border-radius:8px;padding:8px 11px;font-size:14px;min-height:20px;white-space:pre-wrap;word-break:break-word;}
.pv code,.pv pre{background:#eceff3;padding:1px 5px;border-radius:4px;font-family:ui-monospace,Menlo,Consolas,monospace;}
@media(max-width:640px){.grid2,.grid3{grid-template-columns:1fr;}}
</style>"""

TOOLBAR_JS = """<script>
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function pv(ta){
  var el=document.getElementById(ta.id+'_pv'); if(!el)return;
  var out=esc(ta.value);
  out = out.replace(/\\*(.+?)\\*/g, '<b>$1</b>');
  out = out.replace(/_(.+?)_/g, '<i>$1</i>');
  out = out.replace(/`(.+?)`/g, '<code>$1</code>');
  el.innerHTML=out||'<span class="muted">(kosong)</span>';
}
document.querySelectorAll('.tbtn').forEach(function(btn){
  btn.addEventListener('click',function(){
    var ta=document.getElementById(btn.dataset.t);
    var open=btn.dataset.open, close=btn.dataset.close;
    var s=ta.selectionStart,e=ta.selectionEnd;
    var sel=ta.value.substring(s,e)||'teks';
    ta.value=ta.value.substring(0,s)+open+sel+close+ta.value.substring(e);
    ta.selectionStart=s+open.length; ta.selectionEnd=s+open.length+sel.length;
    ta.focus(); pv(ta);
  });
});
document.querySelectorAll('textarea').forEach(function(ta){pv(ta);});
</script>"""


def page(title, body):
    return ("<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>" + html.escape(title) + "</title>" + CSS +
            "</head><body><div class='wrap'>" + body + "</div></body></html>")


def login_page(msg=""):
    flash = "<div class='flash err'>" + html.escape(msg) + "</div>" if msg else ""
    body = ("<div class='card' style='max-width:380px;margin:40px auto;padding:24px;'>"
            "<h1 style='margin-top:0;'>Masuk</h1>" + flash +
            "<form method='post' action='/login' style='display:grid;gap:14px;'>"
            "<div><label>Password</label>"
            "<input type='password' name='password' autofocus></div>"
            "<div><button>Masuk</button></div></form></div>")
    return page("Login", body)


def field_input(name, value):
    return ("<input name='" + name + "' value='" +
            html.escape(str(value), quote=True) + "'>")


def field_textarea(name, value, rows):
    tid = "ta_" + name
    toolbar = (
        "<div class='toolbar'>"
        "<button type='button' class='tbtn' data-t='" + tid + "' data-open='*' data-close='*'>Bold</button>"
        "<button type='button' class='tbtn' data-t='" + tid + "' data-open='_' data-close='_'>Miring</button>"
        "<button type='button' class='tbtn' data-t='" + tid + "' data-open='`' data-close='`'>Mono</button>"
        "</div>"
    )
    return (toolbar +
            "<textarea id='" + tid + "' name='" + name + "' rows='" + str(rows) +
            "' oninput='pv(this)'>" + html.escape(str(value)) + "</textarea>"
            "<div class='pv-label muted'>Pratinjau di Telegram:</div>"
            "<div class='pv' id='" + tid + "_pv'></div>")


def settings_page(s, msg=""):
    flash = "<div class='flash ok'>" + html.escape(msg) + "</div>" if msg else ""
    action = "/settings?" + urlencode({"token": TOKEN})
    body = (
        "<h1>Tampilan Bot &amp; Bahasa</h1>"
        "<p class='muted' style='margin-top:-8px;margin-bottom:18px;'>"
        "Atur teks bot dalam 2 bahasa (English default + Indonesia) dan mata uang. "
        "Perubahan langsung dipakai bot tanpa restart.</p>"
        "<div class='flash' style='background:#eef2ff;color:#334;border:1px solid #d5dbf5;'>"
        "Tip: blok teks lalu klik <b>Mono / Salin</b> untuk alamat wallet — di Telegram jadi "
        "monospace &amp; bisa <b>disalin sekali ketuk</b>. Pakai <b>Bold</b> untuk tebal. "
        "Tekan Enter untuk baris baru (jangan ketik &lt;br&gt;).</div>" + flash +
        "<form method='post' action='" + action + "' class='card' "
        "style='padding:20px;display:grid;gap:18px;'>"
        "<div><label>Nama Toko</label>" + field_input("store_name", s["store_name"]) + "</div>"
        "<fieldset><legend class='muted'>Mata Uang (otomatis mengikuti bahasa)</legend>"
        "<div class='grid3'>"
        "<div><label>Simbol Indonesia</label>" + field_input("currency_id", s["currency_id"]) + "</div>"
        "<div><label>Simbol English</label>" + field_input("currency_en", s["currency_en"]) + "</div>"
        "<div><label>Kurs: 1 USD = ... Rupiah</label>" + field_input("idr_per_usd", s["idr_per_usd"]) + "</div>"
        "</div></fieldset>"
        "<fieldset><legend class='muted'>Pesan Sambutan /start (pakai {store} untuk nama toko)</legend>"
        "<div class='grid2'>"
        "<div><label>English</label>" + field_textarea("welcome_en", s["welcome_en"], 3) + "</div>"
        "<div><label>Indonesia</label>" + field_textarea("welcome_id", s["welcome_id"], 3) + "</div>"
        "</div></fieldset>"
        "<fieldset><legend class='muted'>Detail Pembayaran (tampil saat checkout)</legend>"
        "<div class='grid2'>"
        "<div><label>English</label>" + field_textarea("payment_info_en", s["payment_info_en"], 6) + "</div>"
        "<div><label>Indonesia</label>" + field_textarea("payment_info_id", s["payment_info_id"], 6) + "</div>"
        "</div></fieldset>"
        "<fieldset><legend class='muted'>Teks Pembuka Bantuan / SOS</legend>"
        "<div class='grid2'>"
        "<div><label>English</label>" + field_textarea("sos_intro_en", s["sos_intro_en"], 2) + "</div>"
        "<div><label>Indonesia</label>" + field_textarea("sos_intro_id", s["sos_intro_id"], 2) + "</div>"
        "</div></fieldset>"
        "<div><button>Simpan Perubahan</button></div>"
        "<input type='hidden' name='token' value='" + html.escape(TOKEN, quote=True) + "'>"
        "</form>" + TOOLBAR_JS)
    return page("Pengaturan", body)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # senyapkan log default

    # ---- helpers ----
    def _query(self):
        return parse_qs(urlparse(self.path).query)

    def _token_ok(self, extra=None):
        tok = self._query().get("token", [None])[0]
        if tok is None and extra:
            tok = extra.get("token")
        return tok == TOKEN

    def _form(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length).decode("utf-8") if length else ""
        return {k: v[0] for k, v in parse_qs(body, keep_blank_values=True).items()}

    def _send_html(self, text, code=200):
        data = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, loc):
        self.send_response(303)
        self.send_header("Location", loc)
        self.send_header("Content-Length", "0")
        self.end_headers()

    # ---- routes ----
    def do_GET(self):
        try:
            path = urlparse(self.path).path
            if path == "/healthz":
                return self._send_html("OK")
            if path == "/login":
                return self._send_html(login_page())
            if not self._token_ok():
                return self._redirect("/login")
            if path in ("/", "/settings"):
                q = self._query()
                msg = q.get("msg", [""])[0]
                return self._send_html(settings_page(read_settings(), msg))
            return self._send_html(page("404", "<h1>404</h1>"), 404)
        except Exception as e:
            return self._send_html(page("Error", "<h1>Terjadi error</h1><pre>" +
                                        html.escape(str(e)) + "</pre>"), 500)

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            form = self._form()
            if path == "/login":
                if form.get("password") == PASS:
                    return self._redirect("/settings?" + urlencode({"token": TOKEN}))
                return self._send_html(login_page("Password salah."))
            if not self._token_ok(form):
                return self._redirect("/login")
            if path == "/settings":
                try:
                    s = read_settings()
                    for k in TEXT_FIELDS:
                        if k in form:
                            s[k] = form.get(k, "").strip()
                    digits = "".join(c for c in form.get("idr_per_usd", "") if c.isdigit())
                    if digits:
                        s["idr_per_usd"] = int(digits)
                    write_settings(s)
                    msg = "Perubahan tersimpan."
                except Exception as e:
                    msg = "Gagal menyimpan: " + str(e)
                return self._redirect("/settings?" + urlencode({"token": TOKEN, "msg": msg}))
            return self._send_html(page("404", "<h1>404</h1>"), 404)
        except Exception as e:
            return self._send_html(page("Error", "<h1>Terjadi error</h1><pre>" +
                                        html.escape(str(e)) + "</pre>"), 500)


def main():
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Admin web berjalan di http://localhost:%d/login  (password: %s)" % (PORT, PASS))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
