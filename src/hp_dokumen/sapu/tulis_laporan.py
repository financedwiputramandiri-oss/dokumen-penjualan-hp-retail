"""Menambahkan invoice ke tab laporan bulanan LAP <BLN> dan BUKU <BLN>.

Permintaan Yosua 28 Oktober 2026. Susunan kolomnya dibaca langsung dari
`LAP OKT` dan `BUKU OKT` miliknya, bukan dirancang sendiri — lihat
`catatan_penjualan.JUDUL_LAP` dan `JUDUL_BUKU`.

Modul ini jauh lebih berhati-hati daripada `tulis_catatan.py`, sebab yang
disentuh BUKAN tab kosong yang disiapkan untuk bot: LAP dan BUKU berisi
pekerjaan Yosua berbulan-bulan, diketik tangan, dan tidak ada salinannya.
Empat pagar yang jangan dilonggarkan:

1. **Tidak pernah MENGHAPUS atau MENIMPA baris.** Hanya menyisipkan baris
   baru. Kalau sebuah invoice ternyata sudah ada, modul ini MELEWATinya
   dan melapor — bukan menggantinya. Ini berbeda dari DATA_INVOICE, yang
   memang tab bot dan di sana revisi boleh mengganti.

2. **Tab tidak pernah dibuat sendiri.** Kalau `LAP NOV` belum ada saat
   November tiba, itu harus ketahuan, bukan ditambal dengan tab kosong
   tanpa judul dan tanpa rumus.

3. **Penyisipan di ATAS baris Total.** Tab LAP ditutup baris
   "Total Penjualan <Bulan>". Menambahkan di paling bawah membuat baris
   baru berada DI BAWAH totalnya, jadi tidak pernah ikut terjumlah — dan
   itu tidak kelihatan sampai ada yang menyadari totalnya kurang.

4. **Nomor invoice MELANJUTKAN yang sudah ada di tab itu**, tidak
   mengisi lubang di tengah. Lubang biasanya berarti nomornya dipakai di
   luar sistem ini; mengisinya ulang membuat dua dokumen bernomor sama.

Satu invoice dianggap SUDAH ADA kalau nama customer dan nilai Totalnya
cocok. Nomor invoice tidak bisa dipakai sebagai kunci, sebab invoice yang
baru dibuat bot memang belum punya nomor sampai modul ini memberinya.
"""
from __future__ import annotations

from datetime import date

from ..catatan_penjualan import (
    Catatan, baris_buku, baris_lap, nomor_berikut, tab_buku, tab_lap,
)

# Kolom LAP (0-berbasis): C Nomor Invoice, F Nama Customer, I Total.
LAP_NOMOR, LAP_CUSTOMER, LAP_TOTAL = 2, 5, 8

# Baris pertama yang berisi data, 1-berbasis. Di atasnya judul berkas
# (3 baris), baris kosong, dan judul kolom yang memakai dua baris.
LAP_BARIS_DATA = 7
BUKU_BARIS_DATA = 6

# Selisih rupiah yang masih dianggap invoice yang sama. Angka di LAP
# sering sudah dibulatkan ke rupiah penuh saat diketik tangan.
TOLERANSI = 1.0


def _angka(v) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v or "").strip().replace("Rp", "").replace(" ", "")
    if not t:
        return None
    # Angka Indonesia: titik ribuan, koma desimal. Angka dari Sheets API
    # bisa datang dalam dua-duanya, jadi dicoba apa adanya lebih dulu.
    try:
        return float(t)
    except ValueError:
        pass
    try:
        return float(t.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _nama(v) -> str:
    return str(v or "").strip().upper()


class PenulisLaporan:
    """Menyisipkan invoice ke LAP <BLN> dan BUKU <BLN>."""

    def __init__(self, sambungan, id_sheet: str):
        self.s = sambungan
        self.id = id_sheet
        self._gid: dict[str, int] = {}
        self._isi: dict[str, list[list]] = {}

    # ------------------------------------------------------------ pagar
    def _tab_ada(self, judul: str) -> bool:
        return judul in self._semua_tab()

    def _semua_tab(self) -> dict[str, int]:
        if not self._gid:
            info = self.s.sheets.spreadsheets().get(
                spreadsheetId=self.id, fields="sheets.properties"
            ).execute()
            for sh in info.get("sheets", []):
                pr = sh.get("properties", {})
                self._gid[pr.get("title", "")] = pr.get("sheetId")
        return self._gid

    @staticmethod
    def _periksa_judul(judul: str) -> None:
        """Hanya tab LAP dan BUKU bulanan. Nama lain ditolak."""
        bagian = judul.split(" ", 1)
        if len(bagian) != 2 or bagian[0] not in ("LAP", "BUKU"):
            raise ValueError(
                f"Menolak menulis ke tab '{judul}'. Modul ini hanya boleh "
                f"menyentuh tab 'LAP <BLN>' dan 'BUKU <BLN>'."
            )

    # ------------------------------------------------------------ baca
    def _nilai(self, judul: str) -> list[list]:
        self._periksa_judul(judul)
        if judul not in self._isi:
            hasil = self.s.sheets.spreadsheets().values().get(
                spreadsheetId=self.id, range=f"'{judul}'!A1:O",
            ).execute()
            self._isi[judul] = hasil.get("values") or []
        return self._isi[judul]

    def nomor_terpakai(self, judul: str) -> list[str]:
        return [
            b[LAP_NOMOR] for b in self._nilai(judul)[LAP_BARIS_DATA - 1:]
            if len(b) > LAP_NOMOR and str(b[LAP_NOMOR]).strip()
        ]

    def sudah_ada(self, judul: str, customer: str, total: float) -> str | None:
        """Nomor invoice yang sudah tercatat untuk customer+total ini."""
        for b in self._nilai(judul)[LAP_BARIS_DATA - 1:]:
            if len(b) <= LAP_TOTAL:
                continue
            t = _angka(b[LAP_TOTAL])
            if t is None or _nama(b[LAP_CUSTOMER]) != _nama(customer):
                continue
            if abs(t - total) <= TOLERANSI:
                nomor = str(b[LAP_NOMOR]).strip() if len(b) > LAP_NOMOR else ""
                return nomor or "(tanpa nomor)"
        return None

    def _baris_total(self, judul: str) -> int | None:
        """Nomor baris (1-berbasis) baris 'Total Penjualan ...' di LAP."""
        for i, b in enumerate(self._nilai(judul), start=1):
            if i < LAP_BARIS_DATA:
                continue
            if b and str(b[0]).strip().upper().startswith("TOTAL PENJUALAN"):
                return i
        return None

    def _baris_terisi_terakhir(self, judul: str) -> int:
        isi = self._nilai(judul)
        for i in range(len(isi), 0, -1):
            if any(str(x).strip() for x in isi[i - 1]):
                return i
        return LAP_BARIS_DATA - 1

    # ------------------------------------------------------------ tulis
    def _sisipkan(self, judul: str, mulai: int, baris: list[list]) -> None:
        """Sisipkan `baris` tepat DI ATAS baris nomor `mulai`."""
        self._periksa_judul(judul)
        if not baris:
            return
        gid = self._semua_tab()[judul]
        self.s.sheets.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={"requests": [{"insertDimension": {
                "range": {"sheetId": gid, "dimension": "ROWS",
                          "startIndex": mulai - 1,
                          "endIndex": mulai - 1 + len(baris)},
                "inheritFromBefore": True}}]},
        ).execute()
        lebar = max(len(b) for b in baris)
        rapi = [list(b) + [""] * (lebar - len(b)) for b in baris]
        akhir = mulai + len(baris) - 1
        self.s.sheets.spreadsheets().values().update(
            spreadsheetId=self.id,
            range=f"'{judul}'!A{mulai}:{chr(ord('A') + lebar - 1)}{akhir}",
            valueInputOption="USER_ENTERED",
            body={"values": rapi},
        ).execute()
        self._isi.pop(judul, None)

    def catat(self, catatan: Catatan, *, keterangan: str = "") -> str:
        """Sisipkan satu invoice ke LAP dan BUKU bulan tanggalnya.

        Mengembalikan kalimat yang bisa langsung masuk laporan sapuan.
        BUKU ditulis LEBIH DULU: kalau urutannya dibalik lalu gagal di
        tengah, laporan memuat invoice tanpa rinciannya sama sekali.
        """
        jlap, jbuku = tab_lap(catatan.tanggal), tab_buku(catatan.tanggal)
        for j in (jlap, jbuku):
            if not self._tab_ada(j):
                return (f"Tab '{j}' tidak ada di spreadsheet laporan "
                        f"penjualan. Invoice {catatan.customer} TIDAK "
                        f"dicatat. Buat dulu tabnya, jangan dibuat bot.")

        lama = self.sudah_ada(jlap, catatan.customer, catatan.total)
        if lama:
            return (f"{catatan.customer} Rp{catatan.total:,.0f} sudah ada di "
                    f"{jlap} sebagai {lama} - dilewati.")

        if not catatan.nomor:
            catatan.nomor = nomor_berikut(self.nomor_terpakai(jlap),
                                          catatan.tanggal)

        baris = self._baris_terisi_terakhir(jbuku) + 1
        self._sisipkan(jbuku, baris, baris_buku(catatan, keterangan=keterangan))

        total = self._baris_total(jlap)
        sisip = total if total else self._baris_terisi_terakhir(jlap) + 1
        urut = sisip - LAP_BARIS_DATA + 1
        self._sisipkan(jlap, sisip, [baris_lap(catatan, urut,
                                               keterangan=keterangan)])

        return (f"{catatan.customer} Rp{catatan.total:,.0f} dicatat sebagai "
                f"{catatan.nomor} di {jlap} dan {jbuku}.")
