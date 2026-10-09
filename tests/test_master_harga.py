"""Tab 'Harga Retail' adalah satu-satunya sumber harga dan nama barang.

Permintaan Yosua 14 September 2026: "untuk bagian harga sesuaikan dengan tab
master harga yang ada di setiap tab yang ada di order sheet".

Diperiksa lebih dulu pada seluruh 8.845 baris order sheet 2026: harga di baris
PO memang SUDAH sama persis dengan master di semua baris. Jadi aturan ini tidak
mengubah angka mana pun hari ini — gunanya menangkap kalau suatu saat Sales
mengetik harga sendiri di baris PO.
"""
import openpyxl
import pytest

from hp_dokumen.konfigurasi import Konfigurasi
from hp_dokumen.pemindai import baca_master_harga, baca_order_sheet, cari_di_master
from buat_contoh import buat_contoh


@pytest.fixture
def berkas(tmp_path):
    return buat_contoh(tmp_path / "contoh.xlsx")


def test_kode_dicari_tanpa_peduli_huruf_besar_kecil():
    """`41065 (bottom/Celana)` harus ketemu walau master menulis `Bottom`.

    Tiga kode nyata di order sheet Januari dan Februari 2026 dulu dianggap
    tidak terdaftar hanya karena beda huruf besar-kecil.
    """
    master = {"41065 (Bottom/Celana)": ("Nilo Straight Denim Pants", 44200.0)}
    assert cari_di_master(master, "41065 (bottom/Celana)") is not None
    assert cari_di_master(master, "41065 (BOTTOM/CELANA)") is not None
    assert cari_di_master(master, " 41065 (Bottom/Celana) ") is not None
    assert cari_di_master(master, "41065 (Bottom/Celana)")[1] == 44200.0
    assert cari_di_master(master, "kode lain") is None
    assert cari_di_master({}, "apa pun") is None


def test_harga_diambil_dari_master_bukan_dari_baris_po(berkas, tmp_path):
    """Harga yang diketik beda di baris PO harus ditimpa oleh master."""
    cfg = Konfigurasi.muat()
    master = baca_master_harga(berkas)
    assert master, "berkas contoh harus punya tab Harga Retail"

    # rusak harga satu baris PO supaya berbeda dari master
    wb = openpyxl.load_workbook(berkas)
    ws = next(w for w in wb.worksheets if w.title.lower() not in ("harga retail",))
    kolom_harga = next(
        c for c in range(1, ws.max_column + 1)
        for r in range(1, 12)
        if "PRICE" in str(ws.cell(r, c).value or "").upper()
    )
    baris_data = next(
        r for r in range(1, ws.max_row + 1)
        if str(ws.cell(r, kolom_harga).value or "").replace(".", "").isdigit()
    )
    kode_rusak = None
    for r in range(baris_data, ws.max_row + 1):
        if isinstance(ws.cell(r, kolom_harga).value, (int, float)):
            kode_rusak = str(ws.cell(r, 1).value)
            ws.cell(r, kolom_harga).value = 999999
            break
    assert kode_rusak, "tidak menemukan baris harga untuk dirusak"
    rusak = tmp_path / "rusak.xlsx"
    wb.save(rusak)

    orders = baca_order_sheet(rusak, cfg.customer, tahun_bawaan=2026)
    for o in orders:
        for blok in o.blok:
            for b in blok.baris:
                m = cari_di_master(master, b.kode)
                if m and m[1] > 0:
                    assert abs(b.harga - m[1]) < 0.5, (
                        f"{b.kode}: harga {b.harga} tidak mengikuti master {m[1]}"
                    )
    assert any("HARGA DISESUAIKAN" in p for o in orders for p in o.peringatan), (
        "penyesuaian harga harus DILAPORKAN, tidak boleh diam-diam"
    )


def test_nama_barang_juga_dari_master(berkas):
    """Nama barang di dokumen ikut master, bukan ketikan di baris PO."""
    cfg = Konfigurasi.muat()
    master = baca_master_harga(berkas)
    for o in baca_order_sheet(berkas, cfg.customer, tahun_bawaan=2026):
        for blok in o.blok:
            for b in blok.baris:
                m = cari_di_master(master, b.kode)
                if m and m[0]:
                    assert b.nama == m[0], f"{b.kode}: nama tidak ikut master"


# ------------------------------------------------- KETETAPAN 2 Oktober 2026
# Yosua: "setiap ada update pada tabel di tab harga retail anda harus ikut
# dengan harga tersebut". Tiga tes di bawah menutup celah yang membuat aturan
# itu bisa dilanggar DIAM-DIAM.

def test_nama_tab_harga_boleh_berakhiran_apa_pun():
    """`Harga Retail per Mei 2025` juga tab master harga.

    Order Sheet Mei 2025 menamainya begitu. Pencocokan nama yang persis
    membuat 83 artikelnya tidak pernah terbaca, dan harga dokumennya diam-diam
    diambil dari baris PO — persis yang dilarang ketetapan ini.

    Tapi AWALAN, bukan "mengandung": tab `PO 30 Okt Borneo Retail - Deliv`
    di order sheet Januari 2025 juga memuat kata "Retail" padahal itu tab PO
    sungguhan. Kalau ikut tertangkap, tab PO-nya hilang dari dokumen.
    """
    from hp_dokumen.pemindai import adalah_tab_harga

    for nama in ("Harga Retail", "Harga Retail per Mei 2025", "HARGA RETAIL",
                 " Harga  Retail ", "harga retail 2026"):
        assert adalah_tab_harga(nama), f"{nama!r} seharusnya dikenali"

    for nama in ("PO 30 Okt Borneo Retail - Deliv", "PO 28 September - Dunia Bayi",
                 "Packing List Haritsa", "Retail Harga", ""):
        assert not adalah_tab_harga(nama), f"{nama!r} BUKAN tab harga"


def test_master_terbaca_dari_tab_yang_namanya_berakhiran_lain(tmp_path):
    """Harga tetap diambil dari master walau nama tabnya tidak persis."""
    from hp_dokumen.pemindai import master_harga_dari_buku

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Harga Retail per Mei 2025"
    ws.append(["Artikel", "Nama Barang", "Harga Ritel"])
    ws.append(["42003.A", "Leo Set", 71000])
    assert master_harga_dari_buku(wb) == {"42003.A": ("Leo Set", 71000.0)}


def test_tanpa_tab_harga_program_memperingatkan_keras(tmp_path):
    """Master kosong WAJIB menghasilkan peringatan, bukan diam.

    Kalau tab harga tidak ketemu, harga diambil dari baris PO — dan itu
    tidak terverifikasi. Dulu hal ini terjadi tanpa pesan apa pun, jadi tidak
    ada yang tahu dokumennya memakai harga yang belum tentu berlaku.
    """
    berkas_contoh = buat_contoh(tmp_path / "tanpa_master.xlsx")
    wb = openpyxl.load_workbook(berkas_contoh)
    nama_tab_harga = [n for n in wb.sheetnames if "harga" in n.lower()]
    assert nama_tab_harga, "berkas contoh seharusnya punya tab harga"
    for n in nama_tab_harga:
        del wb[n]
    wb.save(berkas_contoh)

    cfg = Konfigurasi.muat()
    orders = baca_order_sheet(berkas_contoh, cfg.customer, tahun_bawaan=2026)
    assert orders, "order sheet contoh tidak terbaca"
    for o in orders:
        assert any("TAB HARGA RETAIL TIDAK KETEMU" in w for w in o.peringatan), (
            f"tab '{o.nama_tab}' tidak diperingatkan padahal master kosong")


def test_tab_harga_tidak_ikut_dipindai_sebagai_po(tmp_path):
    """Tab master harga bukan PO — tidak boleh menghasilkan dokumen."""
    berkas_contoh = buat_contoh(tmp_path / "contoh_tab.xlsx")
    wb = openpyxl.load_workbook(berkas_contoh)
    for n in list(wb.sheetnames):
        if n.strip().lower() == "harga retail":
            wb[n].title = "Harga Retail per Contoh 2026"
    wb.save(berkas_contoh)

    cfg = Konfigurasi.muat()
    orders = baca_order_sheet(berkas_contoh, cfg.customer, tahun_bawaan=2026)
    from hp_dokumen.pemindai import adalah_tab_harga
    nakal = [o.nama_tab for o in orders if adalah_tab_harga(o.nama_tab)]
    assert not nakal, f"tab harga ikut jadi PO: {nakal}"
