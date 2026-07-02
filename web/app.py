import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, jsonify, redirect, render_template, request

import storage
app = Flask(__name__)

PASS = os.getenv("ADMIN_WEB_PASSWORD", "jomok123")


@app.route("/")
def home():
    if not request.args.get("token"):
        return redirect("/login")
    return render_template("orders.html", store_name=storage.get_settings()["store_name"],
                           orders=storage.list_orders(), counts=storage.order_counts(),
                           statuses=storage.ORDER_STATUSES, bot_stats=storage.stats(), token="ok")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST" and request.form.get("password") == PASS:
        return redirect("/?token=ok")
    return render_template("login.html", store_name=storage.get_settings()["store_name"])


@app.route("/products")
def products():
    if not request.args.get("token"):
        return redirect("/login")
    return render_template("products.html", store_name=storage.get_settings()["store_name"],
                           products=storage.list_products(), token="ok")


@app.route("/products/add", methods=["POST"])
def products_add():
    name = request.form.get("name","").strip()
    desc = request.form.get("description","").strip()
    cat = request.form.get("category","Umum").strip() or "Umum"
    price = int("".join(c for c in request.form.get("price","0") if c.isdigit()) or 0)
    url = request.form.get("photo_url","").strip() or None
    if name: storage.add_product(name, desc, price, cat, photo_url=url)
    return redirect("/products?token=ok")


@app.route("/products/delete/<int:pid>", methods=["POST"])
def products_delete(pid):
    storage.delete_product(pid)
    return redirect("/products?token=ok")


@app.route("/products/edit/<int:pid>", methods=["POST"])
def products_edit(pid):
    fields = {"name": request.form.get("name","").strip(),
              "category": request.form.get("category","Umum").strip() or "Umum",
              "description": request.form.get("description","").strip(),
              "photo_url": request.form.get("photo_url","").strip() or None}
    pr = "".join(c for c in request.form.get("price","") if c.isdigit())
    if pr: fields["price"] = int(pr)
    if fields["name"]: storage.update_product(pid, fields)
    return redirect("/products?token=ok")


@app.route("/orders/status/<int:oid>", methods=["POST"])
def order_status(oid):
    storage.update_order_status(oid, request.form.get("status", "Baru"))
    return redirect("/?token=ok")


@app.route("/settings", methods=["GET","POST"])
def settings_view():
    if not request.args.get("token") and request.method == "GET":
        return redirect("/login")
    if request.method == "POST":
        rate = "".join(c for c in request.form.get("idr_per_usd","") if c.isdigit())
        fields = {k: request.form.get(k,"") for k in [
            "store_name","currency_id","currency_en","welcome_en","welcome_id",
            "payment_info_en","payment_info_id","sos_intro_en","sos_intro_id"]}
        storage.update_settings(fields)
        if rate: storage.update_settings({"idr_per_usd": int(rate)})
        return redirect("/settings?token=ok")
    return render_template("settings.html", store_name=storage.get_settings()["store_name"],
                           s=storage.get_settings(), token="ok")


# Rupiah filter
@app.template_global()
def rupiah(v):
    try: n = int(v)
    except: return v
    return storage.format_price(n, "id")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
