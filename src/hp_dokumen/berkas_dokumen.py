"""Pembuat berkas dokumen — dipakai bersama oleh perintah manual dan bot penyapu.

Dipisahkan ke sini supaya dokumen yang dibuat manusia lewat `jalankan.py buat`
dan dokumen yang dibuat sendiri oleh bot penyapu benar-benar keluar dari satu
kode yang sama. Kalau dua-duanya punya kode sendiri, cepat atau lambat hasilnya
akan berbeda tanpa ada yang sadar.
"""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook

from .dokumen.faktur_pajak import buat_faktur_pajak
from .dokumen.invoice import buat_invoice
from .dokumen.proforma import buat_proforma
from .dokumen.surat_jalan import buat_packing_list, buat_surat_jalan
from .pdf import ke_pdf, libreoffice_ada

NOMOR_KOSONG = "________"


def nama_aman(teks: str) -> str:
    """Ubah nama tab jadi nama berkas yang aman."""
    teks = re.sub(r"[^\w\s\-()&]", "", teks)
    return re.sub(r"\s+", "_", teks.strip())


def buat_berkas(
    cfg,
    order,
    keputusan,
    folder: Path,
    nomor: str = NOMOR_KOSONG,
    *,
    pdf: bool = False,
    sertakan_packing_list: bool = True,
    cetak=None,
) -> list[Path]:
    """Tulis dokumen satu PO ke `folder`. Mengembalikan daftar berkas yang jadi.

    Urutan dokumen mengikuti penjelasan Yosua 12 September 2026: Invoice,
    Surat Jalan, dan Faktur Pajak adalah yang diminta. Packing List ikut dibuat
    selama `sertakan_packing_list` masih True, karena belum dipastikan apakah
    masih dipakai.
    """
    cust = cfg.customer.cari(order.nama_tab)
    pt = cfg.perusahaan.untuk(cust)
    folder.mkdir(parents=True, exist_ok=True)
    aman = nama_aman(order.nama_tab)

    tugas = [
        ("INVOICE",
         lambda ws: buat_invoice(ws, order, keputusan, cust, pt, cfg.pengaturan, nomor)),
        ("SURAT_JALAN",
         lambda ws: buat_surat_jalan(ws, order, cust, pt, nomor)),
        ("FAKTUR_PAJAK",
         lambda ws: buat_faktur_pajak(ws, order, keputusan, cust, pt, cfg.pengaturan, nomor)),
    ]
    if sertakan_packing_list:
        tugas.append(
            ("PACKING_LIST", lambda ws: buat_packing_list(ws, order, cust, pt, nomor))
        )

    # Proforma HANYA untuk customer yang fakturnya dipecah per ukuran
    # (Haritsa & Katamama). Permintaan Yosua 17 September 2026; customer lain
    # tidak pernah memintanya, jadi jangan diterbitkan untuk semua.
    if cust and cust.pecah_per_ukuran:
        tugas.append(
            ("PROFORMA",
             lambda ws: buat_proforma(ws, order, keputusan, cust, pt,
                                      cfg.pengaturan, nomor))
        )

    dibuat: list[Path] = []
    for nama, fungsi in tugas:
        wb = Workbook()
        ws = wb.active
        ws.title = nama.replace("_", " ").title()[:31]
        fungsi(ws)
        p = folder / f"{nama}_{aman}.xlsx"
        wb.save(p)
        dibuat.append(p)

    if pdf:
        if not libreoffice_ada():
            if cetak:
                cetak("  (PDF dilewati: LibreOffice tidak terpasang di komputer ini.")
                cetak("   Di Ubuntu/Debian: sudo apt install libreoffice-calc)")
        else:
            for p in list(dibuat):
                hasil_pdf, pesan = ke_pdf(p, folder)
                if hasil_pdf:
                    dibuat.append(hasil_pdf)
                elif cetak:
                    cetak(f"  (PDF {p.name} dilewati: {pesan})")
    return dibuat
