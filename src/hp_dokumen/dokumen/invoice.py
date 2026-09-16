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

# Lebar A+B minimal supaya "FAKTUR No." (baris 9, tebal ukuran 18) tidak
# terpotong oleh sel nomor di kolom C. Sepuluh huruf pada ukuran 18 memakan
# +-16,4 satuan kolom; 17,5 memberi sedikit kelonggaran.
#
# Ketahuan pada PO yang kode artikelnya pendek (`OB.SS.1.S`, 9 huruf): B
# menyusut ke batas bawah 11,0 sehingga A+B hanya 15,0 dan judulnya tercetak
# "FAKTUR N". Di faktur asli B selebar 15,6-16,14 jadi masalah ini tidak
# pernah muncul. Melebarkan B tidak menambah jumlah lebar A..H — sisanya
# memang sedang menganggur di kolom deskripsi.
LEBAR_JUDUL_FAKTUR = 17.5

# Ukuran huruf dan tinggi baris, dari ENAM faktur asli yang sepakat:
# 0010726 & 0110826 BABY WISE, 0130826 BOBO SAMARINDA, 0420826 YULIS
# (keempatnya 13,5 / 26,25 / huruf 11), lalu 0310726 MAE BEBE dan
# 0400826 KATAMAMA yang sedikit lebih longgar. Diambil yang mayoritas.
# Versi lama memakai huruf 9 dan tinggi baris bawaan, jadi fakturnya
# jauh lebih rapat dan kecil daripada yang dipakai divisi.
TINGGI_JUDUL_INV = 13.5
TINGGI_DATA_INV = 26.25
HURUF_JUDUL_KOLOM_INV = 12
HURUF_ISI_INV = 11


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
    lebar[2] = min(max(kode, MIN_KODE, LEBAR_JUDUL_FAKTUR - lebar[1]), MAKS_KODE)

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
        # Diskon dasar dipulihkan dengan membagi, bukan mengurangi: kedua
        # potongan itu BERUNTUN (kotor x (1-dasar) x (1-tambahan)), bukan
        # dijumlahkan. Contoh Katamama 0220826: efektif 23,17%, tambahan
        # 1,5% -> dasar 22% persis. Kalau dikurangi, hasilnya 21,67%.
        dasar = 1.0 - (1.0 - efektif) / (1.0 - tambahan) if tambahan < 1 else 0.0
        teks = f"{_persen_ringkas(dasar)} + {_persen_ringkas(tambahan)}"
        return teks, None
    return None, efektif


def _persen_ringkas(pecahan: float) -> str:
    """Tulis persen tanpa nol di belakang koma, memakai TITIK desimal.

    Faktur asli menulisnya "22% + 1.5%" (0220826 KATAMAMA TAPOS, F14) —
    titik, bukan koma, dan tanpa angka nol yang tidak perlu.
    """
    angka = round(pecahan * 100, 2)
    utuh = f"{angka:.2f}".rstrip("0").rstrip(".")
    return f"{utuh}%"


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
    # Baris BRAND ADA di faktur asli (A10). Sempat dihapus karena satu
    # berkas menyendiri — lihat gaya.baris_merek().
    gaya.baris_merek(ws, 10)

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
        gaya.sel_judul(ws, j, kolom, teks, ukuran=HURUF_JUDUL_KOLOM_INV)
    gaya.sel_judul(ws, j, 4, "Qty", ukuran=HURUF_JUDUL_KOLOM_INV)
    ws.merge_cells(start_row=j + 1, start_column=4, end_row=j + 2, end_column=4)
    gaya.sel_judul(ws, j + 1, 4, "PCS", ukuran=HURUF_JUDUL_KOLOM_INV)

    if ada_diskon:
        # Bentuk berdiskon, seperti 0010726 BABY WISE dan 0310726 MAE BEBE:
        # Harga/Satuan, Diskon (persennya di F13:F14), lalu Nilai/Diskon.
        gaya.sel_judul(ws, j, 5, "Harga", ukuran=HURUF_JUDUL_KOLOM_INV)
        ws.merge_cells(start_row=j + 1, start_column=5, end_row=j + 2, end_column=5)
        gaya.sel_judul(ws, j + 1, 5, "Satuan", ukuran=HURUF_JUDUL_KOLOM_INV)
        gaya.sel_judul(ws, j, 7, "Nilai", ukuran=HURUF_JUDUL_KOLOM_INV)
        ws.merge_cells(start_row=j + 1, start_column=7, end_row=j + 2, end_column=7)
        gaya.sel_judul(ws, j + 1, 7, "Diskon", ukuran=HURUF_JUDUL_KOLOM_INV)
        # Letak sel persen ikut PANJANG tulisannya — begitu di faktur asli:
        #
        #   persen tunggal ("20%", "22%")  -> label "Diskon " sendirian di F12,
        #       angkanya digabung F13:F14   (0130826 BOBO, 0420826 YULIS)
        #   gabungan ("22% + 1.5%")        -> label digabung F12:F13,
        #       tulisannya sendirian di F14 (0220826 & 0400826 KATAMAMA)
        #
        # Tulisan gabungan memang lebih panjang, jadi diberi barisnya sendiri.
        if teks_persen:
            ws.merge_cells(start_row=j, start_column=6, end_row=j + 1, end_column=6)
            gaya.sel_judul(ws, j, 6, "Diskon ", ukuran=HURUF_JUDUL_KOLOM_INV)
            gaya.sel_judul(ws, j + 2, 6, teks_persen, ukuran=HURUF_JUDUL_KOLOM_INV)
        else:
            gaya.sel_judul(ws, j, 6, "Diskon ", ukuran=HURUF_JUDUL_KOLOM_INV)
            ws.merge_cells(start_row=j + 1, start_column=6, end_row=j + 2, end_column=6)
            sel = gaya.sel_judul(ws, j + 1, 6, angka_persen or 0, ukuran=HURUF_JUDUL_KOLOM_INV)
            sel.number_format = "0%"
    else:
        # Bentuk tanpa diskon, seperti 0020826 CV. BASA MANDIRI: kolom
        # Harga melebar menutupi E:G dan kolom Diskon tidak dicetak sama
        # sekali. Mencetak kolom diskon berisi nol hanya membingungkan.
        ws.merge_cells(start_row=j, start_column=5, end_row=j + 2, end_column=7)
        gaya.sel_judul(ws, j, 5, "Harga", ukuran=HURUF_JUDUL_KOLOM_INV)
        for kolom in (6, 7):
            for baris_judul in range(j, j + 3):
                gaya.sel_judul(ws, baris_judul, kolom, None, ukuran=HURUF_JUDUL_KOLOM_INV)
    for baris_judul in range(j, j + 3):
        ws.row_dimensions[baris_judul].height = TINGGI_JUDUL_INV

    # Lebar kolom dipasang di sini, setelah isinya diketahui.
    for kolom, lebar in lebar_menyesuaikan(baris).items():
        ws.column_dimensions[gaya.huruf(kolom)].width = lebar

    r = BARIS_DATA
    for i, b in enumerate(baris, start=1):
        gaya.sel_isi(ws, r, 1, i, rata="center", ukuran=HURUF_ISI_INV)
        gaya.sel_isi(ws, r, 2, b.kode, ukuran=HURUF_ISI_INV, lipat=True)
        # Deskripsi MELIPAT di keenam faktur asli, bukan terpotong.
        gaya.sel_isi(ws, r, 3, b.deskripsi, ukuran=HURUF_ISI_INV, lipat=True)
        gaya.sel_isi(ws, r, 4, b.qty, rata="center", ukuran=HURUF_ISI_INV)
        ws.row_dimensions[r].height = TINGGI_DATA_INV
        if ada_diskon:
            gaya.sel_isi(ws, r, 5, b.harga, angka=gaya.FORMAT_RP, ukuran=HURUF_ISI_INV)
            gaya.sel_isi(ws, r, 6, (b.diskon / b.qty) if b.qty else 0.0,
                         angka=gaya.FORMAT_RP, ukuran=HURUF_ISI_INV)
            gaya.sel_isi(ws, r, 7, b.diskon, angka=gaya.FORMAT_RP,
                         ukuran=HURUF_ISI_INV)
            # Kolom Jumlah berisi nilai SETELAH diskon. Dibuktikan pada
            # faktur asli 0310726 MAE BEBE baris 1: 18 x 62.900 = 1.132.200,
            # diskon 283.050, kolom H = 849.150. Jumlah seluruh kolom H sama
            # dengan baris "Total", bukan "Subtotal".
            gaya.sel_isi(ws, r, 8, b.nett, angka=gaya.FORMAT_RP, ukuran=HURUF_ISI_INV)
        else:
            # Tanpa diskon, Harga menempati sel gabungan E:G dan
            # Jumlah = qty x harga, persis 0020826 CV. BASA MANDIRI.
            ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=7)
            gaya.sel_isi(ws, r, 5, b.harga, angka=gaya.FORMAT_RP, ukuran=HURUF_ISI_INV)
            for kolom in (6, 7):
                gaya.sel_isi(ws, r, kolom, None, ukuran=HURUF_ISI_INV)
            gaya.sel_isi(ws, r, 8, b.kotor, angka=gaya.FORMAT_RP, ukuran=HURUF_ISI_INV)
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
        # TIDAK ada cetak tebal di blok penutup — permintaan Yosua
        # 14 September 2026. Faktur asli menebalkan seluruh blok ini, tapi
        # begitu tiap sel diberi garis, huruf tebalnya jadi terlalu ramai.
        # Garis sudah cukup untuk memisahkan, jadi hurufnya dibiarkan biasa.
        gaya.sel_isi(ws, p + i, 7, label, ukuran=HURUF_ISI_INV)
        # Seluruh kolom nilai memakai format akuntansi Rupiah yang sama.
        # Bagian ketiga format itu (`_-"Rp"* "-"_-`) khusus untuk nol, jadi
        # Uang Muka yang kosong tampil sebagai tanda "-", bukan angka 0.
        gaya.sel_isi(ws, p + i, 8, nilai, angka=gaya.FORMAT_RP,
                     ukuran=HURUF_ISI_INV)

    # ---- rekening di kolom B, sejajar penutup --------------------------
    # Kolom B, dengan kotak tebal selebar B..C. Diperiksa ulang pada empat
    # faktur asli: 0010726 BABY WISE (B75), 0310726 MAE BEBE (B24),
    # 0110826 BABY WISE (B23), 0420826 YULIS (B60:C63 bergaris medium).
    # Hanya 0020826 CV. BASA MANDIRI yang memakai kolom A, dan berkas itu
    # memang memakai template lama.
    rekening = perusahaan.baris_rekening()
    for i, teks in enumerate(rekening):
        gaya.sel_isi(ws, p + 1 + i, 2, teks, tebal=True, ukuran=HURUF_ISI_INV)

    # Blok penutup bergaris PENUH dan SERAGAM TIPIS — tiap sel punya empat
    # sisi tipis, termasuk bingkai luarnya. Permintaan Yosua 14 September
    # 2026: garis luarnya jangan ditebalkan.
    #
    # Ini justru mengembalikannya ke bentuk faktur asli: di
    # 0020826 CV. BASA MANDIRI sel K27..M31 semuanya `thin` di keempat sisi,
    # tanpa bingkai tebal sama sekali. Jangan panggil `gaya.kotak()` di sini.
    gaya.beri_garis(ws, p, 7, p + len(penutup) - 1, 8)

    # Blok rekening TIDAK bergaris penuh — satu kotak saja mengelilingi
    # keempat barisnya, seperti B60:C63 pada 0420826 YULIS BABY SHOP.
    if rekening:
        gaya.kotak(ws, p + 1, 2, p + len(rekening), 3)

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
