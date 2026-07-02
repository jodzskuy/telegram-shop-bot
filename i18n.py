"""Teks dua bahasa untuk bot Telegram: English (default) + Bahasa Indonesia.

Ubah/ tambah teks di sini bila perlu. Kunci harus sama di kedua bahasa.
"""

LANGS = ("en", "id")
LANG_NAMES = {"en": "English", "id": "Bahasa Indonesia"}

STRINGS = {
    "en": {
        # ---- tombol ----
        "btn_products": "\U0001F6CD\uFE0F Products",
        "btn_cart": "\U0001F6D2 Cart",
        "btn_help": "\U0001F198 Support",
        "btn_admin": "\U0001F6E0\uFE0F Admin",
        "btn_language": "\U0001F310 Language",
        "btn_back": "\u2B05\uFE0F Back",
        "btn_back_menu": "\u2B05\uFE0F Menu",
        "btn_categories": "\u2B05\uFE0F Categories",
        "btn_buy": "\U0001F6D2 Buy / Add to Cart",
        "btn_view_cart": "\U0001F6D2 View Cart",
        "btn_checkout": "\u2705 Checkout",
        "btn_clear_cart": "\U0001F5D1\uFE0F Clear",
        "btn_continue": "\U0001F6CD\uFE0F Continue Shopping",
        "btn_view_products": "\U0001F6CD\uFE0F View Products",
        "btn_paid": "\u2705 I have paid",
        "btn_add_product": "\u2795 Add Product",
        "btn_del_product": "\U0001F5D1\uFE0F Delete Product",
        "btn_catalog": "\U0001F4CB View Catalog",
        "btn_skip_image": "Skip image",
        "btn_save": "\u2705 Save",
        "btn_cancel": "\u274C Cancel",
        "btn_send_details": "\U0001F4E6 Send product details",
        # ---- pesan umum ----
        "choose_lang": "\U0001F310 Please choose your language:",
        "choose_category": "Choose a product category:",
        "products_in": "Products in {cat}:",
        "product_not_found": "Product not found.",
        "price": "Price",
        "added": "Added: {name}",
        "cart_empty": "\U0001F6D2 Your cart is empty.",
        "cart_title": "\U0001F6D2 Your Cart",
        "total": "Total",
        "empty": "(empty)",
        "empty_pick": "Cart is empty. Please pick a product first.",
        "checkout_title": "\U0001F9FE Order Confirmation",
        "payment": "\U0001F4B3 Payment",
        "proof_prompt": "\U0001F4E4 Send Payment Proof\n\nPlease send one of:\n\u2022 Order ID / TX Hash \u2014 type as text, or\n\u2022 Payment screenshot \u2014 send as a photo.\n\nType /cancel to abort.",
        "proof_screenshot": "(payment screenshot)",
        "processing": "\u23F3 Payment for order #{id} is being processed.\nPlease wait a moment \u2014 the admin will send your product details shortly. \U0001F64F",
        "sos_title": "\U0001F198 Support",
        "sos_sent": "\u2705 Your question has been sent to the admin. Thank you!",
        "sos_wait": "Please wait {n} seconds before sending again.",
        "sos_limit": "You have already sent several messages. Please try again later.",
        "admin_only": "\u26D4 This command is for admins only.",
        "admin_title": "\U0001F6E0\uFE0F Admin Mode\nManage your product catalog:",
        "catalog_title": "\U0001F4CB Catalog",
        "choose_delete": "Choose a product to delete:",
        "deleted": "Deleted: {name}",
        "cancelled": "Cancelled.",
        "admin_only_short": "Admins only",
        # ---- pesanan ----
        "new_order": "\U0001F4E6 NEW ORDER #{id}\n{body}\nTotal: {total}\n\nBuyer: {name} (id {uid})\nProof: {proof}\n\nTap the button below to send product details to the buyer.",
        "fulfill_prompt": "\u270D\uFE0F Send product details for order #{id}\n{items}\n\nType the details the buyer will receive (e.g. account, code, license, link, instructions).\nYour message will be forwarded to the buyer and the order marked Completed.\nType /cancel to abort.",
        "order_done": "\u2705 Order #{id} COMPLETED!\n\n\U0001F4E6 Products:\n{items}\nTotal: {total}\n\n\U0001F510 Your product details:\n{details}\n\nThank you for your purchase! See you again. \U0001F64F",
        "details_sent": "\u2705 Details sent to the buyer. Order #{id} marked Completed.",
        "details_fail": "\u26A0\uFE0F Order #{id} marked Completed, but sending to the buyer failed (they may not have started the bot).",
        "order_not_found": "Order not found.",
        "order_not_found2": "Order not found / session ended.",
        # ---- tambah produk ----
        "ap_step1": "\u2795 Add Product\nStep 1/4 \u2014 Send the product name.",
        "ap_step2": "Step 2/4 \u2014 Send the product description.",
        "ap_step3": "Step 3/4 \u2014 Send a product image (photo), or skip.",
        "ap_step4": "Step 4/4 \u2014 Send the price (number, e.g. 50000).",
        "ap_price_invalid": "Price must be a number. Try again (e.g. 50000).",
        "ap_review": "Review product data:\n\nName: {name}\nDescription: {desc}\nImage: {img}\nPrice: {price}\n\nSave this product?",
        "ap_saved": "\u2705 Product {name} added successfully.",
        "yes": "yes",
        "no": "no",
        # ---- force subscribe ----
        "force_sub_required": "⚠️ To use this bot, you must join our channel first.\n\nPlease click the button below, join, then come back and tap \"I have joined\".\n\nAfter joining, tap the button below to verify:",
        "force_sub_join": "📢 Join Channel",
        "force_sub_check": "✅ I have joined — Check again",
        "force_sub_success": "✅ Thank you for joining! You can now use the bot. 🙏",
    },
    "id": {
        # ---- tombol ----
        "btn_products": "\U0001F6CD\uFE0F Produk",
        "btn_cart": "\U0001F6D2 Keranjang",
        "btn_help": "\U0001F198 Bantuan",
        "btn_admin": "\U0001F6E0\uFE0F Admin",
        "btn_language": "\U0001F310 Bahasa",
        "btn_back": "\u2B05\uFE0F Kembali",
        "btn_back_menu": "\u2B05\uFE0F Menu",
        "btn_categories": "\u2B05\uFE0F Kategori",
        "btn_buy": "\U0001F6D2 Beli / Tambah ke Keranjang",
        "btn_view_cart": "\U0001F6D2 Lihat Keranjang",
        "btn_checkout": "\u2705 Checkout / Pesan",
        "btn_clear_cart": "\U0001F5D1\uFE0F Kosongkan",
        "btn_continue": "\U0001F6CD\uFE0F Lanjut Belanja",
        "btn_view_products": "\U0001F6CD\uFE0F Lihat Produk",
        "btn_paid": "\u2705 Saya sudah bayar",
        "btn_add_product": "\u2795 Tambah Produk",
        "btn_del_product": "\U0001F5D1\uFE0F Hapus Produk",
        "btn_catalog": "\U0001F4CB Lihat Katalog",
        "btn_skip_image": "Lewati gambar",
        "btn_save": "\u2705 Simpan",
        "btn_cancel": "\u274C Batal",
        "btn_send_details": "\U0001F4E6 Kirim detail produk",
        # ---- pesan umum ----
        "choose_lang": "\U0001F310 Silakan pilih bahasa Anda:",
        "choose_category": "Pilih kategori produk:",
        "products_in": "Produk pada kategori {cat}:",
        "product_not_found": "Produk tidak ditemukan.",
        "price": "Harga",
        "added": "Ditambahkan: {name}",
        "cart_empty": "\U0001F6D2 Keranjang Anda masih kosong.",
        "cart_title": "\U0001F6D2 Keranjang Anda",
        "total": "Total",
        "empty": "(kosong)",
        "empty_pick": "Keranjang kosong. Silakan pilih produk dulu.",
        "checkout_title": "\U0001F9FE Konfirmasi Pesanan",
        "payment": "\U0001F4B3 Pembayaran",
        "proof_prompt": "\U0001F4E4 Kirim Bukti Pembayaran\n\nSilakan kirim salah satu:\n\u2022 Order ID / TX Hash \u2014 ketik sebagai teks, atau\n\u2022 Screenshot bukti transfer \u2014 kirim sebagai foto.\n\nKetik /cancel untuk membatalkan.",
        "proof_screenshot": "(screenshot bukti transfer)",
        "processing": "\u23F3 Pembayaran untuk pesanan #{id} sedang kami proses.\nMohon tunggu sebentar, admin akan segera mengirimkan detail produk Anda. \U0001F64F",
        "sos_title": "\U0001F198 Bantuan / SOS",
        "sos_sent": "\u2705 Pertanyaan Anda sudah dikirim ke admin. Terima kasih!",
        "sos_wait": "Mohon tunggu {n} detik sebelum mengirim lagi.",
        "sos_limit": "Anda sudah mengirim beberapa pesan. Coba lagi nanti ya.",
        "admin_only": "\u26D4 Perintah ini khusus admin.",
        "admin_title": "\U0001F6E0\uFE0F Mode Admin\nKelola katalog produk:",
        "catalog_title": "\U0001F4CB Katalog",
        "choose_delete": "Pilih produk yang akan dihapus:",
        "deleted": "Dihapus: {name}",
        "cancelled": "Dibatalkan.",
        "admin_only_short": "Khusus admin",
        # ---- pesanan ----
        "new_order": "\U0001F4E6 PESANAN BARU #{id}\n{body}\nTotal: {total}\n\nPembeli: {name} (id {uid})\nBukti: {proof}\n\nTekan tombol di bawah untuk mengirim detail produk ke pembeli.",
        "fulfill_prompt": "\u270D\uFE0F Kirim detail produk untuk pesanan #{id}\n{items}\n\nKetik detail yang akan diterima pembeli (mis. akun, kode, lisensi, link, instruksi).\nPesan Anda akan diteruskan ke pembeli dan pesanan ditandai Selesai.\nKetik /cancel untuk membatalkan.",
        "order_done": "\u2705 Pesanan #{id} SELESAI!\n\n\U0001F4E6 Produk:\n{items}\nTotal: {total}\n\n\U0001F510 Detail produk Anda:\n{details}\n\nTerima kasih sudah berbelanja! Semoga puas dan sampai jumpa lagi. \U0001F64F",
        "details_sent": "\u2705 Detail terkirim ke pembeli. Pesanan #{id} ditandai Selesai.",
        "details_fail": "\u26A0\uFE0F Pesanan #{id} ditandai Selesai, tapi gagal mengirim ke pembeli (mungkin pembeli belum pernah /start).",
        "order_not_found": "Pesanan tidak ditemukan.",
        "order_not_found2": "Pesanan tidak ditemukan / sesi berakhir.",
        # ---- tambah produk ----
        "ap_step1": "\u2795 Tambah Produk\nLangkah 1/4 \u2014 Kirim nama produk.",
        "ap_step2": "Langkah 2/4 \u2014 Kirim deskripsi produk.",
        "ap_step3": "Langkah 3/4 \u2014 Kirim gambar produk (foto), atau lewati.",
        "ap_step4": "Langkah 4/4 \u2014 Kirim harga (angka, contoh 50000).",
        "ap_price_invalid": "Harga harus berupa angka. Coba lagi (contoh 50000).",
        "ap_review": "Periksa data produk:\n\nNama: {name}\nDeskripsi: {desc}\nGambar: {img}\nHarga: {price}\n\nSimpan produk ini?",
        "ap_saved": "\u2705 Produk {name} berhasil ditambahkan.",
        "yes": "ada",
        "no": "tidak ada",
        # ---- force subscribe ----
        "force_sub_required": "⚠️ Untuk menggunakan bot ini, Anda wajib join channel kami dulu.\n\nSilakan klik tombol di bawah, join, lalu kembali dan tekan \"Saya sudah join\".\n\nSetelah join, tekan tombol di bawah untuk verifikasi:",
        "force_sub_join": "📢 Join Channel",
        "force_sub_check": "✅ Saya sudah join — Cek lagi",
        "force_sub_success": "✅ Terima kasih sudah join! Sekarang Anda bisa menggunakan bot. 🙏",
    },
}


def t(lang, key, **kwargs):
    """Ambil teks untuk bahasa; fallback ke English lalu ke key mentah."""
    d = STRINGS.get(lang) or STRINGS["en"]
    s = d.get(key)
    if s is None:
        s = STRINGS["en"].get(key, key)
    return s.format(**kwargs) if kwargs else s


# --- Tambahan: label statistik & info akun (tampil saat /start) ---
_EXTRA = {
    "en": {
        "stats_title": "\U0001F4CA BOT STATISTICS",
        "stat_sold": "Sold",
        "stat_users": "Registered Users",
        "stat_pcs": "pcs",
        "acct_title": "\U0001F464 ACCOUNT INFO",
        "acct_id": "ID",
        "acct_username": "Username",
        "acct_spent": "Total Spent",
    },
    "id": {
        "stats_title": "\U0001F4CA STATISTIK BOT",
        "stat_sold": "Terjual",
        "stat_users": "User Terdaftar",
        "stat_pcs": "pcs",
        "acct_title": "\U0001F464 INFORMASI AKUN",
        "acct_id": "ID",
        "acct_username": "Username",
        "acct_spent": "Total Belanja",
    },
}
for _lang, _extra in _EXTRA.items():
    STRINGS.setdefault(_lang, {}).update(_extra)
