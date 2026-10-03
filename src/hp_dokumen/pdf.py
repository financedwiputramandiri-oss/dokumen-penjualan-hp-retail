"""Ubah berkas .xlsx jadi .pdf memakai LibreOffice.

Kalau LibreOffice tidak ada atau modul Calc-nya belum terpasang, program tetap
jalan dan hanya memberi tahu — berkas Excel-nya tetap dibuat.

Di Ubuntu/Debian, modul yang dibutuhkan: sudo apt install libreoffice-calc
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def cari_libreoffice() -> str | None:
    return shutil.which("libreoffice") or shutil.which("soffice")


def libreoffice_ada() -> bool:
    return cari_libreoffice() is not None


def ke_pdf(berkas_xlsx: Path, folder_tujuan: Path | None = None) -> tuple[Path | None, str]:
    """Ubah satu berkas .xlsx jadi .pdf.

    Kembalikan (path_pdf, pesan). path_pdf None kalau gagal, pesan menjelaskan
    sebabnya supaya bisa ditampilkan ke pengguna.
    """
    exe = cari_libreoffice()
    if not exe:
        return None, "LibreOffice tidak terpasang di komputer ini."

    folder_tujuan = folder_tujuan or berkas_xlsx.parent
    folder_tujuan.mkdir(parents=True, exist_ok=True)

    lingkungan = dict(os.environ)
    lingkungan.setdefault("HOME", tempfile.gettempdir())

    with tempfile.TemporaryDirectory(prefix="lo_profil_") as profil:
        # nama berkas bisa mengandung '&' atau spasi; salin dulu ke nama
        # sederhana supaya LibreOffice tidak salah membacanya
        with tempfile.TemporaryDirectory(prefix="lo_masuk_") as masuk:
            sementara = Path(masuk) / "dokumen.xlsx"
            shutil.copy(berkas_xlsx, sementara)
            keluar = Path(masuk) / "hasil"
            keluar.mkdir()
            try:
                proses = subprocess.run(
                    [
                        exe, "--headless", "--norestore", "--invisible",
                        f"-env:UserInstallation=file://{profil}",
                        "--convert-to", "pdf:calc_pdf_Export",
                        "--outdir", str(keluar), str(sementara),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=lingkungan,
                )
            except subprocess.TimeoutExpired:
                return None, "LibreOffice terlalu lama merespons (lebih dari 5 menit)."

            hasil = keluar / "dokumen.pdf"
            if not hasil.exists():
                pesan = (proses.stderr or proses.stdout or "").strip().splitlines()
                keterangan = pesan[-1] if pesan else "penyebab tidak diketahui"
                if "could not be loaded" in keterangan:
                    keterangan += " (modul Calc belum terpasang: sudah coba 'apt install libreoffice-calc'?)"
                return None, f"LibreOffice gagal membuat PDF: {keterangan}"

            tujuan = folder_tujuan / (berkas_xlsx.stem + ".pdf")
            shutil.copy(hasil, tujuan)
            return tujuan, "berhasil"
