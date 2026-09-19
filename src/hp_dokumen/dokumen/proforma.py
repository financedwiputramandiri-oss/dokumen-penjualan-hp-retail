"""Proforma Invoice — khusus Haritsa & Katamama.

Diminta Yosua 17 September 2026, dengan acuan foto sebuah Faktur Penjualan
yang DITERIMA Katamama dari pemasok lain (PT. Hypefast Distribusi Nusantara).

**Yang diambil dari foto itu hanya TATA LETAKNYA.** Nama, alamat, dan logo di
dokumen ini tetap milik perusahaan pemroses sendiri (CV Dwi Putra Mandiri atau
CV Mutiara Timur Nusantara), diambil dari `config/perusahaan.yaml`. Menerbitkan
dokumen atas nama perusahaan lain jelas tidak boleh.

Bedanya dengan Invoice biasa:

| | Invoice | Proforma |
|---|---|---|
| Kolom | No, Kode, Deskripsi, Qty, Harga, Diskon, Nilai, Jumlah | NO, SKU, KETERANGAN, QTY, UNIT, HARGA, DISK%, PAJAK%, JUMLAH |
| Baris | per artikel + ukuran | per artikel + **VARIAN** + ukuran |
| Penutup | Subtotal..Total | Sub Total .. Grand Total, sepuluh baris |
| Kepala | FAKTUR No. + BRAND | judul besar + blok No./Tanggal/Term/Jatuh Tempo |

Permintaan Yosua yang paling menentukan: *"pada kolom keterangan saya mau ada
level variannya di column keterangan produk seperti pada foto"*. Karena itu
baris proforma dipecah sampai ke WARNA, sementara invoice biasa menjumlahkan
semua warna. Warnanya diambil dari kolom COLOUR order sheet, tidak ditebak.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from openpyxl.worksheet.worksheet import Worksheet

from ..model import KeputusanNett, Order
from . import gaya
from .invoice import _persen_ringkas, _persen_tertulis, susun_baris

KOLOM_TERAKHIR = 9          # A..I
KOL_QTY = 4                 # kolom QTY, tempat angka Total Qty
BARIS_KOP = 1

# Lebar kolom A..I. Jumlahnya 117 satuan, masih di bawah batas 135 yang sudah
# terbukti muat A4 tegak (CLAUDE.md bagian 19).
# Kolom DISK% (7) harus muat tulisan gabungan "22% + 1.5%" — 10 huruf.
# Pada 8,5 satuan angkanya terpotong jadi "2% + 1.5%", terbaca 2% bukan 22%.
LEBAR = {1: 4.5, 2: 14.0, 3: 35.5, 4: 6.5, 5: 7.5, 6: 13.0, 7: 13.0, 8: 8.5, 9: 14.5}

JUDUL_KOLOM = [
    (1, "NO"), (2, "SKU"), (3, "KETERANGAN"), (4, "QTY"), (5, "UNIT"),
    (6, "HARGA"), (7, "DISK%"), (8, "PAJAK%"), (9, "JUMLAH"),
]

# Baris penutup, persis urutan di foto. Yang tidak dihitung program dibiarkan
# nol supaya divisi bisa mengisinya sendiri sebelum dikirim.
PENUTUP_NOL = [
    "Diskon Lainnya", "Potongan Biaya", "Pajak", "Ongkos Kirim",
    "Diskon Ongkos Kirim", "Biaya Lainnya", "Asuransi",
]

UNIT_BAWAAN = "Buah"
HURUF_JUDUL_DOK = 20
HURUF_JUDUL_KOLOM = 11
HURUF_ISI = 11
TINGGI_DATA = 28.5
TINGGI_PENUTUP = 22.5       # baris Total Qty & blok Sub Total..Grand Total


KOL_LABEL_PENUTUP = 6       # label penutup digabung F:H


def _label_nilai(ws, baris: int, label: str, nilai, *, angka=None, tebal=False):
    """Satu baris blok kanan: label digabung F:H, nilainya di I.

    Dulu hanya G:H (17 satuan) dan label terpanjang "Diskon Ongkos Kirim"
    tercetak berdempetan dengan angkanya.
    """
    ws.merge_cells(start_row=baris, start_column=KOL_LABEL_PENUTUP,
                   end_row=baris, end_column=8)
    gaya.sel_isi(ws, baris, KOL_LABEL_PENUTUP, label, ukuran=HURUF_ISI,
                 tebal=tebal, rata="right")
    for k in (7, 8):
        gaya.sel_isi(ws, baris, k, None, ukuran=HURUF_ISI)
    return gaya.sel_isi(ws, baris, 9, nilai, angka=angka or gaya.FORMAT_RP,
                        ukuran=HURUF_ISI, tebal=tebal)




def _lebar_kolom_px(kolom: int) -> float:
    """Lebar satu kolom dalam piksel.

    Rumus bakunya untuk huruf bawaan Calibri 11: px = lebar x 7 + 5.
    """
    return LEBAR[kolom] * 7 + 5


def keterangan(b) -> str:
    """Isi kolom KETERANGAN: nama barang, varian, lalu ukurannya.

    Bentuknya mengikuti foto — produk lalu variannya — dengan pemisah ukuran
    "Uk." yang sudah dipakai di invoice sejak CLAUDE.md bagian 16.

        SoftAir Short Set - New Baby Size Uk. 3-6M - Lion Mouse

    Kalau warnanya kosong di order sheet, bagian variannya tidak dicetak sama
    sekali; jangan diisi tanda hubung menggantung.
    """
    return f"{b.deskripsi} - {b.warna}" if b.warna else b.deskripsi


def buat_proforma(
    ws: Worksheet,
    order: Order,
    keputusan: KeputusanNett,
    customer,
    perusahaan,
    pengaturan,
    nomor: str,
    tanggal_dokumen: Optional[date] = None,
    nomor_referensi: str = "",
) -> dict:
    tanggal = tanggal_dokumen or order.tanggal_po or date.today()
    termin = getattr(customer, "termin_hari", None) or pengaturan.termin_hari_default
    jatuh_tempo = tanggal + timedelta(days=int(termin))

    # ---- kepala dokumen ------------------------------------------------
    r = BARIS_KOP
    ws.merge_cells(start_row=r, start_column=1, end_row=r + 4, end_column=2)
    gaya.pasang_logo(ws, perusahaan, r,
                     _lebar_kolom_px(1) + _lebar_kolom_px(2))

    gaya.sel_isi(ws, r, 3, perusahaan.nama, tebal=True, ukuran=14)
    for i, teks in enumerate(perusahaan.alamat_baris, start=1):
        gaya.sel_isi(ws, r + i, 3, teks, ukuran=10)

    ws.merge_cells(start_row=r, start_column=6, end_row=r, end_column=9)
    gaya.sel_isi(ws, r, 6, "PROFORMA INVOICE", tebal=True,
                 ukuran=HURUF_JUDUL_DOK, rata="right")

    # blok No./Tanggal/No. Ref./Term/Jatuh Tempo di kanan
    info = [
        ("No. Proforma", nomor or ""),
        ("Tanggal", gaya.tanggal_indonesia(tanggal)),
        # No. Ref. di foto (`N260910-KATAMAMATPS-503`) berasal dari sistem
        # pemasok lain dan tidak ada padanannya di order sheet. Dikosongkan
        # untuk diisi tangan — jangan ditebak dari nama tab.
        ("No. Ref.", nomor_referensi),
        ("Term", f"{int(termin)} Hari"),
        ("Jatuh Tempo", gaya.tanggal_indonesia(jatuh_tempo)),
    ]
    for i, (label, nilai) in enumerate(info):
        b = r + 2 + i
        gaya.sel_isi(ws, b, 7, label, ukuran=HURUF_ISI, rata="right")
        ws.merge_cells(start_row=b, start_column=8, end_row=b, end_column=9)
        # Spasi di depan: tanpa itu label di G dan nilainya di H tercetak
        # berdempetan jadi "No. Proforma0400826".
        gaya.sel_isi(ws, b, 8, f"  {nilai}" if nilai else "",
                     tebal=True, ukuran=HURUF_ISI)

    # blok "Kepada"
    b = r + 7
    ws.merge_cells(start_row=b, start_column=1, end_row=b, end_column=2)
    gaya.sel_isi(ws, b, 1, "Kepada", ukuran=HURUF_ISI, rata="center")
    nama_cust = (customer.nama_di_dokumen if customer else "") or order.customer_kunci
    ws.merge_cells(start_row=b, start_column=3, end_row=b, end_column=6)
    gaya.sel_isi(ws, b, 3, nama_cust, tebal=True, ukuran=14)
    alamat = gaya.pecah_alamat(customer.alamat if customer else "") or ["(alamat belum diisi)"]
    for i, teks in enumerate(alamat, start=1):
        ws.merge_cells(start_row=b + i, start_column=3, end_row=b + i, end_column=6)
        gaya.sel_isi(ws, b + i, 3, teks, ukuran=HURUF_ISI)

    # ---- tabel ---------------------------------------------------------
    j = b + max(len(alamat), 3) + 2
    for kolom, teks in JUDUL_KOLOM:
        gaya.sel_judul(ws, j, kolom, teks, ukuran=HURUF_JUDUL_KOLOM)
    ws.row_dimensions[j].height = 22.5

    # DISK% ditulis persis seperti di invoice: "22% + 1.5%" kalau potongannya
    # beruntun, "25%" kalau tunggal. Permintaan Yosua 17 September 2026 —
    # sebelumnya kolom ini berisi persen EFEKTIF (23,17) yang secara aritmetika
    # benar tapi tidak dikenali customer.
    teks_persen, angka_persen = _persen_tertulis(order, keputusan, pengaturan)
    tulisan_diskon = teks_persen or _persen_ringkas(angka_persen or 0.0)

    baris = susun_baris(
        order, keputusan,
        pecah_per_ukuran=bool(customer and customer.pecah_per_ukuran),
        akhiran_y=pengaturan.akhiran_y_untuk_angka,
        pecah_per_warna=True,
    )

    r = j + 1
    for i, x in enumerate(baris, start=1):
        gaya.sel_isi(ws, r, 1, i, rata="center", ukuran=HURUF_ISI)
        gaya.sel_isi(ws, r, 2, x.kode, ukuran=HURUF_ISI, lipat=True)
        gaya.sel_isi(ws, r, 3, keterangan(x), ukuran=HURUF_ISI, lipat=True)
        gaya.sel_isi(ws, r, 4, x.qty, rata="center", ukuran=HURUF_ISI)
        gaya.sel_isi(ws, r, 5, UNIT_BAWAAN, rata="center", ukuran=HURUF_ISI)
        gaya.sel_isi(ws, r, 6, x.harga, angka=gaya.FORMAT_RP, ukuran=HURUF_ISI)
        gaya.sel_isi(ws, r, 7, tulisan_diskon, ukuran=HURUF_ISI, rata="center")
        gaya.sel_isi(ws, r, 8, 0, angka="0.00", ukuran=HURUF_ISI, rata="center")
        gaya.sel_isi(ws, r, 9, x.nett, angka=gaya.FORMAT_RP, ukuran=HURUF_ISI)
        ws.row_dimensions[r].height = TINGGI_DATA
        r += 1
    akhir = r - 1
    gaya.beri_garis(ws, j, 1, akhir, KOLOM_TERAKHIR)

    # ---- penutup -------------------------------------------------------
    kotor = sum(x.kotor for x in baris)
    nett = sum(x.nett for x in baris)
    qty = sum(x.qty for x in baris)

    # ---- baris Total Qty: menutup tabel SAMPAI KOLOM QTY saja -----------
    # Kotaknya BERHENTI di kolom QTY. Sempat digariskan sampai kolom JUMLAH
    # supaya tabelnya "penuh", tapi Yosua mencoret bagian itu (17 Sep 2026):
    # kolom UNIT sampai JUMLAH jadi deretan kotak kosong yang tidak menampung
    # apa pun, dan justru terlihat seperti baris yang lupa diisi.
    #
    # Yang dijumlahkan memang cuma qty, jadi kotaknya berhenti di situ.
    tq = akhir + 1
    ws.merge_cells(start_row=tq, start_column=1, end_row=tq, end_column=3)
    gaya.sel_isi(ws, tq, 1, "Total Qty", ukuran=HURUF_ISI, tebal=True, rata="center")
    gaya.sel_isi(ws, tq, 4, qty, ukuran=HURUF_ISI, tebal=True, rata="center",
                 angka="#,##0")
    gaya.beri_garis(ws, tq, 1, tq, KOL_QTY)

    # ---- blok nilai, MULAI DI BARIS YANG SAMA ---------------------------
    # Sub Total sebaris dengan Total Qty, persis seperti di foto. Sempat
    # diturunkan satu baris, dan akibatnya sisi kanan tabel punya pita kosong
    # setinggi baris Total Qty — tabelnya terlihat TERPUTUS antara baris
    # barang terakhir dan blok Sub Total. Yosua menandainya 17 Sep 2026.
    _label_nilai(ws, tq, "Sub Total", kotor)
    _label_nilai(ws, tq + 1, "Diskon", kotor - nett)
    for i, label in enumerate(PENUTUP_NOL, start=2):
        _label_nilai(ws, tq + i, label, 0)
    baris_total = tq + 2 + len(PENUTUP_NOL)
    _label_nilai(ws, baris_total, "Grand Total", nett, tebal=True)
    gaya.beri_garis(ws, tq, KOL_LABEL_PENUTUP, baris_total, KOLOM_TERAKHIR)

    # Tinggi baris penutup disamakan supaya sambung dengan tabel di atasnya.
    # Bawaannya +-15 sedangkan baris barang 28,5, jadi blok penutup terlihat
    # jauh lebih rapat dan seperti tabel yang lain.
    for r in range(tq, baris_total + 1):
        ws.row_dimensions[r].height = TINGGI_PENUTUP

    gaya.sel_isi(ws, tq + 2, 1, "Catatan :", ukuran=HURUF_ISI)

    for kolom, lebar in LEBAR.items():
        ws.column_dimensions[gaya.huruf(kolom)].width = lebar
    gaya.siapkan_cetak(ws, KOLOM_TERAKHIR)

    return {
        "baris": len(baris),
        "qty": qty,
        "kotor": kotor,
        "nett": nett,
    }
