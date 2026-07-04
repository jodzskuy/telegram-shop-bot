"""Penyimpanan katalog sederhana berbasis file JSON (tanpa database).

Cukup untuk toko kecil. Aman dari akses paralel dengan lock sederhana.
"""
from __future__ import annotations

import json
import os
import threading
import shutil
from datetime import datetime, timezone
from typing import List, Optional

BASE_DIR = os.getenv("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
MAX_BACKUPS = 50
_lock = threading.Lock()

def _auto_backup(filepath: str) -> None:
    """Auto backup file sebelum ditimpa, max 50 backup per file."""
    if not os.path.exists(filepath):
        return
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        basename = os.path.basename(filepath)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dst = os.path.join(BACKUP_DIR, f"{ts}_{basename}")
        shutil.copy2(filepath, dst)
        # Hapus backup lama (MAX per file type)
        backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(f"_{basename}")])
        while len(backups) > MAX_BACKUPS:
            os.remove(os.path.join(BACKUP_DIR, backups.pop(0)))
    except Exception:
        pass  # Backup failure jangan sampai ngebreak operasi utama

_SEED = {
    "products": [
        {
            "id": 1,
            "name": "Kopi Arabika 250g",
            "category": "Minuman",
            "price": 85000,
            "description": "Biji kopi arabika single origin, medium roast.",
            "photo_file_id": None,
        },
        {
            "id": 2,
            "name": "Teh Melati Premium",
            "category": "Minuman",
            "price": 45000,
            "description": "Teh hijau melati wangi, isi 50 kantong.",
            "photo_file_id": None,
        },
        {
            "id": 3,
            "name": "Cokelat Batangan 70%",
            "category": "Makanan",
            "price": 38000,
            "description": "Dark chocolate 70% cocoa, tanpa pemanis buatan.",
            "photo_file_id": None,
        },
        {
            "id": 4,
            "name": "Granola Madu 500g",
            "category": "Makanan",
            "price": 72000,
            "description": "Granola panggang dengan madu asli dan kacang.",
            "photo_file_id": None,
        },
        {
            "id": 5,
            "name": "Tumbler Stainless 500ml",
            "category": "Aksesori",
            "price": 120000,
            "description": "Tumbler tahan panas/dingin hingga 12 jam.",
            "photo_file_id": None,
        },
    ]
}


def _read() -> dict:
    if not os.path.exists(DATA_FILE):
        _write(_SEED)
        return json.loads(json.dumps(_SEED))
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(data: dict) -> None:
    _auto_backup(DATA_FILE)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_categories() -> List[str]:
    with _lock:
        data = _read()
    cats: List[str] = []
    for p in data["products"]:
        if p["category"] not in cats:
            cats.append(p["category"])
    return cats


def list_products(category: Optional[str] = None) -> List[dict]:
    with _lock:
        data = _read()
    items = data["products"]
    if category:
        items = [p for p in items if p["category"] == category]
    return items


def get_product(product_id: int) -> Optional[dict]:
    with _lock:
        data = _read()
    for p in data["products"]:
        if p["id"] == product_id:
            return p
    return None


def add_product(
    name: str,
    description: str,
    price: int,
    category: str = "Umum",
    photo_file_id: Optional[str] = None,
    photo_url: Optional[str] = None,
) -> dict:
    with _lock:
        data = _read()
        new_id = max([p["id"] for p in data["products"]], default=0) + 1
        product = {
            "id": new_id,
            "name": name,
            "category": category,
            "price": price,
            "stock": 999,
            "description": description,
            "photo_file_id": photo_file_id,
            "photo_url": photo_url,
        }
        data["products"].append(product)
        _write(data)
    return product


def update_product(product_id: int, fields: dict) -> bool:
    """Perbarui field produk dari web (nama, kategori, harga, deskripsi, gambar, stok)."""
    allowed = {"name", "category", "price", "stock", "description", "photo_url", "photo_file_id"}
    with _lock:
        data = _read()
        changed = False
        for p in data["products"]:
            if p["id"] == product_id:
                for k, v in fields.items():
                    if k in allowed:
                        p[k] = v
                changed = True
                break
        if changed:
            _write(data)
    return changed


def delete_product(product_id: int) -> bool:
    with _lock:
        data = _read()
        before = len(data["products"])
        data["products"] = [p for p in data["products"] if p["id"] != product_id]
        changed = len(data["products"]) != before
        if changed:
            _write(data)
    return changed


# ------------------------------------------------------------------- pesanan

ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
ORDER_STATUSES = ["Baru", "Diproses", "Selesai", "Batal"]


def _read_orders() -> dict:
    if not os.path.exists(ORDERS_FILE):
        return {"orders": []}
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_orders(data: dict) -> None:
    _auto_backup(ORDERS_FILE)
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_order(customer_name, phone, address, items, total,
              telegram_name="", telegram_id=None,
              proof_text="", proof_photo_file_id=None) -> dict:
    with _lock:
        data = _read_orders()
        new_id = max([o["id"] for o in data["orders"]], default=0) + 1
        order = {
            "id": new_id,
            "created_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "customer_name": customer_name,
            "phone": phone,
            "address": address,
            "items": items,
            "total": total,
            "status": "Diproses",
            "telegram_name": telegram_name,
            "telegram_id": telegram_id,
            "proof_text": proof_text,
            "proof_photo_file_id": proof_photo_file_id,
            "delivery_details": "",
        }
        data["orders"].append(order)
        _write_orders(data)
    return order


def set_order_delivery(order_id: int, details: str) -> bool:
    """Simpan detail produk yang dikirim admin ke pembeli, tandai Selesai."""
    with _lock:
        data = _read_orders()
        changed = False
        for o in data["orders"]:
            if o["id"] == order_id:
                o["delivery_details"] = details
                o["status"] = "Selesai"
                changed = True
                break
        if changed:
            _write_orders(data)
    return changed


def list_orders() -> list:
    with _lock:
        data = _read_orders()
    return list(reversed(data["orders"]))  # terbaru dulu


def get_order(order_id: int):
    with _lock:
        data = _read_orders()
    for o in data["orders"]:
        if o["id"] == order_id:
            return o
    return None


def update_order_status(order_id: int, status: str) -> bool:
    with _lock:
        data = _read_orders()
        changed = False
        for o in data["orders"]:
            if o["id"] == order_id:
                o["status"] = status
                changed = True
                break
        if changed:
            _write_orders(data)
    return changed


def order_counts() -> dict:
    with _lock:
        data = _read_orders()
    counts = {s: 0 for s in ORDER_STATUSES}
    for o in data["orders"]:
        st = o.get("status", "Baru")
        counts[st] = counts.get(st, 0) + 1
    counts["Total"] = len(data["orders"])
    return counts


# ------------------------------------------------------------- pengaturan bot
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")


def _default_settings():
    return {
        "store_name": os.getenv("STORE_NAME", "Mini Online Store"),
        # Mata uang: harga dasar disimpan dalam Rupiah (IDR).
        # English otomatis dikonversi ke USD memakai kurs idr_per_usd.
        "currency_id": os.getenv("CURRENCY", "Rp"),
        "currency_en": os.getenv("CURRENCY_EN", "$"),
        "idr_per_usd": int(os.getenv("IDR_PER_USD", "16000") or 16000),
        # Teks per bahasa (English default).
        "welcome_en": "Hi! Welcome to {store}. Shop right inside Telegram. Choose a menu below:",
        "welcome_id": "Halo! Selamat datang di {store}. Belanja langsung dari Telegram. Pilih menu di bawah:",
        "payment_info_en": ("Please transfer the order total to:\n"
                            "- BCA 1234567890 a/n Mini Online Store\n"
                            "- DANA / OVO 0812-3456-7890\n\n"
                            "After paying, tap \"I have paid\" and the admin will verify."),
        "payment_info_id": ("Silakan transfer sejumlah total pesanan ke:\n"
                            "- BCA 1234567890 a.n. Toko Online Mini\n"
                            "- DANA / OVO 0812-3456-7890\n\n"
                            "Setelah transfer, tekan tombol \"Saya sudah bayar\" dan admin akan memverifikasi."),
        "sos_intro_en": "Type your question in one message and we'll forward it to the admin.",
        "sos_intro_id": "Ketik pertanyaan Anda dalam satu pesan, akan kami teruskan ke admin.",
    }


SETTINGS_KEYS = (
    "store_name", "currency_id", "currency_en", "idr_per_usd",
    "welcome_en", "welcome_id", "payment_info_en", "payment_info_id",
    "sos_intro_en", "sos_intro_id",
)


def format_price(amount, lang="en"):
    """Format harga. Dasar dalam IDR; English dikonversi ke USD via kurs."""
    s = get_settings()
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return str(amount)
    if lang == "id":
        n = int(round(amount))
        grouped = f"{abs(n):,}".replace(",", ".")
        return f"{s['currency_id']}{'-' if n < 0 else ''}{grouped}"
    rate = float(s.get("idr_per_usd") or 16000)
    usd = amount / rate if rate else 0.0
    return f"{s['currency_en']}{usd:,.2f}"


def get_settings():
    with _lock:
        data = _default_settings()
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data.update(json.load(f))
            except Exception:
                pass
        return data


def update_settings(new):
    with _lock:
        cur = get_settings()
        for k in SETTINGS_KEYS:
            if k in new and new[k] is not None:
                cur[k] = new[k]
        _auto_backup(SETTINGS_FILE)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
    return cur


# ------------------------------------------------------------- bahasa pengguna
USERS_FILE = os.path.join(BASE_DIR, "users.json")


def _read_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_users(data: dict) -> None:
    _auto_backup(USERS_FILE)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_lang(uid) -> str:
    with _lock:
        data = _read_users()
    return data.get(str(uid), {}).get("lang", "en")


def is_lang_set(uid) -> bool:
    with _lock:
        data = _read_users()
    return "lang" in data.get(str(uid), {})


def set_user_lang(uid, lang) -> None:
    if lang not in ("en", "id"):
        lang = "en"
    with _lock:
        data = _read_users()
        data.setdefault(str(uid), {})["lang"] = lang
        _write_users(data)


def set_force_sub_ok(uid) -> None:
    """Tandai user sudah join channel (force subscribe)."""
    with _lock:
        data = _read_users()
        data.setdefault(str(uid), {})["force_sub_ok"] = True
        _write_users(data)


def is_force_sub_ok(uid) -> bool:
    """Cek apakah user sudah diverifikasi join channel."""
    with _lock:
        data = _read_users()
    return data.get(str(uid), {}).get("force_sub_ok", False)


def register_user(uid, username=None, name=None) -> bool:
    """Catat pengguna (deteksi customer) agar terhitung di statistik.
    Return True jika user baru (baru pertama kali tercatat)."""
    with _lock:
        data = _read_users()
        rec = data.setdefault(str(uid), {})
        was_new = not rec
        if username:
            rec["username"] = username
        if name:
            rec["name"] = name
        _write_users(data)
    return was_new


def registered_count() -> int:
    with _lock:
        return len(_read_users())


def stats() -> dict:
    """Statistik ringkas: total pcs terjual (pesanan Selesai) & jumlah user."""
    sold = 0
    for o in list_orders():
        if o.get("status") == "Selesai":
            for it in o.get("items", []):
                try:
                    sold += int(it.get("qty", 0) or 0)
                except (TypeError, ValueError):
                    pass
    return {"sold_pcs": sold, "registered_users": registered_count()}


def user_total_spent(uid) -> int:
    """Total belanja (pesanan Selesai) milik satu pengguna, dalam IDR."""
    total = 0
    for o in list_orders():
        if o.get("telegram_id") == uid and o.get("status") == "Selesai":
            try:
                total += int(o.get("total", 0) or 0)
            except (TypeError, ValueError):
                pass
    return total
