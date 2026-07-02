# Bot Toko Telegram + Web Admin

Toko online sederhana: pelanggan belanja lewat Telegram; admin mengelola
katalog, memantau pesanan, dan mengubah tampilan bot lewat Telegram atau web.
Bot & web berbagi file data yang sama sehingga selalu tersinkron.

## Fitur
- Pelanggan: /start, /menu, telusuri per kategori, keranjang, checkout ringkas
  (tanpa alamat) -> tampil detail pembayaran -> tombol "Saya sudah bayar".
- Admin (Telegram): /admin -> tambah/hapus produk, lihat katalog.
- Admin (Web): dashboard pesanan (auto-refresh & ubah status), kelola produk,
  dan halaman "Tampilan Bot" untuk mengubah teks yang tampil di bot.

## Alur checkout (baru, ringkas)
Keranjang -> Checkout -> bot menampilkan ringkasan + detail pembayaran ->
pelanggan menekan "Saya sudah bayar" -> pesanan tersimpan & admin diberi tahu.
Tidak ada permintaan alamat.

## Sinkronisasi bot <-> web
- data.json      : katalog produk
- orders.json    : pesanan (ditulis bot saat bayar, dibaca web)
- settings.json  : teks tampilan bot (diubah dari web, dibaca bot)
Jalankan bot & web di folder/host yang sama agar berbagi file yang sama.

## Menjalankan
```bash
pip install -r requirements.txt
cp .env.example .env      # isi BOT_TOKEN, ADMIN_ID, ADMIN_WEB_PASSWORD
python bot.py             # bot Telegram
python web/app.py         # web admin -> http://127.0.0.1:5000
```

## Konfigurasi .env
| Variabel | Keterangan |
|---|---|
| BOT_TOKEN | Token dari @BotFather |
| ADMIN_ID | ID Telegram admin (@userinfobot) |
| ADMIN_WEB_PASSWORD | Kata sandi login web admin |
| WEB_SECRET | String acak untuk sesi web |
| STORE_NAME / CURRENCY | Nilai awal (selanjutnya bisa diubah di web) |

> Detail pembayaran, pesan sambutan, dan mata uang diatur di halaman
> "Tampilan Bot" pada web admin (tersimpan di settings.json).
