"""Membaca berkas pengaturan di folder config/."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

AKAR = Path(__file__).resolve().parents[2]
FOLDER_CONFIG = AKAR / "config"


# ---------------------------------------------------------------- customer
@dataclass
class Customer:
    kunci: str
    nama_di_dokumen: str
    alamat: str
    npwp: str
    format_invoice: str      # "per_artikel" | "per_ukuran"
    termin_hari: int
    cara_bayar_paksa: str    # "" | "TOP" | "CBD" | "COD"
    perusahaan_pemroses: str  # kode perusahaan, contoh "DPM" / "MTN"; "" = bawaan
    catatan: str

    @property
    def pecah_per_ukuran(self) -> bool:
        return self.format_invoice.strip().lower() == "per_ukuran"

    def kekurangan(self) -> list[str]:
        kurang = []
        if not self.nama_di_dokumen.strip():
            kurang.append("nama di dokumen")
        if not self.alamat.strip():
            kurang.append("alamat")
        if not self.npwp.strip():
            kurang.append("NPWP")
        return kurang


def _normal(teks: str) -> str:
    """Seragamkan teks untuk pencocokan: huruf kecil, tanpa kurung, spasi rapat."""
    teks = teks.replace("(", " ").replace(")", " ").replace("&", " & ")
    teks = re.sub(r"\s+", " ", teks)
    return teks.strip().lower()


BULAN = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
    "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11,
    "desember": 12,
}


SINGKATAN_BULAN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6,
    "jul": 7, "agu": 8, "aug": 8, "ags": 8, "sep": 9, "okt": 10, "oct": 10,
    "nov": 11, "des": 12, "dec": 12,
}


def _bulan(teks: str) -> Optional[int]:
    t = (teks or "").strip().lower()
    if t in BULAN:
        return BULAN[t]
    return SINGKATAN_BULAN.get(t[:3])


def pecah_nama_tab(nama_tab: str) -> tuple[Optional[tuple[int, int, Optional[int]]], str]:
    """Pisahkan nama tab jadi (tanggal, nama customer).

    Order sheet ditulis banyak orang, jadi bentuknya bermacam-macam:

        PO 31 Agustus - Haritsa
        PO 13 Agustus 2026 - Dunia Bayi
        PO 22 Jan Pratama Babyshop          (bulan disingkat, tanpa tanda hubung)
        PO 30 - Jojo Collection             (tanpa bulan)
        2 Feb - Yens Baby                   (tanpa kata PO)
        (Delivery 1) PO 12 Mei - Katamama   (ada awalan pengiriman)

    Semua bentuk di atas harus terbaca. Kalau polanya benar-benar tidak
    dikenali, tanggal = None dan seluruh nama tab dianggap nama customer.
    """
    sisa = re.sub(r"^\s*\(delivery\s*\d*\)\s*", "", str(nama_tab or ""), flags=re.IGNORECASE)
    sisa = sisa.strip()
    asli = sisa

    sisa = re.sub(r"^PO\b[\s.:-]*", "", sisa, flags=re.IGNORECASE).strip()

    hari = bulan = tahun = None
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]+)\s*(\d{4})?\b[\s.:-]*(.*)$", sisa)
    if m and _bulan(m.group(2)) is not None:
        hari = int(m.group(1))
        bulan = _bulan(m.group(2))
        tahun = int(m.group(3)) if m.group(3) else None
        sisa = m.group(4).strip()
    else:
        # bentuk "30 - Jojo Collection": ada tanggal tapi tanpa bulan
        m2 = re.match(r"^(\d{1,2})\s*[-–]\s*(.+)$", sisa)
        if m2:
            hari = int(m2.group(1))
            sisa = m2.group(2).strip()
        else:
            m3 = re.match(r"^[-–]\s*(.+)$", sisa)
            if m3:
                sisa = m3.group(1).strip()

    sisa = re.sub(r"^[\s.:-]+", "", sisa).strip()
    if not sisa:
        return (None, asli)
    if hari is not None and bulan is not None:
        return ((hari, bulan, tahun), sisa)
    return (None, sisa)


class DaftarCustomer:
    def __init__(self, baris: list[Customer]):
        self.semua = baris
        self._index = {_normal(c.kunci): c for c in baris}

    @classmethod
    def muat(cls, berkas: Path | None = None) -> "DaftarCustomer":
        berkas = berkas or (FOLDER_CONFIG / "customer.csv")
        hasil: list[Customer] = []
        with open(berkas, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if not (row.get("kunci_tab") or "").strip():
                    continue
                try:
                    termin = int((row.get("termin_hari") or "").strip() or 30)
                except ValueError:
                    termin = 30
                hasil.append(
                    Customer(
                        kunci=row["kunci_tab"].strip(),
                        nama_di_dokumen=(row.get("nama_di_dokumen") or "").strip(),
                        alamat=(row.get("alamat") or "").strip(),
                        npwp=(row.get("npwp") or "").strip(),
                        format_invoice=(row.get("format_invoice") or "per_artikel").strip(),
                        termin_hari=termin,
                        cara_bayar_paksa=(row.get("cara_bayar_paksa") or "").strip().upper(),
                        perusahaan_pemroses=(row.get("perusahaan_pemroses") or "").strip().upper(),
                        catatan=(row.get("catatan") or "").strip(),
                    )
                )
        return cls(hasil)

    def cari(self, nama_tab: str) -> Optional[Customer]:
        """Cocokkan nama tab ke master customer.

        Tahan terhadap dua hal:
          - tanda kurung pada nama tab, contoh 'Katamama (Tapos)'
          - nama tab yang terpotong 31 huruf oleh ekspor Excel,
            contoh 'PO 31 Agustus - Baby Wise (Sura'
        """
        _, sisa = pecah_nama_tab(nama_tab)
        kunci = _normal(sisa)
        if not kunci:
            return None
        # 1. sama persis
        if kunci in self._index:
            return self._index[kunci]
        # 2. salah satu awalan dari yang lain (menangani pemotongan 31 huruf);
        #    ambil kecocokan terpanjang supaya 'Baby Wise Sura' tidak jatuh ke 'Baby Wise'
        kandidat = [
            (len(k), c)
            for k, c in self._index.items()
            if k.startswith(kunci) or kunci.startswith(k)
        ]
        if kandidat:
            return max(kandidat, key=lambda x: x[0])[1]
        return None


# ------------------------------------------------------------- perusahaan
@dataclass
class Perusahaan:
    kode: str
    nama: str
    nama_resmi: str
    kenakan_ppn: bool
    npwp: str
    alamat_baris: list[str]
    logo: str
    rekening: list[str]
    kota_penerbitan: str = "Jakarta"

    def berkas_logo(self) -> Optional[Path]:
        if not self.logo:
            return None
        p = FOLDER_CONFIG / self.logo
        return p if p.exists() else None


class DaftarPerusahaan:
    """Perusahaan yang bisa memproses order.

    Yang menentukan kop surat di dokumen sekaligus apakah PPN dikenakan:
    order lewat CV. Dwi Putra Mandiri kena PPN, lewat CV. Mutiara Timur
    Nusantara tidak.
    """

    def __init__(self, semua: list[Perusahaan], bawaan: str, kota: str):
        self.semua = semua
        self._index = {p.kode.upper(): p for p in semua}
        self.kode_bawaan = (bawaan or (semua[0].kode if semua else "")).upper()
        self.kota_penerbitan = kota

    @classmethod
    def muat(cls, berkas: Path | None = None) -> "DaftarPerusahaan":
        berkas = berkas or (FOLDER_CONFIG / "perusahaan.yaml")
        d = yaml.safe_load(berkas.read_text(encoding="utf-8")) or {}
        kota = d.get("kota_penerbitan", "Jakarta")
        semua: list[Perusahaan] = []
        for x in d.get("perusahaan") or []:
            semua.append(
                Perusahaan(
                    kode=str(x.get("kode", "")).strip().upper(),
                    nama=x.get("nama", ""),
                    nama_resmi=x.get("nama_resmi", x.get("nama", "")),
                    kenakan_ppn=bool(x.get("kenakan_ppn", True)),
                    npwp=(x.get("npwp") or "").strip(),
                    alamat_baris=list(x.get("alamat_baris") or []),
                    logo=(x.get("logo") or "").strip(),
                    rekening=list(x.get("rekening") or []),
                    kota_penerbitan=kota,
                )
            )
        return cls(semua, d.get("perusahaan_bawaan", ""), kota)

    def bawaan(self) -> Perusahaan:
        return self._index.get(self.kode_bawaan) or self.semua[0]

    def untuk(self, customer: Optional[Customer]) -> Perusahaan:
        kode = (customer.perusahaan_pemroses if customer else "") or ""
        return self._index.get(kode.upper()) or self.bawaan()

    def dikenal(self, kode: str) -> bool:
        return kode.upper() in self._index


# ------------------------------------------------------------- pengaturan
@dataclass
class Pengaturan:
    tarif_ppn: float = 0.11
    ppn_dikonfirmasi: bool = False
    akhiran_y_untuk_angka: bool = True
    ukuran_dikonfirmasi: bool = False
    termin_hari_default: int = 30
    toleransi_cocok: float = 1.0

    @classmethod
    def muat(cls, berkas: Path | None = None) -> "Pengaturan":
        berkas = berkas or (FOLDER_CONFIG / "pengaturan.yaml")
        d = yaml.safe_load(berkas.read_text(encoding="utf-8")) or {}
        ppn = d.get("ppn") or {}
        lu = d.get("label_ukuran") or {}
        return cls(
            tarif_ppn=float(ppn.get("tarif", 0.11)),
            ppn_dikonfirmasi=bool(ppn.get("sudah_dikonfirmasi", False)),
            akhiran_y_untuk_angka=bool(lu.get("akhiran_y_untuk_angka", True)),
            ukuran_dikonfirmasi=bool(lu.get("sudah_dikonfirmasi", False)),
            termin_hari_default=int(d.get("termin_hari_default", 30)),
            toleransi_cocok=float(d.get("toleransi_cocok", 1.0)),
        )


@dataclass
class Konfigurasi:
    perusahaan: DaftarPerusahaan
    customer: DaftarCustomer
    pengaturan: Pengaturan
    peringatan: list[str] = field(default_factory=list)

    @classmethod
    def muat(cls, folder: Path | None = None) -> "Konfigurasi":
        f = folder or FOLDER_CONFIG
        cfg = cls(
            perusahaan=DaftarPerusahaan.muat(f / "perusahaan.yaml"),
            customer=DaftarCustomer.muat(f / "customer.csv"),
            pengaturan=Pengaturan.muat(f / "pengaturan.yaml"),
        )
        p = cfg.pengaturan
        if not p.ppn_dikonfirmasi:
            cfg.peringatan.append(
                f"Tarif PPN masih memakai angka sementara {p.tarif_ppn:.0%} dan BELUM "
                "dikonfirmasi. Cek ke konsultan pajak sebelum lapor Coretax, lalu ubah "
                "config/pengaturan.yaml -> ppn.sudah_dikonfirmasi: true"
            )
        if not p.ukuran_dikonfirmasi:
            gaya = "2 -> 2Y" if p.akhiran_y_untuk_angka else "2 -> 2"
            cfg.peringatan.append(
                f"Penulisan label ukuran angka polos ({gaya}) BELUM dikonfirmasi Yosua. "
                "Ubah di config/pengaturan.yaml -> label_ukuran."
            )
        for pp in cfg.perusahaan.semua:
            if not pp.berkas_logo():
                cfg.peringatan.append(
                    f"Logo {pp.nama} belum ada. Dokumen tetap dibuat, kop memakai "
                    "teks saja. Taruh logo di folder config/ lalu tulis namanya "
                    "di perusahaan.yaml."
                )
            if not pp.npwp:
                cfg.peringatan.append(
                    f"NPWP {pp.nama} belum diisi di config/perusahaan.yaml. "
                    "Dibutuhkan untuk faktur pajak."
                )

        belum = [
            c.kunci for c in cfg.customer.semua if not c.perusahaan_pemroses
        ]
        if belum:
            cfg.peringatan.append(
                f"{len(belum)} customer belum ditentukan diproses lewat perusahaan mana, "
                f"jadi memakai {cfg.perusahaan.bawaan().nama} "
                f"({'kena' if cfg.perusahaan.bawaan().kenakan_ppn else 'tanpa'} PPN). "
                "Isi kolom perusahaan_pemroses di config/customer.csv. "
                "Customer: " + ", ".join(belum[:8]) + ("..." if len(belum) > 8 else "")
            )
        salah = [
            c.kunci for c in cfg.customer.semua
            if c.perusahaan_pemroses and not cfg.perusahaan.dikenal(c.perusahaan_pemroses)
        ]
        if salah:
            cfg.peringatan.append(
                "Kode perusahaan tidak dikenal untuk customer: " + ", ".join(salah)
                + ". Pakai kode yang ada di config/perusahaan.yaml."
            )
        return cfg
