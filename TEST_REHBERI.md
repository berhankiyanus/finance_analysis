# Test Rehberi

Bu dosya, projeyi test etmek için adım adım yönergeler içerir.

## 🚀 Hızlı Test (En Kolay Yol)

### 1. Otomatik Test Scripti

En kolay yol, hazırladığımız test scriptini çalıştırmak:

```bash
python3 test_system.py
```

Bu script tüm modülleri test eder ve sonuçları gösterir.

### 2. Modül Bazlı Testler

#### Veri Toplama Modülü
```bash
python3 -m src.data_collection
```

#### Sentiment Analizi Modülü
```python
python3 -c "from src.sentiment_analysis import SentimentAnalyzer; a = SentimentAnalyzer(); print(a.analyze_sentiment('Şirket güçlü kâr açıkladı'))"
```

#### Finansal Analiz Modülü
```python
python3 -c "from src.financial_analysis import compute_features; from src.data_collection import get_price_data; import pandas as pd; df = get_price_data('AAPL', '1mo'); df_feat = compute_features(df); print('Feature sayısı:', len(df_feat.columns))"
```

### 3. Tam Analiz Testi

#### Basit Test (Dummy Veri ile)
```bash
python3 -m src.main "Apple" "AAPL" 7
```

#### Gerçek Veri ile Test
```bash
python3 -m src.main "Apple" "AAPL" 30
```

#### Örnek Kullanım Dosyası
```bash
python3 example_usage.py
```

## 📋 Adım Adım Test Süreci

### Adım 1: Paket Kontrolü

```bash
# Gerekli paketlerin yüklü olup olmadığını kontrol et
python3 -c "import pandas, numpy, yfinance; print('Temel paketler OK')"
```

Eğer hata alırsanız:
```bash
pip3 install pandas numpy yfinance requests beautifulsoup4 python-dotenv
```

### Adım 2: Modül Import Testi

```python
python3 -c "
from src.data_collection import get_news, get_price_data
from src.sentiment_analysis import SentimentAnalyzer
from src.financial_analysis import compute_features
from src.scoring import compute_overall_score
from src.main import analyze_company
print('✅ Tüm modüller başarıyla yüklendi')
"
```

### Adım 3: Veri Toplama Testi

```python
python3 << EOF
from src.data_collection import get_news, get_price_data

# Haber testi
print("Haber testi...")
news = get_news("Apple", days_back=7)
print(f"✅ {len(news)} haber bulundu")

# Fiyat testi
print("Fiyat testi...")
price = get_price_data("AAPL", period="1mo")
print(f"✅ {len(price)} günlük veri bulundu")
print(f"Son fiyat: ${price.iloc[-1]['close']:.2f}")
EOF
```

### Adım 4: Sentiment Analizi Testi

```python
python3 << EOF
from src.sentiment_analysis import SentimentAnalyzer

analyzer = SentimentAnalyzer()
test_texts = [
    "Şirket güçlü kâr açıkladı",
    "Şirket zarar etti",
    "Şirket normal seyrini sürdürüyor"
]

for text in test_texts:
    result = analyzer.analyze_sentiment(text)
    print(f"{text}: {result['class']} ({result['confidence']:.2%})")
EOF
```

### Adım 5: Finansal Analiz Testi

```python
python3 << EOF
from src.data_collection import get_price_data
from src.financial_analysis import compute_features, create_feature_vector

# Fiyat verisi al
price_df = get_price_data("AAPL", period="3mo")

# Feature'ları hesapla
price_df_feat = compute_features(price_df)
print(f"✅ {len(price_df_feat.columns)} kolon oluşturuldu")

# Feature vektörü
features = create_feature_vector(price_df_feat)
print(f"✅ Feature vektörü: {len(features)} feature")
print(f"   Return 30d: {features.get('return_30d', 0):.2f}%")
print(f"   RSI: {features.get('rsi_14', 0):.2f}")
EOF
```

### Adım 6: Tam Analiz Testi

```bash
# Mini test (7 gün, hızlı)
python3 -m src.main "Apple" "AAPL" 7

# Tam test (30 gün)
python3 -m src.main "Apple" "AAPL" 30

# Farklı şirket
python3 -m src.main "Microsoft" "MSFT" 30
```

## 🧪 Jupyter Notebook ile Test

1. Jupyter'ı başlatın:
```bash
jupyter notebook
```

2. `notebooks/analysis_notebook.ipynb` dosyasını açın

3. Hücreleri sırayla çalıştırın

## ⚠️ Olası Hatalar ve Çözümleri

### Import Hatası
```
ModuleNotFoundError: No module named 'src'
```
**Çözüm**: Proje kök dizininden çalıştırdığınızdan emin olun:
```bash
cd /Users/berhankiyanus/finance
python3 -m src.main "Apple" "AAPL" 30
```

### Transformers Model İndirme Hatası
```
OSError: Can't load tokenizer
```
**Çözüm**: İnternet bağlantınızı kontrol edin. Model ilk kullanımda indirilir.

### API Key Hatası
```
⚠️ NEWS_API_KEY bulunamadı. Dummy veri kullanılıyor.
```
**Çözüm**: Bu normal! Sistem dummy veri ile çalışır. Gerçek veri için `.env` dosyasına API key ekleyin.

### yfinance Veri Hatası
```
yfinance hatası: ...
```
**Çözüm**: İnternet bağlantınızı kontrol edin. yfinance Yahoo Finance'den veri çeker.

## 📊 Test Sonuçlarını Değerlendirme

Başarılı bir test sonucunda şunları görmelisiniz:

1. ✅ Modüller yüklendi
2. ✅ Haber verisi toplandı (veya dummy veri kullanıldı)
3. ✅ Fiyat verisi çekildi
4. ✅ Sentiment analizi yapıldı
5. ✅ Finansal feature'lar hesaplandı
6. ✅ Skor üretildi
7. ✅ Türkçe rapor oluşturuldu

## 🎯 Önerilen Test Sırası

1. **İlk**: `python3 test_system.py` - Tüm sistemi test et
2. **İkinci**: `python3 -m src.main "Apple" "AAPL" 7` - Mini analiz
3. **Üçüncü**: `python3 example_usage.py` - Örnek kullanımlar
4. **Son**: Jupyter notebook ile interaktif analiz

## 💡 İpuçları

- İlk çalıştırmada Transformers modeli indirilecek (birkaç yüz MB), sabırlı olun
- API key olmadan da test edebilirsiniz (dummy veri kullanılır)
- Hızlı test için `days_back=7` kullanın
- Gerçek analiz için `days_back=30` önerilir

