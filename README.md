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
