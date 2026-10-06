@echo off
REM ============================================================
REM  Menjalankan sapuan order sheet Happy Pumpkin.
REM  Berkas ini yang dipanggil Task Scheduler dua kali sehari,
REM  jam 08:00 dan 17:00, Senin sampai Sabtu.
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
REM  Tiap sapuan menambah satu blok catatan, dan selama setahun itu
REM  menumpuk sampai berkasnya tidak bisa dibuka lagi. Pemotongan ini
REM  JANGAN dihapus walau jadwalnya sekarang cuma dua kali sehari -
REM  sapuan manual ikut menulis ke berkas yang sama.
REM ------------------------------------------------------------
if exist "%LOG%" for %%A in ("%LOG%") do if %%~zA GTR 5000000 move /Y "%LOG%" "%LOG%.lama" >nul

REM ------------------------------------------------------------
REM  KUNCI ANTAR-SAPUAN.
REM  Sapuan bisa makan waktu beberapa menit, jadi sapuan manual bisa
REM  dimulai saat yang terjadwal belum selesai. Dua sapuan
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

py jalankan.py sapu --minggu-ini >> "%LOG%" 2>&1
set KODE=%ERRORLEVEL%

echo. >> "%LOG%"
if "%KODE%"=="0" (
    echo SELESAI %DATE% %TIME% - berhasil >> "%LOG%"
) else (
    echo SELESAI %DATE% %TIME% - GAGAL, kode %KODE% >> "%LOG%"
)
goto :eof
