@echo off
REM ============================================================
REM  Menghapus jadwal bot dari Task Scheduler.
REM
REM  WAJIB dijalankan di komputer LAMA kalau bot dipindahkan ke
REM  komputer baru. Dua bot yang menyapu bersamaan akan saling
REM  menimpa kondisi_sapu.json dan laporannya jadi kacau.
REM
REM  Jadwalnya ADA DUA (Pagi dan Sore), jadi dua-duanya dihapus.
REM ============================================================

set "NAMA=Sapu Order Sheet Happy Pumpkin"

echo.
echo  Menghapus jadwal: %NAMA% - Pagi dan - Sore
echo.

schtasks /Delete /TN "%NAMA% - Pagi" /F
schtasks /Delete /TN "%NAMA% - Sore" /F

REM Jadwal versi lama (satu tugas berulang) kalau masih tertinggal.
schtasks /Delete /TN "%NAMA%" /F 2>nul

echo.
echo  Selesai. Kalau ada baris "ERROR: The system cannot find the file
echo  specified", artinya jadwal itu memang belum pernah dipasang di
echo  komputer ini - bukan masalah.
echo.
pause
