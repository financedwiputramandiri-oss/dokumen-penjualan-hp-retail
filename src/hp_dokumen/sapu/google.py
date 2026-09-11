"""Sambungan ke Google Drive dan Google Sheets lewat akun layanan (service account).

Akun layanan adalah "robot" dengan alamat emailnya sendiri. Folder order sheet
cukup di-Share ke alamat itu dengan akses Viewer, lalu bot bisa membaca sendiri
tanpa perlu login siapa pun.

Kredensialnya berupa satu berkas JSON. Taruh di config/kredensial_bot.json.
Berkas itu TIDAK BOLEH masuk git — sudah dikunci lewat .gitignore.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Hanya izin baca untuk Drive, dan tulis untuk menaruh laporan.
LINGKUP = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

MIME_SHEET = "application/vnd.google-apps.spreadsheet"
MIME_FOLDER = "application/vnd.google-apps.folder"
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass
class BerkasDrive:
    id: str
    nama: str
    mime: str
    diubah: str
    ukuran: int = 0


class Sambungan:
    """Pembungkus tipis Google Drive + Sheets."""

    def __init__(self, berkas_kredensial: Path):
        if not berkas_kredensial.exists():
            raise SystemExit(
                f"Berkas kredensial bot tidak ada: {berkas_kredensial}\n"
                "Lihat PANDUAN_BOT.md untuk cara membuatnya (sekitar 10 menit)."
            )
        kredensial = service_account.Credentials.from_service_account_file(
            str(berkas_kredensial), scopes=LINGKUP
        )
        self.email_bot = kredensial.service_account_email
        self.drive = build("drive", "v3", credentials=kredensial, cache_discovery=False)
        self.sheets = build("sheets", "v4", credentials=kredensial, cache_discovery=False)

    # ------------------------------------------------------------- Drive
    def isi_folder(self, id_folder: str) -> list[BerkasDrive]:
        """Daftar berkas di satu folder Drive."""
        hasil: list[BerkasDrive] = []
        token = None
        while True:
            jawab = (
                self.drive.files()
                .list(
                    q=f"'{id_folder}' in parents and trashed = false",
                    fields="nextPageToken, files(id,name,mimeType,modifiedTime,size)",
                    pageSize=200,
                    pageToken=token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            for f in jawab.get("files", []):
                hasil.append(
                    BerkasDrive(
                        id=f["id"], nama=f["name"], mime=f["mimeType"],
                        diubah=f.get("modifiedTime", ""),
                        ukuran=int(f.get("size") or 0),
                    )
                )
            token = jawab.get("nextPageToken")
            if not token:
                break
        return hasil

    def unduh_sebagai_xlsx(self, id_berkas: str, tujuan: Path) -> Optional[Path]:
        """Unduh satu Google Spreadsheet sebagai .xlsx.

        Order sheet yang sangat besar bisa ditolak Google ('file too large').
        Dalam hal itu bot tetap jalan, cukup lewati berkasnya dan laporkan.
        """
        tujuan.parent.mkdir(parents=True, exist_ok=True)
        try:
            minta = self.drive.files().export_media(fileId=id_berkas, mimeType=MIME_XLSX)
            buf = io.BytesIO()
            pengunduh = MediaIoBaseDownload(buf, minta)
            selesai = False
            while not selesai:
                _, selesai = pengunduh.next_chunk()
            tujuan.write_bytes(buf.getvalue())
            return tujuan
        except HttpError:
            return None

    def unggah_laporan(
        self, berkas: Path, id_folder: str, jadikan_sheet: bool = False
    ) -> Optional[str]:
        """Taruh berkas laporan ke folder Drive. Kembalikan id berkasnya."""
        meta = {"name": berkas.name, "parents": [id_folder]}
        if jadikan_sheet:
            meta["mimeType"] = MIME_SHEET
        media = MediaFileUpload(str(berkas), mimetype=MIME_XLSX, resumable=False)
        try:
            f = (
                self.drive.files()
                .create(body=meta, media_body=media, fields="id",
                        supportsAllDrives=True)
                .execute()
            )
            return f.get("id")
        except HttpError:
            return None

    def buat_folder_kalau_belum_ada(self, nama: str, induk: str) -> Optional[str]:
        aman = nama.replace("'", "\\'")
        jawab = (
            self.drive.files()
            .list(
                q=f"'{induk}' in parents and name = '{aman}' "
                f"and mimeType = '{MIME_FOLDER}' and trashed = false",
                fields="files(id)", supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        ada = jawab.get("files", [])
        if ada:
            return ada[0]["id"]
        try:
            f = (
                self.drive.files()
                .create(body={"name": nama, "mimeType": MIME_FOLDER, "parents": [induk]},
                        fields="id", supportsAllDrives=True)
                .execute()
            )
            return f.get("id")
        except HttpError:
            return None

    # ------------------------------------------------------------ Sheets
    def daftar_tab(self, id_sheet: str) -> list[dict]:
        """Judul dan ukuran SEMUA tab, tanpa menarik isinya.

        Nama tab yang dikembalikan LENGKAP — tidak dipotong 31 huruf seperti
        pada ekspor Excel. Panggilan ini murah: hanya beberapa ratus byte.
        """
        jawab = (
            self.sheets.spreadsheets()
            .get(
                spreadsheetId=id_sheet,
                fields=(
                    "sheets.properties.title,"
                    "sheets.properties.sheetId,"
                    "sheets.properties.gridProperties.rowCount,"
                    "sheets.properties.gridProperties.columnCount"
                ),
            )
            .execute()
        )
        hasil = []
        for s in jawab.get("sheets", []):
            pr = s.get("properties", {})
            grid = pr.get("gridProperties", {})
            hasil.append({
                "judul": pr.get("title", ""),
                "id": pr.get("sheetId"),
                "baris": grid.get("rowCount", 0),
                "kolom": grid.get("columnCount", 0),
            })
        return hasil

    def nama_tab(self, id_sheet: str) -> list[str]:
        """Nama semua tab, lengkap tanpa dipotong."""
        return [t["judul"] for t in self.daftar_tab(id_sheet)]

    def ambil_tab(
        self,
        id_sheet: str,
        judul_tab: list[str],
        rumus: bool = False,
        per_permintaan: int = 60,
    ) -> dict[str, list[list]]:
        """Tarik isi beberapa tab sekaligus.

        Memakai batchGet, jadi puluhan tab cukup satu-dua panggilan — bukan
        satu panggilan per tab, dan bukan mengunduh seluruh spreadsheet.

        `rumus=True` mengambil RUMUS tiap sel, bukan hasil hitungnya. Dipakai
        pemantau untuk mendeteksi rumus yang diubah walau angkanya belum
        berubah.
        """
        hasil: dict[str, list[list]] = {}
        if not judul_tab:
            return hasil
        for i in range(0, len(judul_tab), per_permintaan):
            potongan = judul_tab[i:i + per_permintaan]
            jawab = (
                self.sheets.spreadsheets()
                .values()
                .batchGet(
                    spreadsheetId=id_sheet,
                    ranges=[f"'{j}'" for j in potongan],
                    valueRenderOption="FORMULA" if rumus else "UNFORMATTED_VALUE",
                    dateTimeRenderOption="FORMATTED_STRING",
                )
                .execute()
            )
            for judul, bagian in zip(potongan, jawab.get("valueRanges", [])):
                hasil[judul] = bagian.get("values", []) or []
        return hasil

    def buku_dari_tab(self, id_sheet: str, judul_tab: list[str], rumus: bool = False):
        """Ambil beberapa tab dan bungkus supaya bisa dibaca pemindai."""
        from .lembar_api import BukuNilai

        return BukuNilai(self.ambil_tab(id_sheet, judul_tab, rumus=rumus))
