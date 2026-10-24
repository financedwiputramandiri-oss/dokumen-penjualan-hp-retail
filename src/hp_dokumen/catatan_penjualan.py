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
