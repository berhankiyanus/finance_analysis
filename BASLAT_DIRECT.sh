#!/bin/bash
# FastAPI'yi doğrudan venv/bin/python ile başlat (activate sorunları için)

cd /Users/berhankiyanus/Desktop/Finance

# PATH'e venv/bin ekle
export PATH="/Users/berhankiyanus/Desktop/Finance/venv/bin:$PATH"

# Python ve uvicorn kontrolü
if [ ! -f venv/bin/python ]; then
    echo "❌ venv/bin/python bulunamadı!"
    exit 1
fi

if [ ! -f venv/bin/uvicorn ]; then
    echo "⚠️  uvicorn bulunamadı, yükleniyor..."
    venv/bin/pip install -q fastapi "uvicorn[standard]"
fi

# FastAPI'yi başlat
echo "🚀 FastAPI başlatılıyor..."
echo "   URL: http://127.0.0.1:8000"
echo "   Docs: http://127.0.0.1:8000/docs"
echo ""
echo "⚠️  Durdurmak için: Ctrl+C"
echo ""

venv/bin/uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

