"""Invoice.

Beda dengan Surat Jalan: invoice TIDAK dipecah per tabel. Satu tabel menerus
untuk seluruh PO. Warna tidak pernah masuk invoice.

Bawaan: satu baris per artikel, semua warna dan ukuran dijumlahkan.
Pengecualian Haritsa & Katamama: dipecah per ukuran, satu baris per artikel per
ukuran. Label ukuran ikut header tabel ASAL barang itu, bukan daftar global.

Baris diskon CBD/COD tidak dicetak — faktur asli DPM tidak memuatnya. Nilai
bersihnya tetap yang dipakai, jadi persen diskon di baris judul dihitung mundur
dari nilai bersih.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.worksheet import Worksheet

from ..model import KeputusanNett, Order
from ..nilai_bersih import nett_baris, persen_diskon_efektif
from ..ukuran import bagi_rata_nilai, deskripsi_dengan_ukuran
from . import gaya

JUDUL_KOLOM = [
    "No.", "ARTICLE CODE", "DESKRIPSI BARANG", "Qty (PCS)",
    "Harga (Satuan)", "Diskon (%)", "Nilai (Diskon)", "Jumlah",
]
KOLOM_TERAKHIR = 8


@dataclass
class BarisInvoice:
    kode: str
    deskripsi: str
    qty: int
    harga: float
    kotor: float
    nett: float

    @property
    def diskon(self) -> float:
        return self.kotor - self.nett


def susun_baris(order: Order, keputusan: KeputusanNett, *, pecah_per_ukuran: bool,
                akhiran_y: bool) -> list[BarisInvoice]:
    """Ubah baris order sheet jadi baris invoice.

    Nilai bersih diambil per baris dari kolom sumbernya, lalu dijumlahkan.
    Saat dipecah per ukuran, nilai bersih satu baris dibagi ke tiap ukuran
    menurut qty dengan metode sisa terbesar, supaya jumlahnya tetap sama persis.
    """
    kumpul: dict[tuple, BarisInvoice] = {}
    urutan: list[tuple] = []

    for blok in order.blok:
        for b in blok.baris:
            n = nett_baris(b, keputusan.kolom)
            if not pecah_per_ukuran:
                kunci = (b.kode, b.nama)
                if kunci not in kumpul:
                    kumpul[kunci] = BarisInvoice(b.kode, b.nama, 0, b.harga, 0.0, 0.0)
                    urutan.append(kunci)
                x = kumpul[kunci]
                x.qty += b.qty
                x.kotor += b.nilai_kotor
                x.nett += n
                continue

            # dipecah per ukuran — label ikut blok asal barang ini
            posisi = [i for i, q in enumerate(b.qty_per_ukuran) if q]
            bobot = [b.qty_per_ukuran[i] for i in posisi]
            bagian_nett = bagi_rata_nilai(n, bobot)
            bagian_kotor = bagi_rata_nilai(b.nilai_kotor, bobot)
            for k, i in enumerate(posisi):
                label = blok.label_ukuran[i] or f"Uk.{i + 1}"
                desk = deskripsi_dengan_ukuran(b.nama, label, akhiran_y)
                kunci = (b.kode, desk)
                if kunci not in kumpul:
                    kumpul[kunci] = BarisInvoice(b.kode, desk, 0, b.harga, 0.0, 0.0)
                    urutan.append(kunci)
                x = kumpul[kunci]
                x.qty += b.qty_per_ukuran[i]
                x.kotor += bagian_kotor[k]
                x.nett += bagian_nett[k]

    return [kumpul[k] for k in urutan]


def buat_invoice(
    ws: Worksheet,
    order: Order,
    keputusan: KeputusanNett,
    customer,
    perusahaan,
    pengaturan,
    nomor: str,
    *,
    uang_muka: float = 0.0,
    tanggal_dokumen: Optional[date] = None,
) -> dict:
    tanggal_dokumen = tanggal_dokumen or order.tanggal_po
    pecah = bool(customer and customer.pecah_per_ukuran)
    baris_inv = susun_baris(
        order, keputusan,
        pecah_per_ukuran=pecah,
        akhiran_y=pengaturan.akhiran_y_untuk_angka,
    )

    r = gaya.tulis_kop(
        ws, perusahaan,
        kolom_terakhir=KOLOM_TERAKHIR,
        nama_customer=customer.nama_di_dokumen if customer else "",
        alamat_customer=customer.alamat if customer else "",
        tanggal_dokumen=tanggal_dokumen,
    )

    gaya.judul(ws, r, 1, "INVOICE", ukuran=16)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=KOLOM_TERAKHIR)
    r += 1
    termin = customer.termin_hari if customer else pengaturan.termin_hari_default
    jatuh_tempo = (tanggal_dokumen + timedelta(days=termin)) if tanggal_dokumen else None
    info = ws.cell(
        r, 1,
        f"No. {nomor}    |    PO: {order.nama_tab}    |    "
        f"Termin: {termin} hari    |    Jatuh tempo: {gaya.tanggal_indonesia(jatuh_tempo) or '-'}",
    )
    info.font = Font(name=gaya.FONT, size=9)
    info.alignment = Alignment(horizontal="center")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=KOLOM_TERAKHIR)
    r += 2

    kotor_total = sum(x.kotor for x in baris_inv)
    nett_total = sum(x.nett for x in baris_inv)
    persen = persen_diskon_efektif(kotor_total, nett_total)

    awal_tabel = r
    gaya.baris_judul_tabel(ws, r, JUDUL_KOLOM)
    # persen diskon ditulis sekali di baris judul, seperti faktur asli
    sel_persen = ws.cell(r, 6, persen)
    sel_persen.number_format = "0.00%"
    sel_persen.font = Font(name=gaya.FONT, size=9, bold=True)
    sel_persen.alignment = Alignment(horizontal="center", vertical="center")
    r += 1

    for no, x in enumerate(baris_inv, start=1):
        ws.cell(r, 1, no).alignment = Alignment(horizontal="center")
        ws.cell(r, 2, x.kode)
        ws.cell(r, 3, x.deskripsi)
        c = ws.cell(r, 4, x.qty); c.alignment = Alignment(horizontal="center"); c.number_format = gaya.ANGKA
        c = ws.cell(r, 5, x.harga); c.number_format = gaya.RUPIAH
        c = ws.cell(r, 7, x.diskon); c.number_format = gaya.RUPIAH
        c = ws.cell(r, 8, x.nett); c.number_format = gaya.RUPIAH
        for cc in range(1, KOLOM_TERAKHIR + 1):
            ws.cell(r, cc).font = Font(name=gaya.FONT, size=9)
        r += 1

    gaya.beri_garis(ws, awal_tabel, 1, r - 1, KOLOM_TERAKHIR)
    akhir_tabel = r - 1
    r += 1

    # ---- penutup di kolom G-H ------------------------------------------
    tarif = pengaturan.tarif_ppn
    total_setelah_muka = nett_total - uang_muka
    dpp = total_setelah_muka / (1 + tarif) if tarif else total_setelah_muka
    ppn = total_setelah_muka - dpp

    penutup = [
        ("Subtotal", kotor_total),
        ("Diskon", -(kotor_total - nett_total)),
        ("Total", nett_total),
        ("Uang Muka", -uang_muka),
        ("DPP", dpp),
        (f"PPN {tarif:.0%}", ppn),
        ("Total", total_setelah_muka),
    ]
    awal_penutup = r
    for label, nilai in penutup:
        sel = ws.cell(r, 7, label)
        sel.font = Font(name=gaya.FONT, size=9, bold=label == "Total")
        sel.alignment = Alignment(horizontal="right")
        n = ws.cell(r, 8, nilai)
        n.number_format = gaya.RUPIAH
        n.font = Font(name=gaya.FONT, size=9, bold=label == "Total")
        r += 1
    gaya.beri_garis(ws, awal_penutup, 7, r - 1, 8)

    # ---- info rekening di kolom B --------------------------------------
    rb = awal_penutup
    for teks in perusahaan.rekening:
        sel = ws.cell(rb, 2, teks)
        sel.font = Font(name=gaya.FONT, size=9, bold=teks.endswith(":"))
        rb += 1

    r = max(r, rb) + 2
    sel = ws.cell(r, 7, "Hormat kami,")
    sel.font = Font(name=gaya.FONT, size=10)
    sel.alignment = Alignment(horizontal="center")
    sel = ws.cell(r + 4, 7, "(................................)")
    sel.font = Font(name=gaya.FONT, size=9)
    sel.alignment = Alignment(horizontal="center")

    gaya.atur_lebar(ws, {1: 5, 2: 18, 3: 46, 4: 9, 5: 14, 6: 10, 7: 15, 8: 16})
    gaya.siapkan_cetak(ws, KOLOM_TERAKHIR, landscape=False)

    return {
        "baris_invoice": len(baris_inv),
        "qty": sum(x.qty for x in baris_inv),
        "kotor": kotor_total,
        "nett": nett_total,
        "persen_efektif": persen,
        "dpp": dpp,
        "ppn": ppn,
        "total_setelah_muka": total_setelah_muka,
        "termin_hari": termin,
        "jatuh_tempo": jatuh_tempo,
        "dipecah_per_ukuran": pecah,
        "awal_tabel": awal_tabel,
        "akhir_tabel": akhir_tabel,
    }
