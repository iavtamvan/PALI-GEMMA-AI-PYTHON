#!/bin/bash

echo "🔁 Mengaktifkan virtual environment..."
source venv310/bin/activate

echo "🌍 Menyiapkan environment variable..."
export ALLOWED_HOSTS="127.0.0.1 localhost 0.0.0.0 192.168.0.111"
export SECRET_KEY=<HF_TOKEN>
export DEBUG=True

echo "🚀 Menjalankan Django server di 0.0.0.0:8000..."
python manage.py runserver 0.0.0.0:8000
