@echo off
REM ============================================================
REM  Memasang jadwal bot Happy Pumpkin di Windows Task Scheduler.
REM
REM  CARA PAKAI: klik KANAN berkas ini, pilih "Run as administrator".
REM
REM  Jadwalnya: Senin sampai Sabtu, tiap 6 jam pada jam kerja,
REM             jadi menyapu jam 08:00 dan 14:00. Minggu libur.
REM
REM  Perlu menyapu SEKARANG di luar jadwal? Klik dua kali
REM  sapu-sekarang.bat - tidak perlu menyentuh jadwal ini.
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
echo  Menyapu jam : 08:00 dan 14:00
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
REM /RI 360                = diulang tiap 6 jam (360 menit).
REM /ET 17:00 /K           = berhenti mengulang di akhir jam kerja, dan
REM                          sapuan yang masih berjalan saat itu dihentikan.
REM                          Jadi yang benar-benar jalan: 08:00 dan 14:00.
REM /IT = jalan HANYA kalau Bapak sedang login.
REM      Ini WAJIB. Kalau bot jalan saat belum login, drive G: dari Google
REM      Drive for Desktop belum ada, dan dokumennya gagal ditulis.
REM /F  = timpa jadwal lama kalau sudah pernah dipasang.
schtasks /Create /TN "%NAMA%" /TR "\"%SKRIP%\"" /SC WEEKLY /D MON,TUE,WED,THU,FRI,SAT /ST 08:00 /RI 360 /ET 17:00 /K /RU "%USERNAME%" /IT /F

if errorlevel 1 goto :gagal

echo.
echo ============================================================
echo  JADWAL BERHASIL DIPASANG
echo ============================================================
echo.
echo  Bot menyapu jam 08:00 dan 14:00, Senin sampai Sabtu, selama
echo  komputer menyala dan Bapak sedang login.
echo.
echo  BUTUH CEPAT DI LUAR JADWAL?
echo      Klik dua kali  jadwal\sapu-sekarang.bat
echo  Sapuan itu langsung jalan dan hasilnya terlihat di layar.
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
