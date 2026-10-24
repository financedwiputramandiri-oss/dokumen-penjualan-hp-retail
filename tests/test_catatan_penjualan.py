"""Baris untuk DATA_INVOICE dan DATA_ARTIKEL di laporan penjualan.

Permintaan Yosua 24 Oktober 2026. Yang paling mahal kalau salah bukan
bentuk barisnya, melainkan: angka di laporan penjualan berbeda dari
fakturnya, baris masuk dua kali saat PO direvisi, atau tab laporan
bulanan Yosua ikut tertimpa.
"""
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from hp_dokumen.catatan_penjualan import (JUDUL_ARTIKEL, JUDUL_INVOICE,
                                          NomorKosong, periksa, susun)
from hp_dokumen.sapu.tulis_catatan import TAB_DIIZINKAN, PenulisCatatan


def _baris(kode, nama, qty, harga, nett):
    return SimpleNamespace(kode=kode, deskripsi=nama, qty=qty,
                           harga=harga, kotor=qty * harga, nett=nett)


def _bahan(kena_ppn=True):
    order = SimpleNamespace(customer_kunci="Joy Baby")
    baris = [_baris("42057.1.AT.S", "Hoodie Set Small", 9, 69000, 466_000.0),
             _baris("42057.1.AT.M", "Hoodie Set Medium", 5, 74000, 288_000.0)]
    total = sum(b.nett for b in baris)
    dpp = total / 1.11 if kena_ppn else total
    hasil = {"nett": total, "dpp": dpp, "ppn": total - dpp,
             "termin_hari": 30, "jatuh_tempo": date(2026, 11, 18),
             "kena_ppn": kena_ppn}
    return order, baris, hasil, total


def test_bentuk_baris_mengikuti_judul_kolom_di_sheet():
    order, baris, hasil, _ = _bahan()
    c = susun(order, None, baris, hasil, nomor="0010826",
              tanggal=date(2026, 10, 19))
    assert len(c.baris_invoice()) == len(JUDUL_INVOICE)
    assert all(len(a) == len(JUDUL_ARTIKEL) for a in c.baris_artikel())


def test_jumlah_artikel_sama_dengan_total_invoice():
    """Kolom Jumlah berisi NETT, bukan qty x harga.

    Kalau diisi nilai kotor, kedua tab selalu beda sebesar diskon dan
    tidak ada yang tahu mana yang benar.
    """
    order, baris, hasil, total = _bahan()
    c = susun(order, None, baris, hasil, nomor="0010826")
    assert sum(a[7] for a in c.baris_artikel()) == pytest.approx(total)
    assert periksa(c) == []


def test_nomor_kosong_ditolak():
    order, baris, hasil, _ = _bahan()
    for nomor in ("", "   ", "________", "---"):
        with pytest.raises(NomorKosong):
            susun(order, None, baris, hasil, nomor=nomor)


def test_mtn_tanpa_ppn_dpp_sama_dengan_total():
    order, baris, hasil, total = _bahan(kena_ppn=False)
    c = susun(order, None, baris, hasil, nomor="FA-01/10/2026")
    assert c.ppn == 0
    assert c.dpp == pytest.approx(total)
    assert periksa(c) == []


def test_periksa_menangkap_angka_yang_tidak_cocok():
    order, baris, hasil, _ = _bahan()
    hasil["nett"] = hasil["nett"] + 1_000_000      # sengaja dirusak
    c = susun(order, None, baris, hasil, nomor="0010826")
    assert any("DATA_ARTIKEL" in p for p in periksa(c))


def test_nama_customer_dipakai_kalau_ada_padanannya():
    order, baris, hasil, _ = _bahan()
    c = susun(order, None, baris, hasil, nomor="0010826",
              nama_customer="PT JOY BABY SEJAHTERA")
    assert c.customer == "PT JOY BABY SEJAHTERA"
    assert all(a[2] == "PT JOY BABY SEJAHTERA" for a in c.baris_artikel())


def test_tanpa_padanan_memakai_nama_tab():
    order, baris, hasil, _ = _bahan()
    c = susun(order, None, baris, hasil, nomor="0010826", nama_customer="  ")
    assert c.customer == "Joy Baby"


# --------------------------------------------------------------- pagar
class _SambunganPalsu:
    """Tiruan Sheets API — tidak menyentuh Google sama sekali."""

    def __init__(self, tab=("DATA_INVOICE", "DATA_ARTIKEL"), nomor=()):
        self._tab = list(tab)
        self._nomor = list(nomor)
        self.ditulis: list[tuple[str, int]] = []
        self.sheets = self

    # bentuk rantai panggilan Google dipalsukan seadanya
    def nama_tab(self, _id):
        return list(self._tab)

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, spreadsheetId, range):
        self._range = range
        return self

    def append(self, spreadsheetId, range, valueInputOption,
               insertDataOption, body):
        judul = range.split("'")[1]
        self.ditulis.append((judul, len(body["values"])))
        return SimpleNamespace(execute=lambda: {})

    def execute(self):
        return {"values": [[n] for n in self._nomor]}


def _catatan(nomor="0010826"):
    order, baris, hasil, _ = _bahan()
    return susun(order, None, baris, hasil, nomor=nomor)


def test_hanya_dua_tab_itu_yang_boleh_ditulis():
    p = PenulisCatatan(_SambunganPalsu(), "id")
    for terlarang in ("LAP OKT", "BUKU OKT", "ARTIKEL OKT", "TAGIHAN",
                      "BOT_REKAP", "Sheet1"):
        with pytest.raises(ValueError, match="Menolak menulis"):
            p._periksa_tab(terlarang)
    for boleh in TAB_DIIZINKAN:
        p._periksa_tab(boleh)


def test_tab_yang_belum_ada_TIDAK_dibuat_sendiri():
    p = PenulisCatatan(_SambunganPalsu(tab=("LAP OKT",)), "id")
    with pytest.raises(ValueError, match="HARUS dibuat lebih dulu"):
        p.catat(_catatan())


def test_nomor_yang_sudah_tercatat_dilewati():
    s = _SambunganPalsu(nomor=["0010826"])
    hasil = PenulisCatatan(s, "id").catat(_catatan("0010826"))
    assert "dilewati" in hasil
    assert s.ditulis == []          # tidak ada yang ditulis sama sekali


def test_nomor_baru_ditulis_artikel_dulu_baru_invoice():
    """Urutannya penting: kalau dibalik lalu artikelnya gagal, laporan
    memuat invoice tanpa rincian dan nomornya terlanjur dianggap ada."""
    s = _SambunganPalsu(nomor=["0009999"])
    hasil = PenulisCatatan(s, "id").catat(_catatan("0010826"))
    assert "tercatat" in hasil
    assert [t[0] for t in s.ditulis] == ["DATA_ARTIKEL", "DATA_INVOICE"]
    assert s.ditulis[0][1] == 2     # dua baris artikel
    assert s.ditulis[1][1] == 1
