# -*- coding: utf-8 -*-
"""Menyusun berkas ringkasan sistem otomatisasi untuk diunggah ke Drive Yosua."""
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

JUDUL = Font(bold=True, size=14, color="FFFFFF")
ISI_JUDUL = PatternFill("solid", fgColor="1F3864")
KEPALA = Font(bold=True, size=11, color="FFFFFF")
ISI_KEPALA = PatternFill("solid", fgColor="4472C4")
TEBAL = Font(bold=True)
GARIS = Border(*[Side(style="thin", color="BFBFBF")] * 4)
BUNGKUS = Alignment(wrap_text=True, vertical="top")
ATAS = Alignment(vertical="top")

wb = Workbook()
wb.remove(wb.active)


def lembar(nama, judul, kolom, baris, lebar):
    ws = wb.create_sheet(nama)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(kolom))
    s = ws.cell(1, 1, judul)
    s.font = JUDUL
    s.fill = ISI_JUDUL
    s.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 28
    for i, j in enumerate(kolom, start=1):
        c = ws.cell(3, i, j)
        c.font = KEPALA
        c.fill = ISI_KEPALA
        c.alignment = BUNGKUS
        c.border = GARIS
    for r, isi in enumerate(baris, start=4):
        for i, nilai in enumerate(isi, start=1):
            c = ws.cell(r, i, nilai)
            c.alignment = BUNGKUS if i > 1 else ATAS
            c.border = GARIS
            if i == 1:
                c.font = TEBAL
    for i, w in enumerate(lebar, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A4"
    return ws


# ---------------------------------------------------------------- 1
lembar(
    "MULAI DI SINI",
    "SISTEM OTOMATISASI DOKUMEN PENJUALAN — HAPPY PUMPKIN",
    ["Hal", "Keterangan"],
    [
        ("Berkas ini apa?",
         "Peta dan status sistem otomatisasi dokumen penjualan Happy Pumpkin. "
         "Berkas ini penjelasan, BUKAN mesinnya. Mesinnya berupa program di "
         "komputer/server, bukan rumus di dalam spreadsheet."),
        ("Gunanya sistem",
         "Membuat Surat Jalan, Invoice, Packing List, dan Faktur Pajak secara "
         "otomatis dari order sheet mana pun — bulan berjalan maupun order "
         "sheet lama 2025-2026."),
        ("Dibuat kapan", "10-12 September 2026"),
        ("Status hari ini",
         "Mesin SELESAI dan sudah diuji (60 tes otomatis lulus, angka Agustus "
         "2026 cocok sampai rupiah terakhir). Bot penyapu 12 jam SELESAI "
         "kodenya, tinggal menunggu akun layanan Google dibuat Yosua."),
        ("Yang sudah ada di Drive Yosua",
         "1) DATABASE CUSTOMER HAPPY PUMPKIN 2025-2026 — 164 customer, diskon, "
         "dan cara bayar.  2) Berkas ringkasan ini."),
        ("Yang BELUM disentuh",
         "Sheet OTOMATISASI_HAPPY_PUMPKIN_SINKRON milik Yosua masih utuh apa "
         "adanya, belum ditambah apa pun. Penambahan tab BOT_ baru terjadi "
         "setelah akun layanan Google dibuat. Lihat lembar BOT PENYAPU."),
        ("Cara baca berkas ini",
         "Lembar di bawah, urut: ISI SISTEM (bagian-bagiannya), 4 ATURAN WAJIB "
         "(pondasi yang tidak boleh dilanggar), CARA PAKAI HARIAN (untuk "
         "rekan kerja), BOT PENYAPU, ANGKA TERVERIFIKASI, dan YANG DITUNGGU."),
    ],
    [24, 108],
)

# ---------------------------------------------------------------- 2
lembar(
    "ISI SISTEM",
    "BAGIAN-BAGIAN SISTEM DAN TUGASNYA",
    ["Bagian", "Tugasnya", "Nama berkas program"],
    [
        ("Pembaca tata letak",
         "Menentukan letak tiap kolom dari TULISAN di baris judul, bukan dari "
         "huruf kolom. Wajib, karena susunan order sheet berubah tiap periode: "
         "Januari 2025 punya 3 kolom ukuran, Februari-Mei 6 kolom, Juli-September "
         "2025 8 kolom, Oktober 2025 sampai kini 9 kolom.",
         "tata_letak.py"),
        ("Pemindai blok",
         "Menangkap SEMUA tabel bertumpuk dalam satu tab PO. Satu tab bisa "
         "berisi 6 tabel dengan sistem ukuran berbeda-beda. Kalau hanya tabel "
         "pertama yang dibaca, qty dan nilainya kurang.",
         "pemindai.py"),
        ("Penentu nilai bersih",
         "Mengambil nilai bersih dari kolomnya sendiri (TOTAL VALUE / CBD / COD), "
         "tidak pernah menghitung dari persentase tebakan. Kolom yang terisi "
         "hanya sebagian diabaikan seluruhnya dan order diperlakukan TOP.",
         "nilai_bersih.py"),
        ("Pengurus label ukuran",
         "Tiap blok memakai label ukuran dari baris judulnya sendiri "
         "(0-3M/3-6M/S/M/L, atau 1/2/3/4/5/6/7-8Y/9-10Y, dan seterusnya). "
         "Akhiran Y dipakai sesuai keputusan Yosua (2 menjadi 2Y).",
         "ukuran.py"),
        ("Pencocokan wajib",
         "Sebelum dokumen dibuat, total program dibandingkan dengan baris TOTAL "
         "milik order sheet sendiri. Kalau tidak cocok, program BERHENTI dan "
         "tidak mengeluarkan dokumen. Ini pengaman supaya tidak ada faktur salah "
         "yang terlanjur dikirim.",
         "rekonsiliasi.py"),
        ("Empat dokumen",
         "Surat Jalan (satu tabel per blok, bertumpuk), Invoice (satu tabel "
         "menerus, tanpa warna, tanpa baris diskon CBD/COD), Packing List "
         "(seperti Surat Jalan ditambah kolom JUMLAH DIKIRIM dan NO. KOLI), "
         "Faktur Pajak (data siap ketik ke Coretax, DPP dihitung mundur).",
         "dokumen/"),
        ("Database customer",
         "Menelusuri 21 order sheet 2025-2026, mengumpulkan 379 PO menjadi "
         "164 customer beserta tingkat diskon dan cara bayar terakhirnya.",
         "db_customer.py"),
        ("Bot penyapu",
         "Membaca tab order sheet lewat Google Sheets API tiap 12 jam, "
         "membandingkan dengan sapuan sebelumnya, dan membunyikan alarm kalau "
         "ada PO lama yang ATO-nya sudah terisi lalu diubah.",
         "sapu/"),
        ("Keluaran berkas",
         "Excel (.xlsx) dan PDF. Semua dokumen dan laporan keluar ke folder "
         "keluaran/.",
         "pdf.py, laporan.py"),
        ("Tes otomatis",
         "60 tes yang dijalankan tiap kali program diubah, supaya perbaikan di "
         "satu tempat tidak diam-diam merusak tempat lain.",
         "tests/"),
    ],
    [22, 84, 24],
)

# ---------------------------------------------------------------- 3
lembar(
    "4 ATURAN WAJIB",
    "EMPAT ATURAN YANG TIDAK BOLEH DILANGGAR",
    ["No", "Aturan", "Kenapa penting", "Bukti nyata"],
    [
        (1, "Tangkap semua blok bertumpuk dalam satu tab PO.",
         "Satu tab PO sering berisi beberapa tabel dengan judul ARTICLE CODE "
         "sendiri-sendiri, mewakili kategori produk berbeda.",
         "Tab Miniku Agustus 2026: 6 blok, 288 baris, 1.783 pcs. Kalau hanya "
         "blok pertama yang dibaca, hilang sebagian besar."),
        (2, "Ambil nilai bersih dari kolomnya, jangan hitung dari persen.",
         "Judul kolom potongan berbeda-beda antar tab dan tidak selalu 1,5%. "
         "Menebak persentase pasti meleset.",
         "Yulis memakai CBD + 2% (meleset Rp112.850 kalau ditebak 1,5%), "
         "Baby Wise Surabaya memakai COD + 2% (meleset Rp80.402)."),
        (3, "Label ukuran mengikuti baris judul tiap blok.",
         "Tiap blok punya sistem ukuran sendiri. Memakai satu set label untuk "
         "semua blok membuat qty masuk ke kolom yang salah.",
         "Miniku blok 2 memakai 0-3M/3-6M/6-12M/S/M/L, blok 3 memakai "
         "1/2/3/4/5/6/7-8Y/9-10Y."),
        (4, "Invoice Haritsa dan Katamama dipecah per artikel + ukuran.",
         "Customer lain cukup per artikel. Dua customer ini memang menerima "
         "rincian sampai ukuran.",
         "Nilai per baris dibagi ke ukuran memakai pembagian sisa terbesar, "
         "supaya jumlah pecahannya tetap sama persis dengan nilai barisnya."),
    ],
    [5, 46, 50, 54],
)

# ---------------------------------------------------------------- 4
lembar(
    "CARA PAKAI HARIAN",
    "CARA PAKAI SEHARI-HARI UNTUK DIVISI",
    ["Langkah", "Perintah yang diketik", "Hasilnya"],
    [
        ("1. Ambil order sheetnya",
         "Di Google Sheets: File > Download > Microsoft Excel (.xlsx), simpan "
         "sebagai data/order_sheet.xlsx",
         "Tidak perlu kunci API, tidak perlu izin khusus. Cara ini sengaja "
         "dipilih supaya tidak terhalang Apps Script yang terkunci."),
        ("2. Lihat daftar PO", "python3 jalankan.py daftar",
         "Tabel semua PO di order sheet itu: jumlah baris, qty, nilai kotor, "
         "nilai bersih, dan cara bayarnya."),
        ("3. Periksa dulu", "python3 jalankan.py periksa",
         "LAPORAN_PENCOCOKAN.xlsx. Semua harus COCOK. Kalau ada yang tidak, "
         "jangan cetak dokumen dulu."),
        ("4. Buat dokumen satu PO",
         "python3 jalankan.py buat \"PO 20 Agustus - Miniku\"",
         "Empat berkas sekaligus di folder keluaran/: Surat Jalan, Invoice, "
         "Packing List, Faktur Pajak."),
        ("5. Buat semua sekaligus", "python3 jalankan.py buat-semua",
         "Seluruh PO di order sheet itu, masing-masing satu folder."),
        ("6. Rekap sebulan", "python3 jalankan.py rekap",
         "Ringkasan nilai penjualan sebulan untuk dicocokkan ke Laporan "
         "Penjualan."),
        ("7. Database customer", "python3 jalankan.py telusuri",
         "DATABASE_CUSTOMER.xlsx dari seluruh order sheet 2025-2026."),
        ("Kalau program berhenti",
         "(tidak perlu mengetik apa-apa)",
         "Program sengaja berhenti kalau angkanya tidak cocok dengan baris "
         "TOTAL order sheet. Baca pesannya, perbaiki order sheetnya, jalankan "
         "ulang. JANGAN dipaksa terus."),
    ],
    [24, 52, 72],
)

# ---------------------------------------------------------------- 5
lembar(
    "BOT PENYAPU",
    "BOT PENYAPU 12 JAM — PEMANTAU PERUBAHAN ORDER SHEET",
    ["Hal", "Keterangan"],
    [
        ("Tugasnya",
         "Tiap 12 jam membaca seluruh order sheet 2025-2026, membandingkan "
         "dengan sapuan sebelumnya, lalu melapor kalau ada PO lama yang sudah "
         "final tiba-tiba berubah."),
        ("Cara membacanya",
         "MEMBACA TAB LANGSUNG lewat Google Sheets API. Bot TIDAK mengunduh "
         "spreadsheet tiap hari — sesuai arahan Yosua 11 September 2026."),
        ("Hemat berapa",
         "Sapuan pertama 21 order sheet = 42 panggilan API. Kalau tidak ada "
         "yang berubah = 0 panggilan. Kalau 1 order sheet berubah = 2 "
         "panggilan. Bandingkan dengan mengunduh: selalu ~25 MB tiap kali."),
        ("Kuota Google",
         "Batas Google 300 panggilan baca per menit. Pemakaian tertinggi kita "
         "42, itu pun hanya sekali di awal. Tidak perlu minta tambah kuota."),
        ("Hak aksesnya",
         "Akun layanan diberi akses VIEWER saja ke folder order sheet. Bot "
         "secara teknis TIDAK BISA mengubah order sheet, walaupun salah "
         "perintah."),
        ("Boleh menulis di mana",
         "Hanya tab berawalan BOT_ di sheet OTOMATISASI: BOT_DAFTAR_PO, "
         "BOT_PERUBAHAN, BOT_STATUS. Program MENOLAK menulis ke tab lain — "
         "penolakan itu diuji otomatis. Tab buatan Yosua aman."),
        ("Alarm GENTING",
         "PO yang ATO-nya SUDAH TERISI lalu qty, susunan qty, jumlah baris, "
         "nilai bersih, nilai kotor, cara bayar, atau rumusnya berubah. Ini "
         "yang berbahaya, karena fakturnya mungkin sudah terlanjur dikirim."),
        ("Alarm PERHATIAN",
         "PO baru muncul, PO hilang, atau nilai tidak terbaca."),
        ("Kabar biasa",
         "Perubahan pada PO yang ATO-nya memang belum terisi. Wajar, tidak "
         "perlu ditindak."),
        ("Pengaman alarm palsu",
         "Kalau nilai rupiah terbaca nol padahal jumlah baris dan qty persis "
         "sama, itu dianggap gagal baca rumus, bukan angka yang diubah orang. "
         "Diuji pada Agustus 2026: tanpa pengaman muncul 40 alarm palsu, "
         "dengan pengaman tinggal 2 perubahan yang memang disisipkan untuk "
         "diuji. Alarm palsu membuat orang berhenti percaya laporannya."),
        ("Laporannya ke mana",
         "Berkas laporan ditulis ke folder Google Drive Yosua, dan ringkasannya "
         "ke tab BOT_ di sheet OTOMATISASI."),
        ("Supaya bot jalan",
         "Yosua membuat akun layanan Google sendiri lewat Google Cloud Console "
         "(langkahnya ada di berkas PANDUAN_BOT.md), lalu membagikan folder "
         "order sheet ke alamat akun layanan itu sebagai Viewer. Berkas "
         "kredensialnya JANGAN dikirim lewat WhatsApp atau email."),
    ],
    [24, 108],
)

# ---------------------------------------------------------------- 6
ws = lembar(
    "ANGKA TERVERIFIKASI",
    "ANGKA YANG SUDAH DIBUKTIKAN — ORDER SHEET AGUSTUS 2026",
    ["Pemeriksaan", "Hasil"],
    [
        ("PO berisi data", "16 PO"),
        ("Blok tabel", "37 blok"),
        ("Baris artikel", "1.194 baris"),
        ("Total qty", "8.600 pcs"),
        ("Nilai sebelum diskon", "Rp561.768.900"),
        ("Nilai bersih", "Rp424.156.009"),
        ("Cocok dengan baris TOTAL tiap tab", "16 dari 16 tab cocok"),
        ("qty x harga = nilai kotor", "1.194 dari 1.194 baris cocok"),
        ("Kode artikel ada di Harga Retail", "0 yang tidak ketemu"),
        ("Nama barang sama dengan master harga", "1.194 dari 1.194 sama persis"),
        ("Harga PO sama dengan master harga", "sama persis, rasio 1,0 semua"),
        ("Uji silang paling meyakinkan",
         "Dikurangi satu tab yang baru terisi (Baby Wise 31 Agustus: 121 baris, "
         "991 pcs, Rp60.894.800), angkanya kembali PERSIS ke angka acuan lama "
         "1.073 baris / 7.609 pcs / Rp500.874.100 / nett Rp380.007.279."),
        ("Cocok dengan faktur asli",
         "FA-009 Baby Fame Rp22.899.000 cocok persis dengan faktur yang sudah "
         "terbit."),
        ("Selisih yang ditemukan program",
         "FA-013 Panda & Bear tercatat potongan 20% padahal seharusnya 18% "
         "(selisih Rp125.040). FA-008 Canina tercatat tanpa potongan (selisih "
         "Rp255.618). Dua-duanya perlu ditelusuri Yosua."),
        ("Database customer 2025-2026",
         "21 dari 22 order sheet terbaca, 379 PO, 164 customer. Diskon: 25% "
         "(60 customer), 20% (33), 18% (25), 22% (18), 30% (6). Cara bayar "
         "terakhir: TOP 115, CBD 38, COD 10."),
        ("Tes otomatis", "60 tes, semuanya lulus"),
    ],
    [42, 96],
)

# ---------------------------------------------------------------- 7
lembar(
    "YANG DITUNGGU",
    "YANG MASIH DITUNGGU DARI YOSUA — SISTEM BELUM 100% TANPA INI",
    ["Yang ditunggu", "Kenapa perlu", "Akibat kalau belum ada"],
    [
        ("Akun layanan Google",
         "Supaya bot penyapu 12 jam bisa jalan. Harus dibuat Yosua sendiri di "
         "Google Cloud Console, tidak bisa dibuatkan dari sini.",
         "Bot belum jalan. Tab BOT_ belum muncul di sheet OTOMATISASI."),
        ("NPWP 14 customer",
         "Wajib untuk Faktur Pajak di Coretax.",
         "Faktur Pajak keluar dengan kolom NPWP kosong. TIDAK ditebak program."),
        ("Alamat 8 customer",
         "Baby Wise Surabaya, Natasha, Panda & Bear, Katamama Cikarang, Yulis, "
         "Miniku, Baby Fame, Canina.",
         "Kop Kepada Yth. pada Surat Jalan dan Invoice kosong."),
        ("Customer mana pakai perusahaan mana",
         "PPN 11% hanya berlaku untuk order lewat CV. Dwi Putra Mandiri, tidak "
         "berlaku untuk CV. Mutiara Timur Nusantara. 14 customer belum "
         "ditentukan.",
         "Program memakai DPM sebagai bawaan dan memberi peringatan. Risiko "
         "salah kena PPN."),
        ("NPWP dan alamat CV Mutiara Timur Nusantara",
         "Kop surat, rekening, dan NPWP penjual ikut perusahaan pemrosesnya.",
         "Dokumen atas nama MTN belum bisa dicetak lengkap."),
        ("NPWP CV Dwi Putra Mandiri",
         "Wajib di Faktur Pajak.",
         "Kolom NPWP penjual kosong."),
        ("Format nomor dokumen",
         "Pola lama 0050726 = urut 005, bulan 07, tahun 26. Nomor urutnya tidak "
         "ditebak program.",
         "Nomor dokumen dikosongkan, diisi manual saat cetak."),
        ("18 grup nama customer",
         "Ada di lembar PERIKSA_NAMA pada berkas DATABASE CUSTOMER. Perlu "
         "dipastikan sama toko atau beda toko. TIDAK digabung dengan menebak, "
         "karena Baby Wise dan Baby Wise Surabaya memang dua toko berbeda.",
         "Database customer masih punya nama kembar."),
        ("Termin per customer",
         "Termin 30 hari tidak berlaku untuk semua.",
         "Semua sementara disetel 30 hari."),
        ("Berkas logo",
         "Untuk kop surat. Taruh di folder config/, tulis namanya di "
         "perusahaan.yaml.",
         "Dokumen tercetak tanpa logo."),
        ("Tarif PPN",
         "Sementara 11%, perlu dipastikan masih sesuai aturan yang berlaku.",
         "Faktur Pajak memakai 11%."),
        ("Order Sheet Juni 2025",
         "Berkasnya 11,4 MB, ditolak Google saat diekspor ke Excel.",
         "Satu-satunya order sheet yang belum terbaca. Akan terbaca sendiri "
         "begitu bot penyapu jalan, karena bot membaca lewat API tanpa "
         "mengekspor."),
    ],
    [34, 62, 62],
)

wb.save("keluaran/SISTEM_OTOMATISASI_HAPPY_PUMPKIN.xlsx")
print("tersimpan:", wb.sheetnames)

# --- versi CSV, untuk diunggah ke Drive sebagai Google Sheet satu lembar ---
import csv, io

out = io.StringIO()
w = csv.writer(out, lineterminator="\n")
w.writerow(["SISTEM OTOMATISASI DOKUMEN PENJUALAN - HAPPY PUMPKIN", "", "", ""])
w.writerow(["CV Dwi Putra Mandiri", "", "", ""])
for nama in wb.sheetnames:
    ws = wb[nama]
    w.writerow([])
    w.writerow(["### " + nama])
    w.writerow([ws.cell(3, c).value for c in range(1, ws.max_column + 1)])
    for r in range(4, ws.max_row + 1):
        isi = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
        if any(isi):
            w.writerow([("" if v is None else str(v)) for v in isi])
with open("keluaran/SISTEM_OTOMATISASI_HAPPY_PUMPKIN.csv", "w", encoding="utf-8") as f:
    f.write(out.getvalue())
print("csv juga tersimpan")
