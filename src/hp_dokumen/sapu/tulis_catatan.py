"""Menambahkan baris invoice ke spreadsheet LAPORAN PENJUALAN.

Berbeda dari `tulis_sheet.py` yang hanya boleh menyentuh tab berawalan
`BOT_`, modul ini menulis ke tab milik Yosua sendiri — DATA_INVOICE dan
DATA_ARTIKEL. Karena itu pagarnya dibuat lebih ketat, bukan lebih longgar:

1. HANYA dua tab itu yang boleh ditulis. Nama lain ditolak dengan galat,
   dan penolakan itu diuji. Tab laporan bulanan Yosua (LAP, BUKU, ARTIKEL,
   TAGIHAN) tidak boleh tersentuh sama sekali — isinya hasil kerja
   berbulan-bulan dan tidak ada salinannya.

2. HANYA MENAMBAH di bawah. Tidak pernah `clear`, tidak pernah menimpa
   baris yang sudah ada, tidak pernah membuat tab baru. Kalau tabnya
   belum ada, itu galat — bukan alasan untuk membuatnya sendiri.

3. Baris dengan No Invoice yang SUDAH ADA dilewati. Tanpa ini, sapuan
   kedua menggandakan seluruh laporan penjualan dan tidak ada yang
   menyadarinya sampai angka bulanannya dipakai.

Pemeriksaan nomor dilakukan dengan MEMBACA kolom B lebih dulu. Mahal satu
panggilan, tapi jauh lebih murah daripada laporan penjualan ganda.
"""
from __future__ import annotations

from ..catatan_penjualan import TAB_ARTIKEL, TAB_INVOICE, Catatan

TAB_DIIZINKAN = (TAB_INVOICE, TAB_ARTIKEL)


class PenulisCatatan:
    """Menambah baris ke DATA_INVOICE dan DATA_ARTIKEL."""

    def __init__(self, sambungan, id_sheet: str):
        self.s = sambungan
        self.id = id_sheet

    # ------------------------------------------------------------ pagar
    @staticmethod
    def _periksa_tab(judul: str) -> None:
        if judul not in TAB_DIIZINKAN:
            raise ValueError(
                f"Menolak menulis ke tab '{judul}'. Di spreadsheet laporan "
                f"penjualan, hanya {' dan '.join(TAB_DIIZINKAN)} yang boleh "
                f"ditulis."
            )

    def _pastikan_ada(self, judul: str) -> None:
        self._periksa_tab(judul)
        if judul not in self.s.nama_tab(self.id):
            raise ValueError(
                f"Tab '{judul}' tidak ada di spreadsheet laporan penjualan. "
                f"Tab itu HARUS dibuat lebih dulu oleh Yosua beserta judul "
                f"kolomnya — program sengaja tidak membuatnya sendiri."
            )

    # ------------------------------------------------------------ baca
    def nomor_sudah_ada(self) -> set[str]:
        """Semua No Invoice yang sudah tercatat di DATA_INVOICE."""
        self._pastikan_ada(TAB_INVOICE)
        hasil = self.s.sheets.spreadsheets().values().get(
            spreadsheetId=self.id, range=f"'{TAB_INVOICE}'!B2:B",
        ).execute()
        return {
            str(b[0]).strip()
            for b in (hasil.get("values") or []) if b and str(b[0]).strip()
        }

    # ------------------------------------------------------------ tulis
    def _tambah(self, judul: str, baris: list[list]) -> None:
        self._pastikan_ada(judul)
        if not baris:
            return
        self.s.sheets.spreadsheets().values().append(
            spreadsheetId=self.id,
            range=f"'{judul}'!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": baris},
        ).execute()

    def catat(self, catatan: Catatan, *, sudah: set[str] | None = None) -> str:
        """Tambahkan satu invoice. Kembalikan keterangan apa yang terjadi."""
        ada = self.nomor_sudah_ada() if sudah is None else sudah
        if catatan.nomor in ada:
            return f"dilewati — No Invoice {catatan.nomor} sudah tercatat"

        # DATA_ARTIKEL dulu, baru DATA_INVOICE. Kalau urutannya dibalik dan
        # penulisan artikel gagal di tengah, laporan memuat invoice tanpa
        # rinciannya dan nomornya sudah terlanjur dianggap tercatat.
        self._tambah(TAB_ARTIKEL, catatan.baris_artikel())
        self._tambah(TAB_INVOICE, [catatan.baris_invoice()])
        ada.add(catatan.nomor)
        return (f"tercatat — 1 baris DATA_INVOICE, "
                f"{len(catatan.artikel)} baris DATA_ARTIKEL")
