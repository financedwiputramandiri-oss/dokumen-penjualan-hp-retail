"""Bot penyapu: satu kali jalan = satu kali sapuan.

Urutannya:
  1. Daftar semua order sheet di folder Drive
  2. Unduh masing-masing sebagai .xlsx
  3. Baca semua tab PO, hitung nilainya
  4. Bandingkan dengan keadaan sapuan sebelumnya -> cari perubahan
  5. Buat draf dokumen untuk PO yang ATO-nya sudah terisi
  6. Tulis laporan, taruh ke Google Drive

Dijalankan tiap 12 jam lewat penjadwal (cron / Task Scheduler).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import yaml

from ..konfigurasi import AKAR, Konfigurasi
from ..model import Order
from ..nilai_bersih import tentukan_nett
from ..pemindai import baca_master_harga, baca_order_sheet
from ..rekonsiliasi import periksa_order
from .google import Sambungan
from .kondisi import Kondisi, sidik_dari_order
from .laporan_sapu import tulis as tulis_laporan
from .pantau import GENTING, Perubahan, bandingkan
from .tulis_sheet import PenulisSheet


@dataclass
class Pengaturan:
    folder: list[dict]
    folder_laporan_id: str
    nama_folder_laporan: str
    sheet_otomatisasi_id: str
    buat_draf: bool
    pantau_perubahan: bool
    pantau_rumus: bool
    hanya_hari: int
    berkas_kredensial: Path
    berkas_kondisi: Path
    folder_unduhan: Path

    @classmethod
    def muat(cls, berkas: Path | None = None) -> "Pengaturan":
        berkas = berkas or (AKAR / "config" / "bot.yaml")
        d = yaml.safe_load(berkas.read_text(encoding="utf-8")) or {}
        return cls(
            folder=list(d.get("folder_order_sheet") or []),
            folder_laporan_id=(d.get("folder_laporan_id") or "").strip(),
            nama_folder_laporan=d.get("nama_folder_laporan", "LAPORAN BOT ORDER SHEET"),
            sheet_otomatisasi_id=(d.get("sheet_otomatisasi_id") or "").strip(),
            buat_draf=bool(d.get("buat_draf_dokumen", True)),
            pantau_perubahan=bool(d.get("pantau_perubahan", True)),
            pantau_rumus=bool(d.get("pantau_rumus", True)),
            hanya_hari=int(d.get("hanya_yang_berubah_hari", 0)),
            berkas_kredensial=AKAR / d.get("berkas_kredensial", "config/kredensial_bot.json"),
            berkas_kondisi=AKAR / d.get("berkas_kondisi", "data/kondisi_sapu.json"),
            folder_unduhan=AKAR / d.get("folder_unduhan", "data/arsip"),
        )


@dataclass
class HasilSapuan:
    perubahan: list[Perubahan]
    diperiksa: list[tuple[str, str, int]]
    draf: list[str]
    masalah: list[str]
    berkas_laporan: Optional[Path] = None
    id_laporan_drive: Optional[str] = None

    @property
    def genting(self) -> list[Perubahan]:
        return [p for p in self.perubahan if p.tingkat == GENTING]


def _perlu_ditarik(diubah_iso: str, hanya_hari: int) -> bool:
    if hanya_hari <= 0 or not diubah_iso:
        return True
    try:
        t = datetime.fromisoformat(diubah_iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    return t >= datetime.now(timezone.utc) - timedelta(days=hanya_hari)


def sapu(
    pengaturan: Pengaturan | None = None,
    konfigurasi: Konfigurasi | None = None,
    cetak=print,
) -> HasilSapuan:
    p = pengaturan or Pengaturan.muat()
    cfg = konfigurasi or Konfigurasi.muat()
    sambung = Sambungan(p.berkas_kredensial)
    cetak(f"Bot: {sambung.email_bot}")

    kondisi = Kondisi.muat(p.berkas_kondisi)
    perubahan: list[Perubahan] = []
    diperiksa: list[tuple[str, str, int]] = []
    draf: list[str] = []
    masalah: list[str] = []
    rekaman: list[dict] = []   # untuk tab BOT_DAFTAR_PO di sheet OTOMATISASI

    for f in p.folder:
        id_folder, nama_folder = f.get("id", ""), f.get("nama", f.get("id", ""))
        if not id_folder:
            continue
        cetak(f"\nFolder: {nama_folder}")
        try:
            isi = sambung.isi_folder(id_folder)
        except Exception as e:
            masalah.append(f"Folder '{nama_folder}' tidak bisa dibaca: {e}")
            cetak(f"  GAGAL dibaca: {e}")
            continue

        lembar = [x for x in isi if x.mime == "application/vnd.google-apps.spreadsheet"]
        for berkas in sorted(lembar, key=lambda x: x.nama):
            if not _perlu_ditarik(berkas.diubah, p.hanya_hari):
                continue
            aman = "".join(c if c.isalnum() or c in " -_." else "_" for c in berkas.nama)
            tujuan = p.folder_unduhan / f"{aman}.xlsx"
            cetak(f"  menarik: {berkas.nama[:58]}")
            if sambung.unduh_sebagai_xlsx(berkas.id, tujuan) is None:
                masalah.append(
                    f"'{berkas.nama}' tidak bisa diunduh sebagai Excel "
                    "(biasanya karena berkasnya terlalu besar). Tab PO-nya dilewati."
                )
                cetak("    GAGAL diunduh (berkas terlalu besar?)")
                continue

            # Nama tab yang LENGKAP diambil lewat Sheets API, bukan dari .xlsx,
            # karena ekspor Excel memotong nama tab di 31 huruf.
            nama_tab_asli: dict[str, str] = {}
            try:
                for judul in sambung.nama_tab(berkas.id):
                    nama_tab_asli[judul[:31]] = judul
            except Exception:
                pass

            try:
                orders = baca_order_sheet(tujuan, cfg.customer)
                master = baca_master_harga(tujuan)
            except Exception as e:
                masalah.append(f"'{berkas.nama}' gagal dibaca: {e}")
                continue
            diperiksa.append((berkas.nama, berkas.id, len(orders)))

            for order in orders:
                tab_penuh = nama_tab_asli.get(order.nama_tab, order.nama_tab)
                cust = cfg.customer.cari(tab_penuh)
                keputusan = tentukan_nett(order, cust)

                rumus = None
                if p.pantau_perubahan and p.pantau_rumus:
                    try:
                        rumus = sambung.nilai_tab(berkas.id, tab_penuh, rumus=True)
                    except Exception:
                        rumus = None

                baru = sidik_dari_order(berkas.id, berkas.nama, tab_penuh,
                                        order, keputusan, rumus)
                if p.pantau_perubahan:
                    lama = kondisi.ambil(baru.kunci)
                    perubahan.extend(bandingkan(lama, baru))
                kondisi.pasang(baru)

                pt = cfg.perusahaan.untuk(cust)
                siap, keterangan = False, "ATO belum terisi"
                if order.qty > 0:
                    hr = periksa_order(order, keputusan, cfg.pengaturan, master, cust)
                    if hr.lolos:
                        siap, keterangan = True, "angka cocok dengan order sheet"
                        if p.buat_draf:
                            draf.append(f"{berkas.nama} / {tab_penuh}")
                    else:
                        keterangan = "angka belum cocok: " + ", ".join(
                            x.nama for x in hr.yang_gagal
                        )
                        masalah.append(f"'{tab_penuh}' {keterangan}.")

                rekaman.append({
                    "sumber": berkas.nama, "tab": tab_penuh,
                    "customer": cust.kunci if cust else "(belum terdaftar)",
                    "tanggal": order.tanggal_po.isoformat() if order.tanggal_po else "",
                    "blok": len(order.blok), "baris": order.jumlah_baris,
                    "qty": order.qty, "kotor": order.nilai_kotor,
                    "cara_bayar": keputusan.cara_bayar, "nett": keputusan.nett_total,
                    "perusahaan": pt.nama, "kena_ppn": pt.kenakan_ppn,
                    "siap": siap, "keterangan": keterangan,
                })

    kondisi.simpan(p.berkas_kondisi)

    waktu = datetime.now()
    nama_laporan = f"LAPORAN_SAPUAN_{waktu:%Y%m%d_%H%M}.xlsx"
    berkas_laporan = AKAR / "keluaran" / "sapuan" / nama_laporan
    tulis_laporan(berkas_laporan, perubahan, diperiksa, draf, masalah, waktu)

    id_drive = None
    genting = [x for x in perubahan if x.tingkat == GENTING]
    induk = p.folder_laporan_id
    if induk:
        folder_id = sambung.buat_folder_kalau_belum_ada(p.nama_folder_laporan, induk) or induk
        id_drive = sambung.unggah_laporan(berkas_laporan, folder_id)
        if id_drive is None:
            masalah.append("Laporan gagal diunggah ke Google Drive.")

    # ---- tulis ke sheet OTOMATISASI, hanya tab berawalan BOT_ -----------
    if p.sheet_otomatisasi_id:
        try:
            penulis = PenulisSheet(sambung, p.sheet_otomatisasi_id)
            penulis.muat_daftar_tab()
            penulis.tulis_daftar_po(rekaman)
            penulis.tulis_perubahan(perubahan)
            tautan = (
                f"https://drive.google.com/file/d/{id_drive}/view" if id_drive else ""
            )
            penulis.tulis_status(
                waktu, len(diperiksa), sum(n for _, _, n in diperiksa),
                len(genting), len(draf), tautan,
            )
            cetak("Sheet OTOMATISASI diperbarui (tab BOT_DAFTAR_PO, BOT_PERUBAHAN, BOT_STATUS).")
        except Exception as e:
            masalah.append(f"Sheet OTOMATISASI tidak bisa diperbarui: {e}")
            cetak(f"Sheet OTOMATISASI gagal diperbarui: {e}")

    hasil = HasilSapuan(perubahan, diperiksa, draf, masalah, berkas_laporan, id_drive)

    cetak(f"\nSelesai. {len(diperiksa)} order sheet, "
          f"{sum(n for _, _, n in diperiksa)} tab PO diperiksa.")
    if genting:
        cetak(f"ADA {len(genting)} PERUBAHAN PENTING:")
        for x in genting[:15]:
            cetak(f"  - [{x.jenis}] {x.tab} ({x.nama_sheet[:40]}): {x.keterangan}")
        if len(genting) > 15:
            cetak(f"  ... dan {len(genting) - 15} lagi, lihat laporannya.")
    else:
        cetak("Tidak ada perubahan penting pada PO lama.")
    cetak(f"Laporan: {berkas_laporan}")
    if id_drive:
        cetak(f"Laporan di Drive: https://drive.google.com/file/d/{id_drive}/view")
    return hasil
