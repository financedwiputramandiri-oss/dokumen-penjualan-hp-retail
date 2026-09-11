"""Tes bahwa berkas dokumen benar-benar terbentuk dan angkanya cocok."""
from pathlib import Path

import openpyxl
import pytest
from openpyxl import Workbook

from buat_contoh import buat_contoh
from hp_dokumen.dokumen.faktur_pajak import buat_faktur_pajak
from hp_dokumen.dokumen.invoice import buat_invoice
from hp_dokumen.dokumen.surat_jalan import buat_packing_list, buat_surat_jalan
from hp_dokumen.konfigurasi import Customer, DaftarCustomer, Pengaturan, Perusahaan
from hp_dokumen.nilai_bersih import tentukan_nett
from hp_dokumen.pemindai import baca_order_sheet


@pytest.fixture(scope="module")
def bahan(tmp_path_factory):
    berkas = buat_contoh(tmp_path_factory.mktemp("d") / "contoh.xlsx")
    daftar = DaftarCustomer([
        Customer("Contoh TOP", "PT Contoh Satu", "Jl. Contoh 1", "", "per_artikel", 30, "", ""),
        Customer("Contoh CBD", "PT Contoh Dua", "Jl. Contoh 2", "", "per_ukuran", 30, "", ""),
    ])
    orders = baca_order_sheet(berkas, daftar, tahun_bawaan=2026)
    perusahaan = Perusahaan("CV CONTOH", ["Jl. A", "Kota"], "", ["REKENING:", "BANK X"], "Jakarta")
    return orders, daftar, perusahaan, Pengaturan()


def _cari_baris(ws, kolom, teks):
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, kolom).value == teks:
            return r
    return None


def test_surat_jalan_satu_tabel_per_blok(bahan, tmp_path):
    orders, daftar, perusahaan, _ = bahan
    o = next(x for x in orders if "TOP" in x.nama_tab)
    wb = Workbook()
    buat_surat_jalan(wb.active, o, daftar.cari(o.nama_tab), perusahaan, "001")
    p = tmp_path / "sj.xlsx"
    wb.save(p)

    ws = openpyxl.load_workbook(p).active
    judul = [r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == "No."]
    assert len(judul) == len(o.blok) == 2, "harus ada satu tabel per blok"
    total_rows = [r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == "TOTAL"]
    assert len(total_rows) == 2, "tiap tabel punya baris TOTAL sendiri"
    assert _cari_baris(ws, 1, "TOTAL SELURUH PO") is not None
    # label ukuran tiap tabel berbeda
    assert ws.cell(judul[0], 5).value == "0-3M"
    assert ws.cell(judul[1], 5).value == "1"


def test_packing_list_punya_kolom_gudang(bahan, tmp_path):
    orders, daftar, perusahaan, _ = bahan
    o = next(x for x in orders if "TOP" in x.nama_tab)
    wb = Workbook()
    buat_packing_list(wb.active, o, daftar.cari(o.nama_tab), perusahaan, "001")
    p = tmp_path / "pl.xlsx"
    wb.save(p)
    ws = openpyxl.load_workbook(p).active
    semua = {ws.cell(r, c).value for r in range(1, ws.max_row + 1) for c in range(1, 20)}
    assert "JUMLAH DIKIRIM" in semua
    assert "NO. KOLI" in semua


def test_invoice_satu_tabel_menerus_dan_total_cocok(bahan, tmp_path):
    orders, daftar, perusahaan, pengaturan = bahan
    o = next(x for x in orders if "TOP" in x.nama_tab)
    c = daftar.cari(o.nama_tab)
    k = tentukan_nett(o, c)
    wb = Workbook()
    ringkas = buat_invoice(wb.active, o, k, c, perusahaan, pengaturan, "001")
    p = tmp_path / "inv.xlsx"
    wb.save(p)

    ws = openpyxl.load_workbook(p).active
    judul = [r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == "No."]
    assert len(judul) == 1, "invoice tidak boleh dipecah per tabel"

    # jumlah kolom H pada baris data harus sama dengan nett order sheet
    r = judul[0] + 1
    jumlah = 0.0
    while isinstance(ws.cell(r, 1).value, int):
        jumlah += ws.cell(r, 8).value or 0
        r += 1
    assert abs(jumlah - k.nett_total) < 0.01
    assert abs(ringkas["nett"] - k.nett_total) < 0.01
    assert ringkas["qty"] == o.qty
    # warna tidak boleh muncul di invoice
    teks = {ws.cell(rr, 3).value for rr in range(1, ws.max_row + 1)}
    assert "Merah" not in teks and "Biru" not in teks


def test_invoice_penutup_lengkap_dan_berurutan(bahan, tmp_path):
    orders, daftar, perusahaan, pengaturan = bahan
    o = next(x for x in orders if "TOP" in x.nama_tab)
    c = daftar.cari(o.nama_tab)
    k = tentukan_nett(o, c)
    wb = Workbook()
    buat_invoice(wb.active, o, k, c, perusahaan, pengaturan, "001")
    p = tmp_path / "inv2.xlsx"
    wb.save(p)
    ws = openpyxl.load_workbook(p).active
    # penutup ada SESUDAH tabel data, jadi mulai memindai dari baris terakhir tabel
    awal = _cari_baris(ws, 1, "No.")
    r = awal + 1
    while isinstance(ws.cell(r, 1).value, int):
        r += 1
    abaikan = {"Hormat kami,", "(................................)"}
    label = [ws.cell(rr, 7).value for rr in range(r, ws.max_row + 1)
             if isinstance(ws.cell(rr, 7).value, str) and ws.cell(rr, 7).value not in abaikan]
    assert label == ["Subtotal", "Diskon", "Total", "Uang Muka", "DPP", "PPN 11%", "Total"]


def test_faktur_pajak_dpp_plus_ppn_sama_dengan_total(bahan, tmp_path):
    orders, daftar, perusahaan, pengaturan = bahan
    o = next(x for x in orders if "CBD" in x.nama_tab)
    c = daftar.cari(o.nama_tab)
    k = tentukan_nett(o, c)
    wb = Workbook()
    ringkas = buat_faktur_pajak(wb.active, o, k, c, perusahaan, pengaturan, "REF-001")
    assert abs(ringkas["dpp"] + ringkas["ppn"] - k.nett_total) < 0.01
    assert abs(ringkas["dpp"] * (1 + pengaturan.tarif_ppn) - k.nett_total) < 0.01


def test_dokumen_tetap_jadi_walau_data_customer_kosong(bahan, tmp_path):
    """Rekan kerja tidak boleh kena error hanya karena alamat belum diisi."""
    orders, _, perusahaan, pengaturan = bahan
    o = next(x for x in orders if "TOP" in x.nama_tab)
    k = tentukan_nett(o, None)
    wb = Workbook()
    buat_surat_jalan(wb.active, o, None, perusahaan, "001")
    buat_invoice(wb.create_sheet("inv"), o, k, None, perusahaan, pengaturan, "001")
    buat_faktur_pajak(wb.create_sheet("fp"), o, k, None, perusahaan, pengaturan, "001")
    wb.save(tmp_path / "kosong.xlsx")
