"""Aturan 3 & 4 — penanganan label ukuran.

Label ukuran SELALU ikut header tabel (blok) asal barang itu.
Tidak boleh ada satu daftar ukuran global untuk seluruh tab.
"""
from __future__ import annotations

import re
from typing import Optional

# Label yang sudah punya satuan ditulis apa adanya.
_POLA_ANGKA_POLOS = re.compile(r"^\d+$")


def rapikan_label(nilai) -> Optional[str]:
    """Ubah isi sel header ukuran jadi teks yang rapi.

    Excel sering menyimpan label angka sebagai bilangan pecahan (2.0),
    jadi 2.0 dirapikan jadi "2". Sel kosong jadi None.
    """
    if nilai is None:
        return None
    if isinstance(nilai, float) and nilai.is_integer():
        return str(int(nilai))
    if isinstance(nilai, int):
        return str(nilai)
    teks = str(nilai).strip()
    return teks or None


def tulis_untuk_deskripsi(label: str, akhiran_y_untuk_angka: bool) -> str:
    """Bentuk label ukuran saat dipakai di deskripsi invoice.

    Angka polos (1, 2, 3) -> "2Y" kalau pengaturan akhiran_y_untuk_angka aktif.
    Label bersatuan (0-3M, 7-8Y, S, M, L, XL, NB) selalu apa adanya.
    """
    label = (label or "").strip()
    if akhiran_y_untuk_angka and _POLA_ANGKA_POLOS.match(label):
        return f"{label}Y"
    return label


def deskripsi_dengan_ukuran(nama_barang: str, label: str, akhiran_y_untuk_angka: bool) -> str:
    """'Luma Satin Kutubaru Kebaya Set Medium Size' + '5-6Y' -> '... Uk. 5-6Y'.

    Pemisahnya ' Uk. ', bukan ' - ', mengikuti faktur asli CV Dwi Putra Mandiri
    (berkas 0250726 KATAMAMA TAPOS di Drive).
    """
    return f"{nama_barang} Uk. {tulis_untuk_deskripsi(label, akhiran_y_untuk_angka)}"


def bagi_rata_nilai(total: float, bobot: list[int]) -> list[float]:
    """Bagi satu nilai rupiah ke beberapa ukuran menurut qty, tanpa selisih.

    Dipakai saat invoice dipecah per ukuran: nilai bersih tersimpan per baris
    (satu baris = satu artikel + satu warna, mencakup semua ukurannya), jadi
    harus dibagi ke tiap ukuran. Sisa pembulatan diberikan ke ukuran dengan
    pecahan terbesar supaya jumlahnya tetap sama persis dengan sumbernya.
    """
    jumlah_bobot = sum(bobot)
    if jumlah_bobot <= 0:
        return [0.0] * len(bobot)
    # kerja dalam satuan sen supaya pembulatan bisa dikendalikan
    total_sen = int(round(total * 100))
    mentah = [total_sen * b / jumlah_bobot for b in bobot]
    dasar = [int(x) for x in mentah]
    sisa = total_sen - sum(dasar)
    urut = sorted(range(len(bobot)), key=lambda i: mentah[i] - dasar[i], reverse=True)
    for k in range(sisa):
        dasar[urut[k % len(urut)]] += 1
    return [x / 100 for x in dasar]
