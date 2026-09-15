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


def nett_baris(baris: Baris, kunci: str) -> float:
    """Nilai bersih satu baris dari kolom sumber yang dipilih.

    `kunci` adalah nama kolom nett di tab itu, contoh "TOP", "CBD", atau
    "COD@AD" kalau ada dua kolom berjenis sama.
    """
    nilai = baris.nett.get(kunci)
    return float(nilai) if nilai is not None else 0.0


def _terisi(order: Order, kunci: str) -> int:
    return sum(
        1
        for b in order.semua_baris
        if b.nett.get(kunci) is not None and b.nett.get(kunci) != 0
    )


def tentukan_nett(order: Order, customer: Customer | None = None) -> KeputusanNett:
    """Aturan 2 — pilih kolom nilai bersih untuk SATU order.

    Diperiksa SEMUA kolom nett yang ada di tab itu, bukan cuma dua kolom tetap,
    karena susunan order sheet berubah-ubah antar tahun. Kolom yang terisi penuh
    di semua baris dipakai; kolom yang terisi sebagian diabaikan seluruhnya.
    """
    baris = order.semua_baris
    n = len(baris)
    kandidat = [k for k in order.kolom_nett() if k.jenis not in ("TOP", "LAIN")]

    terisi = {k.kunci: _terisi(order, k.kunci) for k in kandidat}
    terisi_cbd = max(
        (v for k, v in terisi.items() if k.startswith("CBD")), default=0
    )
    terisi_cod = max(
        (v for k, v in terisi.items() if k.startswith("COD")), default=0
    )

    paksa = (customer.cara_bayar_paksa if customer else "") or ""
    dioverride = False
    dipakai = None

    if paksa in ("TOP", "CBD", "COD"):
        dioverride = True
        if paksa == "TOP":
            kunci, nama = "TOP", "TOP"
        else:
            cocok = [k for k in kandidat if k.jenis == paksa]
            if cocok:
                dipakai = cocok[0]
                kunci, nama = dipakai.kunci, paksa
            else:
                kunci, nama = "TOP", "TOP"
        alasan = (
            f"Dipaksa lewat config/customer.csv (cara_bayar_paksa={paksa}), "
            "bukan dari kelengkapan kolom."
        )
    else:
        penuh = [k for k in kandidat if n > 0 and terisi[k.kunci] == n]
        if penuh:
            dipakai = penuh[0]
            kunci, nama = dipakai.kunci, dipakai.jenis
            alasan = f"Kolom '{dipakai.judul}' terisi penuh di semua baris."
            if len(penuh) > 1:
                lain = ", ".join(f"'{k.judul}'" for k in penuh[1:])
                alasan += f" (kolom lain yang juga penuh: {lain} — yang kiri dipakai)"
        else:
            kunci, nama = "TOP", "TOP"
            sebagian = [
                f"'{k.judul}' {terisi[k.kunci]}/{n}"
                for k in kandidat
                if terisi[k.kunci]
            ]
            if sebagian:
                alasan = (
                    "Terisi sebagian: " + "; ".join(sebagian)
                    + " — jadi diabaikan seluruhnya dan order diperlakukan TOP."
                )
            else:
                alasan = "Semua kolom potongan CBD/COD kosong."

    keterangan = "TOTAL VALUE"
    if dipakai is not None:
        keterangan = f"{dipakai.judul} (kolom {dipakai.huruf})"
    else:
        top = order.kolom_nett()
        t0 = next((k for k in top if k.jenis == "TOP"), None)
        if t0 is not None:
            keterangan = f"{t0.judul} (kolom {t0.huruf})"

    nett = sum(nett_baris(b, kunci) for b in baris)
    return KeputusanNett(
        cara_bayar=nama,
        kolom=kunci,
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
