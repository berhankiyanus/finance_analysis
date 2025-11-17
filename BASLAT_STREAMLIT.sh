#!/bin/bash
# Streamlit Başlatma Scripti

cd /Users/berhankiyanus/Desktop/Finance

# Virtual environment'ı aktifleştir
source venv/bin/activate 2>/dev/null || . venv/bin/activate

# Gerekli paketleri kontrol et ve yükle
echo "📦 Paketler kontrol ediliyor..."
pip install -q streamlit plotly requests pandas numpy scikit-learn yfinance python-dotenv 2>&1 | grep -v "already satisfied" | tail -3

# Streamlit'i başlat
echo ""
echo "🚀 Streamlit başlatılıyor..."
echo "   URL: http://localhost:8501"
echo ""
streamlit run app.py

