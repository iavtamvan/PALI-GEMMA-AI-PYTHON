@echo off
cd /d %~dp0

echo 🔁 Mengaktifkan virtual environment...
call venv310\Scripts\activate.bat

echo 🌍 Menyiapkan environment variable...
set ALLOWED_HOSTS=127.0.0.1 localhost 0.0.0.0 192.168.0.105
set SECRET_KEY=<HF_TOKEN>
set DEBUG=True

echo 🚀 Menjalankan Django server di 0.0.0.0:8000...
python manage.py runserver 0.0.0.0:8000

pause
