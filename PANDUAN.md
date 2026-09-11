# Panduan Pemakaian — untuk semua rekan kerja

Panduan ini untuk yang **tidak perlu paham program**. Ikuti saja urutannya.

---

## Sekali saja di awal (pemasangan)

1. Pastikan **Python** sudah terpasang di komputer.
   Cek dengan membuka Terminal / Command Prompt lalu ketik:

   ```
   python3 --version
   ```

   Kalau muncul angka versi, berarti sudah ada.

2. Pasang bahan yang dibutuhkan. Ketik sekali saja:

   ```
   pip3 install -r requirements.txt
   ```

3. (Pilihan) Kalau mau hasilnya sekalian jadi PDF, pasang LibreOffice:

   ```
   sudo apt install libreoffice-calc      # Linux
   ```

   Di Windows/Mac, cukup pasang LibreOffice dari situs resminya.
   Kalau tidak dipasang, berkas Excel tetap dibuat — hanya PDF-nya dilewati.

---

## Setiap kali mau membuat dokumen

### Langkah 1 — Ambil order sheet terbaru

1. Buka order sheet di Google Spreadsheet.
2. Menu **File → Download → Microsoft Excel (.xlsx)**.
3. Simpan berkasnya ke folder `data/` dengan nama **`order_sheet.xlsx`**
   (timpa yang lama).

> Tidak perlu kunci API, tidak perlu izin khusus. Cukup unduh biasa.

### Langkah 2 — Lihat daftar PO

```
python3 jalankan.py daftar
```

Muncul daftar semua PO beserta jumlah baris dan jumlah barangnya.

### Langkah 3 — Cocokkan angkanya dulu

```
python3 jalankan.py periksa
```

Program membandingkan hasil hitungannya dengan **baris TOTAL milik order sheet
sendiri**. Kalau tertulis **COCOK** semua, aman dilanjut.
Kalau ada yang **GAGAL**, jangan dilanjut — laporkan ke Yosua dulu.

Hasil lengkapnya tersimpan di `keluaran/LAPORAN_PENCOCOKAN.xlsx`.

### Langkah 4 — Buat dokumennya

Untuk satu customer (cukup sebagian namanya):

```
python3 jalankan.py buat "Panda"
```

Untuk semua PO sekaligus:

```
python3 jalankan.py buat-semua
```

Kalau mau sekalian PDF, tambahkan `--pdf` di belakang:

```
python3 jalankan.py buat "Panda" --pdf
```

Hasilnya ada di folder `keluaran/`, satu map per PO, berisi 4 berkas:
Surat Jalan, Packing List, Invoice, dan Faktur Pajak.

### Langkah 5 — Rekap sebulan (untuk laporan keuangan & pajak)

```
python3 jalankan.py rekap
```

Menghasilkan `keluaran/REKAP_PENJUALAN.xlsx` berisi nilai per PO
lengkap dengan DPP dan PPN-nya.

---

## Kalau ada data yang perlu diisi

Semua yang perlu diisi manusia ada di folder `config/`. Bisa dibuka pakai
Excel atau Notepad.

| Berkas | Isinya |
|---|---|
| `config/customer.csv` | Nama customer di dokumen, alamat, **NPWP**, format invoice, termin |
| `config/perusahaan.yaml` | Kop surat CV Dwi Putra Mandiri, nomor rekening, nama berkas logo |
| `config/pengaturan.yaml` | Tarif PPN, penulisan label ukuran, nomor dokumen |

Program akan **mengingatkan sendiri** kalau ada yang masih kosong —
dokumen tetap dibuat, bagian yang kosong ditandai `(belum diisi)`.

---

## Arti pesan yang sering muncul

| Pesan | Artinya | Yang perlu dilakukan |
|---|---|---|
| `COCOK` | Angka hasil olahan sama dengan order sheet | Lanjut |
| `GAGAL` | Ada selisih dengan order sheet | Jangan dipakai, lapor ke Yosua |
| `Kolom DISCOUNT CBD baru terisi 44 dari 288 baris` | Sales belum menarik rumus sampai bawah | Minta Sales melengkapi. Sementara order dihitung sebagai TOP |
| `Data customer ... belum lengkap: NPWP` | NPWP belum diisi | Isi di `config/customer.csv` |
| `Tarif PPN masih ... BELUM dikonfirmasi` | Tarif pajak belum dipastikan | Tanya konsultan pajak sebelum lapor |
| `Berkas logo belum ada` | Logo belum ditaruh | Taruh di `config/`, tulis namanya di `perusahaan.yaml` |

---

## Kalau ada masalah

| Masalah | Sebabnya | Cara mengatasi |
|---|---|---|
| `Order sheet belum ada` | Berkas belum diunduh | Ulangi Langkah 1 |
| `Tidak ada PO yang cocok dengan '...'` | Salah ketik nama | Jalankan `python3 jalankan.py daftar` dulu |
| PDF tidak terbentuk | LibreOffice belum ada | Pasang LibreOffice, atau pakai berkas Excel-nya saja |
| Nama customer tertulis `(nama customer belum diisi)` | Belum diisi di master | Isi `config/customer.csv` |
