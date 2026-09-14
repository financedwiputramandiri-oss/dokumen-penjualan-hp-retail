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


def kotak(ws: Worksheet, r1: int, c1: int, r2: int, c2: int,
          tebal: str = "medium") -> None:
    """Beri garis kotak MENGELILINGI satu blok, tanpa garis di dalamnya.

    Dipakai untuk blok rekening dan blok penutup invoice, supaya keduanya
    terbaca sebagai satu kotak seperti di faktur asli DPM — bukan kisi-kisi
    per sel. Garis dalam sel yang sudah ada dipertahankan.
    """
    sisi = Side(style=tebal, color="000000")
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            g = ws.cell(r, c).border
            ws.cell(r, c).border = Border(
                left=sisi if c == c1 else g.left,
                right=sisi if c == c2 else g.right,
                top=sisi if r == r1 else g.top,
                bottom=sisi if r == r2 else g.bottom,
            )


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
    # Margin diambil dari faktur asli DPM (0010726 BABY WISE dan
    # 0310726 MAE BEBE). Margin bawaan Excel 0,7 inci membuat tabel
    # terdorong ke halaman kedua saat dicetak di A4.
    ws.page_margins.left = 0.15
    ws.page_margins.right = 0.15
    ws.page_margins.top = 0.2
    ws.page_margins.bottom = 0.25
    ws.print_area = f"A1:{get_column_letter(kolom_terakhir)}{max(ws.max_row, 1)}"


def blok_tanda_tangan(ws: Worksheet, baris: int, kolom: list[int], label: list[str]) -> int:
    for c, teks in zip(kolom, label):
        _tulis(ws, baris, c, teks, size=10)
        _tulis(ws, baris + 4, c, "(................................)", size=9)
    return baris + 5


def pecah_alamat(alamat: str, maksimal: int = 4) -> list[str]:
    """Pecah alamat satu baris jadi beberapa baris pendek seperti faktur asli.

    Faktur DPM menulis alamat customer 3-4 baris, dipotong di koma. Kalau
    dijejalkan satu baris panjang, kopnya tidak seperti aslinya.
    """
    if not alamat or not alamat.strip():
        return []
    bagian = [x.strip() for x in alamat.split(",") if x.strip()]
    if len(bagian) <= maksimal:
        return bagian
    # gabungkan kelebihannya ke baris terakhir supaya tidak ada yang hilang
    kepala = bagian[: maksimal - 1]
    return kepala + [", ".join(bagian[maksimal - 1:])]


def kop_dpm(
    ws: Worksheet,
    perusahaan,
    *,
    nama_customer: str,
    alamat_customer: str,
    tanggal_dokumen: Optional[date],
    baris_mulai: int,
    kolom_kanan: int,
) -> None:
    """Kop surat persis seperti faktur asli CV Dwi Putra Mandiri.

    Susunannya diambil dari berkas asli di Drive (0250726 KATAMAMA TAPOS,
    0010726 BABY WISE): ruang logo di kolom A-B yang digabung, teks perusahaan
    di kolom C, lalu tanggal dan "Kepada Yth." di kolom kanan.

    JANGAN diubah tanpa memeriksa ulang berkas aslinya. Divisi mengenali
    fakturnya dari bentuk ini.
    """
    r = baris_mulai

    # ---- ruang logo: A..B digabung setinggi blok teks -------------------
    ws.merge_cells(start_row=r, start_column=1, end_row=r + 4, end_column=2)
    logo = perusahaan.berkas_logo()
    if logo:
        try:
            from openpyxl.drawing.image import Image as XlImage

            img = XlImage(str(logo))
            if img.height:
                rasio = img.width / img.height
                img.height = 70
                img.width = int(70 * rasio)
            ws.add_image(img, f"A{r}")
        except Exception:  # logo rusak tidak boleh menggagalkan dokumen
            pass

    # ---- teks perusahaan di kolom C ------------------------------------
    _tulis(ws, r, 3, perusahaan.nama, bold=True, size=11)
    for i, baris_alamat in enumerate(perusahaan.alamat_baris, start=1):
        _tulis(ws, r + i, 3, baris_alamat, size=9)

    # ---- blok kanan: tanggal, Kepada Yth., nama, alamat ----------------
    k = kolom_kanan
    _tulis(ws, r, k, f"{perusahaan.kota_penerbitan}, {tanggal_indonesia(tanggal_dokumen)}", size=10)
    _tulis(ws, r + 1, k, "Kepada Yth.", size=10)
    _tulis(ws, r + 2, k, nama_customer or "(nama customer belum diisi)", bold=True, size=10)
    baris_alamat_cust = pecah_alamat(alamat_customer)
    if not baris_alamat_cust:
        baris_alamat_cust = ["(alamat belum diisi)"]
    for i, teks in enumerate(baris_alamat_cust, start=3):
        _tulis(ws, r + i, k, teks, size=9)


def judul_faktur(ws: Worksheet, baris: int, nomor: str, *, kolom_nomor: int = 3) -> None:
    """Baris penanda faktur: "FAKTUR NO." lalu nomornya BERGARIS BAWAH.

    Dibaca dari 0020826 CV. BASA MANDIRI: A9 berisi "FAKTUR NO." tebal, dan
    nomornya ada di sel TERPISAH dengan garis bawah. Bukan satu kalimat
    "FAKTUR No. 0020826" seperti versi sebelumnya.

    Faktur asli TIDAK memuat baris BRAND — itu hanya ada di Surat Jalan.
    """
    _tulis(ws, baris, 1, "FAKTUR NO.", bold=True, size=11)
    sel = _tulis(ws, baris, kolom_nomor, nomor, bold=True, size=11)
    sel.font = Font(name=FONT, size=11, bold=True, underline="single")
    return sel


# ---------------------------------------------------------------- pembantu
# Format akuntansi Rupiah persis seperti faktur asli DPM: "Rp" menempel di
# tepi KIRI sel dan angkanya rata kanan. Dibaca dari 0020826 CV. BASA MANDIRI.
# Inilah sebabnya "Rp" terlihat seperti kolom sendiri padahal bukan.
FORMAT_RP = r'_-"Rp"* #,##0_-;\-"Rp"* #,##0_-;_-"Rp"* "-"_-;_-@_-'
FORMAT_ANGKA = "#,##0"


def huruf(kolom: int) -> str:
    from openpyxl.utils import get_column_letter

    return get_column_letter(kolom)


def sel_judul(ws: Worksheet, baris: int, kolom: int, teks):
    """Sel judul tabel: tebal, rata tengah, berbingkai."""
    sel = ws.cell(baris, kolom, teks)
    sel.font = Font(name=FONT, size=9, bold=True)
    sel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    sel.border = GARIS
    return sel


def sel_isi(ws: Worksheet, baris: int, kolom: int, nilai, *, rata: str = "left",
            angka: Optional[str] = None, tebal: bool = False):
    """Sel isi tabel."""
    sel = ws.cell(baris, kolom, nilai)
    sel.font = Font(name=FONT, size=9, bold=tebal)
    sel.alignment = Alignment(horizontal=rata, vertical="center")
    if angka:
        sel.number_format = angka
        if rata == "left":
            sel.alignment = Alignment(horizontal="right", vertical="center")
    return sel
