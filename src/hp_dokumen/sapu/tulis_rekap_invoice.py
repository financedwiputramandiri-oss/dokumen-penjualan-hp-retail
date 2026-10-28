"""Menambahkan satu baris per invoice ke sheet REKAP INVOICE.

Permintaan Yosua 28 Oktober 2026: tiap invoice yang terbit masuk ke SATU
sheet rekap, di samping tab LAP/BUKU di laporan penjualan.

Berkasnya dibuat khusus untuk ini dan isinya seluruhnya milik bot, jadi
tidak ada pekerjaan tangan yang bisa tertimpa. Walau begitu pagarnya tetap
dipasang, sebab berkas yang hari ini kosong bisa saja besok dipakai orang:

1. Hanya tab `REKAP INVOICE` yang boleh disentuh, dan tab itu tidak
   dibuat sendiri kalau hilang.
2. Tab `REKAP INVOICE` DIBUAT SENDIRI kalau belum ada, lengkap dengan
   judul kolomnya. Ini satu-satunya tempat bot boleh membuat tab, dan
   boleh justru karena berkas ini memang berkasnya sendiri. Di berkas
   laporan penjualan milik Yosua, tab yang hilang TETAP tidak pernah
   dibuat - lihat `tulis_laporan.py`.
3. Baris hanya DITAMBAHKAN. Satu-satunya penghapusan yang mungkin adalah
   mengganti baris invoice yang KUNCInya sama persis saat PO direvisi.
4. Kuncinya Customer + Tanggal, sama dengan DATA_INVOICE, supaya kedua
   tempat itu tidak pernah berbeda isi.
"""
from __future__ import annotations

from ..catatan_penjualan import Catatan, FORMAT_TANGGAL, kunci

TAB_REKAP = "REKAP INVOICE"

JUDUL_REKAP = ["Tanggal", "No Invoice", "Tab PO", "Customer", "PT", "Qty",
               "Subtotal", "Diskon", "% Diskon", "Cara Bayar", "Total",
               "DPP", "PPN", "Dicatat"]

KOL_TANGGAL = 0
KOL_CUSTOMER = 3


def baris_rekap(catatan: Catatan, *, tab_po: str = "", pt: str = "",
                subtotal: float = 0.0, persen: str = "",
                cara_bayar: str = "", dicatat: str = "") -> list:
    qty = sum(a[5] for a in catatan.artikel)
    diskon = round(subtotal - catatan.total, 2) if subtotal else ""
    return [
        catatan.tanggal.strftime(FORMAT_TANGGAL),
        catatan.nomor,
        tab_po,
        catatan.customer,
        pt,
        qty,
        round(subtotal, 2) if subtotal else "",
        diskon,
        persen,
        cara_bayar,
        round(catatan.total, 2),
        round(catatan.dpp, 2),
        round(catatan.ppn, 2),
        dicatat,
    ]


class PenulisRekapInvoice:
    """Menambah dan mengganti baris di tab REKAP INVOICE."""

    def __init__(self, sambungan, id_sheet: str):
        self.s = sambungan
        self.id = id_sheet
        self._gid: int | None = None
        self._kunci: set[tuple[str, str]] | None = None

    @staticmethod
    def _periksa_tab(judul: str) -> None:
        if judul != TAB_REKAP:
            raise ValueError(
                f"Menolak menulis ke tab '{judul}'. Di berkas rekap invoice, "
                f"hanya '{TAB_REKAP}' yang boleh ditulis."
            )

    def _id_tab(self) -> int:
        if self._gid is None:
            info = self.s.sheets.spreadsheets().get(
                spreadsheetId=self.id, fields="sheets.properties"
            ).execute()
            for sh in info.get("sheets", []):
                pr = sh.get("properties", {})
                if pr.get("title") == TAB_REKAP:
                    self._gid = pr.get("sheetId")
            if self._gid is None:
                self._gid = self._buat_tab()
        return self._gid

    def _buat_tab(self) -> int:
        """Buat tab REKAP INVOICE beserta judul kolomnya.

        Hanya di berkas rekap ini - berkas yang isinya memang milik bot.
        """
        hasil = self.s.sheets.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={"requests": [{"addSheet": {
                "properties": {"title": TAB_REKAP}}}]},
        ).execute()
        gid = (hasil["replies"][0]["addSheet"]["properties"]["sheetId"])
        self.s.sheets.spreadsheets().values().update(
            spreadsheetId=self.id,
            range=f"'{TAB_REKAP}'!A1:N1",
            valueInputOption="USER_ENTERED",
            body={"values": [JUDUL_REKAP]},
        ).execute()
        return gid

    def _nilai(self) -> list[list]:
        self._id_tab()
        hasil = self.s.sheets.spreadsheets().values().get(
            spreadsheetId=self.id, range=f"'{TAB_REKAP}'!A2:N",
        ).execute()
        return hasil.get("values") or []

    def muat_kunci(self) -> set[tuple[str, str]]:
        if self._kunci is None:
            self._kunci = {
                kunci(b[KOL_CUSTOMER] if len(b) > KOL_CUSTOMER else "",
                      b[KOL_TANGGAL] if len(b) > KOL_TANGGAL else "")
                for b in self._nilai() if any(str(x).strip() for x in b)
            }
        return self._kunci

    def _hapus_kunci(self, k: tuple[str, str]) -> int:
        baris = [
            i for i, b in enumerate(self._nilai(), start=2)
            if kunci(b[KOL_CUSTOMER] if len(b) > KOL_CUSTOMER else "",
                     b[KOL_TANGGAL] if len(b) > KOL_TANGGAL else "") == k
        ]
        if not baris:
            return 0
        gid = self._id_tab()
        self.s.sheets.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={"requests": [
                {"deleteDimension": {"range": {
                    "sheetId": gid, "dimension": "ROWS",
                    "startIndex": r - 1, "endIndex": r}}}
                for r in sorted(baris, reverse=True)]},
        ).execute()
        return len(baris)

    def catat(self, catatan: Catatan, *, paksa: bool = False, **tambahan) -> str:
        k = catatan.kunci
        if not paksa and k in self.muat_kunci():
            return ""
        diganti = self._hapus_kunci(k) if paksa else 0
        self.s.sheets.spreadsheets().values().append(
            spreadsheetId=self.id,
            range=f"'{TAB_REKAP}'!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [baris_rekap(catatan, **tambahan)]},
        ).execute()
        self._kunci = None
        awalan = f"{diganti} baris lama diganti, " if diganti else ""
        return (f"rekap invoice: {awalan}{catatan.customer} "
                f"Rp{catatan.total:,.0f} ditambahkan.")
