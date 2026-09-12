"""Perintah-perintah yang dijalankan lewat jalankan.py.

Sengaja dibuat sesedikit mungkin dan berbahasa Indonesia:

    python3 jalankan.py daftar
    python3 jalankan.py periksa
    python3 jalankan.py buat "Panda"
    python3 jalankan.py buat-semua
    python3 jalankan.py rekap
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .berkas_dokumen import buat_berkas, nama_aman
from .konfigurasi import Konfigurasi, AKAR
from .laporan import cetak_rinci, cetak_ringkas, tulis_laporan_pencocokan, tulis_rekap_penjualan
from .model import Order
from .nilai_bersih import tentukan_nett
from .pemindai import baca_master_harga, baca_order_sheet
from .riwayat import telusuri_berkas
from .db_customer import bangun as bangun_customer, dugaan_nama_sama
from .laporan_customer import tulis as tulis_db_customer
from .rekonsiliasi import HasilRekonsiliasi, periksa_order

BERKAS_BAWAAN = AKAR / "data" / "order_sheet.xlsx"
FOLDER_KELUARAN = AKAR / "keluaran"


def _cari_berkas(diberikan: str | None) -> Path:
    if diberikan:
        p = Path(diberikan)
        if not p.exists():
            raise SystemExit(f"Berkas tidak ditemukan: {p}")
        return p
    if BERKAS_BAWAAN.exists():
        return BERKAS_BAWAAN
    lain = sorted((AKAR / "data").glob("*.xlsx"))
    if lain:
        return lain[0]
    raise SystemExit(
        "Order sheet belum ada.\n"
        "Cara mengambilnya:\n"
        "  1. Buka order sheet di Google Spreadsheet\n"
        "  2. Menu File > Download > Microsoft Excel (.xlsx)\n"
        f"  3. Simpan berkasnya sebagai: {BERKAS_BAWAAN}\n"
    )


def _aman(teks: str) -> str:
    """Ubah nama tab jadi nama berkas yang aman."""
    return nama_aman(teks)


def _muat(args) -> tuple[Konfigurasi, list[Order], dict, Path]:
    cfg = Konfigurasi.muat()
    berkas = _cari_berkas(getattr(args, "berkas", None))
    orders = baca_order_sheet(berkas, cfg.customer, tahun_bawaan=args.tahun)
    master = baca_master_harga(berkas)
    return cfg, orders, master, berkas


def _periksa_semua(cfg, orders, master) -> list[HasilRekonsiliasi]:
    hasil = []
    for o in orders:
        cust = cfg.customer.cari(o.nama_tab)
        kep = tentukan_nett(o, cust)
        hasil.append(periksa_order(o, kep, cfg.pengaturan, master, cust))
    return hasil


def _saring(orders: list[Order], kata: str | None) -> list[Order]:
    if not kata:
        return orders
    k = kata.strip().lower()
    cocok = [o for o in orders if k in o.nama_tab.lower() or k in o.customer_kunci.lower()]
    if not cocok:
        raise SystemExit(
            f"Tidak ada PO yang cocok dengan '{kata}'.\n"
            "Jalankan dulu: python3 jalankan.py daftar"
        )
    return cocok


def _tampilkan_peringatan_umum(cfg) -> None:
    if cfg.peringatan:
        print("\nPERLU DIPERHATIKAN (pengaturan):")
        for w in cfg.peringatan:
            print(f"  - {w}")


# ------------------------------------------------------------- perintah
def perintah_daftar(args) -> int:
    cfg, orders, master, berkas = _muat(args)
    print(f"\nOrder sheet: {berkas}")
    print(f"Jumlah PO berisi data: {len(orders)}\n")
    print(f"{'NO':>3}  {'TAB / PO':<34}{'CUSTOMER':<22}{'BLOK':>5}{'BARIS':>7}{'QTY':>8}")
    print("-" * 82)
    for i, o in enumerate(orders, start=1):
        print(f"{i:>3}  {o.nama_tab[:33]:<34}{(o.customer_kunci or '(belum terdaftar)')[:21]:<22}"
              f"{len(o.blok):>5}{o.jumlah_baris:>7}{o.qty:>8}")
    print()
    return 0


def perintah_periksa(args) -> int:
    cfg, orders, master, berkas = _muat(args)
    orders = _saring(orders, args.po)
    hasil = _periksa_semua(cfg, orders, master)
    cetak_ringkas(hasil)
    if args.rinci or args.po:
        for h in hasil:
            cetak_rinci(h)
    _tampilkan_peringatan_umum(cfg)

    gagal = [h for h in hasil if not h.lolos]
    out = FOLDER_KELUARAN / "LAPORAN_PENCOCOKAN.xlsx"
    tulis_laporan_pencocokan(hasil, out, cfg.peringatan)
    print(f"\nLaporan lengkap disimpan: {out}")
    if gagal:
        print(f"\nADA {len(gagal)} PO YANG TIDAK COCOK. Dokumen TIDAK boleh dibuat dulu.")
        return 1
    print("\nSemua PO cocok dengan angka order sheet.")
    return 0


def _nomor(cfg, urut: int, diberikan: str | None) -> str:
    if diberikan:
        return diberikan
    import yaml
    d = yaml.safe_load((AKAR / "config" / "pengaturan.yaml").read_text(encoding="utf-8")) or {}
    nd = d.get("nomor_dokumen") or {}
    if not nd.get("otomatis"):
        return "________"
    awal = int(nd.get("nomor_awal", 1))
    return f"{awal + urut:03d}{int(nd.get('bulan', 8)):02d}{int(nd.get('tahun', 26)):02d}"


def _buat_dokumen(cfg, h: HasilRekonsiliasi, urut: int, args) -> list[Path]:
    folder = FOLDER_KELUARAN / _aman(h.order.nama_tab)
    return buat_berkas(
        cfg, h.order, h.keputusan, folder,
        _nomor(cfg, urut, args.nomor),
        pdf=args.pdf, cetak=print,
    )


def perintah_buat(args) -> int:
    cfg, orders, master, berkas = _muat(args)
    orders = _saring(orders, args.po)
    hasil = _periksa_semua(cfg, orders, master)

    gagal = [h for h in hasil if not h.lolos]
    if gagal and not args.abaikan_pencocokan:
        print("\nBERHENTI. Angka hasil olahan tidak cocok dengan order sheet:\n")
        for h in gagal:
            cetak_rinci(h)
        print("\nDokumen TIDAK dibuat. Perbaiki dulu order sheetnya.")
        print("(Kalau benar-benar perlu, tambahkan --abaikan-pencocokan, tapi hasilnya tidak bisa dipercaya.)")
        return 1

    cetak_ringkas(hasil)
    print()
    semua: list[Path] = []
    for i, h in enumerate(hasil):
        print(f"Membuat dokumen: {h.order.nama_tab}")
        dibuat = _buat_dokumen(cfg, h, i, args)
        semua.extend(dibuat)
        for p in dibuat:
            print(f"  - {p.relative_to(AKAR)}")

    lap = tulis_laporan_pencocokan(hasil, FOLDER_KELUARAN / "LAPORAN_PENCOCOKAN.xlsx", cfg.peringatan)
    print(f"\nLaporan pencocokan: {lap.relative_to(AKAR)}")
    _tampilkan_peringatan_umum(cfg)
    for h in hasil:
        if h.peringatan:
            print(f"\nPERLU DIPERHATIKAN — {h.order.nama_tab}:")
            for w in h.peringatan:
                print(f"  - {w}")
    print(f"\nSelesai. {len(semua)} berkas dibuat di folder keluaran/")
    return 0


def perintah_rekap(args) -> int:
    cfg, orders, master, berkas = _muat(args)
    hasil = _periksa_semua(cfg, orders, master)
    cetak_ringkas(hasil)
    out = tulis_rekap_penjualan(hasil, FOLDER_KELUARAN / "REKAP_PENJUALAN.xlsx", cfg.pengaturan.tarif_ppn)
    print(f"\nRekap penjualan disimpan: {out.relative_to(AKAR)}")
    _tampilkan_peringatan_umum(cfg)
    return 0


def perintah_telusuri(args) -> int:
    """Telusuri semua order sheet lama -> database customer."""
    folder = Path(args.folder) if args.folder else (AKAR / "data" / "arsip")
    berkas = sorted(folder.glob("*.xlsx"))
    if not berkas:
        raise SystemExit(
            f"Tidak ada order sheet di {folder}.\n"
            "Unduh order sheet lama (File > Download > Microsoft Excel) "
            f"lalu simpan semuanya di {folder}"
        )
    print(f"Menelusuri {len(berkas)} order sheet di {folder}\n")
    semua = []
    sumber = []
    for f in berkas:
        judul = f.stem.replace("_", " ")
        c = telusuri_berkas(f, judul)
        semua.extend(c)
        sumber.append(f"{judul}  -> {len(c)} PO")
        print(f"  {len(c):>3} PO   {judul[:64]}")
    if not semua:
        raise SystemExit("Tidak ada PO yang terbaca.")

    daftar, jejak = bangun_customer(semua)
    grup = dugaan_nama_sama(daftar)
    print(f"\nRINGKASAN")
    print(f"  PO terbaca            : {len(semua)}")
    print(f"  Customer setelah digabung : {len(daftar)}")
    print(f"  Digabung otomatis (nama tab terpotong) : {len(jejak)}")
    print(f"  Grup nama yang perlu diperiksa manusia  : {len(grup)}")

    print(f"\n{'CUSTOMER':<32}{'PO':>4}{'PERIODE AKTIF':>28}{'DISKON':>8}{'BAYAR':>7}{'NETT':>16}")
    print("-" * 95)
    for c in daftar[: args.tampilkan]:
        print(f"{c.nama_tampil[:31]:<32}{c.jumlah_po:>4}{c.periode_aktif:>28}"
              f"{c.diskon_terakhir:>8.1%}{c.cara_bayar_terakhir:>7}{c.total_nett:>16,.0f}")
    if len(daftar) > args.tampilkan:
        print(f"... dan {len(daftar) - args.tampilkan} customer lagi, lihat berkas Excelnya.")

    out = tulis_db_customer(daftar, FOLDER_KELUARAN / "DATABASE_CUSTOMER.xlsx", jejak, sumber)
    print(f"\nDatabase lengkap disimpan: {out.relative_to(AKAR)}")
    print("  lembar MASTER_CUSTOMER : satu baris satu customer")
    print("  lembar RIWAYAT_PO      : satu baris satu PO, untuk penelusuran")
    print("  lembar PERIKSA_NAMA    : nama mirip yang perlu dipastikan")
    return 0


def perintah_sapu(args) -> int:
    """Satu kali sapuan: tarik order sheet dari Drive, pantau, buat draf."""
    from .sapu.bot import Pengaturan as PengaturanBot, sapu

    cfg = Konfigurasi.muat()
    p = PengaturanBot.muat()
    if args.tanpa_draf:
        p.buat_draf = False
    if args.tanpa_rumus:
        p.pantau_rumus = False
    hasil = sapu(p, cfg)
    return 1 if hasil.genting else 0


def buat_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jalankan.py",
        description="Membuat Surat Jalan, Invoice, Packing List, dan Faktur Pajak dari order sheet.",
    )
    p.add_argument("--berkas", help="Lokasi order sheet .xlsx (bawaan: data/order_sheet.xlsx)")
    p.add_argument("--tahun", type=int, default=date.today().year,
                   help="Tahun untuk tab yang namanya tanpa tahun (bawaan: tahun ini)")
    sub = p.add_subparsers(dest="perintah", required=True)

    a = sub.add_parser("daftar", help="Tampilkan semua PO di order sheet")
    a.set_defaults(fungsi=perintah_daftar)

    b = sub.add_parser("periksa", help="Cocokkan angka hasil olahan dengan order sheet")
    b.add_argument("po", nargs="?", help="Sebagian nama PO/customer, contoh: Panda")
    b.add_argument("--rinci", action="store_true", help="Tampilkan semua pemeriksaan")
    b.set_defaults(fungsi=perintah_periksa)

    c = sub.add_parser("buat", help="Buat 4 dokumen untuk satu PO")
    c.add_argument("po", help="Sebagian nama PO/customer, contoh: Panda")
    c.add_argument("--nomor", help="Nomor dokumen, contoh 0050826")
    c.add_argument("--pdf", action="store_true", help="Sekalian buat PDF")
    c.add_argument("--abaikan-pencocokan", dest="abaikan_pencocokan", action="store_true",
                   help="Tetap buat walau angka tidak cocok (tidak disarankan)")
    c.set_defaults(fungsi=perintah_buat)

    d = sub.add_parser("buat-semua", help="Buat dokumen untuk SEMUA PO")
    d.add_argument("--pdf", action="store_true", help="Sekalian buat PDF")
    d.add_argument("--nomor", help=argparse.SUPPRESS)
    d.add_argument("--abaikan-pencocokan", dest="abaikan_pencocokan", action="store_true",
                   help="Tetap buat walau angka tidak cocok (tidak disarankan)")
    d.set_defaults(fungsi=perintah_buat, po=None)

    e = sub.add_parser("rekap", help="Rekap penjualan sebulan (bahan laporan keuangan & pajak)")
    e.set_defaults(fungsi=perintah_rekap)

    g = sub.add_parser("telusuri",
                       help="Telusuri semua order sheet lama jadi database customer")
    g.add_argument("--folder", help="Folder berisi order sheet lama (bawaan: data/arsip)")
    g.add_argument("--tampilkan", type=int, default=25,
                   help="Berapa customer teratas ditampilkan di layar (bawaan 25)")
    g.set_defaults(fungsi=perintah_telusuri)

    h = sub.add_parser("sapu",
                       help="Tarik order sheet dari Google Drive, pantau perubahan (butuh bot)")
    h.add_argument("--tanpa-draf", dest="tanpa_draf", action="store_true",
                   help="Hanya memantau, tidak membuat draf dokumen")
    h.add_argument("--tanpa-rumus", dest="tanpa_rumus", action="store_true",
                   help="Jangan bandingkan rumus (lebih cepat)")
    h.set_defaults(fungsi=perintah_sapu)
    return p


def main(argv: list[str] | None = None) -> int:
    args = buat_parser().parse_args(argv)
    return args.fungsi(args)


if __name__ == "__main__":
    sys.exit(main())
