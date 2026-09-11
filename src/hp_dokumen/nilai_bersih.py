"""Aturan 2 — nilai bersih diambil dari kolomnya, bukan dihitung.

JANGAN PERNAH menghitung nilai bersih dari persentase diskon yang disimpan di
master atau ditebak dari rasio. Penentuan cara bayar dilakukan di tingkat ORDER
(satu tab), bukan per baris:

    kolom COD/CBD terisi PENUH semua baris  ->  CBD/COD  ->  pakai kolom itu
    kolom COD/CBD terisi sebagian           ->  TOP      ->  pakai TOTAL VALUE
    kolom COD/CBD kosong sama sekali        ->  TOP      ->  pakai TOTAL VALUE

Kolom yang terisi sebagian diabaikan SELURUHNYA, bukan ditambal.
"""
from __future__ import annotations

import re

from .konfigurasi import Customer
from .model import Baris, KeputusanNett, Order


def nett_baris(baris: Baris, kolom: str) -> float:
    """Nilai bersih satu baris dari kolom sumber yang dipilih."""
    if kolom == "AD":
        return baris.disc_cbd if baris.disc_cbd is not None else 0.0
    if kolom == "AE":
        return baris.disc_cod if baris.disc_cod is not None else 0.0
    return baris.total_value


def _nama_cara_bayar(judul: str, bawaan: str) -> str:
    """Ambil nama cara bayar dari judul kolom di order sheet.

    Sebagian tab menamai kolom AD sebagai 'DISCOUNT COD + 2%', bukan CBD.
    Nama yang dipakai di dokumen mengikuti order sheet, bukan tebakan.
    """
    atas = (judul or "").upper()
    if "CBD" in atas:
        return "CBD"
    if "COD" in atas:
        return "COD"
    return bawaan


def tentukan_nett(order: Order, customer: Customer | None = None) -> KeputusanNett:
    baris = order.semua_baris
    n = len(baris)
    terisi_cbd = sum(1 for b in baris if b.disc_cbd is not None and b.disc_cbd != 0)
    terisi_cod = sum(1 for b in baris if b.disc_cod is not None and b.disc_cod != 0)

    paksa = (customer.cara_bayar_paksa if customer else "") or ""
    dioverride = False
    if paksa in ("TOP", "CBD", "COD"):
        dioverride = True
        kolom = {"TOP": "AC", "CBD": "AD", "COD": "AE"}[paksa]
        nama = paksa
        alasan = (
            f"Dipaksa lewat config/customer.csv (cara_bayar_paksa={paksa}), "
            "bukan dari kelengkapan kolom."
        )
    elif n > 0 and terisi_cbd == n:
        kolom = "AD"
        nama = _nama_cara_bayar(order.judul_cbd, "CBD")
        alasan = f"Kolom '{order.judul_cbd or 'AD'}' terisi penuh di semua baris."
    elif n > 0 and terisi_cod == n:
        kolom = "AE"
        nama = _nama_cara_bayar(order.judul_cod, "COD")
        alasan = f"Kolom '{order.judul_cod or 'AE'}' terisi penuh di semua baris."
    elif terisi_cbd or terisi_cod:
        kolom, nama = "AC", "TOP"
        alasan = (
            f"Kolom CBD/COD terisi {terisi_cbd}/{n} (AD) dan {terisi_cod}/{n} (AE) — "
            "terisi sebagian, jadi diabaikan seluruhnya dan order diperlakukan TOP."
        )
    else:
        kolom, nama = "AC", "TOP"
        alasan = "Kolom CBD dan COD kosong sama sekali."

    keterangan = {
        "AC": "TOTAL VALUE (kolom AC)",
        "AD": f"{order.judul_cbd or 'DISCOUNT CBD'} (kolom AD)",
        "AE": f"{order.judul_cod or 'DISCOUNT COD'} (kolom AE)",
    }[kolom]

    nett = sum(nett_baris(b, kolom) for b in baris)
    return KeputusanNett(
        cara_bayar=nama,
        kolom=kolom,
        kolom_sumber=keterangan,
        nett_total=nett,
        jumlah_baris=n,
        terisi_cbd=terisi_cbd,
        terisi_cod=terisi_cod,
        dioverride=dioverride,
        alasan=alasan,
    )


def tarif_tambahan_tertulis(judul: str) -> float | None:
    """Baca angka persen dari judul kolom, contoh 'DISCOUNT CBD + 1.5%' -> 0.015."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", judul or "")
    return float(m.group(1).replace(",", ".")) / 100 if m else None


def persen_diskon_efektif(nilai_kotor: float, nett: float) -> float:
    """Persen diskon untuk DITAMPILKAN di invoice.

    Dihitung MUNDUR dari nilai bersih yang sudah pasti, bukan sebaliknya.
    Totalnya tetap memakai angka dari order sheet, jadi persen ini murni hiasan
    di baris judul invoice dan tidak pernah dipakai untuk menghitung apa pun.
    """
    if nilai_kotor <= 0:
        return 0.0
    return 1.0 - (nett / nilai_kotor)
