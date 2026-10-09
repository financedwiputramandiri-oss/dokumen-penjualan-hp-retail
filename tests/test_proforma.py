"""Tes Proforma Invoice dan kedua gaya faktur.

Dua hal yang dikunci di sini, keduanya dari permintaan Yosua 17 Sep 2026:

1. Faktur per ukuran (Haritsa, Katamama) memakai template yang BERBEDA dari
   faktur per artikel. Sebelumnya program memakai satu template untuk semua,
   dan itulah yang membuat faktur Katamama terlihat salah.
2. Proforma memuat level VARIAN di kolom KETERANGAN, dan hanya diterbitkan
   untuk customer yang fakturnya dipecah per ukuran.
"""
import pytest
from openpyxl import Workbook

from buat_contoh import buat_contoh
from hp_dokumen.dokumen.invoice import (
    GAYA_PER_ARTIKEL, GAYA_PER_UKURAN, buat_invoice,
)
from hp_dokumen.dokumen.proforma import JUDUL_KOLOM, buat_proforma, keterangan
from hp_dokumen.konfigurasi import Customer, DaftarCustomer, Pengaturan, Perusahaan
from hp_dokumen.nilai_bersih import tentukan_nett
from hp_dokumen.pemindai import baca_order_sheet


@pytest.fixture(scope="module")
def bahan(tmp_path_factory):
    berkas = buat_contoh(tmp_path_factory.mktemp("d") / "contoh.xlsx")
    daftar = DaftarCustomer([
        Customer("Contoh TOP", "PT Contoh Satu", "Jl. Contoh 1", "", "per_artikel", 30, "", "", ""),
        Customer("Contoh CBD", "PT Contoh Dua", "Jl. Contoh 2", "", "per_ukuran", 30, "", "", ""),
    ])
    orders = baca_order_sheet(berkas, daftar, tahun_bawaan=2026)
    perusahaan = Perusahaan(
        kode="DPM", nama="CV CONTOH", nama_resmi="CV. CONTOH", kenakan_ppn=True,
        npwp="01.234.567.8-901.000",
        alamat_baris=["Jl. A No. 1, Kelurahan Contoh", "Kota Contoh - 11460",
                      "Phone. 021", "Email : a@b.c"],
        logo="", rekening=["REKENING:", "BANK X"], kota_penerbitan="Jakarta",
    )
    return orders, daftar, perusahaan, Pengaturan()


def _proforma(bahan):
    orders, daftar, pt, peng = bahan
    o = next(x for x in orders if daftar.cari(x.nama_tab)
             and daftar.cari(x.nama_tab).pecah_per_ukuran)
    ws = Workbook().active
    ringkas = buat_proforma(ws, o, tentukan_nett(o, daftar.cari(o.nama_tab)),
                            daftar.cari(o.nama_tab), pt, peng, "0010826")
    return ws, ringkas, o


def test_kolom_proforma_sesuai_foto(bahan):
    """Sembilan kolom, urutannya persis seperti foto dari Yosua."""
    ws, _, _ = _proforma(bahan)
    diharapkan = [t for _, t in JUDUL_KOLOM]
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, 1).value == "NO":
            nyata = [ws.cell(r, c).value for c in range(1, 10)]
            assert nyata == diharapkan
            return
    pytest.fail("baris judul tabel proforma tidak ketemu")


def test_keterangan_proforma_memuat_varian(bahan):
    """Permintaan inti Yosua: level varian ikut di kolom KETERANGAN."""
    ws, _, _ = _proforma(bahan)
    isi = [str(ws.cell(r, 3).value or "") for r in range(1, ws.max_row + 1)]
    assert any(" - " in x and x.strip() for x in isi), (
        "tidak ada satu pun baris KETERANGAN yang memuat varian"
    )


def test_keterangan_tanpa_warna_tidak_menggantung():
    """Warna kosong tidak boleh meninggalkan tanda hubung menggantung."""
    class B:
        deskripsi, warna = "Kaos Uk. M", ""
    assert keterangan(B()) == "Kaos Uk. M"
    B.warna = "Merah"
    assert keterangan(B()) == "Kaos Uk. M - Merah"


def test_penutup_proforma_konsisten(bahan):
    """Sub Total - Diskon harus sama dengan Grand Total, dan Grand Total = nett."""
    ws, ringkas, _ = _proforma(bahan)
    nilai = {}
    for r in range(1, ws.max_row + 1):
        label = ws.cell(r, 6).value
        if isinstance(label, str) and label.strip():
            nilai[label.strip()] = ws.cell(r, 9).value
    assert abs(nilai["Sub Total"] - ringkas["kotor"]) < 0.5
    assert abs(nilai["Grand Total"] - ringkas["nett"]) < 0.5
    assert abs(nilai["Sub Total"] - nilai["Diskon"] - nilai["Grand Total"]) < 0.5


def test_proforma_hanya_untuk_customer_per_ukuran(bahan, tmp_path):
    """Customer per artikel TIDAK boleh ikut dibuatkan proforma.

    Yosua hanya meminta Haritsa dan Katamama. Menerbitkannya untuk semua
    customer berarti mengirim dokumen yang tidak pernah diminta.
    """
    from hp_dokumen.berkas_dokumen import buat_berkas

    orders, daftar, pt, peng = bahan

    class Cfg:
        customer = daftar
        pengaturan = peng

        class perusahaan:
            @staticmethod
            def untuk(_):
                return pt

    for o in orders:
        cust = daftar.cari(o.nama_tab)
        if cust is None:
            continue
        folder = tmp_path / o.nama_tab.replace(" ", "_")
        berkas = buat_berkas(Cfg(), o, tentukan_nett(o, cust), folder)
        punya = any("PROFORMA" in p.name for p in berkas)
        assert punya == cust.pecah_per_ukuran, (
            f"{o.nama_tab}: proforma={punya}, per_ukuran={cust.pecah_per_ukuran}"
        )


def test_dua_gaya_faktur_benar_benar_berbeda(bahan):
    """Kop faktur per ukuran memakai huruf 16/12, per artikel 18/11.

    Dibongkar dari TIGA faktur asli: 0110826 BABY WISE (per artikel),
    0160826 HARITSA dan 0400826 KATAMAMA (keduanya per ukuran). Haritsa dan
    Katamama sepakat melawan Baby Wise di setiap ukuran huruf.
    """
    orders, daftar, pt, peng = bahan
    hasil = {}
    for kunci, per_ukuran in (("artikel", False), ("ukuran", True)):
        o = next(x for x in orders if daftar.cari(x.nama_tab)
                 and daftar.cari(x.nama_tab).pecah_per_ukuran == per_ukuran)
        cust = daftar.cari(o.nama_tab)
        ws = Workbook().active
        buat_invoice(ws, o, tentukan_nett(o, cust), cust, pt, peng, "0010826")
        hasil[kunci] = ws

    a, u = hasil["artikel"], hasil["ukuran"]
    assert a["C2"].font.size == GAYA_PER_ARTIKEL.ukuran_nama_perusahaan == 18
    assert u["C2"].font.size == GAYA_PER_UKURAN.ukuran_nama_perusahaan == 16
    assert a["A9"].font.size == 18 and u["A9"].font.size == 16
    assert a["A10"].font.size == 18 and u["A10"].font.size == 16
    assert a["C3"].font.bold is False and u["C3"].font.bold is True
    assert a.row_dimensions[15].height == 26.25
    assert u.row_dimensions[15].height == 31.5


def test_alamat_perusahaan_dilipat_tanpa_menelan_baris_kontak():
    """Melipat alamat tidak boleh menggabungkan Phone/Email ke dalam alamat.

    Kalau tertelan, nomor telepon bisa muncul di tengah baris alamat.
    """
    from hp_dokumen.dokumen.gaya import _alamat_perusahaan

    baris = ["Jl. A No. 1, Kelurahan Contoh", "Kota Contoh - 11460",
             "Phone. 021", "Wa:(+62) 0", "Email : a@b.c"]
    hasil = _alamat_perusahaan(baris, 44)
    assert hasil[-3:] == ["Phone. 021", "Wa:(+62) 0", "Email : a@b.c"]
    assert all(len(x) <= 44 for x in hasil[:-3])
    # tanpa batas, tidak ada yang diubah
    assert _alamat_perusahaan(baris, None) == baris


def test_disk_persen_ditulis_seperti_invoice(bahan):
    """DISK% memakai tulisan yang sama dengan invoice, bukan persen efektif.

    Permintaan Yosua 17 September 2026: *"untuk disk% pakai 22% + 1.5% saja"*.
    Sebelumnya kolom ini berisi 23,17 — benar secara aritmetika (22% lalu 1,5%
    beruntun) tapi tidak dikenali customer.
    """
    ws, _, _ = _proforma(bahan)
    judul = next(r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == "NO")
    nilai = ws.cell(judul + 1, 7).value
    assert isinstance(nilai, str) and nilai.endswith("%"), (
        f"DISK% harus tulisan persen, bukan {nilai!r}"
    )


def test_kolom_disk_cukup_lebar_untuk_tulisannya():
    """Kolom DISK% harus muat "22% + 1.5%" — 10 huruf.

    Pada 8,5 satuan tulisannya terpotong jadi "2% + 1.5%" dan terbaca 2%
    bukan 22%. Di dokumen penagihan itu kesalahan yang mahal.
    """
    from hp_dokumen.dokumen.proforma import LEBAR

    assert LEBAR[7] >= len("22% + 1.5%") + 1.5


def test_total_qty_baris_penutup_tabel_yang_penuh(bahan):
    """Baris Total Qty berkotak dari NO sampai kolom QTY, lalu BERHENTI.

    Dua permintaan Yosua 17 September 2026 yang berurutan: pertama tabelnya
    dibuat penuh, lalu bagian kanannya dicoret. Hasil akhirnya kotak berhenti
    di kolom QTY — yang dijumlahkan memang cuma qty, dan kolom UNIT sampai
    JUMLAH kalau ikut digariskan hanya jadi kotak kosong yang terlihat seperti
    baris yang lupa diisi.
    """
    from hp_dokumen.dokumen.proforma import KOL_QTY, KOLOM_TERAKHIR

    ws, ringkas, _ = _proforma(bahan)
    baris = next(r for r in range(1, ws.max_row + 1)
                 if str(ws.cell(r, 1).value or "").startswith("Total Qty"))

    assert ws.cell(baris, 1).alignment.horizontal == "center"
    assert ws.cell(baris, 4).value == ringkas["qty"]

    # Bergaris sampai kolom QTY...
    for kolom in range(1, KOL_QTY + 1):
        sel = ws.cell(baris, kolom)
        for sisi in ("left", "right", "top", "bottom"):
            assert getattr(sel.border, sisi).style, (
                f"baris Total Qty tidak bergaris di kolom {kolom} sisi {sisi}"
            )

    # ...dan tidak boleh ada KOTAK KOSONG di baris itu. Yosua mencoret
    # deretan kotak hampa di kanan angka qty (17 September 2026). Sel yang
    # bergaris di baris ini wajib ada isinya — entah label, angka, atau
    # bagian dari sel gabungan yang berisi.
    digabung = {k for m in ws.merged_cells.ranges for k in m.cells
                if m.min_row <= baris <= m.max_row}
    for kolom in range(KOL_QTY + 1, KOLOM_TERAKHIR + 1):
        sel = ws.cell(baris, kolom)
        bergaris = any(getattr(sel.border, s).style
                       for s in ("left", "right", "top", "bottom"))
        if not bergaris:
            continue
        berisi = sel.value not in (None, "") or (baris, kolom) in digabung
        assert berisi, f"kolom {kolom} di baris Total Qty berkotak tapi kosong"


def test_lebar_proforma_masih_muat_a4(bahan):
    """Jumlah lebar A..I tidak boleh melewati batas yang terbukti muat A4."""
    from hp_dokumen.dokumen.proforma import LEBAR

    assert sum(LEBAR.values()) <= 135.0


def test_penutup_menyambung_tabel_tanpa_pita_kosong(bahan):
    """Blok Sub Total MULAI di baris Total Qty, bukan di bawahnya.

    Kalau diturunkan satu baris, sisi kanan tabel punya pita kosong setinggi
    baris Total Qty dan tabelnya terlihat TERPUTUS antara baris barang
    terakhir dan blok Sub Total. Yosua menandainya 17 September 2026.

    Tinggi barisnya juga dikunci: bawaan Excel +-15 sedangkan baris barang
    28,5, jadi tanpa ini blok penutup terlihat seperti tabel yang berbeda.
    """
    from hp_dokumen.dokumen.proforma import TINGGI_PENUTUP

    ws, _, _ = _proforma(bahan)
    tq = next(r for r in range(1, ws.max_row + 1)
              if str(ws.cell(r, 1).value or "").startswith("Total Qty"))
    assert ws.cell(tq, 6).value == "Sub Total", (
        "Sub Total tidak sebaris dengan Total Qty — sisi kanan tabel terputus"
    )
    akhir = next(r for r in range(tq, ws.max_row + 1)
                 if ws.cell(r, 6).value == "Grand Total")
    for r in range(tq, akhir + 1):
        assert ws.row_dimensions[r].height == TINGGI_PENUTUP, (
            f"tinggi baris {r} belum diseragamkan"
        )


def test_logo_rata_tengah_dengan_tulisan_kepada(bahan, tmp_path):
    """Logo ditengahkan di blok A:B, sejajar dengan tulisan "Kepada".

    Permintaan Yosua 17 September 2026. Tulisan "Kepada" digabung A:B dan rata
    tengah, jadi logonya harus ditengahkan di blok yang sama.

    Versi sebelumnya memakai pergeseran tetap 0,5 cm dan meleset 5 piksel ke
    kiri. Tesnya menghitung ulang letak yang benar, jadi ikut menangkap kalau
    lebar kolom atau ukuran logonya berubah.
    """
    from openpyxl import Workbook
    from openpyxl.utils.units import EMU_to_pixels

    from hp_dokumen.dokumen.proforma import _lebar_kolom_px, buat_proforma

    orders, daftar, pt, peng = bahan
    o = next(x for x in orders if daftar.cari(x.nama_tab)
             and daftar.cari(x.nama_tab).pecah_per_ukuran)

    logo = tmp_path / "logo.png"
    try:
        from PIL import Image as PilImage

        PilImage.new("RGB", (202, 190), "red").save(logo)
    except ImportError:
        pytest.skip("Pillow tidak terpasang")

    class PerusahaanBerlogo:
        def __getattr__(self, nama):
            return getattr(pt, nama)

        @staticmethod
        def berkas_logo():
            return logo

    ws = Workbook().active
    buat_proforma(ws, o, tentukan_nett(o, daftar.cari(o.nama_tab)),
                  daftar.cari(o.nama_tab), PerusahaanBerlogo(), peng, "0010826")

    assert ws._images, "logo tidak terpasang"
    gambar = ws._images[0]
    geser = EMU_to_pixels(gambar.anchor._from.colOff)
    benar = (_lebar_kolom_px(1) + _lebar_kolom_px(2) - gambar.width) / 2
    assert abs(geser - benar) <= 1, (
        f"logo digeser {geser} px, rata tengah seharusnya {benar:.1f} px"
    )
