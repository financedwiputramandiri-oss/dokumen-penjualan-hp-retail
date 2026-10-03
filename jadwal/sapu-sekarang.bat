@echo off
REM ============================================================
REM  MENYAPU ORDER SHEET SEKARANG JUGA.
REM
REM  Klik dua kali berkas ini kapan pun order sheet baru direvisi
REM  dan dokumennya dibutuhkan cepat - tidak perlu menunggu jadwal
REM  jam 06:00 atau 18:00, dan tidak perlu menyentuh Task Scheduler.
REM
REM  HANYA MENYAPU ORDER SHEET BULAN INI (--bulan-ini).
REM  Itu yang membuatnya cepat: order sheet bulan-bulan lama sudah
REM  selesai dan tidak akan berubah lagi, jadi tidak perlu dibuka.
REM  Sapuan terjadwal jam 06:00 dan 18:00 tetap membaca SEMUA bulan,
REM  jadi tidak ada yang terlewat.
REM
REM  Kalau perlu menyapu SEMUA bulan sekarang juga, pakai
REM  sapu-semua-bulan.bat di folder yang sama.
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
echo  MENYAPU ORDER SHEET BULAN INI SEKARANG
echo ============================================================
echo.
echo  Hanya order sheet bulan berjalan yang dibaca, supaya invoice
echo  dan surat jalan cepat jadi. Order sheet bulan lain tetap
echo  disapu otomatis jam 06:00 dan 18:00.
echo.

REM Kunci yang sama dipakai sapuan terjadwal, supaya sapuan manual dan
REM sapuan terjadwal tidak pernah berjalan bersamaan lalu saling menimpa
REM data\kondisi_sapu.json.
REM
REM Kunci ini hanya berlaku di KOMPUTER INI. Kalau bot dipasang di
REM beberapa komputer, yang menahannya adalah kunci bersama di sheet
REM OTOMATISASI (tab BOT_KUNCI) - diurus sendiri oleh jalankan.py.
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
echo MULAI (manual, bulan ini saja) %DATE% %TIME% >> "%LOG%"
echo ============================================================ >> "%LOG%"

REM Keluarannya ke layar DAN ke log sekaligus.
py jalankan.py sapu --bulan-ini 2>&1
set KODE=%ERRORLEVEL%
echo SELESAI (manual) %DATE% %TIME% - kode %KODE% >> "%LOG%"
goto :eof
