"""Tata letak Invoice & Surat Jalan milik CV. MUTIARA TIMUR NUSANTARA.

MTN memakai tata letak SENDIRI, bukan sekadar kop yang berbeda. Pertanyaan
lama di CLAUDE.md bagian 19 ("apakah dokumen MTN memang memakai tata letak
sendiri") akhirnya terjawab: YA. Berkas acuannya
`FA 0010526 BABY FAME (MTN).xlsx`, dikirim Yosua 19 September 2026, dibongkar
sel per sel - bukan ditebak.

Beda pokoknya dengan DPM:

| Bagian          | DPM                          | MTN                              |
|-----------------|------------------------------|----------------------------------|
| Blok kanan kop  | "Jakarta, <tgl>" + Kepada Yth| TIDAK ADA                        |
| Customer        | "Kepada Yth." di kanan       | label CUSTOMER di kiri (A11)     |
| Nomor & tanggal | "FAKTUR No. <nomor>" baris 9 | label FAKTUR / TANGGAL di G11/H11|
| Bentuk nomor    | 0010526                      | FA-01/05/2026  /  SJ-01/05/2026  |
| Baris BRAND     | ada                          | TIDAK ADA                        |
| Judul tabel     | 3 tingkat, baris 12-14       | 2 tingkat, baris 17-18           |
| Penutup invoice | Subtotal..DPP..PPN..Total    | Subtotal, Value Disc, Total SAJA |
| Deskripsi SJ    | C:E digabung                 | kolom C tunggal                  |
| Kolom WARNA SJ  | F                            | D                                |

Penutup TANPA DPP dan PPN itu memang benar dan bukan kelalaian: MTN tidak
mengenakan PPN (`kenakan_ppn: false` di perusahaan.yaml, keputusan Yosua
11 September 2026). Jangan "dilengkapi" dengan baris DPP/PPN.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from openpyxl.worksheet.worksheet import Worksheet

from . import gaya
from . import rumus as rms
from .invoice import susun_baris, _persen_tertulis, _persen_ringkas
from ..model import KeputusanNett, Order

# ---------------------------------------------------------------- INVOICE
# Lebar kolom diambil dari berkas asli (jumlah A..H = 117,84).
# Kolom H dilebarkan 15,71 -> 18,0. Di berkas asli tanggalnya "05 Mei 2026"
# (11 huruf) dan muat; "17 September 2026" (17 huruf) TIDAK muat dan tercetak
# terpotong jadi "17 Septe". Berkas asli pun akan terpotong untuk bulan
# berhuruf panjang - jadi ini bukan meniru, melainkan membetulkan.
LEBAR_INV = {1: 3.43, 2: 17.86, 3: 34.43, 4: 6.14,
             5: 12.86, 6: 13.14, 7: 14.29, 8: 18.0}
KOL_AKHIR_INV = 8

BARIS_KOP_INV = 2       # nama perusahaan di C2
BARIS_LABEL_INV = 11    # CUSTOMER / FAKTUR / TANGGAL
BARIS_NILAI_INV = 12    # nama customer / nomor / tanggal
BARIS_JUDUL_INV = 17    # judul tabel, dua tingkat (17-18)
BARIS_DATA_INV = 19

TINGGI_JUDUL_INV = 15.75
TINGGI_DATA_INV = 24.95

HURUF_NAMA = 18         # nama perusahaan
HURUF_KOP = 11          # alamat, telepon, email - semuanya TEBAL di berkas asli
HURUF_LABEL = 11        # kata CUSTOMER / FAKTUR / TANGGAL
HURUF_CUSTOMER = 12
HURUF_JUDUL_KOLOM = 12
HURUF_ISI = 12

# ------------------------------------------------------------ SURAT JALAN
KOL_NO_SJ = 1
KOL_KODE_SJ = 2
KOL_DESK_SJ = 3         # kolom C TUNGGAL, tidak digabung seperti DPM
KOL_WARNA_SJ = 4
KOL_UKURAN_MULAI_SJ = 5  # E dan seterusnya

LEBAR_SJ_TETAP = {1: 5.71, 2: 17.57, 3: 34.43, 4: 12.71}
LEBAR_UKURAN_SJ = 9.0
LEBAR_UKURAN_SJ_SEMPIT = 5.6
LEBAR_QTY_SJ = 8.0
JATAH_A4_SJ = 115.0     # sama dengan DPM, lihat CLAUDE.md bagian 19

BARIS_LABEL_SJ = 11
BARIS_NILAI_SJ = 12
BARIS_KALIMAT_SJ = 17
BARIS_JUDUL_SJ = 19     # dua tingkat (19-20), tiap kolom digabung ke bawah
BARIS_DATA_SJ = 21

TINGGI_JUDUL_SJ = 14.45
TINGGI_DATA_SJ = 20.1

KALIMAT_SJ = "Diterima dengan baik barang-barang tersebut dibawah ini :"


def nomor_mtn(awalan: str, nomor: str, tanggal: Optional[date]) -> str:
    """Bentuk nomor khas MTN: `FA-01/05/2026`, bukan `0010526`.

    Kalau nomornya masih kosong (bawaan program tidak pernah menebak nomor
    urut - lihat CLAUDE.md bagian 9), yang dikembalikan tetap penanda kosong
    supaya jelas harus diisi tangan.
    """
    urut = (nomor or "").strip()
    if not urut or set(urut) <= {"_"}:
        return f"{awalan}-__/__/____"
    if tanggal:
        return f"{awalan}-{urut}/{tanggal.month:02d}/{tanggal.year}"
    return f"{awalan}-{urut}"


def _kop(ws: Worksheet, perusahaan, baris_mulai: int,
         lebar_a: float = None, lebar_b: float = None) -> None:
    """Kop MTN: logo di kiri, teks di kolom C. TIDAK ada blok kanan.

    Lebar kolom A dan B diminta dari pemanggil, sebab Invoice dan Surat Jalan
    MTN memakai lebar yang berbeda. Kalau dihitung dari LEBAR_INV untuk
    dua-duanya, logo Surat Jalan meleset dari tengah tanpa ada yang sadar.
    """
    r = baris_mulai
    a = LEBAR_INV[1] if lebar_a is None else lebar_a
    b = LEBAR_INV[2] if lebar_b is None else lebar_b
    ws.merge_cells(start_row=r, start_column=1, end_row=r + 6, end_column=2)
    gaya.pasang_logo(
        ws, perusahaan, r,
        gaya.lebar_kolom_px(a) + gaya.lebar_kolom_px(b),
    )
    gaya.sel_isi(ws, r, 3, perusahaan.nama_resmi or perusahaan.nama,
                 ukuran=HURUF_NAMA, tebal=True)
    # Alamat, telepon, dan email semuanya TEBAL di berkas asli MTN - beda
    # dengan DPM yang alamatnya biasa.
    for i, teks in enumerate(perusahaan.alamat_baris, start=2):
        gaya.sel_isi(ws, r + i, 3, teks, ukuran=HURUF_KOP, tebal=True)


# Blok customer MTN selalu LIMA baris: label, nama, dan tiga baris alamat -
# persis A11:C15 pada berkas asli. Tingginya dibuat tetap supaya kotaknya
# tidak ikut mengerut waktu alamatnya belum diisi.
BARIS_BLOK_CUSTOMER = 5


def _blok_customer(ws: Worksheet, cust, nama_tampil: str, baris_label: int,
                   kolom_kanan: list[tuple[int, int, str, str]],
                   kotak_gabung: bool = False) -> None:
    """Label CUSTOMER di kiri, label lain (FAKTUR/TANGGAL, dst) di kanan.

    `kolom_kanan` berisi (kolom_awal, kolom_akhir, label, nilai). Rentangnya
    digabung, persis seperti berkas asli MTN yang memakai F11:H11 untuk
    "SURAT JALAN" dan I11:K11 untuk "TANGGAL". Tanpa penggabungan itu tanggal
    panjang seperti "17 September 2026" tercetak terpotong.

    GARIS DAN RATA TENGAH. Berkas asli MTN mengotaki blok customer (A11:C15)
    dan tiap label di kanan, serta menengahkan tulisan labelnya. Versi pertama
    melewatkan keduanya sehingga kepala dokumen MTN tampil polos, dan Yosua
    menambahkannya sendiri di Excel (20 September 2026). Sekarang dipasang
    program.

    `kotak_gabung` membedakan keduanya, mengikuti berkas aslinya: di tab
    faktur label dan nilainya berkotak SENDIRI-SENDIRI (G11 dan G12 masing-
    masing bergaris empat sisi), sedangkan di tab SURAT JALAN keduanya berbagi
    SATU kotak (F11:H12, tanpa garis pemisah di tengahnya).
    """
    # Label CUSTOMER digabung A:C. Tanpa penggabungan ini tulisannya
    # ditengahkan di kolom A yang cuma 3,43 satuan, lalu terpotong garis
    # kotaknya - tercetak "STOMER". Ketahuan dari gambar hasil render.
    ws.merge_cells(start_row=baris_label, start_column=1,
                   end_row=baris_label, end_column=3)
    gaya.sel_isi(ws, baris_label, 1, "CUSTOMER", ukuran=HURUF_LABEL, rata="center")
    for awal, akhir, label, nilai in kolom_kanan:
        for r, teks, tebal in ((baris_label, label, False),
                               (baris_label + 1, nilai, True)):
            if akhir > awal:
                ws.merge_cells(start_row=r, start_column=awal,
                               end_row=r, end_column=akhir)
            gaya.sel_isi(ws, r, awal, teks, ukuran=HURUF_LABEL, tebal=tebal,
                         rata="center")
        if kotak_gabung:
            # TIPIS, bukan medium - satu-satunya garis tebal di dokumen MTN
            # adalah kotak blok rekening.
            gaya.kotak(ws, baris_label, awal, baris_label + 1, akhir,
                       tebal="thin")
        else:
            gaya.beri_garis(ws, baris_label, awal, baris_label + 1, akhir)

    r = baris_label + 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    gaya.sel_isi(ws, r, 1, nama_tampil, ukuran=HURUF_CUSTOMER, tebal=True)

    # Alamat yang belum diketahui DIBIARKAN KOSONG untuk diisi Yosua sendiri.
    # Barisnya tetap dibuat supaya tinggi kotaknya tidak berubah.
    alamat = gaya.pecah_alamat((cust.alamat if cust else ""), 3)
    for i in range(1, BARIS_BLOK_CUSTOMER - 1):
        ws.merge_cells(start_row=r + i, start_column=1, end_row=r + i, end_column=3)
        teks = alamat[i - 1] if i - 1 < len(alamat) else None
        gaya.sel_isi(ws, r + i, 1, teks, ukuran=HURUF_CUSTOMER)

    # Kotak blok customer: SATU kotak luar, ditambah garis di bawah label
    # CUSTOMER saja. TIDAK ada garis antar baris alamat.
    #
    # Revisi Yosua 20 September 2026, dibaca dari berkas suntingannya sendiri
    # (A12..A15 cuma bergaris kiri, C12..C15 cuma bergaris kanan). Berkas asli
    # MTN memang memberi garis atas-bawah di tiap baris, tapi Yosua memilih
    # bentuk yang lebih bersih ini - nama dan alamat customer terbaca sebagai
    # satu blok, bukan empat kotak terpisah. Jangan dikembalikan ke kisi-kisi
    # hanya karena berkas aslinya begitu.
    akhir_blok = baris_label + BARIS_BLOK_CUSTOMER - 1
    gaya.beri_garis(ws, baris_label, 1, baris_label, 3)      # kotak label
    gaya.kotak(ws, baris_label, 1, akhir_blok, 3, tebal="thin")


def buat_invoice_mtn(ws: Worksheet, order: Order, keputusan: KeputusanNett,
                     cust, perusahaan, pengaturan,
                     nomor: str = "________",
                     tanggal_dokumen: Optional[date] = None,
                     pakai_rumus: bool = False) -> dict:
    """Invoice dengan tata letak CV. MUTIARA TIMUR NUSANTARA."""
    tanggal = tanggal_dokumen or order.tanggal_po or date.today()
    ws.title = "Invoice"

    gaya.atur_lebar(ws, LEBAR_INV)
    _kop(ws, perusahaan, BARIS_KOP_INV)

    nama_tampil = (cust.nama_di_dokumen if cust else "") or order.customer_kunci
    _blok_customer(
        ws, cust, nama_tampil, BARIS_LABEL_INV,
        [(7, 7, "FAKTUR", nomor_mtn("FA", nomor, tanggal)),
         (8, 8, "TANGGAL", gaya.tanggal_indonesia(tanggal))],
    )

    per_ukuran = bool(cust and cust.pecah_per_ukuran)
    baris = susun_baris(
        order, keputusan,
        pecah_per_ukuran=per_ukuran,
        akhiran_y=pengaturan.akhiran_y_untuk_angka,
    )
    teks_persen, angka_persen = _persen_tertulis(order, keputusan, pengaturan)
    # Untuk diskon tunggal (TOP) _persen_tertulis mengembalikan None pada
    # teksnya dan angkanya terpisah - kalau dipakai apa adanya, kolom Diskon
    # tercetak KOSONG. Sama seperti proforma (CLAUDE.md bagian 28).
    tulisan_diskon = teks_persen or _persen_ringkas(angka_persen or 0.0)

    # ---- judul tabel: DUA tingkat (17-18), bukan tiga seperti DPM --------
    j = BARIS_JUDUL_INV
    for kolom, teks in ((1, "No."), (2, "ARTICLE CODE"),
                        (3, "DESKRIPSI BARANG"), (8, "Jumlah")):
        ws.merge_cells(start_row=j, start_column=kolom,
                       end_row=j + 1, end_column=kolom)
        gaya.sel_judul(ws, j, kolom, teks, ukuran=HURUF_JUDUL_KOLOM)
    for kolom, atas, bawah in ((4, "Qty", "PCS"), (5, "Harga", "Satuan"),
                               (6, "Diskon", tulisan_diskon),
                               (7, "Nilai", "Diskon")):
        gaya.sel_judul(ws, j, kolom, atas, ukuran=HURUF_JUDUL_KOLOM)
        gaya.sel_judul(ws, j + 1, kolom, bawah, ukuran=HURUF_JUDUL_KOLOM)
    for r in (j, j + 1):
        ws.row_dimensions[r].height = TINGGI_JUDUL_INV
    gaya.beri_garis(ws, j, 1, j + 1, KOL_AKHIR_INV)

    # ---- isi tabel -------------------------------------------------------
    r = BARIS_DATA_INV
    for i, b in enumerate(baris, start=1):
        gaya.sel_isi(ws, r, 1, i, rata="center", ukuran=HURUF_ISI)
        gaya.sel_isi(ws, r, 2, b.kode, ukuran=HURUF_ISI)
        gaya.sel_isi(ws, r, 3,
                     rms.nama_barang(r) if (pakai_rumus and not per_ukuran)
                     else b.deskripsi,
                     ukuran=HURUF_ISI, lipat=True)
        gaya.sel_isi(ws, r, 4, b.qty, rata="center", ukuran=HURUF_ISI, angka="#,##0")
        gaya.sel_isi(ws, r, 5, rms.harga(r) if pakai_rumus else b.harga,
                     ukuran=HURUF_ISI, angka=gaya.FORMAT_RP)
        gaya.sel_isi(ws, r, 6, b.diskon / b.qty if b.qty else 0,
                     ukuran=HURUF_ISI, angka=gaya.FORMAT_RP)
        gaya.sel_isi(ws, r, 7, b.diskon, ukuran=HURUF_ISI, angka=gaya.FORMAT_RP)
        gaya.sel_isi(ws, r, 8,
                     rms.jumlah_baris(r, "D", "E", "G") if pakai_rumus
                     else b.nett,
                     ukuran=HURUF_ISI, angka=gaya.FORMAT_RP)
        ws.row_dimensions[r].height = TINGGI_DATA_INV
        r += 1
    gaya.beri_garis(ws, BARIS_DATA_INV, 1, r - 1, KOL_AKHIR_INV)

    # ---- penutup: HANYA Subtotal, Value Disc, Total ----------------------
    kotor = sum(b.qty * b.harga for b in baris)
    diskon = sum(b.diskon for b in baris)
    nett = kotor - diskon
    p = r + 1
    label_diskon = f"Value Disc {tulisan_diskon}"
    isi = [("Subtotal", kotor), (label_diskon, diskon), ("Total", nett)]
    if pakai_rumus:
        # MTN tidak mengenakan PPN, jadi penutupnya berhenti di Total -
        # tidak ada DPP dan PPN yang perlu diturunkan.
        isi = [(isi[0][0], rms.subtotal(BARIS_DATA_INV, r - 1, "D", "E")),
               (isi[1][0], rms.jumlahkan(BARIS_DATA_INV, r - 1, "G")),
               (isi[2][0], rms.selisih("H", p, p + 1))]
    for i, (label, nilai) in enumerate(isi):
        gaya.sel_isi(ws, p + i, 7, label, ukuran=HURUF_ISI)
        gaya.sel_isi(ws, p + i, 8, nilai, ukuran=HURUF_ISI, angka=gaya.FORMAT_RP)
    gaya.beri_garis(ws, p, 7, p + 2, 8)

    # ---- rekening di kolom A, MULAI SATU BARIS DI BAWAH Subtotal ---------
    # Revisi Yosua 20 September 2026: blok rekening sejajar mulai dari baris
    # "Value Disc", bukan dari "Subtotal", dan dikelilingi kotak medium -
    # sama seperti faktur DPM. Versi sebelumnya menempelkannya sejajar
    # Subtotal dan tanpa kotak sama sekali.
    rekening = perusahaan.baris_rekening()
    for i, teks in enumerate(rekening):
        gaya.sel_isi(ws, p + 1 + i, 1, teks, ukuran=HURUF_ISI, tebal=True)
    if rekening:
        gaya.kotak(ws, p + 1, 1, p + len(rekening), 3)

    akhir = p + max(3, len(rekening))
    ws.merge_cells(start_row=akhir, start_column=7, end_row=akhir, end_column=8)
    gaya.sel_isi(ws, akhir, 7, "Hormat kami,", ukuran=HURUF_ISI, rata="center")

    gaya.siapkan_cetak(ws, KOL_AKHIR_INV)
    ws.print_area = f"A2:H{akhir}"
    return {"qty": sum(b.qty for b in baris), "kotor": kotor,
            "diskon": diskon, "nett": nett, "baris": len(baris)}


# ------------------------------------------------------------ SURAT JALAN
def _lebar_ukuran_sj(jumlah_ukuran: int) -> float:
    """Kolom ukuran menyusut kalau ukurannya banyak, supaya tetap muat A4.

    Aturan yang sama dengan Surat Jalan DPM (CLAUDE.md bagian 23). Berkas
    asli MTN memakai kolom ukuran selebar 13 satuan, tapi di situ ukurannya
    hanya enam; dipaksakan untuk sembilan ukuran, jumlahnya jauh melewati
    jatah A4 dan hurufnya mengecil drastis.
    """
    if jumlah_ukuran <= 0:
        return LEBAR_UKURAN_SJ
    tetap = sum(LEBAR_SJ_TETAP.values()) + LEBAR_QTY_SJ
    muat = (JATAH_A4_SJ - tetap) / jumlah_ukuran
    return max(LEBAR_UKURAN_SJ_SEMPIT, min(LEBAR_UKURAN_SJ, muat))


def buat_surat_jalan_mtn(ws: Worksheet, order: Order, cust, perusahaan,
                         nomor: str = "________",
                         tanggal_dokumen: Optional[date] = None,
                         pakai_rumus: bool = False) -> dict:
    """Surat Jalan dengan tata letak CV. MUTIARA TIMUR NUSANTARA.

    Susunan kolomnya BEDA dari DPM: deskripsi barang di kolom C tunggal
    (bukan C:E digabung), WARNA di kolom D (bukan F), kolom ukuran mulai E.
    """
    from .surat_jalan import _posisi_terpakai, _label_terpakai

    tanggal = tanggal_dokumen or order.tanggal_po or date.today()
    ws.title = "Surat Jalan"

    maks_ukuran = max((len(_posisi_terpakai(b)) for b in order.blok), default=0)
    lebar_uk = _lebar_ukuran_sj(maks_ukuran)
    kol_qty = KOL_UKURAN_MULAI_SJ + maks_ukuran
    lebar = dict(LEBAR_SJ_TETAP)
    for k in range(KOL_UKURAN_MULAI_SJ, kol_qty):
        lebar[k] = lebar_uk
    lebar[kol_qty] = LEBAR_QTY_SJ
    gaya.atur_lebar(ws, lebar)

    _kop(ws, perusahaan, 1, LEBAR_SJ_TETAP[1], LEBAR_SJ_TETAP[2])

    nama_tampil = (cust.nama_di_dokumen if cust else "") or order.customer_kunci
    # Tanggal butuh ruang: kolom Qty cuma 8 satuan, jauh kurang untuk
    # "17 September 2026". Berkas asli pun menggabung I11:K11 untuk ini.
    lebar_tanggal = 3
    awal_tanggal = max(KOL_UKURAN_MULAI_SJ + 1, kol_qty - lebar_tanggal + 1)
    awal_nomor = max(KOL_UKURAN_MULAI_SJ, awal_tanggal - 3)
    _blok_customer(
        ws, cust, nama_tampil, BARIS_LABEL_SJ,
        [(awal_nomor, awal_tanggal - 1, "SURAT JALAN",
          nomor_mtn("SJ", nomor, tanggal)),
         (awal_tanggal, kol_qty, "TANGGAL", gaya.tanggal_indonesia(tanggal))],
        kotak_gabung=True,
    )

    gaya.sel_isi(ws, BARIS_KALIMAT_SJ, 1, KALIMAT_SJ, ukuran=HURUF_CUSTOMER)

    r = BARIS_JUDUL_SJ
    total_qty = 0
    for blok in order.blok:
        posisi = _posisi_terpakai(blok)
        if not posisi:
            continue
        label = _label_terpakai(blok)

        # judul tabel dua tingkat; TIAP kolom digabung ke bawah, sama seperti
        # DPM sejak CLAUDE.md bagian 24.
        tetap = [(KOL_NO_SJ, "No."), (KOL_KODE_SJ, "ARTICLE CODE"),
                 (KOL_DESK_SJ, "DESKRIPSI BARANG"), (KOL_WARNA_SJ, "WARNA")]
        for kolom, teks in tetap:
            ws.merge_cells(start_row=r, start_column=kolom,
                           end_row=r + 1, end_column=kolom)
            gaya.sel_judul(ws, r, kolom, teks, ukuran=HURUF_JUDUL_KOLOM)
        for i, teks in enumerate(label):
            kolom = KOL_UKURAN_MULAI_SJ + i
            ws.merge_cells(start_row=r, start_column=kolom,
                           end_row=r + 1, end_column=kolom)
            gaya.sel_judul(ws, r, kolom, teks, ukuran=HURUF_JUDUL_KOLOM)
        gaya.sel_judul(ws, r, kol_qty, "Qty", ukuran=HURUF_JUDUL_KOLOM)
        gaya.sel_judul(ws, r + 1, kol_qty, "PCS", ukuran=HURUF_JUDUL_KOLOM)
        for baris_judul in (r, r + 1):
            ws.row_dimensions[baris_judul].height = TINGGI_JUDUL_SJ
        gaya.beri_garis(ws, r, 1, r + 1, kol_qty)

        r += 2
        awal = r
        for i, b in enumerate(blok.baris, start=1):
            if not any(b.qty_per_ukuran):
                continue
            gaya.sel_isi(ws, r, KOL_NO_SJ, i, rata="center", ukuran=HURUF_ISI)
            gaya.sel_isi(ws, r, KOL_KODE_SJ, b.kode, ukuran=HURUF_ISI)
            gaya.sel_isi(ws, r, KOL_DESK_SJ, b.nama, ukuran=HURUF_ISI, lipat=True)
            gaya.sel_isi(ws, r, KOL_WARNA_SJ, b.warna, ukuran=HURUF_ISI, lipat=True)
            for k, p in enumerate(posisi):
                q = b.qty_per_ukuran[p]
                gaya.sel_isi(ws, r, KOL_UKURAN_MULAI_SJ + k, q or None,
                             rata="center", ukuran=HURUF_ISI)
            qty = sum(b.qty_per_ukuran[p] for p in posisi)
            total_qty += qty
            # Berkas asli MTN menulis kolom Qty sebagai `=SUM(E21:J21)`.
            gaya.sel_isi(ws, r, kol_qty,
                         rms.qty_surat_jalan(r, gaya.huruf(KOL_UKURAN_MULAI_SJ),
                                             gaya.huruf(kol_qty - 1))
                         if (pakai_rumus and kol_qty > KOL_UKURAN_MULAI_SJ)
                         else qty,
                         rata="center", ukuran=HURUF_ISI)
            ws.row_dimensions[r].height = TINGGI_DATA_SJ
            r += 1
        gaya.beri_garis(ws, awal, 1, r - 1, kol_qty)
        r += 1

    gaya.blok_tanda_tangan(
        ws, r + 1,
        [KOL_KODE_SJ, KOL_DESK_SJ, max(KOL_WARNA_SJ + 1, KOL_UKURAN_MULAI_SJ + 1)],
        ["Penerima :", "Pengirim :", "Mengetahui :"],
    )

    gaya.siapkan_cetak(ws, kol_qty)
    ws.print_area = f"A1:{gaya.huruf(kol_qty)}{r + 3}"
    return {"qty": total_qty, "kolom_terakhir": kol_qty}
