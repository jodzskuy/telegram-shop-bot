#!/usr/bin/env python3
"""Bot Toko Telegram sederhana (python-telegram-bot v22, async).

Dua bahasa: English (default) + Bahasa Indonesia. Pelanggan bisa ganti bahasa
kapan saja lewat tombol \U0001F310 Language/Bahasa atau /language. Pilihan bahasa
disimpan per pengguna (users.json) sehingga tetap sinkron antar sesi.

Mata uang mengikuti bahasa: harga dasar disimpan dalam Rupiah, dan saat bahasa
English dipilih harga otomatis dikonversi ke USD memakai kurs (settings.idr_per_usd).

Alur pelanggan:
  /start -> pilih bahasa (sekali) -> menu -> telusuri produk -> keranjang
  -> Checkout -> bot tampilkan pembayaran -> "Saya sudah bayar"
  -> kirim bukti (Order ID / TX Hash / screenshot) -> "sedang diproses"
  -> admin diberi tahu + tombol "Kirim detail produk" -> pesanan Selesai.
"""
import logging
import os
import time
from collections import defaultdict

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters)

import storage
from i18n import t, LANG_NAMES

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "")  # @username atau ID negatif

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SOS_MSG = 10
AP_NAME, AP_DESC, AP_PHOTO, AP_PRICE, AP_CONFIRM = range(20, 25)
PROOF = 30
FULFILL = 40

SOS_MAX_PER_WINDOW = 3
SOS_WINDOW_SECONDS = 900
SOS_COOLDOWN_SECONDS = 20
_sos_history = defaultdict(list)


def lang_of(update):
    u = update.effective_user
    return storage.get_user_lang(u.id) if u else "en"


def price(amount, lang):
    return storage.format_price(amount, lang)


def is_admin(update):
    return update.effective_user is not None and update.effective_user.id == ADMIN_ID


def force_sub_bot_on():
    return bool(FORCE_SUB_CHANNEL)


async def check_sub_and_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Cek apakah user udah pernah verify force subscribe (trust-based).
    Returns True kalo udah pernah / skip, False kalo belum (tampilin pesan)."""
    uid = update.effective_user.id
    if not force_sub_bot_on():
        return True  # fitur nonaktif
    if uid == ADMIN_ID:
        return True
    # Udah pernah verify sebelumnya
    if storage.is_force_sub_ok(uid):
        return True
    # Belum — tampilkan pesan
    lang = storage.get_user_lang(uid) if storage.is_lang_set(uid) else "en"
    invite_link = f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}"
    text = t(lang, "force_sub_required")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "force_sub_join"), url=invite_link)],
        [InlineKeyboardButton(t(lang, "force_sub_check"), callback_data="force_sub_check")],
    ])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb)
    elif update.message:
        await update.message.reply_text(text, reply_markup=kb)
    return False


def welcome_text(lang):
    s = storage.get_settings()
    key = "welcome_id" if lang == "id" else "welcome_en"
    return s[key].replace("{store}", s["store_name"])


def _fmt_int(n):
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


def _esc(s):
    """Escape + parse format: *bold* -> <b>bold</b>, `code` -> <code>code</code>."""
    import re
    text = str(s)
    # Escape HTML dulu
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Parse *bold* -> <b>bold</b>
    text = re.sub(r'\*(.+?)\*', r'<b>\1</b>', text)
    # Parse `code` -> <code>code</code>
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def _card(rows):
    """Kartu monospace rapi (kolom label sejajar) untuk tampilan modern."""
    w = max((len(lbl) for lbl, _ in rows), default=0)
    body = "\n".join(f"{lbl.ljust(w)}   {val}" for lbl, val in rows)
    return "<pre>" + _esc(body) + "</pre>"


def stats_block(update, lang):
    """Kartu STATISTIK BOT + INFORMASI AKUN (tampil saat /start).

    Dikirim dengan parse_mode=HTML: judul tebal + blok <pre> monospace rapi.
    """
    st = storage.stats()
    s = storage.get_settings()
    u = update.effective_user
    uname = ("@" + u.username) if (u and u.username) else "-"
    uid = u.id if u else "-"
    spent = storage.user_total_spent(u.id) if u else 0
    stat_rows = [
        (t(lang, "stat_sold"), f"{_fmt_int(st['sold_pcs'])} {t(lang, 'stat_pcs')}"),
        (t(lang, "stat_users"), _fmt_int(st["registered_users"])),
    ]
    acct_rows = [
        (t(lang, "acct_id"), uid),
        (t(lang, "acct_username"), uname),
        (t(lang, "acct_spent"), price(spent, lang)),
    ]
    rule = "\u2501" * 18
    return (
        f"\U0001F6CD\uFE0F <b>{_esc(s['store_name'])}</b>\n"
        f"{rule}\n"
        f"<b>{_esc(t(lang, 'stats_title'))}</b>\n"
        f"{_card(stat_rows)}\n"
        f"<b>{_esc(t(lang, 'acct_title'))}</b>\n"
        f"{_card(acct_rows)}"
    )


def home_text(update, lang):
    """Kartu statistik + sapaan menu utama (dipakai di /start dan menu)."""
    return stats_block(update, lang) + "\n\n" + _esc(welcome_text(lang))


def _grid(buttons, cols=2):
    """Susun daftar tombol menjadi grid rapi (default 2 kolom)."""
    return [buttons[i:i + cols] for i in range(0, len(buttons), cols)]


def menu_keyboard(update, lang):
    btns = [
        InlineKeyboardButton(t(lang, "btn_products"), callback_data="browse"),
        InlineKeyboardButton(t(lang, "btn_cart"), callback_data="cart"),
        InlineKeyboardButton(t(lang, "btn_help"), callback_data="sos"),
        InlineKeyboardButton(t(lang, "btn_language"), callback_data="lang_menu"),
    ]
    if is_admin(update):
        btns.append(InlineKeyboardButton(t(lang, "btn_admin"), callback_data="admin"))
    return InlineKeyboardMarkup(_grid(btns, 2))


def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001F1EC\U0001F1E7 English", callback_data="lang_set:en")],
        [InlineKeyboardButton("\U0001F1EE\U0001F1E9 Bahasa Indonesia", callback_data="lang_set:id")],
    ])


def admin_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "btn_add_product"), callback_data="ap_add")],
        [InlineKeyboardButton(t(lang, "btn_stock"), callback_data="stock_menu")],
        [InlineKeyboardButton(t(lang, "btn_del_product"), callback_data="del_menu")],
        [InlineKeyboardButton(t(lang, "btn_catalog"), callback_data="catalog")],
        [InlineKeyboardButton(t(lang, "btn_back_menu"), callback_data="menu")],
    ])


def get_cart(context):
    return context.user_data.setdefault("cart", {})


def cart_summary(cart, lang):
    lines = []
    total = 0
    for pid, qty in cart.items():
        p = storage.get_product(int(pid))
        if not p:
            continue
        sub = p["price"] * qty
        total += sub
        lines.append(f"\u2022 {p['name']} x{qty} = {price(sub, lang)}")
    body = "\n".join(lines) if lines else t(lang, "empty")
    return body, total


def build_items(cart):
    items = []
    for pid, qty in cart.items():
        p = storage.get_product(int(pid))
        if not p:
            continue
        items.append({"name": p["name"], "qty": qty, "price": p["price"], "subtotal": p["price"] * qty})
    return items


async def start(update, context):
    u = update.effective_user
    uid = u.id
    # Deteksi/registrasi customer (agar terhitung di "User Terdaftar").
    storage.register_user(uid, username=u.username, name=u.full_name)
    # Force subscribe check — SEBELUM apa pun, termasuk milih bahasa
    if not await check_sub_and_block(update, context):
        return
    if not storage.is_lang_set(uid):
        # Pertama kali: statistik + info akun, lalu pemilih bahasa di bawahnya.
        await update.message.reply_text(
            stats_block(update, "en") + "\n\n" + t("en", "choose_lang"),
            reply_markup=lang_keyboard(),
            parse_mode="HTML",
        )
        return
    lang = storage.get_user_lang(uid)
    await update.message.reply_text(home_text(update, lang), reply_markup=menu_keyboard(update, lang), parse_mode="HTML")


async def menu_cmd(update, context):
    lang = lang_of(update)
    if not await check_sub_and_block(update, context):
        return ConversationHandler.END
    await update.message.reply_text(home_text(update, lang), reply_markup=menu_keyboard(update, lang), parse_mode="HTML")
    return ConversationHandler.END


async def language_cmd(update, context):
    await update.message.reply_text(t(lang_of(update), "choose_lang"), reply_markup=lang_keyboard())


async def admin_cmd(update, context):
    lang = lang_of(update)
    if not is_admin(update):
        await update.message.reply_text(t(lang, "admin_only"))
        return
    await update.message.reply_text(t(lang, "admin_title"), reply_markup=admin_keyboard(lang))


async def show_categories(q, lang):
    btns = [InlineKeyboardButton(c, callback_data=f"cat:{c}") for c in storage.list_categories()]
    rows = _grid(btns, 2)
    rows.append([InlineKeyboardButton(t(lang, "btn_back_menu"), callback_data="menu")])
    await q.edit_message_text(t(lang, "choose_category"), reply_markup=InlineKeyboardMarkup(rows))


async def show_products_all(q, lang):
    """Tampilkan semua produk langsung tanpa kategori."""
    btns = []
    for p in storage.list_products():
        stok = p.get("stock", 0)
        if stok == 0:
            continue  # skip sold out
        label = p['name']
        btns.append(InlineKeyboardButton(label, callback_data=f"prod:{p['id']}"))
    rows = _grid(btns, 2) if btns else []
    if not rows:
        await q.edit_message_text(t(lang, "empty"), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "btn_back_menu"), callback_data="menu")]]))
        return
    rows.append([InlineKeyboardButton(t(lang, "btn_back_menu"), callback_data="menu")])
    await q.edit_message_text(t(lang, "choose_product"), reply_markup=InlineKeyboardMarkup(rows))


async def show_products(q, cat, lang):
    btns = [InlineKeyboardButton(p['name'], callback_data=f"prod:{p['id']}") for p in storage.list_products(cat)]
    rows = _grid(btns, 2)
    rows.append([InlineKeyboardButton(t(lang, "btn_categories"), callback_data="browse")])
    await q.edit_message_text(t(lang, "products_in", cat=cat), reply_markup=InlineKeyboardMarkup(rows))


async def show_product(q, pid, lang):
    p = storage.get_product(pid)
    if not p:
        await q.edit_message_text(t(lang, "product_not_found"))
        return
    stok = p.get("stock", 0)
    stok_label = "Stok: " + ("Habis" if stok <= 0 else str(stok))
    text = f"{p['name']}\n\n{p['description']}\n\n{t(lang, 'price')}: {price(p['price'], lang)}\n{stok_label}"
    rows = []
    if stok > 0:
        rows.append([InlineKeyboardButton(t(lang, "btn_buy"), callback_data=f"add:{p['id']}")])
    else:
        rows.append([InlineKeyboardButton("Habis", callback_data="noop")])
    rows.append([InlineKeyboardButton(t(lang, "btn_view_cart"), callback_data="cart")])
    rows.append([InlineKeyboardButton(t(lang, "btn_back"), callback_data="browse")])
    kb = InlineKeyboardMarkup(rows)
    img = p.get("photo_url") or p.get("photo_file_id")
    if img:
        try:
            await q.message.reply_photo(img, caption=text, reply_markup=kb)
            return
        except Exception:
            pass  # jika URL gambar bermasalah, jatuh ke mode teks
    await q.edit_message_text(text, reply_markup=kb)


async def add_to_cart(q, context, pid, lang):
    cart = get_cart(context)
    cart[str(pid)] = cart.get(str(pid), 0) + 1
    p = storage.get_product(pid)
    await q.answer(t(lang, "added", name=p['name']) if p else t(lang, "added", name=""))
    await show_cart(q, context, lang)


async def show_cart(q, context, lang):
    cart = get_cart(context)
    body, total = cart_summary(cart, lang)
    if not cart:
        rows = [[InlineKeyboardButton(t(lang, "btn_view_products"), callback_data="browse")],
                [InlineKeyboardButton(t(lang, "btn_back_menu"), callback_data="menu")]]
        await q.edit_message_text(t(lang, "cart_empty"), reply_markup=InlineKeyboardMarkup(rows))
        return
    text = f"{t(lang, 'cart_title')}\n{body}\n\n{t(lang, 'total')}: {price(total, lang)}"
    rows = [
        [InlineKeyboardButton(t(lang, "btn_checkout"), callback_data="checkout")],
        [InlineKeyboardButton(t(lang, "btn_clear_cart"), callback_data="cart_clear")],
        [InlineKeyboardButton(t(lang, "btn_continue"), callback_data="browse")],
        [InlineKeyboardButton(t(lang, "btn_back_menu"), callback_data="menu")],
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(rows))


async def show_checkout(q, context, lang):
    cart = get_cart(context)
    body, total = cart_summary(cart, lang)
    if not cart:
        await q.edit_message_text(t(lang, "empty_pick"))
        return
    s = storage.get_settings()
    pay = s["payment_info_id"] if lang == "id" else s["payment_info_en"]
    text = (f"{t(lang, 'checkout_title')}\n" + body + f"\n{t(lang, 'total')}: {price(total, lang)}\n\n"
            f"{t(lang, 'payment')}\n" + _esc(pay))
    rows = [
        [InlineKeyboardButton(t(lang, "btn_paid"), callback_data="pay_done")],
        [InlineKeyboardButton(t(lang, "btn_back"), callback_data="cart")],
    ]
    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")


# --------------------------------------------------- bukti pembayaran (proof)
async def proof_start(update, context):
    q = update.callback_query
    await q.answer()
    lang = lang_of(update)
    cart = get_cart(context)
    if not cart:
        await q.edit_message_text(t(lang, "empty_pick"))
        return ConversationHandler.END
    await q.edit_message_text(t(lang, "proof_prompt"))
    return PROOF


async def proof_receive(update, context):
    lang = lang_of(update)
    msg = update.message
    proof_photo = None
    if msg.photo:
        proof_photo = msg.photo[-1].file_id
        proof_text = (msg.caption or "").strip() or t(lang, "proof_screenshot")
    else:
        proof_text = (msg.text or "").strip()
    cart = get_cart(context)
    body, total = cart_summary(cart, lang)
    if not cart:
        await msg.reply_text(t(lang, "empty_pick"))
        return ConversationHandler.END
    user = update.effective_user
    saved = storage.add_order(
        customer_name=user.full_name, phone="", address="",
        items=build_items(cart), total=total,
        telegram_name=user.full_name, telegram_id=user.id,
        proof_text=proof_text, proof_photo_file_id=proof_photo,
    )
    context.user_data["cart"] = {}
    if ADMIN_ID:
        alang = storage.get_user_lang(ADMIN_ID)
        # ringkasan item dalam bahasa admin
        alines = [f"\u2022 {it['name']} x{it['qty']} = {price(it['subtotal'], alang)}" for it in saved.get("items", [])]
        abody = "\n".join(alines) if alines else t(alang, "empty")
        caption = t(alang, "new_order", id=saved['id'], body=abody,
                    total=price(total, alang), name=user.full_name, uid=user.id, proof=proof_text)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(t(alang, "btn_send_details"), callback_data=f"fulfill:{saved['id']}")]])
        try:
            if proof_photo:
                await context.bot.send_photo(ADMIN_ID, proof_photo, caption=caption, reply_markup=kb)
            else:
                await context.bot.send_message(ADMIN_ID, caption, reply_markup=kb)
        except Exception as e:
            logging.warning("Gagal kirim ke admin: %s", e)
    await msg.reply_text(t(lang, "processing", id=saved['id']))
    return ConversationHandler.END


# ------------------------------------------------ admin kirim detail (fulfill)
async def fulfill_start(update, context):
    q = update.callback_query
    await q.answer()
    lang = lang_of(update)
    if not is_admin(update):
        await q.answer(t(lang, "admin_only_short"), show_alert=True)
        return ConversationHandler.END
    oid = int(q.data.split(":")[1])
    order = storage.get_order(oid)
    if not order:
        await q.message.reply_text(t(lang, "order_not_found"))
        return ConversationHandler.END
    context.user_data["fulfill_id"] = oid
    item_lines = "\n".join(f"\u2022 {it['name']} x{it['qty']}" for it in order.get("items", []))
    await q.message.reply_text(t(lang, "fulfill_prompt", id=oid, items=item_lines))
    return FULFILL


async def fulfill_receive(update, context):
    lang = lang_of(update)
    oid = context.user_data.get("fulfill_id")
    details = (update.message.text or "").strip()
    order = storage.get_order(oid) if oid else None
    if not order:
        await update.message.reply_text(t(lang, "order_not_found2"))
        return ConversationHandler.END
    storage.set_order_delivery(oid, details)
    cust_id = order.get("telegram_id")
    clang = storage.get_user_lang(cust_id) if cust_id else "en"
    item_lines = "\n".join(f"\u2022 {it['name']} x{it['qty']}" for it in order.get("items", []))
    success = t(clang, "order_done", id=oid, items=item_lines,
                total=price(order['total'], clang), details=details)
    sent = False
    if cust_id:
        try:
            await context.bot.send_message(cust_id, success)
            sent = True
        except Exception as e:
            logging.warning("Gagal kirim ke pembeli: %s", e)
    context.user_data.pop("fulfill_id", None)
    if sent:
        await update.message.reply_text(t(lang, "details_sent", id=oid))
    else:
        await update.message.reply_text(t(lang, "details_fail", id=oid))
    return ConversationHandler.END


async def show_catalog(q, lang):
    lines = [f"\u2022 #{p['id']} {p['name']} \u2014 {price(p['price'], lang)} ({p['category']})" for p in storage.list_products()]
    text = f"{t(lang, 'catalog_title')}\n" + ("\n".join(lines) if lines else t(lang, "empty"))
    await q.edit_message_text(text, reply_markup=admin_keyboard(lang))


async def show_admin(q, update, lang):
    if not is_admin(update):
        await q.answer(t(lang, "admin_only_short"), show_alert=True)
        return
    await q.edit_message_text(t(lang, "admin_title"), reply_markup=admin_keyboard(lang))


async def show_delete_menu(q, lang):
    rows = [[InlineKeyboardButton(f"\U0001F5D1\uFE0F {p['name']} (stok: {p.get('stock',0)})", callback_data=f"del:{p['id']}")] for p in storage.list_products()]
    rows.append([InlineKeyboardButton(t(lang, "btn_back"), callback_data="admin")])
    await q.edit_message_text(t(lang, "choose_delete"), reply_markup=InlineKeyboardMarkup(rows))


async def show_stock_menu(q, update, lang):
    """Tampilkan daftar produk dengan stok, admin bisa edit."""
    rows = []
    for p in storage.list_products():
        stok = p.get("stock", 0)
        label = f"{p['name']} — Stok: {stok}"
        rows.append([InlineKeyboardButton(label, callback_data=f"stock_edit:{p['id']}")])
    rows.append([InlineKeyboardButton(t(lang, "btn_back"), callback_data="admin")])
    await q.edit_message_text("Edit Stok Produk:\nPilih produk untuk ubah stok.", reply_markup=InlineKeyboardMarkup(rows))


async def router(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data
    lang = lang_of(update)
    # Force subscribe check — semua callback dicek kecuali force_sub_* sendiri
    if not data.startswith("force_sub") and not data.startswith("lang_set"):
        if not await check_sub_and_block(update, context):
            return
    if data == "force_sub_check":
        # Verifikasi trust-based: langsung tandai udah join trus ke menu
        uid = update.effective_user.id
        storage.set_force_sub_ok(uid)
        lang = storage.get_user_lang(uid) if storage.is_lang_set(uid) else "en"
        if not storage.is_lang_set(uid):
            # Kalo pertama kali dan blom pilih bahasa
            await q.edit_message_text(
                stats_block(update, "en") + "\n\n" + t("en", "choose_lang"),
                reply_markup=lang_keyboard(),
                parse_mode="HTML",
            )
        else:
            await q.edit_message_text(home_text(update, lang), reply_markup=menu_keyboard(update, lang), parse_mode="HTML")
        return
    elif data == "lang_menu":
        await q.edit_message_text(t(lang, "choose_lang"), reply_markup=lang_keyboard())
    elif data.startswith("lang_set:"):
        newlang = data.split(":")[1]
        storage.set_user_lang(update.effective_user.id, newlang)
        await q.edit_message_text(home_text(update, newlang), reply_markup=menu_keyboard(update, newlang), parse_mode="HTML")
    elif data == "browse":
        await show_products_all(q, lang)
    elif data.startswith("cat:"):
        await show_products(q, data[4:], lang)
    elif data.startswith("prod:"):
        await show_product(q, int(data[5:]), lang)
    elif data.startswith("add:"):
        await add_to_cart(q, context, int(data[4:]), lang)
    elif data == "cart":
        await show_cart(q, context, lang)
    elif data == "cart_clear":
        context.user_data["cart"] = {}
        await show_cart(q, context, lang)
    elif data == "checkout":
        await show_checkout(q, context, lang)
    elif data == "admin":
        await show_admin(q, update, lang)
    elif data == "catalog":
        await show_catalog(q, lang)
    elif data == "del_menu":
        if is_admin(update):
            await show_delete_menu(q, lang)
    elif data.startswith("del:"):
        if is_admin(update):
            p = storage.get_product(int(data[4:]))
            storage.delete_product(int(data[4:]))
            if p:
                await q.answer(t(lang, "deleted", name=p['name']))
            await show_delete_menu(q, lang)
    elif data == "stock_menu":
        if is_admin(update):
            await show_stock_menu(q, update, lang)
    elif data.startswith("stock_edit:"):
        if is_admin(update):
            pid = int(data.split(":")[1])
            context.user_data["edit_stock_pid"] = pid
            context.user_data["edit_stock_msg_id"] = q.message.message_id
            p = storage.get_product(pid)
            await q.edit_message_text(f"Stok saat ini *{p['name']}*: {p.get('stock',0)}\n\nKetik jumlah stok baru (angka):", parse_mode="Markdown")
            return  # JANGAN return state, handle via flag di user_data


# --------------------------------------------------------------- SOS


async def stock_message_handler(update, context):
    """Handle stock edit input — triggered when edit_stock_pid flag is set."""
    pid = context.user_data.pop("edit_stock_pid", None)
    if not pid:
        return  # not in stock mode, skip
    if update.callback_query:
        await update.callback_query.answer()
    uid = update.effective_user.id
    if uid != int(os.getenv("ADMIN_ID", "0")):
        await update.message.reply_text("Khusus admin.")
        return
    lang = lang_of(update)
    digits = "".join(c for c in update.message.text if c.isdigit())
    if not digits:
        await update.message.reply_text("Masukkan angka saja (jumlah stok).")
        # reset flag
        context.user_data["edit_stock_pid"] = pid
        return
    stok_baru = int(digits)
    p = storage.get_product(pid)
    if p:
        storage.update_product(pid, {"stock": stok_baru})
        await update.message.reply_text(f"Stok *{p['name']}* diubah jadi: {stok_baru}", parse_mode="Markdown")
    else:
        await update.message.reply_text("Produk tidak ditemukan.")
    context.user_data.pop("edit_stock_msg_id", None)


async def sos_start(update, context):
    lang = lang_of(update)
    s = storage.get_settings()
    intro = s["sos_intro_id"] if lang == "id" else s["sos_intro_en"]
    text = f"{t(lang, 'sos_title')}\n{_esc(intro)}"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")
    return SOS_MSG


async def sos_receive(update, context):
    lang = lang_of(update)
    uid = update.effective_user.id
    now = time.time()
    hist = [ts for ts in _sos_history[uid] if now - ts < SOS_WINDOW_SECONDS]
    if hist and now - hist[-1] < SOS_COOLDOWN_SECONDS:
        wait = int(SOS_COOLDOWN_SECONDS - (now - hist[-1]))
        await update.message.reply_text(t(lang, "sos_wait", n=wait))
        return SOS_MSG
    if len(hist) >= SOS_MAX_PER_WINDOW:
        await update.message.reply_text(t(lang, "sos_limit"))
        return ConversationHandler.END
    hist.append(now)
    _sos_history[uid] = hist
    if ADMIN_ID:
        u = update.effective_user
        try:
            await context.bot.send_message(ADMIN_ID, f"\U0001F198 SOS \u2014 {u.full_name} (id {u.id}):\n{update.message.text}")
        except Exception as e:
            logging.warning("Gagal kirim SOS ke admin: %s", e)
    await update.message.reply_text(t(lang, "sos_sent"))
    return ConversationHandler.END


# --------------------------------------------------------------- admin add produk
async def ap_start(update, context):
    q = update.callback_query
    await q.answer()
    lang = lang_of(update)
    if not is_admin(update):
        await q.answer(t(lang, "admin_only_short"), show_alert=True)
        return ConversationHandler.END
    context.user_data["ap"] = {}
    await q.edit_message_text(t(lang, "ap_step1"))
    return AP_NAME


async def ap_name(update, context):
    lang = lang_of(update)
    context.user_data["ap"]["name"] = update.message.text.strip()
    await update.message.reply_text(t(lang, "ap_step2"))
    return AP_DESC


async def ap_desc(update, context):
    lang = lang_of(update)
    context.user_data["ap"]["description"] = update.message.text.strip()
    rows = [[InlineKeyboardButton(t(lang, "btn_skip_image"), callback_data="ap_skip")]]
    await update.message.reply_text(t(lang, "ap_step3"), reply_markup=InlineKeyboardMarkup(rows))
    return AP_PHOTO


async def ap_photo(update, context):
    lang = lang_of(update)
    context.user_data["ap"]["photo_file_id"] = update.message.photo[-1].file_id
    await update.message.reply_text(t(lang, "ap_step4"))
    return AP_PRICE


async def ap_photo_skip(update, context):
    q = update.callback_query
    await q.answer()
    lang = lang_of(update)
    context.user_data["ap"]["photo_file_id"] = None
    await q.edit_message_text(t(lang, "ap_step4"))
    return AP_PRICE


async def ap_price(update, context):
    lang = lang_of(update)
    digits = "".join(c for c in update.message.text if c.isdigit())
    if not digits:
        await update.message.reply_text(t(lang, "ap_price_invalid"))
        return AP_PRICE
    ap = context.user_data["ap"]
    ap["price"] = int(digits)
    ap.setdefault("category", "Umum")
    img_label = t(lang, "yes") if ap.get("photo_file_id") else t(lang, "no")
    text = t(lang, "ap_review", name=ap['name'], desc=ap['description'],
             img=img_label, price=price(ap['price'], lang))
    rows = [[InlineKeyboardButton(t(lang, "btn_save"), callback_data="ap_save")],
            [InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="ap_cancel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(rows))
    return AP_CONFIRM


async def ap_save(update, context):
    q = update.callback_query
    await q.answer()
    lang = lang_of(update)
    ap = context.user_data.get("ap", {})
    p = storage.add_product(ap.get("name", ""), ap.get("description", ""), ap.get("price", 0), ap.get("category", "Umum"), ap.get("photo_file_id"))
    await q.edit_message_text(t(lang, "ap_saved", name=p['name']), reply_markup=admin_keyboard(lang))
    return ConversationHandler.END


async def ap_cancel(update, context):
    q = update.callback_query
    await q.answer()
    lang = lang_of(update)
    await q.edit_message_text(t(lang, "cancelled"), reply_markup=admin_keyboard(lang))
    return ConversationHandler.END


async def stock_edit_handler(update, context):
    """Terima input stok baru dari admin."""
    lang = lang_of(update)
    pid = context.user_data.get("edit_stock_pid")
    if not pid:
        await update.message.reply_text("Error: produk tidak ditemukan.")
        return ConversationHandler.END
    digits = "".join(c for c in update.message.text if c.isdigit())
    if not digits:
        await update.message.reply_text("Masukkan angka saja (jumlah stok).")
        return "EDIT_STOCK"
    stok_baru = int(digits)
    p = storage.get_product(pid)
    if p:
        storage.update_product(pid, {"stock": stok_baru})
        await update.message.reply_text(f"Stok *{p['name']}* diubah jadi: {stok_baru}", parse_mode="Markdown")
    else:
        await update.message.reply_text("Produk tidak ditemukan.")
    await update.message.reply_text(t(lang, "admin_title"), reply_markup=admin_keyboard(lang))
    return ConversationHandler.END


async def cancel_conv(update, context):
    lang = lang_of(update)
    context.user_data.pop("fulfill_id", None)
    context.user_data.pop("ap", None)
    await update.message.reply_text(t(lang, "cancelled"), reply_markup=menu_keyboard(update, lang))
    return ConversationHandler.END


async def start_reset(update, context):
    """/start di tengah alur apa pun: bersihkan sesi lalu kembali ke menu utama."""
    context.user_data.pop("ap", None)
    context.user_data.pop("fulfill_id", None)
    await start(update, context)
    return ConversationHandler.END


async def language_reset(update, context):
    """/language di tengah alur apa pun: keluar alur lalu buka pemilih bahasa."""
    context.user_data.pop("ap", None)
    context.user_data.pop("fulfill_id", None)
    await language_cmd(update, context)
    return ConversationHandler.END


def build_app():
    app = Application.builder().token(BOT_TOKEN).build()
    # Perintah reset ini dipasang di SEMUA alur, jadi pelanggan tidak akan
    # pernah "stuck": /start, /menu, /language, /cancel selalu keluar dari
    # alur mana pun (bukti bayar, SOS, tambah produk, dsb) lalu kembali ke
    # menu utama. allow_reentry juga membuat alur bisa dimulai ulang.
    common_fallbacks = [
        CommandHandler("cancel", cancel_conv),
        CommandHandler("menu", menu_cmd),
        CommandHandler("start", start_reset),
        CommandHandler("language", language_reset),
    ]
    sos_conv = ConversationHandler(
        entry_points=[CommandHandler("sos", sos_start), CallbackQueryHandler(sos_start, pattern="^sos$")],
        states={SOS_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, sos_receive)]},
        fallbacks=common_fallbacks,
        allow_reentry=True,
    )
    proof_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(proof_start, pattern="^pay_done$")],
        states={PROOF: [MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, proof_receive)]},
        fallbacks=common_fallbacks,
        allow_reentry=True,
    )
    fulfill_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(fulfill_start, pattern="^fulfill:")],
        states={FULFILL: [MessageHandler(filters.TEXT & ~filters.COMMAND, fulfill_receive)]},
        fallbacks=common_fallbacks,
        allow_reentry=True,
    )
    addproduct_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ap_start, pattern="^ap_add$")],
        states={
            AP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ap_name)],
            AP_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, ap_desc)],
            AP_PHOTO: [MessageHandler(filters.PHOTO, ap_photo), CallbackQueryHandler(ap_photo_skip, pattern="^ap_skip$")],
            AP_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ap_price)],
            AP_CONFIRM: [CallbackQueryHandler(ap_save, pattern="^ap_save$"),
                         CallbackQueryHandler(ap_cancel, pattern="^ap_cancel$")],
        },
        fallbacks=common_fallbacks,
        allow_reentry=True,
    )
    app.add_handler(sos_conv)
    app.add_handler(proof_conv)
    app.add_handler(fulfill_conv)
    app.add_handler(addproduct_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, stock_message_handler))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("language", language_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(router))
    return app


def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN belum diisi. Salin .env.example ke .env lalu isi token.")
    build_app().run_polling()


if __name__ == "__main__":
    main()
