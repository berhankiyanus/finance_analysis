#!/bin/bash
# Local çalıştırma için basit başlatma scripti

cd /Users/berhankiyanus/Desktop/Finance

echo "🚀 Local Çalıştırma Başlatılıyor..."
echo ""
echo "⚠️  ÖNEMLİ: Bu script sadece Streamlit'i başlatır."
echo "   FastAPI'yi başlatmak için başka bir terminal açın ve şu komutu çalıştırın:"
echo "   cd /Users/berhankiyanus/Desktop/Finance"
echo "   . venv/bin/activate"
echo "   venv/bin/python3 -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000"
echo ""
echo "─────────────────────────────────────────────────────────"
echo ""

# Virtual environment kontrolü
if [ ! -d "venv" ]; then
    echo "❌ venv klasörü bulunamadı!"
    echo "   Oluşturmak için: python3 -m venv venv"
    exit 1
fi

# Virtual environment'ı aktifleştir
source venv/bin/activate

# Streamlit kontrolü
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  streamlit bulunamadı, yükleniyor..."
    pip install -q streamlit plotly
fi

# Streamlit'i başlat
echo "✅ Streamlit başlatılıyor..."
echo "   🌐 URL: http://localhost:8501"
echo ""
echo "⚠️  Durdurmak için: Ctrl+C"
echo "─────────────────────────────────────────────────────────"
echo ""

streamlit run app.py

