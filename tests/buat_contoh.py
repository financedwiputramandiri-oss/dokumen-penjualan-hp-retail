"""Buat order sheet CONTOH (data karangan) untuk keperluan tes.

Data asli perusahaan sengaja tidak dipakai di tes supaya tidak ikut masuk git.
Bentuk berkasnya meniru order sheet asli: blok bertumpuk, kolom D..L = ORIGINAL
PO, N..V = AVAILABLE TO ORDER, X = harga, Z = nilai kotor, AC/AD/AE = nett.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

JUDUL_ATAS = {
    1: "ARTICLE \nCODE", 2: "PRODUCT NAME", 3: "COLOUR", 4: "ORIGINAL PO ",
    14: "AVAILABLE TO ORDER (QTY)", 24: "PRICE W/ VAT", 25: "TOTAL ORI PO (VALUE)",
    26: "TOTAL ATO (VALUE)", 27: "LOSSES", 28: "DISC", 29: "TOTAL VALUE ",
    30: "DISCOUNT CBD + 1.5%", 31: "DISCOUNT \nCOD + 1,5%",
}


def _tulis_blok(ws, baris, label_ukuran, baris_data, disc, *, isi_cbd, tarif_cbd=0.015):
    """Tulis satu blok. baris_data = [(kode, nama, warna, [qty per posisi])]."""
    for kolom, teks in JUDUL_ATAS.items():
        ws.cell(baris, kolom, teks)
    for i, lbl in enumerate(label_ukuran):
        if lbl is not None:
            ws.cell(baris + 1, 4 + i, lbl)
            ws.cell(baris + 1, 14 + i, lbl)
    ws.cell(baris + 1, 13, "TOTAL")
    ws.cell(baris + 1, 23, "TOTAL")

    r = baris + 2
    qty_blok = 0
    kotor_blok = 0.0
    ac_blok = 0.0
    ad_blok = 0.0
    for idx, (kode, nama, warna, qty, harga) in enumerate(baris_data):
        ws.cell(r, 1, kode)
        ws.cell(r, 2, nama)
        ws.cell(r, 3, warna)
        for i, q in enumerate(qty):
            if q:
                ws.cell(r, 4 + i, q)
                ws.cell(r, 14 + i, q)
        total_qty = sum(qty)
        kotor = total_qty * harga
        ac = kotor * (1 - disc)
        ws.cell(r, 13, total_qty)
        ws.cell(r, 23, total_qty)
        ws.cell(r, 24, harga)
        ws.cell(r, 25, kotor)
        ws.cell(r, 26, kotor)
        ws.cell(r, 27, 0)
        ws.cell(r, 28, disc)
        ws.cell(r, 29, ac)
        if isi_cbd == "penuh" or (isi_cbd == "sebagian" and idx == 0):
            ad = ac * (1 - tarif_cbd)
            ws.cell(r, 30, ad)
            ad_blok += ad
        qty_blok += total_qty
        kotor_blok += kotor
        ac_blok += ac
        r += 1
    return r, qty_blok, kotor_blok, ac_blok, ad_blok


def buat_contoh(tujuan: Path) -> Path:
    wb = Workbook()

    # --- master harga
    ws = wb.active
    ws.title = "Harga Retail"
    ws.append(["Column 1", "Nama Barang", "Harga Ritel"])
    for kode, nama, harga in [
        ("AA.1", "Contoh Set Small Size", 50000),
        ("AA.2", "Contoh Set Big Size", 60000),
        ("BB.1", "Contoh Dress", 70000),
    ]:
        ws.append([kode, nama, harga])

    # --- PO TOP dengan 2 blok bertumpuk & sistem ukuran berbeda
    ws = wb.create_sheet("PO 05 Januari - Contoh TOP")
    r, q1, g1, ac1, _ = _tulis_blok(
        ws, 1, ["0-3M", "3-6M", "6-12M", None, None, None, None, None, None],
        [("AA.1", "Contoh Set Small Size", "Merah", [2, 3, 0, 0, 0, 0, 0, 0, 0], 50000),
         ("AA.1", "Contoh Set Small Size", "Biru", [1, 1, 1, 0, 0, 0, 0, 0, 0], 50000)],
        disc=0.20, isi_cbd="tidak",
    )
    r += 1
    r, q2, g2, ac2, _ = _tulis_blok(
        ws, r, ["1", "2", "3", None, None, None, None, None, None],
        [("BB.1", "Contoh Dress", "Hijau", [4, 4, 2, 0, 0, 0, 0, 0, 0], 70000)],
        disc=0.20, isi_cbd="sebagian",
    )
    ws.cell(r, 23, q1 + q2)
    ws.cell(r, 26, g1 + g2)
    ws.cell(r, 29, ac1 + ac2)

    # --- PO CBD terisi penuh
    ws = wb.create_sheet("PO 06 Januari - Contoh CBD")
    r, q, g, ac, ad = _tulis_blok(
        ws, 1, ["S", "M", "L", None, None, None, None, None, None],
        [("AA.2", "Contoh Set Big Size", "Merah", [5, 5, 0, 0, 0, 0, 0, 0, 0], 60000),
         ("AA.2", "Contoh Set Big Size", "Biru", [0, 2, 3, 0, 0, 0, 0, 0, 0], 60000)],
        disc=0.22, isi_cbd="penuh",
    )
    ws.cell(r, 23, q)
    ws.cell(r, 26, g)
    ws.cell(r, 29, ac)
    ws.cell(r, 30, ad)

    tujuan.parent.mkdir(parents=True, exist_ok=True)
    wb.save(tujuan)
    return tujuan


if __name__ == "__main__":
    print(buat_contoh(Path(__file__).resolve().parents[1] / "data" / "CONTOH_order_sheet.xlsx"))
