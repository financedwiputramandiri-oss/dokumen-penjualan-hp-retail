# Menjalankan bot lewat systemd (Linux, lebih rapi daripada cron)

Buat `/etc/systemd/system/sapu-order-sheet.service`:

```ini
[Unit]
Description=Sapuan order sheet Happy Pumpkin
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/path/ke/dokumen-penjualan-hp-retail
ExecStart=/usr/bin/python3 jalankan.py sapu
User=NAMA_PENGGUNA
```

Buat `/etc/systemd/system/sapu-order-sheet.timer`:

```ini
[Unit]
Description=Jalankan sapuan order sheet tiap 12 jam

[Timer]
OnCalendar=*-*-* 06,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Nyalakan:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sapu-order-sheet.timer
systemctl list-timers sapu-order-sheet.timer
```

`Persistent=true` berarti kalau komputer sempat mati saat jadwalnya lewat,
sapuan tetap dijalankan begitu komputer menyala lagi.
