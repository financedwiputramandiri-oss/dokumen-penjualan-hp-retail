"""Surat Jalan dan Packing List.

Aturan 3: satu tabel TERPISAH untuk tiap blok (kategori produk), lengkap dengan
baris judul ukurannya sendiri, nomor urut mulai dari 1 lagi, dan baris TOTAL
per tabel. Di bawah semua tabel ada TOTAL SELURUH PO.

Packing List = Surat Jalan + kolom JUMLAH DIKIRIM dan NO. KOLI yang diisi
gudang. Berat dan dimensi tidak ada di order sheet dan tidak boleh ditebak.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

from ..model import Order
from . import gaya

KOLOM_TETAP = ["No.", "ARTICLE CODE", "PRODUCT NAME", "COLOUR"]


def _tulis_tabel_blok(
    ws: Worksheet,
    baris: int,
    blok,
    *,
    dengan_kolom_gudang: bool,
    sembunyikan_ukuran_kosong: bool = True,
) -> tuple[int, int]:
    """Tulis satu tabel untuk satu blok. Kembalikan (baris_berikutnya, kolom_terakhir)."""
    posisi = blok.kolom_terpakai() if sembunyikan_ukuran_kosong else list(range(9))
    if not posisi:
        posisi = list(range(9))
    label = [blok.label_ukuran[i] or f"Uk.{i + 1}" for i in posisi]

    judul = KOLOM_TETAP + label + ["TOTAL"]
    if dengan_kolom_gudang:
        judul += ["JUMLAH DIKIRIM", "NO. KOLI"]
    kolom_terakhir = len(judul)

    gaya.baris_judul_tabel(ws, baris, judul)
    r = baris + 1

    for no, b in enumerate(blok.baris, start=1):
        ws.cell(r, 1, no).alignment = Alignment(horizontal="center")
        ws.cell(r, 2, b.kode)
        ws.cell(r, 3, b.nama)
        ws.cell(r, 4, b.warna)
        for k, i in enumerate(posisi):
            q = b.qty_per_ukuran[i]
            sel = ws.cell(r, 5 + k, q if q else None)
            sel.alignment = Alignment(horizontal="center")
            sel.number_format = gaya.ANGKA
        sel_total = ws.cell(r, 5 + len(posisi), b.qty)
        sel_total.alignment = Alignment(horizontal="center")
        sel_total.font = Font(name=gaya.FONT, size=9, bold=True)
        for c in range(1, kolom_terakhir + 1):
            if ws.cell(r, c).font.size != 9:
                ws.cell(r, c).font = Font(name=gaya.FONT, size=9)
        r += 1

    # baris TOTAL tabel ini
    sel = ws.cell(r, 1, "TOTAL")
    sel.font = Font(name=gaya.FONT, size=9, bold=True)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    sel.alignment = Alignment(horizontal="right")
    for k, i in enumerate(posisi):
        jml = sum(b.qty_per_ukuran[i] for b in blok.baris)
        c = ws.cell(r, 5 + k, jml if jml else None)
        c.font = Font(name=gaya.FONT, size=9, bold=True)
        c.alignment = Alignment(horizontal="center")
    c = ws.cell(r, 5 + len(posisi), blok.qty)
    c.font = Font(name=gaya.FONT, size=9, bold=True)
    c.alignment = Alignment(horizontal="center")

    gaya.beri_garis(ws, baris, 1, r, kolom_terakhir)
    return r + 2, kolom_terakhir


def _bangun(
    ws: Worksheet,
    order: Order,
    customer,
    perusahaan,
    *,
    dengan_kolom_gudang: bool,
    nama_dokumen: str,
    nomor: str,
    tanggal_dokumen: Optional[date],
) -> None:
    # perkirakan kolom terlebar dulu supaya kop bisa ditempatkan rapi
    maks = 0
    for blok in order.blok:
        n = len(KOLOM_TETAP) + max(1, len(blok.kolom_terpakai())) + 1 + (2 if dengan_kolom_gudang else 0)
        maks = max(maks, n)

    r = gaya.tulis_kop(
        ws,
        perusahaan,
        kolom_terakhir=maks,
        nama_customer=customer.nama_di_dokumen if customer else "",
        alamat_customer=customer.alamat if customer else "",
        tanggal_dokumen=tanggal_dokumen,
    )

    gaya.judul(ws, r, 1, nama_dokumen, ukuran=14)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=maks)
    r += 1
    sub = ws.cell(r, 1, f"No. {nomor}    |    PO: {order.nama_tab}")
    sub.font = Font(name=gaya.FONT, size=9)
    sub.alignment = Alignment(horizontal="center")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=maks)
    r += 2

    kolom_terakhir = maks
    for blok in order.blok:
        if len(order.blok) > 1:
            k = ws.cell(r, 1, f"Kategori {blok.nomor} dari {len(order.blok)}")
            k.font = Font(name=gaya.FONT, size=9, bold=True, italic=True)
            r += 1
        r, kt = _tulis_tabel_blok(ws, r, blok, dengan_kolom_gudang=dengan_kolom_gudang)
        kolom_terakhir = max(kolom_terakhir, kt)

    # TOTAL SELURUH PO — label dibentang sampai satu kolom sebelum terakhir
    sel = ws.cell(r, 1, "TOTAL SELURUH PO")
    sel.font = Font(name=gaya.FONT, size=10, bold=True)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=max(2, kolom_terakhir - 1))
    sel.alignment = Alignment(horizontal="right")
    t = ws.cell(r, kolom_terakhir, f"{order.qty} PCS")
    t.font = Font(name=gaya.FONT, size=10, bold=True)
    t.alignment = Alignment(horizontal="center")
    gaya.beri_garis(ws, r, 1, r, kolom_terakhir)
    r += 2

    if dengan_kolom_gudang:
        cat = ws.cell(
            r, 1,
            "Catatan: kolom JUMLAH DIKIRIM dan NO. KOLI diisi gudang saat barang dikemas. "
            "Berat dan dimensi tidak tersedia di order sheet.",
        )
        cat.font = Font(name=gaya.FONT, size=8, italic=True)
        r += 2

    r += 1
    gaya.blok_tanda_tangan(
        ws, r,
        kolom=[1, max(4, kolom_terakhir // 2), max(6, kolom_terakhir - 1)],
        label=["Pengirim :", "Penerima :", "Mengetahui :"],
    )

    lebar = {1: 5, 2: 16, 3: 34, 4: 18}
    for c in range(5, kolom_terakhir + 1):
        lebar[c] = 9
    if dengan_kolom_gudang:
        lebar[kolom_terakhir - 1] = 13
        lebar[kolom_terakhir] = 11
    gaya.atur_lebar(ws, lebar)
    gaya.siapkan_cetak(ws, kolom_terakhir, landscape=True)


def buat_surat_jalan(ws, order, customer, perusahaan, nomor: str, tanggal_dokumen=None) -> None:
    _bangun(
        ws, order, customer, perusahaan,
        dengan_kolom_gudang=False,
        nama_dokumen="SURAT JALAN",
        nomor=nomor,
        tanggal_dokumen=tanggal_dokumen or order.tanggal_po,
    )


def buat_packing_list(ws, order, customer, perusahaan, nomor: str, tanggal_dokumen=None) -> None:
    _bangun(
        ws, order, customer, perusahaan,
        dengan_kolom_gudang=True,
        nama_dokumen="PACKING LIST",
        nomor=nomor,
        tanggal_dokumen=tanggal_dokumen or order.tanggal_po,
    )
