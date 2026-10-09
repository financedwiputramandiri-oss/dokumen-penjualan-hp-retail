"""Menaruh dokumen hasil bot ke folder Google Drive milik Yosua.

Tanpa ini dokumen hanya ada di komputer yang menjalankan bot, dan divisi tidak
bisa mengambilnya. Susunan folder di Drive dibuat mengikuti cara orang mencari:

    DOKUMEN OTOMATIS HAPPY PUMPKIN/
      Order Sheet Agustus 2026/
        PO 20 Agustus - Miniku/
          INVOICE_PO_20_Agustus_-_Miniku.xlsx
          SURAT_JALAN_...
          FAKTUR_PAJAK_...
          PACKING_LIST_...

Nama folder memakai nama asli order sheet dan tab PO, bukan nama berkas yang
sudah diseragamkan, supaya enak dibaca orang.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .draf import HasilDraf

# Batasan Google, bukan salah pengaturan: akun layanan TIDAK punya jatah
# penyimpanan Drive, jadi tidak bisa membuat berkas baru di My Drive siapa pun.
# Folder bisa dibuat (folder tidak memakan ruang), berkas tidak.
_TANPA_KUOTA = "storageQuotaExceeded"

PESAN_TANPA_KUOTA = (
    "Akun layanan Google tidak punya jatah penyimpanan Drive, jadi tidak bisa "
    "menaruh berkas di My Drive. Ini batasan Google - menambah izin TIDAK akan "
    "menolongnya. Dokumen tetap dibuat di folder keluaran/draf. Untuk "
    "memunculkannya di Drive, pakai Google Drive for Desktop lalu arahkan "
    "folder_draf di config/bot.yaml ke folder yang disinkronkan, atau "
    "kosongkan folder_dokumen_id supaya bot berhenti mencoba mengunggah."
)


@dataclass
class HasilUnggah:
    tab: str
    jumlah: int = 0
    gagal: list[str] = field(default_factory=list)
    id_folder: Optional[str] = None

    @property
    def tautan(self) -> str:
        return f"https://drive.google.com/drive/folders/{self.id_folder}" if self.id_folder else ""


class PengunggahDokumen:
    """Menyalin berkas draf ke Drive, membuat foldernya kalau belum ada.

    Id folder yang sudah pernah dibuat disimpan di ingatan selama satu sapuan,
    supaya folder bulan yang sama tidak ditanyakan berulang kali ke Google.
    """

    def __init__(self, sambung, id_induk: str):
        self.sambung = sambung
        self.id_induk = id_induk
        self._folder: dict[tuple[str, ...], Optional[str]] = {}
        # Kalau Google menolak karena kuota, penolakan itu pasti berlaku untuk
        # SEMUA berkas. Mencoba ratusan kali hanya memperlambat sapuan dan
        # membanjiri laporan dengan pesan yang sama.
        self.dimatikan: Optional[str] = None

    def folder(self, *jalur: str) -> Optional[str]:
        """Id folder di dalam induk, dibuat bertingkat sesuai `jalur`."""
        kunci: tuple[str, ...] = ()
        induk = self.id_induk
        for nama in jalur:
            kunci = kunci + (nama,)
            if kunci in self._folder:
                induk = self._folder[kunci]
            else:
                induk = self.sambung.buat_folder_kalau_belum_ada(nama, induk)
                self._folder[kunci] = induk
            if not induk:
                return None
        return induk

    def unggah(self, hasil: HasilDraf, nama_sheet: str) -> HasilUnggah:
        out = HasilUnggah(tab=hasil.tab)
        if self.dimatikan:
            out.gagal.append(self.dimatikan)
            return out
        try:
            id_folder = self.folder(nama_sheet, hasil.tab)
        except Exception as e:
            out.gagal.append(f"folder '{nama_sheet}/{hasil.tab}' gagal dibuat: {e}")
            return out
        if not id_folder:
            out.gagal.append(f"folder '{nama_sheet}/{hasil.tab}' tidak bisa dibuat")
            return out
        out.id_folder = id_folder
        for berkas in hasil.berkas:
            try:
                if self.sambung.unggah_berkas(Path(berkas), id_folder):
                    out.jumlah += 1
                else:
                    out.gagal.append(f"{berkas.name}: ditolak tanpa keterangan")
            except Exception as e:
                if _TANPA_KUOTA in str(e):
                    self.dimatikan = PESAN_TANPA_KUOTA
                    out.gagal.append(PESAN_TANPA_KUOTA)
                    return out
                # Sebab aslinya WAJIB ikut tercatat. Tanpa ini laporannya hanya
                # "0 berkas naik ke Drive", dan tidak ada yang bisa dikerjakan.
                out.gagal.append(f"{berkas.name}: {e}")
        return out
