"""Membungkus hasil Google Sheets API supaya bisa dibaca pemindai apa adanya.

Sheets API mengembalikan isi tab sebagai daftar baris, tiap baris daftar sel:

    [["ARTICLE CODE", "PRODUCT NAME", ...],
     ["", "", "", "0-3M", "3-6M", ...],
     ["OB.SS.1.S", "SoftAir Short Set", "Lion Mouse", ...]]

Pemindai di proyek ini hanya memerlukan empat hal dari sebuah lembar:
`title`, `max_row`, `max_column`, dan `cell(baris, kolom).value`. Kelas di
modul ini menyediakan keempatnya, sehingga SELURUH mesin yang sudah
diverifikasi (tata_letak.py, pemindai.py, nilai_bersih.py) bekerja tanpa
diubah sedikit pun — baik sumbernya berkas Excel maupun Sheets API.

Dengan begitu bot tidak perlu mengunduh seluruh spreadsheet tiap hari; cukup
menarik isi tab yang diperlukan.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class Sel:
    """Meniru sel openpyxl: yang dipakai hanya `.value`."""

    value: Any


_KOSONG = Sel(None)


class LembarNilai:
    """Satu tab hasil Sheets API, dibaca seperti worksheet openpyxl.

    Nomor baris dan kolom dimulai dari 1, sama seperti openpyxl.
    """

    __slots__ = ("title", "_baris", "_max_row", "_max_column")

    def __init__(self, judul: str, nilai: Sequence[Sequence[Any]] | None):
        self.title = judul
        self._baris = list(nilai or [])
        self._max_row = len(self._baris)
        self._max_column = max((len(b) for b in self._baris), default=0)

    @property
    def max_row(self) -> int:
        return self._max_row

    @property
    def max_column(self) -> int:
        return self._max_column

    def cell(self, row: int, column: int) -> Sel:
        """Isi satu sel. Di luar jangkauan atau kosong -> value None.

        Sheets API memotong sel kosong di ujung kanan tiap baris dan
        mengirim sel kosong di tengah sebagai teks kosong. Keduanya
        disamakan menjadi None, persis seperti openpyxl, supaya aturan
        "kolom terisi sebagian" tetap membedakan sel kosong dari angka nol.
        """
        if row < 1 or column < 1 or row > self._max_row:
            return _KOSONG
        baris = self._baris[row - 1]
        if column > len(baris):
            return _KOSONG
        v = baris[column - 1]
        if v is None or (isinstance(v, str) and not v.strip()):
            return _KOSONG
        return Sel(v)


class BukuNilai:
    """Sekumpulan tab dari satu spreadsheet, dibaca seperti Workbook openpyxl."""

    def __init__(self, lembar: dict[str, Sequence[Sequence[Any]]]):
        self._lembar = {
            judul: LembarNilai(judul, nilai) for judul, nilai in lembar.items()
        }

    @property
    def sheetnames(self) -> list[str]:
        return list(self._lembar)

    @property
    def worksheets(self) -> list[LembarNilai]:
        return list(self._lembar.values())

    def __getitem__(self, judul: str) -> LembarNilai:
        return self._lembar[judul]

    def __contains__(self, judul: str) -> bool:
        return judul in self._lembar

    def get(self, judul: str) -> Optional[LembarNilai]:
        return self._lembar.get(judul)
