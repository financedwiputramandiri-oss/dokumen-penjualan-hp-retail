"""Daftar SEDERHANA rumus & perhitungan yang salah di order sheet 2026.

Permintaan Yosua 20 Oktober 2026: *"buat excel nya secara sederhana yang
memuat tentang apa saja rumus yang salah dan perhitungan yang salah dan
selisih dengan nilai aslinya"*.

Sengaja SATU lembar utama, satu baris per masalah, dengan kolom yang sudah
terjawab sendiri: salahnya apa, seharusnya apa, selisihnya berapa. Angkanya
dihitung langsung dari order sheet (lihat alat/audit_harga_diskon.py dan
alat/audit_rumus.py), bukan diketik tangan.
"""
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

TEBAL = Font(bold=True)
JUDUL = Font(bold=True, color="FFFFFF", size=11)
BG = PatternFill("solid", fgColor="C00000")
MERAH = PatternFill("solid", fgColor="FCE4D6")
KUNING = PatternFill("solid", fgColor="FFF2CC")
tipis = Side(style="thin", color="999999")
KOTAK = Border(left=tipis, right=tipis, top=tipis, bottom=tipis)
RP = '_-"Rp"* #,##0_-;\\-"Rp"* #,##0_-;_-"Rp"* "-"_-;_-@_-'

# Satu baris per masalah. Angka selisih dihitung dari order sheet, bukan
# ditebak — rinciannya di CLAUDE.md bagian 49 dan 51.
MASALAH = [
    dict(
        sheet="Februari 2026", tab="DHAWAFEST BAZAAR - MARET 2026", sel="W4:W157",
        jenis="RUMUS QTY",
        salah="=SUM(N4:S4)  — berhenti di kolom S",
        benar="=SUM(N4:V4)",
        akibat="Qty di kolom T, U, V tidak ikut terhitung",
        pcs=76, rp=9609400,
    ),
    dict(
        sheet="Februari 2026", tab="DHAWAFEST BAZAAR - MARET 2026", sel="W160",
        jenis="BARIS TOTAL",
        salah="=sum(W24:W71,W72:W79)  — hanya baris 24-79",
        benar="=SUM(W4:W157)",
        akibat="TOTAL tertulis 307 pcs, isinya 553 pcs",
        pcs=246, rp=33450600,
    ),
    dict(
        sheet="Februari 2026", tab="PO 5 Feb - Defara Baby", sel="W33, W34, W39, W40",
        jenis="RUMUS QTY",
        salah="=SUM(N33:S33)  — berhenti di kolom S",
        benar="=SUM(N33:V33)",
        akibat="4 pcs di kolom T tidak ikut terhitung",
        pcs=4, rp=242600,
    ),
    dict(
        sheet="Maret 2026", tab="PO 04 Maret - Katamama Cikaret", sel="AB3:AB59 vs AC",
        jenis="DISKON",
        salah="Kolom DISC tertulis 25%, rumus AC memakai 22%",
        benar="Pastikan satu: 25% atau 22%",
        akibat="Kalau 25% yang benar, dokumen KURANG menagih",
        pcs=0, rp=284815,
    ),
    dict(
        sheet="Agustus 2026 (Harga Lama)", tab="PO 07 Agustus - Katamama Tapos",
        sel="W116", jenis="BARIS TOTAL",
        salah="=SUM(W3:W108,W114:W115)  — baris 113 terlewat",
        benar="=SUM(W3:W115)",
        akibat="TOTAL tertulis 385 pcs, isinya 389 pcs",
        pcs=4, rp=820000,
    ),
]

BELUM_BERDAMPAK = [
    ("RUMUS QTY", "264 tab",
     "Rumus qty berhenti sebelum kolom ukuran TERAKHIR "
     "(Jan-Jun pakai =SUM(N:S), Jul-Okt pakai =SUM(N:U))",
     "Belum berdampak karena kolom sisanya masih KOSONG. Tapi qty akan "
     "HILANG DIAM-DIAM begitu Sales mengisinya — sudah pernah terjadi pada "
     "Buchi Kids September: 12 pcs, Rp890.400"),
    ("#REF!", "266 tab",
     "Baris TOTAL kolom AD/AE (CBD/COD) berisi #REF!",
     "Dokumen TETAP BENAR — nilai bersih dibaca per baris, bukan dari baris "
     "TOTAL. Tapi total CBD/COD tidak bisa dibaca langsung dari order sheet"),
]


def main():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RUMUS SALAH"

    ws["A1"] = "RUMUS & PERHITUNGAN YANG SALAH DI ORDER SHEET 2026"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = ("Diperiksa 20 Oktober 2026 — 12 order sheet, 264 tab, "
                "12.374 baris. Yang di bawah ini SUDAH salah angkanya.")
    ws["A3"] = "Yang harus dibetulkan ada DI ORDER SHEET, bukan di program."
    ws["A3"].font = Font(italic=True)

    judul = ["NO", "ORDER SHEET", "TAB", "SEL", "JENIS",
             "RUMUS / ISI YANG SALAH", "SEHARUSNYA",
             "SELISIH (pcs)", "SELISIH (Rp)", "AKIBATNYA"]
    ws.append([])
    ws.append(judul)
    br = ws.max_row
    for c in range(1, len(judul) + 1):
        s = ws.cell(br, c)
        s.font, s.fill, s.border = JUDUL, BG, KOTAK
        s.alignment = Alignment(horizontal="center", vertical="center",
                                wrap_text=True)
    ws.row_dimensions[br].height = 30

    for i, m in enumerate(MASALAH, start=1):
        ws.append([i, m["sheet"], m["tab"], m["sel"], m["jenis"],
                   m["salah"], m["benar"],
                   m["pcs"] or None, m["rp"], m["akibat"]])
        r = ws.max_row
        for c in range(1, len(judul) + 1):
            sel = ws.cell(r, c)
            sel.border = KOTAK
            sel.alignment = Alignment(vertical="center", wrap_text=True)
            if c in (6, 7):
                sel.font = Font(name="Consolas", size=10)
        ws.cell(r, 9).number_format = RP
        ws.cell(r, 5).fill = MERAH
        ws.cell(r, 9).font = TEBAL
        ws.row_dimensions[r].height = 32

    # SENGAJA TIDAK ADA BARIS JUMLAH.
    #
    # Kolom selisih TIDAK boleh dijumlahkan: tiap baris mengukur hal yang
    # berbeda, dan sebagian saling tumpang tindih. Pada DHAWAFEST, selisih
    # baris TOTAL (Rp33,4 jt) sebagian sudah memuat akibat rumus qty yang
    # pendek, dan selisih diskon Katamama (Rp284.815) sama sekali bukan
    # jenis yang sama. Satu angka gabungan akan dibaca sebagai "kerugian
    # Rp44 juta" — padahal itu tidak benar.
    ws.append([])
    r = ws.max_row + 1
    ws.cell(r, 1, "CATATAN: kolom SELISIH jangan dijumlahkan. Tiap baris "
                  "mengukur hal yang berbeda dan sebagian saling tumpang "
                  "tindih (selisih baris TOTAL DHAWAFEST sudah memuat "
                  "sebagian akibat rumus qty-nya).")
    ws.cell(r, 1).font = Font(italic=True, bold=True, color="C00000")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=10)
    ws.cell(r, 1).alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[r].height = 30

    for kol, w in zip("ABCDEFGHIJ", (5, 22, 32, 20, 12, 40, 22, 13, 16, 44)):
        ws.column_dimensions[kol].width = w
    ws.freeze_panes = f"A{br + 1}"

    # ---- lembar kedua: yang BELUM berdampak, sengaja pendek ----
    w2 = wb.create_sheet("BELUM BERDAMPAK")
    w2["A1"] = "BELUM BERDAMPAK — perlu dirapikan Sales, tapi angkanya masih benar"
    w2["A1"].font = Font(bold=True, size=13)
    w2.append([])
    w2.append(["JENIS", "JUMLAH TAB", "ISI MASALAHNYA", "KENAPA BELUM BERDAMPAK"])
    for c in range(1, 5):
        s = w2.cell(3, c)
        s.font, s.fill, s.border = JUDUL, BG, KOTAK
        s.alignment = Alignment(horizontal="center", vertical="center")
    for b in BELUM_BERDAMPAK:
        w2.append(list(b))
        r = w2.max_row
        for c in range(1, 5):
            w2.cell(r, c).border = KOTAK
            w2.cell(r, c).alignment = Alignment(vertical="top", wrap_text=True)
        w2.cell(r, 1).fill = KUNING
        w2.row_dimensions[r].height = 60
    for kol, w in zip("ABCD", (14, 13, 52, 60)):
        w2.column_dimensions[kol].width = w

    Path("keluaran").mkdir(exist_ok=True)
    out = "keluaran/RUMUS_SALAH_ORDER_SHEET_2026.xlsx"
    wb.save(out)
    print("tersimpan:", out)
    print("masalah GENTING:", len(MASALAH))


if __name__ == "__main__":
    main()
