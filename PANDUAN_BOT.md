# Panduan Bot Penyapu Order Sheet

Bot ini bekerja tiap 12 jam:

1. Menanyakan ke Google Drive: order sheet mana yang berubah sejak sapuan lalu
2. Untuk yang berubah saja, **membaca isi tab PO langsung** lewat Sheets API
3. **Membuat draf dokumen** untuk PO yang ATO-nya sudah terisi
4. **Membandingkan dengan sapuan sebelumnya** — kalau ada PO lama yang qty
   atau rumusnya berubah, bot melapor
5. Menaruh laporannya ke Google Drive

## Bot TIDAK mengunduh order sheet

Bot membaca tab satu per satu lewat Sheets API, bukan mengunduh seluruh
spreadsheet. Bedanya besar:

| | Kalau mengunduh berkas | Cara yang dipakai sekarang |
|---|---|---|
| Data ditarik tiap sapuan | ~25 MB, 21 berkas penuh | hanya sel tab PO yang berubah |
| Kalau tidak ada yang berubah | tetap 21 unduhan | **0 panggilan** |
| Kalau 1 order sheet berubah | tetap 21 unduhan | 2 panggilan |
| Order Sheet Juni 2025 (11,4 MB) | GAGAL, ditolak Google | terbaca normal |
| Nama tab | terpotong 31 huruf | lengkap |
| Salinan data di komputer | ada | tidak ada |

Order sheet yang tidak berubah **dilewati sama sekali** — bot tahu dari waktu
ubah yang dicatat Google Drive, tanpa perlu membaca isinya. Jadi order sheet
lama yang sudah selesai tidak ditarik berulang tiap hari.

Kalau suatu saat perlu memaksa bot membaca semuanya lagi, ubah
`config/bot.yaml` -> `lewati_yang_tidak_berubah: false`.

---

## Bagian yang harus Bapak kerjakan sendiri

Membuat akun layanan (*service account*) harus lewat Google Cloud Console dan
tidak bisa dikerjakan dari sini. Butuh sekitar **10 menit, sekali saja**.

Akun layanan itu semacam "karyawan robot": punya alamat email sendiri, tapi
tidak bisa login seperti manusia. Folder order sheet cukup di-*Share* ke alamat
itu, lalu bot bisa membaca sendiri tanpa memakai akun Bapak.

### Langkah 1 — Buat proyek

1. Buka https://console.cloud.google.com/
2. Login dengan `finance.dwiputramandiri@gmail.com`
3. Di kanan atas, klik pilihan proyek → **NEW PROJECT**
4. Nama proyek: `happy-pumpkin-bot` → **CREATE**

### Langkah 2 — Nyalakan dua layanan

1. Buka https://console.cloud.google.com/apis/library
2. Cari **Google Drive API** → **ENABLE**
3. Cari **Google Sheets API** → **ENABLE**

### Langkah 3 — Buat akun layanan

1. Buka https://console.cloud.google.com/iam-admin/serviceaccounts
2. **CREATE SERVICE ACCOUNT**
3. Nama: `penyapu-order-sheet` → **CREATE AND CONTINUE**
4. Bagian *Grant this service account access* dilewati saja → **DONE**

### Langkah 4 — Ambil kuncinya

1. Klik akun layanan yang baru dibuat
2. Tab **KEYS** → **ADD KEY** → **Create new key**
3. Pilih **JSON** → **CREATE**
4. Berkas JSON otomatis terunduh
5. Ganti namanya jadi **`kredensial_bot.json`**, taruh di folder **`config/`**

> Berkas ini seperti kunci rumah. Jangan dikirim lewat WhatsApp atau email,
> jangan diunggah ke mana pun. Sudah dikunci supaya tidak ikut masuk git.

### Langkah 5 — Salin alamat email botnya

Di halaman akun layanan ada alamat seperti:

```
penyapu-order-sheet@happy-pumpkin-bot.iam.gserviceaccount.com
```

Salin alamat itu.

### Langkah 6 — Beri izin ke folder order sheet

Ini harus dilakukan oleh **pemilik order sheet**, yaitu
`happypumpkinkids.id@gmail.com`.

Untuk **kedua** folder ini:

- Order Sheet 2026 — https://drive.google.com/drive/folders/1RDH_C3ygjlTwgrxyiTlGtsp3zjTccNTB
- Order Sheet 2025 — https://drive.google.com/drive/folders/1PiXCgbeXMHDOo6Doj5XUPnzmfl9A1S57

Caranya: klik kanan folder → **Share** → tempel alamat email bot → pilih
**Viewer** → hilangkan centang *Notify people* → **Share**.

> **Viewer** berarti bot hanya bisa MEMBACA. Bot tidak akan pernah bisa
> mengubah atau menghapus order sheet. Ini disengaja.

### Langkah 7 — Beri izin folder laporan

Buat satu folder baru di Drive Bapak, misalnya **`LAPORAN BOT HAPPY PUMPKIN`**,
lalu Share ke alamat bot dengan akses **Editor** (supaya bot bisa menaruh
laporan). Salin ID foldernya dari alamat di browser:

```
https://drive.google.com/drive/folders/<INI_ID_NYA>
```

Tempel ID itu ke `config/bot.yaml` pada baris `folder_laporan_id`.

### Langkah 8 — Coba jalankan

```
python3 jalankan.py sapu
```

Kalau berhasil, muncul alamat email bot, daftar order sheet yang ditarik, dan
letak laporannya.

---

## Menjalankan otomatis tiap 12 jam

### Kalau memakai Linux atau Mac

```
crontab -e
```

Tambahkan satu baris (jam 06:00 dan 18:00 setiap hari):

```
0 6,18 * * * cd /path/ke/dokumen-penjualan-hp-retail && /usr/bin/python3 jalankan.py sapu >> keluaran/sapuan/log.txt 2>&1
```

Ganti `/path/ke/` dengan lokasi folder proyek yang sebenarnya.

### Kalau memakai Windows

1. Buka **Task Scheduler** → **Create Basic Task**
2. Nama: `Sapu Order Sheet Happy Pumpkin`
3. Trigger: **Daily**, jam 06:00
4. Action: **Start a program**
   - Program: `python`
   - Arguments: `jalankan.py sapu`
   - Start in: folder proyek
5. Setelah selesai, buka **Properties** → tab **Triggers** → **Edit** →
   centang **Repeat task every** → isi **12 hours**

Berkas `jadwal/` di proyek ini berisi contoh siap pakai untuk keduanya.

---

## Arti laporan bot

Laporan berbentuk Excel dengan tiga lembar.

### Lembar RINGKASAN

Paling atas tertulis salah satu dari:

- **TIDAK ADA PERUBAHAN PENTING** — aman, tidak perlu tindakan
- **ADA N PERUBAHAN PENTING YANG PERLU DIPERIKSA** — ada PO lama yang berubah

### Lembar PERUBAHAN

| Tingkat | Artinya | Tindakan |
|---|---|---|
| **GENTING** | PO yang ATO-nya SUDAH terisi berubah angkanya atau rumusnya | Periksa. Dokumen yang sudah terbit mungkin jadi tidak cocok |
| **PERHATIAN** | Perubahan yang wajar, misal ATO baru terisi | Cukup dibaca |
| **KABAR** | PO baru terlihat pertama kali | Cukup dibaca |

Jenis perubahan yang dipantau:

| Jenis | Artinya |
|---|---|
| Qty berubah | Jumlah barang bertambah atau berkurang |
| Susunan qty berubah | Total sama, tapi pembagian per artikel/ukuran bergeser |
| Jumlah baris berubah | Ada baris artikel ditambah atau dihapus |
| Nilai bersih berubah | Angka rupiah yang ditagihkan berubah |
| Nilai sebelum diskon berubah | Nilai kotor berubah |
| Cara bayar berubah | Kolom nett yang terisi penuh berpindah (TOP ↔ CBD ↔ COD) |
| Rumus berubah | Ada rumus diubah, walau angkanya belum berubah sekarang |
| ATO dikosongkan | PO yang tadinya terisi jadi kosong |
| Nilai tidak terbaca | Bukan perubahan. Hasil rumus gagal terbaca, perlu dicek manual |

### Lembar YANG DIPERIKSA

Daftar order sheet yang disapu, draf yang dibuat, dan masalah teknis yang
ditemui (misalnya order sheet terlalu besar untuk diunduh).

---

## Pertanyaan yang sering muncul

**Apakah bot bisa merusak order sheet?**
Tidak. Bot diberi akses **Viewer** ke folder order sheet — hanya bisa membaca.
Bot hanya bisa menulis ke folder laporan.

**Kalau laptop mati, apa botnya berhenti?**
Ya. Bot jalan di komputer tempat ia dipasang. Kalau ingin jalan terus tanpa
tergantung laptop, perlu dipasang di komputer yang selalu menyala.

**Apakah order sheet yang besar bisa dibaca?**
Bisa. Dulu Order Sheet Juni 2025 (11,4 MB) ditolak Google saat diekspor jadi
Excel. Sekarang bot tidak pernah mengekspor berkas — ia membaca tab langsung,
jadi ukuran berkas tidak lagi jadi masalah.

**Kenapa laporannya bilang banyak order sheet "dilewati"?**
Itu justru yang diharapkan. Artinya order sheet itu tidak berubah sejak sapuan
sebelumnya, jadi tidak perlu dibaca ulang. Yang dibaca hanya yang benar-benar
berubah.

**Bot menemukan perubahan, apa yang harus dilakukan?**
Buka order sheet yang disebut, lihat tab yang disebut. Bandingkan dengan kolom
"sebelumnya" dan "sekarang" di laporan. Kalau memang seharusnya berubah, tidak
apa-apa — sapuan berikutnya akan menganggapnya keadaan baru. Kalau tidak
seharusnya berubah, tanyakan ke yang mengedit.

**Apakah bot mengirim email atau WhatsApp?**
Belum. Laporannya ditaruh ke Google Drive. Kalau ingin diberi tahu lewat email,
bisa ditambahkan menyusul.
