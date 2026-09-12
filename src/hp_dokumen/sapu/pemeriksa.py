"""Pemeriksa persiapan bot: memastikan tiap langkah pemasangan sudah benar.

Dipakai SEBELUM menjalankan sapuan pertama. Tujuannya supaya kalau ada yang
kurang, pesannya menyebut langkah mana yang harus diperbaiki — bukan sekadar
"akses ditolak" yang tidak bisa ditindaklanjuti orang non-teknis.

Semuanya hanya MEMBACA. Perintah ini tidak menulis apa pun ke Drive.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

LULUS = "OK"
GAGAL = "BELUM"


@dataclass
class Hasil:
    nama: str
    keadaan: str
    pesan: str
    perbaikan: str = ""

    @property
    def lulus(self) -> bool:
        return self.keadaan == LULUS


def _kredensial(berkas: Path) -> tuple[Hasil, Optional[str]]:
    if not berkas.exists():
        return Hasil(
            "Berkas kunci bot", GAGAL, f"tidak ada di {berkas}",
            "Langkah 4: unduh kunci JSON, ganti namanya jadi kredensial_bot.json, "
            "taruh di folder config/",
        ), None
    try:
        d = json.loads(berkas.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return Hasil("Berkas kunci bot", GAGAL, f"tidak terbaca: {e}",
                     "Unduh ulang kuncinya, jangan dibuka/disunting di Notepad"), None
    email = d.get("client_email")
    if not email:
        return Hasil("Berkas kunci bot", GAGAL, "bukan kunci akun layanan",
                     "Pastikan memilih JSON pada ADD KEY, bukan berkas lain"), None
    return Hasil("Berkas kunci bot", LULUS, f"terbaca, bot = {email}"), email


def periksa(pengaturan, buat_sambungan=None) -> list[Hasil]:
    """Periksa semua persiapan. `buat_sambungan` hanya untuk keperluan tes."""
    hasil: list[Hasil] = []
    h, email = _kredensial(pengaturan.berkas_kredensial)
    hasil.append(h)
    if not email:
        return hasil

    try:
        if buat_sambungan is None:
            from .google import Sambungan
            buat_sambungan = Sambungan
        sambung = buat_sambungan(pengaturan.berkas_kredensial)
    except Exception as e:
        hasil.append(Hasil("Sambungan ke Google", GAGAL, str(e),
                           "Langkah 2: pastikan Google Drive API dan Google "
                           "Sheets API sudah di-ENABLE di proyeknya"))
        return hasil
    hasil.append(Hasil("Sambungan ke Google", LULUS, "berhasil"))

    # ---- folder order sheet: bot harus bisa MEMBACA ---------------------
    for f in pengaturan.folder:
        nama = f.get("nama") or f.get("id", "")
        id_folder = f.get("id", "")
        if not id_folder:
            continue
        try:
            isi = sambung.isi_folder(id_folder)
        except Exception as e:
            hasil.append(Hasil(
                f"Folder '{nama}'", GAGAL, f"tidak bisa dibaca: {e}",
                f"Langkah 6: Share folder ini ke {email} sebagai Viewer. "
                "Yang men-Share harus pemilik order sheet.",
            ))
            continue
        lembar = [x for x in isi
                  if x.mime == "application/vnd.google-apps.spreadsheet"]
        if not lembar:
            hasil.append(Hasil(
                f"Folder '{nama}'", GAGAL, "terbaca tapi tidak ada spreadsheet",
                "Periksa apakah ID foldernya benar di config/bot.yaml",
            ))
        else:
            hasil.append(Hasil(f"Folder '{nama}'", LULUS,
                               f"{len(lembar)} order sheet terbaca"))

    # ---- folder tujuan: bot harus bisa MENULIS -------------------------
    tujuan = [
        ("Folder laporan", pengaturan.folder_laporan_id, "folder_laporan_id"),
        ("Folder dokumen", pengaturan.folder_dokumen_id, "folder_dokumen_id"),
    ]
    for nama, id_folder, kunci in tujuan:
        if not id_folder:
            hasil.append(Hasil(nama, GAGAL, "belum diisi",
                               f"Isi {kunci} di config/bot.yaml"))
            continue
        try:
            sambung.isi_folder(id_folder)
        except Exception as e:
            hasil.append(Hasil(
                nama, GAGAL, f"tidak bisa dibaca: {e}",
                f"Share folder ini ke {email} sebagai EDITOR (bukan Viewer, "
                "karena bot menaruh berkas di sini)",
            ))
        else:
            hasil.append(Hasil(nama, LULUS, "terbaca"))

    # ---- sheet OTOMATISASI --------------------------------------------
    if pengaturan.sheet_otomatisasi_id:
        try:
            tab = sambung.nama_tab(pengaturan.sheet_otomatisasi_id)
        except Exception as e:
            hasil.append(Hasil(
                "Sheet OTOMATISASI", GAGAL, f"tidak bisa dibaca: {e}",
                f"Share sheet OTOMATISASI ke {email} sebagai Editor",
            ))
        else:
            hasil.append(Hasil("Sheet OTOMATISASI", LULUS, f"{len(tab)} tab terbaca"))

    return hasil


def cetak(hasil: list[Hasil], tulis=print) -> bool:
    """Tampilkan hasil pemeriksaan. Kembalikan True kalau semuanya lulus."""
    lebar = max((len(h.nama) for h in hasil), default=10)
    tulis("\nPEMERIKSAAN PERSIAPAN BOT\n" + "-" * (lebar + 40))
    for h in hasil:
        tulis(f"  [{h.keadaan:<5}] {h.nama:<{lebar}}  {h.pesan}")
    belum = [h for h in hasil if not h.lulus]
    if not belum:
        tulis("\nSemua siap. Bot bisa dijalankan: python3 jalankan.py sapu\n")
        return True
    tulis(f"\nMASIH ADA {len(belum)} HAL YANG PERLU DIBERESKAN:\n")
    for i, h in enumerate(belum, start=1):
        tulis(f"  {i}. {h.nama}: {h.perbaikan}")
    tulis("")
    return False
