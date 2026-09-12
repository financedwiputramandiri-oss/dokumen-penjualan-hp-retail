"""Tes pengunggah dokumen ke Drive, memakai sambungan tiruan.

Tidak menyentuh Google sama sekali. Yang diuji adalah keputusannya: folder apa
yang dibuat, berkas mana yang ditimpa, dan apa yang terjadi kalau Google
menolak.
"""
import pytest

from buat_contoh import buat_contoh
from hp_dokumen.konfigurasi import Konfigurasi
from hp_dokumen.nilai_bersih import tentukan_nett
from hp_dokumen.pemindai import baca_order_sheet
from hp_dokumen.sapu.draf import BARU, buat_draf
from hp_dokumen.sapu.kondisi import sidik_dari_order
from hp_dokumen.sapu.unggah import PengunggahDokumen


class SambunganPalsu:
    """Meniru Sambungan seperlunya, dan mencatat apa yang diminta kepadanya."""

    def __init__(self, folder_gagal=(), berkas_gagal=()):
        self.folder: dict[tuple[str, str], str] = {}
        self.berkas: dict[tuple[str, str], int] = {}   # (folder, nama) -> berapa kali
        self.panggilan_folder = 0
        self.folder_gagal = set(folder_gagal)
        self.berkas_gagal = set(berkas_gagal)

    def buat_folder_kalau_belum_ada(self, nama, induk):
        self.panggilan_folder += 1
        if nama in self.folder_gagal:
            return None
        kunci = (induk, nama)
        self.folder.setdefault(kunci, f"id_{len(self.folder) + 1}")
        return self.folder[kunci]

    def unggah_berkas(self, berkas, id_folder):
        if berkas.name in self.berkas_gagal:
            return None
        kunci = (id_folder, berkas.name)
        self.berkas[kunci] = self.berkas.get(kunci, 0) + 1
        return f"berkas_{len(self.berkas)}"


@pytest.fixture
def draf(tmp_path):
    cfg = Konfigurasi.muat()
    berkas = buat_contoh(tmp_path / "contoh.xlsx")
    o = next(x for x in baca_order_sheet(berkas, cfg.customer, tahun_bawaan=2026) if x.qty > 0)
    k = tentukan_nett(o, cfg.customer.cari(o.nama_tab))
    s = sidik_dari_order("A", "Order Sheet Contoh", o.nama_tab, o, k, None)
    return buat_draf(cfg, o, k, None, s, BARU, tmp_path / "draf")


def test_semua_berkas_naik(draf):
    s = SambunganPalsu()
    hasil = PengunggahDokumen(s, "INDUK").unggah(draf, "Order Sheet Contoh")
    assert hasil.jumlah == len(draf.berkas)
    assert hasil.gagal == []
    assert hasil.tautan.endswith(hasil.id_folder)


def test_folder_bertingkat_sesuai_order_sheet_dan_po(draf):
    s = SambunganPalsu()
    PengunggahDokumen(s, "INDUK").unggah(draf, "Order Sheet Contoh")
    dibuat = [nama for (_, nama) in s.folder]
    assert "Order Sheet Contoh" in dibuat
    assert draf.tab in dibuat
    # folder PO harus berada DI DALAM folder order sheet, bukan di induk
    id_sheet = s.folder[("INDUK", "Order Sheet Contoh")]
    assert (id_sheet, draf.tab) in s.folder


def test_folder_tidak_ditanyakan_berulang(draf):
    """Dua PO dari order sheet yang sama tidak boleh menanyakan folder bulan
    itu dua kali — pemborosan panggilan API."""
    s = SambunganPalsu()
    peng = PengunggahDokumen(s, "INDUK")
    peng.unggah(draf, "Order Sheet Contoh")
    sesudah_pertama = s.panggilan_folder
    peng.unggah(draf, "Order Sheet Contoh")
    # hanya folder PO yang ditanyakan lagi (dan itu pun sudah tersimpan)
    assert s.panggilan_folder == sesudah_pertama


def test_unggah_ulang_menimpa_bukan_menambah(draf):
    s = SambunganPalsu()
    peng = PengunggahDokumen(s, "INDUK")
    peng.unggah(draf, "Order Sheet Contoh")
    peng.unggah(draf, "Order Sheet Contoh")
    assert len(s.berkas) == len(draf.berkas), "berkas bertambah, seharusnya ditimpa"
    assert all(n == 2 for n in s.berkas.values())


def test_folder_gagal_dibuat_dilaporkan_bukan_didiamkan(draf):
    s = SambunganPalsu(folder_gagal={"Order Sheet Contoh"})
    hasil = PengunggahDokumen(s, "INDUK").unggah(draf, "Order Sheet Contoh")
    assert hasil.jumlah == 0
    assert hasil.gagal and "tidak bisa dibuat" in hasil.gagal[0]


def test_satu_berkas_gagal_sisanya_tetap_naik(draf):
    nama_gagal = draf.berkas[0].name
    s = SambunganPalsu(berkas_gagal={nama_gagal})
    hasil = PengunggahDokumen(s, "INDUK").unggah(draf, "Order Sheet Contoh")
    assert hasil.jumlah == len(draf.berkas) - 1
    assert any(nama_gagal in x for x in hasil.gagal)


def test_sebab_kegagalan_ikut_tercatat(draf):
    """Pesan "gagal" tanpa sebab tidak bisa ditindaklanjuti siapa pun.

    Pernah terjadi: sapuan pertama Yosua menampilkan "0 berkas naik ke Drive"
    untuk puluhan PO, tanpa satu pun petunjuk kenapa.
    """
    class Menolak(SambunganPalsu):
        def unggah_berkas(self, berkas, id_folder):
            raise RuntimeError("storageQuotaExceeded: contoh sebab dari Google")

    hasil = PengunggahDokumen(Menolak(), "INDUK").unggah(draf, "Order Sheet Contoh")
    assert hasil.jumlah == 0
    assert hasil.gagal
    assert all("storageQuotaExceeded" in x for x in hasil.gagal), hasil.gagal


def test_folder_gagal_dibuat_sebabnya_ikut(draf):
    class FolderMenolak(SambunganPalsu):
        def buat_folder_kalau_belum_ada(self, nama, induk):
            raise RuntimeError("insufficientFilePermissions: contoh sebab")

    hasil = PengunggahDokumen(FolderMenolak(), "INDUK").unggah(draf, "Order Sheet Contoh")
    assert hasil.gagal and "insufficientFilePermissions" in hasil.gagal[0]
