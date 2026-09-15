"""Tes pemeriksa persiapan bot. Tidak menyentuh Google sama sekali.

Yang diuji terutama: kalau ada yang kurang, pesan perbaikannya menyebut
langkah yang benar. Pesan "akses ditolak" saja tidak bisa ditindaklanjuti
orang yang tidak akrab dengan teknologi.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from hp_dokumen.sapu.pemeriksa import cetak, periksa


@dataclass
class PengaturanPalsu:
    berkas_kredensial: Path
    folder: list = field(default_factory=list)
    folder_laporan_id: str = "L"
    folder_dokumen_id: str = "D"
    sheet_otomatisasi_id: str = "S"


class Berkas:
    mime = "application/vnd.google-apps.spreadsheet"


class SambunganPalsu:
    def __init__(self, _berkas, folder_gagal=()):
        self.folder_gagal = set(folder_gagal)

    def isi_folder(self, id_folder):
        if id_folder in self.folder_gagal:
            raise PermissionError("akses ditolak")
        return [Berkas(), Berkas()]

    def nama_tab(self, _id):
        return ["BOT_STATUS"]


@pytest.fixture
def kunci(tmp_path):
    p = tmp_path / "kredensial_bot.json"
    p.write_text(json.dumps({"client_email": "bot@proyek.iam.gserviceaccount.com"}))
    return p


def _atur(kunci, **ubah):
    d = dict(folder=[{"nama": "Order Sheet 2026", "id": "F26"}])
    d.update(ubah)
    return PengaturanPalsu(berkas_kredensial=kunci, **d)


def test_semua_siap(kunci):
    hasil = periksa(_atur(kunci), buat_sambungan=SambunganPalsu)
    assert all(h.lulus for h in hasil), [h.pesan for h in hasil if not h.lulus]


def test_kunci_belum_ada_menyebut_langkah_4(tmp_path):
    hasil = periksa(_atur(tmp_path / "tidak_ada.json"), buat_sambungan=SambunganPalsu)
    assert len(hasil) == 1, "pemeriksaan harus berhenti kalau kuncinya belum ada"
    assert not hasil[0].lulus
    assert "Langkah 4" in hasil[0].perbaikan


def test_kunci_rusak_tidak_membuat_program_mati(tmp_path):
    p = tmp_path / "kredensial_bot.json"
    p.write_text("{ini bukan json")
    hasil = periksa(_atur(p), buat_sambungan=SambunganPalsu)
    assert not hasil[0].lulus and "tidak terbaca" in hasil[0].pesan


def test_berkas_json_yang_salah_dikenali(tmp_path):
    p = tmp_path / "kredensial_bot.json"
    p.write_text(json.dumps({"apa": "saja"}))
    hasil = periksa(_atur(p), buat_sambungan=SambunganPalsu)
    assert not hasil[0].lulus and "bukan kunci akun layanan" in hasil[0].pesan


def test_folder_order_sheet_belum_dishare_menyebut_viewer_dan_pemilik(kunci):
    def gagal(b):
        return SambunganPalsu(b, folder_gagal={"F26"})
    hasil = periksa(_atur(kunci), buat_sambungan=gagal)
    h = next(x for x in hasil if "Order Sheet 2026" in x.nama)
    assert not h.lulus
    assert "Viewer" in h.perbaikan
    assert "pemilik order sheet" in h.perbaikan
    assert "bot@proyek.iam.gserviceaccount.com" in h.perbaikan


def test_folder_dokumen_belum_dishare_menyebut_EDITOR(kunci):
    def gagal(b):
        return SambunganPalsu(b, folder_gagal={"D"})
    hasil = periksa(_atur(kunci), buat_sambungan=gagal)
    h = next(x for x in hasil if x.nama == "Folder dokumen")
    assert not h.lulus and "EDITOR" in h.perbaikan


def test_folder_tujuan_kosong_diberi_tahu(kunci):
    hasil = periksa(_atur(kunci, folder_dokumen_id=""), buat_sambungan=SambunganPalsu)
    h = next(x for x in hasil if x.nama == "Folder dokumen")
    assert not h.lulus and "folder_dokumen_id" in h.perbaikan


def test_cetak_menampilkan_daftar_perbaikan(kunci):
    baris = []
    def gagal(b):
        return SambunganPalsu(b, folder_gagal={"F26"})
    siap = cetak(periksa(_atur(kunci), buat_sambungan=gagal), tulis=baris.append)
    teks = "\n".join(baris)
    assert siap is False
    assert "PERLU DIBERESKAN" in teks
    assert "Viewer" in teks


# --------------------------------------------- API mati vs masalah izin
GALAT_API_MATI = (
    "<HttpError 403 when requesting https://sheets.googleapis.com/v4/"
    "spreadsheets/1qkd... returned \"Google Sheets API has not been used in "
    "project 76910858898 before or it is disabled. Enable it by visiting "
    "https://console.developers.google.com/apis/api/sheets.googleapis.com/"
    "overview?project=76910858898 then retry.\". Details: 'reason': "
    "'SERVICE_DISABLED'>"
)


class SambunganApiMati(SambunganPalsu):
    """Meniru keadaan nyata: Drive jalan, Sheets API belum dinyalakan."""

    def nama_tab(self, _id):
        raise RuntimeError(GALAT_API_MATI)


def test_api_belum_dinyalakan_tidak_disuruh_share_ulang(kunci):
    """Kalau sebabnya API mati, saran 'Share sebagai Editor' menyesatkan.

    Orang akan men-Share ulang berkas yang izinnya sudah benar, dan
    masalahnya tidak akan pernah selesai.
    """
    hasil = periksa(_atur(kunci), buat_sambungan=SambunganApiMati)
    h = next(x for x in hasil if x.nama == "Sheet OTOMATISASI")
    assert not h.lulus
    assert "Google Sheets API" in h.perbaikan
    assert "ENABLE" in h.perbaikan
    assert "Share" not in h.perbaikan.replace("jangan men-Share", "")


def test_masalah_izin_tetap_disuruh_share(kunci):
    """Kebalikannya: galat izin biasa harus tetap menyarankan Share."""
    def gagal(b):
        return SambunganPalsu(b, folder_gagal={"D"})
    hasil = periksa(_atur(kunci), buat_sambungan=gagal)
    h = next(x for x in hasil if x.nama == "Folder dokumen")
    assert "EDITOR" in h.perbaikan
    assert "ENABLE" not in h.perbaikan
