# Web Form Automation System (Python + Selenium + Docker + MySQL)

Sistem otomasi untuk **mengisi form dan mengklik tombol** di aplikasi web secara
terjadwal. Konfigurasi langkah (field mana diisi apa, tombol mana diklik) disimpan
di MySQL — jadi menambah automation baru cukup lewat SQL/Adminer, tanpa ubah kode.

## Arsitektur

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────┐
│   MySQL     │◄───►│  app (Python)│────►│  selenium (Chrome)  │
│ tasks & logs│     │  scheduler   │     │  browser headless   │
└─────────────┘     └──────────────┘     └────────────────────┘
```

- **mysql** — menyimpan daftar task (`automation_tasks`) dan log hasil (`automation_logs`)
- **selenium** — container `selenium/standalone-chrome`, browser yang benar-benar
  mengisi form & klik tombol. Bisa dilihat live lewat noVNC.
- **app** — scheduler Python yang baca task dari MySQL, jalankan lewat Selenium
  sesuai jadwal cron

## Struktur Proyek

```
web-automation-system/
├── docker-compose.yml
├── .env.example
└── app/
    ├── Dockerfile
    ├── requirements.txt
    ├── init.sql        <- skema tabel + contoh task
    ├── db.py            <- koneksi & logging ke MySQL
    ├── executor.py       <- eksekusi step (fill, click, select, dll)
    ├── runner.py         <- bungkus eksekusi + logging + screenshot error
    ├── scheduler.py       <- baca task dari DB, jadwalkan ke APScheduler
    ├── main.py           <- entry point (mode terjadwal)
    └── run_now.py         <- jalankan 1 task manual buat testing
```

## Cara Menjalankan

1. Copy environment:
   ```bash
   cp .env.example .env
   ```

2. Jalankan semua service:
   ```bash
   docker compose up -d --build
   ```

3. Cek log scheduler:
   ```bash
   docker compose logs -f app
   ```

4. **Lihat browser bekerja secara live** (sangat membantu saat testing):
   buka `http://localhost:7900/?autoconnect=1&resize=scale&password=secret`
   di browser kamu. Password default noVNC adalah `secret`.

5. (Opsional) Adminer untuk lihat/isi tabel: `http://localhost:8080`
   - System: MySQL, Server: `mysql`, User/Password sesuai `.env`, Database sesuai `DB_NAME`

## Menambah Task Baru

Semua task didefinisikan sebagai baris di tabel `automation_tasks`, dengan kolom
`steps_json` berisi array langkah yang dijalankan berurutan.

Contoh insert lewat Adminer atau MySQL client:

```sql
INSERT INTO automation_tasks (task_name, target_url, cron_expression, enabled, description, steps_json)
VALUES (
  'submit_absensi_harian',
  'https://absensi.contoh.com/form',
  '0 8 * * 1-5',   -- setiap Senin-Jumat jam 08:00
  1,
  'Isi form absensi harian otomatis',
  JSON_ARRAY(
    JSON_OBJECT('action','fill','selector_type','css','selector','#nama','value','Budi Santoso'),
    JSON_OBJECT('action','select','selector_type','css','selector','#status','text','Hadir'),
    JSON_OBJECT('action','click','selector_type','css','selector','button[type="submit"]'),
    JSON_OBJECT('action','wait','seconds',2),
    JSON_OBJECT('action','screenshot')
  )
);
```

Lalu restart app agar jadwal terbaru terbaca:
```bash
docker compose restart app
```

## Aksi (action) yang Didukung di `steps_json`

| action              | Field wajib                          | Keterangan                                      |
|---------------------|----------------------------------------|--------------------------------------------------|
| `fill`               | `selector`, `value`                    | Isi input teks/textarea                          |
| `click`              | `selector`                             | Klik tombol/link/checkbox                        |
| `select`             | `selector`, `value` **atau** `text`     | Pilih opsi di `<select>` dropdown                |
| `wait`               | `seconds`                              | Jeda beberapa detik (misal tunggu animasi/loading)|
| `wait_for_element`   | `selector`                             | Tunggu elemen muncul dulu (misal setelah AJAX)   |
| `goto`               | `url`                                  | Pindah ke URL lain di tengah alur                |
| `screenshot`         | -                                       | Simpan screenshot kondisi browser saat ini        |

`selector_type` bisa `css` (default), `xpath`, `id`, `name`, atau `class`.

### Cara dapat selector CSS/XPath elemen di web target

1. Buka web target di browser biasa
2. Klik kanan elemen (input/button) → **Inspect**
3. Di DevTools, klik kanan elemen di HTML → **Copy → Copy selector** (untuk CSS)
   atau **Copy → Copy XPath**
4. Pakai hasil copy itu sebagai `selector`

## Testing Task Sebelum Diaktifkan (Sangat Disarankan)

Jangan langsung aktifkan (`enabled=1`) task baru. Set `enabled=0` dulu, lalu test manual:

```bash
docker compose exec app python run_now.py submit_absensi_harian
```

Sambil buka noVNC (`http://localhost:7900`) untuk lihat browser mengisi form secara
live. Kalau sudah berjalan sesuai harapan, baru set `enabled=1` di database.

## Melihat Riwayat Eksekusi

```sql
SELECT * FROM automation_logs ORDER BY started_at DESC LIMIT 20;
```

Kalau `status = 'FAILED'`, kolom `message` biasanya mencantumkan path screenshot
error yang tersimpan di volume `app_screenshots` — bisa diambil dengan:
```bash
docker compose cp app:/app/screenshots/<nama_file>.png ./
```

## Catatan Penting

- **Login/kredensial**: kalau form butuh login, tambahkan step `fill` untuk
  username/password + `click` untuk tombol login sebagai langkah awal sebelum
  mengisi form utamanya.
- **Elemen dinamis (React/Vue/AJAX)**: gunakan `wait_for_element` atau `wait`
  sebelum `fill`/`click` supaya Selenium tidak mencoba klik elemen yang belum
  muncul di halaman.
- **CAPTCHA**: Selenium tidak bisa menyelesaikan CAPTCHA otomatis. Kalau web
  target pakai CAPTCHA, automation ini tidak akan bisa lolos di bagian itu.
- Timezone scheduler diset ke `Asia/Jakarta` di `app/scheduler.py`.
- Untuk menonaktifkan sementara: update `enabled=0` pada task terkait, lalu
  `docker compose restart app`.
