"""Mengenali tata letak kolom order sheet secara otomatis.

Tata letak order sheet BERUBAH sepanjang waktu. Contoh nyata:

| Periode        | Kolom ukuran | Kolom nilai bersih                          |
|----------------|--------------|---------------------------------------------|
| Januari 2025   | 2-3          | P TOTAL VALUE, Q CBD + 2%, R COD + 1,5%     |
| Agustus 2025   | 7            | AA TOTAL VALUE, AB PPN + 11%, AC COD + 1,5% |
| Okt 2025 - kini| 9            | AC TOTAL VALUE, AD CBD/COD, AE COD          |

Karena itu kolom TIDAK BOLEH dipatok pada huruf tertentu. Modul ini membaca
baris judul dan menentukan sendiri di mana tiap kolom berada, jadi satu
program bisa membaca order sheet tahun berapa pun.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Kata kunci judul kolom, diperiksa pada teks judul yang sudah diseragamkan.
_ORI = "ORIGINAL PO"
_ATO = "AVAILABLE TO ORDER"
_HARGA = "PRICE W/ VAT"
_ORI_VALUE = "TOTAL ORI PO"
_ATO_VALUE = "TOTAL ATO"
_LOSSES = "LOSSES"
_NOTE = "NOTE"
_TOTAL = "TOTAL"


def seragam(v) -> str:
    """Seragamkan isi sel judul: huruf besar, tanpa baris baru, spasi rapat."""
    if v is None:
        return ""
    s = str(v).replace("\n", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().upper()


@dataclass
class KolomNett:
    """Satu kolom nilai bersih di order sheet."""

    kolom: int
    judul: str           # teks judul apa adanya, contoh "DISCOUNT CBD + 1.5%"
    jenis: str           # "TOP" | "CBD" | "COD" | "PPN" | "LAIN"
    tarif: Optional[float]  # persen yang tertulis di judul, contoh 0.015
    kunci: str = ""      # nama unik dalam satu tab; "COD@AD" kalau jenisnya kembar

    @property
    def huruf(self) -> str:
        from openpyxl.utils import get_column_letter
        return get_column_letter(self.kolom)


@dataclass
class TataLetak:
    """Peta kolom satu tab order sheet."""

    baris_judul: int
    kol_kode: int = 1
    kol_nama: int = 2
    kol_warna: int = 3
    ori_mulai: int = 0
    ori_selesai: int = 0      # inklusif
    ato_mulai: int = 0
    ato_selesai: int = 0      # inklusif
    kol_ato_total: int = 0
    kol_harga: int = 0
    kol_ori_value: int = 0
    kol_ato_value: int = 0
    kol_losses: int = 0
    kol_disc: int = 0
    kol_note: int = 0
    nett: list[KolomNett] = field(default_factory=list)
    catatan: list[str] = field(default_factory=list)

    @property
    def jumlah_ukuran(self) -> int:
        return max(0, self.ato_selesai - self.ato_mulai + 1)

    def kolom_top(self) -> Optional[KolomNett]:
        for k in self.nett:
            if k.jenis == "TOP":
                return k
        return None

    def kolom_jenis(self, jenis: str) -> Optional[KolomNett]:
        for k in self.nett:
            if k.jenis == jenis:
                return k
        return None

    def lengkap(self) -> bool:
        return bool(
            self.ato_mulai and self.ato_selesai
            and self.kol_harga and self.kol_ato_value and self.kolom_top()
        )


def _tarif_dari_judul(judul: str) -> Optional[float]:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", judul)
    return float(m.group(1).replace(",", ".")) / 100 if m else None


def _jenis_nett(judul: str) -> str:
    """Tentukan jenis kolom nilai bersih dari judulnya."""
    j = judul.upper()
    if "CBD" in j:
        return "CBD"
    if "COD" in j:
        return "COD"
    if "PPN" in j:
        return "PPN"
    if "TOTAL VALUE" in j:
        return "TOP"
    return "LAIN"


def kenali(ws, baris_judul: int, kolom_maks: int = 60) -> TataLetak:
    """Baca baris judul satu blok, tentukan letak tiap kolom.

    `baris_judul` adalah baris yang kolom A-nya berisi "ARTICLE CODE".
    """
    t = TataLetak(baris_judul=baris_judul)
    batas = min(kolom_maks, max(ws.max_column or 1, 1))
    judul = {c: seragam(ws.cell(baris_judul, c).value) for c in range(1, batas + 1)}
    isi = {c: j for c, j in judul.items() if j}
    # Kolom TOTAL ditulis di baris LABEL UKURAN (satu baris di bawah judul),
    # bukan di baris judul, jadi baris itu ikut dibaca khusus untuk mencari TOTAL.
    bawah = {
        c: seragam(ws.cell(baris_judul + 1, c).value) for c in range(1, batas + 1)
    }
    total_di = {c for c, j in list(isi.items()) + list(bawah.items()) if j == _TOTAL}

    def cari(kunci: str, mulai: int = 1) -> Optional[int]:
        for c in sorted(isi):
            if c >= mulai and kunci in isi[c]:
                return c
        return None

    def total_setelah(c0: int) -> Optional[int]:
        sesudah = sorted(c for c in total_di if c > c0)
        return sesudah[0] if sesudah else None

    c_ori = cari(_ORI)
    c_ato = cari(_ATO)
    t.kol_harga = cari(_HARGA) or 0
    t.kol_ori_value = cari(_ORI_VALUE) or 0
    t.kol_ato_value = cari(_ATO_VALUE) or 0
    t.kol_losses = cari(_LOSSES) or 0
    t.kol_note = cari(_NOTE) or 0

    if not c_ori or not c_ato or not t.kol_harga:
        t.catatan.append(
            "Baris judul tidak memuat ORIGINAL PO / AVAILABLE TO ORDER / PRICE W/ VAT."
        )
        return t

    # Kolom TOTAL berada tepat sebelum blok berikutnya.
    # ORIGINAL PO : dari c_ori sampai sebelum kolom TOTAL pertama setelahnya.
    total_setelah_ori = total_setelah(c_ori)
    if total_setelah_ori and total_setelah_ori >= c_ato:
        total_setelah_ori = None
    t.ori_mulai = c_ori
    t.ori_selesai = (total_setelah_ori - 1) if total_setelah_ori else (c_ato - 1)

    # AVAILABLE TO ORDER : dari c_ato sampai sebelum kolom TOTAL berikutnya,
    # atau sampai sebelum PRICE W/ VAT kalau tidak ada TOTAL.
    total_setelah_ato = total_setelah(c_ato)
    t.ato_mulai = c_ato
    if total_setelah_ato and total_setelah_ato < t.kol_harga:
        t.ato_selesai = total_setelah_ato - 1
        t.kol_ato_total = total_setelah_ato
    else:
        t.ato_selesai = t.kol_harga - 1
        t.catatan.append("Kolom TOTAL milik AVAILABLE TO ORDER tidak ketemu.")

    # Kolom DISC / DISCOUNT tunggal (persen diskon dasar), yang berdiri sendiri
    # tepat sebelum TOTAL VALUE. Dibedakan dari "DISCOUNT CBD + ..." dsb.
    for c in sorted(isi):
        if c <= t.kol_ato_value:
            continue
        j = isi[c]
        if j in ("DISC", "DISCOUNT"):
            t.kol_disc = c
            break

    # Kolom nilai bersih: semua judul TOTAL VALUE / DISCOUNT ... setelah LOSSES
    mulai_nett = t.kol_losses or t.kol_ato_value or t.kol_harga
    for c in sorted(isi):
        if c <= mulai_nett or c == t.kol_disc or c == t.kol_note:
            continue
        j = isi[c]
        if not ("TOTAL VALUE" in j or j.startswith("DISCOUNT")):
            continue
        jenis = _jenis_nett(j)
        if jenis == "LAIN" and "TOTAL VALUE" not in j:
            continue
        t.nett.append(
            KolomNett(kolom=c, judul=str(ws.cell(baris_judul, c).value).replace("\n", " ").strip(),
                      jenis=jenis, tarif=_tarif_dari_judul(j))
        )

    # Kalau ada beberapa kolom berjudul TOTAL VALUE, yang pertama dipakai
    # sebagai nett TOP; sisanya dicatat sebagai kolom tambahan.
    top = [k for k in t.nett if k.jenis == "TOP"]
    if len(top) > 1:
        for k in top[1:]:
            k.jenis = "LAIN"
        t.catatan.append(
            f"Ada {len(top)} kolom berjudul TOTAL VALUE; yang dipakai kolom {top[0].huruf}."
        )
    if not top:
        t.catatan.append("Kolom TOTAL VALUE tidak ketemu.")

    # Satu tab bisa punya DUA kolom dengan jenis sama, contoh Agustus 2026
    # Baby Wise (Surabaya): AD dan AE dua-duanya berjudul COD. Kalau kuncinya
    # sama, yang satu akan menimpa yang lain, jadi kunci dibuat unik.
    hitung: dict[str, int] = {}
    for k in t.nett:
        hitung[k.jenis] = hitung.get(k.jenis, 0) + 1
    for k in t.nett:
        k.kunci = k.jenis if hitung[k.jenis] == 1 else f"{k.jenis}@{k.huruf}"
    if any(v > 1 for v in hitung.values()):
        kembar = sorted(j for j, v in hitung.items() if v > 1)
        t.catatan.append(
            "Ada lebih dari satu kolom nilai bersih berjenis " + ", ".join(kembar)
            + ". Semuanya tetap dibaca, dibedakan lewat huruf kolomnya."
        )
    return t
