"""Rekap hasil sapuan: berapa PO yang dokumennya benar-benar terbit.

Dipakai BERSAMA oleh tiga tempat supaya angkanya tidak pernah berbeda:
lembar REKAP di berkas laporan, tab `BOT_REKAP` di sheet OTOMATISASI, dan
ringkasan yang dicetak di layar. Kalau salah satunya dihitung sendiri, cepat
atau lambat ketiganya akan menyebut angka yang berlainan dan tidak ada yang
tahu mana yang benar.

Satu aturan yang jangan diubah: untuk PO yang dokumennya TIDAK terbit, qty
dan nilainya DIKOSONGKAN, bukan ditampilkan. Angka itu justru yang belum
terverifikasi terhadap baris TOTAL order sheet — kalau ikut ditampilkan,
orang akan memakainya sebagai angka resmi, padahal itu persis yang sedang
bermasalah. Aturan yang sama dipakai REKAP_SAPUAN.csv (CLAUDE.md bagian 30).
"""
from __future__ import annotations

from dataclasses import dataclass, field

JUDUL_PER_PO = [
    "ORDER SHEET", "TAB PO", "CUSTOMER", "TANGGAL PO", "QTY",
    "SEBELUM DISKON", "CARA BAYAR", "NILAI BERSIH", "DOKUMEN", "KETERANGAN",
]

JUDUL_PER_SHEET = [
    "ORDER SHEET", "PO", "DOKUMEN TERBIT", "QTY (PCS)",
    "SEBELUM DISKON (RP)", "NILAI BERSIH (RP)", "KETERANGAN",
]

TERBIT = "TERBIT"
TIDAK_TERBIT = "TIDAK TERBIT"


@dataclass
class BarisSheet:
    """Satu order sheet: berapa PO-nya, berapa yang dokumennya terbit."""
    nama: str
    po: int = 0
    terbit: int = 0
    qty: int = 0
    kotor: float = 0.0
    nett: float = 0.0
    sebab: list[str] = field(default_factory=list)

    @property
    def keterangan(self) -> str:
        if self.terbit == self.po:
            return ""
        # Sebabnya hampir selalu sama untuk seluruh tab dalam satu order
        # sheet, jadi yang ditulis cukup yang berbeda-beda saja.
        unik = list(dict.fromkeys(self.sebab))
        return "; ".join(unik[:3])[:200]


def _terbit(r: dict) -> bool:
    return bool(r.get("siap"))


def baris_per_po(rekaman: list[dict]) -> list[list]:
    """Satu baris per PO, siap ditulis ke lembar atau tab mana pun."""
    keluar = []
    for r in rekaman:
        ada = _terbit(r)
        keluar.append([
            r.get("sumber", ""),
            r.get("tab", ""),
            r.get("customer", ""),
            r.get("tanggal", ""),
            r.get("qty", 0) if ada else "",
            round(r.get("kotor", 0.0)) if ada else "",
            r.get("cara_bayar", "") if ada else "",
            round(r.get("nett", 0.0)) if ada else "",
            TERBIT if ada else TIDAK_TERBIT,
            r.get("keterangan", ""),
        ])
    return keluar


def per_order_sheet(rekaman: list[dict]) -> list[BarisSheet]:
    """Kumpulkan per order sheet, urutannya mengikuti urutan sapuan."""
    kumpul: dict[str, BarisSheet] = {}
    for r in rekaman:
        nama = r.get("sumber", "")
        b = kumpul.setdefault(nama, BarisSheet(nama))
        b.po += 1
        if _terbit(r):
            b.terbit += 1
            b.qty += int(r.get("qty", 0) or 0)
            b.kotor += float(r.get("kotor", 0.0) or 0.0)
            b.nett += float(r.get("nett", 0.0) or 0.0)
        elif r.get("keterangan"):
            b.sebab.append(str(r["keterangan"]))
    return list(kumpul.values())


def total(baris: list[BarisSheet]) -> BarisSheet:
    t = BarisSheet("TOTAL")
    for b in baris:
        t.po += b.po
        t.terbit += b.terbit
        t.qty += b.qty
        t.kotor += b.kotor
        t.nett += b.nett
    return t


def baris_per_sheet(rekaman: list[dict], *, dengan_total: bool = True) -> list[list]:
    """Tabel ringkas per order sheet, ditutup baris TOTAL."""
    kumpul = per_order_sheet(rekaman)
    keluar = []
    for b in kumpul + ([total(kumpul)] if dengan_total else []):
        ada = b.terbit > 0
        keluar.append([
            b.nama, b.po, b.terbit,
            b.qty if ada else "",
            round(b.kotor) if ada else "",
            round(b.nett) if ada else "",
            b.keterangan if b.nama != "TOTAL" else "",
        ])
    return keluar
