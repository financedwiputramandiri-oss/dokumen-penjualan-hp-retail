"""Kunci sapuan antar-KOMPUTER.

Begitu bot dipasang di laptop DAN komputer kantor, keduanya bangun jam
06:00. Tanpa kunci ini, keduanya menyapu bersamaan dan saling menimpa
catatan sapuan - kegagalan yang tidak memunculkan galat sama sekali,
hanya dokumen yang dibuat ulang terus-menerus.

Tidak menyentuh Google: seluruhnya lewat sambungan palsu.
"""
from datetime import datetime, timedelta, timezone

import pytest

from hp_dokumen.sapu.kunci_bersama import (
    TAB_KUNCI, KunciBersama, Pemegang, kalimat_ditolak,
)


# ------------------------------------------------------------ sambungan palsu
class _Kerja:
    def __init__(self, fn):
        self.fn = fn

    def execute(self):
        return self.fn()


class _Nilai:
    def __init__(self, papan):
        self.p = papan

    def clear(self, spreadsheetId, range, body):
        judul = range.strip("'")
        return _Kerja(lambda: self.p.tab.__setitem__(judul, []))

    def update(self, spreadsheetId, range, valueInputOption, body):
        judul = range.split("'!")[0].strip("'")
        isi = [list(r) for r in body["values"]]
        return _Kerja(lambda: self.p.tab.__setitem__(judul, isi))


class _Spreadsheets:
    def __init__(self, papan):
        self.p = papan

    def values(self):
        return _Nilai(self.p)

    def batchUpdate(self, spreadsheetId, body):
        def jalan():
            for r in body["requests"]:
                self.p.tab.setdefault(r["addSheet"]["properties"]["title"], [])
        return _Kerja(jalan)


class _Sheets:
    def __init__(self, papan):
        self.p = papan

    def spreadsheets(self):
        return _Spreadsheets(self.p)


class SheetPalsu:
    """Satu spreadsheet yang dilihat SEMUA komputer, seperti aslinya."""

    def __init__(self):
        self.tab: dict[str, list[list]] = {}

    @property
    def sheets(self):
        return _Sheets(self)

    def nama_tab(self, id_sheet):
        return list(self.tab)

    def ambil_tab(self, id_sheet, judul, **_):
        return {j: [list(r) for r in self.tab.get(j, [])] for j in judul}


def _kunci(papan, perangkat):
    # jeda=0: tesnya tidak perlu benar-benar menunggu
    return KunciBersama(papan, "SHEET", perangkat=perangkat, jeda=0)


# ------------------------------------------------------------------- tes
def test_komputer_kedua_mengalah_selagi_yang_pertama_menyapu():
    papan = SheetPalsu()
    a, b = _kunci(papan, "LAPTOP"), _kunci(papan, "KOMPUTER-KANTOR")
    assert a.ambil("sapuan penuh") is True
    assert b.ambil("sapuan penuh") is False
    assert b.pemegang_lain.perangkat == "LAPTOP"


def test_kunci_dilepas_boleh_diambil_komputer_lain():
    papan = SheetPalsu()
    a, b = _kunci(papan, "LAPTOP"), _kunci(papan, "KOMPUTER-KANTOR")
    assert a.ambil()
    a.lepas()
    assert b.ambil() is True


def test_kunci_yang_ditinggal_komputer_mati_kedaluwarsa_sendiri():
    """Tanpa ini, satu komputer yang mati listrik memblokir seluruh armada."""
    papan = SheetPalsu()
    tua = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(timespec="seconds")
    papan.tab[TAB_KUNCI] = [["TOKEN", "KOMPUTER", "MULAI (UTC)", "KETERANGAN"],
                            ["abc123", "KOMPUTER-MATI", tua, "sedang menyapu"]]
    assert _kunci(papan, "LAPTOP").ambil() is True


def test_kunci_yang_masih_muda_tidak_diambil_alih():
    papan = SheetPalsu()
    baru = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(timespec="seconds")
    papan.tab[TAB_KUNCI] = [["TOKEN", "KOMPUTER", "MULAI (UTC)", "KETERANGAN"],
                            ["abc123", "KOMPUTER-KANTOR", baru, "sedang menyapu"]]
    assert _kunci(papan, "LAPTOP").ambil() is False


def test_yang_kalah_balapan_tidak_ikut_menyapu():
    """Dua komputer menulis pada detik yang sama: hanya SATU yang lanjut.

    Tulis-tunggu-baca adalah pengganti operasi tulis-kalau-masih-sama yang
    tidak dipunyai Sheets API. Yang tokennya sudah tertimpa harus mengalah,
    bukan menganggap dirinya pemegang kunci.
    """
    papan = SheetPalsu()
    b = _kunci(papan, "KOMPUTER-KANTOR")
    asli = b._baca

    def _baca_seolah_tertimpa():
        hasil = asli()
        if hasil.token == b.token and hasil.token:
            return Pemegang("token-lain", "LAPTOP", hasil.mulai, "sedang menyapu")
        return hasil

    b._baca = _baca_seolah_tertimpa
    assert b.ambil() is False
    assert b.token == ""


def test_lepas_tidak_menghapus_kunci_milik_komputer_lain():
    """Sapuan yang kelewat lama sudah diambil alih; kuncinya bukan miliknya lagi.

    Kalau tetap dihapus, komputer yang sedang menyapu berjalan tanpa kunci
    sama sekali dan komputer ketiga ikut masuk.
    """
    papan = SheetPalsu()
    a = _kunci(papan, "LAPTOP")
    assert a.ambil()
    # komputer lain mengambil alih karena sapuan A dianggap tertinggal
    papan.tab[TAB_KUNCI] = [["TOKEN", "KOMPUTER", "MULAI (UTC)", "KETERANGAN"],
                            ["token-lain", "KOMPUTER-KANTOR",
                             datetime.now(timezone.utc).isoformat(timespec="seconds"),
                             "sedang menyapu"]]
    a.lepas()
    assert papan.tab[TAB_KUNCI][1][0] == "token-lain"
    assert papan.tab[TAB_KUNCI][1][1] == "KOMPUTER-KANTOR"


def test_kunci_hanya_boleh_di_tab_berawalan_BOT():
    """Aturan tulis_sheet.py: bot tidak pernah menyentuh tab buatan Yosua."""
    assert TAB_KUNCI.startswith("BOT_")


def test_kalimat_ditolak_menyebut_komputernya_supaya_bisa_ditindaklanjuti():
    papan = SheetPalsu()
    a, b = _kunci(papan, "LAPTOP-YOSUA"), _kunci(papan, "KOMPUTER-KANTOR")
    a.ambil()
    b.ambil()
    pesan = kalimat_ditolak(b.pemegang_lain)
    assert "LAPTOP-YOSUA" in pesan
    assert "DILEWATI" in pesan


def test_dipakai_sebagai_with_melepas_kuncinya_sendiri():
    papan = SheetPalsu()
    with _kunci(papan, "LAPTOP") as k:
        assert k.ambil()
    assert _kunci(papan, "KOMPUTER-KANTOR").ambil() is True
