#!/usr/bin/env python3
"""Web admin untuk Bot Toko Telegram - mode simple."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for
import storage

load_dotenv(os.path.join(ROOT, ".env"))
PASS = os.getenv("ADMIN_WEB_PASSWORD", "admin123")
TOKEN = os.getenv("WEB_TOKEN", "rahasia123")

app = Flask(__name__)

def cek():
    return request.args.get("token") == TOKEN or request.form.get("token") == TOKEN

@app.route("/")
def home():
    if not cek():
        return redirect(url_for("login"))
    return render_template("orders.html", store_name=storage.get_settings()["store_name"], active="orders",
                           orders=storage.list_orders(), counts=storage.order_counts(),
                           statuses=storage.ORDER_STATUSES, bot_stats=storage.stats(), token=TOKEN)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST" and request.form.get("password") == PASS:
        return redirect(url_for("home", token=TOKEN))
    return render_template("login.html", store_name=storage.get_settings()["store_name"])

@app.route("/logout")
def logout():
    return redirect(url_for("login"))

@app.route("/products")
def products():
    if not cek(): return redirect(url_for("login"))
    try:
        return render_template("products.html", store_name=storage.get_settings()["store_name"], active="products",
                               products=storage.list_products(), token=TOKEN)
    except Exception as e:
        return f"ERROR products: {e}", 500

@app.route("/products/add", methods=["POST"])
def products_add():
    if not cek(): return redirect(url_for("login"))
    name = request.form.get("name", "").strip()
    desc = request.form.get("description", "").strip()
    cat = request.form.get("category", "Umum").strip() or "Umum"
    price = int("".join(c for c in request.form.get("price", "0") if c.isdigit()) or 0)
    url = request.form.get("photo_url", "").strip() or None
    if name: storage.add_product(name, desc, price, cat, photo_url=url)
    return redirect(url_for("products", token=TOKEN))

@app.route("/products/delete/<int:pid>", methods=["POST"])
def products_delete(pid):
    if not cek(): return redirect(url_for("login"))
    storage.delete_product(pid)
    return redirect(url_for("products", token=TOKEN))

@app.route("/products/edit/<int:pid>", methods=["POST"])
def products_edit(pid):
    if not cek(): return redirect(url_for("login"))
    fields = {"name": request.form.get("name","").strip(), "category": request.form.get("category","Umum").strip() or "Umum",
              "description": request.form.get("description","").strip(), "photo_url": request.form.get("photo_url","").strip() or None}
    pr = "".join(c for c in request.form.get("price","") if c.isdigit())
    if pr: fields["price"] = int(pr)
    if fields["name"]: storage.update_product(pid, fields)
    return redirect(url_for("products", token=TOKEN))

@app.route("/orders/status/<int:oid>", methods=["POST"])
def order_status(oid):
    if not cek(): return redirect(url_for("login"))
    storage.update_order_status(oid, request.form.get("status", "Baru"))
    return redirect(url_for("home", token=TOKEN))

@app.route("/settings", methods=["GET","POST"])
def settings_view():
    if not cek(): return redirect(url_for("login"))
    if request.method == "POST":
        try:
            rate = "".join(c for c in request.form.get("idr_per_usd","") if c.isdigit())
            storage.update_settings({
                "store_name": request.form.get("store_name","").strip(),
                "currency_id": request.form.get("currency_id","Rp").strip() or "Rp",
                "currency_en": request.form.get("currency_en","$").strip() or "$",
                "idr_per_usd": int(rate) if rate else 16000,
                "welcome_en": request.form.get("welcome_en",""),
                "welcome_id": request.form.get("welcome_id",""),
                "payment_info_en": request.form.get("payment_info_en",""),
                "payment_info_id": request.form.get("payment_info_id",""),
                "sos_intro_en": request.form.get("sos_intro_en",""),
                "sos_intro_id": request.form.get("sos_intro_id",""),
            })
            return redirect(url_for("settings_view", token=TOKEN))
        except Exception as e:
            return f"ERROR: {e}", 500
    return render_template("settings.html", store_name=storage.get_settings()["store_name"],
                           active="settings", s=storage.get_settings(), token=TOKEN)

@app.route("/api/orders")
def api_orders():
    if not cek(): return redirect(url_for("login"))
    return jsonify(storage.list_orders())


# --- template filter rupiah ---
def rupiah(v):
    try: n = int(v)
    except: return v
    return storage.format_price(n, "id")
app.jinja_env.filters["rupiah"] = rupiah

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
