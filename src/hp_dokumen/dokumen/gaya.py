"""Tampilan dokumen: kop surat, garis tabel, format angka, pengaturan cetak.

Semua dokumen memakai kop yang sama supaya seragam.
Warna sengaja tidak dipakai — semua tabel putih, sesuai permintaan Yosua.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

FONT = "Calibri"
RUPIAH = '"Rp"#,##0'
RUPIAH_DESIMAL = '"Rp"#,##0.00'
ANGKA = "#,##0"

_tipis = Side(style="thin", color="000000")
GARIS = Border(left=_tipis, right=_tipis, top=_tipis, bottom=_tipis)

BULAN_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def tanggal_indonesia(t: Optional[date]) -> str:
    if t is None:
        return ""
    return f"{t.day} {BULAN_ID[t.month]} {t.year}"


def rupiah_teks(x: float) -> str:
    return f"Rp{x:,.0f}".replace(",", ".")


def judul(ws: Worksheet, baris: int, kolom: int, teks: str, ukuran: int = 14) -> None:
    sel = ws.cell(baris, kolom, teks)
    sel.font = Font(name=FONT, size=ukuran, bold=True)
    sel.alignment = Alignment(horizontal="center", vertical="center")


def _tulis(ws, r, c, teks, *, bold=False, size=10, align="left", wrap=False):
    sel = ws.cell(r, c, teks)
    sel.font = Font(name=FONT, size=size, bold=bold)
    sel.alignment = Alignment(horizontal=align, vertical="top", wrap_text=wrap)
    return sel


def tulis_kop(
    ws: Worksheet,
    perusahaan,
    *,
    kolom_terakhir: int,
    nama_customer: str,
    alamat_customer: str,
    tanggal_dokumen: Optional[date],
    baris_mulai: int = 1,
) -> int:
    """Tulis kop surat. Mengembalikan nomor baris kosong pertama sesudah kop."""
    r = baris_mulai
    kiri = 1
    # kolom kanan: mundur 3 kolom dari kolom terakhir supaya alamat muat
    kanan = max(kiri + 1, kolom_terakhir - 2)

    logo = perusahaan.berkas_logo()
    baris_logo = 0
    if logo:
        try:
            from openpyxl.drawing.image import Image as XlImage

            img = XlImage(str(logo))
            # tinggi tetap 70 px, lebar ikut proporsi
            if img.height:
                rasio = img.width / img.height
                img.height = 70
                img.width = int(70 * rasio)
            ws.add_image(img, f"A{r}")
            baris_logo = 4
        except Exception:  # logo rusak tidak boleh menggagalkan dokumen
            baris_logo = 0

    kolom_teks = 2 if baris_logo else 1
    _tulis(ws, r, kolom_teks, perusahaan.nama, bold=True, size=12)
    for i, baris_alamat in enumerate(perusahaan.alamat_baris, start=1):
        _tulis(ws, r + i, kolom_teks, baris_alamat, size=9)
    tinggi_kiri = 1 + len(perusahaan.alamat_baris)

    # blok kanan
    _tulis(
        ws, r, kanan,
        f"{perusahaan.kota_penerbitan}, {tanggal_indonesia(tanggal_dokumen)}",
        size=10,
    )
    _tulis(ws, r + 2, kanan, "Kepada Yth.", size=10)
    _tulis(ws, r + 3, kanan, nama_customer or "(nama customer belum diisi)", bold=True, size=10)
    if alamat_customer:
        _tulis(ws, r + 4, kanan, alamat_customer, size=9, wrap=True)
        ws.row_dimensions[r + 4].height = 42
        tinggi_kanan = 5
    else:
        _tulis(ws, r + 4, kanan, "(alamat belum diisi)", size=9)
        tinggi_kanan = 5

    return r + max(tinggi_kiri, tinggi_kanan, baris_logo) + 1


def baris_judul_tabel(ws: Worksheet, baris: int, kolom_judul: list[str], kolom_mulai: int = 1) -> None:
    for i, teks in enumerate(kolom_judul):
        sel = ws.cell(baris, kolom_mulai + i, teks)
        sel.font = Font(name=FONT, size=9, bold=True)
        sel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        sel.border = GARIS
    ws.row_dimensions[baris].height = 28


def beri_garis(ws: Worksheet, r1: int, c1: int, r2: int, c2: int) -> None:
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            ws.cell(r, c).border = GARIS


def atur_lebar(ws: Worksheet, lebar: dict[int, float]) -> None:
    for kolom, w in lebar.items():
        ws.column_dimensions[get_column_letter(kolom)].width = w


def siapkan_cetak(ws: Worksheet, kolom_terakhir: int, *, landscape: bool = False) -> None:
    from openpyxl.worksheet.properties import PageSetupProperties

    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.print_options.horizontalCentered = False
    ws.page_margins.left = 0.4
    ws.page_margins.right = 0.4
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5
    ws.print_area = f"A1:{get_column_letter(kolom_terakhir)}{max(ws.max_row, 1)}"


def blok_tanda_tangan(ws: Worksheet, baris: int, kolom: list[int], label: list[str]) -> int:
    for c, teks in zip(kolom, label):
        _tulis(ws, baris, c, teks, size=10)
        _tulis(ws, baris + 4, c, "(................................)", size=9)
    return baris + 5
