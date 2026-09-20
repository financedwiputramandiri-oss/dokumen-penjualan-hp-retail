"""Membuat ulang draf dokumen begitu ATO terisi atau direvisi.

Arahan Yosua 12 September 2026:

    "PO dapat dianggap final ketika sudah terisi, namun itu tidak sepenuhnya
     final karena jika ada revisi anda juga harus memperbaikinya lagi dan
     menyesuaikannya dengan data yang paling terbaru"

Jadi draf tidak cukup dibuat sekali. Tiap sapuan, keadaan PO sekarang
dibandingkan dengan sapuan sebelumnya. Kalau yang berubah memang mengubah isi
dokumen, dokumen dibuat ulang dan yang lama dipindahkan ke folder kedaluwarsa —
bukan ditimpa, supaya masih bisa ditelusuri kalau ada yang menanyakan draf lama.

Perubahan rumus SAJA tidak membuat dokumen dibuat ulang. Rumus berubah tetap
dilaporkan sebagai alarm, tapi selama angkanya masih sama, isi dokumennya juga
sama dan tidak ada gunanya membuat berkas baru yang identik.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..berkas_dokumen import buat_berkas, nama_aman
from .kondisi import SidikPO

BARU = "baru"
REVISI = "revisi"

# Hanya nilai-nilai ini yang benar-benar mengubah isi dokumen.
_YANG_MENGUBAH_DOKUMEN = ("baris", "qty", "kotor", "nett", "cara_bayar", "sidik_qty")


@dataclass
class HasilDraf:
    tab: str
    alasan: str
    folder: Path
    berkas: list[Path] = field(default_factory=list)
    diarsipkan_ke: Optional[Path] = None
    yang_berubah: list[str] = field(default_factory=list)

    def ringkas(self) -> str:
        if self.alasan == BARU:
            return f"{self.tab} — draf pertama, {len(self.berkas)} berkas"
        ubah = ", ".join(self.yang_berubah) or "isi berubah"
        return f"{self.tab} — DIBUAT ULANG ({ubah}), {len(self.berkas)} berkas"


def _sudah_ada_berkas(folder: Path) -> bool:
    return folder.is_dir() and any(folder.glob("*.xlsx"))


def perlu_draf(lama: Optional[SidikPO], baru: SidikPO, folder: Path) -> Optional[str]:
    """Tentukan apakah draf perlu dibuat. None berarti tidak perlu.

    Pemanggil WAJIB memastikan dulu angka PO ini sudah cocok dengan order
    sheet. Modul ini tidak memeriksa kecocokan, hanya memutuskan perlu atau
    tidaknya membuat ulang.
    """
    if not baru.ato_terisi:
        return None
    if not _sudah_ada_berkas(folder):
        return BARU
    if lama is None:
        return BARU
    if _yang_berubah(lama, baru):
        return REVISI
    return None


def _yang_berubah(lama: SidikPO, baru: SidikPO) -> list[str]:
    nama_enak = {
        "baris": "jumlah baris", "qty": "qty", "kotor": "nilai sebelum diskon",
        "nett": "nilai bersih", "cara_bayar": "cara bayar", "sidik_qty": "susunan qty",
    }
    return [
        nama_enak[k] for k in _YANG_MENGUBAH_DOKUMEN
        if getattr(lama, k) != getattr(baru, k)
    ]


def arsipkan(folder: Path, folder_arsip: Path, waktu: datetime) -> Optional[Path]:
    """Pindahkan draf lama ke folder kedaluwarsa. None kalau tidak ada apa-apa."""
    if not _sudah_ada_berkas(folder):
        return None
    dasar = folder_arsip / f"{folder.name}__{waktu:%Y%m%d_%H%M%S}"
    tujuan, n = dasar, 2
    # Dua pengarsipan bisa jatuh di detik yang sama. Kalau nama tujuannya
    # dipakai begitu saja, shutil.move justru menaruh folder lama DI DALAM
    # arsip sebelumnya, dan draf yang lebih tua jadi tersembunyi.
    while tujuan.exists():
        tujuan = dasar.with_name(f"{dasar.name}_{n}")
        n += 1
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(folder), str(tujuan))
    return tujuan


def buat_draf(
    cfg,
    order,
    keputusan,
    lama: Optional[SidikPO],
    baru: SidikPO,
    alasan: str,
    folder_induk: Path,
    *,
    nomor: str = "________",
    master: dict | None = None,
    pdf: bool = False,
    waktu: Optional[datetime] = None,
) -> HasilDraf:
    """Buat draf dokumen satu PO, mengarsipkan draf lama kalau ada."""
    waktu = waktu or datetime.now()
    folder = folder_induk / nama_aman(baru.nama_sheet) / nama_aman(order.nama_tab)
    arsip = arsipkan(folder, folder_induk / "_KEDALUWARSA", waktu) if alasan == REVISI else None
    berkas = buat_berkas(cfg, order, keputusan, folder, nomor,
                         master=master, pdf=pdf)
    return HasilDraf(
        tab=order.nama_tab,
        alasan=alasan,
        folder=folder,
        berkas=berkas,
        diarsipkan_ke=arsip,
        yang_berubah=_yang_berubah(lama, baru) if lama else [],
    )
