"""Audit khusus RUMUS HARGA dan DISKON di order sheet.

Permintaan Yosua 20 Oktober 2026: *"cek kembali hasilnya apakah ada salah
perhitungan atau rumus di bagian harga dan diskon yang telah dibuat di
ordersheet dalam kurun waktu tahun ini"*.

Audit bagian 49 memeriksa qty, baris TOTAL, dan galat Excel. Yang BELUM
diperiksa justru rantai uangnya sendiri:

    X  PRICE W/ VAT        <- idealnya VLOOKUP ke tab Harga Retail
    Z  TOTAL ATO (VALUE)   = X * W
    AB DISC                persen diskon yang DITULIS
    AC TOTAL VALUE         = Z - (Z * <persen>)   <- persennya MATI di rumus
    AD/AE CBD/COD          = AC - (AC * <tarif>)  <- tarifnya juga MATI

Dua angka persen itu (AB yang tertulis, dan yang tertanam di rumus AC)
TIDAK saling menunjuk. Jadi keduanya bisa berbeda tanpa ada yang tahu —
dan yang dipakai menghitung uang adalah yang di dalam rumus.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter as L

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hp_dokumen import tata_letak as tl
from hp_dokumen.pemindai import adalah_tab_harga, master_harga_dari_buku

# "25%" / "0.25" / "1,5%" di dalam rumus
_PERSEN = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
_KALI = re.compile(r"\*\s*(0?[.,]\d+)")

STAT = Counter()


def persen_dalam_rumus(rumus: str):
    """Persen yang DITANAM di dalam rumus diskon, jadi pecahan (0,25)."""
    if not isinstance(rumus, str):
        return None
    m = _PERSEN.search(rumus)
    if m:
        return float(m.group(1).replace(",", ".")) / 100
    m = _KALI.search(rumus)
    if m:
        v = float(m.group(1).replace(",", "."))
        # `=Z3*0.75` berarti diskon 25%, bukan 75%
        return round(1 - v, 6) if v > 0.5 else v
    return None


def _n(v):
    return float(v) if isinstance(v, (int, float)) else None


def _persen_sel(v):
    """Isi kolom DISC jadi pecahan.

    Kolom DISC kadang berisi ANGKA (0.25) dan kadang TEKS ("27.5%").
    Versi pertama pemeriksa ini hanya membaca angka, jadi tab yang
    DISC-nya teks tidak pernah diperiksa sama sekali — dan hasilnya
    terlihat bersih padahal pemeriksaannya memang tidak jalan.
    """
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*%\s*", v)
        if m:
            return float(m.group(1).replace(",", ".")) / 100
    return None


def audit_tab(berkas, ws, wv, master):
    t = []

    def lapor(jenis, sel, isi, pesan):
        t.append([berkas, ws.title, jenis, sel, str(isi)[:70], pesan])

    maks_r = min(ws.max_row or 1, 2000)
    maks_c = min(ws.max_column or 1, 60)
    judul = [r for r in range(1, maks_r + 1)
             if tl.seragam(ws.cell(r, 1).value) == "ARTICLE CODE"]
    if not judul:
        return t
    tata0 = tl.kenali(ws, judul[0], maks_c)
    if not tata0.lengkap() or tata0.hanya_qty:
        return t

    harga_rumus = Counter()
    STAT["tab"] += 1
    persen_ac = Counter()          # persen yang tertanam di rumus AC
    persen_ab = Counter()          # angka di kolom DISC
    tarif_nett = defaultdict(Counter)
    baris_dipakai = 0

    batas = judul + [maks_r + 1]
    for i, br in enumerate(judul):
        tata = tl.kenali(ws, br, maks_c)
        if not tata.lengkap():
            continue
        k_top = tata.kolom_top()
        for r in range(br + 2, batas[i + 1]):
            kode = ws.cell(r, tata.kol_kode).value
            if not kode or tl.seragam(kode) in ("ARTICLE CODE", "TOTAL"):
                continue
            qty = _n(wv.cell(r, tata.kol_ato_total).value) if tata.kol_ato_total else None
            if not qty:
                continue
            baris_dipakai += 1
            STAT["baris"] += 1

            # ---- 1. harga: rumus atau diketik tangan? -------------------
            fx = ws.cell(r, tata.kol_harga).value if tata.kol_harga else None
            if isinstance(fx, str) and fx.startswith("="):
                harga_rumus["rumus"] += 1
                STAT["harga VLOOKUP"] += 1
                if "VLOOKUP" not in fx.upper() and "INDEX" not in fx.upper():
                    lapor("HARGA RUMUS ANEH", f"{L(tata.kol_harga)}{r}", fx,
                          "harga bukan VLOOKUP ke tab Harga Retail")
            else:
                harga_rumus["diketik"] += 1
                STAT["harga diketik"] += 1

            harga = _n(wv.cell(r, tata.kol_harga).value) if tata.kol_harga else None
            kotor = _n(wv.cell(r, tata.kol_ato_value).value) if tata.kol_ato_value else None

            # ---- 2. nilai kotor = qty x harga ---------------------------
            if harga is not None and kotor is not None:
                if abs(qty * harga - kotor) > 1:
                    lapor("NILAI KOTOR SALAH", f"{L(tata.kol_ato_value)}{r}",
                          f"{kotor:,.0f}",
                          f"qty {qty:g} x harga {harga:,.0f} = {qty*harga:,.0f}")

            # ---- 3. persen diskon: yang tertanam vs kolom DISC ----------
            if k_top:
                fac = ws.cell(r, k_top.kolom).value
                p = persen_dalam_rumus(fac)
                if p is not None:
                    persen_ac[round(p, 6)] += 1
                    STAT["AC berumus"] += 1
                nett = _n(wv.cell(r, k_top.kolom).value)
                # nilai bersih harus cocok dengan persen yang tertanam
                if p is not None and kotor and nett is not None:
                    harap = kotor * (1 - p)
                    if abs(harap - nett) > 1:
                        lapor("NILAI BERSIH TIDAK COCOK RUMUSNYA",
                              f"{L(k_top.kolom)}{r}", f"{nett:,.2f}",
                              f"kotor {kotor:,.0f} x (1-{p:.4%}) = {harap:,.2f}")
            if tata.kol_disc:
                d = _persen_sel(wv.cell(r, tata.kol_disc).value)
                if d is not None:
                    persen_ab[round(d, 6)] += 1
                    STAT["DISC terbaca"] += 1

            # ---- 4. tarif CBD/COD: tertanam vs JUDUL kolomnya -----------
            for k in tata.nett:
                if k.jenis not in ("CBD", "COD"):
                    continue
                f = ws.cell(r, k.kolom).value
                p = persen_dalam_rumus(f)
                if p is not None:
                    tarif_nett[(k.kolom, k.judul, k.tarif)][round(p, 6)] += 1
                    STAT["CBD/COD berumus"] += 1

    if not baris_dipakai:
        return t

    # ---- harga diketik tangan -----------------------------------------
    if harga_rumus["diketik"]:
        bagian = harga_rumus["diketik"] / max(1, sum(harga_rumus.values()))
        lapor("HARGA DIKETIK TANGAN", "", f"{harga_rumus['diketik']} baris",
              f"{bagian:.0%} baris harganya BUKAN rumus ke tab Harga Retail, "
              "jadi tidak ikut berubah kalau harga retail diperbarui")

    # ---- persen diskon tidak seragam dalam satu tab --------------------
    if len(persen_ac) > 1:
        rinci = ", ".join(f"{p:.4%} ({n} baris)"
                          for p, n in sorted(persen_ac.items()))
        lapor("DISKON TIDAK SERAGAM", "", "", 
              f"persen diskon di rumus TOTAL VALUE berbeda-beda: {rinci}")

    # ---- persen di rumus vs kolom DISC ---------------------------------
    if persen_ac and persen_ab:
        pac = max(persen_ac, key=persen_ac.get)
        pab = max(persen_ab, key=persen_ab.get)
        if abs(pac - pab) > 0.0005:
            lapor("KOLOM DISC TIDAK COCOK RUMUS", "",
                  f"DISC tertulis {pab:.4%}",
                  f"tapi rumus TOTAL VALUE memakai {pac:.4%}. "
                  "Yang dipakai menghitung uang adalah yang di rumus")

    # ---- tarif CBD/COD vs judul kolomnya -------------------------------
    for (kol, jud, tarif_judul), hit in tarif_nett.items():
        p = max(hit, key=hit.get)
        if len(hit) > 1:
            lapor("TARIF CBD/COD TIDAK SERAGAM", L(kol), jud,
                  "tarif berbeda antar baris: "
                  + ", ".join(f"{x:.3%} ({n})" for x, n in sorted(hit.items())))
        if tarif_judul is not None and abs(p - tarif_judul) > 0.0005:
            lapor("TARIF TIDAK COCOK JUDUL", L(kol), jud,
                  f"judul kolom menulis {tarif_judul:.3%} "
                  f"tapi rumusnya memakai {p:.3%}")
    return t


def main(folder):
    semua = []
    STAT.clear()
    for p in sorted(Path(folder).glob("*.xlsx")):
        wb = openpyxl.load_workbook(p)
        wv = openpyxl.load_workbook(p, data_only=True)
        master = master_harga_dari_buku(wv)
        n = 0
        for j in wb.sheetnames:
            if adalah_tab_harga(j):
                continue
            t = audit_tab(p.stem, wb[j], wv[j], master)
            semua += t
            n += len(t)
        print(f"{p.stem:<28} temuan {n}")
    Path("keluaran").mkdir(exist_ok=True)
    with open("keluaran/AUDIT_HARGA_DISKON.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ORDER SHEET", "TAB", "JENIS", "SEL", "ISI", "KETERANGAN"])
        w.writerows(semua)
    print("\nYANG BENAR-BENAR DIPERIKSA (bukti pemeriksaannya jalan):")
    for k in ("tab", "baris", "harga VLOOKUP", "harga diketik",
              "AC berumus", "DISC terbaca", "CBD/COD berumus"):
        print(f"  {k:<20} {STAT[k]:>7}")
    print(f"\nTOTAL {len(semua)} temuan")
    for j, n in Counter(x[2] for x in semua).most_common():
        print(f"  {j:<34} {n}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/audit2026")
