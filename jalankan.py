#!/usr/bin/env python3
"""Titik masuk program. Jalankan dari folder proyek:

    python3 jalankan.py daftar
    python3 jalankan.py periksa
    python3 jalankan.py buat "Panda"
    python3 jalankan.py buat-semua --pdf
    python3 jalankan.py rekap
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from hp_dokumen.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
