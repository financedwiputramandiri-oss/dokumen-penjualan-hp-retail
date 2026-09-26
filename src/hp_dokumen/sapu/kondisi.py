"""Sidik jari tiap tab PO, untuk membandingkan keadaan sekarang dengan sebelumnya.

Yang dipantau khusus adalah PO LAMA YANG ATO-NYA SUDAH TERISI. PO seperti itu
seharusnya sudah beku: barangnya sudah dikirim dan dokumennya sudah terbit.
Kalau qty atau rumusnya berubah, itu harus dilaporkan.
"""
from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _sidik(teks: str) -> str:
    return hashlib.sha256(teks.encode("utf-8")).hexdigest()[:16]


@dataclass
class SidikPO:
    """Ringkasan satu tab PO pada satu waktu."""

    id_sheet: str
    nama_sheet: str
    tab: str
    ato_terisi: bool
    baris: int
    qty: int
    kotor: float
    nett: float
    cara_bayar: str
    sidik_qty: str = ""       # sidik jari seluruh angka qty
    sidik_rumus: str = ""     # sidik jari seluruh rumus di tab
    diperiksa: str = ""

    @property
    def kunci(self) -> str:
        return f"{self.id_sheet}::{self.tab}"


@dataclass
class Kondisi:
    """Seluruh sidik jari yang tersimpan dari sapuan sebelumnya."""

    versi: int = 2
    disapu_terakhir: str = ""
    disapu_oleh: str = ""                      # nama komputer yang menyapu terakhir
    po: dict = field(default_factory=dict)     # kunci -> dict SidikPO
    sheet: dict = field(default_factory=dict)  # id_sheet -> {"diubah", "nama", "tab"}

    @classmethod
    def muat(cls, berkas: Path) -> "Kondisi":
        if not berkas.exists():
            return cls()
        try:
            d = json.loads(berkas.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        return cls(versi=d.get("versi", 1),
                   disapu_terakhir=d.get("disapu_terakhir", ""),
                   disapu_oleh=d.get("disapu_oleh", ""),
                   po=d.get("po", {}),
                   sheet=d.get("sheet", {}))

    def simpan(self, berkas: Path) -> None:
        berkas.parent.mkdir(parents=True, exist_ok=True)
        self.disapu_terakhir = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.disapu_oleh = nama_komputer()
        berkas.write_text(
            json.dumps(asdict(self), indent=1, ensure_ascii=False), encoding="utf-8"
        )

    def ambil(self, kunci: str) -> Optional[SidikPO]:
        d = self.po.get(kunci)
        return SidikPO(**d) if d else None

    def pasang(self, s: SidikPO) -> None:
        s.diperiksa = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.po[s.kunci] = asdict(s)

    # ---- catatan per spreadsheet, supaya yang tidak berubah bisa dilewati --
    def berubah_sejak_sapuan_lalu(self, id_sheet: str, diubah: str) -> bool:
        """True kalau spreadsheet ini berubah sejak terakhir diperiksa.

        Waktu `diubah` diambil dari Google Drive dan berubah setiap kali ada
        yang mengedit. Kalau sama dengan sapuan sebelumnya, isinya pasti sama
        juga, jadi tidak perlu ditarik sama sekali.
        """
        lama = (self.sheet.get(id_sheet) or {}).get("diubah")
        return not lama or not diubah or lama != diubah

    def catat_sheet(self, id_sheet: str, nama: str, diubah: str, jumlah_tab: int) -> None:
        self.sheet[id_sheet] = {
            "nama": nama,
            "diubah": diubah,
            "tab": jumlah_tab,
            "diperiksa": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }


def sidik_dari_order(id_sheet: str, nama_sheet: str, tab: str, order, keputusan,
                     baris_rumus: list[list] | None = None) -> SidikPO:
    """Bentuk sidik jari satu tab PO dari hasil pemindaian."""
    angka_qty = ";".join(
        f"{b.baris_sheet}:{b.kode}:{','.join(str(q) for q in b.qty_per_ukuran)}"
        for blk in order.blok for b in blk.baris
    )
    rumus = ""
    if baris_rumus:
        rumus = "\n".join(
            "\t".join("" if v is None else str(v) for v in baris)
            for baris in baris_rumus
        )
    return SidikPO(
        id_sheet=id_sheet,
        nama_sheet=nama_sheet,
        tab=tab,
        ato_terisi=order.qty > 0,
        baris=order.jumlah_baris,
        qty=order.qty,
        kotor=round(order.nilai_kotor, 2),
        nett=round(keputusan.nett_total, 2),
        cara_bayar=keputusan.cara_bayar,
        sidik_qty=_sidik(angka_qty),
        sidik_rumus=_sidik(rumus) if rumus else "",
    )


def nama_komputer() -> str:
    """Nama komputer yang menjalankan sapuan.

    Dipakai untuk mengenali kalau bot dijalankan bergantian dari dua
    komputer. Kalau itu terjadi, masing-masing punya kondisi_sapu.json
    sendiri (atau saling menimpa lewat Drive), dan dokumen dibuat ulang
    terus-menerus tanpa ada yang sadar.
    """
    try:
        return platform.node() or ""
    except Exception:
        return ""


def kondisi_dibagi(berkas_kondisi: Path, folder_draf: Path) -> bool:
    """True kalau catatan sapuan ikut disinkronkan ke semua komputer.

    Syaratnya berkas kondisi berada DI DALAM folder draf — folder yang
    disalin Google Drive for Desktop. Kalau begitu, laptop dan komputer
    kantor membaca catatan yang sama, jadi dokumen yang sudah dibuat di
    satu komputer tidak dibuat ulang di komputer lain.

    Kalau berkas kondisinya tinggal di dalam folder proyek masing-masing,
    tiap komputer punya catatan sendiri dan akan mengarsipkan draf komputer
    lain ke _KEDALUWARSA tanpa alasan.
    """
    try:
        berkas_kondisi.resolve().relative_to(folder_draf.resolve())
        return True
    except (ValueError, OSError):
        return False


def salinan_bentrok(berkas_kondisi: Path) -> list[str]:
    """Salinan bentrok yang dibuat Google Drive di sebelah berkas kondisi.

    Kalau dua komputer menulis berkas yang sama sebelum Drive sempat
    menyinkronkan, Drive tidak menggabungkannya — ia menyimpan berkas kedua
    dengan nama lain, misalnya `kondisi_sapu (1).json`. Berkas aslinya
    tetap terbaca, jadi tidak ada galat apa pun dan kejadian itu lewat
    tanpa disadari. Justru itu yang berbahaya: separuh catatan sapuan ada
    di berkas yang tidak pernah dibaca siapa pun.
    """
    try:
        induk = berkas_kondisi.parent
        if not induk.exists():
            return []
        pokok, akhiran = berkas_kondisi.stem, berkas_kondisi.suffix
        bentrok = []
        for lain in sorted(induk.iterdir()):
            if lain.name == berkas_kondisi.name or lain.suffix != akhiran:
                continue
            n = lain.stem
            if n.startswith(pokok) and n != pokok:
                sisa = n[len(pokok):].strip()
                # "kondisi_sapu (1)" dan "kondisi_sapu - salinan bentrok ..."
                if sisa.startswith(("(", "-", "—")) or "bentrok" in sisa.lower() \
                        or "conflict" in sisa.lower():
                    bentrok.append(lain.name)
        return bentrok
    except OSError:
        return []


def peringatan_pindah_komputer(kondisi: "Kondisi", dibagi: bool = False) -> str:
    """Kalimat peringatan kalau sapuan terakhir dari komputer LAIN.

    Kosong kalau komputernya sama, kalau catatan lamanya belum mencantumkan
    nama komputer (kondisi_sapu.json versi lama), ATAU kalau catatan
    sapuannya memang sengaja dibagi lewat Google Drive — pada pemasangan
    multi-perangkat, berpindah komputer justru yang diharapkan.
    """
    lama = (kondisi.disapu_oleh or "").strip()
    kini = nama_komputer().strip()
    if not lama or not kini or lama == kini or dibagi:
        return ""
    return (
        f"Sapuan terakhir dijalankan dari komputer '{lama}', sekarang dari "
        f"'{kini}', padahal catatan sapuan (berkas_kondisi) TIDAK berada di "
        f"dalam folder yang disinkronkan Google Drive. Akibatnya tiap "
        f"komputer punya catatan sendiri dan draf komputer lain diarsipkan "
        f"ke _KEDALUWARSA tanpa alasan. Pindahkan berkas_kondisi di "
        f"config/bot.yaml ke dalam folder draf — lihat PANDUAN_BOT.md "
        f"bagian \"Bot dipakai dari beberapa perangkat\"."
    )
