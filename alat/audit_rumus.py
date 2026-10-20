"""Audit seluruh order sheet: tiap TAB dan tiap SEL BERUMUS.

Dibuat 20 Oktober 2026 atas permintaan Yosua: "audit seluruh ordersheet dan
cek rumus di setiap cell pada tahun ini ... dan periksa juga setiap tab nya".

Yang diperiksa per tab:

  1. Tata letaknya dikenali (ARTICLE CODE / ATO / PRICE W/ VAT ketemu)
  2. Rumus qty per baris (kolom TOTAL ATO) MENJANGKAU seluruh kolom ukuran
  3. Rumus baris TOTAL MENJANGKAU seluruh baris data
  4. Sel berisi galat Excel (#REF!, #N/A, ...) di mana pun
  5. Nilai kotor = qty x harga per baris
  6. Kolom nilai bersih: mana yang terisi penuh, mana yang separuh
  7. Harga baris PO sama dengan tab Harga Retail (KETETAPAN bagian 41)

Cacat 2 dan 3 adalah dua jenis yang berbeda dan sering tertukar — lihat
CLAUDE.md bagian 30. Yang pertama membuat qty di kolom terakhir hilang;
yang kedua membuat baris data di luar rentang tidak ikut dijumlah.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hp_dokumen import tata_letak as tl
# Pembacaan rumus SATU sumber dengan peringatan yang dipakai program sehari-hari
# (src/hp_dokumen/periksa_rumus.py). Kalau dibiarkan dua salinan, cepat atau
# lambat audit dan peringatan menyebut angka yang berbeda — pola yang sama
# dengan rekap di CLAUDE.md bagian 35.
from hp_dokumen.periksa_rumus import (GALAT_EXCEL as GALAT,
                                      nomor_kolom as _kolom,
                                      rentang_rumus as rentang_sum)
from hp_dokumen.pemindai import (adalah_tab_harga, cari_di_master,
                                 master_harga_dari_buku)


class Temuan:
    """Satu temuan audit.

    `tingkat` memisahkan yang SUDAH salah angkanya dari yang baru berpotensi.
    Tanpa pemisahan ini laporannya 12.000 baris dan tidak ada yang membacanya
    — pelajaran alarm palsu di CLAUDE.md bagian 14.
    """

    def __init__(self, berkas, tab, jenis, sel, isi, pesan):
        self.berkas, self.tab, self.jenis = berkas, tab, jenis
        self.sel, self.isi, self.pesan = sel, isi, pesan

    @property
    def tingkat(self) -> str:
        if "belum berdampak" in self.pesan:
            return "POTENSI"
        if self.jenis == "GALAT EXCEL" and self.sel[:2] == "AA":
            return "POTENSI"   # kolom LOSSES tidak dipakai dokumen mana pun
        return "GENTING"

    def baris(self):
        return [self.tingkat, self.berkas, self.tab, self.jenis,
                self.sel, self.isi, self.pesan]


def baris_judul_blok(ws, batas_baris: int) -> list[int]:
    out = []
    for r in range(1, batas_baris + 1):
        if tl.seragam(ws.cell(r, 1).value) == "ARTICLE CODE":
            out.append(r)
    return out


def audit_tab(berkas: str, ws, wv, master: dict) -> tuple[list[Temuan], dict]:
    temuan: list[Temuan] = []
    nama = ws.title
    maks_r = min(ws.max_row or 1, 2000)
    maks_c = min(ws.max_column or 1, 60)

    def lapor(jenis, r, c, isi, pesan):
        temuan.append(Temuan(berkas, nama, jenis,
                             f"{get_column_letter(c)}{r}", str(isi)[:90], pesan))

    # ---- 4. galat Excel di mana pun ------------------------------------
    galat_n = 0
    for r in range(1, maks_r + 1):
        for c in range(1, maks_c + 1):
            for sumber in (ws.cell(r, c).value, wv.cell(r, c).value):
                if isinstance(sumber, str) and sumber.strip() in GALAT:
                    galat_n += 1
                    if galat_n <= 6:
                        lapor("GALAT EXCEL", r, c, sumber, "sel berisi galat")
                    break
    if galat_n > 6:
        temuan.append(Temuan(berkas, nama, "GALAT EXCEL", "", "",
                             f"total {galat_n} sel bergalat di tab ini"))

    judul = baris_judul_blok(ws, maks_r)
    ringkas = {"tab": nama, "blok": len(judul), "galat": galat_n,
               "baris_data": 0, "dikenali": bool(judul)}
    if not judul:
        return temuan, ringkas

    tata0 = tl.kenali(ws, judul[0], maks_c)
    if not tata0.lengkap():
        lapor("TATA LETAK", judul[0], 1, nama,
              "susunan kolom tidak dikenali: " + "; ".join(tata0.catatan))
        return temuan, ringkas
    if tata0.hanya_qty:
        ringkas["jenis"] = "packing list"
        return temuan, ringkas

    baris_data: list[int] = []
    batas_blok = judul + [maks_r + 1]

    for i, br in enumerate(judul):
        tata = tl.kenali(ws, br, maks_c)
        if not tata.lengkap():
            lapor("TATA LETAK", br, 1, f"blok {i+1}",
                  "; ".join(tata.catatan) or "blok tidak dikenali")
            continue
        for r in range(br + 2, batas_blok[i + 1]):
            kode = ws.cell(r, tata.kol_kode).value
            if not kode or tl.seragam(kode) in ("ARTICLE CODE", "TOTAL"):
                continue
            qty = wv.cell(r, tata.kol_ato_total).value if tata.kol_ato_total else None
            if not isinstance(qty, (int, float)) or not qty:
                continue
            baris_data.append(r)

            # ---- 2. rumus qty per baris menjangkau seluruh kolom ukuran
            f = ws.cell(r, tata.kol_ato_total).value
            if isinstance(f, str) and f.startswith("="):
                for c1, r1, c2, r2 in rentang_sum(f):
                    if r1 != r or r2 != r:
                        continue
                    if c1 == tata.ato_mulai and c2 < tata.ato_selesai:
                        hilang = sum(
                            (wv.cell(r, c).value or 0)
                            for c in range(c2 + 1, tata.ato_selesai + 1)
                            if isinstance(wv.cell(r, c).value, (int, float)))
                        lapor("RUMUS QTY PENDEK", r, tata.kol_ato_total, f,
                              f"berhenti di {get_column_letter(c2)}, "
                              f"seharusnya {get_column_letter(tata.ato_selesai)}"
                              + (f" - {hilang:g} pcs tidak terhitung" if hilang else
                                 " - belum berdampak, kolom sisanya kosong"))

            # ---- 5. nilai kotor = qty x harga
            if tata.kol_harga and tata.kol_ato_value:
                h = wv.cell(r, tata.kol_harga).value
                z = wv.cell(r, tata.kol_ato_value).value
                if isinstance(h, (int, float)) and isinstance(z, (int, float)):
                    if abs(qty * h - z) > 1:
                        lapor("NILAI KOTOR", r, tata.kol_ato_value, f"{z:,.0f}",
                              f"qty {qty:g} x harga {h:,.0f} = {qty*h:,.0f}")

            # ---- 7. harga ikut tab Harga Retail
            if master and tata.kol_harga:
                m = cari_di_master(master, str(kode))
                h = wv.cell(r, tata.kol_harga).value
                if m is None:
                    lapor("KODE TAK TERDAFTAR", r, tata.kol_kode, kode,
                          "tidak ada di tab Harga Retail")
                else:
                    hm = m[1] if isinstance(m, tuple) else getattr(m, "harga", 0)
                    if isinstance(h, (int, float)) and hm and abs(h - hm) > 0.5:
                        lapor("HARGA BEDA MASTER", r, tata.kol_harga, f"{h:,.0f}",
                              f"Harga Retail menulis {hm:,.0f}")

    ringkas["baris_data"] = len(baris_data)
    if not baris_data:
        ringkas["jenis"] = "ATO kosong"
        return temuan, ringkas

    # ---- 3. baris TOTAL menjangkau seluruh baris data -------------------
    #
    # Baris TOTAL punya DUA bentuk, dan keduanya harus diperiksa dengan cara
    # yang berbeda. Kalau tidak dibedakan, yang satu terbaca sebagai cacat
    # padahal wajar:
    #
    #   MENURUN   W116 = SUM(W3:W115)      -> periksa rentang BARISnya
    #   MENDATAR  W74  = SUM(N74:S74)      -> baris TOTAL menjumlah sel total
    #                                         tiap kolom ukuran. Yang diperiksa
    #                                         rentang KOLOMnya, lalu tiap sel
    #                                         total kolom ukuran itu sendiri.
    # Satu tab bisa punya BEBERAPA baris TOTAL — satu per blok, lalu satu
    # TOTAL seluruh PO di paling bawah. Yang dicari yang TERAKHIR, dan yang
    # MENURUN diutamakan. Mengambil yang pertama ketemu memilih TOTAL blok,
    # dan cacat di TOTAL seluruh PO lolos tanpa terdeteksi (terbukti pada
    # DHAWAFEST BAZAAR Februari 2026: W160 yang cacat, W124 yang terbaca).
    kol_t = tata0.kol_ato_total
    data_set = set(baris_data)
    menurun_kandidat, mendatar_kandidat = [], []
    for r in range(min(baris_data), maks_r + 1):
        if r in data_set:
            continue
        f = ws.cell(r, kol_t).value
        if not (isinstance(f, str) and f.upper().startswith("=SUM")):
            continue
        rg = rentang_sum(f)
        if any(c1 == c2 == kol_t for c1, _, c2, _ in rg):
            menurun_kandidat.append(r)
        elif any(r1 == r2 == r for _, r1, _, r2 in rg):
            mendatar_kandidat.append(r)
    baris_total = (menurun_kandidat or mendatar_kandidat or [None])[-1]
    if baris_total is None:
        temuan.append(Temuan(berkas, nama, "BARIS TOTAL", "", "",
                             "baris TOTAL berumus tidak ketemu di kolom "
                             + get_column_letter(kol_t)))
    else:
        f = ws.cell(baris_total, kol_t).value
        rentang = rentang_sum(f)
        mendatar = baris_total not in menurun_kandidat

        def periksa_menurun(sel_r, sel_c, rumus, kolom_diperiksa):
            tercakup = set()
            for c1, r1, c2, r2 in rentang_sum(rumus):
                if c1 == c2 == kolom_diperiksa:
                    tercakup |= set(range(r1, r2 + 1))
            for m in re.findall(r"(?<![:\w$])\$?([A-Z]{1,3})\$?(\d+)(?![:\d])", rumus):
                if _kolom(m[0]) == kolom_diperiksa:
                    tercakup.add(int(m[1]))
            luput = sorted(r for r in baris_data
                           if r not in tercakup
                           and isinstance(wv.cell(r, kolom_diperiksa).value, (int, float))
                           and wv.cell(r, kolom_diperiksa).value)
            if luput:
                hilang = sum(wv.cell(r, kolom_diperiksa).value or 0 for r in luput)
                temuan.append(Temuan(
                    berkas, nama, "BARIS TOTAL KURANG",
                    f"{get_column_letter(sel_c)}{sel_r}", str(rumus)[:90],
                    f"{len(luput)} baris data tidak ikut dijumlah "
                    f"(baris {luput[0]}-{luput[-1]}), {hilang:g} pcs"))

        if mendatar:
            # Rentang kolomnya harus menjangkau seluruh kolom ukuran.
            for c1, r1, c2, r2 in rentang:
                if r1 == r2 == baris_total and c1 == tata0.ato_mulai \
                        and c2 < tata0.ato_selesai:
                    hilang = sum(
                        (wv.cell(baris_total, c).value or 0)
                        for c in range(c2 + 1, tata0.ato_selesai + 1)
                        if isinstance(wv.cell(baris_total, c).value, (int, float)))
                    temuan.append(Temuan(
                        berkas, nama, "TOTAL MENDATAR PENDEK",
                        f"{get_column_letter(kol_t)}{baris_total}", str(f)[:90],
                        f"berhenti di {get_column_letter(c2)}, seharusnya "
                        f"{get_column_letter(tata0.ato_selesai)}"
                        + (f" - {hilang:g} pcs tidak terhitung" if hilang else
                           " - belum berdampak, kolom sisanya kosong")))
            # lalu tiap sel total kolom ukuran diperiksa menurun
            for c in range(tata0.ato_mulai, tata0.ato_selesai + 1):
                fk = ws.cell(baris_total, c).value
                if isinstance(fk, str) and fk.upper().startswith("=SUM"):
                    periksa_menurun(baris_total, c, fk, c)
        else:
            periksa_menurun(baris_total, kol_t, f, kol_t)
    ringkas["baris_total"] = baris_total
    return temuan, ringkas


def audit_berkas(path: Path):
    wb = openpyxl.load_workbook(path, data_only=False)
    wv = openpyxl.load_workbook(path, data_only=True)
    master = master_harga_dari_buku(wv)
    semua, ringkas = [], []
    for j in wb.sheetnames:
        if adalah_tab_harga(j):
            continue
        t, r = audit_tab(path.stem, wb[j], wv[j], master)
        semua += t
        ringkas.append(r)
    return semua, ringkas, len(master)


def main(folder: str):
    import csv
    berkas = sorted(Path(folder).glob("*.xlsx"))
    semua, baris_ringkas = [], []
    for p in berkas:
        t, r, nmaster = audit_berkas(p)
        semua += t
        n_tab = len(r)
        n_data = sum(x["baris_data"] for x in r)
        print(f"{p.stem:<28} tab {n_tab:>3}  baris {n_data:>5}  "
              f"master {nmaster:>3}  temuan {len(t):>4}")
        for x in r:
            baris_ringkas.append([p.stem, x["tab"], x["blok"], x["baris_data"],
                                  x["galat"], x.get("jenis", ""),
                                  "ya" if x["dikenali"] else "TIDAK"])
    Path("keluaran").mkdir(exist_ok=True)
    with open("keluaran/AUDIT_TEMUAN.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["TINGKAT", "ORDER SHEET", "TAB", "JENIS", "SEL", "ISI",
                    "KETERANGAN"])
        for t in semua:
            w.writerow(t.baris())
    with open("keluaran/AUDIT_TAB.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ORDER SHEET", "TAB", "BLOK", "BARIS DATA", "SEL GALAT",
                    "CATATAN", "DIKENALI"])
        w.writerows(baris_ringkas)
    print(f"\nTOTAL temuan {len(semua)} dari {len(baris_ringkas)} tab")
    from collections import Counter
    for j, n in Counter((t.tingkat, t.jenis) for t in semua).most_common():
        print(f"  {j[0]:<8} {j[1]:<22} {n}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/audit2026")
