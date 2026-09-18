@echo off
REM ============================================================
REM  MENYAPU ORDER SHEET SEKARANG JUGA.
REM
REM  Klik dua kali berkas ini kapan pun order sheet baru direvisi
REM  dan dokumennya dibutuhkan cepat - tidak perlu menunggu jadwal
REM  jam 08:00 atau 14:00, dan tidak perlu menyentuh Task Scheduler.
REM
REM  Bedanya dengan sapu.bat: hasilnya ditampilkan DI LAYAR supaya
REM  Bapak bisa melihat jalannya, bukan hanya masuk ke berkas log.
REM ============================================================

cd /d "%~dp0.."

set "LOG=%CD%\keluaran\sapuan\log-sapuan.txt"
set "KUNCI=%CD%\data\sapu-sedang-jalan.lock"
if not exist "%CD%\keluaran\sapuan" mkdir "%CD%\keluaran\sapuan"
if not exist "%CD%\data" mkdir "%CD%\data"

echo.
echo ============================================================
echo  MENYAPU ORDER SHEET SEKARANG
echo ============================================================
echo.
echo  Sapuan pertama bisa makan waktu beberapa menit karena semua
echo  order sheet dibaca. Sapuan berikutnya jauh lebih cepat -
echo  order sheet yang tidak berubah dilewati begitu saja.
echo.

REM Kunci yang sama dipakai sapuan terjadwal, supaya sapuan manual dan
REM sapuan terjadwal tidak pernah berjalan bersamaan lalu saling menimpa
REM data\kondisi_sapu.json.
2>nul (
    9>"%KUNCI%" (
        call :sapu
    )
) || (
    echo.
    echo  DILEWATI: sapuan terjadwal sedang berjalan.
    echo  Tunggu sebentar, lalu klik dua kali berkas ini lagi.
    echo.
    pause
    exit /b 0
)

echo.
if "%KODE%"=="0" (
    echo  SELESAI - sapuan berhasil.
) else (
    echo  SELESAI - GAGAL, kode %KODE%.
    echo  Catatan lengkapnya ada di:
    echo      keluaran\sapuan\log-sapuan.txt
)
echo.
pause
exit /b %KODE%

:sapu
echo. >> "%LOG%"
echo ============================================================ >> "%LOG%"
echo MULAI (manual) %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

REM Keluarannya ke layar DAN ke log sekaligus.
py jalankan.py sapu 2>&1
set KODE=%ERRORLEVEL%
echo SELESAI (manual) %DATE% %TIME% - kode %KODE% >> "%LOG%"
goto :eof
