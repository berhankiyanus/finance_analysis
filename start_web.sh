#!/bin/bash
# Web Uygulamasını Başlatma Scripti

echo "=========================================="
echo "🌐 Finansal Analiz Web Uygulaması"
echo "=========================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Virtual environment kontrolü
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment bulunamadı. Oluşturuluyor...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment oluşturuldu${NC}"
fi

# Virtual environment'ı aktifleştir
echo -e "${YELLOW}📦 Virtual environment aktifleştiriliyor...${NC}"
source venv/bin/activate

# Streamlit kontrolü
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}📥 Streamlit yükleniyor...${NC}"
    pip install --quiet streamlit plotly
    echo -e "${GREEN}✅ Streamlit yüklendi${NC}"
fi

echo ""
echo -e "${GREEN}🚀 Web uygulaması başlatılıyor...${NC}"
echo ""
echo "Tarayıcınızda otomatik olarak açılacak:"
echo "   http://localhost:8501"
echo ""
echo "Durdurmak için: Ctrl+C"
echo ""

# Streamlit'i başlat
streamlit run app.py

