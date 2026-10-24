# MASTER PROMPT — tempel ini ke Claude Code

> Salin seluruh isi blok di bawah, lalu tempel sebagai pesan pertama di Claude Code.
> Sebelum itu, taruh ketiga berkas ini di folder proyek:
> `CLAUDE.md`, `.claude/skills/dokumen-happy-pumpkin/SKILL.md`, dan berkas ini.

---

Saya Yosua, Finance di CV Dwi Putra Mandiri (brand Happy Pumpkin). Saya
memindahkan proyek otomatisasi dokumen penjualan dari Claude.ai ke sini.

Baca dulu `CLAUDE.md` dan `.claude/skills/dokumen-happy-pumpkin/SKILL.md`
sebelum mengerjakan apa pun. Keduanya berisi konteks lengkap, temuan, dan
keputusan yang sudah saya ambil. Jangan mengulang penelusuran yang sudah
tercatat di sana.

## Yang saya butuhkan

Sistem yang membaca order sheet di Google Spreadsheet, lalu menghasilkan
**Surat Jalan, Invoice, Packing List, dan Faktur Pajak** sesuai ketentuan
masing-masing customer.

Order sheet: `1yBWhMTFY8pLEhvEVFHI2hhrOouUx36aGjaE83ApcNhw`

## Empat perbaikan yang harus dikerjakan lebih dulu

### 1. Tangkap SELURUH isi tiap tab, tanpa kecuali

Versi lama hanya menangkap blok pertama tiap tab, hilang Rp147.829.100.
Satu tab PO bisa berisi beberapa tabel bertumpuk, masing-masing dengan baris
judul `ARTICLE CODE` sendiri.

Aturan: pindai seluruh tab sampai baris terakhir, temukan **semua** baris
judul, ambil semua baris data di bawah tiap judul. Selesai memproses, wajib
cocokkan dengan baris total milik order sheet sendiri. Kalau tidak sama,
berhenti dan laporkan — jangan lanjut membuat dokumen.

### 2. Nilai bersih diambil dari kolom yang benar, dinamis per order

Jangan pernah menghitung diskon dari persentase yang ditebak atau disimpan
di master. Ambil langsung nilai bersihnya dari order sheet:

- **Customer TOP/Tempo** → kolom `TOTAL VALUE` (font biru tua)
- **Customer COD/CBD** → kolom `DISCOUNT COD/CBD + X%` (font biru muda)

Penentuannya di tingkat order, dari kelengkapan kolomnya:

```
kolom COD/CBD terisi PENUH semua baris  →  CBD/COD  →  pakai kolom itu
kolom COD/CBD terisi sebagian           →  TOP      →  pakai TOTAL VALUE
kolom COD/CBD kosong                    →  TOP      →  pakai TOTAL VALUE
```

Kolom yang terisi sebagian **diabaikan seluruhnya**. Jangan ditambal, jangan
dihitung sendiri, jangan mencampur dua sumber dalam satu invoice. Sales
sering belum menarik rumusnya sampai baris terakhir — Miniku hanya 44 dari
288 baris.

Tetap laporkan berapa baris yang terisi dari total, supaya saya bisa minta
Sales melengkapinya.

Nilai bersih di Invoice dan semua dokumen lain wajib dicocokkan dengan
jumlah kolom sumbernya. Kalau beda, hentikan dan laporkan.

### 3. Label ukuran ikut header tabelnya masing-masing

Tiap tabel dalam satu tab punya sistem ukuran sendiri karena mewakili
kategori produk berbeda. Contoh: `PO 31 Agustus - Baby Wise` punya 3 tabel
dengan 3 sistem ukuran.

- **Surat Jalan dan Packing List** — buat ulang tabel terpisah untuk tiap
  kategori, lengkap dengan baris judul ukurannya sendiri dan TOTAL per tabel
- **Invoice** — nilai ukuran yang muncul di deskripsi ikut header tabel asal
  barang itu, bukan satu daftar global

### 4. Format deskripsi invoice

Bawaan: satu baris per artikel, tanpa keterangan ukuran.

Pengecualian **Haritsa dan Katamama** (Tapos maupun Cikarang): dipecah per
ukuran, satu baris per artikel per ukuran.

Penulisannya berubah, pakai tanda hubung bukan kata "Uk.":

```
sebelum : Alice Ruffle Sleeveless Top Small Size Uk. 2
sesudah : Alice Ruffle Sleeveless Top Small Size - 2Y
```

**Tanyakan dulu ke saya** sebelum menerapkan: apakah semua label ukuran yang
berupa angka polos (1, 2, 3, 4, 5, 6) ditulis dengan akhiran Y, sementara
label yang sudah punya satuan (`0-3M`, `7-8Y`, `S`, `M`, `L`, `XL`) ditulis
apa adanya? Jangan menebak.

## Cara saya ingin Anda bekerja

- Bahasa Indonesia yang jelas dan sederhana. Rekan kerja saya kurang akrab
  dengan teknologi.
- Selalu cocokkan angka hasil olahan dengan angka milik order sheet sendiri
  sebelum menyatakan selesai. Tunjukkan perbandingannya.
- Kalau ada data yang kurang atau meragukan, tanya dulu. Jangan diisi tebakan.
- Ingatkan saya kalau ada yang berpotensi terlewat di laporan keuangan atau
  pajak.
- Keluaran berupa berkas: Excel (.xlsx) atau PDF sesuai kebutuhan.

## Langkah pertama

Jangan langsung menulis kode. Mulai dengan:

1. Baca `CLAUDE.md` dan berkas skill
2. Sampaikan rencana kerja Anda dalam poin-poin singkat
3. Sebutkan apa saja yang perlu saya siapkan (kredensial Sheets API,
   akses, keputusan yang tertunda)
4. Ajukan pertanyaan yang perlu dijawab sebelum mulai, termasuk soal
   akhiran Y di nomor 4

Setelah saya setujui rencananya, baru mulai membangun.
