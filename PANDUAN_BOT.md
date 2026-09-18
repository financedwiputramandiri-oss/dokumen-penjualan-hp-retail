# Panduan Bot Penyapu Order Sheet

Bot ini bekerja tiap 12 jam:

1. Menanyakan ke Google Drive: order sheet mana yang berubah sejak sapuan lalu
2. Untuk yang berubah saja, **membaca isi tab PO langsung** lewat Sheets API
3. **Membandingkan dengan sapuan sebelumnya** — kalau ada PO lama yang qty
   atau rumusnya berubah, bot melapor
4. **Membuat draf dokumen sendiri** untuk PO yang ATO-nya sudah terisi, dan
   **membuat ulang** draf PO yang direvisi
5. Menaruh laporannya ke Google Drive

## Draf dokumen dibuat dan diperbarui sendiri

Sesuai arahan Yosua: ATO terisi berarti pesanan final untuk pertama kali, tapi
**tidak final selamanya**. Kalau direvisi, dokumennya wajib mengikuti angka
terbaru.

Yang dikerjakan bot:

| Keadaan PO | Yang dilakukan bot |
|---|---|
| ATO belum terisi | Tidak membuat apa-apa |
| ATO terisi, angka **cocok** dengan order sheet | Membuat draf Invoice, Surat Jalan, Faktur Pajak, Packing List |
| ATO terisi, angka **belum cocok** | **Tidak membuat dokumen.** Masalahnya dicatat di laporan |
| Qty / nilai / cara bayar / jumlah baris direvisi | Dokumen **dibuat ulang**, draf lama dipindahkan ke `_KEDALUWARSA` |
| Hanya rumusnya yang berubah, angkanya tetap | Alarm tetap berbunyi, tapi dokumen **tidak** dibuat ulang — isinya sama |
| Tidak ada perubahan | Tidak menulis apa-apa |

Letak berkasnya:

```
keluaran/draf/
  Order_Sheet_Agustus_2026/
    PO_20_Agustus_-_Miniku/
      INVOICE_PO_20_Agustus_-_Miniku.xlsx
      SURAT_JALAN_PO_20_Agustus_-_Miniku.xlsx
      FAKTUR_PAJAK_PO_20_Agustus_-_Miniku.xlsx
      PACKING_LIST_PO_20_Agustus_-_Miniku.xlsx
  _KEDALUWARSA/
    PO_20_Agustus_-_Miniku__20260912_062821/   <- draf sebelum revisi
```

**Draf lama tidak pernah ditimpa**, selalu dipindahkan ke `_KEDALUWARSA` dulu.
Jadi kalau ada yang bertanya "faktur yang kemarin angkanya berapa", jawabannya
masih ada.

Kalau mau sekalian PDF-nya, ubah `draf_pdf: true` di `config/bot.yaml`. Perlu
LibreOffice terpasang, dan sapuannya jadi jauh lebih lama.

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

### Langkah 7b — Beri izin folder dokumen

Folder ini **sudah dibuatkan** di My Drive Bapak:

**DOKUMEN OTOMATIS HAPPY PUMPKIN**
https://drive.google.com/drive/folders/1kucuLO3P4yZUnRgXO8ISvxXcHa9531tP

ID-nya sudah terisi di `config/bot.yaml` pada baris `folder_dokumen_id`, jadi
tidak perlu diisi lagi. Yang perlu Bapak lakukan hanya **Share folder ini ke
alamat email bot dengan akses Editor**.

> **Perhatikan bedanya, ini penting:**
>
> | Folder | Akses bot | Alasan |
> |---|---|---|
> | Order Sheet 2025 & 2026 | **Viewer** | bot hanya membaca, tidak boleh bisa mengubah order sheet |
> | LAPORAN BOT | **Editor** | bot menaruh laporan di sini |
> | DOKUMEN OTOMATIS | **Editor** | bot menaruh Invoice, Surat Jalan, Faktur Pajak di sini |
>
> Jangan memberi Editor pada folder order sheet. Kalau bot hanya Viewer di
> sana, order sheet Bapak aman apa pun yang terjadi.

Isi foldernya akan tersusun begini, dibuat sendiri oleh bot:

```
DOKUMEN OTOMATIS HAPPY PUMPKIN/
  Order Sheet Agustus 2026/
    PO 20 Agustus - Miniku/
      INVOICE_PO_20_Agustus_-_Miniku.xlsx
      SURAT_JALAN_PO_20_Agustus_-_Miniku.xlsx
      FAKTUR_PAJAK_PO_20_Agustus_-_Miniku.xlsx
      PACKING_LIST_PO_20_Agustus_-_Miniku.xlsx
    PO 31 Agustus - Haritsa/
      ...
```

Kalau sebuah PO direvisi, berkas di Drive **ditimpa** dengan yang terbaru —
bukan ditambah — supaya tidak ada dua "Invoice Miniku" yang membingungkan.
Versi lamanya tetap aman di folder `_KEDALUWARSA` pada komputer yang
menjalankan bot.

Kalau Bapak tidak mau dokumennya naik ke Drive, kosongkan `folder_dokumen_id`.

### Langkah 8 — Periksa dulu, baru jalankan

Ketik ini untuk memastikan semua langkah di atas sudah benar:

```
python3 jalankan.py periksa-bot
```

Perintah ini **hanya membaca**, tidak mengubah apa pun. Hasilnya seperti ini:

```
PEMERIKSAAN PERSIAPAN BOT
  [OK   ] Berkas kunci bot         terbaca, bot = penyapu-order-sheet@...
  [OK   ] Sambungan ke Google      berhasil
  [OK   ] Folder 'Order Sheet 2026'  12 order sheet terbaca
  [BELUM] Folder dokumen           tidak bisa dibaca: akses ditolak

MASIH ADA 1 HAL YANG PERLU DIBERESKAN:
  1. Folder dokumen: Share folder ini ke penyapu-order-sheet@... sebagai
     EDITOR (bukan Viewer, karena bot menaruh berkas di sini)
```

Kalau ada yang **BELUM**, pesannya menyebut langkah mana yang harus diperbaiki.
Beresi dulu, lalu jalankan `periksa-bot` lagi sampai semuanya **OK**.

### Langkah 9 — Coba jalankan

```
python3 jalankan.py sapu
```

Kalau berhasil, muncul alamat email bot, daftar order sheet yang ditarik, dan
letak laporannya.

---

## Menjalankan otomatis tiap 12 jam

### Kalau memakai Windows

Tidak perlu mengetik apa pun di Task Scheduler. Di folder `jadwal/` sudah ada
berkas siap pakai:

| Berkas | Gunanya |
|---|---|
| `sapu.bat` | yang benar-benar menjalankan sapuan. Boleh juga diklik dua kali kalau mau menyapu sekarang |
| `pasang-jadwal.bat` | memasang jadwalnya di Task Scheduler |
| `hapus-jadwal.bat` | menghapus jadwalnya lagi |

**Langkahnya:**

1. Buka folder proyek, masuk ke folder `jadwal`
2. **Klik KANAN** `pasang-jadwal.bat`
3. Pilih **Run as administrator**
4. Kalau muncul peringatan Windows, pilih **Yes**
5. Tunggu sampai tertulis `JADWAL BERHASIL DIPASANG`, lalu tekan sembarang
   tombol untuk menutup

Selesai. Bot jalan sendiri jam **06:00** dan **18:00** setiap hari.

**Mencoba tanpa menunggu jamnya.** Klik dua kali `sapu.bat`. Kalau selesai
tanpa galat, jadwalnya pasti jalan juga.

**Melihat bot pernah jalan atau tidak.** Buka
`keluaran\sapuan\log-sapuan.txt`. Tiap sapuan menulis baris `MULAI` dan
`SELESAI` beserta jam dan hasilnya.

#### Dua hal yang perlu dipahami

**1. Komputer harus menyala DAN Bapak harus sudah login.**
Jadwalnya sengaja dipasang dengan `/IT` — hanya jalan saat Bapak login.
Itu bukan kekurangan, itu keharusan: `folder_draf` menunjuk ke
`G:\My Drive\...` milik Google Drive for Desktop, dan drive `G:` itu belum
ada sebelum Bapak login. Kalau bot dipaksa jalan saat belum login, semua
dokumennya gagal ditulis.

Kalau jam 06:00 komputernya mati, Windows menjalankan sapuan yang terlewat
begitu komputer menyala. Tidak ada sapuan yang hilang.

**2. Kalau bot dipindahkan ke komputer lain, hapus jadwal di komputer lama.**
Klik kanan `hapus-jadwal.bat` → Run as administrator. Dua bot yang menyapu
bersamaan akan saling menimpa `data/kondisi_sapu.json` dan laporannya jadi
kacau.

#### Kalau `pasang-jadwal.bat` gagal

Pasang manual lewat Task Scheduler:

1. Tekan tombol Windows, ketik `Task Scheduler`, buka
2. Menu kanan: **Create Task** (bukan *Create Basic Task*)
3. Tab **General**
   - Name: `Sapu Order Sheet Happy Pumpkin`
   - Pilih **Run only when user is logged on** ← penting, jangan yang satunya
4. Tab **Triggers** → **New**
   - Begin the task: **On a schedule**, **Daily**, mulai jam `06:00`
   - Centang **Repeat task every** → ketik `12 hours`
   - For a duration of: **Indefinitely**
5. Tab **Actions** → **New**
   - Action: **Start a program**
   - Program/script: tekan **Browse**, pilih `jadwal\sapu.bat` di folder proyek
6. Tab **Conditions** → hilangkan centang
   **Start the task only if the computer is on AC power**, supaya laptop tetap
   menyapu walau sedang tidak dicolok
7. **OK**

### Kalau memakai Linux atau Mac

```
crontab -e
```

Tambahkan satu baris (jam 06:00 dan 18:00 setiap hari):

```
0 6,18 * * * cd /path/ke/dokumen-penjualan-hp-retail && /usr/bin/python3 jalankan.py sapu >> keluaran/sapuan/log.txt 2>&1
```

Ganti `/path/ke/` dengan lokasi folder proyek yang sebenarnya.

Berkas contoh siap pakai ada di `jadwal/crontab-contoh.txt` dan
`jadwal/systemd-contoh.md`.

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

---

## Pindah ke komputer lain

Bot tidak terikat pada satu komputer. Boleh dicoba dulu di laptop, lalu
dipindahkan ke komputer kantor atau server kapan saja.

Yang perlu **ikut pindah** hanya dua berkas:

| Berkas | Isinya | Kalau tertinggal |
|---|---|---|
| `config/kredensial_bot.json` | kunci akun layanan | bot tidak bisa masuk ke Google |
| `data/kondisi_sapu.json` | ingatan sapuan terakhir | bot menganggap semua PO baru, lalu membuat ulang seluruh draf sekali |

Selebihnya (program, pengaturan, panduan) ada di git — cukup `git clone` lagi
di komputer baru.

Langkahnya:

1. Di komputer baru: `git clone` repo ini, lalu `pip3 install -r requirements.txt`
2. Salin kedua berkas di atas dari komputer lama (pakai flashdisk atau
   folder Drive pribadi — **jangan lewat WhatsApp atau email**)
3. Jalankan `python3 jalankan.py periksa-bot` sampai semuanya OK
4. Pasang penjadwalnya (lihat folder `jadwal/`)
5. **Matikan penjadwal di komputer lama**, supaya tidak ada dua bot yang
   menyapu bersamaan

Akun layanannya **tidak perlu dibuat ulang**. Alamat email bot dan semua izin
folder tetap berlaku, karena izinnya melekat pada akun layanan, bukan pada
komputernya.

> Kalau `data/kondisi_sapu.json` tertinggal, tidak ada yang rusak — bot hanya
> membuat ulang semua draf satu kali, lalu tenang lagi. Isi folder Drive tetap
> benar karena berkas bernama sama ditimpa, bukan ditambah.

### Jangan jalankan dua bot sekaligus

Dua bot yang menyapu bersamaan akan saling menimpa `kondisi_sapu.json` dan bisa
memunculkan alarm yang membingungkan. Satu komputer saja yang menjalankan
penjadwal.

---

## Kenapa dokumen tidak naik sendiri ke Drive

Google punya batasan yang tidak bisa dilewati: **akun layanan tidak punya jatah
penyimpanan Drive.** Pesan resminya:

    Service Accounts do not have storage quota.
    reason: storageQuotaExceeded

Artinya bot **tidak bisa membuat berkas baru** di My Drive siapa pun, walaupun
sudah diberi peran Editor. Menambah izin tidak akan menolong. (Membuat folder
tetap bisa, karena folder tidak memakan ruang.)

Dua jalan keluar resmi dari Google — Shared Drive dan OAuth delegation —
keduanya **butuh langganan Google Workspace**, sedangkan akun Happy Pumpkin
memakai `@gmail.com` biasa.

### Jalan keluar yang dipakai: Google Drive for Desktop

Cara paling sederhana, gratis, dan tidak mengubah cara kerja bot sama sekali.

1. Pasang **Google Drive for Desktop** dari https://www.google.com/drive/download/
2. Login dengan akun Bapak. Akan muncul drive baru di komputer, biasanya `G:`
3. Buat folder di dalamnya, misalnya `G:\My Drive\DOKUMEN OTOMATIS HAPPY PUMPKIN`
4. Di `config/bot.yaml`, ubah dua baris:

```yaml
folder_draf: "G:/My Drive/DOKUMEN OTOMATIS HAPPY PUMPKIN"
folder_dokumen_id: ""
```

Sejak itu bot menulis dokumen ke folder tersebut seperti biasa, dan Google Drive
for Desktop yang menyalinkannya ke Drive. Berkasnya **dimiliki Bapak**, bukan
akun layanan, jadi tidak kena batasan kuota.

`folder_dokumen_id` dikosongkan supaya bot berhenti mencoba mengunggah sendiri.

### Kalau Drive for Desktop tidak dipakai

Kosongkan saja `folder_dokumen_id`. Dokumen tetap dibuat lengkap di
`keluaran/draf/`, tinggal disalin ke Drive secara manual kalau perlu.

Laporan sapuan **tetap naik ke Drive** dengan normal — laporan diunggah ke
folder LAPORAN BOT, dan ukurannya kecil... tapi perlu dicatat: laporan pun
berkas baru, jadi kemungkinan besar ikut tertolak. Kalau begitu, kosongkan juga
`folder_laporan_id`; laporannya tetap tersimpan di `keluaran/sapuan/`.

---

# Bot dipakai dari beberapa perangkat

Pertanyaan Yosua 18 September 2026: bagaimana supaya bot bisa dipakai dari
laptop maupun komputer kantor.

## Yang perlu dipisahkan dulu

| Yang mau dilakukan | Butuh apa |
|---|---|
| **Mengambil dokumen hasil bot** | tidak perlu apa-apa — cukup buka folder Drive |
| **Membuat dokumen manual** | kode + Python. Tidak perlu kunci bot |
| **Menjalankan sapuan otomatis** | kode + kunci bot + Drive for Desktop |

Yang pertama sudah jalan sekarang di semua perangkat, termasuk HP.

## Susunan yang dianjurkan

Taruh folder proyeknya **DI DALAM** folder Drive yang disinkronkan:

    G:\My Drive\
      DOKUMEN OTOMATIS HAPPY PUMPKIN\     <- hasil dokumen
      dokumen-penjualan-hp-retail\        <- folder proyek, ikut disinkronkan
        config\
        src\
        jadwal\

Lalu di `config/bot.yaml` tulis alamat RELATIF:

    folder_draf: "../DOKUMEN OTOMATIS HAPPY PUMPKIN"

Alamat relatif dihitung dari folder proyek, jadi **satu config yang sama
langsung benar di semua komputer** — tidak peduli drive-nya G:, H:, atau apa
pun. Kode, config, dan kunci botnya ikut tersinkron sendiri, jadi tidak ada
lagi "komputer ini kodenya masih lama".

## SATU komputer saja yang memasang jadwal

Ini tidak bisa ditawar. Yang boleh jalan di banyak komputer hanya perintah
manual (`daftar`, `periksa`, `buat`, `buat-semua`, `rekap`, `faktur-pajak`).

Sebabnya `data/kondisi_sapu.json`: berkas itu mencatat sidik jari tiap PO.
Kalau dua komputer menyapu bergantian, catatannya saling menimpa, dan seluruh
dokumen dibuat ulang berkali-kali tanpa ada yang sadar.

Program sekarang **mencatat nama komputer yang menyapu terakhir**. Kalau
sapuan berikutnya datang dari komputer lain, laporan sapuan memberi
peringatan dan menyebut cara membereskannya. Peringatan itu bukan larangan
menjalankan manual — hanya penanda kalau ada dua jadwal hidup bersamaan.

Di komputer yang **tidak** dipakai menjadwal: klik kanan
`jadwal\hapus-jadwal.bat` -> **Run as administrator**.

## Kunci bot ikut tersinkron — keputusan Bapak

Kalau folder proyek ditaruh di dalam Drive, `config\kredensial_bot.json` ikut
naik ke Drive Bapak.

| | |
|---|---|
| Untungnya | tidak perlu menyalin kunci lewat flash disk tiap ganti komputer |
| Risikonya | **siapa pun yang diberi akses ke folder itu ikut mendapat kunci botnya** |

Karena itu: **folder proyek jangan pernah di-Share ke siapa pun.** Kalau
sewaktu-waktu perlu berbagi dokumen, bagikan folder
`DOKUMEN OTOMATIS HAPPY PUMPKIN` saja, jangan folder proyeknya.

Kalau lebih tenang menyimpan kuncinya di luar Drive, taruh di folder lokal
lalu arahkan di `config/bot.yaml`:

    berkas_kredensial: "C:/kunci-bot/kredensial_bot.json"

Konsekuensinya alamat itu harus ada di tiap komputer.

## Order sheet tetap hanya bisa DIBACA

Tidak ada yang berubah di sini. Akun layanan bot punya izin **Viewer** pada
folder order sheet, jadi bot tidak akan pernah bisa mengubahnya, dari
komputer mana pun. Jangan pernah menaikkannya menjadi Editor.
