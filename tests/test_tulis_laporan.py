"""Tab LAP dan BUKU berisi pekerjaan Yosua yang tidak ada salinannya.

Tes di sini mengunci pagar-pagarnya: tidak pernah menghapus, tidak pernah
membuat tab, menyisipkan di ATAS baris Total, dan melewati invoice yang
sudah ada alih-alih menggandakannya.
"""
import pathlib
from datetime import date

import pytest

from hp_dokumen.catatan_penjualan import (
    Catatan, baris_buku, baris_lap, nomor_berikut, tab_buku, tab_lap,
)
from hp_dokumen.sapu.tulis_laporan import PenulisLaporan


class _Nilai:
    def __init__(self, bank):
        self.bank = bank

    def get(self, spreadsheetId=None, range=None):
        judul = range.split("'")[1]
        isi = self.bank.isi.get(judul, [])
        # Hormati baris awal pada rentang (mis. A2:N), sebab modul yang
        # diuji memetakan hasilnya kembali ke nomor baris sheet.
        awal = "".join(c for c in range.split("!")[1].split(":")[0]
                       if c.isdigit())
        return _Jalan({"values": isi[int(awal) - 1:] if awal else isi})

    def update(self, spreadsheetId=None, range=None, valueInputOption=None,
               body=None):
        judul = range.split("'")[1]
        mulai = int("".join(c for c in range.split("!")[1].split(":")[0]
                            if c.isdigit()))
        isi = self.bank.isi.setdefault(judul, [])
        for i, b in enumerate(body["values"]):
            while len(isi) < mulai - 1 + i + 1:
                isi.append([])
            isi[mulai - 1 + i] = list(b)
        return _Jalan({})

    def append(self, spreadsheetId=None, range=None, valueInputOption=None,
               insertDataOption=None, body=None):
        judul = range.split("'")[1]
        isi = self.bank.isi.setdefault(judul, [])
        while isi and not any(str(x).strip() for x in isi[-1]):
            isi.pop()
        isi.extend(list(b) for b in body["values"])
        return _Jalan({})


class _Sheets:
    def __init__(self, bank):
        self.bank = bank

    def spreadsheets(self):
        return self

    def get(self, spreadsheetId=None, fields=None):
        return _Jalan({"sheets": [
            {"properties": {"title": t, "sheetId": i}}
            for i, t in enumerate(self.bank.isi)]})

    def values(self):
        return _Nilai(self.bank)

    def batchUpdate(self, spreadsheetId=None, body=None):
        balasan = []
        for p in body["requests"]:
            tambah = p.get("addSheet")
            if tambah:
                judul = tambah["properties"]["title"]
                self.bank.isi.setdefault(judul, [])
                balasan.append({"addSheet": {"properties": {
                    "title": judul,
                    "sheetId": list(self.bank.isi).index(judul)}}})
                continue
            hapus = p.get("deleteDimension")
            if hapus:
                self.bank.penghapusan += 1
                judul = list(self.bank.isi)[hapus["range"]["sheetId"]]
                isi = self.bank.isi[judul]
                a, b = hapus["range"]["startIndex"], hapus["range"]["endIndex"]
                del isi[a:b]
                balasan.append({})
                continue
            sis = p.get("insertDimension")
            if sis:
                gid = sis["range"]["sheetId"]
                judul = list(self.bank.isi)[gid]
                a, b = sis["range"]["startIndex"], sis["range"]["endIndex"]
                isi = self.bank.isi[judul]
                while len(isi) < a:
                    isi.append([])
                for _ in range(b - a):
                    isi.insert(a, [])
            balasan.append({})
        return _Jalan({"replies": balasan})


class _Jalan:
    def __init__(self, hasil):
        self.hasil = hasil

    def execute(self):
        return self.hasil


class SambunganPalsu:
    def __init__(self, isi):
        self.isi = isi
        self.penghapusan = 0
        self.sheets = _Sheets(self)


def _lap_awal():
    kosong = [[] for _ in range(4)]
    return kosong + [
        ["No", "Tanggal", "Nomor Invoice", "Nomor Faktur Pajak", "NPWP",
         "Nama Customer", "DPP", "PPN", "Total"],
        [],
        [1, "01/10/2026", "0011026", "", "", "RIA INDAH MANDIRI",
         31567567.57, 3472432.43, 35040000],
        [2, "02/10/2026", "0021026", "", "", "BABY WISE INDONESIA",
         27529883, 3028287, 30558170],
        ["Total Penjualan Oktober", "", "", "", "", "", 59097450, 6500719,
         65598170],
    ]


def _buku_awal():
    return [[] for _ in range(5)] + [
        ["01/10/2026", "0011026", "0011026", "RIA INDAH MANDIRI", "X", "A1",
         10, 100, 1000, 900, 100, 1000],
        [],
    ]


def _catatan(total=5_000_000.0, cust="JOY BABY"):
    return Catatan(
        nomor="", customer=cust, tanggal=date(2026, 10, 28),
        dpp=total / 1.11, ppn=total - total / 1.11, total=total,
        jatuh_tempo=date(2026, 11, 27),
        artikel=[["28/10/2026", "", cust, "AB.1", "Kaos Bayi", 10, 600.0,
                  total / 2],
                 ["28/10/2026", "", cust, "AB.2", "Celana Bayi", 5, 1200.0,
                  total / 2]],
    )


def _penulis():
    s = SambunganPalsu({"LAP OKT": _lap_awal(), "BUKU OKT": _buku_awal()})
    return PenulisLaporan(s, "id"), s


def test_nomor_melanjutkan_yang_tertinggi_bukan_mengisi_lubang():
    assert nomor_berikut(["0011026", "0051026"], date(2026, 10, 1)) == "0061026"


def test_nomor_mengabaikan_bulan_lain_dan_akhiran_huruf():
    terpakai = ["0011026", "0991126", "0071026.A", "'0081026"]
    assert nomor_berikut(terpakai, date(2026, 10, 1)) == "0091026"


def test_nomor_diulang_dari_satu_tiap_bulan():
    assert nomor_berikut(["0381026"], date(2026, 11, 2)) == "0011126"


def test_tab_dinamai_menurut_bulan_tanggalnya():
    assert tab_lap(date(2026, 5, 9)) == "LAP MEI"
    assert tab_buku(date(2026, 12, 1)) == "BUKU DES"


def test_disisipkan_DI_ATAS_baris_total_penjualan():
    p, s = _penulis()
    p.catat(_catatan())
    isi = s.isi["LAP OKT"]
    judul = [i for i, b in enumerate(isi)
             if b and str(b[0]).startswith("Total Penjualan")]
    baru = [i for i, b in enumerate(isi) if len(b) > 5 and b[5] == "JOY BABY"]
    assert baru and judul, "baris baru dan baris total harus ada"
    assert baru[0] < judul[0], "baris baru harus DI ATAS baris Total"


def test_tidak_pernah_menghapus_baris():
    p, s = _penulis()
    p.catat(_catatan())
    assert s.penghapusan == 0


def test_baris_lama_yosua_tidak_berubah():
    p, s = _penulis()
    sebelum = [list(b) for b in s.isi["LAP OKT"][:8]]
    p.catat(_catatan())
    assert [list(b) for b in s.isi["LAP OKT"][:8]] == sebelum


def test_invoice_yang_sudah_ada_DILEWATI_bukan_digandakan():
    p, s = _penulis()
    pesan = p.catat(_catatan(total=30558170.0, cust="Baby Wise Indonesia"))
    assert "sudah ada" in pesan and "0021026" in pesan
    assert sum(1 for b in s.isi["LAP OKT"]
               if len(b) > 5 and str(b[5]).upper() == "BABY WISE INDONESIA") == 1


def test_tab_yang_belum_ada_TIDAK_dibuat_sendiri():
    s = SambunganPalsu({"LAP OKT": _lap_awal(), "BUKU OKT": _buku_awal()})
    p = PenulisLaporan(s, "id")
    c = _catatan()
    c.tanggal = date(2026, 11, 3)
    pesan = p.catat(c)
    assert "tidak ada" in pesan and "TIDAK" in pesan
    assert "LAP NOV" not in s.isi


@pytest.mark.parametrize("judul", ["TAGIHAN", "DATA_INVOICE", "ARTIKEL OKT",
                                   "Sheet1", "LAPORAN"])
def test_menolak_tab_di_luar_LAP_dan_BUKU(judul):
    p, _ = _penulis()
    with pytest.raises(ValueError):
        p._periksa_judul(judul)


def test_harga_di_BUKU_adalah_harga_SETELAH_diskon():
    """Dibuktikan dari invoice 0081026 Haritsa: 18 x 34.500 = 621.000, dan
    jumlah seluruh kolom itu sama dengan Total invoice."""
    c = _catatan(total=5_000_000.0)
    c.nomor = "0391026"
    baris = baris_buku(c)
    artikel = [b for b in baris if len(b) > 8 and b[5]]
    for b in artikel:
        assert b[8] == pytest.approx(b[6] * b[7], abs=0.01)
    assert sum(b[8] for b in artikel) == pytest.approx(c.total, abs=0.01)


def test_baris_total_buku_memuat_qty_dan_nilai_invoice():
    c = _catatan()
    c.nomor = "0391026"
    akhir = [b for b in baris_buku(c)
             if b and str(b[4]).startswith("Total ")][0]
    assert akhir[6] == 15
    assert akhir[8] == pytest.approx(c.total, abs=0.01)


def test_npwp_dan_nomor_faktur_pajak_dikosongkan():
    """Keduanya tidak ada di order sheet dan tidak boleh ditebak."""
    c = _catatan()
    c.nomor = "0391026"
    b = baris_lap(c, 3)
    assert b[3] == "" and b[4] == ""
    assert b[2] == "0391026" and b[5] == "JOY BABY"


# --------------------------------------------------------------- pagar tahun

def test_pagar_tahun_menolak_po_tahun_lain():
    """Tab LAP/BUKU hanya menyebut BULAN, tidak menyebut tahun.

    Tanpa pagar ini, sapuan penuh (yang membaca order sheet 2025 juga)
    akan menyisipkan invoice Januari 2025 ke tab `LAP JAN` milik laporan
    2026 dan menambah total penjualan setahun - tanpa galat apa pun.
    """
    import ast
    import pathlib

    sumber = (pathlib.Path(__file__).resolve().parent.parent
              / "src/hp_dokumen/sapu/bot.py").read_text()
    pohon = ast.parse(sumber)
    fn = next(n for n in pohon.body
              if isinstance(n, ast.FunctionDef) and n.name == "_catat_penjualan")

    arg = [a.arg for a in fn.args.kwonlyargs]
    assert "tahun_laporan" in arg, "pagar tahun hilang dari _catat_penjualan"

    # Pagarnya harus KELUAR lebih dulu, sebelum faktur dibangun - kalau
    # tidak, PO tahun lain tetap memakan waktu membangun berkas sementara.
    badan = ast.dump(fn)
    assert "tahun_laporan" in badan.split("buat_berkas")[0], \
        "pemeriksaan tahun harus dilakukan SEBELUM faktur dibangun"


def test_bot_yaml_mengisi_tahun_laporan_kalau_sheet_laporan_dipakai():
    import pathlib
    import yaml

    akar = pathlib.Path(__file__).resolve().parent.parent
    d = yaml.safe_load((akar / "config/bot.yaml").read_text()) or {}
    if (d.get("sheet_laporan_penjualan_id") or "").strip():
        assert int(d.get("tahun_laporan") or 0) >= 2026, (
            "sheet_laporan_penjualan_id terisi tapi tahun_laporan kosong - "
            "sapuan penuh akan mencampur invoice tahun lain"
        )


def test_tahun_laporan_bawaannya_TAHUN_BERJALAN_bukan_nol():
    """bot.yaml milik Yosua dilindungi dari pembaruan otomatis, jadi kunci
    `tahun_laporan` yang baru TIDAK akan pernah sampai ke komputernya.
    Kalau bawaannya 0, pagarnya mati persis di tempat yang paling penting.

    Dibaca dari SUMBERNYA, bukan dengan mengimpor `bot.py` - modul itu
    menarik pustaka Google yang tidak selalu ada di mesin pemeriksa.
    """
    import pathlib

    sumber = (pathlib.Path(__file__).resolve().parent.parent
              / "src/hp_dokumen/sapu/bot.py").read_text()
    potong = sumber.split("tahun_laporan=int(", 1)
    assert len(potong) == 2, "pembacaan tahun_laporan hilang"
    assert "_date.today().year" in potong[1][:200], (
        "bawaan tahun_laporan harus TAHUN BERJALAN, bukan 0"
    )


# ---------------------------------------- tahun order sheet, bukan 2026
def test_bot_memakai_TAHUN_ORDER_SHEET_saat_membaca_buku():
    """`baca_buku` bawaannya 2026 — order sheet 2025 harus menimpanya.

    Tanpa ini SELURUH PO 2025 bertanggal 2026, dan pagar `tahun_laporan`
    TIDAK menangkapnya sebab tahun yang dibandingkan sudah terlanjur
    salah. Terbukti pada sapuan 28 Oktober 2026: `PO 29 Desember - Baby
    Wise` dari order sheet Desember 2025 masuk REKAP INVOICE sebagai
    29/12/2026, lalu ikut disisipkan ke LAP DES milik laporan 2026.

    Diperiksa dari SUMBER, bukan dengan menjalankan bot: `sapu/bot.py`
    tidak bisa diimpor di wadah ini (cryptography rusak).
    """
    sumber = (pathlib.Path(__file__).resolve().parent.parent
              / "src" / "hp_dokumen" / "sapu" / "bot.py").read_text()
    assert "baca_buku(buku, cfg.customer)" not in sumber, (
        "baca_buku dipanggil tanpa tahun — order sheet 2025 akan "
        "bertanggal 2026"
    )
    assert "tahun_di(berkas.nama)" in sumber
    assert "tahun_di(nama_folder)" in sumber
