"""Sheet REKAP INVOICE: satu baris per invoice yang terbit."""
from datetime import date

import pytest

from hp_dokumen.catatan_penjualan import Catatan
from hp_dokumen.sapu.tulis_rekap_invoice import (
    JUDUL_REKAP, TAB_REKAP, PenulisRekapInvoice, baris_rekap,
)
from tests.test_tulis_laporan import SambunganPalsu, _catatan


def _penulis(isi=None):
    s = SambunganPalsu(isi if isi is not None else {TAB_REKAP: [JUDUL_REKAP]})
    return PenulisRekapInvoice(s, "id"), s


def test_baris_memakai_urutan_kolom_judulnya():
    c = _catatan(total=5_000_000.0)
    c.nomor = "0391026"
    b = baris_rekap(c, tab_po="PO 28 Okt - Joy Baby", pt="DPM",
                    subtotal=6_000_000.0, persen="16.67%", cara_bayar="CBD")
    assert len(b) == len(JUDUL_REKAP)
    k = dict(zip(JUDUL_REKAP, b))
    assert k["No Invoice"] == "0391026"
    assert k["Customer"] == "JOY BABY"
    assert k["PT"] == "DPM"
    assert k["Qty"] == 15
    assert k["Total"] == pytest.approx(5_000_000.0)
    assert k["Cara Bayar"] == "CBD"


def test_diskon_adalah_subtotal_dikurangi_total():
    c = _catatan(total=5_000_000.0)
    b = baris_rekap(c, subtotal=6_500_000.0)
    assert dict(zip(JUDUL_REKAP, b))["Diskon"] == pytest.approx(1_500_000.0)


def test_subtotal_kosong_tidak_memunculkan_diskon_palsu():
    """Tanpa subtotal, diskon DIKOSONGKAN - bukan ditulis sebesar Total."""
    b = baris_rekap(_catatan(total=5_000_000.0))
    k = dict(zip(JUDUL_REKAP, b))
    assert k["Diskon"] == "" and k["Subtotal"] == ""


def test_invoice_yang_sudah_tercatat_dilewati():
    p, s = _penulis()
    assert p.catat(_catatan())
    p._kunci = None
    assert p.catat(_catatan()) == ""
    baris = [b for b in s.isi[TAB_REKAP][1:] if b]
    assert len(baris) == 1


def test_paksa_MENGGANTI_bukan_menggandakan():
    p, s = _penulis()
    p.catat(_catatan(total=5_000_000.0))
    p.catat(_catatan(total=7_000_000.0), paksa=True)
    baris = [b for b in s.isi[TAB_REKAP][1:] if b and str(b[0]).strip()]
    assert len(baris) == 1, "revisi harus mengganti, bukan menambah"
    assert float(baris[0][10]) == pytest.approx(7_000_000.0)


@pytest.mark.parametrize("judul", ["Sheet1", "DATA_INVOICE", "LAP OKT",
                                   "TAGIHAN", "rekap invoice"])
def test_menolak_tab_selain_REKAP_INVOICE(judul):
    p, _ = _penulis()
    with pytest.raises(ValueError):
        p._periksa_tab(judul)


def test_tab_dibuat_sendiri_lengkap_dengan_judul_kolom():
    """Hanya di berkas rekap ini - berkas yang isinya memang milik bot."""
    p, s = _penulis({"Untitled": [[]]})
    p.catat(_catatan())
    assert TAB_REKAP in s.isi
    assert s.isi[TAB_REKAP][0] == JUDUL_REKAP
