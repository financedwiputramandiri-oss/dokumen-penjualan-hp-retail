"""Memperbarui kode bot dari GitHub, sendiri, tanpa diunduh manusia.

Permintaan Yosua 28 Oktober 2026: *"BUATKAN SEMUA OTOMATIS SENDIRI SAYA
TIDAK MAU MELAKUKAN APAPUN"*.

Selama ini tiap perbaikan format mengharuskan Yosua mengunduh ZIP lalu
mengekstraknya sendiri (CLAUDE.md bagian 25). Itu langkah manual yang
berulang, dan dua kali sudah menimbulkan masalah: ekstraksi yang tidak
lengkap, dan `config/bot.yaml` bawaan repo menimpa pengaturannya (bagian
27). Modul ini menghapus langkah itu — `jadwal/sapu.bat` memanggilnya
sebelum menyapu, jadi kode terbaru terpasang sendiri dua kali sehari.

EMPAT ATURAN YANG JANGAN DILONGGARKAN
-------------------------------------

1. **Berkas pengaturan TIDAK PERNAH ditimpa.** `DILINDUNGI` memuat
   `config/*.yaml`, `config/customer.csv`, kredensial, dan seluruh isi
   `data/`. Inilah cacat bagian 27 yang pernah membuat bot kembali
   mencoba unggahan Drive yang sudah terbukti gagal — dan tidak ada yang
   menyangka bahwa MEMPERBARUI bisa MEMBATALKAN pengaturan.

2. **Kegagalan memperbarui TIDAK PERNAH menggagalkan sapuan.** Internet
   mati, GitHub sedang tumbang, berkas terkunci Excel — semuanya berakhir
   dengan kode 0 dan satu baris pesan. Sapuan dengan kode kemarin jauh
   lebih baik daripada tidak menyapu sama sekali.

3. **Ditulis ke folder sementara dulu, baru disalin.** Kalau unduhan
   putus di tengah, folder proyek tidak pernah berisi setengah versi.

4. **Hanya berkas yang ISINYA BERBEDA yang disalin**, dan jumlahnya
   dilaporkan. Dengan begitu log sapuan memperlihatkan dengan jelas kapan
   kode berubah dan kapan tidak.
"""
from __future__ import annotations

import filecmp
import io
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

AKAR = Path(__file__).resolve().parent.parent

PEMILIK = "financedwiputramandiri-oss"
REPO = "dokumen-penjualan-hp-retail"
CABANG = "claude/admiring-hamilton-did8qv"

# Jalur (relatif ke akar proyek) yang TIDAK BOLEH ditimpa pembaruan.
# Isinya beda di tiap komputer dan tidak ada di repo mana pun.
DILINDUNGI = (
    "config/bot.yaml",
    "config/customer.csv",
    "config/pengaturan.yaml",
    "config/perusahaan.yaml",
    "config/kredensial_bot.json",
    "data",
    "keluaran",
)

BATAS_DETIK = 120


def _url_zip() -> str:
    return (f"https://codeload.github.com/{PEMILIK}/{REPO}/zip/refs/heads/"
            + urllib.parse.quote(CABANG, safe=""))


def dilindungi(rel: str) -> bool:
    """Apakah jalur ini termasuk yang tidak boleh ditimpa."""
    r = rel.replace("\\", "/")
    return any(r == d or r.startswith(d + "/") for d in DILINDUNGI)


def _unduh(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=BATAS_DETIK) as resp:
        return resp.read()


def _salin(sumber: Path, tujuan: Path) -> list[str]:
    """Salin berkas yang isinya berbeda. Mengembalikan daftar yang berubah."""
    berubah: list[str] = []
    for asal in sorted(sumber.rglob("*")):
        if asal.is_dir():
            continue
        rel = asal.relative_to(sumber).as_posix()
        if dilindungi(rel):
            continue
        sasaran = tujuan / rel
        if sasaran.exists() and filecmp.cmp(asal, sasaran, shallow=False):
            continue
        sasaran.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(asal, sasaran)
        berubah.append(rel)
    return berubah


def perbarui(akar: Path | None = None, *, unduh=_unduh) -> tuple[bool, str]:
    """Tarik kode terbaru. Mengembalikan (berhasil, pesan).

    `unduh` bisa diganti saat pengujian supaya tidak menyentuh jaringan.
    """
    akar = Path(akar or AKAR)
    try:
        isi = unduh(_url_zip())
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return False, f"tidak bisa mengunduh pembaruan ({e}) - memakai kode yang ada"

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tdir = Path(tmp)
            with zipfile.ZipFile(io.BytesIO(isi)) as z:
                z.extractall(tdir)
            puncak = [p for p in tdir.iterdir() if p.is_dir()]
            if len(puncak) != 1:
                return False, "isi ZIP tidak seperti yang diharapkan - dilewati"
            berubah = _salin(puncak[0], akar)
    except (zipfile.BadZipFile, OSError, shutil.Error) as e:
        return False, f"gagal memasang pembaruan ({e}) - memakai kode yang ada"

    if not berubah:
        return True, "kode sudah yang terbaru"
    contoh = ", ".join(berubah[:5]) + (" ..." if len(berubah) > 5 else "")
    return True, f"{len(berubah)} berkas diperbarui: {contoh}"


def main() -> int:
    ok, pesan = perbarui()
    print(("PEMBARUAN: " if ok else "PEMBARUAN DILEWATI: ") + pesan)
    # SELALU 0: kegagalan memperbarui tidak boleh menghentikan sapuan.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
