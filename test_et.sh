#!/bin/bash
# Test Etme Scripti

echo "=========================================="
echo "FİNANSAL ANALİZ SİSTEMİ - TEST SCRIPTİ"
echo "=========================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
RED='\033[0;31m'
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

# Paketleri yükle
echo -e "${YELLOW}📥 Gerekli paketler yükleniyor...${NC}"
pip install --quiet --upgrade pip
pip install --quiet pandas numpy yfinance requests beautifulsoup4 python-dotenv

# Transformers ve PyTorch (opsiyonel, büyük dosyalar)
echo -e "${YELLOW}🤖 NLP paketleri yükleniyor (bu biraz zaman alabilir)...${NC}"
pip install --quiet transformers torch sentencepiece

echo ""
echo -e "${GREEN}✅ Kurulum tamamlandı!${NC}"
echo ""
echo "=========================================="
echo "TEST BAŞLIYOR..."
echo "=========================================="
echo ""

# Test 1: Modül import
echo "📦 TEST 1: Modül Import"
python3 -c "
try:
    from src.data_collection import get_news, get_price_data
    from src.sentiment_analysis import SentimentAnalyzer
    from src.financial_analysis import compute_features
    from src.scoring import compute_overall_score
    from src.main import analyze_company
    print('✅ Tüm modüller başarıyla yüklendi')
except Exception as e:
    print(f'❌ Hata: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Modül testi başarılı${NC}"
else
    echo -e "${RED}❌ Modül testi başarısız${NC}"
    exit 1
fi

echo ""

# Test 2: Veri toplama
echo "📥 TEST 2: Veri Toplama"
python3 -c "
from src.data_collection import get_news, get_price_data

# Haber testi
news = get_news('Apple', days_back=7)
print(f'✅ {len(news)} haber bulundu')

# Fiyat testi
price = get_price_data('AAPL', period='1mo')
print(f'✅ {len(price)} günlük fiyat verisi bulundu')
print(f'   Son fiyat: \${price.iloc[-1][\"close\"]:.2f}')
"

echo ""

# Test 3: Mini analiz
echo "🚀 TEST 3: Mini Analiz (7 gün)"
echo "----------------------------------------"
python3 -m src.main "Apple" "AAPL" 7

echo ""
echo "=========================================="
echo -e "${GREEN}✅ TÜM TESTLER TAMAMLANDI!${NC}"
echo "=========================================="
echo ""
echo "💡 Şimdi şu komutları deneyebilirsiniz:"
echo "   python3 -m src.main \"Apple\" \"AAPL\" 30"
echo "   python3 example_usage.py"
echo "   python3 test_system.py"
echo ""

