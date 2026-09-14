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

KOLOM_TERAKHIR = 8          # A..H, persis seperti faktur asli DPM
BARIS_KOP = 2               # kop mulai baris 2 (baris 1 dibiarkan kosong)
BARIS_JUDUL = 12            # baris judul tabel: 12-14, tiga baris bertingkat
BARIS_DATA = 15             # baris pertama data
# Lebar kolom diambil dari faktur asli DPM 0010726 BABY WISE. Jumlah A..H
# 107,7 satuan — muat satu halaman A4 tegak dengan margin 0,15 inci.
# Versi lama memakai kolom C selebar 39,4 dan tabelnya terpotong saat dicetak.
LEBAR = {1: 4.0, 2: 15.6, 3: 29.9, 4: 4.9, 5: 12.1, 6: 12.7, 7: 13.6, 8: 15.6}

# Jatah lebar A..H. Faktur asli memakai 107,7 satuan dengan skala cetak 97%.
# Karena `fitToWidth` menyusutkan sendiri isinya agar selebar satu halaman,
# jatah ini boleh melar sampai MAKS_JATAH tanpa ada yang terpotong ke samping —
# yang terjadi hanya hurufnya mengecil. 135 satuan setara skala +-78%, masih
# terbaca, dan itu batas yang benar-benar dibutuhkan: invoice Haritsa yang
# dipecah per ukuran butuh kode 23 huruf dan deskripsi 43 huruf sekaligus.
JATAH_A4 = sum(LEBAR.values())
MAKS_JATAH = 135.0
MIN_KODE, MAKS_KODE = 11.0, 23.0
MIN_DESKRIPSI = 22.0


def lebar_menyesuaikan(baris) -> dict:
    """Lebarkan kolom ARTICLE CODE dan DESKRIPSI mengikuti isi terpanjang.

    Lebar tetap seperti faktur asli memotong kode panjang macam
    `71092.S (Bottom/Celana)` menjadi `71092.S (Bottom/Celan` — di invoice itu
    fatal, customer tidak bisa tahu barang mana yang ditagih.

    Yang melebar hanya B dan C, dan keduanya berbagi satu jatah tetap, jadi
    jumlah A..H tidak pernah berubah dan dokumennya tetap muat A4 tegak.
    """
    lebar = dict(LEBAR)
    if not baris:
        return lebar
    huruf = 1.05  # perkiraan lebar satu huruf Calibri 10 dalam satuan kolom
    kode = max(len(str(b.kode)) for b in baris) * huruf + 1.5
    lebar[2] = min(max(kode, MIN_KODE), MAKS_KODE)

    deskripsi = max(len(str(b.deskripsi)) for b in baris) * huruf + 1.5
    lain = sum(v for k, v in lebar.items() if k != 3)
    # Pakai lebar seperlunya. Kalau totalnya masih di bawah jatah faktur asli,
    # sisanya diberikan ke deskripsi supaya bentuknya tetap seperti aslinya.
    lebar[3] = max(deskripsi, JATAH_A4 - lain, MIN_DESKRIPSI)
    if lain + lebar[3] > MAKS_JATAH:
        lebar[3] = max(MAKS_JATAH - lain, MIN_DESKRIPSI)
    return lebar


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


def _persen_tertulis(order: Order, keputusan: KeputusanNett, pengaturan) -> tuple:
    """Tulisan diskon di baris judul, meniru faktur asli.

    Faktur asli menulisnya dengan dua cara:
      - satu angka persen, contoh 25%            -> Baby Wise 0010726
      - gabungan dasar + tambahan, "22% + 1,5%"  -> Katamama 0250726

    Yang kedua dipakai kalau nilai bersihnya diambil dari kolom CBD/COD, karena
    di situ ada potongan tambahan di atas diskon dasar.
    """
    from ..nilai_bersih import tarif_tambahan_tertulis

    kotor = sum(b.nilai_kotor for blok in order.blok for b in blok.baris)
    efektif = persen_diskon_efektif(kotor, keputusan.nett_total)
    tambahan = tarif_tambahan_tertulis(keputusan.kolom_sumber)
    if tambahan:
        dasar = max(0.0, efektif - tambahan)
        teks = (f"{dasar * 100:.0f}% + "
                f"{tambahan * 100:.1f}%".replace(".", ","))
        return teks, None
    return None, efektif


def buat_invoice(
    ws: Worksheet,
    order: Order,
    keputusan: KeputusanNett,
    customer,
    perusahaan,
    pengaturan,
    nomor: str,
    tanggal_dokumen: Optional[date] = None,
) -> None:
    """Tulis invoice ke satu lembar, mengikuti faktur asli CV Dwi Putra Mandiri.

    Tata letaknya disalin dari berkas asli di Drive, bukan dikarang: kop dengan
    ruang logo, baris FAKTUR No., baris BRAND, judul tabel tiga tingkat, lalu
    penutup Subtotal / Diskon / Total / Uang Muka / DPP / PPN / Total di kolom
    G-H dan informasi rekening di kolom B.
    """
    tanggal = tanggal_dokumen or order.tanggal_po or date.today()

    gaya.kop_dpm(
        ws, perusahaan,
        nama_customer=(customer.nama_di_dokumen if customer else "") or order.customer_kunci,
        alamat_customer=(customer.alamat if customer else ""),
        tanggal_dokumen=tanggal,
        baris_mulai=BARIS_KOP,
        kolom_kanan=6,
    )
    gaya.judul_faktur(ws, 9, nomor)

    # ---- isi tabel disusun dulu: bentuk judulnya ikut ada/tidaknya diskon
    baris = susun_baris(
        order, keputusan,
        pecah_per_ukuran=bool(customer and customer.pecah_per_ukuran),
        akhiran_y=pengaturan.akhiran_y_untuk_angka,
    )
    ada_diskon = any(b.diskon > 0.5 for b in baris)

    # ---- judul tabel: tiga baris bertingkat ----------------------------
    j = BARIS_JUDUL
    teks_persen, angka_persen = _persen_tertulis(order, keputusan, pengaturan)
    tegak = [(1, "No."), (2, "ARTICLE CODE"), (3, "DESKRIPSI BARANG"), (8, "Jumlah")]
    for kolom, teks in tegak:
        ws.merge_cells(start_row=j, start_column=kolom, end_row=j + 2, end_column=kolom)
        gaya.sel_judul(ws, j, kolom, teks)
    gaya.sel_judul(ws, j, 4, "Qty")
    ws.merge_cells(start_row=j + 1, start_column=4, end_row=j + 2, end_column=4)
    gaya.sel_judul(ws, j + 1, 4, "PCS")

    if ada_diskon:
        # Bentuk berdiskon, seperti 0010726 BABY WISE dan 0310726 MAE BEBE:
        # Harga/Satuan, Diskon (persennya di F13:F14), lalu Nilai/Diskon.
        gaya.sel_judul(ws, j, 5, "Harga")
        ws.merge_cells(start_row=j + 1, start_column=5, end_row=j + 2, end_column=5)
        gaya.sel_judul(ws, j + 1, 5, "Satuan")
        gaya.sel_judul(ws, j, 7, "Nilai")
        ws.merge_cells(start_row=j + 1, start_column=7, end_row=j + 2, end_column=7)
        gaya.sel_judul(ws, j + 1, 7, "Diskon")
        gaya.sel_judul(ws, j, 6, "Diskon ")
        ws.merge_cells(start_row=j + 1, start_column=6, end_row=j + 2, end_column=6)
        if teks_persen:
            gaya.sel_judul(ws, j + 1, 6, teks_persen)
        else:
            sel = gaya.sel_judul(ws, j + 1, 6, angka_persen or 0)
            sel.number_format = "0%"
    else:
        # Bentuk tanpa diskon, seperti 0020826 CV. BASA MANDIRI: kolom
        # Harga melebar menutupi E:G dan kolom Diskon tidak dicetak sama
        # sekali. Mencetak kolom diskon berisi nol hanya membingungkan.
        ws.merge_cells(start_row=j, start_column=5, end_row=j + 2, end_column=7)
        gaya.sel_judul(ws, j, 5, "Harga")
        for kolom in (6, 7):
            for baris_judul in range(j, j + 3):
                gaya.sel_judul(ws, baris_judul, kolom, None)
    # Lebar kolom dipasang di sini, setelah isinya diketahui.
    for kolom, lebar in lebar_menyesuaikan(baris).items():
        ws.column_dimensions[gaya.huruf(kolom)].width = lebar

    r = BARIS_DATA
    for i, b in enumerate(baris, start=1):
        gaya.sel_isi(ws, r, 1, i, rata="center")
        gaya.sel_isi(ws, r, 2, b.kode)
        gaya.sel_isi(ws, r, 3, b.deskripsi)
        gaya.sel_isi(ws, r, 4, b.qty, rata="center")
        if ada_diskon:
            gaya.sel_isi(ws, r, 5, b.harga, angka=gaya.FORMAT_RP)
            gaya.sel_isi(ws, r, 6, (b.diskon / b.qty) if b.qty else 0.0,
                         angka=gaya.FORMAT_RP)
            gaya.sel_isi(ws, r, 7, b.diskon, angka=gaya.FORMAT_RP)
            # Kolom Jumlah berisi nilai SETELAH diskon. Dibuktikan pada
            # faktur asli 0310726 MAE BEBE baris 1: 18 x 62.900 = 1.132.200,
            # diskon 283.050, kolom H = 849.150. Jumlah seluruh kolom H sama
            # dengan baris "Total", bukan "Subtotal".
            gaya.sel_isi(ws, r, 8, b.nett, angka=gaya.FORMAT_RP)
        else:
            # Tanpa diskon, Harga menempati sel gabungan E:G dan
            # Jumlah = qty x harga, persis 0020826 CV. BASA MANDIRI.
            ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7)
            gaya.sel_isi(ws, r, 5, b.harga, angka=gaya.FORMAT_RP)
            for kolom in (6, 7):
                gaya.sel_isi(ws, r, kolom, None)
            gaya.sel_isi(ws, r, 8, b.kotor, angka=gaya.FORMAT_RP)
        r += 1
    akhir = r - 1
    gaya.beri_garis(ws, j, 1, akhir, KOLOM_TERAKHIR)

    # ---- penutup di kolom G-H ------------------------------------------
    kotor = sum(b.kotor for b in baris)
    diskon = sum(b.diskon for b in baris)
    total = kotor - diskon
    tarif = pengaturan.tarif_ppn if perusahaan.kenakan_ppn else 0.0
    dpp = total / (1 + tarif) if tarif else total
    ppn = total - dpp

    label_ppn = f"PPN {tarif * 100:.0f}%" if tarif else "PPN (tidak dikenakan)"
    # Faktur asli TANPA diskon (0020826 CV. BASA MANDIRI) tidak memuat baris
    # Subtotal dan Diskon sama sekali — langsung Total. Baris berisi nol hanya
    # menimbulkan pertanyaan. Yang berdiskon tetap memuat keduanya, seperti
    # 0010726 BABY WISE.
    penutup = []
    if ada_diskon:
        penutup += [("Subtotal", kotor), ("Diskon", diskon)]
    penutup += [
        ("Total", total), ("Uang Muka", 0),
        ("DPP", dpp), (label_ppn, ppn), ("Total", dpp + ppn),
    ]
    p = akhir + 1
    for i, (label, nilai) in enumerate(penutup):
        tebal = i == 0 or i == len(penutup) - 1
        gaya.sel_isi(ws, p + i, 7, label, tebal=True)
        # "Uang Muka" nol ditulis polos tanpa "Rp", sama seperti faktur asli.
        angka = gaya.FORMAT_ANGKA if label == "Uang Muka" else gaya.FORMAT_RP
        gaya.sel_isi(ws, p + i, 8, nilai, angka=angka, tebal=tebal)

    # ---- rekening di kolom A, sejajar penutup --------------------------
    # Faktur asli menaruhnya di kolom A (0020826 A28:A31), bukan kolom B.
    rekening = perusahaan.baris_rekening()
    for i, teks in enumerate(rekening):
        gaya.sel_isi(ws, p + 1 + i, 1, teks, tebal=True)

    # Kedua blok diberi garis kotak, persis seperti faktur asli.
    gaya.kotak(ws, p, 7, p + len(penutup) - 1, 8)
    if rekening:
        gaya.kotak(ws, p + 1, 1, p + len(rekening), 3)

    baris_hormat = p + len(penutup)
    ws.merge_cells(start_row=baris_hormat, start_column=7, end_row=baris_hormat, end_column=8)
    gaya.sel_isi(ws, baris_hormat, 7, "Hormat kami,", rata="center")

    gaya.siapkan_cetak(ws, KOLOM_TERAKHIR)

    # Nilai balik ini dipakai laporan dan tes. Bentuknya sengaja dipertahankan
    # walaupun tata letaknya berubah, supaya tidak ada pemanggil yang rusak.
    termin = customer.termin_hari if customer else pengaturan.termin_hari_default
    return {
        "baris_invoice": len(baris),
        "qty": sum(b.qty for b in baris),
        "kotor": kotor,
        "nett": total,
        "persen_efektif": persen_diskon_efektif(kotor, total),
        "dpp": dpp,
        "ppn": ppn,
        "total_setelah_muka": dpp + ppn,
        "termin_hari": termin,
        "jatuh_tempo": tanggal + timedelta(days=termin) if termin else None,
        "kena_ppn": bool(perusahaan.kenakan_ppn),
        "perusahaan": getattr(perusahaan, "nama", ""),
    }
