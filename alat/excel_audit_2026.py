"""Satu berkas Excel sederhana: rumus & hitungan yang SALAH di order sheet 2026.

Dibuat 21 Oktober 2026 atas permintaan Yosua "JADIKAN DALAM BENTUK EXCEL",
menggabungkan audit CLAUDE.md bagian 49-52 menjadi SATU berkas.

Sumbernya dua, dan sengaja dua:
  keluaran/AUDIT_TEMUAN.csv   - rumus qty, baris TOTAL, galat Excel
  keluaran/PERSEN_HILANG.csv  - tanda % hilang dari rumus diskon
  keluaran/DAMPAK_PERSEN_HILANG.csv - cara bayar yang dipilih per tab

TIDAK ADA baris JUMLAH di lembar mana pun. Barisnya mengukur hal yang
berbeda dan sebagian bertumpuk, jadi menjumlahkannya menyesatkan.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

AKAR = Path(__file__).resolve().parent.parent
KEL = AKAR / "keluaran"

JUDUL = Font(bold=True, size=11, color="FFFFFF")
ISI_JUDUL = PatternFill("solid", fgColor="2F5597")
MERAH = Font(bold=True, color="C00000")
MERAH_IT = Font(italic=True, color="C00000", size=9)
HIJAU = Font(bold=True, color="006100")
TIPIS = Side(style="thin", color="999999")
KOTAK = Border(left=TIPIS, right=TIPIS, top=TIPIS, bottom=TIPIS)
RP = '_-"Rp"* #,##0_-;\\-"Rp"* #,##0_-;_-"Rp"* "-"_-;_-@_-'


def _judul(ws, kolom: list[tuple[str, int]], baris: int = 1) -> None:
    for i, (nama, lebar) in enumerate(kolom, start=1):
        sel = ws.cell(baris, i, nama)
        sel.font = JUDUL
        sel.fill = ISI_JUDUL
        sel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        sel.border = KOTAK
        ws.column_dimensions[get_column_letter(i)].width = lebar
    ws.row_dimensions[baris].height = 30
    ws.freeze_panes = ws.cell(baris + 1, 1)


def _baris(ws, r: int, nilai: list, rp_kolom: tuple[int, ...] = ()) -> None:
    for i, v in enumerate(nilai, start=1):
        sel = ws.cell(r, i, v)
        sel.border = KOTAK
        sel.alignment = Alignment(vertical="top", wrap_text=True)
        if i in rp_kolom:
            sel.number_format = RP


def _baca(nama: str) -> list[dict]:
    p = KEL / nama
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --------------------------------------------------------------- RUMUS SALAH
def lembar_rumus_salah(wb: Workbook) -> int:
    ws = wb.create_sheet("RUMUS SALAH")
    _judul(ws, [
        ("NO", 5), ("ORDER SHEET", 22), ("TAB", 30), ("SEL", 16),
        ("JENIS KESALAHAN", 26), ("RUMUS YANG SALAH", 24),
        ("SEHARUSNYA", 24), ("SELISIH pcs", 11), ("SELISIH Rp", 16),
        ("AKIBATNYA SEKARANG", 40),
    ])
    data = [
        ("Februari 2026", "DHAWAFEST BAZAAR - MARET 2026",
         "W20:W23, W32:W35,\nW44:W47, W56:W59\n(16 sel)",
         "Rumus qty berhenti terlalu awal", "=SUM(N20:S20)", "=SUM(N20:V20)",
         31, 5455000,
         "Qty di kolom T, U, V tidak pernah ikut terhitung."),
        ("Februari 2026", "DHAWAFEST BAZAAR - MARET 2026", "W160",
         "Baris TOTAL tidak lengkap", "=sum(W24:W71,W72:W79)", "=SUM(W4:W157)",
         246, 33450600,
         "43 baris data (baris 4-119) di luar rentang, tidak ikut dijumlah."),
        ("Agustus 2026 Harga Lama", "PO 07 Agustus - Katamama Tapos", "W116",
         "Baris TOTAL tidak lengkap", "=SUM(W3:W108,W114:W115)", "=SUM(W3:W115)",
         4, 820000,
         "Baris 113 terlewat. Sudah dilaporkan 20 Okt, BELUM dibetulkan."),
        ("Maret 2026", "PO 04 Maret - Katamama Cikaret", "AB3:AB59 vs AC3:AC59",
         "Kolom DISC beda dari rumus", "DISC tertulis 25%", "rumus memakai 22%",
         None, 284815,
         "Kolom DISC dan persen di dalam rumus tidak saling menunjuk. "
         "Yang menghitung uang adalah yang di rumus (22%). "
         "PERLU DIPASTIKAN YOSUA: 25% atau 22%?"),
        ("September 2026", "PO 11 September - Katamama (Tapos)", "AD3:AD8",
         "TANDA % HILANG", "=AC3-(AC3*1.5)", "=AC3-(AC3*1.5%)",
         None, 999034,
         "PALING MAHAL. Tanpa % Excel menghitung AC x (-0,5), jadi NEGATIF. "
         "Invoice KURANG MENAGIH Rp999.034 dan pencocokan tetap LULUS."),
    ]
    r = 2
    for i, d in enumerate(data, start=1):
        _baris(ws, r, [i, *d], rp_kolom=(9,))
        if "TANDA %" in d[3]:
            for c in range(1, 11):
                ws.cell(r, c).font = MERAH
        ws.row_dimensions[r].height = 58
        r += 1

    r += 1
    sel = ws.cell(r, 1,
                  "CATATAN: angka SELISIH Rp di tiap baris mengukur hal yang "
                  "BERBEDA dan sebagian bertumpuk, jadi SENGAJA TIDAK DIJUMLAHKAN. "
                  "Baris 1-3 adalah qty yang hilang dari order sheet; baris 4-5 "
                  "adalah selisih tagihan pada invoice yang sudah terbit.")
    sel.font = MERAH_IT
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=10)
    sel.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 42
    return len(data)


# --------------------------------------------------------- TANDA % HILANG
def lembar_persen(wb: Workbook) -> int:
    ws = wb.create_sheet("TANDA % HILANG")
    sel = ws.cell(1, 1,
                  "Rumus diskon CBD/COD ditulis TANPA tanda %, contoh "
                  "=AC3-(AC3*1.5) yang seharusnya =AC3-(AC3*1.5%). "
                  "Tanpa %, Excel menghitung AC x (1 - 1,5) = AC x (-0,5), "
                  "jadi nilai bersihnya NEGATIF.")
    sel.font = MERAH
    ws.merge_cells("A1:H1")
    sel.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 46

    _judul(ws, [
        ("NO", 5), ("ORDER SHEET", 20), ("TAB", 32), ("KOLOM", 22),
        ("SEL BERUMUS SALAH", 11), ("HASILNYA NEGATIF", 11),
        ("CONTOH RUMUS", 22), ("DIPAKAI DOKUMEN?", 42),
    ], baris=3)

    dampak = {(d["ORDER SHEET"], d["TAB"]): d for d in _baca("DAMPAK_PERSEN_HILANG.csv")}
    r = 4
    n = 0
    for i, d in enumerate(_baca("PERSEN_HILANG.csv"), start=1):
        k = (d["ORDER SHEET"], d["TAB"])
        dm = dampak.get(k, {})
        cara = dm.get("CARA BAYAR DIPILIH", "?")
        if cara == "TOP":
            akibat = ("TIDAK — Aturan 2 memilih TOP karena kolomnya terisi "
                      "sebagian. Dokumennya BENAR, tapi hanya karena kebetulan: "
                      "begitu Sales menarik kolom ini sampai penuh, fakturnya "
                      "langsung salah besar.")
        else:
            akibat = ("YA — kolom ini yang dipakai menghitung invoice. "
                      "DOKUMENNYA SALAH.")
        _baris(ws, r, [i, d["ORDER SHEET"].replace("_", " "), d["TAB"],
                       d["KOLOM"], int(d["JUMLAH SEL"]), int(d["HASIL NEGATIF"]),
                       d["RUMUS"], akibat])
        if cara != "TOP":
            for c in range(1, 9):
                ws.cell(r, c).font = MERAH
        ws.row_dimensions[r].height = 50
        r += 1
        n = i
    return n


# ------------------------------------------------------- GALAT #REF! DI AD/AE
def lembar_ref(wb: Workbook) -> int:
    ws = wb.create_sheet("REF DI BARIS TOTAL")
    sel = ws.cell(1, 1,
                  "#REF! di kolom DISCOUNT CBD/COD. SELURUHNYA berada di baris "
                  "TOTAL / baris ringkasan (baris yang tidak punya ARTICLE CODE), "
                  "sudah diperiksa satu per satu. Nilai bersih dibaca PER BARIS "
                  "(Aturan 2), jadi ini TIDAK membuat satu dokumen pun salah — "
                  "tapi membuat Yosua tidak bisa membaca total CBD/COD langsung "
                  "dari sheet, dan itu sumber kebingungan berulang.")
    sel.font = Font(italic=True, color="7F6000")
    ws.merge_cells("A1:D1")
    sel.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 62

    _judul(ws, [("NO", 5), ("ORDER SHEET", 24), ("TAB", 34),
                ("JUMLAH SEL #REF!", 16)], baris=3)
    hit: dict[tuple[str, str], int] = {}
    for d in _baca("AUDIT_TEMUAN.csv"):
        if d["TINGKAT"] != "GENTING" or d["JENIS"] != "GALAT EXCEL":
            continue
        if not re.match(r"^A[DE]\d+$", d["SEL"] or ""):
            continue
        k = (d["ORDER SHEET"].replace("_", " "), d["TAB"])
        hit[k] = hit.get(k, 0) + 1
    r = 4
    for i, ((o, t), c) in enumerate(sorted(hit.items(), key=lambda x: -x[1]), start=1):
        _baris(ws, r, [i, o, t, c])
        r += 1
    return len(hit)


# ----------------------------------------------------------------- BERSIH
def lembar_bersih(wb: Workbook) -> None:
    ws = wb.create_sheet("SUDAH DIPERIKSA BERSIH")
    _judul(ws, [("NO", 5), ("YANG DIPERIKSA", 54), ("HASIL", 26)])
    data = [
        ("Harga memakai VLOOKUP ke tab Harga Retail", "11.045 dari 11.045 baris"),
        ("Harga diketik tangan di baris PO", "0 baris"),
        ("Kode artikel tidak ada di tab Harga Retail", "0 kode"),
        ("Harga baris PO beda dari tab Harga Retail", "0 baris"),
        ("qty x harga = nilai kotor (kolom Z)", "0 selisih"),
        ("Rumus menunjuk baris LAIN (meleset satu baris)", "0 rumus"),
        ("Rumus CBD/COD menunjuk kolom sumber yang salah", "0 rumus"),
        ("Nilai bersih cocok dengan persen di dalam rumusnya", "0 selisih"),
    ]
    for i, (a, b) in enumerate(data, start=1):
        _baris(ws, i + 1, [i, a, b])
        ws.cell(i + 1, 3).font = HIJAU
        ws.cell(i + 1, 3).alignment = Alignment(horizontal="center")


# --------------------------------------------------------------- RINGKASAN
def lembar_ringkasan(wb: Workbook, n_rumus: int, n_persen: int, n_ref: int) -> None:
    ws = wb.create_sheet("RINGKASAN", 0)
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 34
    ws.column_dimensions["C"].width = 56

    sel = ws.cell(1, 1, "AUDIT ORDER SHEET HAPPY PUMPKIN 2026")
    sel.font = Font(bold=True, size=16)
    ws.merge_cells("A1:C1")
    ws.cell(2, 1, "Rumus dan hitungan yang salah — harga, diskon, CBD, COD").font = Font(italic=True, size=10)
    ws.merge_cells("A2:C2")
    ws.cell(3, 1, "Diperiksa 21 Oktober 2026 · 11 order sheet (Januari - Oktober) · 243 tab · 11.045 baris data").font = Font(size=9, color="666666")
    ws.merge_cells("A3:C3")

    r = 5
    _judul(ws, [("TEMUAN", 52), ("JUMLAH", 34), ("HARUS DIKERJAKAN SIAPA", 56)], baris=r)
    isi = [
        ("Rumus / hitungan SALAH yang perlu dibetulkan", f"{n_rumus} temuan di 4 tab", "SALES — betulkan di order sheet"),
        ("  di antaranya: tanda % hilang dari rumus diskon", f"{n_persen} tab, 249 sel", "SALES — ganti *1.5 jadi *1.5%"),
        ("  invoice yang sudah terbit dan KURANG MENAGIH", "1 — Katamama Tapos 11 Sep", "YOSUA — terbitkan ulang sesudah dibetulkan"),
        ("  perlu keputusan Yosua dulu", "1 — Katamama Cikaret Maret", "YOSUA — 25% atau 22%?"),
        ("#REF! di baris TOTAL kolom CBD/COD", f"{n_ref} tab", "SALES — rapikan, tidak mendesak"),
        ("Rumus qty tidak menjangkau kolom ukuran ke-9", "±10.770 baris", "BELUM berdampak (kolom V masih kosong)"),
        ("Pemeriksaan yang hasilnya BERSIH", "8 jenis", "tidak ada"),
    ]
    r += 1
    for a, b, c in isi:
        _baris(ws, r, [a, b, c])
        if "KURANG MENAGIH" in a or "tanda %" in a:
            for k in range(1, 4):
                ws.cell(r, k).font = MERAH
        r += 1

    r += 1
    sel = ws.cell(r, 1, "YANG PALING MENDESAK")
    sel.font = Font(bold=True, size=12, color="C00000")
    r += 1
    for t in [
        "1. PO 11 September - Katamama (Tapos), sel AD3 sampai AD8:",
        "   ganti  =AC3-(AC3*1.5)  menjadi  =AC3-(AC3*1.5%)",
        "   Sesudah itu invoice PO ini HARUS diterbitkan ulang — sekarang kurang menagih Rp999.034.",
        "",
        "2. Lima belas tab April 2026 punya rumus yang sama salahnya, tapi dokumennya masih benar",
        "   karena kolomnya terisi sebagian. JANGAN menarik kolom itu sampai penuh sebelum rumusnya",
        "   dibetulkan — kalau ditarik dulu, 15 faktur sekaligus jadi salah besar.",
        "",
        "3. Kolom DISC Katamama Cikaret Maret tertulis 25% tapi rumusnya memakai 22%.",
        "   Perlu dipastikan Yosua mana yang benar; selisihnya Rp284.815.",
    ]:
        ws.cell(r, 1, t).font = Font(size=10, bold=t.startswith(("1.", "2.", "3.")))
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
        r += 1


def main() -> None:
    wb = Workbook()
    wb.remove(wb.active)
    n_rumus = lembar_rumus_salah(wb)
    n_persen = lembar_persen(wb)
    n_ref = lembar_ref(wb)
    lembar_bersih(wb)
    lembar_ringkasan(wb, n_rumus, n_persen, n_ref)
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
    out = KEL / "AUDIT_ORDER_SHEET_2026.xlsx"
    wb.save(out)
    print(f"{out}  ({out.stat().st_size} byte, {len(wb.worksheets)} lembar)")


if __name__ == "__main__":
    main()
