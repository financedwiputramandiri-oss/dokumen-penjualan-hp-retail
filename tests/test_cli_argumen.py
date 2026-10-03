"""Tes susunan argumen baris perintah.

Satu cacat pernah lolos ke tangan Yosua: sub-perintah `faktur-pajak` punya
`--berkas` sendiri, yang menimpa `--berkas` milik perintah induk dengan None.
Akibatnya

    jalankan.py --berkas "order sheet Juli.xlsx" faktur-pajak

diam-diam membaca data/order_sheet.xlsx (bulan lain) dan tetap melaporkan
"berhasil". Faktur pajak bulan yang salah adalah kesalahan yang mahal, jadi
bentuknya dikunci di sini.
"""
from hp_dokumen.cli import buat_parser

# Argumen milik perintah induk. Sub-perintah tidak boleh punya nama yang sama,
# sebab argparse memakai satu namespace: yang belakangan selalu menang.
ARGUMEN_INDUK = {"--berkas", "--tahun"}


def _sub_parser(parser):
    """Semua sub-perintah beserta namanya."""
    for aksi in parser._actions:
        if hasattr(aksi, "choices") and isinstance(aksi.choices, dict):
            yield from aksi.choices.items()


def test_sub_perintah_tidak_menimpa_argumen_induk():
    parser = buat_parser()
    for nama, sub in _sub_parser(parser):
        milik_sub = {s for a in sub._actions for s in a.option_strings}
        bentrok = milik_sub & ARGUMEN_INDUK
        assert not bentrok, (
            f"Sub-perintah '{nama}' mendeklarasikan {sorted(bentrok)}, "
            "padahal itu argumen perintah induk. Argparse akan menimpanya "
            "dengan None dan berkas yang dibaca jadi salah."
        )


def test_berkas_tetap_terbaca_di_setiap_sub_perintah():
    """--berkas di depan harus sampai ke semua sub-perintah."""
    parser = buat_parser()
    for nama, sub in _sub_parser(parser):
        # sebagian sub-perintah butuh satu kata (nama PO), sebagian tidak
        wajib = [a for a in sub._actions if not a.option_strings and a.nargs is None]
        args = parser.parse_args(
            ["--berkas", "juli.xlsx", nama] + ["Panda"] * len(wajib))
        assert args.berkas == "juli.xlsx", (
            f"'{nama}' kehilangan nilai --berkas."
        )
