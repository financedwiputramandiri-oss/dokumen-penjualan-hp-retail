"""Menyusun database customer dari seluruh riwayat order sheet.

Menjawab: tiap customer levelnya diskon berapa, cara bayarnya TOP/COD/CBD,
kapan saja belanja, dan berapa nilainya — dari order sheet paling lama sampai
yang terbaru.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from .riwayat import CatatanPO, gabungkan_nama


@dataclass
class Customer:
    """Satu customer hasil penggabungan, dengan riwayatnya."""

    kunci: str
    nama_tampil: str
    po: list[CatatanPO] = field(default_factory=list)
    ejaan: set[str] = field(default_factory=set)

    # ---- urutan waktu ---------------------------------------------------
    def urut(self) -> list[CatatanPO]:
        return sorted(self.po, key=lambda x: (x.tahun, x.bulan, x.tab))

    @property
    def pertama(self) -> CatatanPO:
        return self.urut()[0]

    @property
    def terakhir(self) -> CatatanPO:
        return self.urut()[-1]

    @property
    def jumlah_po(self) -> int:
        return len(self.po)

    @property
    def total_qty(self) -> int:
        return sum(x.qty for x in self.po)

    @property
    def total_kotor(self) -> float:
        return sum(x.kotor for x in self.po)

    @property
    def total_nett(self) -> float:
        return sum(x.nett for x in self.po)

    # ---- diskon ---------------------------------------------------------
    def diskon_dipakai(self) -> list[float]:
        """Semua tingkat diskon yang pernah dipakai, urut dari kecil."""
        return sorted({round(x.diskon_nyata, 4) for x in self.po})

    @property
    def diskon_terakhir(self) -> float:
        return self.terakhir.diskon_nyata

    @property
    def diskon_berubah(self) -> bool:
        return len(self.diskon_dipakai()) > 1

    def riwayat_diskon(self) -> list[tuple[str, float]]:
        """Perubahan diskon sepanjang waktu, hanya saat berubah."""
        hasil: list[tuple[str, float]] = []
        for x in self.urut():
            d = round(x.diskon_nyata, 4)
            if not hasil or abs(hasil[-1][1] - d) > 1e-9:
                hasil.append((x.periode, d))
        return hasil

    # ---- cara bayar -----------------------------------------------------
    def cara_bayar_dipakai(self) -> list[str]:
        urut = []
        for x in self.po:
            if x.cara_bayar not in urut:
                urut.append(x.cara_bayar)
        return urut

    @property
    def cara_bayar_terakhir(self) -> str:
        return self.terakhir.cara_bayar

    @property
    def pernah_ppn(self) -> bool:
        """Pernah memakai kolom DISCOUNT PPN — petunjuk diproses lewat CV DPM."""
        return any(x.cara_bayar == "PPN" for x in self.po)

    def cara_bayar_utama(self) -> str:
        """Cara bayar yang paling sering dipakai."""
        hitung: dict[str, int] = {}
        for x in self.po:
            hitung[x.cara_bayar] = hitung.get(x.cara_bayar, 0) + 1
        return max(hitung, key=lambda k: (hitung[k], k)) if hitung else ""

    @property
    def cara_bayar_berubah(self) -> bool:
        return len(set(x.cara_bayar for x in self.po)) > 1

    @property
    def periode_aktif(self) -> str:
        a, b = self.pertama, self.terakhir
        return a.periode if a.periode == b.periode else f"{a.periode} - {b.periode}"


def bangun(catatan: Iterable[CatatanPO]) -> tuple[list[Customer], list[str]]:
    """Gabungkan catatan PO jadi daftar customer."""
    catatan = list(catatan)
    baku, jejak = gabungkan_nama(catatan)
    per_kunci: dict[str, Customer] = {}
    for c in catatan:
        k = baku.get(c.kunci, c.kunci)
        if k not in per_kunci:
            per_kunci[k] = Customer(kunci=k, nama_tampil="")
        per_kunci[k].po.append(c)
        per_kunci[k].ejaan.add(c.nama_mentah)
    for cust in per_kunci.values():
        # nama tampil = ejaan terpanjang yang pernah muncul (paling lengkap)
        cust.nama_tampil = max(sorted(cust.ejaan), key=len)
    return sorted(per_kunci.values(), key=lambda c: -c.total_nett), jejak


def dugaan_nama_sama(daftar: list[Customer], panjang_min: int = 5) -> list[list[Customer]]:
    """Cari customer yang KEMUNGKINAN sebenarnya sama, untuk diperiksa manusia.

    Tidak digabung otomatis. Contoh nyata yang tidak boleh ditebak sendiri:
    'Joy Baby' dan 'Joy Baby (Mojokerto)' bisa jadi satu toko yang namanya
    dilengkapi belakangan, bisa juga dua cabang berbeda.
    """
    def padat(s: str) -> str:
        return s.replace(" ", "")

    hasil: list[list[Customer]] = []
    sudah: set[str] = set()
    urut = sorted(daftar, key=lambda c: len(padat(c.kunci)))
    for i, a in enumerate(urut):
        if a.kunci in sudah:
            continue
        pa = padat(a.kunci)
        if len(pa) < panjang_min:
            continue
        grup = [a]
        for b in urut[i + 1:]:
            if b.kunci in sudah:
                continue
            if padat(b.kunci).startswith(pa):
                grup.append(b)
        if len(grup) > 1:
            for g in grup:
                sudah.add(g.kunci)
            hasil.append(grup)
    return hasil
