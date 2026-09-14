"""Tes kesiapan cetak A4.

Yosua melaporkan dokumen tidak muat di kertas A4 dan blok penutup invoice
tidak berkotak. Tiga hal dikunci di sini:

  1. Blok penutup (Subtotal..Total) dan blok rekening invoice punya garis
     kotak mengelilinginya.
  2. Semua dokumen disetel A4 tegak, muat selebar satu halaman.
  3. Jumlah lebar kolom tidak melebihi apa yang muat di A4 tegak.

Batas lebar dihitung dari faktur asli DPM: A4 tegak (8,27 inci) dikurangi
margin 0,15 + 0,15, dibagi lebar satu satuan kolom Excel (+-0,0959 inci)
menghasilkan +-83 satuan pada skala 100%. Faktur asli sendiri memakai 107,7
satuan dengan skala cetak 97%, jadi batasnya diambil 115 — cukup longgar
untuk Surat Jalan sembilan ukuran, tapi tetap menangkap kolom yang kebablasan
seperti versi lama (C selebar 39,4).
"""
import openpyxl
import pytest
from openpyxl import Workbook

from hp_dokumen.dokumen.invoice import buat_invoice
from hp_dokumen.dokumen.surat_jalan import buat_packing_list, buat_surat_jalan
from hp_dokumen.konfigurasi import Konfigurasi
from hp_dokumen.nilai_bersih import tentukan_nett
from hp_dokumen.pemindai import baca_order_sheet
from buat_contoh import buat_contoh

BATAS_LEBAR_A4 = 135.0


@pytest.fixture
def bahan(tmp_path):
    cfg = Konfigurasi.muat()
    berkas = buat_contoh(tmp_path / "contoh.xlsx")
    orders = [o for o in baca_order_sheet(berkas, cfg.customer, tahun_bawaan=2026) if o.qty > 0]
    return orders, cfg


def _lebar_terpakai(ws) -> float:
    """Jumlah lebar kolom sampai kolom terakhir yang dicetak."""
    import re
    akhir = ws.print_area[0] if isinstance(ws.print_area, list) else ws.print_area
    # print_area berbentuk "'Sheet'!$A$1:$M$41" — ambil huruf kolom terakhirnya
    kolom_akhir = openpyxl.utils.column_index_from_string(
        re.search(r"\$?([A-Z]+)\$?\d+$", akhir.split(":")[-1]).group(1)
    )
    total = 0.0
    for c in range(1, kolom_akhir + 1):
        d = ws.column_dimensions.get(openpyxl.utils.get_column_letter(c))
        total += d.width if d and d.width else 8.43
    return total


def _simpan(ws, tmp_path, nama):
    p = tmp_path / nama
    ws.parent.save(p)
    return openpyxl.load_workbook(p).active


def test_invoice_blok_penutup_dan_rekening_berkotak(bahan, tmp_path):
    orders, cfg = bahan
    o = orders[0]
    c = cfg.customer.cari(o.nama_tab)
    wb = Workbook()
    buat_invoice(wb.active, o, tentukan_nett(o, c), c, cfg.perusahaan.untuk(c),
                 cfg.pengaturan, "001")
    ws = _simpan(wb.active, tmp_path, "inv.xlsx")

    subtotal = next(r for r in range(1, ws.max_row + 1)
                    if ws.cell(r, 7).value == "Subtotal")
    assert ws.cell(subtotal, 7).border.top.style, "sisi atas blok penutup tidak bergaris"
    assert ws.cell(subtotal, 7).border.left.style, "sisi kiri blok penutup tidak bergaris"

    rek = next(r for r in range(1, ws.max_row + 1)
               if "PEMBAYARAN DITRANSFER" in str(ws.cell(r, 1).value or ""))
    assert ws.cell(rek, 1).border.top.style, "sisi atas blok rekening tidak bergaris"
    assert ws.cell(rek, 1).border.left.style, "sisi kiri blok rekening tidak bergaris"


@pytest.mark.parametrize("dokumen", ["invoice", "surat_jalan", "packing_list"])
def test_semua_dokumen_a4_tegak_dan_muat(bahan, tmp_path, dokumen):
    orders, cfg = bahan
    # PO dengan ukuran terbanyak — yang paling mungkin tidak muat
    o = max(orders, key=lambda x: max(len(b.label_ukuran) for b in x.blok))
    c = cfg.customer.cari(o.nama_tab)
    wb = Workbook()
    if dokumen == "invoice":
        buat_invoice(wb.active, o, tentukan_nett(o, c), c, cfg.perusahaan.untuk(c),
                     cfg.pengaturan, "001")
    elif dokumen == "surat_jalan":
        buat_surat_jalan(wb.active, o, c, cfg.perusahaan.untuk(c), "001")
    else:
        buat_packing_list(wb.active, o, c, cfg.perusahaan.untuk(c), "001")
    ws = _simpan(wb.active, tmp_path, f"{dokumen}.xlsx")

    assert ws.page_setup.orientation == "portrait", f"{dokumen} tidak tegak"
    # openpyxl mengembalikan paperSize sebagai angka saat berkas dibaca ulang,
    # padahal konstantanya berupa teks. Disamakan dulu supaya tidak salah alarm.
    assert int(ws.page_setup.paperSize) == int(ws.PAPERSIZE_A4), f"{dokumen} bukan A4"
    assert ws.page_setup.fitToWidth == 1, f"{dokumen} tidak dipaskan selebar halaman"
    assert ws.sheet_properties.pageSetUpPr.fitToPage is True

    lebar = _lebar_terpakai(ws)
    assert lebar <= BATAS_LEBAR_A4, (
        f"{dokumen} selebar {lebar:.1f} satuan, lebih dari batas "
        f"{BATAS_LEBAR_A4} yang masih terbaca di A4 tegak."
    )


def test_invoice_lebar_menyesuaikan_tetap_dalam_jatah_a4():
    """Kolom B dan C boleh melebar, tapi jumlah A..H tidak boleh bertambah."""
    from hp_dokumen.dokumen.invoice import (
        MAKS_JATAH, MAKS_KODE, BarisInvoice, lebar_menyesuaikan,
    )

    panjang = [BarisInvoice(
        kode="71092.S (Bottom/Celana)",
        deskripsi="Luma Satin Kutubaru Kebaya Set Small Size Uk. 6-12M",
        qty=1, harga=1000, kotor=1000, nett=750)]
    pendek = [BarisInvoice(kode="41080", deskripsi="Woody set",
                           qty=1, harga=1000, kotor=1000, nett=750)]

    # Yang wajib: tidak pernah MELEBIHI jatah. Lebih sempit selalu aman.
    for baris in (panjang, pendek, []):
        lebar = lebar_menyesuaikan(baris)
        assert sum(lebar.values()) <= MAKS_JATAH + 0.01, (
            "jumlah lebar A..H melebihi jatah A4"
        )

    # kode panjang harus dapat ruang lebih daripada kode pendek
    assert lebar_menyesuaikan(panjang)[2] > lebar_menyesuaikan(pendek)[2]
    assert lebar_menyesuaikan(panjang)[2] <= MAKS_KODE


def test_surat_jalan_kode_panjang_tidak_menambah_lebar(bahan):
    """Kolom ARTICLE CODE boleh melebar, tapi total lebar tidak bertambah."""
    from hp_dokumen.dokumen.surat_jalan import LEBAR, _lebar_menyesuaikan

    orders, _ = bahan
    for o in orders:
        lebar = _lebar_menyesuaikan(o)
        assert sum(lebar.values()) <= sum(LEBAR.values()) + 0.01, (
            f"{o.nama_tab}: lebar kolom tetap bertambah, bisa tidak muat A4"
        )
        assert lebar[5] >= 20.0, "kolom deskripsi terlalu sempit"


def test_blok_penutup_invoice_bergaris_penuh(bahan, tmp_path):
    """Tiap sel blok penutup punya garis di keempat sisinya.

    Permintaan Yosua 14 September 2026, dan memang begitu aslinya: di
    0020826 CV. BASA MANDIRI sel K27..M31 semuanya bergaris `thin` di
    keempat sisi. Versi sebelumnya hanya menggambar kotak luar, sehingga
    Subtotal/Diskon/Total/DPP/PPN berhimpitan tanpa pemisah.
    """
    orders, cfg = bahan
    o = orders[0]
    c = cfg.customer.cari(o.nama_tab)
    wb = Workbook()
    buat_invoice(wb.active, o, tentukan_nett(o, c), c, cfg.perusahaan.untuk(c),
                 cfg.pengaturan, "001")
    ws = _simpan(wb.active, tmp_path, "inv_garis.xlsx")

    mulai = next(r for r in range(1, ws.max_row + 1)
                 if ws.cell(r, 7).value == "Subtotal")
    akhir = max(r for r in range(mulai, ws.max_row + 1)
                if ws.cell(r, 7).value not in (None, "", "Hormat kami,"))
    assert akhir > mulai, "blok penutup tidak ditemukan"

    for r in range(mulai, akhir + 1):
        for c_ in (7, 8):
            b = ws.cell(r, c_).border
            for sisi, nama in ((b.left, "kiri"), (b.right, "kanan"),
                               (b.top, "atas"), (b.bottom, "bawah")):
                assert sisi.style, (
                    f"{ws.cell(r, c_).coordinate} tidak bergaris di sisi {nama}"
                )


def test_uang_muka_nol_tampil_sebagai_strip(bahan, tmp_path):
    """Uang Muka kosong harus tampil '-', bukan angka 0.

    Dicapai lewat bagian ketiga format akuntansi Rupiah (`_-"Rp"* "-"_-`)
    yang memang khusus untuk nilai nol. Kalau format ini diganti dengan
    format angka biasa, yang tercetak kembali jadi 0.
    """
    orders, cfg = bahan
    o = orders[0]
    c = cfg.customer.cari(o.nama_tab)
    wb = Workbook()
    buat_invoice(wb.active, o, tentukan_nett(o, c), c, cfg.perusahaan.untuk(c),
                 cfg.pengaturan, "001")
    ws = _simpan(wb.active, tmp_path, "inv_uangmuka.xlsx")

    baris = next(r for r in range(1, ws.max_row + 1)
                 if ws.cell(r, 7).value == "Uang Muka")
    sel = ws.cell(baris, 8)
    assert sel.value == 0
    bagian = sel.number_format.split(";")
    assert len(bagian) >= 3, "format angka tidak punya bagian khusus nol"
    assert '"-"' in bagian[2], (
        f"nilai nol tidak tampil sebagai '-' (format nol: {bagian[2]!r})"
    )


def test_blok_penutup_invoice_tidak_bercetak_tebal(bahan, tmp_path):
    """Blok penutup tidak boleh bercetak tebal.

    Permintaan Yosua 14 September 2026. Faktur asli menebalkan seluruh blok
    ini, tapi begitu tiap sel diberi garis, huruf tebalnya jadi terlalu
    ramai. Garisnya sudah cukup memisahkan.
    """
    orders, cfg = bahan
    o = orders[0]
    c = cfg.customer.cari(o.nama_tab)
    wb = Workbook()
    buat_invoice(wb.active, o, tentukan_nett(o, c), c, cfg.perusahaan.untuk(c),
                 cfg.pengaturan, "001")
    ws = _simpan(wb.active, tmp_path, "inv_tanpa_tebal.xlsx")

    mulai = next(r for r in range(1, ws.max_row + 1)
                 if ws.cell(r, 7).value == "Subtotal")
    akhir = max(r for r in range(mulai, ws.max_row + 1)
                if ws.cell(r, 7).value not in (None, "", "Hormat kami,"))

    for r in range(mulai, akhir + 1):
        for c_ in (7, 8):
            sel = ws.cell(r, c_)
            assert not sel.font.bold, (
                f"{sel.coordinate} ({sel.value!r}) masih bercetak tebal"
            )
