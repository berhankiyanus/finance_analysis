#!/bin/bash
# Sprint 1 MVP Başlatma Scripti

cd /Users/berhankiyanus/Desktop/Finance

# Virtual environment'ı aktifleştir
source venv/bin/activate 2>/dev/null || . venv/bin/activate

# Gerekli paketleri kontrol et ve yükle
echo "📦 Paketler kontrol ediliyor..."
pip install -q fastapi uvicorn[standard] streamlit requests pandas numpy scikit-learn yfinance python-dotenv 2>&1 | grep -v "already satisfied" | tail -3

# FastAPI'yi başlat
echo ""
echo "🚀 FastAPI başlatılıyor..."
echo "   URL: http://127.0.0.1:8000"
echo "   Docs: http://127.0.0.1:8000/docs"
echo ""
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

