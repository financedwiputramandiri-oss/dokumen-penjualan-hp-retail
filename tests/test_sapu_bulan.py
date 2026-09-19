"""Sapuan cepat: hanya order sheet bulan berjalan.

Sapuan penuh membaca 22 order sheet. Kalau yang dibutuhkan cuma dokumen
untuk PO yang baru masuk hari ini, 21 di antaranya sia-sia. Yang dikunci di
sini adalah hal-hal yang kalau salah membuat order sheet yang DICARI malah
terlewat - kegagalan yang tidak menimbulkan galat apa pun, cuma "0 dokumen".
"""
from datetime import date

import pytest

from hp_dokumen.sapu.bulan import (
    cocok_bulan, folder_bisa_dilewati, nama_bulan, tahun_di, urai_bulan,
)


def test_order_sheet_bulan_lain_tidak_ikut():
    assert cocok_bulan("Order Sheet September 2026", 9, 2026)
    assert not cocok_bulan("Order Sheet Agustus 2026", 9, 2026)
    assert not cocok_bulan("Order Sheet September 2025", 9, 2026)


def test_dua_order_sheet_satu_bulan_ikut_dua_duanya():
    """Agustus 2026 punya "Harga Lama" dan "Harga Baru" - dua-duanya PO asli."""
    for n in ("Order Sheet Agustus 2026 Harga Lama",
              "Order Sheet Agustus 2026 Harga Baru"):
        assert cocok_bulan(n, 8, 2026), n


def test_tahun_diambil_dari_nama_folder_kalau_berkasnya_tidak_menyebut():
    """Folder order sheet Happy Pumpkin bernama "Order Sheet 2026"/"2025"."""
    assert cocok_bulan("Order Sheet September", 9, 2026, "Order Sheet 2026")
    assert not cocok_bulan("Order Sheet September", 9, 2026, "Order Sheet 2025")


def test_tanpa_tahun_di_mana_pun_tetap_diikutkan():
    """Lebih baik menyapu satu berkas berlebih daripada melewatkan yang dicari."""
    assert cocok_bulan("Order Sheet September", 9, 2026, "Order Sheet")


def test_nama_bulan_dicocokkan_sebagai_kata_utuh():
    """Tanpa batas kata, "Mei" ikut tertangkap di dalam kata lain.

    Order sheet yang salah disapu berarti dokumen bulan lain ikut dibuat
    ulang - dan itu tidak kelihatan sampai ada yang membuka foldernya.
    """
    assert not cocok_bulan("Order Sheet Meikarta 2026", 5, 2026)
    assert not cocok_bulan("Order Sheet Januari 2026", 6, 2026)   # "Jan" vs "Jun"
    assert cocok_bulan("Order Sheet Juni 2026", 6, 2026)


def test_singkatan_yang_dipakai_sales_ikut_dikenali():
    assert cocok_bulan("Order Sheet Agu 2026", 8, 2026)
    assert cocok_bulan("Order Sheet Sept 2026", 9, 2026)
    assert cocok_bulan("Order Sheet Des 2026", 12, 2026)


def test_berkas_yang_bukan_order_sheet_bulanan_tidak_pernah_ikut():
    for n in ("Harga Retail", "DATABASE CUSTOMER", "OTOMATISASI SINKRON"):
        for b in range(1, 13):
            assert not cocok_bulan(n, b, 2026), f"{n} vs bulan {b}"


def test_folder_tahun_lain_dilewati_seluruhnya():
    """Menghemat satu panggilan Drive per folder."""
    assert folder_bisa_dilewati("Order Sheet 2025", 2026)
    assert not folder_bisa_dilewati("Order Sheet 2026", 2026)
    # folder tanpa tahun SELALU dibuka - tidak boleh menebak
    assert not folder_bisa_dilewati("Order Sheet", 2026)


def test_urai_bulan_menerima_bentuk_yang_wajar_diketik_orang():
    assert urai_bulan("2026-09") == (9, 2026)
    assert urai_bulan("09/2026") == (9, 2026)
    assert urai_bulan("September 2026") == (9, 2026)
    assert urai_bulan("September", date(2026, 3, 1)) == (9, 2026)
    assert urai_bulan("", date(2026, 3, 1)) == (3, 2026)


def test_bulan_ngawur_ditolak_bukan_diam_diam_jadi_bulan_lain():
    with pytest.raises(ValueError):
        urai_bulan("bulan depan")


def test_tahun_di_nama():
    assert tahun_di("Order Sheet Agustus 2026 Harga Lama") == 2026
    assert tahun_di("Order Sheet") is None
    assert nama_bulan(9) == "September"


# ------------------------------------------------------- sambungan ke perintah
def _tangkap(monkeypatch):
    """Ganti sapu() dengan penampung, supaya perintahnya bisa diuji tanpa Google."""
    from hp_dokumen.sapu import bot
    from hp_dokumen.sapu.bot import HasilSapuan

    dicatat = {}

    def palsu(p=None, cfg=None, cetak=print, saring_bulan=None, paksa=False,
              pakai_kunci=None):
        dicatat.update(saring_bulan=saring_bulan, paksa=paksa,
                       pakai_kunci=pakai_kunci)
        return HasilSapuan([], [], [], [])

    monkeypatch.setattr(bot, "sapu", palsu)
    return dicatat


def test_bulan_ini_diteruskan_ke_sapuan(monkeypatch):
    from hp_dokumen.cli import main

    dicatat = _tangkap(monkeypatch)
    assert main(["sapu", "--bulan-ini"]) == 0
    assert dicatat["saring_bulan"] == (date.today().month, date.today().year)


def test_tanpa_pilihan_bulan_seluruh_order_sheet_disapu(monkeypatch):
    from hp_dokumen.cli import main

    dicatat = _tangkap(monkeypatch)
    assert main(["sapu"]) == 0
    assert dicatat["saring_bulan"] is None


def test_bulan_tertentu_bisa_diminta(monkeypatch):
    from hp_dokumen.cli import main

    dicatat = _tangkap(monkeypatch)
    assert main(["sapu", "--bulan", "2026-02"]) == 0
    assert dicatat["saring_bulan"] == (2, 2026)


def test_bulan_yang_salah_ketik_dihentikan_bukan_disapu_diam_diam(monkeypatch):
    """Menyapu bulan yang salah berarti menerbitkan dokumen bulan yang salah."""
    from hp_dokumen.cli import main

    dicatat = _tangkap(monkeypatch)
    assert main(["sapu", "--bulan", "bulan depan"]) == 2
    assert dicatat == {}, "sapuan tidak boleh jalan kalau bulannya tidak jelas"


def test_sapuan_yang_mengalah_ke_komputer_lain_bukan_kegagalan(monkeypatch):
    """Kalau dihitung gagal, log jadwal penuh 'GAGAL' padahal semuanya wajar."""
    from hp_dokumen.cli import main
    from hp_dokumen.sapu import bot
    from hp_dokumen.sapu.bot import HasilSapuan

    monkeypatch.setattr(bot, "sapu", lambda *a, **k: HasilSapuan(
        [], [], [], ["dilewati"], dijalankan=False, alasan_batal="dilewati"))
    assert main(["sapu", "--bulan-ini"]) == 0


# ------------------------------------------- sapuan sungguhan, tanpa Google
class _DrivePalsu:
    """Drive berisi order sheet beberapa bulan. Mencatat apa yang DIBUKA."""

    MIME = "application/vnd.google-apps.spreadsheet"

    def __init__(self, isi: dict[str, list[str]]):
        from hp_dokumen.sapu.google import BerkasDrive

        self.isi = {
            id_folder: [BerkasDrive(n, n, self.MIME, "2026-09-18T00:00:00Z")
                        for n in nama]
            for id_folder, nama in isi.items()
        }
        self.dibuka: list[str] = []
        self.email_bot = "bot@contoh.iam.gserviceaccount.com"

    def isi_folder(self, id_folder):
        return self.isi.get(id_folder, [])

    def daftar_tab(self, id_sheet):
        self.dibuka.append(id_sheet)
        return [{"judul": "Sheet1"}]     # tanpa tab PO: cukup untuk tesnya


def _pengaturan(tmp_path):
    from hp_dokumen.sapu.bot import Pengaturan

    p = Pengaturan.muat()
    p.berkas_kondisi = tmp_path / "kondisi_sapu.json"
    p.folder_draf = tmp_path / "draf"
    p.folder_laporan_id = ""
    p.folder_dokumen_id = ""
    p.sheet_otomatisasi_id = ""
    p.folder = [
        {"nama": "Order Sheet 2026", "id": "F2026"},
        {"nama": "Order Sheet 2025", "id": "F2025"},
    ]
    return p


def _drive():
    return _DrivePalsu({
        "F2026": ["Order Sheet September 2026",
                  "Order Sheet Agustus 2026 Harga Lama",
                  "Order Sheet Juli 2026"],
        "F2025": ["Order Sheet September 2025"],
    })


def test_sapuan_bulan_ini_hanya_membuka_order_sheet_bulan_itu(tmp_path):
    """Inilah seluruh gunanya: order sheet bulan lain TIDAK dibuka sama sekali.

    Kalau yang lain tetap dibuka, sapuan "cepat" tidak lebih cepat sedikit
    pun dan tidak ada yang sadar — hasilnya sama saja.
    """
    from hp_dokumen.konfigurasi import Konfigurasi
    from hp_dokumen.sapu.bot import _sapu

    drive = _drive()
    _sapu(_pengaturan(tmp_path), Konfigurasi.muat(), drive,
          lambda *a: None, (9, 2026), False)
    assert drive.dibuka == ["Order Sheet September 2026"]


def test_sapuan_penuh_membuka_semua_order_sheet(tmp_path):
    from hp_dokumen.konfigurasi import Konfigurasi
    from hp_dokumen.sapu.bot import _sapu

    drive = _drive()
    _sapu(_pengaturan(tmp_path), Konfigurasi.muat(), drive,
          lambda *a: None, None, False)
    assert len(drive.dibuka) == 4


def test_bulan_yang_tidak_ada_order_sheetnya_dilaporkan_keras(tmp_path):
    """"0 order sheet dibaca" terlihat seperti sapuan yang wajar.

    Padahal artinya nama berkas di Drive tidak memuat nama bulannya, dan
    tidak akan ada dokumen yang terbit sampai itu dibetulkan.
    """
    from hp_dokumen.konfigurasi import Konfigurasi
    from hp_dokumen.sapu.bot import _sapu

    hasil = _sapu(_pengaturan(tmp_path), Konfigurasi.muat(), _drive(),
                  lambda *a: None, (1, 2026), False)
    assert any("TIDAK ADA order sheet" in m for m in hasil.masalah)
