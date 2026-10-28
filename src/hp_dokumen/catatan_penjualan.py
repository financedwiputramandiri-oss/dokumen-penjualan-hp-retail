"""Baris untuk LAPORAN PENJUALAN: tab DATA_INVOICE dan DATA_ARTIKEL.

Permintaan Yosua 24 Oktober 2026: setiap Invoice dan Surat Jalan yang dibuat,
datanya harus ikut masuk ke spreadsheet
`LAPORAN_PENJUALAN_DPM_JAN-OKT_2026_DENGAN_TAGIHAN`.

Dua tab tujuan sudah disiapkan Yosua dan masih kosong, hanya berisi judul
kolom — judul itulah yang dijadikan acuan di modul ini, bukan tebakan:

    DATA_INVOICE : Tanggal | No Invoice | Customer | DPP | PPN | Total
                   | Tanggal Bayar | Jatuh Tempo | Dicatat
    DATA_ARTIKEL : Tanggal | No Invoice | Customer | Artikel | Nama Barang
                   | Qty | Harga | Jumlah

Modul ini SENGAJA tidak menyentuh Google sama sekali. Ia hanya menyusun
barisnya, supaya bisa diuji tanpa kredensial dan dipakai bersama oleh
perintah manual maupun bot — pola yang sama dengan `berkas_dokumen.py`
(CLAUDE.md bagian 15).

Tiga keputusan yang jangan diubah tanpa alasan:

1. Kolom `Jumlah` di DATA_ARTIKEL berisi nilai BERSIH per baris, bukan
   `qty x harga`. Dengan begitu jumlah seluruh kolom Jumlah sama persis
   dengan kolom Total di DATA_INVOICE, jadi kedua tab bisa saling
   dicocokkan. Kalau diisi nilai kotor, keduanya selalu beda sebesar
   diskon dan tidak ada yang tahu mana yang benar.

2. `No Invoice` DIKOSONGKAN — keputusan Yosua 24 Oktober 2026: *"untuk
   pola nomor invoice biarkan kosong tapi urutannya sesuai dengan waktu
   invoice dibuat"*. Baris baru selalu ditambahkan di BAWAH, jadi urutan
   barisnya sama dengan urutan pembuatannya. Nomor boleh diisi lewat
   `--nomor` kalau suatu saat polanya sudah ditetapkan.

   Karena nomornya kosong, kunci pengenal satu invoice adalah
   **Customer + Tanggal** (KUNCI, di bawah). Dua kolom itu sudah ada di
   sheet, jadi tidak perlu kolom tambahan.

3. MTN tidak kena PPN, jadi DPP = Total dan PPN = 0 — bukan dihitung
   mundur dari 111%. Mengisi PPN untuk MTN berarti melaporkan pajak yang
   tidak pernah ditagih.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

JUDUL_INVOICE = ["Tanggal", "No Invoice", "Customer", "DPP", "PPN", "Total",
                 "Tanggal Bayar", "Jatuh Tempo", "Dicatat"]
JUDUL_ARTIKEL = ["Tanggal", "No Invoice", "Customer", "Artikel", "Nama Barang",
                 "Qty", "Harga", "Jumlah"]

TAB_INVOICE = "DATA_INVOICE"
TAB_ARTIKEL = "DATA_ARTIKEL"

FORMAT_TANGGAL = "%d/%m/%Y"


def kunci(customer: str, tanggal_teks: str) -> tuple[str, str]:
    """Pengenal satu invoice di laporan penjualan.

    Nomor invoice sengaja dikosongkan (keputusan Yosua 24 Oktober 2026),
    jadi yang dipakai mengenali baris adalah Customer + Tanggal. Keduanya
    sudah menjadi kolom di sheet, jadi tidak ada kolom bantu yang perlu
    ditambahkan ke berkas Yosua.

    Dibandingkan setelah diseragamkan huruf besar-kecil dan spasi tepinya,
    sebab nama customer di sheet pernah diketik tangan.
    """
    return ((customer or "").strip().upper(), (tanggal_teks or "").strip())


@dataclass
class Catatan:
    """Satu invoice beserta rincian artikelnya, siap ditulis ke sheet."""

    nomor: str
    customer: str
    tanggal: date
    dpp: float
    ppn: float
    total: float
    jatuh_tempo: date | None
    artikel: list[list] = field(default_factory=list)

    @property
    def kunci(self) -> tuple[str, str]:
        return kunci(self.customer, self.tanggal.strftime(FORMAT_TANGGAL))

    def baris_invoice(self, dicatat: datetime | None = None) -> list:
        d = dicatat or datetime.now()
        return [
            self.tanggal.strftime(FORMAT_TANGGAL),
            self.nomor,
            self.customer,
            round(self.dpp, 2),
            round(self.ppn, 2),
            round(self.total, 2),
            "",                                   # Tanggal Bayar — diisi saat dibayar
            self.jatuh_tempo.strftime(FORMAT_TANGGAL) if self.jatuh_tempo else "",
            d.strftime("%d/%m/%Y %H:%M"),
        ]

    def baris_artikel(self) -> list[list]:
        return list(self.artikel)


def susun(order, keputusan, baris_invoice, hasil: dict, *,
          nomor: str = "", nama_customer: str = "",
          tanggal: date | None = None) -> Catatan:
    """Susun catatan dari satu invoice yang baru dibuat.

    `baris_invoice` adalah keluaran `invoice.susun_baris()`, dan `hasil`
    adalah dict yang dikembalikan `invoice.buat_invoice()` — keduanya
    dipakai apa adanya supaya angka di laporan penjualan TIDAK PERNAH
    dihitung ulang dengan cara yang berbeda dari fakturnya.
    """
    # Nomor penampung dari pembuat dokumen ("________") dianggap kosong —
    # kalau ikut tertulis, kolom No Invoice penuh garis bawah yang tidak
    # berarti apa-apa.
    nomor = (nomor or "").strip()
    if set(nomor) <= {"_", "-", " "}:
        nomor = ""

    tgl = tanggal or date.today()
    cust = (nama_customer or "").strip() or order.customer_kunci
    tgl_teks = tgl.strftime(FORMAT_TANGGAL)

    artikel = [
        [tgl_teks, nomor, cust, b.kode, b.deskripsi,
         b.qty, round(b.harga, 2), round(b.nett, 2)]
        for b in baris_invoice
    ]

    jatuh = hasil.get("jatuh_tempo")
    if jatuh is None and hasil.get("termin_hari"):
        jatuh = tgl + timedelta(days=int(hasil["termin_hari"]))

    return Catatan(
        nomor=nomor,
        customer=cust,
        tanggal=tgl,
        dpp=float(hasil.get("dpp") or 0.0),
        ppn=float(hasil.get("ppn") or 0.0),
        total=float(hasil.get("nett") or 0.0),
        jatuh_tempo=jatuh,
        artikel=artikel,
    )


def periksa(catatan: Catatan, toleransi: float = 1.0) -> list[str]:
    """Pemeriksaan yang harus lolos sebelum barisnya boleh dikirim.

    Murah, tapi menangkap kelas kesalahan yang paling mahal: angka di
    laporan penjualan yang tidak sama dengan fakturnya sendiri.
    """
    pesan = []
    jml = sum(a[7] for a in catatan.artikel)
    if abs(jml - catatan.total) > toleransi:
        pesan.append(
            f"Jumlah kolom 'Jumlah' di DATA_ARTIKEL (Rp{jml:,.2f}) tidak sama "
            f"dengan Total di DATA_INVOICE (Rp{catatan.total:,.2f}), "
            f"selisih Rp{jml - catatan.total:,.2f}."
        )
    if abs((catatan.dpp + catatan.ppn) - catatan.total) > toleransi:
        pesan.append(
            f"DPP + PPN (Rp{catatan.dpp + catatan.ppn:,.2f}) tidak sama dengan "
            f"Total (Rp{catatan.total:,.2f})."
        )
    if catatan.total <= 0:
        pesan.append("Total nol atau negatif.")
    if not catatan.customer:
        pesan.append("Nama customer kosong.")
    return pesan


# ---------------------------------------------------------------- LAP / BUKU
#
# Permintaan Yosua 28 Oktober 2026: invoice yang terbit juga masuk ke tab
# laporan bulanan LAP <BLN> dan BUKU <BLN>, mengikuti format yang SUDAH ADA
# di berkasnya. Susunan kolom di bawah dibaca langsung dari `LAP OKT` dan
# `BUKU OKT` milik Yosua, bukan dirancang sendiri.

BULAN_SINGKAT = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MEI", 6: "JUN",
                 7: "JUL", 8: "AGU", 9: "SEP", 10: "OKT", 11: "NOV", 12: "DES"}

# LAP <BLN> — judul 3 baris, judul kolom di baris 5-6, data mulai baris 7,
# ditutup satu baris "Total Penjualan <Bulan>".
JUDUL_LAP = ["No", "Tanggal", "Nomor Invoice", "Nomor Faktur Pajak", "NPWP",
             "Nama Customer", "DPP", "PPN", "Total", "", "Tanggal Bayar",
             "", "Keterangan"]

# BUKU <BLN> — judul 3 baris, judul kolom di baris 4-5, data mulai baris 6.
# Satu invoice = baris artikel pertama yang membawa TGL/NO/CUSTOMER dan
# seluruh angka ringkasannya, lalu baris artikel berikutnya yang hanya
# mengisi kolom E-I, lalu satu baris "Total <nomor>", lalu satu baris kosong.
JUDUL_BUKU = ["TGL", "NO", "NO FAKTUR", "CUSTOMER", "NAMA BARANG", "ARTIKEL",
              "QTY", "HARGA", "JUMLAH", "DPP", "PPN", "JUMLAH", "DISKON",
              "POTONGAN DISKON", "KETERANGAN"]


def tab_lap(tanggal: date) -> str:
    return f"LAP {BULAN_SINGKAT[tanggal.month]}"


def tab_buku(tanggal: date) -> str:
    return f"BUKU {BULAN_SINGKAT[tanggal.month]}"


def nomor_berikut(nomor_terpakai, tanggal: date) -> str:
    """Nomor invoice berikutnya, MELANJUTKAN yang sudah ada di tab LAP.

    Polanya dibaca dari berkas Yosua sendiri: `0011026` = urut 001, bulan
    10, tahun 26. Urutannya diulang tiap bulan dan DIPAKAI BERSAMA oleh DPM
    dan MTN — dua hal yang dulu tercatat belum pasti di CLAUDE.md bagian 26,
    dan terjawab oleh isi `LAP OKT` (nomor 0201026 milik CV. MTN).

    Nomornya MELANJUTKAN yang terbesar, bukan mengisi lubang di tengah.
    Lubang biasanya berarti nomor itu memang dipakai di luar sistem ini;
    mengisinya ulang akan membuat dua dokumen bernomor sama.
    """
    ekor = f"{tanggal.month:02d}{tanggal.year % 100:02d}"
    tertinggi = 0
    for n in nomor_terpakai:
        t = str(n or "").strip().lstrip("'")
        # Buang akhiran huruf seperti ".A" pada faktur Haritsa yang dipecah.
        pokok = t.split(".")[0]
        if not pokok.isdigit() or not pokok.endswith(ekor):
            continue
        urut = pokok[:-4]
        if urut.isdigit():
            tertinggi = max(tertinggi, int(urut))
    return f"{tertinggi + 1:03d}{ekor}"


def baris_lap(catatan: "Catatan", no_urut: int, *, keterangan: str = "") -> list:
    """Satu baris untuk tab LAP <BLN>.

    Nomor Faktur Pajak dan NPWP DIKOSONGKAN — keduanya tidak ada di order
    sheet dan tidak boleh ditebak (CLAUDE.md bagian 33 dan 45).
    """
    return [
        no_urut,
        catatan.tanggal.strftime(FORMAT_TANGGAL),
        catatan.nomor,
        "",                      # Nomor Faktur Pajak - diisi manual
        "",                      # NPWP - diisi manual
        catatan.customer,
        round(catatan.dpp, 2),
        round(catatan.ppn, 2),
        round(catatan.total, 2),
        "",
        "",                      # Tanggal Bayar - diisi saat dibayar
        "",
        keterangan,
    ]


def baris_buku(catatan: "Catatan", *, diskon_teks: str = "",
               potongan: float = 0.0, keterangan: str = "") -> list[list]:
    """Baris-baris untuk tab BUKU <BLN>, satu kelompok per invoice.

    Kolom HARGA di BUKU berisi harga SETELAH diskon, dan JUMLAH berisi
    `qty x harga setelah diskon` — dibuktikan dari invoice 0081026 Haritsa
    di berkas Yosua: 18 x 34.500 = 621.000, dan jumlah seluruh kolom itu
    sama dengan Total invoice. Karena itu harga satuannya diturunkan dari
    nilai bersih per baris, BUKAN dari harga retail.
    """
    tgl = catatan.tanggal.strftime(FORMAT_TANGGAL)
    out: list[list] = []
    for i, a in enumerate(catatan.artikel):
        kode, nama, qty, _harga, nett = a[3], a[4], a[5], a[6], a[7]
        satuan = round(nett / qty, 2) if qty else 0.0
        if i == 0:
            out.append([tgl, catatan.nomor, catatan.nomor, catatan.customer,
                        nama, kode, qty, satuan, round(nett, 2),
                        round(catatan.dpp, 2), round(catatan.ppn, 2),
                        round(catatan.total, 2), diskon_teks,
                        round(potongan, 2) if potongan else "", keterangan])
        else:
            out.append(["", "", "", "", nama, kode, qty, satuan, round(nett, 2)])
    qty_total = sum(a[5] for a in catatan.artikel)
    out.append(["", "", "", "", f"Total {catatan.nomor}".strip(), "",
                qty_total, "", round(catatan.total, 2)])
    out.append([])               # satu baris kosong antar invoice
    return out
