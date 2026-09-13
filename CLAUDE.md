# CLAUDE.md — Proyek Otomatisasi Dokumen Penjualan

**CV Dwi Putra Mandiri · brand Happy Pumpkin**
Pemilik proyek: Yosua, Finance
Dipindahkan dari Claude.ai pada 10 September 2026

Berkas ini adalah ingatan proyek. Isinya konteks, temuan, dan keputusan yang
sudah diambil. Baca seluruhnya sebelum mengerjakan apa pun, dan jangan
mengulang penelusuran yang hasilnya sudah tercatat di sini.

---

## 1. Tujuan

Menghasilkan **Surat Jalan, Invoice, Packing List, dan Faktur Pajak** secara
otomatis dari order sheet, mengikuti ketentuan masing-masing customer, dan
ikut berubah setiap order sheet diperbarui.

## 2. Berkas

| Berkas | ID |
|---|---|
| Order sheet (sumber data) | `1yBWhMTFY8pLEhvEVFHI2hhrOouUx36aGjaE83ApcNhw` |
| OTOMATISASI (versi lama, tanpa sambungan) | `1poWqdvKjJ3gwixtBg2oeZgjhhtUn6ytum2pM297wBUs` |
| OTOMATISASI_HAPPY_PUMPKIN_SINKRON | `1lL-AXy2Th369iC4IJiS1-pM8BQGRnhCPZ5igL9oNpUM` |

Order sheet dimiliki `happypumpkinkids.id@gmail.com`, dibagikan ke
`finance.dwiputramandiri@gmail.com`.

Faktur dan surat jalan lama ada di folder Drive `DPM - INVOICE / SURAT JALAN`,
sekitar 120 berkas, Mei sampai Agustus 2026. Dipakai sebagai acuan format.

---

## 3. Struktur order sheet

### Tab

18 tab: `Harga Retail`, `Packing List Haritsa`, dan 16 tab PO dengan pola
nama `PO <tanggal> - <customer>`.

Nama tab yang memakai kurung: `Baby Wise (Surabaya)`, `Katamama (Tapos)`,
`Katamama (Cikarang)`. Saat mencocokkan ke master customer, buang tanda
kurungnya.

### Kolom tab PO

| Kolom | Isi |
|---|---|
| A | ARTICLE CODE |
| B | PRODUCT NAME |
| C | COLOUR |
| D–L | ORIGINAL PO, 9 kolom ukuran |
| M | TOTAL original PO |
| **N–V** | **AVAILABLE TO ORDER (ATO), 9 kolom ukuran — dasar semua dokumen** |
| W | TOTAL ATO |
| X | PRICE W/ VAT (sudah termasuk PPN) |
| Y | TOTAL ORI PO (VALUE) |
| Z | TOTAL ATO (VALUE) — nilai sebelum diskon |
| AA | LOSSES |
| AB | DISC |
| **AC** | **TOTAL VALUE — nilai bersih untuk customer TOP/Tempo (font biru tua)** |
| **AD** | **DISCOUNT CBD +1,5% — nilai bersih untuk customer CBD (font biru muda)** |
| **AE** | **DISCOUNT COD +1,5% — nilai bersih untuk customer COD (font biru muda)** |
| AF | NOTE (hanya ada di sebagian tab) |

### Blok bertumpuk — temuan paling menentukan

Satu tab PO bisa berisi beberapa tabel bertumpuk. Tiap tabel punya baris
judul `ARTICLE CODE` sendiri dan **sistem ukuran sendiri**, karena mewakili
kategori produk yang berbeda.

Seluruhnya 34 blok dari 15 PO berisi data, dengan 12 set label ukuran berbeda.

Contoh tab Miniku: 6 blok, 302 baris. Blok 2 memakai `0-3M / 3-6M / 6-12M /
S / M / L`, blok 3 memakai `1 / 2 / 3 / 4 / 5 / 6 / 7-8Y / 9-10Y`.

Kolom ukuran yang tidak terpakai **disembunyikan**, bukan dihapus.

### Tab Packing List

`Packing List Haritsa` bukan packing list model ekspor. Isinya daftar barang
yang benar-benar dikirim dalam satu batch, susunannya sama seperti blok PO,
tapi **qty-nya di kolom D–L**, bukan N–V, karena tidak punya blok ORIGINAL PO.

Isi: 6 baris artikel 42054.1.AT, 333 pcs, sebagian dari PO Haritsa yang
1.053 pcs.

---

## 4. Angka acuan

> **Diperbarui 11 September 2026.** Seluruh angka di bawah sudah diverifikasi
> ulang langsung terhadap order sheet oleh program di repo ini, bukan lagi
> hasil penelusuran manual. Lihat bagian 11 untuk hasil terbaru.

Dihitung dari order sheet per 7 September 2026, hanya baris dengan ATO > 0:

| | |
|---|---|
| PO berisi data | 15 |
| Blok | 34 |
| Baris | 1.073 |
| Total qty | **7.609 pcs** |
| Nilai sebelum diskon | **Rp500.874.100** |
| Artikel di Harga Retail | 195 |

Blok terbesar: Miniku blok 3, 227 baris.
PO terbesar: Miniku, 288 baris, 1.783 pcs, Rp120.242.700 sebelum diskon.

Nilai bersih per tab (kolom AC), untuk pencocokan:

| Tab | Sebelum diskon | TOTAL VALUE | Rasio |
|---|---:|---:|---:|
| Haritsa 31 Agu | 57.253.000 | 42.939.750 | 0,750 |
| Baby Wise Surabaya 31 Agu | 22.179.900 | 16.080.428 | 0,725 |
| Natasha 28 Agu | 537.900 | 430.320 | 0,800 |
| Mae Bebe 26 Agu | 7.488.000 | 5.616.000 | 0,750 |
| Panda & Bear 25 Agu | 6.252.000 | 5.126.640 | 0,820 |
| Pratama 25 Agu | 24.318.000 | 18.238.500 | 0,750 |
| Katamama Tapos 24 Agu | 24.790.000 | 19.336.200 | 0,780 |
| Katamama Cikarang 22 Agu | 29.397.600 | 22.930.128 | 0,780 |
| Yulis 22 Agu | 28.935.800 | 22.569.924 | 0,780 |
| Miniku 20 Agu | 120.242.700 | 93.789.306 | 0,780 |
| Mae Bebe 19 Agu | 50.734.500 | 38.050.875 | 0,750 |
| Baby Wise 19 Agu | 56.184.900 | 42.138.675 | 0,750 |
| Baby Fame 14 Agu | 30.532.000 | 22.899.000 | 0,750 |
| Dunia Bayi 13 Agu | 40.865.900 | 30.649.425 | 0,750 |
| Canina Baby 13 Agu | 1.161.900 | 906.282 | 0,780 |

Rasio hanya untuk pemeriksaan. **Jangan dipakai sebagai sumber diskon** —
selalu ambil nilai bersihnya langsung dari kolomnya.

---

## 5. Ketentuan per customer

| Customer | Format invoice | Nama di dokumen | Alamat | NPWP |
|---|---|---|---|---|
| Haritsa | **per artikel + ukuran** | PT. Haritsa Pipa Rezeki | ada | — |
| Katamama Tapos | **per artikel + ukuran** | PT. MAMA PAPA JUARA | ada | — |
| Katamama Cikarang | **per artikel + ukuran** | PT. MAMA PAPA JUARA | — | — |
| Baby Wise | per artikel | BABY WISE INDONESIA | ada | — |
| Baby Wise Surabaya | per artikel | — | — | — |
| Natasha | per artikel | — | — | — |
| Mae Bebe | per artikel | JONNI SETIADI | ada | — |
| Panda & Bear | per artikel | — | — | — |
| Pratama | per artikel | CV. YAKIN ESOK SUKSES | ada | — |
| Yulis Baby Shop | per artikel | — | — | — |
| Miniku | per artikel | — | — | — |
| Baby Fame | per artikel | — | — | — |
| Dunia Bayi | per artikel | PT. DUNIA BAYI SENTOSA | ada | — |
| Canina Baby | per artikel | — | — | — |

Alamat yang sudah diketahui:

- **Haritsa** — JL. T. Hasan Dek, RT 000 RW 000 Beurawe, Kuta Alam
- **Baby Wise** — Ruko Tol Boulevard Blok AH-2/3C-3D, BSD City, Rawabuntu,
  Serpong, Tangerang Selatan, Banten 15318
- **Mae Bebe** — Jl. Bintaro Utama V Blok EA. 1/5, RT.001 RW.010,
  Kel. Jurangmangu Timur, Kec. Pondok Aren, Tangerang Selatan
- **Pratama** — Jl. P. Diponegoro 88, Tamanan Tulungagung, Jawa Timur 66217
- **Katamama Tapos** — Ruko Nirwana Estate, Jl. Raya Cikaret, Pabuaran,
  Cibinong, Kab. Bogor, Jawa Barat
- **Dunia Bayi** — Pertokoan Udayana Blok Jl. Letda Made Putra 37A,
  Dauh Puri, Denpasar Barat, Kota Denpasar, Bali 80113

---

## 6. Format dokumen

Acuan: berkas `0050726 YAKIN ESOK SUKSES (PRATAMA)` dan
`0310726 MAE BEBE JONNI SETIADI` di Drive.

### Kop, dipakai semua dokumen

Logo di kiri. Di sebelahnya:

```
CV DWI PUTRA MANDIRI
Jl. Jelambar Baru Raya No. 46, Grogol Petamburan
Jakarta Barat - 11460, Indonesia
Phone. +62 (021) 22561723
Wa:(+62) 0877 7950 0992
Email : DPMTEX@yahoo.com
```

Di kanan: `Jakarta, <tanggal>`, lalu `Kepada Yth.`, nama dan alamat customer.

### Invoice

Kolom A sampai H:

```
No. | ARTICLE CODE | DESKRIPSI BARANG | Qty (PCS) |
Harga (Satuan) | Diskon (%) | Nilai (Diskon) | Jumlah
```

Persen diskon berada di satu sel di baris judul, nilai rupiahnya dihitung
per baris.

Penutup di kolom G–H, urutannya:
Subtotal, Diskon, Total, Uang Muka, DPP, PPN, Total.

Info rekening di kolom B:

```
PEMBAYARAN DITRANSFER KE REKENING :
CV. DWI PUTRA MANDIRI
BANK BCA
A/C NO. : 277 950 8000
```

`Hormat kami,` di kanan bawah.

Invoice **tidak dipecah per tabel** — satu tabel menerus untuk seluruh PO.
Warna **tidak pernah** masuk invoice.

Baris diskon CBD/COD **tidak dicetak** di invoice; faktur asli DPM tidak
memuatnya.

### Surat Jalan

```
No. | ARTICLE CODE | PRODUCT NAME | COLOUR | <9 kolom ukuran> | TOTAL
```

Satu tabel per blok, bertumpuk dalam satu dokumen. Tiap tabel punya baris
judul sendiri dengan label ukurannya sendiri, nomor urut mulai dari 1 lagi,
dan baris TOTAL di bawahnya. Di bawah semua tabel ada TOTAL SELURUH PO.

Tanda tangan: `Pengirim :` / `Penerima :` / `Mengetahui :`

### Packing List

Sama seperti Surat Jalan, ditambah kolom **JUMLAH DIKIRIM** dan **NO. KOLI**
yang diisi gudang. Berat dan dimensi tidak ada di order sheet dan tidak boleh
ditebak rumus.

### Faktur Pajak

Bukan untuk dicetak. Berisi data siap ketik ke Coretax: nama dan NPWP
pembeli, alamat, nomor referensi, tanggal, DPP, PPN, total. Ditambah rincian
per artikel.

Harga di order sheet sudah termasuk PPN, jadi DPP dihitung mundur.
Tarif sementara 11% — **perlu dicek apakah masih sesuai aturan yang berlaku**.

---

## 7. Temuan yang jangan diulang penelusurannya

### Deskripsi barang selalu sama dengan master harga

Dicek 18 kode artikel dari dua faktur berbeda, semuanya sama huruf per huruf,
termasuk yang aneh seperti `Milo Set (Small Size)` yang memakai kurung. Tidak
ada customer yang minta penamaan sendiri.

### Surat Jalan asli memang bertumpuk

Faktur Mae Bebe 0310726 membuktikan satu Surat Jalan memuat beberapa tabel
dengan judul ukuran berbeda. Struktur blok di order sheet bukan kekacauan.

### Tidak ada NPWP di Drive

Setelah menelusuri ±120 berkas faktur dan surat jalan Mei–Agustus 2026, tidak
ditemukan satu pun NPWP customer, dan tidak ada berkas faktur pajak.

### Kekhususan Haritsa yang belum dikonfirmasi

Berkas faktur Haritsa berisi sheet `FASHION` dan `SURAT JALAN - FASHION`,
dengan brand ditulis `BRAND : HAPPY PUMPKIN " FASHION "`. Kemungkinan Haritsa
menerima faktur terpisah per kategori produk.

### Selisih dengan Laporan Penjualan Agustus 2026

| Faktur | Laporan Penjualan | Order sheet | Selisih |
|---|---:|---:|---:|
| FA-013 Panda & Bear | 5.001.600 | 5.126.640 | 125.040 |
| FA-008 Canina | 1.161.900 | 906.282 | 255.618 |

Panda & Bear tercatat memakai potongan 20% padahal seharusnya 18%. Canina
tercatat tanpa potongan. FA-009 Baby Fame Rp22.899.000 sudah cocok persis.

### Kolom CBD sering belum ditarik penuh

Kolom `DISCOUNT CBD +1,5%` sering belum ditarik sampai baris terakhir oleh
Sales. Di baris yang terisi, nilainya persis `TOTAL VALUE × 0,985`.

**Aturannya: kolom yang terisi sebagian diabaikan seluruhnya, order itu
diperlakukan sebagai TOP.** Jangan ditambal sebagian.

Hasil penerapan pada order sheet Agustus 2026:

| Tab | Baris | AD terisi | Status | Nett dipakai |
|---|---:|---:|---|---:|
| Baby Wise Surabaya 31 Agu | 34 | 34 | CBD | 15.758.819 |
| Pratama 25 Agu | 25 | 25 | CBD | 17.964.922 |
| Katamama Tapos 24 Agu | 106 | 106 | CBD | 19.046.157 |
| Katamama Cikarang 22 Agu | 109 | 109 | CBD | 22.586.176 |
| Yulis 22 Agu | 148 | 148 | CBD | 22.118.526 |
| Canina Baby 13 Agu | 17 | 17 | CBD | 892.688 |
| Haritsa 31 Agu | 24 | 20 | TOP | 42.939.750 |
| Natasha 28 Agu | 8 | 0 | TOP | 430.320 |
| Mae Bebe 26 Agu | 6 | 0 | TOP | 5.616.000 |
| Panda & Bear 25 Agu | 12 | 0 | TOP | 5.126.640 |
| Miniku 20 Agu | 288 | 44 | TOP | 93.789.306 |
| Mae Bebe 19 Agu | 84 | 43 | TOP | 38.050.875 |
| Baby Wise 19 Agu | 105 | 46 | TOP | 42.138.675 |
| Baby Fame 14 Agu | 56 | 51 | TOP | 22.899.000 |
| Dunia Bayi 13 Agu | 51 | 49 | TOP | 30.649.425 |
| **Total nett** | | | | **380.007.279** |

Aturan ini terbukti benar lewat Baby Fame: kolom AD terisi 51 dari 56, jadi
TOP, nett Rp22.899.000 — cocok persis dengan FA-009 di Laporan Penjualan
Agustus 2026. Kalau kolom AD dipaksa dipakai, hasilnya Rp21.757.665 dan
meleset.

Karena penentuannya murni dari kelengkapan data, tidak perlu membaca warna
font atau status tersembunyi kolom lewat Sheets API.

---

## 8. Riwayat keputusan

| Keputusan | Alasan |
|---|---|
| Satu PO = satu Surat Jalan, bukan satu blok = satu dokumen | Sesuai praktik asli, terbukti dari faktur Mae Bebe di Drive |
| Invoice satu tabel menerus | Faktur asli tidak dipecah walaupun Surat Jalannya dipecah |
| Diskon diambil per order, bukan disimpan sebagai persen di master | Persen di master mudah basi dan sudah pernah salah |
| Berat dan koli diisi manual gudang | Tidak ada di order sheet, tidak boleh ditebak |
| MASTER_HARGA ditarik dari order sheet, tapi CEK HARGA tetap membandingkan harga baris PO dengan master | Alat kontrol tidak boleh memeriksa dirinya sendiri |
| Semua warna tabel diputihkan | Permintaan Yosua, 8 September 2026 |
| Pindah dari Apps Script ke rumus murni, lalu ke Claude Code | Apps Script dan script.google.com terkunci di akun Yosua |

---

## 9. Yang masih menggantung

| Hal | Keterangan |
|---|---|
| NPWP 14 customer | Tidak ada di Drive, harus diisi manual |
| Alamat 8 customer | Baby Wise Surabaya, Natasha, Panda & Bear, Katamama Cikarang, Yulis, Miniku, Baby Fame, Canina |
| Tarif PPN | Sementara 11%, perlu dicek |
| Akhiran Y pada label ukuran | Perlu dikonfirmasi ke Yosua. Sementara diaktifkan (2 -> 2Y) mengikuti contoh Yosua sendiri, bisa dimatikan di `config/pengaturan.yaml` |
| Faktur terpisah Haritsa | Apakah benar per kategori produk |
| Selisih FA-013 & FA-008 | Perlu ditelusuri mana yang benar |
| ~~Baby Wise 31 Agustus~~ | **SELESAI 11 Sep 2026.** Sudah terisi final: 121 baris, 991 pcs, Rp60.894.800, TOP, nett Rp44.148.730 |
| Termin pembayaran | Semua disetel 30 hari, belum dikonfirmasi |
| Logo | Belum ada berkasnya. Program sudah siap memasangnya: taruh di `config/`, tulis namanya di `perusahaan.yaml` |
| Nomor dokumen | Pola `0050726` = urut 005, bulan 07, tahun 26. Nomor urut tidak ditebak program — bawaannya dikosongkan |
| Tab `Packing List Haritsa` | **Sudah tidak ada** di order sheet per 11 Sep 2026. Perlu dipastikan memang dihapus |

---

## 10. Cara kerja yang diminta Yosua

- Bahasa Indonesia yang jelas dan sederhana. Rekan kerjanya kurang akrab
  dengan teknologi, jadi hasilnya harus bisa dipakai tanpa pelatihan.
- Keluaran berupa tabel yang rapi, selalu disertai ringkasan.
- Data berantakan dirapikan dan diseragamkan dulu sebelum diolah.
- Kalau ada data kurang atau tidak jelas, **tanya dulu**. Jangan ditebak.
- Ingatkan kalau ada yang berpotensi terlewat di laporan keuangan atau pajak.
- Berkas keluaran: Excel (.xlsx) atau PDF sesuai kebutuhan.

Pekerjaan rutin bulanan Yosua yang lebih luas, di luar proyek ini: laporan
pemasukan dan pengeluaran, kartu stok produk, laba perusahaan, sisa stok
produk, dan pelaporan pajak bulanan.


---

## 11. Verifikasi langsung terhadap order sheet — 11 September 2026

Order sheet dibaca langsung lewat konektor Google Drive, diunduh sebagai
`.xlsx`, lalu diolah program di repo ini. **Semua angka di bagian 4 dan 7
terbukti benar sampai rupiah terakhir.**

### Angka terbaru (seluruh order sheet)

| | Sebelumnya (7 Sep) | Sekarang (11 Sep) | Selisih |
|---|---:|---:|---:|
| PO berisi data | 15 | **16** | +1 |
| Blok | 34 | **37** | +3 |
| Baris | 1.073 | **1.194** | +121 |
| Qty | 7.609 pcs | **8.600 pcs** | +991 |
| Sebelum diskon | Rp500.874.100 | **Rp561.768.900** | +Rp60.894.800 |
| Nilai bersih | Rp380.007.279 | **Rp424.156.009** | +Rp44.148.730 |

**Seluruh selisih berasal dari satu tab saja: `PO 31 Agustus - Baby Wise`**,
yang di bagian 9 tercatat "kolom ATO sempat kosong". Tab itu kini terisi penuh.
Dikurangi tab tersebut, angkanya kembali persis ke angka acuan lama —
1.073 baris / 7.609 pcs / Rp500.874.100 / nett Rp380.007.279. Ini sekaligus
membuktikan pemindai di repo ini membaca order sheet dengan benar.

Tabel AD-terisi di bagian 7 juga cocok **seluruhnya**, ke-15 barisnya.

### Pemeriksaan menyeluruh yang lolos

Diperiksa pada semua 1.194 baris, bukan contoh:

| Pemeriksaan | Hasil |
|---|---|
| Tiap tab cocok dengan baris TOTAL miliknya sendiri | 16 dari 16 cocok |
| `qty x harga = nilai kotor` per baris | 1.194 dari 1.194 cocok |
| Kode artikel ada di `Harga Retail` | 0 tidak ketemu |
| Harga nol | 0 baris |
| Nama barang sama persis dengan master harga | 1.194 dari 1.194 sama |
| Harga PO sama dengan master harga | sama persis, rasio 1,0 untuk semua |

Temuan bagian 7 "deskripsi barang selalu sama dengan master harga" yang dulu
dicek pada 18 kode, kini terbukti untuk **seluruh** baris.

---

## 12. Temuan baru 11 September 2026

### Potongan CBD/COD tidak selalu 1,5% — judul kolomnya yang menentukan

Bagian 7 menyebut nilai kolom AD "persis TOTAL VALUE x 0,985". Itu hanya
benar untuk sebagian tab. Judul kolom AD berbeda-beda antar tab, dan nilainya
mengikuti judul itu:

| Tab | Judul kolom AD | Pengali sebenarnya |
|---|---|---:|
| Pratama, Katamama Tapos, Katamama Cikarang, Canina | `DISCOUNT CBD + 1.5%` | 0,985 |
| **Yulis Baby Shop** | `DISCOUNT CBD + 2%` | **0,98** |
| **Baby Wise (Surabaya)** | `DISCOUNT COD + 2%` | **0,98** |

Dua catatan penting:

1. Tab Baby Wise Surabaya menamai kolom AD sebagai **COD**, bukan CBD.
   Program memakai nama yang tertulis di order sheet, bukan menebak.
2. Ini justru menguatkan Aturan 2: kalau nett dihitung dari persentase
   tebakan 1,5%, Yulis meleset Rp112.850 dan Baby Wise Surabaya meleset
   Rp80.402. Karena nett diambil langsung dari kolomnya, keduanya tepat.

Program sekarang membaca tarif dari judul kolom dan memperingatkan kalau
angka sebenarnya tidak sesuai judulnya.

### Kolom DISC (AB) tidak bisa dipercaya di dua tab Baby Wise

| Tab | Kolom AB tertulis | Diskon sebenarnya dari nilai bersih |
|---|---:|---:|
| PO 31 Agustus - Baby Wise | 0% | **27,5%** |
| PO 31 Agustus - Baby Wise (Surabaya) | 0% | **27,5%** |

Nilai di kolom AC-nya sendiri sudah benar. Yang salah hanya kolom AB.
Program memakai nilai bersih (benar) dan memberi peringatan supaya kolom AB
dirapikan Sales. Di tab lain kolom AB seragam satu nilai dan cocok.

### Kolom ukuran ke-9 (L dan V) tidak pernah terpakai

Di **seluruh** 37 blok, judul kolom ke-9 selalu berisi angka `9`, dan
**tidak ada satu pun baris** yang punya qty di kolom V. Kolom ini sisa
rancangan lama. Program tetap membacanya dan akan memberi tahu kalau suatu
saat terisi.

### Label ukuran kembar dalam satu blok

Tab `PO 28 Agustus - Natasha` blok baris 5 memakai `7-8Y` **dua kali**
(posisi ke-6 dan ke-7). Tidak berdampak karena Natasha tidak dipecah per
ukuran, tapi program sekarang memberi peringatan kalau menemukan label kembar,
sebab invoice per ukuran bisa salah menggabungkan baris.

### Nama tab terpotong saat diunduh sebagai Excel

Excel membatasi nama sheet 31 huruf, jadi hasil unduhan menjadi
`PO 31 Agustus - Baby Wise (Sura` dan `PO 24 Agustus - Katamama (Tapos`.
Pencocokan ke master customer sudah tahan terhadap ini: nama persis menang
lebih dulu, baru kecocokan awalan terpanjang — supaya `Baby Wise` tidak
tertukar dengan `Baby Wise Surabaya`.

### Tab `Packing List Haritsa` sudah tidak ada

Order sheet per 11 September 2026 berisi 17 tab, tanpa `Packing List Haritsa`.
Program tetap mendukung tab berawalan `Packing List` (qty dibaca dari kolom
D–L) kalau nanti dibuat lagi.

### Cara membaca order sheet tanpa kredensial

Tidak perlu Sheets API dan tidak perlu kunci apa pun. Cukup
**File > Download > Microsoft Excel (.xlsx)** lalu simpan ke
`data/order_sheet.xlsx`. Ini sekaligus menyelesaikan hambatan "Apps Script
terkunci di akun Yosua" di bagian 8.

---

## 13. Isi repo ini

| Bagian | Berkas |
|---|---|
| Panduan rekan kerja | `PANDUAN.md` |
| Ringkasan teknis | `README.md` |
| Yang diisi manusia | `config/customer.csv`, `config/perusahaan.yaml`, `config/pengaturan.yaml` |
| Aturan 1 — pindai blok | `src/hp_dokumen/pemindai.py` |
| Aturan 2 — nilai bersih | `src/hp_dokumen/nilai_bersih.py` |
| Aturan 3 & 4 — label ukuran | `src/hp_dokumen/ukuran.py` |
| Pencocokan wajib | `src/hp_dokumen/rekonsiliasi.py` |
| Keempat dokumen | `src/hp_dokumen/dokumen/` |
| Laporan & rekap | `src/hp_dokumen/laporan.py` |
| Tes otomatis (28 tes) | `tests/` |

Perintah: `daftar`, `periksa`, `buat`, `buat-semua`, `rekap`.
Program **berhenti dan tidak membuat dokumen** kalau pencocokan gagal.


---

## 14. Perluasan 11 September 2026 — seluruh order sheet & bot penyapu

Arahan baru Yosua: sistem harus bisa mengeluarkan dokumen penjualan **kapan pun
untuk order sheet mana pun, lama maupun baru**, dikerjakan manual sehari-hari
oleh divisinya, dan otomatis mengeluarkan draf pertama begitu ATO terisi.

### Berkas yang jadi acuan

| Berkas | ID |
|---|---|
| OTOMATISASI_HAPPY_PUMPKIN_SINKRON (milik Yosua) | `1qkd-_wc3LoGcU7kQ8oJi70bGOMjLpvrPVBXzHeQa4Vw` |
| Folder order sheet 2026 | `1RDH_C3ygjlTwgrxyiTlGtsp3zjTccNTB` |
| Folder order sheet 2025 | `1PiXCgbeXMHDOo6Doj5XUPnzmfl9A1S57` |
| DATABASE CUSTOMER (diunggah 11 Sep 2026, milik Yosua) | `1ffT_GlCQSvKIHoAH25A8-OyqHzoFG1TATS0r1EETFN0` |
| SISTEM OTOMATISASI (ringkasan, diunggah 12 Sep 2026, milik Yosua) | `1Yld4InWIhMXj9uV8fM1pV_0mEUZD7SZse8FJZ5XWiJE` |
| ALUR KERJA SISTEM (diunggah 12 Sep 2026, milik Yosua) | `1ufPsXLUy42u2zfkexcFlPMGKtVCmtIyebKhl_W5-Kaw` |
| Folder DOKUMEN OTOMATIS HAPPY PUMPKIN (dibuat 12 Sep 2026) | `1kucuLO3P4yZUnRgXO8ISvxXcHa9531tP` |
| Folder LAPORAN BOT HAPPY PUMPKIN (dibuat 12 Sep 2026) | `1BTHfFCgULMJGceqGJ9aPDub-Rf8KgBUI` |

Catatan: ID sheet SINKRON di bagian 2 (`1lL-AXy2Th...`) BUKAN yang dipakai.
Yang benar `1qkd-_wc3...`, dimiliki `finance.dwiputramandiri@gmail.com`.

### Keadaan sheet SINKRON saat diperiksa

17 tab, strukturnya sudah benar tapi isinya tidak jalan: `MASTER_HARGA` kosong,
`SUMBER` hanya membaca 1 baris per tab, `DAFTAR_PO` nol, ada `#REF!`, dan
`TARIK` (IMPORTRANGE) tidak tersambung. Yang sudah berisi dan berguna hanya
`MASTER_CUSTOMER` (14 customer).

**Keputusan: struktur tab Yosua dipertahankan, tidak diganti.** Bot hanya
menambah tab berawalan `BOT_`. Modul `sapu/tulis_sheet.py` menolak menulis ke
tab lain, dan penolakan itu diuji.

### Susunan kolom order sheet berubah sepanjang waktu — temuan penting

Pemindai berbasis huruf kolom hanya jalan untuk sheet terbaru. Ada tiga pola:

| Periode | Kolom ukuran | Kolom nilai bersih |
|---|---|---|
| Januari 2025 | 3 | P `TOTAL VALUE`, Q `CBD + 2%`, R `COD + 1,5%` |
| Feb - Mei 2025 | 6 | W, X, Y |
| Juli - Sep 2025 | 8 | AA, AB, AC — **AB Agustus 2025 berjudul `PPN + 11%`** |
| Okt 2025 - kini | 9 | AC, AD, AE |

Agustus 2025 juga punya **baris judul tambahan**, jadi datanya mulai satu baris
lebih bawah. Jarak baris judul ke baris data sekarang dicari sendiri.

Penyelesaiannya: `tata_letak.py` membaca baris judul dan menentukan letak tiap
kolom dari teksnya. Jangan pernah kembali memakai huruf kolom tetap.

### Satu tab bisa punya dua kolom berjenis sama

Agustus 2026 Baby Wise (Surabaya): kolom AD **dan** AE dua-duanya berjudul COD.
April sampai Juli 2026 juga begitu. Kalau dikunci dengan nama jenis saja, yang
satu menimpa yang lain dan nilai bersihnya salah. Kunci kolom nett sekarang
dibuat unik (`COD@AD`, `COD@AE`).

### Database customer dari 21 order sheet

`python3 jalankan.py telusuri` menghasilkan `DATABASE_CUSTOMER.xlsx`.

| | |
|---|---|
| Order sheet terbaca | 21 dari 22 |
| PO terbaca | 379 |
| Customer setelah digabung | 164 |

Tingkat diskon: 25% (60 customer), 20% (33), 18% (25), 22% (18), 30% (6),
sisanya campuran.
Cara bayar terakhir: TOP 115, CBD 38, COD 10, PPN 1.
Tujuh customer pernah memakai kolom `DISCOUNT PPN + 11%`.

**Order Sheet Juni 2025 (11,4 MB) tidak bisa diekspor Google** — ditolak dengan
"file too large". Satu-satunya berkas yang belum terbaca.

### Nama customer: jangan digabung dengan menebak

Ekspor Excel memotong nama tab di 31 huruf, jadi satu toko muncul sebagai
`Baby Fame (Lam`, `Baby Fame (Lampun`, dan `Baby Fame (Lampung)`.

Tapi menggabungkan berdasarkan awalan saja BERBAHAYA: `Baby Wise` dan
`Baby Wise Surabaya` adalah dua toko berbeda, bukan potongan satu sama lain.

**Aturan yang dipakai:** sebuah nama hanya digabung ke nama yang lebih panjang
kalau nama itu selalu berasal dari tab yang panjangnya 30 huruf atau lebih —
artinya memang terpotong. Nama yang pernah muncul dari tab pendek dianggap utuh.
Sisanya dikumpulkan di lembar `PERIKSA_NAMA` untuk dipastikan Yosua, bukan
ditebak. Ada 18 grup yang perlu diperiksa.

Masalah ini **hilang sendiri** begitu bot berjalan, karena Sheets API memberi
nama tab lengkap tanpa dipotong.

### Dua perusahaan pemroses — jawaban Yosua nomor 2

| Kode | Perusahaan | PPN 11% |
|---|---|---|
| `DPM` | CV. Dwi Putra Mandiri | berlaku |
| `MTN` | CV. Mutiara Timur Nusantara | **tidak** berlaku |

Diatur di `config/perusahaan.yaml`, dipasangkan per customer lewat kolom
`perusahaan_pemroses` di `config/customer.csv`. Kop surat, rekening, dan NPWP
penjual ikut perusahaannya. Kalau kosong, memakai DPM dan program mengingatkan.

Jejaknya ada di order sheet Agustus 2025: kolom AB di sana berjudul
`DISCOUNT PPN + 11%`, dipakai 7 customer. Perlu dipastikan apakah itu memang
penanda perusahaan pemroses.

### Bot penyapu

Berjalan tiap 12 jam lewat cron atau systemd. Memakai akun layanan Google
dengan akses **Viewer** ke folder order sheet — bot tidak akan pernah bisa
mengubah order sheet.

**Bot membaca tab langsung lewat Sheets API, TIDAK mengunduh spreadsheet.**
Arahan Yosua 11 September 2026: akun layanan harus membaca dan mengurai tab
order sheet yang ada, bukan mengunduh berkas tiap hari.

`sapu/lembar_api.py` membungkus hasil Sheets API menjadi objek yang menyediakan
`title`, `max_row`, `max_column`, dan `cell(r,c).value` — empat hal yang
dibutuhkan pemindai. Karena itu tata_letak.py, pemindai.py, dan nilai_bersih.py
dipakai APA ADANYA untuk kedua sumber. Sudah dibuktikan memberi hasil identik
pada ke-16 tab Agustus 2026.

Penghematannya:

| Keadaan | Kalau mengunduh berkas | Cara sekarang |
|---|---|---:|
| Sapuan pertama, 21 order sheet | ~25 MB, 21 berkas | 42 panggilan |
| Tidak ada yang berubah | tetap 21 unduhan | **0 panggilan** |
| 1 order sheet berubah | tetap 21 unduhan | 2 panggilan |

Spreadsheet yang tidak berubah dilewati berdasarkan `modifiedTime` dari Drive,
yang dicatat di `data/kondisi_sapu.json`. Order Sheet Juni 2025 (11,4 MB) yang
dulu ditolak Google saat diekspor kini terbaca, karena tidak pernah diekspor.

Nama tab dari Sheets API LENGKAP — masalah pemotongan 31 huruf hilang.

Yang dianggap GENTING hanya perubahan pada PO yang **ATO-nya sudah terisi**:
qty, susunan qty, jumlah baris, nilai bersih, nilai kotor, cara bayar, dan
perubahan rumus walau angkanya belum berubah.

**Pengaman alarm palsu:** kalau nilai rupiah terbaca nol padahal jumlah baris
dan qty persis sama, itu diperlakukan sebagai gagal baca rumus, bukan angka
yang diubah orang. Diuji pada Agustus 2026: tanpa pengaman muncul 40 alarm,
dengan pengaman tinggal 2 perubahan yang memang disisipkan. Alarm palsu membuat
orang berhenti percaya pada laporannya.

### Keputusan Yosua 11 September 2026

| Hal | Keputusan |
|---|---|
| Akhiran Y pada ukuran | **Tetap dipakai** (2 -> 2Y). Sudah final |
| PPN 11% | Hanya untuk order lewat CV. Dwi Putra Mandiri |
| Nomor dokumen | Formatnya masih akan dikonfirmasi Yosua |
| Termin 30 hari | Tidak berlaku untuk semua customer, diambil dari riwayat |

### Yang masih menggantung setelah perluasan ini

| Hal | Keterangan |
|---|---|
| Akun layanan Google | Harus dibuat Yosua sendiri lewat Google Cloud Console, lihat PANDUAN_BOT.md |
| Alamat & NPWP CV Mutiara Timur Nusantara | Belum ada sama sekali |
| NPWP CV Dwi Putra Mandiri | Belum ada |
| Customer mana pakai perusahaan mana | 14 customer belum ditentukan |
| 18 grup nama di PERIKSA_NAMA | Perlu dipastikan sama atau beda. Sudah ada di Google Sheet "DATABASE CUSTOMER HAPPY PUMPKIN 2025-2026" di My Drive Yosua, lembar PERIKSA_NAMA |
| Order Sheet Juni 2025 | Terlalu besar untuk diekspor, belum terbaca |
| Format nomor dokumen | Menunggu Yosua |


### Berkas ringkasan sistem — 12 September 2026

Yosua bertanya apakah ada berkas spreadsheet yang memuat sistem ini. Jawabannya
saat itu: belum ada. Sheet `OTOMATISASI_HAPPY_PUMPKIN_SINKRON` **belum disentuh
sama sekali** — diperiksa 12 Sep 2026, `modifiedTime` masih 10 Sep 2026 10:52
(suntingan Yosua sendiri) dan tidak ada satu pun tab berawalan `BOT_`. Itu memang
sesuai rancangan: tab `BOT_` baru muncul setelah akun layanan Google dibuat.

Karena itu dibuat berkas ringkasan `SISTEM OTOMATISASI DOKUMEN PENJUALAN HAPPY
PUMPKIN` di My Drive Yosua, berisi tujuh bagian: MULAI DI SINI, ISI SISTEM,
4 ATURAN WAJIB, CARA PAKAI HARIAN, BOT PENYAPU, ANGKA TERVERIFIKASI, dan
YANG DITUNGGU. Pembuatnya `alat/ringkasan_sistem.py`, menghasilkan `.xlsx`
(tujuh tab) dan `.csv` (satu lembar).

Catatan teknis unggahan: konektor Drive menolak `base64Content` yang panjang
(berkas 16 KB gagal). Jalur yang berhasil adalah `textContent` berisi CSV dengan
`contentMimeType: text/csv`, yang dikonversi Google menjadi Spreadsheet. Untuk
unggahan berikutnya, pakai CSV lewat `textContent`, jangan xlsx lewat base64.


## 15. Alur kerja resmi — penjelasan Yosua 12 September 2026

Yosua memperjelas alurnya dengan kalimatnya sendiri:

> "dari spreadsheet (External) Order Sheet terdapat tab PO, lalu dari bagian
> Available to Order buatlah Invoice, Surat Jalan, dan Faktur Pajak sesuai
> dengan karakteristik Invoice, Surat Jalan masing-masing setiap customer dan
> buat sistem itu selalu update setiap ada perubahan pada (External) Order Sheet."

### Yang menjadi PASTI

| Hal | Keputusan |
|---|---|
| Sumber | Bagian **AVAILABLE TO ORDER** pada tab PO. ORIGINAL PO tidak dipakai |
| Dokumen | **Invoice, Surat Jalan, Faktur Pajak** — mengikuti karakteristik tiap customer |
| Kapan final | Saat ATO terisi. **Tapi tidak final selamanya** |
| Kalau direvisi | Dokumen **wajib dibuat ulang** mengikuti data paling terbaru |
| Sifat sistem | Selalu ikut berubah setiap order sheet berubah |

Kutipan Yosua untuk poin revisi: *"itu tidak sepenuhnya final karena jika ada
revisi anda juga harus memperbaikinya lagi dan menyesuaikannya dengan data yang
paling terbaru"*.

### Yang MASIH menunggu konfirmasi Yosua (dinyatakan sendiri olehnya)

| Hal | Sementara program memakai |
|---|---|
| Pengiriman bertahap | 1 PO = 1 Surat Jalan = 1 Invoice |
| Perusahaan pemroses DPM/MTN — per customer atau per pesanan | Per customer, di `config/customer.csv` |
| Urutan penerbitan dokumen | Ketiganya dibuat sekaligus |
| Rumus nomor dokumen | Nomor dikosongkan, diisi manual |

### Packing List tidak disebut Yosua

Yosua menyebut **tiga** dokumen. Packing List tetap dibuat program karena sudah
ada, tapi perlu dipastikan apakah masih dipakai. Jangan dihapus sebelum dijawab.

### Draf otomatis — SELESAI 12 September 2026

Celah "bot hanya mendaftar PO siap, belum membuat dokumennya" sudah ditutup.

| Berkas | Isi |
|---|---|
| `berkas_dokumen.py` | Pembuat berkas yang dipakai BERSAMA oleh perintah manual dan bot. Sengaja satu kode, supaya hasil manual dan hasil bot tidak pernah berbeda |
| `sapu/draf.py` | Memutuskan kapan draf dibuat, kapan dibuat ULANG, dan mengarsipkan draf lama |

Aturannya:

| Keadaan | Tindakan |
|---|---|
| ATO belum terisi | tidak membuat apa-apa |
| ATO terisi, angka cocok | buat draf (Invoice, Surat Jalan, Faktur Pajak, Packing List) |
| ATO terisi, angka TIDAK cocok | **tidak membuat dokumen**, masalahnya dicatat |
| qty / nilai / cara bayar / jumlah baris berubah | **buat ulang**, draf lama pindah ke `_KEDALUWARSA` |
| hanya rumus yang berubah | alarm tetap bunyi, dokumen TIDAK dibuat ulang |

Dua keputusan yang jangan diubah tanpa alasan:

1. **Sidik jari disimpan SETELAH draf dibuat.** Kalau pembuatan draf gagal,
   sidik lama tetap tersimpan, jadi sapuan berikutnya mencoba lagi — bukan
   menganggapnya sudah beres.
2. **Draf lama diarsipkan, tidak ditimpa.** Nama folder arsip diberi angka
   tambahan kalau bentrok di detik yang sama; tanpa itu `shutil.move` menaruh
   folder lama DI DALAM arsip sebelumnya dan draf yang lebih tua tersembunyi.
   Ditemukan saat simulasi, bukan dari teori, dan sudah ada tesnya.

Hasil simulasi lima sapuan pada order sheet Agustus 2026 (16 PO):

| Sapuan | Hasil |
|---|---|
| 1 — pertama kali | 16 draf baru |
| 2 — tanpa revisi | 0 dibuat, 16 dilewati |
| 3 — qty Miniku direvisi | 1 dibuat ulang, draf lama masuk `_KEDALUWARSA` |
| 4 — revisi tetap, hanya rumus berubah | 0 dibuat ulang |
| 5 — tidak ada perubahan | 0 dibuat ulang |

Tes bertambah dari 60 menjadi 76.

### Berkas alur kerja di Drive

`ALUR KERJA SISTEM OTOMATISASI HAPPY PUMPKIN`, tujuh bagian: ALUR UTAMA,
ATURAN SELALU UPDATE, KARAKTERISTIK CUSTOMER, ISI TIAP DOKUMEN, SUMBER ANGKA,
SUDAH PASTI, MENUNGGU KONFIRMASI. Pembuatnya `alat/alur_kerja.py`.

### Dokumen dinaikkan ke Drive — 12 September 2026

Yosua bertanya di mana dokumen hasil otomatisasi disimpan. Jawabannya waktu itu:
hanya di komputer yang menjalankan program. Yang naik ke Drive cuma laporan
sapuan, bukan dokumennya — percuma dibuat otomatis kalau divisi tidak bisa
mengambilnya.

Folder `DOKUMEN OTOMATIS HAPPY PUMPKIN` karena itu dibuatkan di My Drive Yosua
dan ID-nya sudah terisi di `config/bot.yaml` (`folder_dokumen_id`).

| Berkas | Isi |
|---|---|
| `sapu/unggah.py` | `PengunggahDokumen` — membuat folder bertingkat dan menaruh berkas |
| `google.py` | `cari_berkas()` dan `unggah_berkas()` yang MENIMPA berkas bernama sama |

Susunan di Drive memakai nama ASLI order sheet dan tab PO (bukan nama berkas
yang sudah diseragamkan), supaya enak dibaca orang:

    DOKUMEN OTOMATIS HAPPY PUMPKIN/
      Order Sheet Agustus 2026/
        PO 20 Agustus - Miniku/
          INVOICE_... , SURAT_JALAN_... , FAKTUR_PAJAK_... , PACKING_LIST_...

Tiga keputusan yang jangan diubah tanpa alasan:

1. **Berkas bernama sama DITIMPA, bukan ditambah.** Kalau tiap revisi membuat
   berkas baru, folder Drive penuh berisi banyak "Invoice Miniku" dan tidak ada
   yang tahu mana yang berlaku. Versi lama tetap aman di `_KEDALUWARSA` pada
   komputer bot.
2. **Id folder di-cache selama satu sapuan.** Tanpa itu folder bulan yang sama
   ditanyakan ke Google berulang kali untuk tiap PO.
3. **Hak akses bot berbeda per folder:** folder order sheet tetap **Viewer**,
   folder laporan dan folder dokumen **Editor**. Jangan pernah memberi Editor
   pada folder order sheet.

Diuji dengan `SambunganPalsu` (tidak menyentuh Google): susunan folder, cache,
penimpaan berkas, folder gagal dibuat, dan satu berkas gagal sementara sisanya
tetap naik. Tes 76 -> 82.

### Akun layanan bot — 12 September 2026

Yosua sudah membuat akun layanannya:

    penyapu-order-sheet@happy-pumpkin-bot.iam.gserviceaccount.com

Proyek Google Cloud: `happy-pumpkin-bot`. Berkas kuncinya ada di tangan Yosua,
TIDAK pernah dikirim ke sesi ini dan memang tidak perlu.

Izin yang SUDAH diberikan lewat konektor Drive (bertindak sebagai Yosua):

| Tempat | Peran | Keadaan |
|---|---|---|
| Folder DOKUMEN OTOMATIS | Editor | selesai |
| Folder LAPORAN BOT | Editor | selesai |
| Sheet OTOMATISASI (`1qkd-...`) | Editor | selesai |
| Folder Order Sheet 2026 (`1RDH...`) | Viewer | **DITOLAK** — "caller does not have permission" |
| Folder Order Sheet 2025 (`1PiX...`) | Viewer | **DITOLAK** — sama |

Dua folder order sheet dimiliki `happypumpkinkids.id@gmail.com`, dan Yosua tidak
punya hak membagikannya. Harus dikerjakan pemilik akun itu. Jangan dicoba lagi
dari sini — hasilnya akan sama.

`config/bot.yaml` sekarang sudah terisi lengkap: `folder_laporan_id`,
`folder_dokumen_id`, dan `sheet_otomatisasi_id`.

### Belum diputuskan: komputer mana yang menjalankan bot

Sesi Claude Code ini berjalan di wadah sementara yang akan dihapus. Bot tiap 12
jam tidak bisa hidup di sini. Perlu ditentukan Yosua: komputer kantor yang
menyala terus, atau server kecil. Berkas kunci dan `data/kondisi_sapu.json`
harus berada di mesin itu.

### Cacat: requirements.txt tidak memuat komponen Google — SELESAI 12 Sep 2026

Saat Yosua memasang di laptop Windows-nya, `py jalankan.py periksa-bot` berhenti
dengan `ModuleNotFoundError: No module named 'google'`, padahal pemasangan
komponen sudah dijalankan benar.

Sebabnya bukan di komputer Yosua: `requirements.txt` hanya berisi `openpyxl` dan
`PyYAML`. Dua paket yang dipakai `sapu/google.py` tidak pernah dicantumkan:

    google-api-python-client
    google-auth

Tidak ketahuan selama ini karena di wadah pengembangan kedua paket itu
kebetulan sudah terpasang.

Sudah ditambahkan, dan dikunci dua tes: satu memastikan keempat paket ada di
`requirements.txt`, satu lagi menyisir seluruh `src/` untuk memastikan tiap
paket pihak ketiga yang diimpor memang tercantum. Tes 90 -> 92.

### Pemeriksa salah mendiagnosis "API belum dinyalakan" — SELESAI 12 Sep 2026

Saat Yosua menjalankan `periksa-bot` di laptopnya, enam dari tujuh pemeriksaan
lolos. Yang gagal cuma sheet OTOMATISASI, dengan galat Google:

    HttpError 403 ... Google Sheets API has not been used in project
    76910858898 before or it is disabled ... 'reason': 'SERVICE_DISABLED'

Sebabnya: pada Langkah 2, hanya **Google Drive API** yang dinyalakan; **Google
Sheets API** belum. Terbukti dari gejalanya — pembacaan folder Drive (5 dari 5)
berhasil, hanya pembacaan tab spreadsheet yang ditolak.

Tapi `pemeriksa.py` menyarankan *"Share sheet OTOMATISASI sebagai Editor"*,
padahal izin sheet itu memang sudah benar sejak awal (diberikan lewat konektor
Drive). Saran yang salah ini berbahaya: orang akan men-Share ulang berkas yang
sudah benar, masalahnya tidak selesai, dan kepercayaan pada pemeriksa hilang.

Sekarang pemeriksa membedakan dua sebab itu. Kalau galatnya mengandung
`SERVICE_DISABLED`, `has not been used in project`, `it is disabled`, atau
`accessNotConfigured`, sarannya berubah jadi menyalakan API di Cloud Console,
menyebut nama API-nya, dan **menegaskan bahwa ini bukan masalah izin sehingga
jangan men-Share ulang apa pun**.

Berlaku untuk ketiga pemeriksaan (folder order sheet, folder tujuan, sheet
OTOMATISASI). Dikunci dua tes: galat API-mati tidak boleh menyuruh Share, dan
galat izin biasa harus tetap menyuruh Share. Tes 92 -> 94.

**Pelajaran yang berlaku umum:** galat 403 dari Google TIDAK selalu berarti
masalah izin. Periksa dulu apakah API-nya menyala.

### Sapuan pertama berhasil, tapi unggahan ke Drive gagal — 12 Sep 2026

Bot berhasil jalan di laptop Yosua. Order sheet 2025 dan 2026 terbaca, draf
dibuat (4 berkas per PO). Tapi tiap PO melaporkan `0 berkas naik ke Drive`.

Sebabnya belum diketahui saat catatan ini ditulis, KARENA `unggah_berkas()`
menelan `HttpError` dan mengembalikan `None`, lalu `unggah()` hanya mencatat
"gagal diunggah" tanpa sebab. Laporannya jadi tidak bisa ditindaklanjuti.

Sudah diperbaiki:

| Berkas | Perubahan |
|---|---|
| `google.py` | `unggah_berkas()` tidak lagi menelan galat — dibiarkan naik ke pemanggil |
| `sapu/unggah.py` | Sebab asli ikut dicatat: `f"{nama}: {e}"`, termasuk kegagalan membuat folder |
| `sapu/bot.py` | Sebab kegagalan pertama LANGSUNG ditampilkan di layar, tidak hanya masuk laporan |

Dikunci dua tes. Tes 94 -> 96.

**SEBABNYA SUDAH PASTI, 12 Sep 2026.** Diuji langsung di laptop Yosua:

| Uji | Hasil |
|---|---|
| Bot membuat FOLDER di DOKUMEN OTOMATIS | berhasil |
| Bot mengunggah BERKAS ke folder yang sama | ditolak |

Pesan resmi Google:

    HttpError 403 ... Service Accounts do not have storage quota.
    Leverage shared drives ... or use OAuth delegation instead.
    'reason': 'storageQuotaExceeded'

Akun layanan **tidak punya jatah penyimpanan Drive**, jadi tidak bisa membuat
berkas baru di My Drive siapa pun. Folder bisa karena tidak memakan ruang.
**Menambah izin TIDAK akan menolong** — jangan pernah coba menyelesaikannya
dengan Share ulang.

Dua jalan keluar resmi Google (Shared Drive, OAuth delegation) sama-sama butuh
**Google Workspace**, sedangkan akun Happy Pumpkin memakai `@gmail.com`.

**Jalan keluar yang dipilih: Google Drive for Desktop.** Bot menulis ke folder
lokal yang disinkronkan, lalu Drive for Desktop yang menyalinkannya. Berkas
dimiliki Yosua, bukan akun layanan, jadi lepas dari batasan kuota. Tidak perlu
perubahan kode — cukup `folder_draf` diarahkan ke folder sinkron dan
`folder_dokumen_id` dikosongkan. Langkahnya ada di PANDUAN_BOT.md.

Program sekarang **berhenti mencoba begitu ditolak karena kuota** (penolakan itu
pasti berlaku untuk semua berkas), dan menampilkan satu pesan yang menjelaskan
batasannya serta jalan keluarnya. Dikunci dua tes. Tes 96 -> 98.

**Catatan yang belum diuji:** laporan sapuan juga berkas baru, jadi
kemungkinan besar ikut tertolak. Kalau terbukti begitu, `folder_laporan_id`
dikosongkan juga.

## 16. Format Invoice & Surat Jalan diperbaiki dari berkas asli — 13 Sep 2026

Yosua melaporkan format invoice dan surat jalan **salah dan berbeda** dari
format CV Dwi Putra Mandiri, lalu memberi folder berisi faktur asli:
`1KqROb51kVZx6_kc7fxC4GXOlCb36Pck1` (± 50 berkas, Juli-Agustus 2026).

Berkas acuan yang dibongkar sel per sel:

| Berkas | Kegunaan |
|---|---|
| `0250726 KATAMAMA TAPOS.xlsx` | customer per ukuran, Surat Jalan satu tabel |
| `0310726 MAE BEBE JONNI SETIADI.xlsx` | Surat Jalan BERTUMPUK dua tabel |
| `0010726 BABY WISE.xlsx` | customer per artikel, faktur berhalaman |

**Tiap berkas punya tab bernama `FORMAT INVOICE` dan `FORMAT SURAT JALAN`.**
Di situlah tata letak resminya. Kalau suatu saat format berubah lagi, bongkar
tab itu, jangan mengarang.

### Yang ternyata salah pada versi lama

| Bagian | Versi lama (salah) | Faktur asli |
|---|---|---|
| Kop | teks mulai kolom A | ruang logo digabung A2:B6, teks di kolom C |
| Judul dokumen | `INVOICE` | `FAKTUR No. <nomor>` |
| Baris BRAND | tidak ada | `BRAND :  HAPPY PUMPKIN` — selalu ada |
| Baris info PO/termin | ada | tidak ada di faktur asli |
| Judul tabel invoice | satu baris | **tiga baris bertingkat** (12-14), data mulai baris 15 |
| Kolom diskon | angka desimal mentah `0.2317...` | `25%` atau `22% + 1,5%` |
| Kolom H | nilai bersih | **Jumlah KOTOR**; nett = Jumlah - Nilai Diskon |
| Pemisah ukuran | `... - 3-6M` | `... Uk. 3-6M` |
| Judul kolom Surat Jalan | PRODUCT NAME / COLOUR / TOTAL | **DESKRIPSI BARANG / WARNA / Qty-PCS** |
| Deskripsi Surat Jalan | satu kolom | tiga kolom digabung (C:E) |
| Kalimat pembuka SJ | tidak ada | `Diterima dengan baik barang-barang tersebut dibawah ini :` |
| Baris TOTAL per tabel SJ | ada | **tidak ada**; jumlah qty ditaruh di kanan baris 9 |
| Penanda blok | `Kategori 1 dari 2` | tidak ada |
| Kolom ukuran | semua kolom blok | **hanya yang benar-benar terisi** |

### Yang TERBUKTI benar dan dipertahankan

- **Surat Jalan memang bisa bertumpuk.** Mae Bebe punya dua tabel (sistem
  ukuran berbeda), Katamama hanya satu. Jadi aturan "satu tabel per blok"
  benar — bukan selalu bertumpuk, bukan selalu tunggal.
- Penutup invoice: Subtotal, Diskon, Total, Uang Muka, DPP, PPN 11%, Total.
- DPP dihitung mundur `Total x 100/111`.
- Blok rekening di kolom B, sejajar penutup.

### Catatan teknis

- `config/perusahaan.yaml` sudah memuat kalimat "PEMBAYARAN DITRANSFER KE
  REKENING :" di daftar rekening, jadi `baris_rekening()` tidak boleh
  menambahkannya lagi — pernah kembar.
- Kolom ukuran ke-9 berjudul angka `9` dan tidak pernah terisi. Surat Jalan
  sekarang hanya mencetak kolom sampai ukuran terakhir yang ada isinya.
- `buat_invoice` tetap mengembalikan dict yang sama seperti sebelumnya supaya
  laporan dan tes tidak rusak, walaupun tata letaknya berubah total.

Empat tes baru mengunci bentuknya (kop, judul tiga tingkat, blok rekening tidak
kembar, kolom ukuran kosong tidak dicetak). Tes 98 -> 102.

## 17. Faktur Pajak format Coretax — 13 September 2026

Permintaan Yosua: faktur pajak dalam bentuk Excel yang bisa langsung dimasukkan
ke **Converter Excel->XML milik DJP**, lalu XML-nya diunggah ke Coretax untuk
membuat faktur **secara borongan**.

`www.pajak.go.id` DIBLOKIR dari sesi ini, jadi templatenya tidak bisa diunduh
langsung. Template resminya didapat dari repo publik
`ACC-TAX-REIGHTEEN/Auto-Input-XML-Pajak-Coretax`, berkas
`Dapur/Template_v.1.6.1.xlsx`. **Struktur di bawah ini dibaca dari berkas itu,
bukan ditebak.**

### Susunan template resmi v1.6.1

| Lembar | Isi |
|---|---|
| `Faktur` | B1 = NPWP Penjual; judul di baris 3; data mulai baris 4; ditutup `END` |
| `DetailFaktur` | judul di baris 1; data mulai baris 2; ditutup `END` |

Kolom `Faktur` (18): Baris, Tanggal Faktur, Jenis Faktur, Kode Transaksi,
Keterangan Tambahan, Dokumen Pendukung, Period Dok Pendukung, Referensi,
Cap Fasilitas, ID TKU Penjual, NPWP/NIK Pembeli, Jenis ID Pembeli,
Negara Pembeli, Nomor Dokumen Pembeli, Nama Pembeli, Alamat Pembeli,
Email Pembeli, ID TKU Pembeli.

Kolom `DetailFaktur` (14): Baris, Barang/Jasa, Kode Barang Jasa,
Nama Barang/Jasa, Nama Satuan Ukur, Harga Satuan, Jumlah Barang Jasa,
Total Diskon, DPP, DPP Nilai Lain, Tarif PPN, PPN, Tarif PPnBM, PPnBM.

### Aturan yang paling mudah salah (dari lembar `Keterangan`)

| Aturan | Nilai |
|---|---|
| Tanggal Faktur | `DD/MM/YYYY` |
| Jenis Faktur | selalu `Normal` |
| Kode Transaksi | `01` = kepada selain Pemungut PPN |
| Satuan ukur | `UM.0021` = Piece |
| Barang/Jasa | `A` = Barang |
| NPWP pembeli tidak diketahui | isi `0000000000000000`, Jenis ID bukan TIN |
| ID TKU Pembeli bukan TIN | isi `000000` |
| DPP Nilai Lain | **sama dengan DPP** kalau tidak memakai nilai lain |
| DPP | harus `Harga Satuan x Jumlah - Total Diskon` |
| PPN | `Tarif PPN x DPP Nilai Lain` |
| Angka | maksimal 2 angka di belakang koma |

### Hal paling menentukan: harga di order sheet SUDAH termasuk PPN

Coretax meminta Harga Satuan dan DPP **tanpa PPN**. Jadi tiap nilai dibagi
`(1 + tarif)` lebih dulu. Kalau ini terlewat, DPP jadi 11% terlalu besar dan
pajak yang dilaporkan salah.

Diuji ulang: `DPP + PPN` kembali ke nilai bersih invoice. Pada order sheet
Agustus 2026 selisihnya **Rp0,01** dari 571 baris — murni pembulatan 2 desimal
yang memang diwajibkan DJP. Program mengawasi selisih ini sendiri dan
memperingatkan kalau ada faktur yang meleset lebih dari Rp1.

### Perintah baru

    python3 jalankan.py faktur-pajak

Menghasilkan SATU berkas `keluaran/FAKTUR_PAJAK_CORETAX.xlsx` berisi SEMUA PO
sekaligus — itulah gunanya untuk unggah borongan. Program menolak membuatnya
kalau angka belum cocok dengan order sheet, dan menyebutkan apa yang masih
kurang sebelum berkasnya layak diunggah.

### Yang masih harus diisi Yosua sebelum bisa diunggah

| Hal | Tempat |
|---|---|
| NPWP CV Dwi Putra Mandiri & CV Mutiara Timur Nusantara | `config/perusahaan.yaml` |
| **ID TKU Penjual (NITKU 22 digit)** | `config/perusahaan.yaml` -> `id_tku` |
| NPWP & NITKU tiap customer | `config/customer.csv` -> `npwp`, `id_tku` |
| Alamat 8 customer | `config/customer.csv` |

NITKU dilihat di Coretax: Profil Wajib Pajak -> Tempat Kegiatan Usaha.

Delapan tes mengunci formatnya. Tes 102 -> 110.

## 18. Uji silang dengan faktur asli Juli 2026 — 13 September 2026

Yosua minta contoh dokumen dari bulan lain. Dipilih **Juli 2026** dengan
sengaja, karena folder faktur asli `1KqROb51...` juga berisi Juli 2026 —
jadi hasil program bisa diadu langsung dengan berkas yang benar-benar
dikirim ke customer.

Dibandingkan baris per baris: `0310726 MAE BEBE JONNI SETIADI` dan
`0010726 BABY WISE` melawan keluaran program untuk `PO 17 Juli - Mae Bebe`
dan `PO 07 Juli - Baby Wise`.

### Dua cacat format yang baru ketahuan

**1. Kolom H (Jumlah) berisi nilai SETELAH diskon, bukan nilai kotor.**

Bagian 16 mencatat sebaliknya, dan itu SALAH. Buktinya aritmetika faktur
asli sendiri, pada dua berkas berbeda:

| Berkas | Baris | Qty x Harga | Nilai Diskon (G) | Jumlah (H) |
|---|---|---:|---:|---:|
| 0310726 MAE BEBE | 1 | 18 x 62.900 = 1.132.200 | 283.050 | **849.150** |
| 0010726 BABY WISE | 1 | 2 x 53.900 = 107.800 | 26.950 | **80.850** |

Jumlah seluruh kolom H sama dengan baris **Total**, bukan **Subtotal**.
Pada Mae Bebe: jumlah H = 11.932.650 = Total. Subtotal 15.910.200 adalah
jumlah kotor yang tidak pernah muncul di kolom mana pun.

Sudah diperbaiki. Tesnya kini memeriksa `H + G = Qty x Harga` di **setiap**
baris, bukan hanya totalnya — supaya cacat semacam ini tidak bisa lolos
lagi hanya karena totalnya kebetulan cocok.

**2. Persen diskon ada di F13, bukan F14.**

Faktur asli: `F12` berisi label `Diskon ` sendirian, `F13:F14` digabung
berisi persennya. Versi lama terbalik — `F12:F13` digabung untuk label dan
persennya jatuh ke `F14`.

### Hasil setelah perbaikan

Invoice Mae Bebe keluaran program sekarang **sama persis** dengan faktur
asli, sel demi sel, kecuali harga 2 artikel (lihat di bawah). Surat Jalan
cocok **seluruhnya**: kedua tabel bertumpuk, 24 baris, kode artikel, warna,
letak kolom ukuran, qty per ukuran, sampai total 288 pcs.

### Harga Milo Set berbeda — order sheet Juli tertinggal

Satu-satunya selisih angka:

| Artikel | Faktur asli 0310726 | Order Sheet Juli 2026 |
|---|---:|---:|
| `42022.A` Milo Set (Small Size) | 61.000 | 49.400 |
| `4202200.A` Milo Set (Big Size) | 69.500 | 55.400 |

Ditelusuri ke seluruh arsip: harga 61.000 / 69.500 **hanya ada di**
`Order Sheet Agustus 2026 Harga Baru`. Juni 2026, Juli 2026, dan
Agustus 2026 Harga Lama semuanya masih 49.400 / 55.400.

Artinya faktur yang diterbitkan 28 Juli 2026 **sudah memakai harga baru**,
padahal order sheet Juli tidak pernah ikut diperbarui. Dampaknya pada satu
PO ini saja:

| | Faktur asli | Dari order sheet Juli |
|---|---:|---:|
| Subtotal | 15.910.200 | 14.985.000 |
| Total (nett) | 11.932.650 | 11.238.750 |
| **Selisih** | | **693.900** |

**Jangan ditambal program.** Program benar membaca order sheetnya; yang
perlu dipastikan Yosua adalah mana yang berlaku untuk Juli — harga lama
atau harga baru — lalu order sheetnya yang dirapikan.

### Tanggal dokumen bukan tanggal PO

Faktur asli 0310726 bertanggal **28 Juli 2026**, sedangkan tabnya
`PO 17 Juli`. Program memakai tanggal PO. Perlu dipastikan Yosua apakah
tanggal dokumen harus tanggal terbit (hari dicetak) atau tanggal PO.

### Cacat `--berkas` ditelan sub-perintah faktur-pajak

    python3 jalankan.py --berkas "order sheet Juli.xlsx" faktur-pajak

diam-diam membaca `data/order_sheet.xlsx` (bulan lain) dan tetap melapor
"berhasil". Sebabnya sub-perintah `faktur-pajak` mendeklarasikan `--berkas`
sendiri; argparse memakai satu namespace, jadi yang belakangan menimpa yang
depan dengan `None`.

Faktur pajak bulan yang salah adalah kesalahan yang mahal. Sudah dihapus,
dan dikunci `tests/test_cli_argumen.py` yang menyisir SEMUA sub-perintah,
bukan hanya yang ini.

### Order sheet Juli 2026 jauh lebih besar dari Agustus

| | Juli 2026 | Agustus 2026 |
|---|---:|---:|
| PO berisi data | **30** | 16 |
| Baris | 1.334 | 1.194 |
| Qty | 10.689 pcs | 8.600 pcs |
| Sebelum diskon | Rp771.475.700 | Rp561.768.900 |
| Nilai bersih | Rp582.599.096 | Rp424.156.009 |

Ke-30 PO **COCOK** dengan baris TOTAL masing-masing tab.

Dua hal yang perlu Yosua rapikan di order sheet Juli:

1. **6 tab bernama `Sheet4` sampai `Sheet9`** berisi data PO sungguhan
   (masing-masing 5-56 baris, sampai 621 pcs) tapi tidak punya nama
   customer. Program tidak bisa menebak ini milik siapa.
2. **22 dari 30 PO customernya belum terdaftar** di `config/customer.csv`,
   antara lain Liz & Co (Surabaya/Bali), Babyland, Piikmii, Halo Baby,
   Mulia Makmur, Millenium, Erka Kids, Joy Baby, HUMAIRAA, Ayleen,
   Katamama Cikaret.

Untuk faktur pajak ini fatal: Coretax menolak faktur tanpa nama pembeli.
Peringatannya sekarang menyebut nama tabnya satu per satu, bukan tanda
petik kosong.

Tes 110 -> 113.

## 19. Siap cetak A4 — 13 September 2026

Yosua melaporkan tiga hal dari contoh Juli: blok "PEMBAYARAN DITRANSFER KE
REKENING" dan blok penutup Subtotal tidak berkotak, dan lebar kolom belum
pas untuk kertas A4. Untuk Surat Jalan ia memberi berkas acuan baru:
`FA 030426 TOKO BABY FAME (MTN)` — `1bIKVDfPgetI5Lnr_I-S9PloiU2VlgSPA`.

### Surat Jalan ternyata dicetak TEGAK, bukan mendatar

Cacat paling menentukan. Program memakai `landscape=True`, padahal **semua**
Surat Jalan asli portrait — baik yang DPM maupun yang MTN:

| Berkas | Kertas | Arah | fitToPage | Skala |
|---|---|---|---|---|
| FA 030426 BABY FAME (MTN) | A4 (paperSize 9) | portrait | ya | 93 |
| 0010726 BABY WISE (DPM) | — | portrait | ya | — |
| 0310726 MAE BEBE (DPM) | — | portrait | ya | 93 |

Karena itu dokumen tidak pernah pas di A4 yang dipakai divisi.

### Lebar kolom diambil dari berkas asli, bukan dikira-kira

Faktur asli (jumlah A..H):

| Berkas | A | B | C | D | E | F | G | H | Jumlah |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0010726 BABY WISE | 4,00 | 15,57 | 29,86 | 4,29 | 12,14 | 12,71 | 13,57 | 15,57 | **107,7** |
| 0310726 MAE BEBE | 4,14 | 10,86 | 33,29 | 4,86 | 14,29 | 14,00 | 15,00 | 16,57 | 113,0 |
| versi lama program | 4,30 | 12,60 | **39,40** | 5,00 | 12,10 | 12,60 | 12,60 | 15,60 | 114,2 |

Margin faktur asli juga jauh lebih sempit dari bawaan Excel:
0,13-0,15 kiri/kanan, bukan 0,7. Margin bawaan itu sendiri sudah cukup
untuk mendorong tabel ke halaman kedua.

Surat Jalan asli: deskripsi barang +-29 satuan (C+D+E digabung di DPM,
kolom C tunggal di MTN — dua-duanya berujung di angka yang sama), WARNA
+-10,3, kolom ukuran sempit, Qty +-7.

### Lebar kolom invoice sekarang menyesuaikan isi

Lebar tetap memotong kode artikel panjang. Pada contoh Mei 2026,
`71092.S (Bottom/Celana)` tercetak jadi `71092.S (Bottom/Celan` — di invoice
itu fatal, customer tidak bisa tahu barang mana yang ditagih.

Aturannya: kolom B dan C berbagi satu **jatah tetap** (`JATAH_A4`, jumlah
lebar A..H dari faktur asli). B melebar mengikuti kode terpanjang, dibatasi
11-23 satuan; sisanya untuk C, minimal 22. Karena jatahnya tetap, jumlah
A..H tidak pernah bertambah dan dokumennya tetap muat A4 tegak.

### Yang dikunci tes

`tests/test_cetak_a4.py`:

1. Blok penutup dan blok rekening invoice punya garis kotak mengelilinginya.
2. Invoice, Surat Jalan, dan Packing List semuanya A4 **tegak** dengan
   `fitToWidth=1` dan `fitToPage=True`.
3. Jumlah lebar kolom sampai kolom cetak terakhir tidak lebih dari 115
   satuan — cukup longgar untuk Surat Jalan sembilan ukuran, tapi tetap
   menangkap kolom kebablasan seperti C selebar 39,4.
4. Lebar yang menyesuaikan isi tidak pernah melebihi jatah A4.

`gaya.kotak()` sengaja hanya menggambar garis di **tepi** blok dan
mempertahankan garis sel yang sudah ada, supaya tidak berubah jadi kisi-kisi.

### Dibuktikan pada PDF sungguhan, bukan pada pengaturan saja

Kedelapan contoh 2026 diubah ke PDF lewat LibreOffice lalu diperiksa:
ke-16 berkas ber-MediaBox 595 x 842 pt — **A4 tegak persis**. Diperiksa juga
isi halaman pertama Surat Jalan Miniku (288 baris, 5 halaman): kolom paling
kanan (Qty) ikut tercetak di halaman yang sama, jadi halaman banyak itu
memanjang ke bawah, bukan terpotong ke samping.

### Yang BELUM diubah dan perlu dipastikan Yosua

Berkas acuan yang diberikan kali ini milik **CV. Mutiara Timur Nusantara**,
dan tata letaknya berbeda dari Surat Jalan DPM:

| | Surat Jalan DPM | Surat Jalan MTN |
|---|---|---|
| Kolom terpakai | A..M | A..K |
| Deskripsi barang | C:E digabung | C tunggal |
| Kolom WARNA | F | D |
| Kolom ukuran | G.. | E..J |
| Kepala dokumen | kop + Kepada Yth. | label CUSTOMER / SURAT JALAN / TANGGAL |
| Baris BRAND | ada | tidak ada |

**Hanya lebar kolom dan pengaturan cetaknya yang diambil.** Tata letak DPM
dipertahankan, sebab bagian 18 baru saja membuktikan Surat Jalan program
cocok seluruhnya dengan Surat Jalan DPM asli. Kalau tata letak MTN yang
dipakai untuk semua, kecocokan itu hilang.

Perlu dijawab Yosua: apakah dokumen MTN memang memakai tata letak sendiri
(kalau ya, program perlu dua tata letak, dipilih dari kolom
`perusahaan_pemroses`), atau MTN yang menyusul mengikuti DPM.

### Nomor dokumen pada contoh 8 bulan

Contoh Januari-Agustus 2026 memakai nomor urut `001` tiap bulan
(`0010126` sampai `0010826`). Itu **nomor contoh**, bukan nomor terbit.
Nomor urut yang sebenarnya tetap tidak ditebak program.

Tes 113 -> 118.
