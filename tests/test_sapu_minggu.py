"""Lingkup sapuan per MINGGU — permintaan Yosua 6 Oktober 2026.

Yang dikunci di sini adalah empat hal yang kalau salah tidak menimbulkan
galat apa pun, cuma dokumen yang diam-diam tidak pernah terbit.
"""
from datetime import date

import pytest

from hp_dokumen.sapu.minggu import (bulan_tersentuh, minggu_dari,
                                    minggu_sekarang, sebutan, tab_dalam_minggu,
                                    tahun_tersentuh, tanggal_tab, urai_minggu)


def test_minggu_mulai_senin_berakhir_minggu():
    senin, mgg = minggu_dari(date(2026, 10, 6))      # Selasa
    assert senin == date(2026, 10, 5) and senin.weekday() == 0
    assert mgg == date(2026, 10, 11) and mgg.weekday() == 6


def test_hari_senin_sendiri_tidak_mundur_seminggu():
    senin, mgg = minggu_dari(date(2026, 10, 5))
    assert senin == date(2026, 10, 5) and mgg == date(2026, 10, 11)


def test_minggu_yang_menyeberang_bulan_menyentuh_DUA_bulan():
    """Jebakan utama: menyaring ke satu bulan melewatkan separuh minggunya."""
    senin, mgg = minggu_dari(date(2026, 9, 30))      # 28 Sep - 4 Okt
    assert bulan_tersentuh(senin, mgg) == [(9, 2026), (10, 2026)]


def test_minggu_yang_menyeberang_tahun_menyentuh_DUA_tahun():
    senin, mgg = minggu_dari(date(2025, 12, 31))     # 29 Des 2025 - 4 Jan 2026
    assert tahun_tersentuh(senin, mgg) == [2025, 2026]


def test_tab_di_luar_minggu_dibuang():
    senin, mgg = minggu_dari(date(2026, 9, 29))      # 28 Sep - 4 Okt
    assert tab_dalam_minggu("PO 28 September - Haritsa", senin, mgg, 2026)
    assert not tab_dalam_minggu("PO 11 September - Katamama (Tapos)",
                                senin, mgg, 2026)


def test_tab_yang_tanggalnya_TIDAK_TERBACA_tetap_ikut():
    """Melewatkan PO jauh lebih mahal daripada menyapu satu tab berlebih.

    `Sheet4` sampai `Sheet9` memang berisi PO sungguhan — CLAUDE.md bagian 18.
    """
    senin, mgg = minggu_dari(date(2026, 9, 29))
    for nama in ("Sheet4", "Order Jastip Ci Ratna", "DHAWAFEST BAZAAR"):
        assert tab_dalam_minggu(nama, senin, mgg, 2026), nama


def test_tahun_diambil_dari_order_sheet_kalau_tab_tidak_menulisnya():
    assert tanggal_tab("PO 28 September - Haritsa", 2026) == date(2026, 9, 28)
    # Tahun di nama tab MENANG atas tahun order sheet.
    assert tanggal_tab("PO 13 Agustus 2026 - Dunia Bayi", 2025) == date(2026, 8, 13)


def test_tanggal_tab_yang_tidak_ada_di_kalender_tidak_meledak():
    assert tanggal_tab("PO 31 September - Entah", 2026) is None


def test_urai_minggu_menolak_salah_ketik():
    """Menerbitkan dokumen periode yang salah lebih mahal daripada ditolak."""
    with pytest.raises(ValueError):
        urai_minggu("minggu lalu")
    with pytest.raises(ValueError):
        urai_minggu("2026-13-01")


def test_urai_minggu_menerima_tanggal_di_dalam_minggunya():
    assert urai_minggu("2026-10-07") == (date(2026, 10, 5), date(2026, 10, 11))


def test_tanpa_pilihan_memakai_minggu_berjalan():
    assert urai_minggu("", date(2026, 10, 6)) == minggu_sekarang(date(2026, 10, 6))


def test_sebutan_terbaca_orang():
    assert sebutan(date(2026, 10, 5), date(2026, 10, 11)) == "5-11 Oktober 2026"
    assert sebutan(date(2026, 9, 28), date(2026, 10, 4)) == \
        "28 September - 4 Oktober 2026"


# ------------------------------------------------- rentang tanggal BEBAS
# Permintaan Yosua 6 Oktober 2026: "sapu dari 21 September sampai 30
# September". Bukan satu minggu penuh, jadi lingkupnya digeneralkan.

def test_rentang_bebas_dibaca_benar():
    from hp_dokumen.sapu.minggu import urai_rentang
    assert urai_rentang("2026-09-21", "2026-09-30") == (
        date(2026, 9, 21), date(2026, 9, 30))


def test_rentang_TERBALIK_ditolak():
    """Rentang terbalik menghasilkan nol PO tanpa galat apa pun, dan itu
    terlihat persis seperti sapuan yang wajar."""
    from hp_dokumen.sapu.minggu import urai_rentang
    with pytest.raises(ValueError, match="terbalik"):
        urai_rentang("2026-09-30", "2026-09-21")


def test_rentang_salah_ketik_ditolak():
    from hp_dokumen.sapu.minggu import urai_rentang
    for a, b in (("21 September", "2026-09-30"), ("2026-09-21", ""),
                 ("2026-02-31", "2026-09-30")):
        with pytest.raises(ValueError):
            urai_rentang(a, b)


def test_tab_disaring_menurut_rentang_bukan_minggu():
    from hp_dokumen.sapu.minggu import tab_dalam_rentang
    a, b = date(2026, 9, 21), date(2026, 9, 30)
    assert tab_dalam_rentang("PO 21 September - Buchi Kids", a, b, 2026)
    assert tab_dalam_rentang("PO 28 September - Haritsa", a, b, 2026)
    assert not tab_dalam_rentang("PO 14 September - Baby Wise", a, b, 2026)
    assert not tab_dalam_rentang("PO 05 Okt - Baby Wise", a, b, 2026)


def test_sebutan_rentang_dalam_satu_bulan():
    assert sebutan(date(2026, 9, 21), date(2026, 9, 30)) == "21-30 September 2026"
