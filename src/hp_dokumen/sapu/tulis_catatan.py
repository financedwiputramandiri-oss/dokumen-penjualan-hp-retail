"""Menambahkan baris invoice ke spreadsheet LAPORAN PENJUALAN.

Berbeda dari `tulis_sheet.py` yang hanya boleh menyentuh tab berawalan
`BOT_`, modul ini menulis ke tab milik Yosua sendiri — DATA_INVOICE dan
DATA_ARTIKEL. Karena itu pagarnya dibuat lebih KETAT, bukan lebih longgar:

1. HANYA dua tab itu yang boleh disentuh. Nama lain ditolak dengan galat,
   dan penolakan itu diuji. Tab laporan bulanan Yosua (LAP, BUKU, ARTIKEL,
   TAGIHAN) tidak boleh tersentuh sama sekali — isinya hasil kerja
   berbulan-bulan dan tidak ada salinannya.

2. Tab yang belum ada TIDAK dibuat sendiri. Kalau tabnya hilang, itu harus
   ketahuan, bukan ditambal diam-diam.

3. Baris lama hanya dihapus kalau KUNCInya cocok persis, dan jumlah baris
   yang akan dihapus dilaporkan. Tidak ada `clear` seluruh tab di mana pun
   di modul ini.

REVISI MENGGANTI, bukan menambah — keputusan Yosua 24 Oktober 2026. Karena
nomor invoice dikosongkan, kunci penggantinya Customer + Tanggal.

Cara menggantinya: baris lama DIHAPUS lalu baris baru DITAMBAHKAN di bawah,
bukan ditimpa di tempat. Dua alasan:
  - jumlah baris DATA_ARTIKEL bisa berubah saat PO direvisi, jadi menimpa
    di tempat akan meninggalkan sisa baris lama;
  - urutan baris harus mengikuti WAKTU PEMBUATAN, dan invoice yang baru
    direvisi memang yang paling baru.
"""
from __future__ import annotations

from ..catatan_penjualan import TAB_ARTIKEL, TAB_INVOICE, Catatan, kunci

TAB_DIIZINKAN = (TAB_INVOICE, TAB_ARTIKEL)

# Kolom yang dipakai sebagai kunci, 0-berbasis: A Tanggal, C Customer.
KOL_TANGGAL = 0
KOL_CUSTOMER = 2


class PenulisCatatan:
    """Menambah dan mengganti baris di DATA_INVOICE dan DATA_ARTIKEL."""

    def __init__(self, sambungan, id_sheet: str):
        self.s = sambungan
        self.id = id_sheet
        self._gid: dict[str, int] = {}

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

    def _id_tab(self, judul: str) -> int:
        """gid tab, dibutuhkan untuk menghapus baris."""
        self._pastikan_ada(judul)
        if judul not in self._gid:
            info = self.s.sheets.spreadsheets().get(
                spreadsheetId=self.id, fields="sheets.properties"
            ).execute()
            for sh in info.get("sheets", []):
                pr = sh.get("properties", {})
                self._gid[pr.get("title", "")] = pr.get("sheetId")
        return self._gid[judul]

    # ------------------------------------------------------------ baca
    def _nilai(self, judul: str) -> list[list]:
        self._pastikan_ada(judul)
        hasil = self.s.sheets.spreadsheets().values().get(
            spreadsheetId=self.id, range=f"'{judul}'!A2:I",
        ).execute()
        return hasil.get("values") or []

    def _baris_berkunci(self, judul: str, k: tuple[str, str]) -> list[int]:
        """Nomor baris sheet (1-berbasis) yang kuncinya cocok."""
        cocok = []
        for i, b in enumerate(self._nilai(judul), start=2):
            tgl = b[KOL_TANGGAL] if len(b) > KOL_TANGGAL else ""
            cust = b[KOL_CUSTOMER] if len(b) > KOL_CUSTOMER else ""
            if kunci(cust, tgl) == k:
                cocok.append(i)
        return cocok

    # ------------------------------------------------------------ tulis
    def _hapus(self, judul: str, baris: list[int]) -> None:
        """Hapus baris tertentu. Dari BAWAH ke atas, supaya nomor baris di
        atasnya tidak bergeser saat penghapusan berikutnya."""
        if not baris:
            return
        gid = self._id_tab(judul)
        permintaan = [
            {"deleteDimension": {"range": {
                "sheetId": gid, "dimension": "ROWS",
                "startIndex": r - 1, "endIndex": r}}}
            for r in sorted(baris, reverse=True)
        ]
        self.s.sheets.spreadsheets().batchUpdate(
            spreadsheetId=self.id, body={"requests": permintaan}
        ).execute()

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

    def catat(self, catatan: Catatan) -> str:
        """Tambahkan satu invoice, mengganti yang lama kalau sudah ada."""
        k = catatan.kunci
        lama_inv = self._baris_berkunci(TAB_INVOICE, k)
        lama_art = self._baris_berkunci(TAB_ARTIKEL, k)

        # Hapus yang lama LEBIH DULU, dua-duanya, baru tulis yang baru.
        # Kalau yang baru ditulis dulu, pencarian baris lama ikut menemukan
        # baris yang baru saja ditambahkan dan langsung menghapusnya lagi.
        self._hapus(TAB_ARTIKEL, lama_art)
        self._hapus(TAB_INVOICE, lama_inv)

        # DATA_ARTIKEL dulu, baru DATA_INVOICE. Kalau urutannya dibalik dan
        # penulisan artikel gagal di tengah, laporan memuat invoice tanpa
        # rinciannya.
        self._tambah(TAB_ARTIKEL, catatan.baris_artikel())
        self._tambah(TAB_INVOICE, [catatan.baris_invoice()])

        n = len(catatan.artikel)
        if lama_inv or lama_art:
            return (f"DIGANTI — {len(lama_inv)} baris DATA_INVOICE dan "
                    f"{len(lama_art)} baris DATA_ARTIKEL yang lama dihapus, "
                    f"diganti 1 + {n} baris baru")
        return f"tercatat — 1 baris DATA_INVOICE, {n} baris DATA_ARTIKEL"
