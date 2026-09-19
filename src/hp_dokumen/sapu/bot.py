"""Bot penyapu: satu kali jalan = satu kali sapuan.

Urutannya:
  1. Daftar semua order sheet di folder Drive
  2. Tarik isi tabnya lewat Sheets API (tidak mengunduh berkas)
  3. Baca semua tab PO, hitung nilainya
  4. Bandingkan dengan keadaan sapuan sebelumnya -> cari perubahan
  5. Buat draf dokumen untuk PO yang ATO-nya sudah terisi, dan BUAT ULANG
     draf yang angkanya direvisi sejak sapuan sebelumnya
  6. Tulis laporan, taruh ke Google Drive

Dijalankan tiap 12 jam lewat penjadwal (cron / Task Scheduler).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import yaml

from ..berkas_dokumen import nama_aman
from ..konfigurasi import AKAR, Konfigurasi
from ..model import Order
from ..nilai_bersih import tentukan_nett
from ..pemindai import baca_buku, master_harga_dari_buku
from ..rekonsiliasi import periksa_order
from .bulan import cocok_bulan, folder_bisa_dilewati, nama_bulan
from .draf import HasilDraf, buat_draf, perlu_draf
from .unggah import PengunggahDokumen
from .google import Sambungan
from .kondisi import (Kondisi, kondisi_dibagi, peringatan_pindah_komputer,
                      salinan_bentrok, sidik_dari_order)
from .kunci_bersama import KunciBersama, kalimat_ditolak
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
    lewati_yang_tidak_berubah: bool = True
    folder_draf: Path = AKAR / "keluaran" / "draf"
    draf_pdf: bool = False
    folder_dokumen_id: str = ""
    pakai_kunci_bersama: bool = True

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
            lewati_yang_tidak_berubah=bool(d.get("lewati_yang_tidak_berubah", True)),
            folder_draf=AKAR / d.get("folder_draf", "keluaran/draf"),
            draf_pdf=bool(d.get("draf_pdf", False)),
            folder_dokumen_id=(d.get("folder_dokumen_id") or "").strip(),
            pakai_kunci_bersama=bool(d.get("pakai_kunci_bersama", True)),
        )


@dataclass
class HasilSapuan:
    perubahan: list[Perubahan]
    diperiksa: list[tuple[str, str, int]]
    draf: list[HasilDraf]
    masalah: list[str]
    berkas_laporan: Optional[Path] = None
    id_laporan_drive: Optional[str] = None
    dilewati: list[str] = field(default_factory=list)
    tab_ditarik: int = 0
    dijalankan: bool = True      # False = komputer lain sedang menyapu
    alasan_batal: str = ""

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
    saring_bulan: tuple[int, int] | None = None,
    paksa: bool = False,
    pakai_kunci: bool | None = None,
) -> HasilSapuan:
    """Satu kali sapuan.

    `saring_bulan` berisi (bulan, tahun). Kalau diisi, HANYA order sheet
    bulan itu yang dibaca — dipakai untuk sapuan mendadak yang harus cepat.
    `paksa` mengabaikan pelewatan "tidak berubah sejak sapuan lalu".
    """
    p = pengaturan or Pengaturan.muat()
    cfg = konfigurasi or Konfigurasi.muat()
    sambung = Sambungan(p.berkas_kredensial)
    cetak(f"Bot: {sambung.email_bot}")

    if saring_bulan:
        cetak(f"Hanya order sheet {nama_bulan(saring_bulan[0])} {saring_bulan[1]}.")

    # ---- kunci antar-KOMPUTER ------------------------------------------
    # Kunci di jadwal/sapu.bat hanya menahan dua sapuan di satu komputer.
    # Begitu bot dipasang di laptop DAN komputer kantor, keduanya bangun
    # pada jam yang sama. Kunci ini ditaruh di sheet OTOMATISASI supaya
    # semua komputer melihatnya pada detik yang sama.
    kunci = None
    if pakai_kunci is None:
        pakai_kunci = p.pakai_kunci_bersama
    if pakai_kunci and p.sheet_otomatisasi_id:
        kunci = KunciBersama(sambung, p.sheet_otomatisasi_id)
        ket = (f"sapuan {nama_bulan(saring_bulan[0])} {saring_bulan[1]}"
               if saring_bulan else "sapuan penuh")
        try:
            dapat = kunci.ambil(ket)
        except Exception as e:
            # Kunci yang tidak bisa dibaca TIDAK boleh menghentikan sapuan —
            # lebih baik menyapu tanpa kunci daripada tidak menyapu sama
            # sekali karena sheetnya sedang tidak bisa dihubungi.
            cetak(f"Kunci bersama tidak bisa dipakai ({e}); sapuan diteruskan.")
            kunci = None
        else:
            if not dapat:
                pesan = kalimat_ditolak(kunci.pemegang_lain)
                cetak(pesan)
                return HasilSapuan([], [], [], [pesan], dijalankan=False,
                                   alasan_batal=pesan)
            cetak(f"Kunci sapuan dipegang komputer ini ({kunci.perangkat}).")
    try:
        return _sapu(p, cfg, sambung, cetak, saring_bulan, paksa)
    finally:
        if kunci:
            try:
                kunci.lepas()
            except Exception as e:
                cetak(f"Kunci sapuan gagal dilepas: {e}")


def _sapu(p, cfg, sambung, cetak, saring_bulan, paksa) -> HasilSapuan:
    pengunggah = (PengunggahDokumen(sambung, p.folder_dokumen_id)
                  if p.folder_dokumen_id else None)

    kondisi = Kondisi.muat(p.berkas_kondisi)
    perubahan: list[Perubahan] = []
    diperiksa: list[tuple[str, str, int]] = []
    draf: list[HasilDraf] = []
    masalah: list[str] = []
    dibagi = kondisi_dibagi(p.berkas_kondisi, p.folder_draf)
    pindah = peringatan_pindah_komputer(kondisi, dibagi)
    if pindah:
        masalah.append(pindah)
        cetak(pindah)
    for nama_bentrok in salinan_bentrok(p.berkas_kondisi):
        # Drive menyimpan salinan bentrok diam-diam: tidak ada galat,
        # berkas aslinya tetap terbaca, dan separuh catatan sapuan ada
        # di berkas yang tidak pernah dibuka siapa pun.
        pesan_bentrok = (
            f"Google Drive membuat salinan bentrok '{nama_bentrok}' di sebelah "
            f"catatan sapuan. Itu tanda dua komputer menyapu bersamaan. "
            f"Periksa jadwalnya, lalu hapus salinan itu."
        )
        masalah.append(pesan_bentrok)
        cetak(pesan_bentrok)
    rekaman: list[dict] = []   # untuk tab BOT_DAFTAR_PO di sheet OTOMATISASI
    dilewati: list[str] = []   # spreadsheet yang tidak berubah sejak sapuan lalu
    cocok_bulan_ini: list[str] = []   # order sheet yang lolos saringan bulan
    dibaca_tab = 0             # berapa tab yang benar-benar ditarik isinya

    for f in p.folder:
        id_folder, nama_folder = f.get("id", ""), f.get("nama", f.get("id", ""))
        if not id_folder:
            continue
        if saring_bulan and folder_bisa_dilewati(nama_folder, saring_bulan[1]):
            cetak(f"\nFolder: {nama_folder} — dilewati, bukan tahun "
                  f"{saring_bulan[1]}")
            continue
        cetak(f"\nFolder: {nama_folder}")
        try:
            isi = sambung.isi_folder(id_folder)
        except Exception as e:
            masalah.append(f"Folder '{nama_folder}' tidak bisa dibaca: {e}")
            cetak(f"  GAGAL dibaca: {e}")
            continue

        lembar = [x for x in isi if x.mime == "application/vnd.google-apps.spreadsheet"]
        if saring_bulan:
            sebelum = len(lembar)
            lembar = [x for x in lembar
                      if cocok_bulan(x.nama, saring_bulan[0], saring_bulan[1],
                                     nama_folder)]
            cocok_bulan_ini.extend(x.nama for x in lembar)
            cetak(f"  {len(lembar)} dari {sebelum} order sheet cocok bulannya")
        for berkas in sorted(lembar, key=lambda x: x.nama):
            if not _perlu_ditarik(berkas.diubah, p.hanya_hari):
                continue

            # Lewati kalau spreadsheet ini tidak berubah sejak sapuan lalu.
            # Waktu ubah datang dari Drive dan tidak memerlukan pembacaan isi,
            # jadi order sheet lama yang sudah selesai tidak ditarik berulang.
            if (p.lewati_yang_tidak_berubah and not paksa
                    and not kondisi.berubah_sejak_sapuan_lalu(
                        berkas.id, berkas.diubah)):
                dilewati.append(berkas.nama)
                cetak(f"  lewati (tidak berubah): {berkas.nama[:52]}")
                continue

            cetak(f"  membaca: {berkas.nama[:56]}")
            try:
                semua_tab = sambung.daftar_tab(berkas.id)
            except Exception as e:
                masalah.append(f"'{berkas.nama}' daftar tabnya tidak bisa dibaca: {e}")
                cetak(f"    GAGAL: {e}")
                continue

            judul_semua = [x["judul"] for x in semua_tab]
            judul_po = [
                j for j in judul_semua
                if j.upper().strip().startswith(("PO ", "(DELIVERY", "PACKING LIST"))
            ]
            judul_diambil = judul_po + [j for j in judul_semua if j.strip() == "Harga Retail"]
            if not judul_po:
                cetak("    tidak ada tab PO, dilewati")
                kondisi.catat_sheet(berkas.id, berkas.nama, berkas.diubah, 0)
                continue

            # Satu-dua panggilan batchGet untuk semua tab sekaligus.
            try:
                buku = sambung.buku_dari_tab(berkas.id, judul_diambil)
            except Exception as e:
                masalah.append(f"'{berkas.nama}' isinya tidak bisa ditarik: {e}")
                cetak(f"    GAGAL menarik isi: {e}")
                continue

            try:
                orders = baca_buku(buku, cfg.customer)
                master = master_harga_dari_buku(buku)
            except Exception as e:
                masalah.append(f"'{berkas.nama}' gagal diolah: {e}")
                continue
            diperiksa.append((berkas.nama, berkas.id, len(orders)))
            dibaca_tab += len(judul_diambil)

            # Rumus hanya ditarik kalau pemantauan rumus dinyalakan, dan
            # hanya untuk tab PO — bukan seluruh spreadsheet.
            rumus_per_tab: dict[str, list] = {}
            if p.pantau_perubahan and p.pantau_rumus:
                try:
                    rumus_per_tab = sambung.ambil_tab(
                        berkas.id, [o.nama_tab for o in orders], rumus=True
                    )
                    dibaca_tab += len(rumus_per_tab)
                except Exception as e:
                    masalah.append(
                        f"'{berkas.nama}' rumusnya tidak bisa dibaca, "
                        f"pemantauan rumus dilewati: {e}"
                    )

            for order in orders:
                tab_penuh = order.nama_tab      # sudah lengkap dari Sheets API
                cust = cfg.customer.cari(tab_penuh)
                keputusan = tentukan_nett(order, cust)

                baru_sidik = sidik_dari_order(
                    berkas.id, berkas.nama, tab_penuh, order, keputusan,
                    rumus_per_tab.get(tab_penuh),
                )
                # Sidik lama selalu diambil: bukan hanya untuk alarm, tapi juga
                # untuk tahu apakah draf dokumennya perlu dibuat ulang.
                lama_sidik = kondisi.ambil(baru_sidik.kunci)
                if p.pantau_perubahan:
                    perubahan.extend(bandingkan(lama_sidik, baru_sidik))

                pt = cfg.perusahaan.untuk(cust)
                siap, keterangan = False, "ATO belum terisi"
                if order.qty > 0:
                    hr = periksa_order(order, keputusan, cfg.pengaturan, master, cust)
                    if hr.lolos:
                        siap, keterangan = True, "angka cocok dengan order sheet"
                        if p.buat_draf:
                            # Dokumen HANYA dibuat kalau angkanya sudah cocok
                            # dengan order sheet. Aturan yang sama dipakai
                            # perintah manual: lebih baik tidak terbit daripada
                            # terbit salah.
                            folder_po = (p.folder_draf / nama_aman(berkas.nama)
                                         / nama_aman(tab_penuh))
                            alasan = perlu_draf(lama_sidik, baru_sidik, folder_po)
                            if alasan:
                                try:
                                    hd = buat_draf(
                                        cfg, order, keputusan, lama_sidik,
                                        baru_sidik, alasan, p.folder_draf,
                                        pdf=p.draf_pdf,
                                    )
                                    draf.append(hd)
                                    cetak(f"    draf {alasan}: {hd.ringkas()}")
                                    if pengunggah:
                                        hu = pengunggah.unggah(hd, berkas.nama)
                                        cetak(f"      -> {hu.jumlah} berkas naik ke Drive")
                                        if hu.gagal:
                                            # Sebab kegagalan pertama langsung
                                            # ditampilkan. Kalau hanya dicatat
                                            # ke laporan, orang melihat "0
                                            # berkas naik" berulang-ulang tanpa
                                            # tahu harus berbuat apa.
                                            cetak(f"      GAGAL: {hu.gagal[0]}")
                                            if len(hu.gagal) > 1:
                                                cetak(f"      (dan {len(hu.gagal) - 1} berkas lain, sebab sama)")
                                        masalah.extend(
                                            f"'{tab_penuh}' {x}" for x in hu.gagal
                                        )
                                except Exception as e:
                                    masalah.append(
                                        f"'{tab_penuh}' drafnya gagal dibuat: {e}"
                                    )
                    else:
                        keterangan = "angka belum cocok: " + ", ".join(
                            x.nama for x in hr.yang_gagal
                        )
                        masalah.append(f"'{tab_penuh}' {keterangan}.")

                # Sidik disimpan SETELAH draf dibuat. Kalau pembuatan draf
                # gagal, sidik lama tetap tersimpan sehingga sapuan berikutnya
                # mencobanya lagi, bukan menganggapnya sudah beres.
                kondisi.pasang(baru_sidik)

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

            kondisi.catat_sheet(berkas.id, berkas.nama, berkas.diubah, len(judul_po))

    if saring_bulan and not cocok_bulan_ini:
        pesan = (
            f"TIDAK ADA order sheet bernama bulan "
            f"{nama_bulan(saring_bulan[0])} {saring_bulan[1]} di folder Drive. "
            f"Sapuan bulan ini tidak menghasilkan apa-apa. Periksa nama "
            f"berkasnya di Drive — bot mencocokkan dari NAMA order sheet, "
            f"jadi namanya harus memuat nama bulannya."
        )
        masalah.append(pesan)
        cetak("\n" + pesan)

    kondisi.simpan(p.berkas_kondisi)

    waktu = datetime.now()
    nama_laporan = f"LAPORAN_SAPUAN_{waktu:%Y%m%d_%H%M}.xlsx"
    berkas_laporan = AKAR / "keluaran" / "sapuan" / nama_laporan
    tulis_laporan(berkas_laporan, perubahan, diperiksa,
                  [d.ringkas() for d in draf], masalah, waktu,
                  dilewati, dibaca_tab)

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

    hasil = HasilSapuan(perubahan, diperiksa, draf, masalah, berkas_laporan, id_drive,
                        dilewati, dibaca_tab)

    if saring_bulan:
        cetak(f"\nSapuan CEPAT: {nama_bulan(saring_bulan[0])} {saring_bulan[1]} saja. "
              f"Order sheet bulan lain sengaja tidak dibuka.")
    cetak(f"Selesai. {len(diperiksa)} order sheet dibaca "
          f"({sum(n for _, _, n in diperiksa)} tab PO, {dibaca_tab} tab ditarik), "
          f"{len(dilewati)} order sheet dilewati karena tidak berubah.")
    if saring_bulan and cocok_bulan_ini and not diperiksa and dilewati:
        cetak("Order sheet bulan ini TIDAK berubah sejak sapuan terakhir, jadi "
              "dokumennya sudah yang terbaru. Kalau tetap ingin dibuat ulang, "
              "jalankan dengan --paksa.")
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
