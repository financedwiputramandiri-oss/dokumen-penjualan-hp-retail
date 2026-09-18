@echo off
REM ============================================================
REM  Menjalankan sapuan order sheet Happy Pumpkin.
REM  Berkas ini yang dipanggil Task Scheduler tiap 10 menit
REM  pada hari kerja Senin-Sabtu jam 08:00-17:00.
REM
REM  Boleh juga diklik dua kali kalau mau menyapu sekarang juga.
REM ============================================================

REM Pindah ke folder proyek. %~dp0 adalah folder tempat berkas ini berada
REM (...\dokumen-penjualan-hp-retail\jadwal\), jadi ".." naik satu tingkat.
REM Ini penting: tanpa baris ini Task Scheduler menjalankan perintah dari
REM C:\Windows\System32 dan Python tidak akan menemukan jalankan.py.
cd /d "%~dp0.."

set "LOG=%CD%\keluaran\sapuan\log-sapuan.txt"
set "KUNCI=%CD%\data\sapu-sedang-jalan.lock"
if not exist "%CD%\keluaran\sapuan" mkdir "%CD%\keluaran\sapuan"
if not exist "%CD%\data" mkdir "%CD%\data"

REM ------------------------------------------------------------
REM  Log dipotong kalau sudah lewat 5 MB.
REM  Pada jadwal 10 menit ada sekitar 330 sapuan per minggu; tanpa ini
REM  log-sapuan.txt tumbuh terus sampai tidak bisa dibuka lagi.
REM ------------------------------------------------------------
if exist "%LOG%" for %%A in ("%LOG%") do if %%~zA GTR 5000000 move /Y "%LOG%" "%LOG%.lama" >nul

REM ------------------------------------------------------------
REM  KUNCI ANTAR-SAPUAN.
REM  Sapuan pertama bisa makan waktu lebih dari 10 menit, jadi sapuan
REM  berikutnya sudah dimulai sebelum yang ini selesai. Dua sapuan
REM  bersamaan saling menimpa data\kondisi_sapu.json, dan akibatnya
REM  dokumen dibuat ulang terus-menerus tanpa ada yang sadar.
REM
REM  Berkas kunci dipegang lewat handle 9. Windows mengunci berkas itu
REM  selama proses hidup, dan MELEPASKANNYA SENDIRI begitu proses mati -
REM  termasuk kalau Task Scheduler membunuhnya jam 17:00 (/ET /K).
REM  Karena itu kuncinya tidak pernah tertinggal menyangkut.
REM ------------------------------------------------------------
2>nul (
    9>"%KUNCI%" (
        call :sapu
    )
) || (
    echo. >> "%LOG%"
    echo DILEWATI %DATE% %TIME% - masih ada sapuan yang berjalan >> "%LOG%"
    exit /b 0
)

exit /b %KODE%

:sapu
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
goto :eof
