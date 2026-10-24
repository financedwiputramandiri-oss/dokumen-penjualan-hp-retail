"""Tulisan diskon di invoice diambil dari ANGKA KOLOM, bukan judul kolom.

Ditemukan 24 Oktober 2026 pada `PO 19 Okt - Joy Baby`: judul kolomnya
berbunyi `DISCOUNT CBD + 2%` padahal isi kolomnya 1,95%. Karena tulisan
diskon dipulihkan dari judul, faktur mencetak `19.96% + 2%` — DUA-DUANYA
meleset, padahal yang sebenarnya `20% + 1.95%`.

Totalnya tidak pernah salah (nilai bersih diambil dari kolomnya, Aturan 2),
jadi pencocokan LULUS dan tidak ada peringatan apa pun. Yang salah hanya
angka yang DIBACA CUSTOMER — kelas kesalahan yang sama dengan CLAUDE.md
bagian 43, dan yang paling mudah lolos karena nilai selnya benar.
"""
from types import SimpleNamespace

import pytest

from hp_dokumen.dokumen.invoice import _persen_tertulis
from hp_dokumen.model import KeputusanNett


def _order(kotor: float, nett_top: float, nett_cbd: float, judul: str):
    """Satu order sederhana: satu blok, satu baris, dua kolom nett."""
    kolom = [
        SimpleNamespace(jenis="TOP", kunci="TOP@AC", judul="TOTAL VALUE",
                        huruf="AC", kolom=29),
        SimpleNamespace(jenis="CBD", kunci="CBD@AD", judul=judul,
                        huruf="AD", kolom=30),
    ]
    baris = SimpleNamespace(nilai_kotor=kotor,
                            nett={"TOP@AC": nett_top, "CBD@AD": nett_cbd})
    blok = SimpleNamespace(baris=[baris], tata=SimpleNamespace(nett=kolom))
    return SimpleNamespace(blok=[blok], semua_baris=[baris],
                           kolom_nett=lambda: kolom)


def _keputusan(judul: str, nett: float, cara: str = "CBD"):
    return KeputusanNett(cara_bayar=cara, kolom="CBD@AD",
                         kolom_sumber=judul, nett_total=nett,
                         jumlah_baris=1, terisi_cbd=1, terisi_cod=0)


def test_judul_berbohong_tulisan_diskon_tetap_angka_sebenarnya():
    """Joy Baby: judul bilang 2%, kolomnya 1,95%. Yang dicetak harus 1,95%."""
    kotor = 19_660_300.0
    top = kotor * 0.80                 # diskon dasar 20% persis
    cbd = top * (1 - 0.0195)           # tambahan SEBENARNYA 1,95%
    judul = "DISCOUNT \nCBD + 2%"

    teks, angka = _persen_tertulis(_order(kotor, top, cbd, judul),
                                   _keputusan(judul, cbd), None)

    assert teks == "20% + 1.95%"
    assert angka is None
    assert "19.96%" not in teks        # yang dulu salah dicetak


def test_judul_jujur_hasilnya_tidak_berubah():
    """Katamama: judul 1,5% dan kolomnya memang 1,5% — harus tetap 22% + 1.5%."""
    kotor = 27_332_900.0
    top = kotor * 0.78
    cbd = top * (1 - 0.015)
    judul = "DISCOUNT CBD + 1,5%"

    teks, _ = _persen_tertulis(_order(kotor, top, cbd, judul),
                               _keputusan(judul, cbd), None)
    assert teks == "22% + 1.5%"


def test_order_TOP_tetap_memakai_persen_efektif():
    """Tanpa potongan tambahan, bentuknya satu angka — bukan 'x% + y%'."""
    kotor = 1_000_000.0
    top = kotor * 0.75
    judul = "TOTAL VALUE"

    teks, angka = _persen_tertulis(_order(kotor, top, 0.0, judul),
                                   _keputusan(judul, top, cara="TOP"), None)
    assert teks is None
    assert angka == pytest.approx(0.25)


def test_kolom_TOP_nol_tidak_membuat_rumus_meledak():
    """Kalau kolom TOP kosong, kembali ke cara lama — jangan bagi nol."""
    kotor = 1_000_000.0
    judul = "DISCOUNT CBD + 2%"
    cbd = kotor * 0.75 * 0.98

    teks, _ = _persen_tertulis(_order(kotor, 0.0, cbd, judul),
                               _keputusan(judul, cbd), None)
    assert teks is not None and "%" in teks
