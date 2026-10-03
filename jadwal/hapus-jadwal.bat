@echo off
REM ============================================================
REM  Menghapus jadwal bot dari Task Scheduler.
REM
REM  WAJIB dijalankan di komputer LAMA kalau bot dipindahkan ke
REM  komputer baru. Dua bot yang menyapu bersamaan akan saling
REM  menimpa kondisi_sapu.json dan laporannya jadi kacau.
REM ============================================================

set "NAMA=Sapu Order Sheet Happy Pumpkin"

echo.
echo  Menghapus jadwal: %NAMA%
echo.

schtasks /Delete /TN "%NAMA%" /F

if errorlevel 1 (
    echo.
    echo  Gagal menghapus. Kemungkinan jadwalnya memang belum pernah
    echo  dipasang di komputer ini, atau perlu "Run as administrator".
) else (
    echo.
    echo  Jadwal sudah dihapus. Bot tidak akan jalan sendiri lagi
    echo  di komputer ini.
)
echo.
pause
