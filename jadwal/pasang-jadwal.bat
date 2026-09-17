@echo off
REM ============================================================
REM  Memasang jadwal bot tiap 12 jam di Windows Task Scheduler.
REM
REM  CARA PAKAI: klik KANAN berkas ini, pilih "Run as administrator".
REM  Jadwalnya: jam 06:00 dan 18:00 setiap hari.
REM ============================================================

set "NAMA=Sapu Order Sheet Happy Pumpkin"
set "SKRIP=%~dp0sapu.bat"

echo.
echo ============================================================
echo  MEMASANG JADWAL BOT HAPPY PUMPKIN
echo ============================================================
echo.
echo  Nama jadwal : %NAMA%
echo  Menjalankan : %SKRIP%
echo  Setiap      : 12 jam, mulai jam 06:00
echo.

if not exist "%SKRIP%" (
    echo  GAGAL: sapu.bat tidak ketemu di folder yang sama dengan berkas ini.
    echo  Pastikan seluruh isi folder jadwal\ ikut terekstrak.
    echo.
    pause
    exit /b 1
)

REM /IT = jalan HANYA kalau Bapak sedang login.
REM      Ini WAJIB. Kalau bot jalan saat belum login, drive G: dari Google
REM      Drive for Desktop belum ada, dan dokumennya gagal ditulis.
REM /F  = timpa jadwal lama kalau sudah pernah dipasang.
schtasks /Create /TN "%NAMA%" /TR "\"%SKRIP%\"" /SC HOURLY /MO 12 /ST 06:00 /RU "%USERNAME%" /IT /F

if errorlevel 1 goto :gagal

echo.
echo ============================================================
echo  JADWAL BERHASIL DIPASANG
echo ============================================================
echo.
echo  Bot jalan sendiri jam 06:00 dan 18:00 setiap hari, selama
echo  komputer menyala dan Bapak sedang login.
echo.
echo  Mau mencoba sekarang tanpa menunggu jamnya? Jalankan:
echo      schtasks /Run /TN "%NAMA%"
echo.
echo  Catatan hasil tiap sapuan ada di:
echo      keluaran\sapuan\log-sapuan.txt
echo.
pause
exit /b 0

:gagal
echo.
echo ============================================================
echo  GAGAL MEMASANG JADWAL
echo ============================================================
echo.
echo  Dua sebab yang paling sering:
echo.
echo  1. Berkas ini tidak dijalankan sebagai Administrator.
echo     Tutup jendela ini, klik KANAN pasang-jadwal.bat,
echo     lalu pilih "Run as administrator".
echo.
echo  2. Windows meminta password. Kalau itu yang terjadi, pasang
echo     lewat Task Scheduler secara manual - langkahnya ada di
echo     PANDUAN_BOT.md bagian "Kalau pasang-jadwal.bat gagal".
echo.
pause
exit /b 1
