@echo off
REM ============================================================
REM  Memasang jadwal bot Happy Pumpkin di Windows Task Scheduler.
REM
REM  CARA PAKAI: klik KANAN berkas ini, pilih "Run as administrator".
REM
REM  Jadwalnya: Senin sampai Sabtu, jam 08:00 sampai 17:00,
REM             menyapu setiap 10 menit. Minggu libur.
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
echo  Hari        : Senin, Selasa, Rabu, Kamis, Jumat, Sabtu
echo  Jam         : 08:00 sampai 17:00
echo  Setiap      : 10 menit
echo.

if not exist "%SKRIP%" (
    echo  GAGAL: sapu.bat tidak ketemu di folder yang sama dengan berkas ini.
    echo  Pastikan seluruh isi folder jadwal\ ikut terekstrak.
    echo.
    pause
    exit /b 1
)

REM /SC WEEKLY /D MON..SAT = hanya hari kerja, Minggu dilewati.
REM /ST 08:00              = sapuan pertama tiap harinya.
REM /RI 10                 = diulang tiap 10 menit.
REM /ET 17:00 /K           = berhenti mengulang jam 17:00, dan sapuan yang
REM                          masih berjalan saat itu dihentikan.
REM /IT = jalan HANYA kalau Bapak sedang login.
REM      Ini WAJIB. Kalau bot jalan saat belum login, drive G: dari Google
REM      Drive for Desktop belum ada, dan dokumennya gagal ditulis.
REM /F  = timpa jadwal lama kalau sudah pernah dipasang.
schtasks /Create /TN "%NAMA%" /TR "\"%SKRIP%\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI,SAT /ST 08:00 /RI 10 /ET 17:00 /K /RU "%USERNAME%" /IT /F

if errorlevel 1 goto :gagal

echo.
echo ============================================================
echo  JADWAL BERHASIL DIPASANG
echo ============================================================
echo.
echo  Bot menyapu tiap 10 menit, Senin sampai Sabtu jam 08:00-17:00,
echo  selama komputer menyala dan Bapak sedang login.
echo.
echo  Sapuan yang belum selesai saat sapuan berikutnya tiba akan
echo  DILEWATI, bukan dijalankan bersamaan - jadi catatannya aman.
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
