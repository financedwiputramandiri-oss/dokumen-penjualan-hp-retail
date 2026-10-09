"""Kunci sapuan yang berlaku untuk SEMUA komputer sekaligus.

Kenapa perlu
------------
`jadwal/sapu.bat` sudah punya kunci, tapi kunci itu berupa berkas di
komputer yang bersangkutan. Kunci semacam itu hanya menahan dua sapuan di
SATU komputer. Begitu bot dipasang di laptop DAN di komputer kantor,
keduanya bangun jam 06:00 dan menyapu bersamaan:

  * `kondisi_sapu.json` ditulis dua kali, yang belakangan menimpa yang
    duluan, jadi sebagian PO kehilangan sidik jarinya dan dokumennya
    dibuat ulang terus-menerus;
  * kalau berkas kondisinya ditaruh di folder Drive, Drive malah membuat
    salinan bentrok dan tidak ada yang tahu mana yang berlaku;
  * dua komputer menulis dokumen ke folder sinkron yang sama pada detik
    yang sama.

Kunci berbasis berkas di folder Drive TIDAK menolong: Drive baru
menyinkronkan beberapa detik sampai semenit kemudian, dan dalam jeda itu
kedua komputer sama-sama merasa mendapat kunci.

Karena itu kuncinya ditaruh di tempat yang dilihat semua komputer pada
detik yang sama: sheet OTOMATISASI, tab `BOT_KUNCI`. Bot sudah punya hak
Editor di situ dan sudah menulis tab `BOT_` lain, jadi tidak ada izin baru
yang perlu diberikan.

Cara kerjanya
-------------
Ambil kunci = tulis token acak milik sendiri, tunggu sebentar, lalu BACA
ULANG. Kalau yang terbaca masih token sendiri, kunci itu milik kita; kalau
sudah tertimpa komputer lain, kita mengalah. Sheets API tidak punya
operasi tulis-kalau-masih-sama, jadi tulis-tunggu-baca inilah pengganti
yang paling dekat, dan itu sudah cukup: yang dilindungi bukan transaksi
uang, hanya supaya dua sapuan tidak jalan bersamaan.

Kunci KEDALUWARSA sendiri sesudah `BATAS_MENIT`. Tanpa itu, satu komputer
yang mati listrik di tengah sapuan akan memblokir seluruh armada selamanya.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from .kondisi import nama_komputer
from .tulis_sheet import PenulisSheet

TAB_KUNCI = "BOT_KUNCI"

# Sapuan penuh pertama pernah makan waktu beberapa menit. 45 menit memberi
# kelonggaran besar, sekaligus memastikan kunci yang ditinggal komputer mati
# tidak menahan sapuan berikutnya lebih dari satu putaran jadwal.
BATAS_MENIT = 45

# Jeda antara menulis token dan membacanya kembali. Cukup untuk memastikan
# penulisan komputer lain yang berbarengan sudah ikut mendarat.
JEDA_PERIKSA = 3.0


def _sekarang() -> datetime:
    return datetime.now(timezone.utc)


def _baca_waktu(teks: str) -> Optional[datetime]:
    try:
        t = datetime.fromisoformat((teks or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


@dataclass
class Pemegang:
    """Siapa yang sedang memegang kunci."""

    token: str = ""
    perangkat: str = ""
    mulai: str = ""
    keterangan: str = ""

    @property
    def kosong(self) -> bool:
        return not self.token

    def kedaluwarsa(self, batas_menit: int = BATAS_MENIT) -> bool:
        t = _baca_waktu(self.mulai)
        if t is None:
            return True
        return _sekarang() - t > timedelta(minutes=batas_menit)

    def umur_menit(self) -> int:
        t = _baca_waktu(self.mulai)
        if t is None:
            return 0
        return int((_sekarang() - t).total_seconds() // 60)


class KunciBersama:
    """Kunci sapuan di tab BOT_KUNCI sheet OTOMATISASI."""

    def __init__(self, sambungan, id_sheet: str, perangkat: str = "",
                 batas_menit: int = BATAS_MENIT, jeda: float = JEDA_PERIKSA):
        self.penulis = PenulisSheet(sambungan, id_sheet)
        self.s = sambungan
        self.id = id_sheet
        self.perangkat = perangkat or nama_komputer() or "(tanpa nama)"
        self.batas_menit = batas_menit
        self.jeda = jeda
        self.token = ""
        self.pemegang_lain: Optional[Pemegang] = None

    # ------------------------------------------------------------ baca
    def _baca(self) -> Pemegang:
        if TAB_KUNCI not in (self.penulis._judul or []):
            return Pemegang()
        baris = self.s.ambil_tab(self.id, [TAB_KUNCI]).get(TAB_KUNCI, [])
        for b in baris[1:]:
            nilai = [str(x).strip() if x is not None else "" for x in b]
            nilai += [""] * (4 - len(nilai))
            if nilai[0]:
                return Pemegang(*nilai[:4])
        return Pemegang()

    def _tulis(self, p: Pemegang) -> None:
        self.penulis.tulis_tab(TAB_KUNCI, [
            ["TOKEN", "KOMPUTER", "MULAI (UTC)", "KETERANGAN"],
            [p.token, p.perangkat, p.mulai, p.keterangan],
            [],
            ["CATATAN",
             "Tab ini dipakai bot untuk memastikan hanya SATU komputer "
             "menyapu pada satu waktu. Jangan diketik manual. Kalau baris "
             f"di atas terisi lebih dari {self.batas_menit} menit, bot "
             "menganggapnya tertinggal dan mengambil alih sendiri."],
        ])

    # ---------------------------------------------------------- ambil
    def ambil(self, keterangan: str = "") -> bool:
        """True kalau kunci berhasil didapat. False = komputer lain sedang menyapu."""
        self.penulis.muat_daftar_tab()
        lama = self._baca()
        if not lama.kosong and not lama.kedaluwarsa(self.batas_menit):
            self.pemegang_lain = lama
            return False

        self.token = uuid.uuid4().hex[:12]
        self._tulis(Pemegang(self.token, self.perangkat,
                             _sekarang().isoformat(timespec="seconds"),
                             keterangan or "sedang menyapu"))

        # Tulis dulu, baru periksa. Kalau dua komputer menulis berbarengan,
        # yang terbaca sesudah jeda ini hanya SATU token, dan hanya pemilik
        # token itu yang melanjutkan.
        time.sleep(self.jeda)
        kini = self._baca()
        if kini.token != self.token:
            self.pemegang_lain = kini
            self.token = ""
            return False
        return True

    def lepas(self) -> None:
        """Kosongkan kunci. Aman dipanggil walau kunci tidak pernah didapat."""
        if not self.token:
            return
        try:
            kini = self._baca()
            # Kunci yang sudah diambil alih komputer lain (karena sapuan ini
            # kelewat lama) TIDAK dihapus — kalau dihapus, sapuan komputer itu
            # berjalan tanpa kunci sama sekali.
            if kini.token == self.token:
                self._tulis(Pemegang("", "", "",
                                     f"selesai {_sekarang():%Y-%m-%d %H:%M} UTC "
                                     f"oleh {self.perangkat}"))
        finally:
            self.token = ""

    def __enter__(self) -> "KunciBersama":
        return self

    def __exit__(self, *_) -> None:
        self.lepas()


def kalimat_ditolak(pemegang: Optional[Pemegang]) -> str:
    """Penjelasan untuk orang, bukan untuk log."""
    if pemegang is None or pemegang.kosong:
        return "Komputer lain sedang menyapu. Coba lagi sebentar lagi."
    return (
        f"DILEWATI: komputer '{pemegang.perangkat}' sedang menyapu "
        f"(mulai {pemegang.umur_menit()} menit lalu). Sapuan ini dihentikan "
        f"supaya keduanya tidak saling menimpa catatan sapuan. "
        f"Tunggu sampai selesai, lalu jalankan lagi."
    )
