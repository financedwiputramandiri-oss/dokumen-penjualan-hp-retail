"""Tes draf otomatis: kapan dokumen dibuat, kapan dibuat ULANG, kapan tidak.

Aturan yang diuji di sini berasal dari penjelasan Yosua 12 September 2026:
ATO terisi berarti final untuk pertama kali, tapi revisi tetap wajib diikuti
dengan membuat ulang dokumennya memakai angka terbaru.
"""
from dataclasses import replace
from pathlib import Path

import pytest

from buat_contoh import buat_contoh
from hp_dokumen.konfigurasi import Konfigurasi
from hp_dokumen.nilai_bersih import tentukan_nett
from hp_dokumen.pemindai import baca_order_sheet
from hp_dokumen.sapu.draf import BARU, REVISI, arsipkan, buat_draf, perlu_draf
from hp_dokumen.sapu.kondisi import sidik_dari_order


@pytest.fixture
def cfg():
    return Konfigurasi.muat()


@pytest.fixture
def bahan(tmp_path, cfg):
    """Satu PO contoh beserta sidik jarinya."""
    berkas = buat_contoh(tmp_path / "contoh.xlsx")
    orders = baca_order_sheet(berkas, cfg.customer, tahun_bawaan=2026)
    o = next(x for x in orders if x.qty > 0)
    k = tentukan_nett(o, cfg.customer.cari(o.nama_tab))
    s = sidik_dari_order("sheet1", "Order Sheet Contoh", o.nama_tab, o, k, None)
    return o, k, s


# ----------------------------------------------------------- kapan dibuat
def test_ato_belum_terisi_tidak_membuat_draf(tmp_path, bahan):
    _, _, s = bahan
    kosong = replace(s, ato_terisi=False)
    assert perlu_draf(None, kosong, tmp_path / "belum_ada") is None


def test_po_baru_dengan_ato_terisi_dibuatkan_draf(tmp_path, bahan):
    _, _, s = bahan
    assert perlu_draf(None, s, tmp_path / "belum_ada") == BARU


def test_tidak_ada_perubahan_tidak_dibuat_ulang(tmp_path, bahan, cfg):
    o, k, s = bahan
    hasil = buat_draf(cfg, o, k, None, s, BARU, tmp_path)
    assert hasil.alasan == BARU
    assert perlu_draf(s, s, hasil.folder) is None


# ---------------------------------------------------------- kapan diulang
@pytest.mark.parametrize("ubah", [
    {"qty": 999},
    {"baris": 99},
    {"nett": 1234.0},
    {"kotor": 5678.0},
    {"cara_bayar": "COD"},
    {"sidik_qty": "beda"},
])
def test_revisi_membuat_dokumen_dibuat_ulang(tmp_path, bahan, cfg, ubah):
    o, k, s = bahan
    hasil = buat_draf(cfg, o, k, None, s, BARU, tmp_path)
    baru = replace(s, **ubah)
    assert perlu_draf(s, baru, hasil.folder) == REVISI


def test_rumus_berubah_saja_tidak_membuat_dokumen_diulang(tmp_path, bahan, cfg):
    """Rumus berubah tetap dilaporkan sebagai alarm, tapi isi dokumennya sama.

    Membuat ulang berkas yang isinya identik hanya membuat orang ragu mana
    yang terbaru.
    """
    o, k, s = bahan
    hasil = buat_draf(cfg, o, k, None, s, BARU, tmp_path)
    baru = replace(s, sidik_rumus="rumus_lain")
    assert perlu_draf(s, baru, hasil.folder) is None


def test_berkas_draf_hilang_dibuat_lagi(tmp_path, bahan, cfg):
    o, k, s = bahan
    hasil = buat_draf(cfg, o, k, None, s, BARU, tmp_path)
    for f in hasil.folder.glob("*.xlsx"):
        f.unlink()
    assert perlu_draf(s, s, hasil.folder) == BARU


# ------------------------------------------------------------- isi & arsip
def test_draf_berisi_ketiga_dokumen_yang_diminta(tmp_path, bahan, cfg):
    o, k, s = bahan
    hasil = buat_draf(cfg, o, k, None, s, BARU, tmp_path)
    gabung = " ".join(p.name for p in hasil.berkas)
    for wajib in ("INVOICE", "SURAT_JALAN", "FAKTUR_PAJAK"):
        assert wajib in gabung, f"{wajib} tidak dibuat"
    assert all(p.exists() and p.stat().st_size > 0 for p in hasil.berkas)


def test_draf_lama_diarsipkan_bukan_ditimpa(tmp_path, bahan, cfg):
    o, k, s = bahan
    pertama = buat_draf(cfg, o, k, None, s, BARU, tmp_path)
    jumlah_awal = len(list(pertama.folder.glob("*.xlsx")))

    baru = replace(s, qty=s.qty + 10)
    kedua = buat_draf(cfg, o, k, s, baru, REVISI, tmp_path)

    assert kedua.diarsipkan_ke is not None
    assert kedua.diarsipkan_ke.exists()
    assert len(list(kedua.diarsipkan_ke.glob("*.xlsx"))) == jumlah_awal
    assert len(list(kedua.folder.glob("*.xlsx"))) == jumlah_awal
    assert "_KEDALUWARSA" in str(kedua.diarsipkan_ke)


def test_ringkasan_revisi_menyebut_apa_yang_berubah(tmp_path, bahan, cfg):
    o, k, s = bahan
    buat_draf(cfg, o, k, None, s, BARU, tmp_path)
    baru = replace(s, qty=s.qty + 10, cara_bayar="COD")
    hasil = buat_draf(cfg, o, k, s, baru, REVISI, tmp_path)
    assert "DIBUAT ULANG" in hasil.ringkas()
    assert "qty" in hasil.ringkas()
    assert "cara bayar" in hasil.ringkas()


def test_arsipkan_folder_kosong_tidak_bikin_sampah(tmp_path):
    from datetime import datetime
    kosong = tmp_path / "tidak_ada"
    assert arsipkan(kosong, tmp_path / "_KEDALUWARSA", datetime.now()) is None
    assert not (tmp_path / "_KEDALUWARSA").exists()


def test_dua_arsip_di_detik_sama_tidak_saling_menelan(tmp_path, bahan, cfg):
    """Kalau nama arsipnya bentrok, draf lama tidak boleh masuk ke dalam
    arsip sebelumnya — semuanya harus tetap sejajar dan bisa ditemukan."""
    from datetime import datetime
    from dataclasses import replace as ganti
    o, k, s = bahan
    waktu = datetime(2026, 9, 12, 6, 0, 0)

    buat_draf(cfg, o, k, None, s, BARU, tmp_path, waktu=waktu)
    a = buat_draf(cfg, o, k, s, ganti(s, qty=s.qty + 1), REVISI, tmp_path, waktu=waktu)
    b = buat_draf(cfg, o, k, s, ganti(s, qty=s.qty + 2), REVISI, tmp_path, waktu=waktu)

    assert a.diarsipkan_ke != b.diarsipkan_ke
    assert a.diarsipkan_ke.parent == b.diarsipkan_ke.parent
    for arsip in (a.diarsipkan_ke, b.diarsipkan_ke):
        assert list(arsip.glob("*.xlsx")), f"{arsip} kosong"
        assert not list(arsip.glob("*/*.xlsx")), f"{arsip} menelan arsip lain"
