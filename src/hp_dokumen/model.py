"""Bentuk data yang dipakai di seluruh program.

Istilah:
  Baris  = satu baris artikel di order sheet (kode + nama + warna + qty per ukuran)
  Blok   = satu tabel dalam satu tab, punya baris judul ARTICLE CODE sendiri
           dan sistem ukurannya sendiri
  Order  = satu tab PO = satu customer = satu set dokumen
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

# Jumlah kolom ukuran di order sheet (D..L untuk PO asli, N..V untuk ATO)
JUMLAH_KOLOM_UKURAN = 9


@dataclass
class Baris:
    """Satu baris artikel yang benar-benar dipesan (qty > 0)."""

    baris_sheet: int          # nomor baris asli di order sheet, untuk penelusuran
    kode: str
    nama: str
    warna: str
    qty_per_ukuran: list[int]  # panjang 9, ikut posisi kolom N..V
    harga: float               # PRICE W/ VAT, sudah termasuk PPN
    nilai_kotor: float         # TOTAL ATO VALUE
    nett: dict = field(default_factory=dict)  # jenis -> nilai; None = sel kosong
    disc_persen: float = 0.0   # kolom DISC, hanya untuk pemeriksaan
    catatan: str = ""

    # Nama lama dipertahankan supaya kode lain tidak perlu berubah.
    @property
    def total_value(self) -> float:
        return self.nett.get("TOP") or 0.0

    def _nett_berjenis(self, jenis: str) -> Optional[float]:
        """Nilai kolom nett pertama berjenis ini (kunci bisa 'COD' atau 'COD@AD')."""
        for kunci, nilai in self.nett.items():
            if kunci == jenis or kunci.startswith(jenis + "@"):
                return nilai
        return None

    @property
    def disc_cbd(self) -> Optional[float]:
        return self._nett_berjenis("CBD")

    @property
    def disc_cod(self) -> Optional[float]:
        return self._nett_berjenis("COD")

    @property
    def qty(self) -> int:
        return sum(self.qty_per_ukuran)


@dataclass
class Blok:
    """Satu tabel dalam satu tab. Punya label ukuran sendiri."""

    nomor: int
    baris_judul: int                 # nomor baris ARTICLE CODE di sheet
    label_ukuran: list[Optional[str]]  # ikut posisi kolom; None = kolom kosong
    baris: list[Baris] = field(default_factory=list)
    tata: object = None   # TataLetak blok ini, untuk penelusuran

    @property
    def qty(self) -> int:
        return sum(b.qty for b in self.baris)

    @property
    def nilai_kotor(self) -> float:
        return sum(b.nilai_kotor for b in self.baris)

    def kolom_terpakai(self) -> list[int]:
        """Posisi kolom ukuran yang benar-benar ada isinya di blok ini."""
        dipakai = []
        for i in range(len(self.label_ukuran)):
            if any(b.qty_per_ukuran[i] for b in self.baris):
                dipakai.append(i)
        return dipakai


@dataclass
class TotalSheet:
    """Baris TOTAL milik order sheet sendiri — dipakai untuk mencocokkan."""

    baris_sheet: Optional[int]
    qty: Optional[int]
    nilai_kotor: Optional[float]
    total_value: Optional[float]


@dataclass
class Order:
    """Satu tab PO."""

    nama_tab: str
    customer_kunci: str          # kunci yang cocok di config/customer.csv
    tanggal_po: Optional[date]
    blok: list[Blok] = field(default_factory=list)
    total_sheet: TotalSheet = None  # type: ignore[assignment]
    peringatan: list[str] = field(default_factory=list)
    judul_cbd: str = ""          # teks judul kolom AD apa adanya di order sheet
    judul_cod: str = ""          # teks judul kolom AE apa adanya di order sheet

    # ---- ringkasan angka -------------------------------------------------
    @property
    def semua_baris(self) -> list[Baris]:
        return [b for blk in self.blok for b in blk.baris]

    @property
    def jumlah_baris(self) -> int:
        return len(self.semua_baris)

    @property
    def qty(self) -> int:
        return sum(b.qty for b in self.semua_baris)

    @property
    def nilai_kotor(self) -> float:
        return sum(b.nilai_kotor for b in self.semua_baris)

    def kolom_nett(self) -> list:
        """Kolom nilai bersih yang tersedia di tab ini, menurut tata letaknya."""
        tata = self.blok[0].tata if self.blok else None
        return list(getattr(tata, "nett", []) or [])


@dataclass
class KeputusanNett:
    """Hasil Aturan 2: cara bayar dan kolom sumber nilai bersih."""

    cara_bayar: str        # nama untuk ditampilkan: "TOP" | "CBD" | "COD"
    kolom: str             # kolom sumber yang dipakai: "AC" | "AD" | "AE"
    kolom_sumber: str      # keterangan lengkap kolom, apa adanya dari order sheet
    nett_total: float
    jumlah_baris: int
    terisi_cbd: int
    terisi_cod: int
    dioverride: bool = False
    alasan: str = ""

    @property
    def cbd_lengkap(self) -> bool:
        return self.jumlah_baris > 0 and self.terisi_cbd == self.jumlah_baris

    @property
    def cod_lengkap(self) -> bool:
        return self.jumlah_baris > 0 and self.terisi_cod == self.jumlah_baris
