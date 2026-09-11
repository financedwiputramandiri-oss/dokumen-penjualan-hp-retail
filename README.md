# Dokumen Penjualan Happy Pumpkin

Membuat **Surat Jalan, Invoice, Packing List, dan Faktur Pajak** secara
otomatis dari order sheet Google Spreadsheet milik CV Dwi Putra Mandiri
(brand Happy Pumpkin).

> **Baru pertama memakai? Buka [PANDUAN.md](PANDUAN.md).**
> Panduan itu ditulis untuk yang tidak perlu paham program.

---

## Cara cepat

```bash
pip3 install -r requirements.txt

# 1. Unduh order sheet dari Google Spreadsheet
#    (File > Download > Microsoft Excel) simpan ke data/order_sheet.xlsx

python3 jalankan.py daftar        # lihat semua PO
python3 jalankan.py periksa       # cocokkan angka dengan order sheet
python3 jalankan.py buat "Panda"  # buat 4 dokumen untuk satu PO
python3 jalankan.py buat-semua    # buat untuk semua PO
python3 jalankan.py rekap         # rekap sebulan untuk laporan & pajak
python3 jalankan.py telusuri      # database customer dari SEMUA order sheet lama
python3 jalankan.py sapu          # tarik dari Google Drive + pantau perubahan
```

Tambahkan `--pdf` untuk sekalian membuat PDF.

---

## Empat aturan yang dipegang program ini

Aturan ini berasal dari kesalahan nyata yang pernah terjadi. Jangan diubah
tanpa membaca `CLAUDE.md` lebih dulu.

### 1. Seluruh isi tab ditangkap, tanpa kecuali

Satu tab PO bisa berisi **beberapa tabel bertumpuk**, masing-masing dengan
baris judul `ARTICLE CODE` sendiri. Versi lama hanya menangkap tabel pertama
dan kehilangan Rp147.829.100.

Program memindai sampai baris terakhir, lalu **wajib mencocokkan** hasilnya
dengan baris TOTAL milik order sheet sendiri. Kalau tidak cocok, program
**berhenti** dan tidak membuat dokumen.

### 2. Nilai bersih diambil dari kolomnya, tidak pernah dihitung

| Cara bayar | Kolom sumber |
|---|---|
| TOP / Tempo | `TOTAL VALUE` (AC) |
| CBD | `DISCOUNT CBD` (AD) |
| COD | `DISCOUNT COD` (AE) |

Penentuannya di tingkat order, dari kelengkapan kolom:

```
kolom CBD/COD terisi PENUH semua baris  ->  CBD/COD  ->  pakai kolom itu
kolom CBD/COD terisi sebagian           ->  TOP      ->  pakai TOTAL VALUE
kolom CBD/COD kosong sama sekali        ->  TOP      ->  pakai TOTAL VALUE
```

Kolom yang terisi sebagian **diabaikan seluruhnya**, tidak ditambal.
Persentase diskon tidak pernah dipakai untuk menghitung apa pun — kalau ada
persen yang muncul di invoice, itu dihitung **mundur** dari nilai bersih.

### 3. Label ukuran ikut tabelnya masing-masing

Tiap tabel mewakili kategori produk dengan sistem ukuran berbeda.
Surat Jalan dan Packing List membuat tabel terpisah per kategori, lengkap
dengan baris judul ukuran sendiri dan TOTAL per tabel.

### 4. Bentuk deskripsi invoice

Bawaan satu baris per artikel. **Haritsa dan Katamama** dipecah per ukuran,
ditulis `<nama barang> - <ukuran>`, contoh
`Alice Ruffle Sleeveless Top Small Size - 2Y`.

---

## Membaca order sheet tahun berapa pun

Susunan kolom order sheet **berubah sepanjang waktu**. Karena itu kolom tidak
dipatok pada huruf tertentu — program membaca baris judul lalu menentukan
sendiri letak tiap kolom (`tata_letak.py`).

| Periode | Kolom ukuran | Kolom nilai bersih |
|---|---|---|
| Januari 2025 | 3 | P `TOTAL VALUE`, Q `CBD + 2%`, R `COD + 1,5%` |
| Agustus 2025 | 7 | AA `TOTAL VALUE`, AB `PPN + 11%`, AC `COD + 1,5%` |
| Okt 2025 - kini | 9 | AC `TOTAL VALUE`, AD, AE |

Nama tab juga bermacam-macam (`PO 22 Jan ...`, `PO 30 - ...`, `(Delivery 1) ...`)
dan semuanya terbaca.

## Database customer

```bash
python3 jalankan.py telusuri
```

Menelusuri semua order sheet di `data/arsip/`, menghasilkan
`keluaran/DATABASE_CUSTOMER.xlsx` berisi tingkat diskon, kondisi pembayaran
(TOP/COD/CBD), periode aktif, dan nilai belanja tiap customer.

Nama customer di order sheet berantakan. Penggabungan nama hanya dilakukan
kalau nama tab memang terpotong 31 huruf oleh ekspor Excel. Nama mirip yang
sama-sama utuh **tidak** digabung sendiri — dikumpulkan di lembar
`PERIKSA_NAMA` untuk dipastikan manusia, karena `Baby Wise` dan
`Baby Wise Surabaya` itu dua toko berbeda.

## Dua perusahaan pemroses

Order bisa diproses lewat dua perusahaan, dan itu menentukan apakah PPN
dikenakan:

| Kode | Perusahaan | PPN 11% |
|---|---|---|
| `DPM` | CV. Dwi Putra Mandiri | berlaku |
| `MTN` | CV. Mutiara Timur Nusantara | tidak berlaku |

Diatur di `config/perusahaan.yaml`, dipasangkan ke customer lewat kolom
`perusahaan_pemroses` di `config/customer.csv`.

## Bot penyapu

Menarik order sheet dari Google Drive tiap 12 jam, membuat draf dokumen, dan
memberi tahu kalau ada PO lama yang qty atau rumusnya berubah.
Cara memasangnya ada di **[PANDUAN_BOT.md](PANDUAN_BOT.md)**.

## Isi folder

```
config/          diisi manusia: customer, kop surat, tarif PPN
data/            order sheet yang diunduh (tidak masuk git)
keluaran/        hasil dokumen (tidak masuk git)
src/hp_dokumen/  program
  pemindai.py      Aturan 1 — pindai semua blok
  nilai_bersih.py  Aturan 2 — tentukan nett
  ukuran.py        Aturan 3 & 4 — label ukuran
  rekonsiliasi.py  pencocokan wajib
  dokumen/         pembuat keempat dokumen
  tata_letak.py    mengenali susunan kolom order sheet apa pun
  riwayat.py       menelusuri order sheet lama
  db_customer.py   menyusun database customer
  sapu/            bot penyapu: Drive, pemantauan, laporan
  laporan.py       laporan pencocokan & rekap
tests/           tes otomatis, memakai data contoh (bukan data asli)
CLAUDE.md        ingatan proyek: konteks, temuan, keputusan
PANDUAN.md       panduan untuk rekan kerja
```

## Menjalankan tes

```bash
python3 -m pytest
```

## Catatan data

Order sheet asli **tidak disimpan di git** (lihat `.gitignore`). Tes memakai
berkas contoh berisi data karangan yang dibuat oleh `tests/buat_contoh.py`.
