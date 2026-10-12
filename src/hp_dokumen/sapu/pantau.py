"""Aturan alarm: perubahan apa yang dianggap penting dan harus dilaporkan."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .kondisi import SidikPO

# Tingkat kegentingan
GENTING = "GENTING"    # PO lama yang sudah terisi ATO berubah angkanya
PERHATIAN = "PERHATIAN"  # berubah, tapi wajar (PO baru terisi, dsb)
KABAR = "KABAR"        # sekadar pemberitahuan


@dataclass
class Perubahan:
    tingkat: str
    id_sheet: str
    nama_sheet: str
    tab: str
    jenis: str
    keterangan: str
    sebelum: str = ""
    sesudah: str = ""

    @property
    def genting(self) -> bool:
        return self.tingkat == GENTING


def _rp(x: float) -> str:
    return f"Rp{x:,.0f}".replace(",", ".")


def bandingkan(lama: Optional[SidikPO], baru: SidikPO) -> list[Perubahan]:
    """Bandingkan keadaan satu tab PO sekarang dengan sebelumnya."""
    hasil: list[Perubahan] = []

    def tambah(tingkat, jenis, ket, sebelum="", sesudah=""):
        hasil.append(
            Perubahan(tingkat, baru.id_sheet, baru.nama_sheet, baru.tab,
                      jenis, ket, str(sebelum), str(sesudah))
        )

    # PO yang baru pertama kali terlihat
    if lama is None:
        if baru.ato_terisi:
            tambah(KABAR, "PO baru",
                   f"PO baru terbaca dengan ATO sudah terisi: {baru.baris} baris, "
                   f"{baru.qty} pcs, nett {_rp(baru.nett)}.")
        else:
            tambah(KABAR, "PO baru", "PO baru terbaca, ATO belum terisi.")
        return hasil

    # ATO baru terisi -> ini yang ditunggu, bukan masalah
    if not lama.ato_terisi and baru.ato_terisi:
        tambah(PERHATIAN, "ATO baru terisi",
               f"ATO baru terisi: {baru.baris} baris, {baru.qty} pcs, "
               f"nett {_rp(baru.nett)}. Draf dokumen dibuat.",
               "kosong", f"{baru.qty} pcs")
        return hasil

    # ATO yang tadinya terisi jadi kosong -> serius
    if lama.ato_terisi and not baru.ato_terisi:
        tambah(GENTING, "ATO dikosongkan",
               "PO ini tadinya sudah terisi ATO, sekarang kosong.",
               f"{lama.qty} pcs", "kosong")
        return hasil

    if not baru.ato_terisi:
        return hasil

    # ---- pengaman: nilai tidak terbaca, bukan nilai yang berubah ----------
    # Kalau seluruh nilai rupiah tiba-tiba jadi nol padahal jumlah baris dan
    # qty-nya persis sama, hampir pasti yang terjadi adalah hasil rumusnya
    # tidak ikut terbaca, bukan angkanya benar-benar dihapus. Tanpa pengaman
    # ini satu kali salah baca bisa memunculkan puluhan alarm palsu, dan alarm
    # palsu membuat orang berhenti mempercayai laporannya.
    nilai_hilang = (
        baru.kotor == 0
        and lama.kotor > 0
        and baru.qty == lama.qty
        and baru.baris == lama.baris
    )
    if nilai_hilang:
        tambah(PERHATIAN, "Nilai tidak terbaca",
               "Jumlah baris dan qty masih sama persis, tapi nilai rupiahnya "
               "terbaca nol. Kemungkinan besar hasil rumus tidak ikut terbaca, "
               "bukan angkanya yang dihapus. Perlu diperiksa manual.",
               _rp(lama.kotor), "tidak terbaca")
        # qty tetap dibandingkan, tapi nilai rupiahnya tidak
        if lama.sidik_qty != baru.sidik_qty:
            tambah(GENTING, "Susunan qty berubah",
                   "Jumlah totalnya sama, tapi pembagian qty per artikel atau "
                   "per ukuran berubah.", "susunan lama", "susunan baru")
        return hasil

    # ---- mulai sini: PO lama yang ATO-nya sudah terisi, seharusnya beku ----
    if lama.qty != baru.qty:
        selisih = baru.qty - lama.qty
        tambah(GENTING, "Qty berubah",
               f"Jumlah barang berubah {selisih:+,} pcs pada PO yang ATO-nya "
               "sudah terisi.", f"{lama.qty} pcs", f"{baru.qty} pcs")
    elif lama.sidik_qty != baru.sidik_qty:
        tambah(GENTING, "Susunan qty berubah",
               "Jumlah totalnya sama, tapi pembagian qty per artikel atau per "
               "ukuran berubah.", "susunan lama", "susunan baru")

    if lama.baris != baru.baris:
        tambah(GENTING, "Jumlah baris berubah",
               f"Jumlah baris artikel berubah {baru.baris - lama.baris:+}.",
               f"{lama.baris} baris", f"{baru.baris} baris")

    if abs(lama.nett - baru.nett) > 0.5:
        tambah(GENTING, "Nilai bersih berubah",
               f"Nilai bersih berubah {_rp(baru.nett - lama.nett)} pada PO yang "
               "ATO-nya sudah terisi.", _rp(lama.nett), _rp(baru.nett))

    if abs(lama.kotor - baru.kotor) > 0.5:
        tambah(GENTING, "Nilai sebelum diskon berubah",
               f"Nilai sebelum diskon berubah {_rp(baru.kotor - lama.kotor)}.",
               _rp(lama.kotor), _rp(baru.kotor))

    if lama.cara_bayar != baru.cara_bayar:
        tambah(GENTING, "Cara bayar berubah",
               "Kolom nilai bersih yang terisi penuh berubah, jadi cara bayarnya "
               "ikut berubah.", lama.cara_bayar, baru.cara_bayar)

    if lama.sidik_rumus and baru.sidik_rumus and lama.sidik_rumus != baru.sidik_rumus:
        tambah(GENTING, "Rumus berubah",
               "Ada rumus di tab ini yang diubah, padahal ATO-nya sudah terisi. "
               "Angkanya mungkin belum berubah sekarang, tapi bisa berubah nanti.",
               "rumus lama", "rumus baru")

    return hasil
