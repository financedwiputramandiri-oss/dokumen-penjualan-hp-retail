"""Pencocokan wajib sebelum dokumen boleh dibuat.

Kalau ada yang tidak cocok, program BERHENTI dan melaporkan — tidak
melanjutkan membuat dokumen. Ini permintaan tegas di CLAUDE.md dan SKILL.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .konfigurasi import Customer, Pengaturan
from .model import Order
from .nilai_bersih import nett_baris, persen_diskon_efektif, tarif_tambahan_tertulis
from .pemindai import cari_di_master
from .model import KeputusanNett


@dataclass
class Pemeriksaan:
    nama: str
    nilai_hitung: str
    nilai_sheet: str
    cocok: bool
    keterangan: str = ""


@dataclass
class HasilRekonsiliasi:
    order: Order
    keputusan: KeputusanNett
    periksa: list[Pemeriksaan] = field(default_factory=list)
    peringatan: list[str] = field(default_factory=list)

    @property
    def lolos(self) -> bool:
        return all(p.cocok for p in self.periksa)

    @property
    def yang_gagal(self) -> list[Pemeriksaan]:
        return [p for p in self.periksa if not p.cocok]


def _diskon_dasar(order, keputusan, efektif: float) -> float:
    """Diskon dasar sebelum tambahan CBD/COD, untuk dibandingkan dengan kolom AB."""
    dipakai = next((k for k in order.kolom_nett() if k.kunci == keputusan.kolom), None)
    tambahan = dipakai.tarif if dipakai else None
    if tambahan is None:
        return efektif
    return 1 - (1 - efektif) / (1 - tambahan)


def _rp(x: float) -> str:
    return f"Rp{x:,.0f}".replace(",", ".")


def periksa_order(
    order: Order,
    keputusan: KeputusanNett,
    pengaturan: Pengaturan,
    master_harga: dict[str, tuple[str, float]] | None = None,
    customer: Customer | None = None,
) -> HasilRekonsiliasi:
    tol = pengaturan.toleransi_cocok
    hasil = HasilRekonsiliasi(order=order, keputusan=keputusan)
    t = order.total_sheet

    # 1. total qty vs baris TOTAL milik order sheet
    if t and t.qty is not None:
        hasil.periksa.append(
            Pemeriksaan(
                "Total qty (pcs)",
                f"{order.qty:,}".replace(",", "."),
                f"{t.qty:,}".replace(",", "."),
                order.qty == t.qty,
                f"baris TOTAL order sheet: baris {t.baris_sheet}",
            )
        )
    else:
        hasil.peringatan.append("Baris TOTAL order sheet tidak ada — qty tidak bisa dicocokkan.")

    # 2. nilai sebelum diskon vs baris TOTAL
    if t and t.nilai_kotor is not None:
        hasil.periksa.append(
            Pemeriksaan(
                "Nilai sebelum diskon",
                _rp(order.nilai_kotor),
                _rp(t.nilai_kotor),
                abs(order.nilai_kotor - t.nilai_kotor) <= tol,
                "jumlah kolom TOTAL ATO (VALUE) / kolom Z",
            )
        )

    # 3. nilai bersih vs jumlah kolom sumbernya
    jumlah_kolom = sum(nett_baris(b, keputusan.kolom) for b in order.semua_baris)
    hasil.periksa.append(
        Pemeriksaan(
            f"Nilai bersih ({keputusan.kolom_sumber})",
            _rp(keputusan.nett_total),
            _rp(jumlah_kolom),
            abs(keputusan.nett_total - jumlah_kolom) <= tol,
            keputusan.alasan,
        )
    )

    # 4. nilai bersih TOP juga harus sama dengan baris TOTAL kolom AC
    if keputusan.kolom == "TOP" and t and t.total_value:
        hasil.periksa.append(
            Pemeriksaan(
                "Nilai bersih vs baris TOTAL sheet",
                _rp(keputusan.nett_total),
                _rp(t.total_value),
                abs(keputusan.nett_total - t.total_value) <= tol,
                "kolom AC di baris TOTAL",
            )
        )

    # 5. aritmetika tiap baris: nilai kotor harus = qty x harga
    meleset = [
        b for b in order.semua_baris if abs(b.nilai_kotor - b.qty * b.harga) > tol
    ]
    hasil.periksa.append(
        Pemeriksaan(
            "Tiap baris: qty x harga = nilai kotor",
            f"{len(order.semua_baris) - len(meleset)} baris cocok",
            f"{len(order.semua_baris)} baris",
            not meleset,
            "" if not meleset else "baris meleset: "
            + ", ".join(str(b.baris_sheet) for b in meleset[:10]),
        )
    )

    # 6. tidak boleh ada harga nol
    nol = [b for b in order.semua_baris if b.harga <= 0]
    hasil.periksa.append(
        Pemeriksaan(
            "Tidak ada harga nol",
            f"{len(nol)} baris berharga nol",
            "0 baris",
            not nol,
            "" if not nol else "baris: " + ", ".join(str(b.baris_sheet) for b in nol[:10]),
        )
    )

    # 7. semua kode artikel ada di master harga
    #
    # Pencariannya lewat cari_di_master(), yang TIDAK peduli huruf besar-kecil.
    # Pemindai sudah begitu sejak bagian 21 CLAUDE.md, tapi pemeriksa ini dulu
    # tertinggal memakai `in master_harga` yang peka huruf — akibatnya
    # `41065 (bottom/Celana)` dianggap artikel tak terdaftar dan SELURUH
    # dokumen bulan itu diblokir, padahal barangnya sama dan harganya sudah
    # benar diambil dari master.
    if master_harga:
        cocok = {k: cari_di_master(master_harga, k) for k in {b.kode for b in order.semua_baris}}
        hilang = sorted({k for k, v in cocok.items() if v is None})
        hasil.periksa.append(
            Pemeriksaan(
                "Kode artikel ada di master harga",
                f"{len(hilang)} kode tidak ketemu",
                "0 kode",
                not hilang,
                "" if not hilang else ", ".join(hilang[:10]),
            )
        )
        beda_nama = sorted(
            {
                b.kode
                for b in order.semua_baris
                if cocok.get(b.kode)
                and b.nama
                and cocok[b.kode][0]
                and b.nama != cocok[b.kode][0]
            }
        )
        if beda_nama:
            hasil.peringatan.append(
                "Nama barang beda dengan master harga untuk kode: "
                + ", ".join(beda_nama[:10])
                + ". Dokumen memakai nama dari master harga."
            )
        beda_harga = sorted(
            {
                b.kode
                for b in order.semua_baris
                if cocok.get(b.kode)
                and cocok[b.kode][1] > 0
                and abs(b.harga - cocok[b.kode][1]) > tol
            }
        )
        if beda_harga:
            hasil.peringatan.append(
                "CEK HARGA: harga di PO beda dengan master harga untuk kode: "
                + ", ".join(beda_harga[:10])
            )

    # 8. kolom DISC (AB) hanya alat periksa — laporkan kalau tidak sejalan
    persen_sheet = {round(b.disc_persen, 6) for b in order.semua_baris}
    efektif = persen_diskon_efektif(order.nilai_kotor, keputusan.nett_total)
    if len(persen_sheet) == 1:
        satu = persen_sheet.pop()
        # untuk CBD/COD ada tambahan 1,5% di atas diskon dasar, jadi wajar beda
        dasar_diharapkan = efektif if keputusan.kolom == "TOP" else _diskon_dasar(order, keputusan, efektif)
        if abs(satu - dasar_diharapkan) > 0.0005:
            hasil.peringatan.append(
                f"Kolom DISC (AB) di order sheet tertulis {satu:.2%}, tapi nilai bersih "
                f"yang sebenarnya setara diskon {dasar_diharapkan:.3%}. "
                "Dokumen memakai nilai bersih dari kolom sumber (benar); "
                "kolom AB di order sheet perlu dirapikan Sales."
            )
    elif len(persen_sheet) > 1:
        hasil.peringatan.append(
            "Kolom DISC (AB) tidak seragam dalam satu tab: "
            + ", ".join(f"{p:.2%}" for p in sorted(persen_sheet))
            + ". Invoice memakai satu persen diskon, jadi angkanya dihitung dari nilai bersih."
        )

    # 9. kolom CBD/COD terisi sebagian -> minta Sales melengkapi
    n = keputusan.jumlah_baris
    if 0 < keputusan.terisi_cbd < n:
        hasil.peringatan.append(
            f"Kolom DISCOUNT CBD baru terisi {keputusan.terisi_cbd} dari {n} baris. "
            "Order ini diperlakukan TOP. Minta Sales menarik rumusnya sampai baris terakhir "
            "kalau memang order CBD."
        )
    if 0 < keputusan.terisi_cod < n:
        hasil.peringatan.append(
            f"Kolom DISCOUNT COD baru terisi {keputusan.terisi_cod} dari {n} baris. "
            "Order ini diperlakukan TOP."
        )

    # 11. tarif tambahan CBD/COD: bandingkan yang sebenarnya dengan judul kolom
    if keputusan.kolom != "TOP":
        dasar = sum(b.total_value for b in order.semua_baris)
        if dasar > 0:
            rasio = keputusan.nett_total / dasar
            tambahan = 1 - rasio
            dipakai = next((k for k in order.kolom_nett() if k.kunci == keputusan.kolom), None)
            judul = dipakai.judul if dipakai else ""
            nilai_tertulis = dipakai.tarif if dipakai else None
            if nilai_tertulis is not None:
                if abs(tambahan - nilai_tertulis) > 0.0005:
                    hasil.peringatan.append(
                        f"Potongan {keputusan.cara_bayar} yang sebenarnya di kolomnya "
                        f"{tambahan:.2%}, padahal judul kolomnya tertulis "
                        f"'{judul.strip()}' ({nilai_tertulis:.2%}). "
                        "Dokumen memakai angka asli dari kolom (benar). "
                        "Tanyakan ke Sales mana yang seharusnya dipakai."
                    )

    # 10. kelengkapan data customer
    if customer is None:
        hasil.peringatan.append(
            f"Tab '{order.nama_tab}' belum terdaftar di config/customer.csv."
        )
    else:
        kurang = customer.kekurangan()
        if kurang:
            hasil.peringatan.append(
                f"Data customer '{customer.kunci}' belum lengkap: {', '.join(kurang)}. "
                "Isi di config/customer.csv."
            )

    hasil.peringatan.extend(order.peringatan)
    return hasil
