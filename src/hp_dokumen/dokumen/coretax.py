"""Faktur Pajak dalam format template resmi Coretax (DJP).

Tujuannya: berkas ini langsung bisa dimasukkan ke Converter Excel->XML milik
DJP, lalu XML-nya diunggah ke Coretax untuk membuat faktur pajak secara
borongan (bulk) — tanpa mengetik ulang satu per satu.

Susunan kolomnya MENGIKUTI TEMPLATE RESMI v1.6.1, bukan karangan:

    Faktur        : B1 = NPWP Penjual, judul di baris 3, data mulai baris 4,
                    ditutup 'END'
    DetailFaktur  : judul di baris 1, data mulai baris 2, ditutup 'END'

Aturan pengisian diambil dari lembar 'Keterangan' template itu. Yang paling
menentukan dan mudah salah:

  * Tanggal Faktur   : DD/MM/YYYY
  * Jenis Faktur     : selalu 'Normal'
  * Harga Satuan/DPP : nilai TANPA PPN. Harga di order sheet Happy Pumpkin
                       SUDAH termasuk PPN, jadi harus dibagi (1 + tarif).
  * DPP Nilai Lain   : diisi sama dengan DPP kalau tidak memakai nilai lain
  * DPP              : harus sama dengan Harga Satuan x Jumlah - Total Diskon
  * PPN              : Tarif PPN x DPP Nilai Lain
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from openpyxl import Workbook

JUDUL_FAKTUR = [
    "Baris", "Tanggal Faktur", "Jenis Faktur", "Kode Transaksi",
    "Keterangan Tambahan", "Dokumen Pendukung", "Period Dok Pendukung",
    "Referensi", "Cap Fasilitas", "ID TKU Penjual", "NPWP/NIK Pembeli",
    "Jenis ID Pembeli", "Negara Pembeli", "Nomor Dokumen Pembeli",
    "Nama Pembeli", "Alamat Pembeli", "Email Pembeli", "ID TKU Pembeli",
]
JUDUL_DETAIL = [
    "Baris", "Barang/Jasa", "Kode Barang Jasa", "Nama Barang/Jasa",
    "Nama Satuan Ukur", "Harga Satuan", "Jumlah Barang Jasa", "Total Diskon",
    "DPP", "DPP Nilai Lain", "Tarif PPN", "PPN", "Tarif PPnBM", "PPnBM",
]

BARIS_JUDUL_FAKTUR = 3
BARIS_DATA_FAKTUR = 4
BARIS_JUDUL_DETAIL = 1
BARIS_DATA_DETAIL = 2

# Nilai bawaan, semuanya dari lembar referensi template resmi
KODE_TRANSAKSI = "01"          # kepada selain Pemungut PPN
JENIS_FAKTUR = "Normal"
BARANG = "A"                   # A = Barang, B = Jasa
SATUAN_PCS = "UM.0021"         # Piece
NEGARA_INDONESIA = "IDN"
JENIS_ID_NPWP = "TIN"
NPWP_KOSONG = "0000000000000000"


def _bulat(x: float) -> float:
    """Dua angka di belakang koma, sesuai aturan template."""
    return round(x + 0.0, 2)


@dataclass
class HasilCoretax:
    faktur: int = 0
    detail: int = 0
    selisih_pembulatan: float = 0.0
    peringatan: list = field(default_factory=list)

    @property
    def siap_unggah(self) -> bool:
        return self.faktur > 0 and not self.peringatan


def _npwp_bersih(npwp: str) -> str:
    return "".join(ch for ch in (npwp or "") if ch.isdigit())


def susun_faktur(order, keputusan, customer, perusahaan, pengaturan, baris_invoice,
                 nomor: str, tanggal: Optional[date]) -> tuple:
    """Satu PO -> satu baris Faktur + beberapa baris DetailFaktur.

    `baris_invoice` adalah hasil `invoice.susun_baris`, supaya angka di faktur
    pajak PASTI sama dengan yang tercetak di invoice. Jangan dihitung ulang
    dari order sheet dengan cara lain.
    """
    tgl = tanggal or order.tanggal_po or date.today()
    tarif = pengaturan.tarif_ppn if perusahaan.kenakan_ppn else 0.0
    pembagi = 1 + tarif

    npwp_pembeli = _npwp_bersih(customer.npwp if customer else "")
    pakai_npwp = len(npwp_pembeli) >= 15

    baris_f = {
        "Tanggal Faktur": tgl.strftime("%d/%m/%Y"),
        "Jenis Faktur": JENIS_FAKTUR,
        "Kode Transaksi": KODE_TRANSAKSI,
        "Keterangan Tambahan": "",
        "Dokumen Pendukung": "",
        "Period Dok Pendukung": "",
        "Referensi": nomor if nomor and "_" not in nomor else order.nama_tab,
        "Cap Fasilitas": "",
        "ID TKU Penjual": getattr(perusahaan, "id_tku", "") or "",
        "NPWP/NIK Pembeli": npwp_pembeli if pakai_npwp else NPWP_KOSONG,
        "Jenis ID Pembeli": JENIS_ID_NPWP if pakai_npwp else "National ID",
        "Negara Pembeli": NEGARA_INDONESIA,
        "Nomor Dokumen Pembeli": "-" if pakai_npwp else "",
        "Nama Pembeli": (customer.nama_di_dokumen if customer else "") or order.customer_kunci,
        "Alamat Pembeli": (customer.alamat if customer else ""),
        "Email Pembeli": "",
        "ID TKU Pembeli": (getattr(customer, "id_tku", "") or "") if pakai_npwp else "000000",
    }

    detail = []
    for b in baris_invoice:
        if b.qty <= 0:
            continue
        harga_satuan = _bulat(b.harga / pembagi)
        dpp = _bulat(b.nett / pembagi)
        diskon = _bulat(harga_satuan * b.qty - dpp)
        if diskon < 0:          # pembulatan bisa membuatnya minus tipis
            harga_satuan = _bulat((b.nett / pembagi) / b.qty)
            diskon = _bulat(harga_satuan * b.qty - dpp)
        ppn = _bulat(dpp * tarif)
        detail.append({
            "Barang/Jasa": BARANG,
            "Kode Barang Jasa": "",
            "Nama Barang/Jasa": b.deskripsi,
            "Nama Satuan Ukur": SATUAN_PCS,
            "Harga Satuan": harga_satuan,
            "Jumlah Barang Jasa": b.qty,
            "Total Diskon": max(0.0, diskon),
            "DPP": dpp,
            "DPP Nilai Lain": dpp,
            "Tarif PPN": round(tarif * 100),
            "PPN": ppn,
            "Tarif PPnBM": 0,
            "PPnBM": 0,
        })
    # Nilai bersih yang SEHARUSNYA — dipakai tulis() untuk memeriksa apakah
    # pembulatan dua desimal membuat faktur pajak melenceng dari invoice.
    return baris_f, detail, keputusan.nett_total


def tulis(berkas, kumpulan, perusahaan) -> HasilCoretax:
    """Tulis satu berkas Coretax berisi BANYAK faktur sekaligus.

    `kumpulan` adalah daftar (baris_faktur, daftar_detail, nett_harapan)
    hasil susun_faktur.

    Selisih pembulatan diawasi di sini. Template DJP hanya mengizinkan dua
    angka di belakang koma, jadi selisih beberapa sen tidak terhindarkan; yang
    berbahaya adalah selisih yang membesar tanpa ketahuan.
    """
    BATAS_SELISIH = 1.0  # rupiah, per faktur
    hasil = HasilCoretax()
    wb = Workbook()

    ws = wb.active
    ws.title = "Faktur"
    ws.cell(1, 1, "NPWP Penjual")
    npwp_penjual = _npwp_bersih(getattr(perusahaan, "npwp", ""))
    ws.cell(1, 2, npwp_penjual)
    if not npwp_penjual:
        hasil.peringatan.append(
            f"NPWP {perusahaan.nama} belum diisi di config/perusahaan.yaml — "
            "kolom NPWP Penjual kosong dan Coretax akan menolak berkasnya."
        )
    for i, judul in enumerate(JUDUL_FAKTUR, start=1):
        ws.cell(BARIS_JUDUL_FAKTUR, i, judul)

    wd = wb.create_sheet("DetailFaktur")
    for i, judul in enumerate(JUDUL_DETAIL, start=1):
        wd.cell(BARIS_JUDUL_DETAIL, i, judul)

    r_f = BARIS_DATA_FAKTUR
    r_d = BARIS_DATA_DETAIL
    selisih_total = 0.0
    for urut, (baris_f, detail, nett_harapan) in enumerate(kumpulan, start=1):
        jadi = sum(d["DPP"] + d["PPN"] for d in detail)
        selisih = jadi - nett_harapan
        selisih_total += selisih
        if abs(selisih) > BATAS_SELISIH:
            hasil.peringatan.append(
                f"'{baris_f.get('Nama Pembeli')}': faktur pajak meleset "
                f"Rp{selisih:,.2f} dari nilai invoice. Periksa sebelum diunggah."
            )
        ws.cell(r_f, 1, urut)
        for i, judul in enumerate(JUDUL_FAKTUR[1:], start=2):
            ws.cell(r_f, i, baris_f.get(judul, ""))
        if not baris_f.get("ID TKU Penjual"):
            hasil.peringatan.append(
                "ID TKU Penjual (22 digit NITKU) belum diisi — wajib menurut DJP."
            )
        nama_pembeli = baris_f.get("Nama Pembeli")
        acuan = baris_f.get("Referensi") or "(tanpa acuan)"
        if not nama_pembeli:
            # Coretax menolak faktur tanpa nama pembeli. Ini terjadi kalau
            # tab PO belum dikenali di config/customer.csv — lebih sering
            # daripada yang disangka: order sheet Juli 2026 punya 22 tab
            # seperti itu dari 30.
            hasil.peringatan.append(
                f"{acuan}: nama pembeli kosong karena customernya belum "
                "terdaftar. Tambahkan di config/customer.csv — Coretax akan "
                "menolak faktur tanpa nama pembeli."
            )
        elif not baris_f.get("Alamat Pembeli"):
            hasil.peringatan.append(
                f"Alamat pembeli '{nama_pembeli}' belum diisi."
            )
        r_f += 1

        for d in detail:
            wd.cell(r_d, 1, urut)
            for i, judul in enumerate(JUDUL_DETAIL[1:], start=2):
                wd.cell(r_d, i, d.get(judul, ""))
            r_d += 1
        hasil.detail += len(detail)
        hasil.faktur += 1

    ws.cell(r_f, 1, "END")
    wd.cell(r_d, 1, "END")

    hasil.selisih_pembulatan = round(selisih_total, 2)
    # peringatan yang sama tidak perlu diulang puluhan kali
    hasil.peringatan = list(dict.fromkeys(hasil.peringatan))
    wb.save(berkas)
    return hasil
