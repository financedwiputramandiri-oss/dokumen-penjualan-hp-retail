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
                                          kunci, periksa, susun)
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


def test_nomor_boleh_kosong_dan_penampung_dibersihkan():
    """Keputusan Yosua 24 Okt 2026: No Invoice dikosongkan.

    Nomor penampung dari pembuat dokumen ("________") tidak boleh ikut
    tertulis — kolomnya jadi penuh garis bawah yang tidak berarti apa-apa.
    """
    order, baris, hasil, _ = _bahan()
    for nomor in ("", "   ", "________", "---"):
        c = susun(order, None, baris, hasil, nomor=nomor)
        assert c.nomor == ""
        assert c.baris_invoice()[1] == ""
    c = susun(order, None, baris, hasil, nomor="0010826")
    assert c.baris_invoice()[1] == "0010826"


def test_kunci_dari_customer_dan_tanggal():
    """Karena nomor kosong, inilah satu-satunya pengenal barisnya."""
    order, baris, hasil, _ = _bahan()
    c = susun(order, None, baris, hasil, nomor="",
              nama_customer="jonni setiadi ", tanggal=date(2026, 10, 19))
    assert c.kunci == ("JONNI SETIADI", "19/10/2026")
    assert kunci("  Jonni Setiadi", "19/10/2026") == c.kunci


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

    def __init__(self, tab=("DATA_INVOICE", "DATA_ARTIKEL"), isi=None):
        self._tab = list(tab)
        self._isi = isi or {}
        self.ditulis: list[tuple[str, int]] = []
        self.dihapus: list[tuple[str, int]] = []
        self.sheets = self
        self._range = ""

    def nama_tab(self, _id):
        return list(self._tab)

    def spreadsheets(self):
        return self

    def values(self):
        return self

    def get(self, spreadsheetId, range=None, fields=None):
        self._range = range or ""
        self._fields = fields
        return self

    def append(self, spreadsheetId, range, valueInputOption,
               insertDataOption, body):
        self.ditulis.append((range.split("'")[1], len(body["values"])))
        return SimpleNamespace(execute=lambda: {})

    def batchUpdate(self, spreadsheetId, body):
        for r in body["requests"]:
            d = r["deleteDimension"]["range"]
            nama = next(k for k, v in self._gid().items()
                        if v == d["sheetId"])
            self.dihapus.append((nama, d["startIndex"] + 1))
        return SimpleNamespace(execute=lambda: {})

    def _gid(self):
        return {t: i for i, t in enumerate(self._tab)}

    def execute(self):
        if self._fields:
            return {"sheets": [{"properties": {"title": t, "sheetId": i}}
                               for i, t in enumerate(self._tab)]}
        judul = self._range.split("'")[1] if "'" in self._range else ""
        return {"values": self._isi.get(judul, [])}


def _catatan(cust="JONNI SETIADI", tgl=date(2026, 10, 14)):
    order, baris, hasil, _ = _bahan()
    return susun(order, None, baris, hasil, nomor="",
                 nama_customer=cust, tanggal=tgl)


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


def test_invoice_baru_ditulis_artikel_dulu_baru_invoice():
    """Urutannya penting: kalau dibalik lalu artikelnya gagal, laporan
    memuat invoice tanpa rincian."""
    s = _SambunganPalsu()
    hasil = PenulisCatatan(s, "id").catat(_catatan())
    assert "tercatat" in hasil
    assert [t[0] for t in s.ditulis] == ["DATA_ARTIKEL", "DATA_INVOICE"]
    assert s.ditulis[0][1] == 2 and s.ditulis[1][1] == 1
    assert s.dihapus == []


def test_revisi_MENGGANTI_baris_lama():
    """Keputusan Yosua 24 Okt 2026: revisi mengganti, bukan menambah."""
    lama_inv = [["14/10/2026", "", "JONNI SETIADI", 1, 2, 3]]
    lama_art = [["14/10/2026", "", "JONNI SETIADI", "X", "Y", 1, 2, 3],
                ["14/10/2026", "", "JONNI SETIADI", "Z", "W", 1, 2, 3]]
    s = _SambunganPalsu(isi={"DATA_INVOICE": lama_inv,
                             "DATA_ARTIKEL": lama_art})
    hasil = PenulisCatatan(s, "id").catat(_catatan(), paksa=True)
    assert "DIGANTI" in hasil
    assert sorted(s.dihapus) == [("DATA_ARTIKEL", 2), ("DATA_ARTIKEL", 3),
                                 ("DATA_INVOICE", 2)]
    assert [t[0] for t in s.ditulis] == ["DATA_ARTIKEL", "DATA_INVOICE"]


def test_customer_atau_tanggal_berbeda_TIDAK_ikut_terhapus():
    """Pagar paling penting: jangan menghapus invoice orang lain."""
    lama_inv = [["14/10/2026", "", "BABY WISE", 1, 2, 3],
                ["13/10/2026", "", "JONNI SETIADI", 1, 2, 3]]
    s = _SambunganPalsu(isi={"DATA_INVOICE": lama_inv, "DATA_ARTIKEL": []})
    hasil = PenulisCatatan(s, "id").catat(_catatan())
    assert "tercatat" in hasil
    assert s.dihapus == []


def test_baris_dihapus_dari_BAWAH_ke_atas():
    """Kalau dihapus dari atas, nomor baris di bawahnya bergeser dan
    penghapusan berikutnya mengenai baris yang salah."""
    lama = [["14/10/2026", "", "JONNI SETIADI", "A", "a", 1, 2, 3],
            ["14/10/2026", "", "JONNI SETIADI", "B", "b", 1, 2, 3],
            ["14/10/2026", "", "JONNI SETIADI", "C", "c", 1, 2, 3]]
    s = _SambunganPalsu(isi={"DATA_INVOICE": [], "DATA_ARTIKEL": lama})
    PenulisCatatan(s, "id").catat(_catatan())
    baris = [r for t, r in s.dihapus if t == "DATA_ARTIKEL"]
    assert baris == sorted(baris, reverse=True)


# ------------------------------------------------- sambungan ke pembuat draf
def test_buat_berkas_mengembalikan_bahan_catatan(tmp_path):
    """Angka laporan penjualan diambil dari pembuat faktur yang SAMA.

    Kalau `ringkas` tidak terisi, bot terpaksa menghitung ulang sendiri dan
    cepat atau lambat laporan penjualan menyebut angka yang berbeda dari
    fakturnya.
    """
    from hp_dokumen.berkas_dokumen import buat_berkas
    from buat_contoh import buat_contoh
    from hp_dokumen.konfigurasi import Konfigurasi
    from hp_dokumen.nilai_bersih import tentukan_nett
    from hp_dokumen.pemindai import baca_order_sheet

    cfg = Konfigurasi.muat()
    berkas = buat_contoh(tmp_path / "contoh.xlsx")
    orders = baca_order_sheet(berkas, cfg.customer, tahun_bawaan=2026)
    order = orders[0]
    keputusan = tentukan_nett(order, cfg.customer.cari(order.customer_kunci))

    ringkas: dict = {}
    buat_berkas(cfg, order, keputusan, tmp_path / "out", "",
                ringkas=ringkas)

    assert ringkas["baris_faktur"], "baris faktur tidak ikut dikembalikan"
    assert "nett" in ringkas and "dpp" in ringkas and "ppn" in ringkas
    # jumlah nett tiap baris HARUS sama dengan total fakturnya
    assert sum(b.nett for b in ringkas["baris_faktur"]) == pytest.approx(
        ringkas["nett"], abs=1.0)


# ------------------------------------------------- lewati yang sudah ada
def test_yang_sudah_tercatat_dilewati_tanpa_menulis():
    """Sapuan yang tidak mengubah apa pun tidak boleh menulis sama sekali.

    Dua sapuan sehari x ratusan baris berarti menulis ulang seluruh
    laporan tiap 9 jam, memboroskan kuota Google dan membuat kolom
    Dicatat berubah tanpa sebab.
    """
    lama = [["14/10/2026", "", "JONNI SETIADI", 1, 2, 3]]
    s = _SambunganPalsu(isi={"DATA_INVOICE": lama, "DATA_ARTIKEL": []})
    p = PenulisCatatan(s, "id")
    assert p.sudah_tercatat(_catatan())
    assert "dilewati" in p.catat(_catatan())
    assert s.ditulis == [] and s.dihapus == []


def test_revisi_tetap_menulis_walau_kuncinya_sudah_ada():
    """paksa=True dipakai saat PO-nya memang direvisi."""
    lama = [["14/10/2026", "", "JONNI SETIADI", 1, 2, 3]]
    s = _SambunganPalsu(isi={"DATA_INVOICE": lama, "DATA_ARTIKEL": []})
    hasil = PenulisCatatan(s, "id").catat(_catatan(), paksa=True)
    assert "DIGANTI" in hasil
    assert s.ditulis


def test_kunci_dibaca_sekali_lalu_diingat():
    """Memeriksa 16 PO tidak boleh berarti 16 kali membaca tab yang sama."""
    s = _SambunganPalsu(isi={"DATA_INVOICE": [], "DATA_ARTIKEL": []})
    p = PenulisCatatan(s, "id")
    for tgl in (date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3)):
        p.sudah_tercatat(_catatan(tgl=tgl))
    assert p._kunci is not None


def test_sesudah_dicatat_kuncinya_langsung_dikenali():
    """Tanpa ini, PO yang sama dalam satu sapuan bisa masuk dua kali."""
    s = _SambunganPalsu(isi={"DATA_INVOICE": [], "DATA_ARTIKEL": []})
    p = PenulisCatatan(s, "id")
    assert "tercatat" in p.catat(_catatan())
    assert p.sudah_tercatat(_catatan())
    assert "dilewati" in p.catat(_catatan())


# ------------------------------------- customer yang BELUM terdaftar
def test_label_dari_tab_membuang_tanggal_PO():
    from hp_dokumen.catatan_penjualan import label_dari_tab
    assert label_dari_tab("PO 06 September - BabyLand (Denpasar)") == \
        "BabyLand (Denpasar)"
    assert label_dari_tab("PO 2 Okt - Raja Murah (SGC)") == "Raja Murah (SGC)"


def test_label_dari_tab_tanpa_pola_PO_dipakai_apa_adanya():
    """`Sheet4` memang berisi PO sungguhan (bagian 18) - jangan dikosongkan."""
    from hp_dokumen.catatan_penjualan import label_dari_tab
    assert label_dari_tab("Sheet4") == "Sheet4"
    assert label_dari_tab("Order Jastip Ci Ratna") == "Order Jastip Ci Ratna"


def test_customer_belum_terdaftar_tetap_tercatat():
    """Tanpa ini, belasan PO per sapuan DITOLAK dan hilang dari laporan.

    Sapuan 28 Oktober 2026: BALONKU, Cherry, Liz & Co, BabyLand, Raja Murah
    dan lainnya semuanya "TIDAK dicatat - Nama customer kosong".
    """
    order, baris, hasil, _ = _bahan()
    order.customer_kunci = ""
    order.nama_tab = "PO 06 September - BabyLand (Denpasar)"
    c = susun(order, None, baris, hasil)
    assert c.customer == "BabyLand (Denpasar)"
    assert "Nama customer kosong." not in " ".join(periksa(c))
