"""CONTOH LOKAL: kolom AD/AE diisi lewat PILIHAN persen, bukan rumus diketik.

Dibuat 22 Oktober 2026 atas permintaan Yosua: "saya ingin menambahkan fitur
agar ada pilihan untuk memilih persentase diskon jadi tidak harus mengetik
rumus ... jangan langsung diterapkan di file online coba dulu ambil data
ordersheet lalu buat di file excel lokal".

BERKAS INI TIDAK MENYENTUH ORDER SHEET ONLINE SAMA SEKALI. Ia hanya MEMBACA
salinan .xlsx lalu menulis berkas contoh baru di keluaran/.

Gagasannya:

  SEKARANG   tiap sel AD diketik sendiri  ->  =AC3-(AC3*1.5)   (tanda % lupa)
  USULAN     persen DIPILIH sekali di satu sel  ->  AD3 = AC3 x (1 - $AI$4)

Tiga cacat yang hilang sendiri kalau persennya dipilih, bukan diketik:

  1. tanda % lupa diketik (CLAUDE.md bagian 52) - tidak mungkin lagi, sebab
     yang disimpan di sel pilihan sudah berupa angka persen
  2. kolom DISC beda dari persen di dalam rumus (bagian 51) - tidak mungkin
     lagi, sebab AB dan AC membaca SEL YANG SAMA
  3. judul kolom beda dari tarif sebenarnya (bagian 12) - tidak mungkin lagi,
     sebab judulnya dibentuk dari sel pilihan itu juga
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

AKAR = Path(__file__).resolve().parent.parent

LBR_DAFTAR = "DAFTAR DISKON"

# Kolom yang disalin APA ADANYA sebagai nilai (A sampai AA)
SALIN_SAMPAI = 27
K_W, K_X, K_Z, K_AB, K_AC, K_AD, K_AE = 23, 24, 26, 28, 29, 30, 31

# Sel pengaturan, ditaruh di kolom AH/AI — di LUAR kolom yang dibaca program,
# jadi letak kolom A..AE tidak bergeser sedikit pun dan pemindai tetap jalan.
K_LABEL, K_PILIH = 34, 35
B_DASAR, B_CBD, B_COD, B_TAMBAH = 2, 3, 4, 5

PERSEN_DASAR = [0.0, 0.18, 0.20, 0.22, 0.25, 0.265, 0.275, 0.30]
PERSEN_TAMBAH = [0.0, 0.015, 0.02, 0.025, 0.03, 0.05]

JUDUL = Font(bold=True, size=9, color="FFFFFF")
ISI_JUDUL = PatternFill("solid", fgColor="2F5597")
KUNING = PatternFill("solid", fgColor="FFF2CC")
HIJAU = PatternFill("solid", fgColor="E2EFDA")
TIPIS = Side(style="thin", color="BFBFBF")
KOTAK = Border(left=TIPIS, right=TIPIS, top=TIPIS, bottom=TIPIS)
TEBAL = Side(style="medium", color="C00000")
KOTAK_PILIH = Border(left=TEBAL, right=TEBAL, top=TEBAL, bottom=TEBAL)
RP = "#,##0"
PCT = "0.0#%"


def _lembar_daftar(wb: openpyxl.Workbook) -> None:
    """Daftar persen yang boleh dipilih. SATU tempat untuk seluruh order sheet."""
    ws = wb.create_sheet(LBR_DAFTAR)
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["D"].width = 72
    for c, nama in ((1, "DISKON DASAR"), (2, "TAMBAHAN CBD/COD")):
        sel = ws.cell(1, c, nama)
        sel.font = JUDUL
        sel.fill = ISI_JUDUL
        sel.alignment = Alignment(horizontal="center")
    for i, v in enumerate(PERSEN_DASAR, start=2):
        s = ws.cell(i, 1, v)
        s.number_format = PCT
        s.alignment = Alignment(horizontal="center")
    for i, v in enumerate(PERSEN_TAMBAH, start=2):
        s = ws.cell(i, 2, v)
        s.number_format = PCT
        s.alignment = Alignment(horizontal="center")

    ws.cell(1, 4, "CARA MENAMBAH PILIHAN BARU").font = Font(bold=True, size=11)
    baris = [
        "Kalau ada tingkat diskon baru, cukup ketik angkanya di bawah daftar",
        "pada lembar INI — pilihannya langsung muncul di semua tab PO.",
        "",
        "Ketiknya pakai tanda persen, contoh: 28%  (jangan 28, jangan 0,28).",
        "",
        "JANGAN menghapus atau menyisipkan baris di tengah daftar — pilihan di",
        "tab PO menunjuk ke rentang baris ini, dan rentangnya akan bergeser.",
    ]
    for i, t in enumerate(baris, start=2):
        ws.cell(i, 4, t).font = Font(size=10, bold=t.startswith(("Ketiknya", "JANGAN")))
    ws.sheet_view.showGridLines = False


def _panel(ws, pakai_cbd: bool, pakai_cod: bool, tambahan: float) -> None:
    """Empat sel pilihan di kolom AH/AI.

    Kolom yang TIDAK ADA di tab aslinya tidak diberi pilihan sama sekali —
    sengaja. Memberi pilihan 0% untuk kolom yang tidak dipakai akan membuat
    kolom itu terisi penuh dengan angka yang sama dengan TOTAL VALUE, dan
    Aturan 2 akan memilihnya sebagai CBD/COD padahal order ini TOP. Nilainya
    kebetulan sama hari ini, tapi cara bayar yang tercatat jadi salah.
    """
    ws.column_dimensions[L(K_LABEL)].width = 30
    ws.column_dimensions[L(K_PILIH)].width = 14

    sel = ws.cell(1, K_LABEL, "PENGATURAN DISKON — PILIH DARI DAFTAR")
    sel.font = Font(bold=True, size=10, color="FFFFFF")
    sel.fill = ISI_JUDUL
    ws.merge_cells(start_row=1, start_column=K_LABEL, end_row=1, end_column=K_PILIH)
    sel.alignment = Alignment(horizontal="center", vertical="center")

    isi = [
        (B_DASAR, "Diskon dasar (kolom DISC)", 0.25, True),
        (B_CBD, "Tambahan CBD", 0.02, pakai_cbd),
        (B_COD, "Tambahan COD", 0.015, pakai_cod),
        (B_TAMBAH, "Tambahan ke-2 (kalau ada)", tambahan, pakai_cbd),
    ]
    aktif = []
    for r, nama, bawaan, dipakai in isi:
        lab = ws.cell(r, K_LABEL, nama)
        lab.font = Font(size=10)
        lab.border = KOTAK
        lab.fill = HIJAU
        if not dipakai:
            lab.font = Font(size=10, italic=True, color="808080")
            s = ws.cell(r, K_PILIH, "tidak dipakai")
            s.font = Font(size=9, italic=True, color="808080")
            s.border = KOTAK
            s.alignment = Alignment(horizontal="center")
            continue
        aktif.append(r)
        p = ws.cell(r, K_PILIH, bawaan)
        p.number_format = PCT
        p.fill = KUNING
        p.border = KOTAK_PILIH
        p.font = Font(bold=True, size=11)
        p.alignment = Alignment(horizontal="center")

    dv_dasar = DataValidation(
        type="list",
        formula1=f"'{LBR_DAFTAR}'!$A$2:$A${len(PERSEN_DASAR) + 1}",
        allow_blank=False,
        showDropDown=False,
    )
    dv_dasar.error = "Pilih salah satu persen dari daftar."
    dv_dasar.errorTitle = "Harus dipilih dari daftar"
    dv_tambah = DataValidation(
        type="list",
        formula1=f"'{LBR_DAFTAR}'!$B$2:$B${len(PERSEN_TAMBAH) + 1}",
        allow_blank=False,
        showDropDown=False,
    )
    dv_tambah.error = "Pilih salah satu persen dari daftar."
    dv_tambah.errorTitle = "Harus dipilih dari daftar"
    ws.add_data_validation(dv_dasar)
    ws.add_data_validation(dv_tambah)
    dv_dasar.add(ws.cell(B_DASAR, K_PILIH))
    for r in (B_CBD, B_COD, B_TAMBAH):
        if r in aktif:
            dv_tambah.add(ws.cell(r, K_PILIH))

    r = B_TAMBAH + 2
    for t in [
        "Isi hanya SEL KUNING di atas.",
        "Kolom DISC, TOTAL VALUE, CBD dan COD ikut sendiri.",
        "Tidak ada rumus yang perlu diketik lagi.",
        "",
        "Tambahan ke-2 dipakai kalau diskonnya tiga tingkat,",
        "contoh 25% + 2% + 2%. Kalau tidak ada, pilih 0%.",
        "Potongannya BERUNTUN, bukan dijumlahkan.",
    ]:
        s = ws.cell(r, K_LABEL, t)
        s.font = Font(size=9, italic=True, color="7F6000")
        r += 1


def _judul_kolom(ws, pakai_cbd: bool, pakai_cod: bool) -> None:
    """Judul AD/AE dibentuk dari sel pilihan, jadi tidak bisa berbeda lagi."""
    p = f"${L(K_PILIH)}$"
    # Persennya ditulis ROUND(x*100,2)&"%", BUKAN TEXT(x,"0.##%").
    # Diuji langsung di Google Sheets 22 Okt 2026: TEXT(0,02;"0.##%") di sana
    # menghasilkan "2.%" — ada TITIK menggantung sesudah angkanya. Bentuk
    # ROUND ini memberi "2%", "1.5%", "27.5%" dengan benar di Google Sheets
    # MAUPUN Excel.
    ad = (f'="DISCOUNT CBD + "&ROUND({p}{B_CBD}*100,2)&"%"'
          f'&IF({p}{B_TAMBAH}>0," + "&ROUND({p}{B_TAMBAH}*100,2)&"%","")')
    ae = f'="DISCOUNT COD + "&ROUND({p}{B_COD}*100,2)&"%"'
    pasang = ([(K_AD, ad)] if pakai_cbd else []) + ([(K_AE, ae)] if pakai_cod else [])
    for kol, rumus in pasang:
        sel = ws.cell(1, kol, rumus)
        sel.font = Font(bold=True, size=9)
        sel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        sel.fill = PatternFill("solid", fgColor="DDEBF7")
        sel.border = KOTAK


def _rumus_baris(ws, r: int, pakai_cbd: bool, pakai_cod: bool) -> None:
    p = f"${L(K_PILIH)}$"
    z, ac = f"{L(K_Z)}{r}", f"{L(K_AC)}{r}"

    ab = ws.cell(r, K_AB, f"={p}{B_DASAR}")
    ab.number_format = PCT
    ab.alignment = Alignment(horizontal="center")

    ws.cell(r, K_AC, f"={z}*(1-{p}{B_DASAR})")
    kolom = [K_AC]
    if pakai_cbd:
        ws.cell(r, K_AD, f"={ac}*(1-{p}{B_CBD})*(1-{p}{B_TAMBAH})")
        kolom.append(K_AD)
    if pakai_cod:
        ws.cell(r, K_AE, f"={ac}*(1-{p}{B_COD})")
        kolom.append(K_AE)
    for kol in kolom:
        s = ws.cell(r, kol)
        s.number_format = RP
        s.border = KOTAK


def _salin_tab(wb_baru, ws_nilai, nama: str, tambahan: float) -> int:
    ws = wb_baru.create_sheet(nama[:31])
    last = max(
        (r for r in range(1, ws_nilai.max_row + 1)
         if ws_nilai.cell(r, 1).value not in (None, "")),
        default=0,
    )
    judul_ada = {
        r for r in range(1, last + 1)
        if str(ws_nilai.cell(r, 1).value or "").strip().upper().startswith("ARTICLE")
    }
    jdl_cbd = str(ws_nilai.cell(1, K_AD).value or "")
    jdl_cod = str(ws_nilai.cell(1, K_AE).value or "")
    pakai_cbd = "CBD" in jdl_cbd.upper()
    pakai_cod = "COD" in jdl_cod.upper()

    n = 0
    for r in range(1, last + 1):
        # Pada BARIS JUDUL, judul DISC dan TOTAL VALUE ikut disalin. Kalau
        # tidak, kedua kolom itu tampil tanpa judul sama sekali — ketahuan
        # dari melihat gambar hasil render, bukan dari nilai selnya.
        batas = K_AC if r in judul_ada else SALIN_SAMPAI
        for c in range(1, batas + 1):
            v = ws_nilai.cell(r, c).value
            if v is None:
                continue
            sel = ws.cell(r, c, v)
            if c in (K_X, K_Z) or (c == K_W and r not in judul_ada):
                sel.number_format = RP
            if r in judul_ada:
                sel.font = Font(bold=True, size=9)
                sel.alignment = Alignment(horizontal="center", vertical="center",
                                          wrap_text=True)
                sel.fill = PatternFill("solid", fgColor="DDEBF7")
                sel.border = KOTAK
        if r in judul_ada:
            continue
        kode = ws_nilai.cell(r, 1).value
        qty = ws_nilai.cell(r, K_W).value
        if kode and isinstance(qty, (int, float)) and qty:
            _rumus_baris(ws, r, pakai_cbd, pakai_cod)
            n += 1

    _judul_kolom(ws, pakai_cbd, pakai_cod)
    _panel(ws, pakai_cbd=pakai_cbd, pakai_cod=pakai_cod, tambahan=tambahan)

    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 14
    for c in range(4, 23):
        ws.column_dimensions[L(c)].width = 5.5
    for c in range(23, 32):
        ws.column_dimensions[L(c)].width = 15
    ws.freeze_panes = "D2"
    ws.sheet_view.showGridLines = False
    return n


def _cara_pakai(wb, rincian: list[tuple[str, int]]) -> None:
    ws = wb.create_sheet("CARA PAKAI", 0)
    ws.column_dimensions["A"].width = 100
    sel = ws.cell(1, 1, "CONTOH: MEMILIH PERSEN DISKON, BUKAN MENGETIK RUMUS")
    sel.font = Font(bold=True, size=15)
    ws.cell(2, 1, "Berkas CONTOH LOKAL · dibuat 22 Oktober 2026 · order sheet online TIDAK disentuh").font = Font(italic=True, size=10, color="C00000")

    r = 4
    blok = [
        ("BAGIAN", "YANG HARUS DICOBA"),
        ("", "1. Buka salah satu tab PO di berkas ini."),
        ("", "2. Lihat ke kanan, kolom AH dan AI — ada kotak PENGATURAN DISKON."),
        ("", "3. Klik sel KUNING, muncul tanda panah kecil. Pilih persennya dari daftar."),
        ("", "4. Kolom DISC, TOTAL VALUE, DISCOUNT CBD, dan DISCOUNT COD berubah sendiri."),
        ("", "5. Judul kolom AD dan AE juga ikut berubah mengikuti pilihannya."),
        ("", ""),
        ("BAGIAN", "APA YANG BERUBAH DARI CARA SEKARANG"),
        ("", "SEKARANG  : tiap sel AD diketik sendiri, contoh  =AC3-(AC3*1.5%)"),
        ("", "USULAN    : persennya dipilih SEKALI di satu sel, rumusnya menunjuk ke situ"),
        ("", ""),
        ("BAGIAN", "TIGA KESALAHAN YANG HILANG SENDIRI"),
        ("", "1. Tanda % lupa diketik. Inilah yang membuat PO 11 September - Katamama"),
        ("", "   (Tapos) kurang menagih Rp999.034, dan 16 tab lain berisiko sama."),
        ("", "   Dengan pilihan, angkanya sudah berupa persen — tidak bisa lupa lagi."),
        ("", "2. Kolom DISC beda dari persen di dalam rumus (Katamama Cikaret Maret:"),
        ("", "   DISC tertulis 25%, rumusnya memakai 22%). Sekarang keduanya membaca"),
        ("", "   SEL YANG SAMA, jadi tidak mungkin lagi berbeda."),
        ("", "3. Judul kolom beda dari tarif sebenarnya. Judulnya sekarang dibentuk"),
        ("", "   dari sel pilihan itu juga."),
        ("", ""),
        ("BAGIAN", "YANG TIDAK BERUBAH"),
        ("", "Letak kolom A sampai AE sama persis seperti order sheet sekarang."),
        ("", "Sel pengaturan ditaruh di kolom AH/AI yang kosong, jadi program pembuat"),
        ("", "Invoice dan Surat Jalan tetap membacanya tanpa perubahan apa pun."),
        ("", "Aturan 2 juga tidak berubah: nilai bersih tetap dibaca dari kolomnya."),
        ("", ""),
        ("BAGIAN", "YANG PERLU DIPERHATIKAN SEBELUM DIPASANG DI ORDER SHEET ONLINE"),
        ("", "1. Daftar persennya ada di lembar DAFTAR DISKON — satu tempat untuk semua."),
        ("", "2. Di Google Sheets pilihan ini namanya Data > Data validation. Bentuknya"),
        ("", "   sama, hanya tampilan panahnya sedikit berbeda dari Excel."),
        ("", "3. Kalau nanti dipasang, sel AD dan AE yang lama HARUS ditimpa seluruhnya."),
        ("", "   Kalau sebagian masih rumus lama, order sheet jadi campuran dua cara dan"),
        ("", "   itu lebih membingungkan daripada sekarang."),
        ("", "4. Tab yang persen diskonnya TIDAK seragam antar baris perlu diperiksa"),
        ("", "   dulu — satu sel pilihan berlaku untuk seluruh tab."),
        ("", ""),
        ("BAGIAN", "ISI BERKAS CONTOH INI"),
    ]
    for tag, t in blok:
        sel = ws.cell(r, 1, t)
        if tag == "BAGIAN":
            sel.font = Font(bold=True, size=12, color="2F5597")
        else:
            sel.font = Font(size=10)
        r += 1
    for nama, n in rincian:
        ws.cell(r, 1, f"   Tab '{nama}' — {n} baris berisi diskon pilihan").font = Font(size=10)
        r += 1
    ws.sheet_view.showGridLines = False


def _perbandingan(wb) -> None:
    """Angka SEBELUM dan SESUDAH, diukur dari order sheet sungguhan.

    Angka di lembar ini bukan contoh karangan — semuanya sudah diadu dengan
    order sheet Oktober 2026 dan dihitung ulang lewat LibreOffice.
    """
    ws = wb.create_sheet("PERBANDINGAN")
    for c, w in ((1, 30), (2, 32), (3, 20), (4, 20), (5, 16), (6, 46)):
        ws.column_dimensions[L(c)].width = w

    sel = ws.cell(1, 1, "ANGKANYA SEBELUM DAN SESUDAH")
    sel.font = Font(bold=True, size=15)
    ws.cell(2, 1, "Diadu langsung dengan Order Sheet Oktober 2026 (versi 22 Okt 10:13)").font = Font(italic=True, size=10, color="666666")

    r = 4
    for i, nama in enumerate(["TAB", "ANGKA", "ORDER SHEET SEKARANG",
                              "CONTOH INI", "SELISIH", "KETERANGAN"], start=1):
        c = ws.cell(r, i, nama)
        c.font = JUDUL
        c.fill = ISI_JUDUL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = KOTAK
    ws.row_dimensions[r].height = 28

    data = [
        ("PO 14 Okt - Mae Bebe", "Nilai kotor (Z)", 64314900, 64314900, 0,
         "sama persis"),
        ("PO 14 Okt - Mae Bebe", "TOTAL VALUE 25% (AC)", 48236175, 48236175, 0,
         "sama persis"),
        ("PO 14 Okt - Mae Bebe", "DISCOUNT COD + 1,5% (AE)", 47512632.38,
         47512632.38, 0, "sama persis — sampai sen terakhir"),
        ("PO 15 Okt - Caroline", "Nilai kotor (Z)", 24266100, 24266100, 0,
         "sama persis"),
        ("PO 15 Okt - Caroline", "TOTAL VALUE 25% (AC)", 18199575, 18199575, 0,
         "sama persis"),
        ("PO 15 Okt - Caroline", "Nilai bersih yang DIPAKAI invoice",
         17835583.50, 17478871.83, -356711.67,
         "BEDA — lihat penjelasan di bawah"),
    ]
    r += 1
    for tab, ang, a, b, d, ket in data:
        _b = [tab, ang, a, b, d, ket]
        for i, v in enumerate(_b, start=1):
            c = ws.cell(r, i, v)
            c.border = KOTAK
            c.alignment = Alignment(vertical="center", wrap_text=True)
            if i in (3, 4, 5):
                c.number_format = RP
        if d:
            for i in range(1, 7):
                ws.cell(r, i).font = Font(bold=True, color="C00000")
        r += 1

    r += 1
    sel = ws.cell(r, 1, "KENAPA CAROLINE BERBEDA — INI JUSTRU GUNANYA")
    sel.font = Font(bold=True, size=12, color="C00000")
    r += 1
    for t in [
        "Bulan lalu Bapak minta diskon Caroline menjadi 25% + 2% + 2% = Rp17.478.872.",
        "",
        "Di order sheet sekarang potongan ketiga itu ditaruh di KOLOM TERPISAH:",
        "    AD berjudul 'DISCOUNT CBD + 2%'  ->  Rp17.835.584   (25% + 2%)",
        "    AE berjudul 'DISCOUNT 2%'        ->  Rp17.478.872   (25% + 2% + 2%)",
        "",
        "Aturan 2 memilih kolom PALING KIRI yang terisi penuh, yaitu AD. Jadi invoice",
        "yang terbit hari ini memakai Rp17.835.584 — BUKAN angka yang Bapak minta.",
        "Selisihnya Rp356.712, dan pencocokan tetap LULUS sehingga tidak ada",
        "peringatan apa pun.",
        "",
        "Pada contoh ini ketiga tingkat masuk ke SATU kolom AD, dan judulnya ikut",
        "berbunyi 'DISCOUNT CBD + 2% + 2%'. Hasilnya langsung Rp17.478.872 —",
        "angka yang Bapak minta — tanpa perlu kolom tambahan.",
        "",
        "PERLU KEPUTUSAN BAPAK: apakah Caroline memang 25% + 2% + 2%? Kalau ya,",
        "kolom AE di order sheet perlu dikosongkan supaya tidak ada dua angka.",
    ]:
        c = ws.cell(r, 1, t)
        c.font = Font(size=10, bold=t.startswith(("Aturan 2", "PERLU KEPUTUSAN")))
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        r += 1
    ws.sheet_view.showGridLines = False
    # Tanpa ini tabelnya terpotong di kolom 3 dan tiga kolom sisanya pindah
    # ke halaman berikutnya. Ketahuan dari melihat GAMBAR hasil render PDF,
    # bukan dari nilai selnya — pola berulang di CLAUDE.md bagian 19 dst.
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:F{r}"


def main() -> None:
    sumber = AKAR / "data/semua/10_Oktober_2026.xlsx"
    if not sumber.exists():
        sys.exit(f"Order sheet tidak ketemu: {sumber}")
    wb_lama = openpyxl.load_workbook(sumber, data_only=True)

    # Dua tab sengaja dipilih berbeda sifatnya:
    #   Mae Bebe  - satu blok, hanya COD, diskon tunggal
    #   Caroline  - EMPAT blok, CBD dengan potongan tambahan 2% (bagian 48)
    pilih = [("PO 14 Okt - Mae Bebe", 0.0),
             ("PO 15 Okt - Caroline Mom, Baby ", 0.02)]

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    rincian = []
    for nama, tambahan in pilih:
        if nama not in wb_lama.sheetnames:
            sys.exit(f"Tab tidak ketemu: {nama}")
        n = _salin_tab(wb, wb_lama[nama], nama, tambahan)
        rincian.append((nama[:31], n))
    _lembar_daftar(wb)
    _perbandingan(wb)
    _cara_pakai(wb, rincian)

    # Urutan lembar: penjelasan dulu, baru tab PO, daftar paling belakang.
    urut = ["CARA PAKAI", "PERBANDINGAN"] + [n for n, _ in rincian] + [LBR_DAFTAR]
    wb._sheets = [wb[n] for n in urut]

    out = AKAR / "keluaran/CONTOH_PILIHAN_DISKON.xlsx"
    out.parent.mkdir(exist_ok=True)
    wb.save(out)
    print(f"{out}  ({out.stat().st_size} byte)")
    for nama, n in rincian:
        print(f"  {nama}: {n} baris")


if __name__ == "__main__":
    main()
