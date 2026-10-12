"""Menyaring order sheet menurut BULAN, supaya sapuan mendadak cepat.

Sapuan penuh membaca 22 order sheet. Kalau yang dibutuhkan cuma dokumen
untuk PO yang baru saja masuk, 21 di antaranya sia-sia — bulan-bulan lama
sudah selesai dan tidak akan berubah lagi.

Penyaringan dilakukan dari NAMA BERKASNYA, bukan dari isinya, supaya order
sheet bulan lain tidak perlu dibuka sama sekali. Order sheet Happy Pumpkin
selalu memuat nama bulan pada namanya:

    Order Sheet September 2026
    Order Sheet Agustus 2026 Harga Lama
    Order Sheet Agustus 2026 Harga Baru

Dua berkas terakhir dua-duanya Agustus, dan dua-duanya memang ikut disapu.
"""
from __future__ import annotations

import re
from datetime import date

BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

# Ejaan lain yang pernah dipakai Sales pada nama berkas. Dicocokkan sesudah
# nama resminya, jadi "Agustus" tidak pernah tertukar dengan "Agu".
ALIAS = {
    1: ["Jan"], 2: ["Feb", "Pebruari"], 3: ["Mar"], 4: ["Apr"], 5: [],
    6: ["Jun"], 7: ["Jul"], 8: ["Agu", "Agt", "Agust", "August"],
    9: ["Sep", "Sept"], 10: ["Okt", "Oct"], 11: ["Nov", "Nop"], 12: ["Des", "Dec"],
}

_TAHUN = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def nama_bulan(bulan: int) -> str:
    return BULAN[bulan - 1]


def _sebutan(bulan: int) -> list[str]:
    return [BULAN[bulan - 1]] + ALIAS.get(bulan, [])


def _ada_nama_bulan(nama: str, bulan: int) -> bool:
    """True kalau nama berkas menyebut bulan ini sebagai KATA UTUH.

    Batas kata penting: tanpa itu "Mei" ikut tertangkap di dalam kata lain,
    dan "Jun" tertangkap di dalam "Juni" — dua bulan yang berbeda.
    """
    besar = nama.upper()
    for kata in _sebutan(bulan):
        if re.search(rf"(?<![A-Z]){re.escape(kata.upper())}(?![A-Z])", besar):
            return True
    return False


def tahun_di(nama: str) -> int | None:
    """Tahun yang tertulis di sebuah nama, kalau ada. 20xx saja."""
    cocok = _TAHUN.findall(nama or "")
    return int(cocok[-1]) if cocok else None


def cocok_bulan(nama_berkas: str, bulan: int, tahun: int,
                nama_folder: str = "") -> bool:
    """True kalau order sheet ini memang order sheet bulan yang diminta.

    Bulannya HARUS tertulis di nama berkas — kalau tidak ada, berkas itu
    bukan order sheet bulanan dan tidak ikut disapu.

    Tahunnya dicari di nama berkas dulu, lalu di nama foldernya. Folder
    order sheet Happy Pumpkin memang bernama "Order Sheet 2026" dan
    "Order Sheet 2025", jadi berkas yang namanya tidak memuat tahun tetap
    bisa ditentukan. Kalau tahunnya tidak ketemu di mana pun, berkas itu
    TETAP diikutkan: lebih baik menyapu satu berkas berlebih daripada
    melewatkan order sheet yang dicari.
    """
    if not _ada_nama_bulan(nama_berkas or "", bulan):
        return False
    t = tahun_di(nama_berkas) or tahun_di(nama_folder)
    return t is None or t == tahun


def folder_bisa_dilewati(nama_folder: str, tahun: int) -> bool:
    """True kalau seluruh folder ini pasti bukan tahun yang dicari.

    Menghemat satu panggilan Drive per folder. Hanya berani melewati kalau
    nama foldernya benar-benar menyebut tahun lain; folder tanpa tahun
    selalu dibuka.
    """
    t = tahun_di(nama_folder)
    return t is not None and t != tahun


def bulan_sekarang(hari_ini: date | None = None) -> tuple[int, int]:
    h = hari_ini or date.today()
    return h.month, h.year


def urai_bulan(teks: str, hari_ini: date | None = None) -> tuple[int, int]:
    """Baca pilihan bulan dari baris perintah.

    Diterima: "2026-09", "09/2026", "September 2026", "September".
    Tanpa tahun -> tahun berjalan.
    """
    teks = (teks or "").strip()
    if not teks:
        return bulan_sekarang(hari_ini)

    angka = re.fullmatch(r"(20\d{2})[-/](\d{1,2})", teks)
    if angka:
        return int(angka.group(2)), int(angka.group(1))
    angka = re.fullmatch(r"(\d{1,2})[-/](20\d{2})", teks)
    if angka:
        return int(angka.group(1)), int(angka.group(2))

    tahun = tahun_di(teks) or (hari_ini or date.today()).year
    for b in range(1, 13):
        if _ada_nama_bulan(teks, b):
            return b, tahun
    raise ValueError(
        f"Bulan '{teks}' tidak dikenali. Contoh yang benar: "
        f"2026-09, September 2026, atau September."
    )
