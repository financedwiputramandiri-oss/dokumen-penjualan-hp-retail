"""Tes berkas penjadwal Windows di folder `jadwal/`.

Berkas .bat tidak bisa dijalankan dari sini, jadi yang dikunci adalah
hal-hal yang kalau salah membuat bot diam-diam tidak jalan — dan
kegagalannya baru ketahuan berminggu-minggu kemudian, saat orang sadar
dokumennya tidak pernah muncul.
"""
from pathlib import Path

import pytest

JADWAL = Path(__file__).resolve().parent.parent / "jadwal"
SAPU = JADWAL / "sapu.bat"
PASANG = JADWAL / "pasang-jadwal.bat"
HAPUS = JADWAL / "hapus-jadwal.bat"
SEMUA_BAT = [SAPU, PASANG, HAPUS]


def test_ketiga_berkas_bat_ada():
    for berkas in SEMUA_BAT:
        assert berkas.exists(), f"{berkas.name} hilang dari folder jadwal/"


def test_sapu_bat_pindah_ke_folder_proyek():
    """Tanpa `cd /d "%~dp0.."` Task Scheduler jalan dari C:\\Windows\\System32.

    Python tidak akan menemukan jalankan.py di sana, dan tugasnya gagal
    diam-diam tiap 12 jam. Ini persis jenis masalah yang menyandung
    pemasangan di device baru (CLAUDE.md bagian 25).
    """
    isi = SAPU.read_text(encoding="ascii")
    assert 'cd /d "%~dp0.."' in isi


def test_sapu_bat_mencatat_hasilnya_ke_log():
    """Sapuan terjadwal tidak ada yang menonton layarnya.

    Kalau keluarannya tidak ditulis ke berkas, kegagalan bot tidak
    meninggalkan jejak apa pun.
    """
    isi = SAPU.read_text(encoding="ascii")
    assert "log-sapuan.txt" in isi
    assert "jalankan.py sapu >>" in isi
    assert "2>&1" in isi, "galat harus ikut tercatat, bukan cuma keluaran biasa"


def test_pasang_jadwal_memakai_IT():
    """/IT membuat tugas jalan HANYA saat penggunanya login.

    Ini wajib: `folder_draf` menunjuk ke G:\\My Drive\\... milik Google
    Drive for Desktop, dan drive itu tidak ada sebelum orangnya login.
    Tanpa /IT bot jalan di ruang hampa dan semua dokumennya gagal ditulis.
    """
    isi = PASANG.read_text(encoding="ascii")
    assert " /IT " in isi or isi.rstrip().endswith("/IT")


def test_pasang_jadwal_hari_kerja_tiap_10_menit():
    """Senin-Sabtu, 08:00-17:00, tiap 10 menit (permintaan Yosua 18 Sep 2026).

    Kelima bagiannya harus lengkap. Kalau `/ET` atau `/K` hilang, bot terus
    menyapu sepanjang malam; kalau `/D` hilang, ikut jalan hari Minggu.
    """
    isi = PASANG.read_text(encoding="ascii")
    assert "/SC WEEKLY" in isi
    assert "/D MON,TUE,WED,THU,FRI,SAT" in isi, "Minggu harus libur"
    assert "/ST 08:00" in isi
    assert "/RI 10" in isi
    assert "/ET 17:00" in isi
    assert " /K " in isi, "tanpa /K sapuan yang tersangkut tidak dihentikan"
    assert "SUN" not in isi.upper().replace("SUNDAY", ""), "hari Minggu tidak boleh ikut"


def test_sapu_bat_menolak_sapuan_bertabrakan():
    """Sapuan pertama bisa lebih lama dari 10 menit.

    Kalau dua sapuan jalan bersamaan, keduanya menulis
    data/kondisi_sapu.json dan saling menimpa - dokumen lalu dibuat ulang
    terus-menerus tanpa ada yang sadar. Kuncinya dipegang lewat handle 9,
    yang dilepas Windows sendiri saat prosesnya mati, jadi tidak pernah
    tertinggal menyangkut walau tugasnya dibunuh /K jam 17:00.
    """
    isi = SAPU.read_text(encoding="ascii")
    assert "sapu-sedang-jalan.lock" in isi
    assert '9>"%KUNCI%"' in isi
    assert "DILEWATI" in isi, "sapuan yang dilewati harus tercatat di log"


def test_sapu_bat_memotong_log_yang_kebesaran():
    """330 sapuan per minggu; tanpa pemotongan log-nya tidak bisa dibuka lagi."""
    isi = SAPU.read_text(encoding="ascii")
    assert "%%~zA GTR" in isi
    assert "log-sapuan.txt.lama" in isi or '"%LOG%.lama"' in isi


def test_nama_jadwal_sama_di_pasang_dan_hapus():
    """Kalau namanya beda, hapus-jadwal.bat tidak menghapus apa pun.

    Jadwal lama tetap hidup, dan waktu bot pindah komputer ada DUA bot
    yang menyapu bersamaan lalu saling menimpa kondisi_sapu.json.
    """
    def nama(berkas: Path) -> str:
        for baris in berkas.read_text(encoding="ascii").splitlines():
            if baris.strip().lower().startswith('set "nama='):
                return baris.split("=", 1)[1].rstrip('"')
        pytest.fail(f"{berkas.name} tidak menyetel variabel NAMA")

    assert nama(PASANG) == nama(HAPUS)


@pytest.mark.parametrize("berkas", SEMUA_BAT, ids=lambda b: b.name)
def test_bat_hanya_huruf_ascii_dan_berakhiran_crlf(berkas: Path):
    """Windows membaca .bat memakai codepage lama, bukan UTF-8.

    Satu huruf beraksen saja bisa membuat barisnya salah terbaca. Akhiran
    baris juga harus CRLF — `.gitattributes` menjaganya tetap begitu
    walau repo ini dikerjakan di Linux.
    """
    data = berkas.read_bytes()
    data.decode("ascii")  # gagal kalau ada huruf di luar ASCII
    assert b"\r\n" in data
    assert b"\n" not in data.replace(b"\r\n", b""), "ada baris yang bukan CRLF"


# ---------------------------------------------------- bot di banyak perangkat
def test_kondisi_mencatat_nama_komputer(tmp_path):
    """kondisi_sapu.json harus menyimpan komputer mana yang menyapu terakhir.

    Tanpa ini, bot yang dijalankan bergantian dari laptop dan komputer
    kantor saling menimpa catatannya, dan dokumen dibuat ulang
    terus-menerus tanpa ada yang sadar.
    """
    from hp_dokumen.sapu.kondisi import Kondisi, nama_komputer

    berkas = tmp_path / "kondisi_sapu.json"
    Kondisi().simpan(berkas)
    assert Kondisi.muat(berkas).disapu_oleh == nama_komputer()


def test_peringatan_muncul_kalau_komputernya_berganti(tmp_path):
    from hp_dokumen.sapu.kondisi import Kondisi, peringatan_pindah_komputer

    k = Kondisi()
    k.simpan(tmp_path / "a.json")          # mengisi nama komputer sekarang
    assert peringatan_pindah_komputer(k) == "", "komputer yang sama jangan diperingatkan"

    k.disapu_oleh = "LAPTOP-LAMA-YANG-BUKAN-INI"
    pesan = peringatan_pindah_komputer(k)
    assert "LAPTOP-LAMA-YANG-BUKAN-INI" in pesan
    assert "hapus-jadwal.bat" in pesan, "peringatan harus menyebut cara membereskannya"


def test_catatan_lama_tanpa_nama_komputer_tidak_diperingatkan():
    """kondisi_sapu.json versi lama belum punya kolom itu.

    Pemeriksa tidak boleh menggagalkan sesuatu yang sebenarnya sah - aturan
    yang sama dengan CLAUDE.md bagian 24.
    """
    from hp_dokumen.sapu.kondisi import Kondisi, peringatan_pindah_komputer

    assert peringatan_pindah_komputer(Kondisi(disapu_oleh="")) == ""
