#!/bin/bash
# Streamlit'i doğrudan venv/bin/python ile başlat (activate sorunları için)

cd /Users/berhankiyanus/Desktop/Finance

# PATH'e venv/bin ekle
export PATH="/Users/berhankiyanus/Desktop/Finance/venv/bin:$PATH"

# Python kontrolü
if [ ! -f venv/bin/python ]; then
    echo "❌ venv/bin/python bulunamadı!"
    exit 1
fi

if [ ! -f venv/bin/streamlit ]; then
    echo "⚠️  streamlit bulunamadı, yükleniyor..."
    venv/bin/pip install -q streamlit plotly
fi

# Streamlit'i başlat
echo "🚀 Streamlit başlatılıyor..."
echo "   URL: http://localhost:8501"
echo ""
echo "⚠️  Durdurmak için: Ctrl+C"
echo ""

venv/bin/streamlit run app.py

