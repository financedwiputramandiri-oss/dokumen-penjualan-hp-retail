"""Menulis hasil sapuan ke dalam sheet OTOMATISASI milik Yosua.

ATURAN PALING PENTING DI MODUL INI:
bot hanya boleh menyentuh tab yang namanya diawali `BOT_`. Tab buatan Yosua
(PENGATURAN, MASTER_CUSTOMER, SURAT_JALAN, INVOICE, dan lain-lain) tidak boleh
dibaca-tulis, dihapus, atau diubah urutannya. Kalau suatu saat ada tab bernama
`BOT_...` yang ternyata buatan manusia, hentikan bot, jangan ditimpa.

Dengan begitu sheet Yosua tetap bisa dipakai manual seperti biasa, dan bot
hanya menambah lembar baru di sebelahnya.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from . import rekap as rkp

AWALAN_BOT = "BOT_"

TAB_DAFTAR = "BOT_DAFTAR_PO"
TAB_PERUBAHAN = "BOT_PERUBAHAN"
TAB_STATUS = "BOT_STATUS"
TAB_REKAP = "BOT_REKAP"


class PenulisSheet:
    """Menulis tab BOT_ ke satu Google Spreadsheet."""

    def __init__(self, sambungan, id_sheet: str):
        self.s = sambungan
        self.id = id_sheet
        self._judul: list[str] = []

    # ------------------------------------------------------------ dasar
    def muat_daftar_tab(self) -> list[str]:
        self._judul = self.s.nama_tab(self.id)
        return self._judul

    def _pastikan_tab(self, judul: str) -> None:
        """Buat tab kalau belum ada. Hanya boleh untuk tab berawalan BOT_."""
        if not judul.startswith(AWALAN_BOT):
            raise ValueError(
                f"Bot menolak menulis ke tab '{judul}'. "
                f"Bot hanya boleh menulis ke tab berawalan '{AWALAN_BOT}'."
            )
        if judul in self._judul:
            return
        self.s.sheets.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={"requests": [{"addSheet": {"properties": {"title": judul}}}]},
        ).execute()
        self._judul.append(judul)

    def tulis_tab(self, judul: str, baris: list[list]) -> None:
        """Kosongkan lalu isi ulang satu tab BOT_."""
        self._pastikan_tab(judul)
        self.s.sheets.spreadsheets().values().clear(
            spreadsheetId=self.id, range=f"'{judul}'", body={}
        ).execute()
        if not baris:
            return
        self.s.sheets.spreadsheets().values().update(
            spreadsheetId=self.id,
            range=f"'{judul}'!A1",
            valueInputOption="RAW",
            body={"values": baris},
        ).execute()

    # ------------------------------------------------------------- isi
    def tulis_status(self, waktu: datetime, jumlah_sheet: int, jumlah_po: int,
                     jumlah_genting: int, jumlah_draf: int,
                     tautan_laporan: str = "") -> None:
        baris = [
            ["STATUS BOT PENYAPU ORDER SHEET"],
            [],
            ["Sapuan terakhir", waktu.strftime("%d %B %Y, %H:%M")],
            ["Order sheet diperiksa", jumlah_sheet],
            ["Tab PO diperiksa", jumlah_po],
            ["Draf dokumen dibuat", jumlah_draf],
            ["Perubahan penting", jumlah_genting],
            [],
            ["Rekap hasil sapuan", f"lihat tab {TAB_REKAP}"],
            ["Berkas laporan lengkap", tautan_laporan or "(tidak dibuat)"],
            [],
            ["CATATAN",
             "Tab yang namanya diawali BOT_ diisi ulang otomatis tiap sapuan. "
             "Jangan diketik manual, isinya akan tertimpa. "
             "Tab lain di sheet ini tidak pernah disentuh bot."],
            ["", "Berkas laporan ditaruh di folder _LAPORAN, satu folder dengan "
                 "dokumennya. Kalau folder itu disinkronkan Google Drive for "
                 "Desktop, laporannya ikut naik ke Drive dengan sendirinya."],
        ]
        if jumlah_genting:
            baris.insert(2, [f"ADA {jumlah_genting} PERUBAHAN PENTING — lihat tab {TAB_PERUBAHAN}"])
        else:
            baris.insert(2, ["Tidak ada perubahan penting pada PO lama."])
        self.tulis_tab(TAB_STATUS, baris)

    def tulis_rekap(self, rekaman: list[dict], waktu: datetime) -> None:
        """Hasil sapuan dalam bentuk paling ringkas: per order sheet.

        Inilah jawaban atas "hasil sapuan bisa dilihat di Drive di mana".
        Tab ini ditulis lewat Sheets API ke berkas yang SUDAH ADA dan
        dimiliki Yosua, jadi tidak pernah kena batas `storageQuotaExceeded`
        yang memblokir pengunggahan berkas baru oleh akun layanan
        (CLAUDE.md bagian 14 dan 30). Tidak perlu Drive for Desktop.
        """
        baris = [
            ["REKAP HASIL SAPUAN"],
            [f"Sapuan {waktu.strftime('%d %B %Y, %H:%M')}"],
            [],
            list(rkp.JUDUL_PER_SHEET),
        ]
        baris.extend(rkp.baris_per_sheet(rekaman))
        baris.append([])
        baris.append([
            "Qty dan nilai dikosongkan untuk order sheet yang dokumennya belum "
            "terbit — angka itu justru yang belum cocok dengan baris TOTAL "
            "order sheet, jadi jangan dipakai sebagai angka resmi."
        ])
        self.tulis_tab(TAB_REKAP, baris)

    def tulis_daftar_po(self, rekaman: Iterable[dict]) -> None:
        baris = [[
            "ORDER SHEET", "TAB PO", "CUSTOMER", "TANGGAL PO", "BLOK", "BARIS",
            "QTY", "SEBELUM DISKON", "CARA BAYAR", "NILAI BERSIH",
            "PERUSAHAAN", "PPN", "DRAF SIAP?", "KETERANGAN",
        ]]
        for r in rekaman:
            baris.append([
                r.get("sumber", ""), r.get("tab", ""), r.get("customer", ""),
                r.get("tanggal", ""), r.get("blok", 0), r.get("baris", 0),
                r.get("qty", 0), round(r.get("kotor", 0.0)),
                r.get("cara_bayar", ""), round(r.get("nett", 0.0)),
                r.get("perusahaan", ""), "YA" if r.get("kena_ppn") else "TIDAK",
                "SIAP" if r.get("siap") else "BELUM", r.get("keterangan", ""),
            ])
        self.tulis_tab(TAB_DAFTAR, baris)

    def tulis_perubahan(self, perubahan: Iterable) -> None:
        baris = [[
            "TINGKAT", "ORDER SHEET", "TAB PO", "JENIS PERUBAHAN",
            "KETERANGAN", "SEBELUMNYA", "SEKARANG",
        ]]
        for p in perubahan:
            baris.append([
                p.tingkat, p.nama_sheet, p.tab, p.jenis,
                p.keterangan, p.sebelum, p.sesudah,
            ])
        if len(baris) == 1:
            baris.append(["-", "", "", "", "Tidak ada perubahan.", "", ""])
        self.tulis_tab(TAB_PERUBAHAN, baris)
