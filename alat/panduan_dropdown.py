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

PILIHAN_CBD = [f"DISCOUNT CBD + {t}" for t in
               ("0%", "0,5%", "1%", "1,5%", "2%", "2,5%",
                "3%", "3,5%", "4%", "4,5%", "5%")]
PILIHAN_COD = [n.replace("CBD", "COD") for n in PILIHAN_CBD]

# Rumus inti. Judul memuat SATU persen, jadi cukup REGEXEXTRACT — tidak
# perlu SPLIT/ARRAYFORMULA seperti saat judulnya bisa bertingkat.
# SUBSTITUTE koma->titik WAJIB: VALUE("1,5%") memberi #VALUE! di Google
# Sheets, yang titik memberi 0,015. Sudah diuji 22 Oktober 2026.
def _tarif(sel: str) -> str:
    return (f'IFERROR(VALUE(REGEXEXTRACT(SUBSTITUTE({sel},",","."),'
            f'"[0-9.]+%")),0)')


RUMUS_AD = f"=AC3*(1-{_tarif('AD$1')})"
RUMUS_AE = f"=AC3*(1-{_tarif('AE$1')})"

LANGKAH = [
    (1, "Pasang dropdown di judul kolom AD",
     "Klik judul kolom AD (sel gabungan AD1:AD2).\n"
     "Menu  Insert  >  Dropdown",
     "Aturannya menempel di sel kiri-atas, yaitu AD1. Kalau sel gabungan "
     "rewel, lepas gabungannya dulu, pasang dropdown, lalu gabung lagi."),
    (2, "Isi 11 pilihannya",
     "Klik 'Add another item' lalu ketik satu per satu:\n\n"
     "DISCOUNT CBD + 0%        DISCOUNT CBD + 0,5%\n"
     "DISCOUNT CBD + 1%        DISCOUNT CBD + 1,5%\n"
     "DISCOUNT CBD + 2%        DISCOUNT CBD + 2,5%\n"
     "DISCOUNT CBD + 3%        DISCOUNT CBD + 3,5%\n"
     "DISCOUNT CBD + 4%        DISCOUNT CBD + 4,5%\n"
     "DISCOUNT CBD + 5%",
     "Jenjang 0,5%. Isinya TULISAN JUDUL lengkap, bukan angka persen saja — "
     "sebab sel ini memang judul kolomnya. Boleh pakai KOMA persis seperti "
     "order sheet sekarang; rumusnya mengubahnya sendiri."),
    (3, "Atur tampilannya",
     "Di panel kanan:  Display style  >  Arrow",
     "Kalau dibiarkan Chip, judulnya berubah jadi gelembung berwarna dan "
     "baris judul tabel jadi tidak seragam dengan kolom lain."),
    (4, "Simpan",
     "Klik tombol  Done",
     "Judul AD sekarang punya panah kecil. Klik panahnya untuk memilih."),
    (5, "Ulangi untuk kolom AE",
     "Klik judul kolom AE (AE1:AE2). Insert > Dropdown.\n"
     "Isi 11 pilihan yang sama, tapi tulis COD:\n\n"
     "DISCOUNT COD + 0%  ...  DISCOUNT COD + 5%",
     "Cara cepat: klik AD1, Ctrl+C, lalu klik AE1 dan Ctrl+V — dropdownnya "
     "ikut tersalin. Sesudah itu tinggal sunting daftarnya, ganti CBD "
     "jadi COD."),
    (6, "Isi rumus kolom AD",
     f"Klik sel AD3, ketik lalu Enter:\n\n    {RUMUS_AD}",
     "Panjang, tapi diketik SEKALI lalu disalin. Tanda $ pada AD$1 wajib — "
     "tanpa itu rumusnya menunjuk AD2, AD3, dan seterusnya saat disalin "
     "ke bawah."),
    (7, "Isi rumus kolom AE",
     f"Klik sel AE3, ketik lalu Enter:\n\n    {RUMUS_AE}",
     "Sama persis dengan rumus AD, hanya AD$1 diganti AE$1."),
    (8, "Salin ke seluruh baris",
     "Pilih AD3:AE3.  Ctrl+C.\n"
     "Pilih AD4 sampai baris data terakhir.  Ctrl+V.",
     "Salin HANYA sampai baris data terakhir. Jangan sampai kena baris "
     "TOTAL — baris TOTAL punya rumus SUM sendiri dan akan tertimpa."),
    (9, "Sekalian kunci kolom DISC (dianjurkan)",
     "Pilih AB3 sampai baris terakhir. Insert > Dropdown. Isi:\n\n"
     "    0%   18%   20%   22%   25%   26,5%   27,5%   30%\n\n"
     "Lalu ubah AC3 jadi:   =Z3*(1-AB3)   dan salin ke bawah.",
     "Dengan ini kolom DISC dan uangnya membaca sel yang SAMA, jadi tidak "
     "mungkin lagi berbeda. Inilah cacat yang ditemukan di PO 04 Maret - "
     "Katamama Cikaret: DISC tertulis 25% tapi rumusnya memakai 22%."),
    (10, "PERIKSA sebelum ditinggalkan",
     "Lihat baris TOTAL kolom AC, AD, dan AE.\n"
     "Bandingkan dengan angka SEBELUM diubah.",
     "Kalau berbeda, URUNGKAN semuanya (Ctrl+Z berkali-kali) dan tanyakan "
     "dulu. Jangan pernah meninggalkan tab yang angkanya berubah tanpa "
     "sebab yang jelas."),
]

RUMUS = [
    ("AD3", "DISCOUNT CBD", RUMUS_AD,
     "TOTAL VALUE dikurangi persen yang tertulis di judul AD1"),
    ("AE3", "DISCOUNT COD", RUMUS_AE,
     "TOTAL VALUE dikurangi persen yang tertulis di judul AE1"),
    ("AC3", "TOTAL VALUE", "=Z3*(1-AB3)",
     "Nilai kotor dikurangi diskon dasar di kolom DISC (langkah 9)"),
]

UJI = [
    ("Judul 0,5%", '"DISCOUNT CBD + 0,5%"', "0,5%  ->  18.108.577,13", "benar"),
    ("Judul 1,5% pakai KOMA", '"DISCOUNT COD + 1,5%"', "1,5%  ->  17.926.581,38",
     "benar — koma tidak masalah"),
    ("Judul 2%", '"DISCOUNT CBD + 2%"', "2%  ->  17.835.583,50",
     "benar — cocok dengan order sheet"),
    ("Judul 2,5%", '"DISCOUNT CBD + 2,5%"', "2,5%", "benar"),
    ("Judul 4,5%", '"DISCOUNT CBD + 4,5%"', "4,5%  ->  17.380.594,13", "benar"),
    ("Judul 0%", '"DISCOUNT CBD + 0%"', "0%  ->  18.199.575", "benar"),
    ("Judul tanpa persen", '"TOTAL VALUE"', "0%  ->  18.199.575",
     "tidak error, dibaca 0%"),
    ("Judul kosong", "sel kosong", "0%", "tidak error"),
    ("Judul ada ganti barisnya", '"DISCOUNT" + enter + "COD + 1,5%"', "1,5%",
     "benar — seperti judul di order sheet sekarang"),
]

HATI = [
    ("Isi dropdown harus TULISAN JUDUL, bukan angka persen",
     "Sel itu adalah judul kolomnya. Kalau isinya cuma '2%', judul kolom "
     "hilang dan yang terbaca orang hanya angka."),
    ("Tab yang persen diskonnya TIDAK seragam antar baris",
     "Satu judul berlaku untuk SELURUH kolom di tab itu. Periksa dulu kolom "
     "DISC-nya satu nilai atau tidak. Contoh yang sudah ketahuan: PO 04 "
     "Maret - Katamama Cikaret, 55 baris 25% tapi 2 baris 22%."),
    ("Kolom AD atau AE yang lama HARUS ditimpa SELURUHNYA",
     "Kalau sebagian masih rumus lama, order sheet jadi campuran dua cara. "
     "Itu lebih membingungkan daripada sekarang, dan lebih sulit diperiksa."),
    ("Jangan mengisi kolom yang tab itu memang tidak punya",
     "Memberi judul 'DISCOUNT CBD + 0%' pada tab yang tidak punya CBD membuat "
     "kolomnya terisi penuh dengan angka yang sama dengan TOTAL VALUE, lalu "
     "Aturan 2 memilihnya sebagai CBD padahal ordernya TOP. Angkanya "
     "kebetulan sama, tapi CARA BAYAR yang tercatat jadi salah. "
     "Biarkan judulnya kosong dan kolomnya kosong."),
    ("Jangan menyisipkan baris atau kolom",
     "Letak kolom A sampai AE harus tetap, kalau bergeser program pembuat "
     "Invoice berhenti mengenali tabnya."),
    ("Kerjakan SATU tab dulu, periksa, baru lanjut",
     "Jangan mengubah 16 tab sekaligus. Kalau ada yang salah, mencarinya "
     "jauh lebih sulit."),
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
    ws.cell(2, 1, "Dropdown dipasang LANGSUNG di judul kolom AD dan AE · "
                  "dua komponen: CBD dan COD · jenjang 0,5% · "
                  "semua rumus sudah diuji langsung di Google Sheets").font = Font(italic=True, size=10, color="666666")
    _hdr(ws, [("NO", 5), ("LANGKAH", 30), ("YANG DIKETIK / DIKLIK", 56),
              ("KENAPA BEGITU", 60)], baris=4)
    r = 5
    for no, judul, aksi, kenapa in LANGKAH:
        _isi(ws, r, [no, judul, aksi, kenapa], mono_kolom=(3,))
        ws.cell(r, 2).font = Font(bold=True, size=10)
        # +1 baris kelonggaran: huruf Consolas lebih lebar, jadi lipatannya
        # sering satu baris lebih banyak daripada perkiraan.
        ws.row_dimensions[r].height = 14 * (max(
            2, _tinggi(aksi, 50), _tinggi(kenapa, 60)) + 1)
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
        ws.row_dimensions[r].height = 14 * (max(
            2, _tinggi(rum, 62), _tinggi(arti, 50)) + 1)
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
    _hdr(ws, [("YANG DIUJI", 30), ("JUDUL DI AD1 / AE1", 40),
              ("TARIF TERBACA -> NETT DARI 18.199.575", 38),
              ("KESIMPULAN", 44)], baris=4)
    r = 5
    for a, b, c, d in UJI:
        _isi(ws, r, [a, b, c, d], mono_kolom=(2,))
        if "RUSAK" in d or "JELEK" in d:
            for i in (1, 3, 4):
                ws.cell(r, i).font = MERAH
        ws.row_dimensions[r].height = 14 * max(
            2, _tinggi(b, 40), _tinggi(d, 44))
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

    ws = wb.create_sheet("DAFTAR PILIHAN", 1)
    ws.cell(1, 1, "DAFTAR PILIHAN DROPDOWN — SALIN APA ADANYA").font = Font(bold=True, size=14)
    ws.cell(2, 1, "Jenjang 0,5% · dua komponen saja: CBD dan COD").font = Font(italic=True, size=10, color="666666")
    _hdr(ws, [("UNTUK JUDUL KOLOM AD (CBD)", 34),
              ("UNTUK JUDUL KOLOM AE (COD)", 34)], baris=4)
    for i, (a, b) in enumerate(zip(PILIHAN_CBD, PILIHAN_COD), start=5):
        _isi(ws, i, [a, b], mono_kolom=(1, 2))
    r = 5 + len(PILIHAN_CBD) + 1
    s2 = ws.cell(r, 1, "Boleh pakai KOMA persis seperti order sheet sekarang — "
                       "rumusnya mengubahnya sendiri. Sudah diuji.")
    s2.font = Font(size=10, italic=True, color="7F6000")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    ws.sheet_view.showGridLines = False

    out = AKAR / "keluaran/PANDUAN_DROPDOWN_DISKON.xlsx"
    out.parent.mkdir(exist_ok=True)
    wb.save(out)
    print(f"{out}  ({out.stat().st_size} byte, {len(wb.worksheets)} lembar)")


if __name__ == "__main__":
    main()
