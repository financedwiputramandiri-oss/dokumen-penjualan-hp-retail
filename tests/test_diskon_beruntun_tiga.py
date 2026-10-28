"""Judul kolom nett boleh memuat LEBIH DARI SATU potongan tambahan.

Contoh nyata: Caroline Mom, Baby & Gift Shop, Oktober 2026 — diskon
`25% + 2% + 2%`. Dulu hanya persen PERTAMA yang dibaca dari judul kolom,
jadi potongan kedua hilang dari tulisan diskon di invoice dan diskon
dasarnya dipulihkan dengan pembagi yang salah (26.53% + 2%, bukan
25% + 2% + 2%).

Potongannya BERUNTUN, bukan dijumlahkan — aturan yang sama dengan
bagian 22.
"""
import pytest

from hp_dokumen.dokumen.invoice import LEBAR, lebar_menyesuaikan
from hp_dokumen.nilai_bersih import daftar_tarif_tertulis, tarif_tambahan_tertulis


def test_semua_persen_di_judul_terbaca():
    assert daftar_tarif_tertulis("DISCOUNT  CBD + 2% + 2%") == [0.02, 0.02]
    assert daftar_tarif_tertulis("DISCOUNT CBD + 1.5%") == [0.015]
    assert daftar_tarif_tertulis("TOTAL VALUE") == []


def test_tarif_tambahan_digabung_beruntun_bukan_dijumlahkan():
    gabungan = tarif_tambahan_tertulis("DISCOUNT  CBD + 2% + 2%")
    assert gabungan == pytest.approx(1 - 0.98 * 0.98)   # 3,96%
    assert gabungan != pytest.approx(0.04)              # bukan 2% + 2%


def test_satu_potongan_tidak_berubah_perilakunya():
    assert tarif_tambahan_tertulis("DISCOUNT CBD + 1.5%") == pytest.approx(0.015)
    assert tarif_tambahan_tertulis("TOTAL VALUE") is None


def test_kolom_diskon_melebar_untuk_tulisan_beruntun():
    """Tulisan diskon yang panjang tidak boleh terpotong.

    Nilai selnya SELALU benar, jadi hanya lebar kolomnya yang bisa salah —
    dan faktur yang memotongnya memberi tahu customer persen yang BERBEDA
    dari yang dipakai menghitung.
    """
    class B:
        kode = "OB.SS.1.S"
        deskripsi = "SoftAir Short Set - New Baby Size"

    baris = [B()]
    polos = lebar_menyesuaikan(baris)
    panjang = lebar_menyesuaikan(baris, tulisan_diskon="25% + 2% + 2%")
    assert panjang[6] > polos[6]
    assert panjang[6] >= len("25% + 2% + 2%") * 1.0
    # Jatah A..H tetap di bawah batas, jadi dokumennya masih muat A4 tegak.
    from hp_dokumen.dokumen.invoice import GAYA_PER_ARTIKEL
    assert sum(panjang.values()) <= GAYA_PER_ARTIKEL.maks_jatah
