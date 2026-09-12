"""Tes pencocokan nama tab ke master customer."""
from hp_dokumen.konfigurasi import Customer, DaftarCustomer, pecah_nama_tab


def buat(*kunci):
    return DaftarCustomer([
        Customer(k, f"PT {k}", "alamat", "", "per_artikel", 30, "", "", "") for k in kunci
    ])


def test_pecah_nama_tab():
    assert pecah_nama_tab("PO 13 Agustus 2026 - Dunia Bayi") == ((13, 8, 2026), "Dunia Bayi")
    assert pecah_nama_tab("PO 31 Agustus - Haritsa") == ((31, 8, None), "Haritsa")
    assert pecah_nama_tab("Harga Retail") == (None, "Harga Retail")


def test_tanda_kurung_diabaikan():
    d = buat("Katamama Tapos", "Katamama Cikarang")
    assert d.cari("PO 24 Agustus - Katamama (Tapos)").kunci == "Katamama Tapos"


def test_nama_tab_terpotong_31_huruf():
    """Ekspor Excel memotong nama tab jadi 31 huruf."""
    d = buat("Baby Wise", "Baby Wise Surabaya", "Canina Baby", "Katamama Cikarang")
    assert d.cari("PO 31 Agustus - Baby Wise (Sura").kunci == "Baby Wise Surabaya"
    assert d.cari("PO 13 Agustus 2026 - Canina Bab").kunci == "Canina Baby"
    assert d.cari("PO 22 Agustus - Katamama (Cikar").kunci == "Katamama Cikarang"


def test_nama_persis_menang_atas_awalan():
    """'Baby Wise' tidak boleh tertukar dengan 'Baby Wise Surabaya'."""
    d = buat("Baby Wise", "Baby Wise Surabaya")
    assert d.cari("PO 31 Agustus - Baby Wise").kunci == "Baby Wise"


def test_ampersand_dan_spasi():
    d = buat("Panda & Bear")
    assert d.cari("PO 25 Agustus - Panda & Bear").kunci == "Panda & Bear"


def test_tab_tak_dikenal_mengembalikan_none():
    assert buat("Haritsa").cari("PO 01 Januari - Toko Baru") is None


def test_kekurangan_data_terdeteksi():
    c = Customer("X", "", "", "", "per_artikel", 30, "", "", "")
    assert set(c.kekurangan()) == {"nama di dokumen", "alamat", "NPWP"}


def test_requirements_memuat_komponen_google():
    """requirements.txt WAJIB memuat komponen Google.

    Pernah terlewat: berkasnya hanya berisi openpyxl dan PyYAML, sehingga
    `jalankan.py periksa-bot` di komputer baru berhenti dengan
    "No module named 'google'" walaupun pemasangan sudah dijalankan benar.
    """
    from hp_dokumen.konfigurasi import AKAR

    isi = (AKAR / "requirements.txt").read_text(encoding="utf-8").lower()
    for paket in ("google-api-python-client", "google-auth", "openpyxl", "pyyaml"):
        assert paket in isi, f"{paket} tidak ada di requirements.txt"


def test_semua_impor_pihak_ketiga_ada_di_requirements():
    """Tiap paket luar yang diimpor program harus tercantum di requirements."""
    import re
    from hp_dokumen.konfigurasi import AKAR

    peta = {                      # nama saat diimpor -> nama saat dipasang
        "openpyxl": "openpyxl",
        "yaml": "pyyaml",
        "google": "google-auth",
        "googleapiclient": "google-api-python-client",
    }
    isi = (AKAR / "requirements.txt").read_text(encoding="utf-8").lower()
    dipakai = set()
    for berkas in (AKAR / "src").rglob("*.py"):
        for baris in berkas.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*(?:from|import)\s+([a-zA-Z_][\w]*)", baris)
            if m and m.group(1) in peta:
                dipakai.add(peta[m.group(1)])
    kurang = [p for p in sorted(dipakai) if p not in isi]
    assert not kurang, f"diimpor program tapi tidak ada di requirements.txt: {kurang}"
