"""Menyaring sapuan menurut MINGGU, bukan bulan.

Permintaan Yosua 6 Oktober 2026: *"jika terdapat proses sweep bot atau sapu
bot buat scope menjadi perminggu saja untuk menghemat credit"*.

Penyaringan bulan (`bulan.py`) sudah memangkas 22 order sheet jadi satu.
Lingkup minggu memangkas lagi di dalam berkas itu: dari +-20 tab PO sebulan
jadi tab yang tanggalnya memang jatuh di minggu berjalan. Yang dihemat bukan
cuma waktu — isi tab ditarik lewat `batchGet`, jadi tab yang disaring di sini
tidak pernah ikut diminta ke Google sama sekali.

Dua hal yang mudah salah dan sudah dikunci tes:

1. **Satu minggu bisa menyeberang dua bulan.** Minggu 28 September - 4 Oktober
   menyentuh order sheet September DAN Oktober. Menyaring ke satu bulan saja
   akan melewatkan separuhnya, diam-diam.
2. **Tab yang tanggalnya tidak terbaca JANGAN dibuang.** Nama tab ditulis
   Sales dengan bentuk bermacam-macam (lihat `pecah_nama_tab`), dan tab
   seperti `Sheet4` memang berisi PO sungguhan. Melewatkan satu PO yang
   seharusnya terbit jauh lebih mahal daripada menyapu satu tab berlebih.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from ..konfigurasi import pecah_nama_tab


def minggu_dari(hari: date) -> tuple[date, date]:
    """Senin sampai Minggu yang memuat `hari`."""
    senin = hari - timedelta(days=hari.weekday())
    return senin, senin + timedelta(days=6)


def minggu_sekarang(hari_ini: date | None = None) -> tuple[date, date]:
    return minggu_dari(hari_ini or date.today())


def urai_minggu(teks: str, hari_ini: date | None = None) -> tuple[date, date]:
    """Baca pilihan minggu dari baris perintah.

    Diterima: "2026-10-06" (minggu yang memuat tanggal itu), atau kosong
    (minggu berjalan). Salah ketik DITOLAK, tidak diam-diam memakai minggu
    lain — menerbitkan dokumen periode yang salah jauh lebih mahal daripada
    perintah yang ditolak.
    """
    teks = (teks or "").strip()
    if not teks:
        return minggu_sekarang(hari_ini)
    m = re.fullmatch(r"(20\d{2})-(\d{1,2})-(\d{1,2})", teks)
    if not m:
        raise ValueError(
            f"Tanggal '{teks}' tidak dikenali. Tulis seperti 2026-10-06 "
            f"(tanggal mana pun di dalam minggu yang dimaksud)."
        )
    try:
        hari = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError as e:
        raise ValueError(f"Tanggal '{teks}' tidak ada di kalender ({e}).") from e
    return minggu_dari(hari)


def bulan_tersentuh(senin: date, minggu: date) -> list[tuple[int, int]]:
    """(bulan, tahun) yang disentuh rentang ini — bisa dua, kalau menyeberang."""
    hasil: list[tuple[int, int]] = []
    h = senin
    while h <= minggu:
        kunci = (h.month, h.year)
        if kunci not in hasil:
            hasil.append(kunci)
        h += timedelta(days=1)
    return hasil


def tahun_tersentuh(senin: date, minggu: date) -> list[int]:
    return sorted({t for _, t in bulan_tersentuh(senin, minggu)})


def tanggal_tab(nama_tab: str, tahun_bawaan: int) -> date | None:
    """Tanggal PO dari nama tabnya, atau None kalau tidak terbaca.

    Tahun sering tidak ditulis di nama tab (`PO 28 September - Haritsa`),
    jadi dipakai tahun order sheetnya.
    """
    tgl, _ = pecah_nama_tab(nama_tab)
    if not tgl:
        return None
    hari, bulan, tahun = tgl
    try:
        return date(tahun or tahun_bawaan, bulan, hari)
    except ValueError:
        return None


def tab_dalam_minggu(nama_tab: str, senin: date, minggu: date,
                     tahun_bawaan: int) -> bool:
    """True kalau tab ini perlu ikut disapu.

    Tab yang tanggalnya TIDAK TERBACA ikut disapu — lihat catatan 2 di kepala
    berkas. Diam-diam melewatkan PO adalah kegagalan yang paling mahal di
    sistem ini.
    """
    tgl = tanggal_tab(nama_tab, tahun_bawaan)
    if tgl is None:
        return True
    return senin <= tgl <= minggu


def sebutan(senin: date, minggu: date) -> str:
    from .bulan import nama_bulan
    if (senin.month, senin.year) == (minggu.month, minggu.year):
        return (f"{senin.day}-{minggu.day} {nama_bulan(senin.month)} "
                f"{senin.year}")
    return (f"{senin.day} {nama_bulan(senin.month)} - "
            f"{minggu.day} {nama_bulan(minggu.month)} {minggu.year}")
