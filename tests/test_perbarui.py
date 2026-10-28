"""Bot memperbarui kodenya sendiri.

Yang paling berbahaya dari pembaruan otomatis bukan kegagalannya,
melainkan KEBERHASILANNYA menimpa pengaturan orang. Tes di sini menjaga
tiga hal itu: pengaturan tidak pernah tertimpa, kegagalan tidak pernah
menghentikan sapuan, dan folder proyek tidak pernah berisi setengah versi.
"""
import io
import zipfile
from pathlib import Path

import pytest

from alat import perbarui as P

AKAR = Path(__file__).resolve().parent.parent


def _zip(isi: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for nama, teks in isi.items():
            z.writestr(f"repo-cabang/{nama}", teks)
    return buf.getvalue()


def _proyek(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "config/bot.yaml").write_text("folder_draf: G:/punya Yosua\n")
    (tmp_path / "config/customer.csv").write_text("nama,alamat\nA,B\n")
    (tmp_path / "data/kondisi_sapu.json").write_text("{}")
    (tmp_path / "src/lama.py").write_text("versi lama\n")
    return tmp_path


@pytest.mark.parametrize("jalur", [
    "config/bot.yaml", "config/customer.csv", "config/pengaturan.yaml",
    "config/perusahaan.yaml", "config/kredensial_bot.json",
    "data/kondisi_sapu.json", "data/semua/x.xlsx", "keluaran/INVOICE.xlsx",
])
def test_pengaturan_dan_data_dilindungi(jalur):
    assert P.dilindungi(jalur)


@pytest.mark.parametrize("jalur", [
    "src/hp_dokumen/cli.py", "jadwal/sapu.bat", "config/logo_dpm_kecil.png",
    "CLAUDE.md", "requirements.txt",
])
def test_kode_dan_logo_TIDAK_dilindungi(jalur):
    assert not P.dilindungi(jalur)


def test_pengaturan_yosua_tidak_tertimpa(tmp_path):
    """Cacat bagian 27: bot.yaml bawaan repo membatalkan pengaturannya."""
    akar = _proyek(tmp_path)
    data = _zip({
        "config/bot.yaml": "folder_draf: keluaran/draf\n",   # nilai repo
        "config/customer.csv": "nama,alamat\n",
        "data/kondisi_sapu.json": "{}",
        "src/lama.py": "versi baru\n",
    })
    ok, pesan = P.perbarui(akar, unduh=lambda _u: data)
    assert ok, pesan
    assert (akar / "config/bot.yaml").read_text() == "folder_draf: G:/punya Yosua\n"
    assert (akar / "config/customer.csv").read_text() == "nama,alamat\nA,B\n"
    assert (akar / "src/lama.py").read_text() == "versi baru\n"


def test_berkas_baru_ikut_terpasang(tmp_path):
    akar = _proyek(tmp_path)
    data = _zip({"src/baru.py": "halo\n"})
    ok, _ = P.perbarui(akar, unduh=lambda _u: data)
    assert ok and (akar / "src/baru.py").read_text() == "halo\n"


def test_tanpa_perubahan_dilaporkan_sudah_terbaru(tmp_path):
    akar = _proyek(tmp_path)
    data = _zip({"src/lama.py": "versi lama\n"})
    ok, pesan = P.perbarui(akar, unduh=lambda _u: data)
    assert ok and "sudah yang terbaru" in pesan


def test_gagal_mengunduh_TIDAK_merusak_apa_pun(tmp_path):
    akar = _proyek(tmp_path)

    def meledak(_u):
        raise OSError("jaringan mati")

    ok, pesan = P.perbarui(akar, unduh=meledak)
    assert not ok and "memakai kode yang ada" in pesan
    assert (akar / "src/lama.py").read_text() == "versi lama\n"


def test_zip_rusak_TIDAK_merusak_apa_pun(tmp_path):
    akar = _proyek(tmp_path)
    ok, pesan = P.perbarui(akar, unduh=lambda _u: b"bukan zip")
    assert not ok and "memakai kode yang ada" in pesan
    assert (akar / "src/lama.py").read_text() == "versi lama\n"


def test_main_SELALU_kode_nol_walau_gagal(tmp_path, monkeypatch, capsys):
    """Kegagalan memperbarui tidak boleh menghentikan sapuan."""
    monkeypatch.setattr(P, "perbarui", lambda *a, **k: (False, "jaringan mati"))
    assert P.main() == 0
    assert "DILEWATI" in capsys.readouterr().out


@pytest.mark.parametrize("berkas", ["sapu.bat", "sapu-sekarang.bat",
                                    "sapu-semua-bulan.bat"])
def test_bat_memanggil_pembaru_SEBELUM_menyapu(berkas):
    isi = (AKAR / "jadwal" / berkas).read_text(encoding="ascii")
    assert "alat\\perbarui.py" in isi, "pembaruan tidak dipanggil"
    assert isi.index("alat\\perbarui.py") < isi.index("jalankan.py sapu"), \
        "pembaruan harus dijalankan SEBELUM sapuan, bukan sesudahnya"


def test_cabang_yang_ditarik_sama_dengan_cabang_repo():
    """Kalau cabangnya salah, bot menarik kode orang lain diam-diam."""
    kepala = (AKAR / ".git" / "HEAD").read_text().strip()
    if kepala.startswith("ref: refs/heads/"):
        assert P.CABANG == kepala.split("refs/heads/", 1)[1]
