@echo off
REM ============================================================
REM  Menjalankan sapuan order sheet Happy Pumpkin.
REM  Berkas ini yang dipanggil Task Scheduler tiap 12 jam.
REM
REM  Boleh juga diklik dua kali kalau mau menyapu sekarang juga.
REM ============================================================

REM Pindah ke folder proyek. %~dp0 adalah folder tempat berkas ini berada
REM (...\dokumen-penjualan-hp-retail\jadwal\), jadi ".." naik satu tingkat.
REM Ini penting: tanpa baris ini Task Scheduler menjalankan perintah dari
REM C:\Windows\System32 dan Python tidak akan menemukan jalankan.py.
cd /d "%~dp0.."

set "LOG=%CD%\keluaran\sapuan\log-sapuan.txt"
if not exist "%CD%\keluaran\sapuan" mkdir "%CD%\keluaran\sapuan"

echo. >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo MULAI  %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

py jalankan.py sapu >> "%LOG%" 2>&1
set KODE=%ERRORLEVEL%

echo. >> "%LOG%"
if "%KODE%"=="0" (
    echo SELESAI %DATE% %TIME% - berhasil >> "%LOG%"
) else (
    echo SELESAI %DATE% %TIME% - GAGAL, kode %KODE% >> "%LOG%"
)

exit /b %KODE%
