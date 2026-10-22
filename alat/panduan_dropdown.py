"""PANDUAN: memasang pilihan persen diskon di Google Sheets.

Dibuat 22 Oktober 2026. Ditulis untuk dikerjakan sendiri oleh rekan kerja
yang tidak akrab dengan rumus, lewat menu Insert > Dropdown.

Seluruh rumus di berkas ini SUDAH DIUJI LANGSUNG di Google Sheets, bukan
ditulis dari ingatan. Tiga hal yang ketahuan dari pengujian itu dan tidak
boleh diubah:

  1. Isi dropdown WAJIB memakai TITIK  ->  1.5%   BUKAN  1,5%
     Diuji: =1000-(1000*"1,5%") memberi #VALUE!, yang titik memberi 985.
     Judul kolom di order sheet sekarang menulis "1,5%" dengan koma, jadi
     ini jebakan yang hampir pasti dimasuki kalau tidak diperingatkan.

  2. Judul kolom ditulis ROUND(x*100,2)&"%", BUKAN TEXT(x,"0.##%").
     Diuji: TEXT di Google Sheets memberi "2.%" — ada titik menggantung.

  3. Dropdown boleh berisi TEKS "25%"; Google Sheets mengubahnya sendiri
     saat dihitung. Diuji pada angka Caroline sungguhan: lewat teks dan
     lewat angka sama-sama memberi 17.478.871,83.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

AKAR = Path(__file__).resolve().parent.parent

JUDUL = Font(bold=True, size=11, color="FFFFFF")
ISI_JUDUL = PatternFill("solid", fgColor="2F5597")
KUNING = PatternFill("solid", fgColor="FFF2CC")
MERAH = Font(bold=True, color="C00000")
TIPIS = Side(style="thin", color="BFBFBF")
KOTAK = Border(left=TIPIS, right=TIPIS, top=TIPIS, bottom=TIPIS)
MONO = Font(name="Consolas", size=10)

LANGKAH = [
    (1, "Buat tempat pilihannya",
     "Buka tab PO. Klik sel AH2, ketik: Diskon dasar\n"
     "AH3: Tambahan CBD    AH4: Tambahan COD    AH5: Tambahan ke-2",
     "Kolom AH dan AI dipilih karena KOSONG. Jangan menyisipkan baris atau "
     "kolom baru — letak kolom A sampai AE harus tetap, kalau bergeser "
     "program pembuat Invoice berhenti mengenali tabnya."),
    (2, "Pasang dropdown pertama",
     "Klik sel AI2.  Menu  Insert  >  Dropdown",
     "Panel 'Data validation rules' muncul di kanan layar."),
    (3, "Isi daftar persennya",
     "Di panel kanan, di bawah 'Criteria' sudah tertulis Dropdown.\n"
     "Klik 'Add another item' untuk tiap pilihan, lalu ketik:\n\n"
     "    0%    18%    20%    22%    25%    26.5%    27.5%    30%",
     "WAJIB pakai TITIK, bukan koma. Tulis 26.5% — JANGAN 26,5%. "
     "Sudah diuji: yang pakai koma membuat seluruh rumus jadi #VALUE!."),
    (4, "Simpan",
     "Klik tombol  Done  di bawah panel.",
     "Sel AI2 sekarang punya panah kecil. Klik panahnya, pilih 25%."),
    (5, "Pasang dropdown untuk tambahan CBD/COD",
     "Klik sel AI3.  Insert > Dropdown.  Isi daftarnya:\n\n"
     "    0%    1.5%    2%    2.5%    3%    5%\n\n"
     "Klik Done. Lalu ulangi untuk AI4 dan AI5.",
     "Cara cepat: sesudah AI3 jadi, klik AI3, tekan Ctrl+C, lalu pilih "
     "AI4:AI5 dan tekan Ctrl+V. Dropdownnya ikut tersalin."),
    (6, "Isi rumus kolom DISC (AB)",
     "Klik sel AB3, ketik rumus ini lalu Enter:\n\n"
     "    =$AI$2",
     "Tanda $ WAJIB ada. Tanpa $, saat rumusnya disalin ke bawah ia akan "
     "menunjuk AI4, AI5, dan seterusnya — bukan sel pilihan lagi."),
    (7, "Isi rumus TOTAL VALUE (AC)",
     "Klik sel AC3, ketik lalu Enter:\n\n"
     "    =Z3*(1-$AI$2)",
     "Inilah yang menggantikan =Z3-(Z3*25%). Persennya tidak lagi "
     "ditulis di dalam rumus, jadi kolom DISC dan uangnya TIDAK MUNGKIN "
     "berbeda lagi."),
    (8, "Isi rumus DISCOUNT CBD (AD)",
     "Klik sel AD3, ketik lalu Enter:\n\n"
     "    =AC3*(1-$AI$3)*(1-$AI$5)",
     "Dikali dua kali, BUKAN dijumlahkan. 2% lalu 2% sama dengan 3,96%, "
     "bukan 4%. Kalau tidak ada tambahan ke-2, pilih 0% di AI5 dan "
     "rumusnya tetap benar."),
    (9, "Isi rumus DISCOUNT COD (AE)",
     "Klik sel AE3, ketik lalu Enter:\n\n"
     "    =AC3*(1-$AI$4)",
     "KALAU tab ini tidak punya kolom COD, LEWATI langkah ini dan biarkan "
     "AE kosong. Mengisinya dengan 0% membuat kolomnya terisi penuh, lalu "
     "program menganggap ordernya COD padahal TOP."),
    (10, "Salin ke seluruh baris",
     "Pilih AB3:AE3.  Ctrl+C.\n"
     "Pilih AB4 sampai baris data terakhir.  Ctrl+V.",
     "Salin HANYA sampai baris data terakhir. Jangan sampai kena baris "
     "TOTAL — baris TOTAL punya rumus SUM sendiri dan akan tertimpa."),
    (11, "Buat judul kolom ikut berubah",
     "Klik sel AD1, ketik lalu Enter:\n\n"
     '    ="DISCOUNT CBD + "&ROUND($AI$3*100,2)&"%"\n'
     '     &IF($AI$5>0," + "&ROUND($AI$5*100,2)&"%","")\n\n'
     "Klik sel AE1, ketik lalu Enter:\n\n"
     '    ="DISCOUNT COD + "&ROUND($AI$4*100,2)&"%"',
     "Pakai ROUND, JANGAN TEXT. Sudah diuji: TEXT di Google Sheets "
     'memberi "2.%" dengan titik menggantung, ROUND memberi "2%". '
     "Sesudah ini judul kolom tidak mungkin lagi berbeda dari tarif "
     "yang sebenarnya dipakai."),
    (12, "Beri warna sel pilihannya",
     "Pilih AI2:AI5.  Klik ikon ember cat.  Pilih kuning.",
     "Supaya rekan kerja langsung tahu hanya sel kuning yang boleh diisi."),
    (13, "PERIKSA sebelum ditinggalkan",
     "Lihat baris TOTAL kolom AC, AD, dan AE.\n"
     "Bandingkan dengan angka SEBELUM diubah.",
     "Kalau berbeda, URUNGKAN semuanya (Ctrl+Z berkali-kali) dan "
     "tanyakan dulu. Jangan pernah meninggalkan tab yang angkanya "
     "berubah tanpa sebab yang jelas."),
]

RUMUS = [
    ("AB3", "Kolom DISC", "=$AI$2",
     "Persen diskon dasar, dibaca dari sel pilihan"),
    ("AC3", "TOTAL VALUE", "=Z3*(1-$AI$2)",
     "Nilai kotor dikurangi diskon dasar"),
    ("AD3", "DISCOUNT CBD", "=AC3*(1-$AI$3)*(1-$AI$5)",
     "TOTAL VALUE dikurangi tambahan CBD, lalu tambahan ke-2 (BERUNTUN)"),
    ("AE3", "DISCOUNT COD", "=AC3*(1-$AI$4)",
     "TOTAL VALUE dikurangi tambahan COD"),
    ("AD1", "Judul kolom CBD",
     '="DISCOUNT CBD + "&ROUND($AI$3*100,2)&"%"&IF($AI$5>0," + "&ROUND($AI$5*100,2)&"%","")',
     "Judul ikut persen yang dipilih"),
    ("AE1", "Judul kolom COD",
     '="DISCOUNT COD + "&ROUND($AI$4*100,2)&"%"',
     "Judul ikut persen yang dipilih"),
]

UJI = [
    ("Isi dropdown pakai KOMA", '=1000-(1000*"1,5%")', "#VALUE!",
     "RUSAK — jangan pernah pakai koma di isi dropdown"),
    ("Isi dropdown pakai TITIK", '=1000-(1000*"1.5%")', "985", "benar"),
    ("Dropdown berisi teks persen",
     '=24266100*(1-"25%")*(1-"2%")*(1-"2%")', "17.478.871,83", "benar"),
    ("Kalau diisi angka biasa",
     "=24266100*(1-0,25)*(1-0,02)*(1-0,02)", "17.478.871,83",
     "sama persis — jadi teks maupun angka dua-duanya jalan"),
    ("Judul pakai TEXT", '=TEXT(0,02;"0.##%")', "2.%",
     "JELEK — ada titik menggantung"),
    ("Judul pakai ROUND", '=ROUND(0,02*100;2)&"%"', "2%", "benar"),
    ("Judul 1,5 persen", '=ROUND(0,015*100;2)&"%"', "1.5%", "benar"),
    ("Judul 27,5 persen", '=ROUND(0,275*100;2)&"%"', "27.5%", "benar"),
]

HATI = [
    ("Tab yang persen diskonnya TIDAK seragam antar baris",
     "Satu sel pilihan berlaku untuk SELURUH tab. Periksa dulu kolom DISC-nya "
     "satu nilai atau tidak. Contoh yang sudah ketahuan: PO 04 Maret - "
     "Katamama Cikaret, 55 baris 25% tapi 2 baris 22%."),
    ("Kolom AD atau AE yang lama HARUS ditimpa SELURUHNYA",
     "Kalau sebagian masih rumus lama, order sheet jadi campuran dua cara. "
     "Itu lebih membingungkan daripada sekarang, dan lebih sulit diperiksa."),
    ("Jangan mengisi kolom yang tab itu memang tidak punya",
     "Mengisi AD dengan 0% membuat kolomnya terisi penuh, lalu Aturan 2 "
     "memilihnya sebagai CBD padahal ordernya TOP. Angkanya kebetulan sama, "
     "tapi CARA BAYAR yang tercatat jadi salah."),
    ("Jangan menyisipkan baris atau kolom",
     "Letak kolom A sampai AE harus tetap. Sel pilihan sengaja ditaruh di "
     "AH/AI yang kosong supaya tidak menggeser apa pun."),
    ("Kerjakan SATU tab dulu, periksa, baru lanjut",
     "Jangan mengubah 16 tab sekaligus. Kalau ada yang salah, mencarinya "
     "jauh lebih sulit."),
    ("Potongan BERUNTUN, bukan dijumlahkan",
     "25% + 2% + 2% berarti dikali (1-25%) lalu (1-2%) lalu (1-2%). "
     "Hasilnya 28,95%, BUKAN 29%. Selisihnya nyata di angka rupiah."),
]


def _hdr(ws, kolom, baris=1):
    for i, (nama, lebar) in enumerate(kolom, start=1):
        s = ws.cell(baris, i, nama)
        s.font = JUDUL
        s.fill = ISI_JUDUL
        s.alignment = Alignment(horizontal="center", vertical="center",
                                wrap_text=True)
        s.border = KOTAK
        ws.column_dimensions[chr(64 + i)].width = lebar
    ws.row_dimensions[baris].height = 28
    ws.freeze_panes = ws.cell(baris + 1, 1)


def _tinggi(teks: str, lebar: int) -> int:
    """Jumlah BARIS tampil sesudah teksnya melipat di kolom selebar itu.

    Menghitung tinggi dari jumlah '\n' saja TIDAK CUKUP — baris panjang
    melipat sendiri dan bagian bawahnya terpotong tanpa jejak di nilai sel.
    Ketahuan dari melihat gambar hasil render, bukan dari membaca selnya.
    """
    n = 0
    for baris in str(teks).split("\n"):
        n += max(1, -(-len(baris) // max(10, lebar - 2)))
    return n


def _isi(ws, r, nilai, mono_kolom=()):
    for i, v in enumerate(nilai, start=1):
        s = ws.cell(r, i, v)
        s.border = KOTAK
        s.alignment = Alignment(vertical="top", wrap_text=True)
        if i in mono_kolom:
            s.font = MONO
            s.fill = KUNING
            # Rumus di sini untuk DIBACA, bukan dihitung. Tanpa baris ini
            # openpyxl menganggap teks berawalan "=" sebagai rumus, dan
            # Excel menampilkan HASILNYA (0) — bukan rumusnya. Ketahuan
            # dari melihat gambar hasil render.
            if isinstance(v, str) and v.startswith("="):
                s.data_type = "s"


def main() -> None:
    wb = Workbook()

    ws = wb.active
    ws.title = "LANGKAH DEMI LANGKAH"
    ws.cell(1, 1, "MEMASANG PILIHAN PERSEN DISKON DI GOOGLE SHEETS").font = Font(bold=True, size=15)
    ws.cell(2, 1, "Lewat menu Insert > Dropdown · dikerjakan per tab PO · "
                  "semua rumus sudah diuji langsung di Google Sheets").font = Font(italic=True, size=10, color="666666")
    _hdr(ws, [("NO", 5), ("LANGKAH", 30), ("YANG DIKETIK / DIKLIK", 56),
              ("KENAPA BEGITU", 60)], baris=4)
    r = 5
    for no, judul, aksi, kenapa in LANGKAH:
        _isi(ws, r, [no, judul, aksi, kenapa], mono_kolom=(3,))
        ws.cell(r, 2).font = Font(bold=True, size=10)
        ws.row_dimensions[r].height = 14 * max(
            2, _tinggi(aksi, 56), _tinggi(kenapa, 60))
        r += 1
    ws.sheet_view.showGridLines = False

    ws = wb.create_sheet("DAFTAR RUMUS")
    ws.cell(1, 1, "RUMUS YANG DIPAKAI — SALIN APA ADANYA").font = Font(bold=True, size=14)
    ws.cell(2, 1, "Baris 3 sebagai contoh. Sesudah diketik di baris 3, "
                  "tinggal disalin ke bawah.").font = Font(italic=True, size=10, color="666666")
    _hdr(ws, [("SEL", 8), ("ISI KOLOM", 20), ("RUMUSNYA", 72),
              ("ARTINYA", 50)], baris=4)
    r = 5
    for sel, isi, rum, arti in RUMUS:
        _isi(ws, r, [sel, isi, rum, arti], mono_kolom=(3,))
        ws.row_dimensions[r].height = 14 * max(
            2, _tinggi(rum, 72), _tinggi(arti, 50))
        r += 1
    r += 1
    s = ws.cell(r, 1, "Tanda $ pada $AI$2 WAJIB ada. Tanpa $, rumusnya ikut "
                      "bergeser saat disalin ke bawah dan akan menunjuk sel "
                      "yang salah.")
    s.font = MERAH
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    ws.sheet_view.showGridLines = False

    ws = wb.create_sheet("HASIL PENGUJIAN")
    ws.cell(1, 1, "BUKTI: SUDAH DIUJI DI GOOGLE SHEETS, BUKAN DARI INGATAN").font = Font(bold=True, size=14)
    ws.cell(2, 1, "Diuji 22 Oktober 2026 di spreadsheet sungguhan, "
                  "lalu spreadsheet ujinya dihapus.").font = Font(italic=True, size=10, color="666666")
    _hdr(ws, [("YANG DIUJI", 34), ("RUMUS UJINYA", 46),
              ("HASILNYA", 18), ("KESIMPULAN", 46)], baris=4)
    r = 5
    for a, b, c, d in UJI:
        _isi(ws, r, [a, b, c, d], mono_kolom=(2,))
        if "RUSAK" in d or "JELEK" in d:
            for i in (1, 3, 4):
                ws.cell(r, i).font = MERAH
        ws.row_dimensions[r].height = 14 * max(
            2, _tinggi(b, 46), _tinggi(d, 46))
        r += 1
    ws.sheet_view.showGridLines = False

    ws = wb.create_sheet("HATI-HATI")
    ws.cell(1, 1, "ENAM HAL YANG PALING MUDAH SALAH").font = Font(bold=True, size=14)
    _hdr(ws, [("NO", 5), ("HAL", 48), ("KENAPA BERBAHAYA", 86)], baris=3)
    r = 4
    for i, (a, b) in enumerate(HATI, start=1):
        _isi(ws, r, [i, a, b])
        ws.cell(r, 2).font = Font(bold=True, size=10, color="C00000")
        ws.row_dimensions[r].height = 14 * max(
            2, _tinggi(a, 48), _tinggi(b, 86))
        r += 1
    ws.sheet_view.showGridLines = False

    out = AKAR / "keluaran/PANDUAN_DROPDOWN_DISKON.xlsx"
    out.parent.mkdir(exist_ok=True)
    wb.save(out)
    print(f"{out}  ({out.stat().st_size} byte, {len(wb.worksheets)} lembar)")


if __name__ == "__main__":
    main()
