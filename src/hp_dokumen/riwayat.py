"""Menelusuri seluruh order sheet lama untuk membangun database customer.

Menghasilkan, per customer: tingkat diskon, kondisi pembayaran (TOP/COD/CBD),
periode aktif, dan nilai belanja — dari order sheet paling lama sampai terbaru.

Nama customer di order sheet berantakan: ada salah ketik, ada yang memakai
spasi berbeda, dan nama tab terpotong 31 huruf saat diunduh sebagai Excel.
Modul ini menyeragamkannya lebih dulu.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import openpyxl

from .konfigurasi import pecah_nama_tab
from .nilai_bersih import tentukan_nett
from .pemindai import pindai_tab

BULAN = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11,
    "desember": 12,
}

# Kata yang ditulis bermacam-macam tapi maksudnya sama.
_SERAGAM = [
    (r"\bbaby\s*shop\b", "babyshop"),
    (r"\bbaby\s*store\b", "babystore"),
    (r"\bbaby\s*&\s*kids\b", "babykids"),
    (r"\bbaby\s*and\s*kids\b", "babykids"),
    (r"\bcollection\b", "collection"),
    (r"\bstore\b", "store"),
]


def _tanpa_aksen(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def seragamkan_nama(nama: str) -> str:
    """Bentuk baku sebuah nama customer untuk pembandingan."""
    s = _tanpa_aksen(str(nama or "")).lower()
    s = re.sub(r"^\(delivery\s*\d*\)\s*", "", s)
    s = re.sub(r"^po\s+", "", s)
    s = re.sub(r"^\d{1,2}\s+\w+\s*-?\s*", "", s)   # sisa tanggal di depan
    s = s.replace("&", " dan ")
    s = re.sub(r"[^\w\s]", " ", s)                  # buang kurung & tanda baca
    s = re.sub(r"\s+", " ", s).strip()
    for pola, ganti in _SERAGAM:
        s = re.sub(pola, ganti, s)
    return re.sub(r"\s+", " ", s).strip()


@dataclass
class CatatanPO:
    """Satu PO dari satu order sheet."""

    tahun: int
    bulan: int
    sumber: str
    tab: str
    nama_mentah: str
    kunci: str
    tanggal: Optional[str]
    baris: int
    qty: int
    kotor: float
    nett: float
    cara_bayar: str
    kolom_sumber: str
    diskon_nyata: float          # dihitung mundur dari TOTAL VALUE
    diskon_ditulis: list[float]  # isi kolom DISC di order sheet
    terisi_cbd: int
    terisi_cod: int

    @property
    def periode(self) -> str:
        nama = [k for k, v in BULAN.items() if v == self.bulan]
        return f"{nama[0].title()} {self.tahun}" if nama else str(self.tahun)


def periode_dari_judul(judul: str) -> tuple[int, int]:
    m = re.search(
        r"(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|"
        r"Oktober|November|Desember)\s*(\d{4})",
        judul, re.I,
    )
    if not m:
        return (0, 0)
    return (int(m.group(2)), BULAN[m.group(1).lower()])


def telusuri_berkas(berkas: Path, judul: str | None = None) -> list[CatatanPO]:
    """Baca satu order sheet, kembalikan satu CatatanPO per tab PO."""
    judul = judul or berkas.stem
    tahun, bulan = periode_dari_judul(judul)
    hasil: list[CatatanPO] = []
    try:
        wb = openpyxl.load_workbook(berkas, data_only=True)
    except Exception:
        return hasil

    for ws in wb.worksheets:
        nama_tab = ws.title
        atas = nama_tab.upper().strip()
        if not (atas.startswith("PO ") or atas.startswith("(DELIVERY")):
            continue
        try:
            blok, total, _w = pindai_tab(ws)
        except Exception:
            continue
        baris = [b for blk in blok for b in blk.baris]
        if not baris:
            continue

        # Order palsu supaya tentukan_nett bisa dipakai apa adanya
        from .model import Order

        order = Order(nama_tab=nama_tab, customer_kunci="", tanggal_po=None,
                      blok=blok, total_sheet=total)
        k = tentukan_nett(order)

        bersih = re.sub(r"^\(Delivery\s*\d*\)\s*", "", nama_tab, flags=re.I)
        _, nama_mentah = pecah_nama_tab(bersih)
        kotor = sum(b.nilai_kotor for b in baris)
        ac = sum(b.total_value for b in baris)
        hasil.append(
            CatatanPO(
                tahun=tahun, bulan=bulan, sumber=judul, tab=nama_tab,
                nama_mentah=nama_mentah.strip(),
                kunci=seragamkan_nama(nama_mentah),
                tanggal=None,
                baris=len(baris),
                qty=sum(b.qty for b in baris),
                kotor=kotor, nett=k.nett_total,
                cara_bayar=k.cara_bayar,
                kolom_sumber=k.kolom_sumber,
                diskon_nyata=round(1 - ac / kotor, 4) if kotor else 0.0,
                diskon_ditulis=sorted({round(b.disc_persen, 4) for b in baris}),
                terisi_cbd=k.terisi_cbd, terisi_cod=k.terisi_cod,
            )
        )
    return hasil


# ------------------------------------------------------- penggabungan nama
BATAS_NAMA_TAB = 30   # nama tab sepanjang ini atau lebih dianggap kemungkinan terpotong


def gabungkan_nama(
    catatan: list["CatatanPO"], panjang_min: int = 6
) -> tuple[dict[str, str], list[str]]:
    """Satukan nama yang sebenarnya sama jadi satu nama baku.

    Masalahnya: saat order sheet diunduh sebagai Excel, nama tab dipotong di
    31 huruf. Satu toko jadi muncul sebagai 'baby fame lam', 'baby fame lampun',
    dan 'baby fame lampung', tergantung panjang tanggal di depannya.

    Menggabungkan berdasarkan awalan saja BERBAHAYA: 'Baby Wise' dan
    'Baby Wise Surabaya' adalah dua toko berbeda, bukan potongan satu sama lain.

    Aturan yang dipakai: sebuah nama hanya boleh digabung ke nama yang lebih
    panjang kalau nama itu SELALU berasal dari tab yang panjangnya tepat 31
    huruf — artinya memang terpotong. Nama yang pernah muncul dari tab lebih
    pendek dari 31 huruf dianggap nama utuh dan dibiarkan berdiri sendiri.

    Mengembalikan ({kunci: kunci_baku}, daftar catatan penggabungan).
    """
    def padat(s: str) -> str:
        return s.replace(" ", "")

    # Sebuah kunci "utuh" kalau pernah datang dari tab yang tidak terpotong.
    utuh: dict[str, bool] = {}
    for c in catatan:
        if not c.kunci:
            continue
        tidak_terpotong = len(c.tab) < BATAS_NAMA_TAB
        utuh[c.kunci] = utuh.get(c.kunci, False) or tidak_terpotong

    unik = sorted(utuh, key=lambda x: (-len(padat(x)), x))
    baku: dict[str, str] = {}
    jejak: list[str] = []
    for k in unik:
        if k in baku:
            continue
        baku[k] = k
        pk = padat(k)
        for lain in unik:
            if lain in baku or lain == k:
                continue
            if utuh.get(lain):
                continue          # nama utuh, bukan potongan — jangan digabung
            pl = padat(lain)
            if len(pl) >= panjang_min and pk.startswith(pl):
                baku[lain] = k
                jejak.append(f"'{lain}' (nama tab terpotong) digabung ke '{k}'")
    return baku, jejak
