---
name: dokumen-penjualan-happy-pumpkin
description: Membaca order sheet Happy Pumpkin di Google Spreadsheet dan menghasilkan Surat Jalan, Invoice, Packing List, atau Faktur Pajak. Pakai skill ini setiap kali pekerjaan menyangkut order sheet, PO customer, nilai bersih penjualan, label ukuran per kategori produk, atau keempat dokumen tersebut. Juga dipakai saat memeriksa ulang angka dokumen terhadap order sheet.
---

# Dokumen Penjualan Happy Pumpkin

Skill ini memuat aturan yang tidak boleh dilanggar saat mengolah order sheet
menjadi dokumen penjualan. Konteks lengkap proyek ada di `CLAUDE.md`.

## Urutan kerja

```
1. Pindai tab      →  temukan semua blok, ambil semua baris
2. Tentukan nett   →  TOP pakai TOTAL VALUE, CBD/COD pakai kolom COD/CBD
3. Cocokkan        →  bandingkan dengan total milik order sheet sendiri
4. Baru bentuk dokumen
```

Langkah 3 tidak boleh dilewati. Kalau tidak cocok, berhenti dan laporkan.

---

## Aturan 1 — Tangkap seluruh isi tab

Satu tab PO berisi beberapa tabel bertumpuk. Tiap tabel punya baris judul
`ARTICLE CODE` sendiri.

```
Pindai kolom A dari baris 1 sampai baris terakhir.
Tiap sel yang mengandung teks "ARTICLE" adalah awal blok baru.
Baris judul ukuran ada di baris berikutnya, kolom D sampai L.
Data mulai dua baris di bawah judul, berhenti saat kolom A kosong.
```

Qty diambil dari kolom **N sampai V** (AVAILABLE TO ORDER), bukan D sampai L.
Baris dengan total qty nol dilewati.

**Pengecualian tab Packing List:** tab yang namanya diawali `Packing List`
tidak punya blok ORIGINAL PO, jadi qty-nya di kolom **D sampai L**. Tab ini
juga lebih sempit — hanya sekitar 15 kolom. Lebarkan dulu tabelnya jadi 29
kolom sebelum diproses, kalau tidak pembacaan kolom AB akan gagal.

### Wajib dicocokkan

Order sheet punya baris total sendiri di bawah tiap blok. Setelah memproses,
bandingkan hasil dengan baris itu. Untuk seluruh order sheet Agustus 2026:
**1.073 baris, 7.609 pcs, Rp500.874.100 sebelum diskon.**

Versi lama pernah hanya menangkap blok pertama tiap tab dan kehilangan
Rp147.829.100. Jangan terulang.

---

## Aturan 2 — Nilai bersih diambil dari kolomnya, bukan dihitung

**Jangan pernah** menghitung nilai bersih dari persentase diskon yang
disimpan di master atau ditebak dari rasio. Ambil dari order sheet:

| Cara bayar | Kolom sumber | Tanda |
|---|---|---|
| TOP / Tempo | `TOTAL VALUE` (AC) | font biru tua |
| CBD | `DISCOUNT CBD + X%` (AD) | font biru muda |
| COD | `DISCOUNT COD + X%` (AE) | font biru muda |

### Menentukan cara bayar

Pemeriksaannya di **tingkat order**, bukan per baris:

```
kolom COD/CBD terisi PENUH untuk semua baris  →  CBD/COD  →  pakai kolom itu
kolom COD/CBD terisi sebagian                 →  TOP      →  pakai TOTAL VALUE
kolom COD/CBD kosong sama sekali              →  TOP      →  pakai TOTAL VALUE
```

Terisi sebagian berarti **seluruh kolom itu diabaikan**, bukan ditambal.
Jangan pernah menghitung sendiri nilai untuk baris yang kosong, dan jangan
mencampur dua sumber dalam satu invoice.

Alasannya: kolom itu sering belum ditarik sampai bawah oleh Sales. Kalau
ditambal sebagian, hasilnya campur aduk dan tidak bisa dicocokkan ke mana
pun. Kalau order memang CBD tapi kolomnya belum lengkap, itu urusan yang
harus dirapikan Sales lebih dulu — bukan ditebak sistem.

Aturan ini sudah diuji: Baby Fame kolom AD terisi 51 dari 56, jadi TOP,
nett Rp22.899.000. Angka itu cocok persis dengan FA-009 di Laporan Penjualan
Agustus 2026.

Karena penentuannya murni dari kelengkapan data, **tidak perlu membaca font
atau status tersembunyi kolom lewat Sheets API**. Tetap sediakan override
manual per customer kalau suatu saat diperlukan, dan laporkan mana yang
dioverride.

### Wajib dilaporkan

Untuk tiap order, sebutkan: status TOP atau CBD/COD, kolom yang dipakai, dan
berapa baris kolom COD/CBD yang terisi dari total baris. Kalau sebagian,
tandai supaya Yosua bisa meminta Sales melengkapinya.

### Wajib dicocokkan

Nilai bersih di Invoice harus sama dengan jumlah kolom sumbernya. Kalau beda,
hentikan dan laporkan selisihnya per baris.

---

## Aturan 3 — Label ukuran ikut tabelnya

Tiap tabel dalam satu tab mewakili kategori produk berbeda dengan sistem
ukuran berbeda. Ada 12 set label berbeda di order sheet Agustus.

| Dokumen | Cara menampilkan |
|---|---|
| Surat Jalan | Tabel terpisah per kategori, judul ukuran sendiri, TOTAL per tabel |
| Packing List | Sama seperti Surat Jalan, ditambah kolom JUMLAH DIKIRIM dan NO. KOLI |
| Invoice | Label ukuran di deskripsi ikut tabel asal barang |

Tabel di Surat Jalan disusun bertumpuk dalam satu dokumen, dipisah satu baris
kosong. Nomor urut mulai dari 1 lagi di tiap tabel.

Kolom ukuran yang kosong boleh disembunyikan sebelum cetak, seperti kebiasaan
di order sheet.

---

## Aturan 4 — Bentuk deskripsi invoice

Bawaan: satu baris per artikel, semua warna dan ukuran dijumlahkan, tanpa
keterangan ukuran.

**Pengecualian: Haritsa, Katamama Tapos, Katamama Cikarang.** Dipecah per
ukuran — satu baris per artikel per ukuran.

Penulisan:

```
<nama barang> - <label ukuran>
```

Contoh: `Alice Ruffle Sleeveless Top Small Size - 2Y`

Label ukuran diambil dari header tabel asal barang itu.

> **Belum diputuskan.** Apakah label berupa angka polos (1, 2, 3) ditulis
> dengan akhiran Y sementara label bersatuan (`0-3M`, `7-8Y`, `S`, `M`, `L`)
> ditulis apa adanya? Tanyakan ke Yosua sebelum menerapkan. Jangan menebak.

Nama barang selalu sama persis dengan master harga. Tidak ada penamaan khusus
per customer. Warna tidak pernah masuk invoice.

---

## Pemeriksaan sebelum menyatakan selesai

| Periksa | Harus |
|---|---|
| Jumlah baris terbaca | Sama dengan jumlah baris di order sheet |
| Total qty | Sama dengan baris total milik order sheet |
| Nilai sebelum diskon | Sama dengan jumlah kolom TOTAL ATO (VALUE) |
| Nilai bersih | Sama dengan jumlah kolom sumber nett |
| Qty Surat Jalan vs Invoice | Sama |
| Kode artikel | Semua ada di master harga |
| Harga | Tidak ada yang nol |

Tampilkan perbandingannya dalam tabel. Jangan cuma menulis "cocok".

---

## Yang tidak boleh dilakukan

- Menghitung nilai bersih dari persentase yang disimpan atau ditebak
- Memakai satu set label ukuran untuk semua tabel
- Mengambil qty dari kolom ORIGINAL PO
- Menebak berat, jumlah koli, atau dimensi — itu diisi gudang
- Menyatakan selesai tanpa menunjukkan angka pencocokan
- Mengisi data yang kurang dengan tebakan. Tanya dulu.

---

## Catatan bahasa

Seluruh keluaran untuk Yosua dan timnya dalam bahasa Indonesia yang sederhana.
Hindari istilah teknis kalau ada padanan yang lebih umum. Rekan kerjanya
kurang akrab dengan teknologi, jadi hasilnya harus bisa dipakai tanpa
pelatihan khusus.
