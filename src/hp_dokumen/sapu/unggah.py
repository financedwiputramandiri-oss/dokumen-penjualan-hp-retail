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
        id_folder = self.folder(nama_sheet, hasil.tab)
        if not id_folder:
            out.gagal.append(f"folder '{nama_sheet}/{hasil.tab}' tidak bisa dibuat")
            return out
        out.id_folder = id_folder
        for berkas in hasil.berkas:
            if self.sambung.unggah_berkas(Path(berkas), id_folder):
                out.jumlah += 1
            else:
                out.gagal.append(f"{berkas.name} gagal diunggah")
        return out
