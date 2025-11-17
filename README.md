# Finansal Şirket Analiz ve Haber Sentiment Analizi Sistemi

🌐 **Web Uygulaması**: `streamlit run app.py` veya `./start_web.sh` ile başlatın!

## 📋 PROJE ÖZETİ ve AMAÇ

Bu proje, bir şirket adı veya borsa kodu (ticker) girdiğinizde, o şirket hakkında kapsamlı bir finansal analiz ve haber sentiment analizi yapan bir yapay zeka sistemidir.

### Çözdüğü Problem

Yatırımcılar ve finansal analistler, bir şirket hakkında karar verirken hem finansal verileri hem de piyasadaki haberleri ve duyarlılığı birlikte değerlendirmek zorundadır. Bu sistem, bu iki önemli bilgi kaynağını otomatik olarak toplayıp analiz ederek, kullanıcıya:

- **Haber Analizi**: Şirketle ilgili son haberleri toplar ve her haberin olumlu/olumsuz/nötr duyarlılığını analiz eder
- **Finansal Veri Analizi**: Şirketin fiyat hareketleri, volatilite, getiri oranları ve temel finansal göstergelerini inceler
- **Skor Üretimi**: Haber sentiment sonuçları ile finansal göstergeleri birleştirerek 0-100 arası bir "Genel Durum / Risk Skoru" üretir ve Türkçe bir özet rapor sunar

### Hedef Kullanıcılar

- Bireysel yatırımcılar
- Finansal analistler
- Finans eğitimi alan öğrenciler
- Finansal danışmanlar

### Sistemin Üç Ana Bileşeni

1. **Haber Analizi Modülü**: İnternetten şirketle ilgili haberleri toplar, temizler ve sentiment analizi yapar
2. **Finansal Veri Analizi Modülü**: Fiyat verilerini ve temel finansal göstergeleri analiz eder, istatistiksel özellikler çıkarır
3. **Skorlama ve Raporlama Modülü**: İki modülün sonuçlarını birleştirerek skor üretir ve Türkçe özet rapor oluşturur

---

## 🏗️ SİSTEM MİMARİSİ (HIGH-LEVEL)

Sistem, 6 ana katmandan oluşmaktadır:

### 1. Veri Toplama Katmanı (Data Collection Layer)

**Girdi**: Şirket adı veya borsa ticker'ı (örn: "Apple", "AAPL", "THYAO")

**İşlemler**:
- Haber API'lerinden veya web scraping ile son haberleri toplama
- Finansal veri API'lerinden (Yahoo Finance, Alpha Vantage vb.) fiyat ve temel göstergeleri çekme
- Veri doğrulama ve temel format kontrolü

**Çıktı**:
- Ham haber verisi (başlık, özet, tarih, kaynak, link)
- Ham fiyat verisi (tarih, açılış, yüksek, düşük, kapanış, hacim)
- Temel finansal göstergeler (P/E, gelir, kâr marjı vb. - eğer mevcutsa)

### 2. Veri Ön İşleme Katmanı (Data Preprocessing Layer)

**Girdi**: Ham haber ve finansal veri

**İşlemler**:
- Haberler için: HTML tag temizleme, özel karakter düzeltme, dil kontrolü, çok kısa/gereksiz haberlerin filtrelenmesi
- Finansal veri için: Eksik veri yönetimi (interpolation veya forward fill), zaman serisi hizalama, outlier tespiti
- Haber tarihleri ile fiyat verisini eşleştirme (temporal alignment)

**Çıktı**:
- Temizlenmiş haber DataFrame'i
- Temizlenmiş ve hizalanmış fiyat DataFrame'i

### 3. NLP / Sentiment Analizi Katmanı

**Girdi**: Temizlenmiş haber başlıkları ve metinleri

**İşlemler**:
- Her haber için sentiment analizi (pozitif/negatif/nötr sınıflandırması)
- Sentiment skoru hesaplama (olasılık değerleri ile)
- Haberlerin ağırlıklı ortalamasını alma (tarih bazlı ağırlıklandırma - daha yeni haberler daha önemli)

**Çıktı**:
- Her haber için sentiment sınıfı ve skoru
- Toplam sentiment skoru (normalize edilmiş, 0-100 arası)

### 4. Finansal Metrik Analizi ve Feature Engineering Katmanı

**Girdi**: Temizlenmiş fiyat verisi ve temel finansal göstergeler

**İşlemler**:
- Zaman serisi feature'ları üretme:
  - Son 5, 10, 20, 30 günlük getiri oranları
  - Volatilite (standart sapma)
  - Hareketli ortalamalar (MA5, MA10, MA20, MA50)
  - RSI (Relative Strength Index) gibi teknik göstergeler
- Temel finansal rasyoları normalize etme (eğer mevcutsa)

**Çıktı**:
- Feature vektörü (pandas Series veya dict)
- Finansal sağlık skoru (0-100 arası normalize edilmiş)

### 5. Skor Hesaplama ve Karar Katmanı (Scoring & Decision Layer)

**Girdi**: Sentiment skoru + Finansal feature skoru

**İşlemler**:
- Ağırlıklı ortalama ile birleştirme (örn: 0.4 * sentiment + 0.6 * finansal)
- Skor aralığına göre yorum üretme
- İsteğe bağlı: Basit ML modeli ile kısa dönem yön tahmini (yukarı/aşağı/yatay)

**Çıktı**:
- Genel Durum / Risk Skoru (0-100)
- Türkçe metinsel özet
- Yön tahmini (opsiyonel)

### 6. Sunum Katmanı (Presentation Layer)

**Girdi**: Skor, özet, ham veriler

**İşlemler**:
- Konsol çıktısı formatlama
- Jupyter Notebook'ta görselleştirme (grafikler, tablolar)
- İleri seviye: REST API endpoint'leri (FastAPI)
- İleri seviye: Web arayüzü (Streamlit veya React)

**Çıktı**:
- Formatlanmış rapor (konsol/notebook/web)

---

## 📊 VERİ TOPLAMA PLANI

### Haber Verileri

#### Önerilen Veri Kaynakları

1. **NewsAPI** (https://newsapi.org/)
   - Ücretsiz tier: 100 istek/gün
   - Çoklu kaynak desteği
   - API key gerektirir

2. **Alpha Vantage News & Sentiment API**
   - Finansal haberler için özelleşmiş
   - Sentiment skorları da içerir (ekstra maliyetli olabilir)

3. **Web Scraping** (Alternatif)
   - Finansal haber sitelerinden (ör: Bloomberg, Reuters, finansal haber siteleri)
   - BeautifulSoup veya Selenium kullanımı
   - Dikkat: robots.txt ve kullanım şartlarına uygunluk

#### Tarih Filtresi

- Varsayılan: Son 30 gün
- Ayarlanabilir parametre: `days_back=30`
- Her haber için timestamp kaydedilmeli

#### Haber Verisi Şeması

```python
news_df kolonları:
- 'title': str          # Haber başlığı
- 'summary': str        # Haber özeti (varsa)
- 'content': str        # Tam haber metni (varsa)
- 'published_at': datetime  # Yayın tarihi
- 'source': str         # Kaynak (örn: "Bloomberg", "Reuters")
- 'url': str            # Haber linki
- 'relevance_score': float  # Şirketle ilgili olma skoru (0-1)
```

### Finansal Veriler

#### Önerilen Veri Kaynakları

1. **Yahoo Finance** (yfinance kütüphanesi)
   - Ücretsiz, kolay kullanım
   - OHLCV verisi (Open, High, Low, Close, Volume)
   - Tarihsel veri desteği

2. **Alpha Vantage**
   - Temel göstergeler (P/E, gelir vb.)
   - API key gerektirir, rate limit var

3. **Financial Modeling Prep API**
   - Detaylı finansal göstergeler
   - Ücretsiz tier mevcut

#### Fiyat Verisi Şeması

```python
price_df kolonları:
- 'date': datetime      # Tarih
- 'open': float         # Açılış fiyatı
- 'high': float         # En yüksek
- 'low': float          # En düşük
- 'close': float        # Kapanış fiyatı
- 'volume': int         # İşlem hacmi
- 'adjusted_close': float  # Düzeltilmiş kapanış (split/dividend sonrası)
```

#### Temel Finansal Göstergeler Şeması (Opsiyonel)

```python
fundamentals_df kolonları:
- 'pe_ratio': float           # P/E oranı
- 'market_cap': float         # Piyasa değeri
- 'revenue_growth': float     # Gelir büyümesi (%)
- 'profit_margin': float      # Kâr marjı (%)
- 'debt_to_equity': float     # Borç/Özsermaye
- 'current_ratio': float      # Cari oran
- 'roe': float                # Özsermaye kârlılığı (%)
```

---

## 🔧 VERİ ÖN İŞLEME ADIMLARI

### Haberler İçin Ön İşleme

#### 1. HTML Tag Temizleme
```python
# BeautifulSoup ile HTML içeriği temizleme
from bs4 import BeautifulSoup

def clean_html(text):
    if pd.isna(text):
        return ""
    soup = BeautifulSoup(str(text), 'html.parser')
    return soup.get_text()
```

#### 2. Özel Karakter ve Whitespace Temizleme
```python
import re

def clean_text(text):
    # HTML tag'leri kaldır
    text = clean_html(text)
    # Çoklu boşlukları tek boşluğa çevir
    text = re.sub(r'\s+', ' ', text)
    # Başta/sonda boşlukları kaldır
    text = text.strip()
    return text
```

#### 3. Dil Kontrolü ve Filtreleme
- Türkçe ve İngilizce haberler kabul edilir
- Çok kısa haberler filtrelenir (örn: < 20 karakter)
- Duplicate haberler tespit edilir (başlık benzerliği ile)

#### 4. Tarih Normalizasyonu
- Tüm tarihler UTC'ye çevrilir
- Eksik tarihler varsa, haber sıralamasından tahmin edilir

### Finansal Veri İçin Ön İşleme

#### 1. Eksik Veri Yönetimi
```python
# Forward fill (son bilinen değerle doldur)
price_df['close'].fillna(method='ffill', inplace=True)

# Veya interpolation (doğrusal interpolasyon)
price_df['close'].interpolate(method='linear', inplace=True)
```

#### 2. Zaman Serisi Hizalama
- Haber tarihleri ile fiyat verisini eşleştirme
- Her haber için, o tarihteki veya en yakın tarihteki fiyat verisi bulunur

#### 3. Outlier Tespiti
- Aşırı fiyat hareketleri tespit edilir (örn: %50'den fazla günlük değişim)
- Bu durumlar loglanır ama veri silinmez (gerçek olaylar olabilir)

### Feature Üretme Örnekleri

```python
# Son 5 günlük getiri
price_df['return_5d'] = price_df['close'].pct_change(5)

# Son 10 günlük volatilite (standart sapma)
price_df['volatility_10d'] = price_df['close'].pct_change().rolling(10).std()

# Hareketli ortalama (10 gün)
price_df['ma_10'] = price_df['close'].rolling(10).mean()

# RSI (14 günlük)
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

price_df['rsi_14'] = calculate_rsi(price_df['close'])
```

---

## 🤖 NLP / SENTIMENT ANALİZİ TASARIMI

### Model Seçimi

#### Önerilen Model: FinBERT veya FinBERT-TR

1. **FinBERT** (Hugging Face: `ProsusAI/finbert`)
   - Finansal alan için fine-tune edilmiş BERT modeli
   - İngilizce haberler için ideal
   - 3 sınıf: positive, negative, neutral

2. **Türkçe için Alternatifler**:
   - `dbmdz/bert-base-turkish-cased` + fine-tuning
   - `savasy/bert-base-turkish-sentiment-cased` (genel sentiment, finansal değil)
   - Veya çok dilli modeller: `xlm-roberta-base`

#### Model Kullanım Konsepti

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Model yükleme
model_name = "ProsusAI/finbert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# Sentiment analizi fonksiyonu
def analyze_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    # Sınıf: 0=positive, 1=negative, 2=neutral
    predicted_class = torch.argmax(probs, dim=-1).item()
    confidence = probs[0][predicted_class].item()
    
    return {
        'class': ['positive', 'negative', 'neutral'][predicted_class],
        'confidence': confidence,
        'probs': {
            'positive': probs[0][0].item(),
            'negative': probs[0][1].item(),
            'neutral': probs[0][2].item()
        }
    }
```

### Sentiment Skoru Hesaplama

Her haber için sentiment skoru:

```python
def news_to_score(sentiment_result):
    """
    Sentiment sonucunu -1 ile +1 arası skora çevir
    """
    if sentiment_result['class'] == 'positive':
        return sentiment_result['probs']['positive']
    elif sentiment_result['class'] == 'negative':
        return -sentiment_result['probs']['negative']
    else:  # neutral
        return 0.0
```

Tüm haberlerin ağırlıklı ortalaması:

```python
def aggregate_sentiment(news_df):
    """
    Haberleri tarih bazlı ağırlıklandırarak toplam sentiment skoru hesapla
    """
    # Daha yeni haberler daha yüksek ağırlık alır
    news_df['weight'] = (news_df['published_at'] - news_df['published_at'].min()).dt.days + 1
    news_df['weight'] = news_df['weight'] / news_df['weight'].max()
    
    # Ağırlıklı ortalama
    weighted_score = (news_df['sentiment_score'] * news_df['weight']).sum() / news_df['weight'].sum()
    
    # -1 ile +1 arası skoru 0-100 arasına normalize et
    normalized_score = (weighted_score + 1) * 50  # -1 -> 0, +1 -> 100
    
    return normalized_score
```

### İleri Seviye: Finansal Domain Fine-Tuning

Eğer Türkçe finansal haberler için özel model eğitmek isterseniz:

1. **Veri Toplama**: Türkçe finansal haberler + manuel sentiment etiketleme
2. **Fine-tuning**: `dbmdz/bert-base-turkish-cased` modelini finansal veri ile fine-tune etme
3. **Değerlendirme**: Test seti üzerinde doğruluk ölçümü

Bu aşama şimdilik opsiyoneldir, hazır modellerle başlanabilir.

---

## 📈 FİNANSAL ANALİZ ve ÖZELLİK (FEATURE) ÜRETME

### Zaman Serisi Feature'ları

#### 1. Getiri Oranları
```python
# Günlük getiri
price_df['daily_return'] = price_df['close'].pct_change()

# Son X günlük kümülatif getiri
for period in [5, 10, 20, 30]:
    price_df[f'return_{period}d'] = price_df['close'].pct_change(period)
```

#### 2. Volatilite
```python
# Son X günlük volatilite (standart sapma)
for period in [5, 10, 20, 30]:
    price_df[f'volatility_{period}d'] = price_df['daily_return'].rolling(period).std()
```

#### 3. Hareketli Ortalamalar
```python
# Basit hareketli ortalama
for period in [5, 10, 20, 50, 200]:
    price_df[f'ma_{period}'] = price_df['close'].rolling(period).mean()

# Üssel hareketli ortalama (EMA)
for period in [12, 26]:
    price_df[f'ema_{period}'] = price_df['close'].ewm(span=period).mean()
```

#### 4. Teknik Göstergeler

**RSI (Relative Strength Index)**:
```python
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

price_df['rsi_14'] = calculate_rsi(price_df['close'])
```

**MACD (Moving Average Convergence Divergence)**:
```python
ema_12 = price_df['close'].ewm(span=12).mean()
ema_26 = price_df['close'].ewm(span=26).mean()
price_df['macd'] = ema_12 - ema_26
price_df['macd_signal'] = price_df['macd'].ewm(span=9).mean()
price_df['macd_histogram'] = price_df['macd'] - price_df['macd_signal']
```

**Bollinger Bands**:
```python
period = 20
std_mult = 2
price_df['bb_middle'] = price_df['close'].rolling(period).mean()
bb_std = price_df['close'].rolling(period).std()
price_df['bb_upper'] = price_df['bb_middle'] + (bb_std * std_mult)
price_df['bb_lower'] = price_df['bb_middle'] - (bb_std * std_mult)
```

### Temel Finansal Rasyolar (Eğer Mevcutsa)

Bu veriler genellikle ücretli API'lerden gelir veya manuel olarak toplanır.

#### Normalizasyon ve Skorlama

```python
def normalize_financial_metrics(fundamentals_df):
    """
    Finansal göstergeleri 0-100 arası skora çevir
    """
    scores = {}
    
    # P/E oranı: Düşük P/E genelde iyi (tersine çevir)
    if 'pe_ratio' in fundamentals_df:
        pe = fundamentals_df['pe_ratio']
        # P/E 0-50 arası normal kabul edilir
        pe_score = max(0, min(100, (50 - pe) / 50 * 100))
        scores['pe_score'] = pe_score
    
    # Gelir büyümesi: Yüksek büyüme iyi
    if 'revenue_growth' in fundamentals_df:
        growth = fundamentals_df['revenue_growth']
        # %0-50 arası büyüme normal
        growth_score = max(0, min(100, growth / 50 * 100))
        scores['growth_score'] = growth_score
    
    # Kâr marjı: Yüksek marj iyi
    if 'profit_margin' in fundamentals_df:
        margin = fundamentals_df['profit_margin']
        # %0-30 arası marj normal
        margin_score = max(0, min(100, margin / 30 * 100))
        scores['margin_score'] = margin_score
    
    # Borç/Özsermaye: Düşük oran iyi
    if 'debt_to_equity' in fundamentals_df:
        de_ratio = fundamentals_df['debt_to_equity']
        # 0-2 arası normal
        de_score = max(0, min(100, (2 - de_ratio) / 2 * 100))
        scores['de_score'] = de_score
    
    # Tüm skorların ortalaması
    overall_score = sum(scores.values()) / len(scores) if scores else 50.0
    
    return {
        'individual_scores': scores,
        'overall_score': overall_score
    }
```

### Feature Vektörü Oluşturma

Tüm feature'ları birleştirerek model için hazır vektör:

```python
def create_feature_vector(price_df, fundamentals_df=None):
    """
    Tüm feature'ları birleştirerek tek bir vektör oluştur
    """
    latest = price_df.iloc[-1]  # En son günün verisi
    
    features = {
        # Getiri feature'ları
        'return_5d': latest.get('return_5d', 0),
        'return_10d': latest.get('return_10d', 0),
        'return_30d': latest.get('return_30d', 0),
        
        # Volatilite
        'volatility_10d': latest.get('volatility_10d', 0),
        'volatility_30d': latest.get('volatility_30d', 0),
        
        # Hareketli ortalamalar (fiyatın MA'lara göre konumu)
        'price_vs_ma10': (latest['close'] / latest.get('ma_10', latest['close']) - 1) * 100,
        'price_vs_ma20': (latest['close'] / latest.get('ma_20', latest['close']) - 1) * 100,
        
        # Teknik göstergeler
        'rsi_14': latest.get('rsi_14', 50),
        'macd': latest.get('macd', 0),
    }
    
    # Finansal göstergeler varsa ekle
    if fundamentals_df is not None:
        fin_scores = normalize_financial_metrics(fundamentals_df)
        features['financial_score'] = fin_scores['overall_score']
    
    return features
```

---

## 🎯 SKORLAMA SİSTEMİ TASARIMI

### Genel Durum / Risk Skoru Formülü

#### Basit Ağırlıklı Ortalama Yaklaşımı

```python
def compute_overall_score(sentiment_score, financial_score, 
                         sentiment_weight=0.4, financial_weight=0.6):
    """
    Haber sentiment ve finansal skorları birleştir
    
    Parametreler:
    - sentiment_score: 0-100 arası haber sentiment skoru
    - financial_score: 0-100 arası finansal sağlık skoru
    - sentiment_weight: Haber ağırlığı (varsayılan 0.4)
    - financial_weight: Finansal ağırlık (varsayılan 0.6)
    """
    # Ağırlıkların toplamı 1 olmalı
    total_weight = sentiment_weight + financial_weight
    sentiment_weight = sentiment_weight / total_weight
    financial_weight = financial_weight / total_weight
    
    # Ağırlıklı ortalama
    overall_score = (sentiment_score * sentiment_weight + 
                     financial_score * financial_weight)
    
    # 0-100 arasına sınırla
    overall_score = max(0, min(100, overall_score))
    
    return overall_score
```

#### Finansal Skor Hesaplama

Finansal feature'lardan skor üretme:

```python
def compute_financial_score(feature_vector):
    """
    Feature vektöründen finansal sağlık skoru hesapla
    """
    scores = []
    
    # Getiri skoru (son 30 günlük getiri)
    return_30d = feature_vector.get('return_30d', 0) * 100  # Yüzdeye çevir
    # %-20 ile %+20 arası normal, bunun dışı ekstrem
    return_score = max(0, min(100, 50 + return_30d * 2.5))  # %0 getiri = 50 skor
    scores.append(('return', return_score, 0.3))  # %30 ağırlık
    
    # Volatilite skoru (düşük volatilite iyi)
    vol_30d = feature_vector.get('volatility_30d', 0) * 100
    # %0-5 arası volatilite normal
    vol_score = max(0, min(100, 100 - vol_30d * 10))
    scores.append(('volatility', vol_score, 0.2))  # %20 ağırlık
    
    # RSI skoru (30-70 arası sağlıklı)
    rsi = feature_vector.get('rsi_14', 50)
    if 30 <= rsi <= 70:
        rsi_score = 100 - abs(rsi - 50) * 2  # 50'ye yakın = yüksek skor
    else:
        rsi_score = max(0, 100 - abs(rsi - 50) * 1.5)  # Aşırı değerler düşük skor
    scores.append(('rsi', rsi_score, 0.2))  # %20 ağırlık
    
    # Fiyat vs MA skoru (fiyat MA'nın üstündeyse iyi)
    price_vs_ma20 = feature_vector.get('price_vs_ma20', 0)
    ma_score = max(0, min(100, 50 + price_vs_ma20 * 2))
    scores.append(('trend', ma_score, 0.3))  # %30 ağırlık
    
    # Ağırlıklı ortalama
    total_score = sum(score * weight for _, score, weight in scores)
    total_weight = sum(weight for _, _, weight in scores)
    
    return total_score / total_weight if total_weight > 0 else 50.0
```

### Skor Aralıkları ve Yorumlama

```python
def interpret_score(overall_score):
    """
    Skoru yorumla ve kategori belirle
    """
    if overall_score >= 70:
        category = "Güçlü / Olumlu Görünüm"
        risk_level = "Düşük Risk"
        recommendation = "Şirket güçlü finansal göstergelere ve olumlu haber akışına sahip."
    elif overall_score >= 50:
        category = "Nötr / Karışık Görünüm"
        risk_level = "Orta Risk"
        recommendation = "Şirket karışık sinyaller veriyor. Dikkatli takip edilmeli."
    elif overall_score >= 30:
        category = "Zayıf / Olumsuz Görünüm"
        risk_level = "Yüksek Risk"
        recommendation = "Şirket zayıf finansal göstergelere veya olumsuz haber akışına sahip."
    else:
        category = "Çok Zayıf / Kritik Durum"
        risk_level = "Çok Yüksek Risk"
        recommendation = "Şirket ciddi sorunlar yaşıyor olabilir. Dikkatli olunmalı."
    
    return {
        'category': category,
        'risk_level': risk_level,
        'recommendation': recommendation
    }
```

### Türkçe Özet Rapor Üretme

```python
def generate_turkish_summary(company_name, sentiment_score, financial_score, 
                            overall_score, news_count, interpretation):
    """
    Türkçe özet rapor oluştur
    """
    summary = f"""
╔══════════════════════════════════════════════════════════════╗
║  {company_name.upper()} - FİNANSAL ANALİZ RAPORU              ║
╚══════════════════════════════════════════════════════════════╝

📊 GENEL DURUM SKORU: {overall_score:.1f}/100
   Kategori: {interpretation['category']}
   Risk Seviyesi: {interpretation['risk_level']}

📰 HABER ANALİZİ
   Sentiment Skoru: {sentiment_score:.1f}/100
   Analiz Edilen Haber Sayısı: {news_count}
   
💰 FİNANSAL ANALİZ
   Finansal Sağlık Skoru: {financial_score:.1f}/100

💡 ÖNERİ
   {interpretation['recommendation']}

───────────────────────────────────────────────────────────────
"""
    return summary
```

---

## 🚀 İLERİ SEVİYE: MAKİNE ÖĞRENMESİ MODELİ (OPSİYONEL)

### Problem Tanımı

**Girdi**: Feature vektörü (sentiment + finansal feature'lar)  
**Çıktı**: Önümüzdeki 5-10 günlük fiyat yönü tahmini (yukarı/aşağı/yatay)

### Önerilen Modeller

#### 1. Başlangıç Seviyesi: Scikit-learn Modelleri

**Logistic Regression**:
- Hızlı, yorumlanabilir
- Feature importance çıkarılabilir

**Random Forest**:
- Non-linear ilişkileri yakalayabilir
- Feature importance sağlar

**Gradient Boosting (XGBoost/LightGBM)**:
- Genelde en iyi performans
- Hyperparameter tuning gerekir

#### 2. İleri Seviye: Zaman Serisi Modelleri

**LSTM (Long Short-Term Memory)**:
- Zaman serisi bağımlılıklarını öğrenir
- PyTorch veya TensorFlow ile implementasyon

**Transformer Tabanlı Modeller**:
- Time Series Transformer
- Daha karmaşık ama güçlü

### Model Eğitim Süreci

#### 1. Veri Hazırlama

```python
def prepare_training_data(historical_data):
    """
    Geçmiş veriden eğitim seti oluştur
    """
    X = []  # Feature'lar
    y = []  # Hedef (gelecek getiri veya yön)
    
    for i in range(30, len(historical_data) - 5):  # En az 30 gün geçmiş + 5 gün gelecek
        # Feature'ları çıkar
        features = create_feature_vector(historical_data.iloc[:i+1])
        X.append(list(features.values()))
        
        # Gelecek 5 günlük getiri
        future_return = (historical_data.iloc[i+5]['close'] / 
                        historical_data.iloc[i]['close'] - 1)
        
        # Yön sınıflandırması
        if future_return > 0.02:  # %2'den fazla artış
            y.append('up')
        elif future_return < -0.02:  # %2'den fazla düşüş
            y.append('down')
        else:
            y.append('neutral')
    
    return np.array(X), np.array(y)
```

#### 2. Train/Validation/Test Ayrımı

**ÖNEMLİ**: Zaman serisi verisi olduğu için **zaman bazlı** ayrım yapılmalı:

```python
# YANLIŞ: Rastgele ayrım (future leakage riski)
# X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)

# DOĞRU: Zaman bazlı ayrım
split_idx = int(len(X) * 0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# Validation seti de train'den zaman bazlı ayrılmalı
val_split_idx = int(len(X_train) * 0.8)
X_train_final, X_val = X_train[:val_split_idx], X_train[val_split_idx:]
y_train_final, y_val = y_train[:val_split_idx], y_train[val_split_idx:]
```

#### 3. Model Eğitimi (Örnek: Random Forest)

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Model oluştur
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42
)

# Eğit
model.fit(X_train_final, y_train_final)

# Validation setinde değerlendir
val_pred = model.predict(X_val)
print(classification_report(y_val, val_pred))

# Test setinde değerlendir
test_pred = model.predict(X_test)
print(classification_report(y_test, test_pred))
```

#### 4. Feature Importance Analizi

```python
importances = model.feature_importances_
feature_names = list(feature_vector.keys())

# En önemli feature'ları göster
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importances
}).sort_values('importance', ascending=False)

print(importance_df)
```

### Dikkat Edilmesi Gerekenler

1. **Future Leakage**: Gelecekteki verileri kullanmamaya dikkat edin
2. **Overfitting**: Zaman serisi modelleri kolayca overfit olabilir, regularization kullanın
3. **Veri Miktarı**: ML modeli için yeterli veri gerekir (en az birkaç yıl)
4. **Backtesting**: Model performansını geçmiş veri üzerinde test edin

---

## 📅 ADIM ADIM PROJE PLANI (MİLTAŞ + GÖREVLER)

### Aşama 1: Veri Toplama Prototipi (1-2 hafta)

**Hedef**: Haber ve fiyat verilerini toplayan çalışan bir sistem

**Yapılacak İşler**:
- [ ] NewsAPI veya alternatif haber kaynağı entegrasyonu
- [ ] yfinance ile fiyat verisi çekme fonksiyonu
- [ ] Veri yapılarını tanımlama (pandas DataFrame şemaları)
- [ ] Basit test: Bir şirket için veri çekme ve kaydetme
- [ ] Hata yönetimi ve logging ekleme

**Kullanılacak Teknolojiler**:
- `requests`: API istekleri
- `yfinance`: Yahoo Finance verisi
- `pandas`: Veri yapıları
- `python-dotenv`: API key yönetimi

**Çıktı**: `data_collection.py` modülü

---

### Aşama 2: NLP Sentiment Pipeline'ı (1-2 hafta)

**Hedef**: Haber metinlerinden sentiment analizi yapan sistem

**Yapılacak İşler**:
- [ ] Hugging Face transformers kurulumu
- [ ] FinBERT veya alternatif model seçimi ve yükleme
- [ ] Sentiment analizi fonksiyonu implementasyonu
- [ ] Batch processing (çoklu haber için optimize)
- [ ] Sentiment skorunu normalize etme (-1 ile +1 arası)
- [ ] Ağırlıklı ortalama hesaplama (tarih bazlı)

**Kullanılacak Teknolojiler**:
- `transformers`: Hugging Face modelleri
- `torch`: PyTorch (model backend)
- `numpy`: Sayısal işlemler

**Çıktı**: `sentiment_analysis.py` modülü

---

### Aşama 3: Finansal Feature Engineering ve Basit Skor Sistemi (1-2 hafta)

**Hedef**: Fiyat verisinden feature çıkarma ve finansal skor hesaplama

**Yapılacak İşler**:
- [ ] Veri ön işleme fonksiyonları (eksik veri, outlier)
- [ ] Getiri, volatilite, MA hesaplama
- [ ] RSI, MACD gibi teknik göstergeler
- [ ] Feature vektörü oluşturma fonksiyonu
- [ ] Finansal skor hesaplama algoritması
- [ ] Skor normalizasyonu (0-100 arası)

**Kullanılacak Teknolojiler**:
- `pandas`: Veri işleme
- `numpy`: Matematiksel işlemler
- `ta-lib` (opsiyonel): Teknik analiz göstergeleri

**Çıktı**: `financial_analysis.py` modülü

---

### Aşama 4: Skorlama ve Raporlama Sistemi (1 hafta)

**Hedef**: Tüm bileşenleri birleştirip skor üreten ve Türkçe rapor oluşturan sistem

**Yapılacak İşler**:
- [ ] Sentiment ve finansal skorları birleştirme fonksiyonu
- [ ] Genel durum skoru hesaplama (ağırlıklı ortalama)
- [ ] Skor yorumlama ve kategori belirleme
- [ ] Türkçe özet rapor üretme fonksiyonu
- [ ] Konsol çıktısı formatlama
- [ ] Ana `main()` fonksiyonu ile tüm akışı birleştirme

**Kullanılacak Teknolojiler**:
- Python standart kütüphaneleri
- `pandas`: Veri birleştirme

**Çıktı**: `scoring.py` ve `main.py` dosyaları

---

### Aşama 5: Jupyter Notebook ile Görselleştirme (1 hafta)

**Hedef**: Sonuçları görsel olarak sunan interaktif notebook

**Yapılacak İşler**:
- [ ] Fiyat grafiği çizme (matplotlib/plotly)
- [ ] Sentiment skorlarını zaman serisi olarak gösterme
- [ ] Skor karşılaştırması (bar chart)
- [ ] Haber başlıklarını tablo olarak gösterme
- [ ] İnteraktif widget'lar (şirket seçimi için)

**Kullanılacak Teknolojiler**:
- `matplotlib`: Statik grafikler
- `plotly`: İnteraktif grafikler
- `ipywidgets`: İnteraktif widget'lar
- `jupyter`: Notebook ortamı

**Çıktı**: `analysis_notebook.ipynb`

---

### Aşama 6 (Opsiyonel): ML Modeli ile Yön Tahmini (2-3 hafta)

**Hedef**: Gelecek fiyat yönünü tahmin eden basit bir model

**Yapılacak İşler**:
- [ ] Geçmiş veri toplama (en az 1-2 yıl)
- [ ] Eğitim verisi hazırlama (feature + hedef)
- [ ] Zaman bazlı train/test ayrımı
- [ ] Model seçimi ve eğitimi (Random Forest veya XGBoost)
- [ ] Model değerlendirme (accuracy, precision, recall)
- [ ] Tahmin fonksiyonu implementasyonu
- [ ] Backtesting

**Kullanılacak Teknolojiler**:
- `scikit-learn`: ML modelleri
- `xgboost` veya `lightgbm`: Gradient boosting
- `pandas`: Veri işleme

**Çıktı**: `prediction_model.py` modülü

---

### Aşama 7 (Opsiyonel): FastAPI ile REST API (1-2 hafta)

**Hedef**: Web servisi olarak kullanılabilir API

**Yapılacak İşler**:
- [ ] FastAPI projesi kurulumu
- [ ] Endpoint tasarımı (`/analyze/{ticker}`)
- [ ] Request/Response modelleri (Pydantic)
- [ ] Hata yönetimi ve validation
- [ ] API dokümantasyonu (Swagger)
- [ ] Basit rate limiting
- [ ] Docker containerization (opsiyonel)

**Kullanılacak Teknolojiler**:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Veri validation

**Çıktı**: `api/` klasörü ve `main.py` (API)

---

### Aşama 8 (Opsiyonel): Web Arayüzü (2-3 hafta)

**Hedef**: Kullanıcı dostu web arayüzü

**Yapılacak İşler**:
- [ ] Streamlit veya React ile frontend
- [ ] Şirket arama formu
- [ ] Sonuçları görselleştirme
- [ ] Responsive tasarım
- [ ] API entegrasyonu

**Kullanılacak Teknolojiler**:
- `streamlit`: Hızlı prototip için
- veya `react` + `fastapi`: Production için

**Çıktı**: Web uygulaması

---

## 💻 ÖRNEK KOD İSKELETİ (V1 PROTOTİP)

Aşağıdaki kod iskeleti, projenin temel yapısını ve konseptini gösterir. Her modül ayrı bir Python dosyası olarak organize edilmiştir.

### Proje Yapısı

```
finance/
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── data_collection.py      # Veri toplama
│   ├── sentiment_analysis.py   # NLP sentiment
│   ├── financial_analysis.py   # Finansal analiz
│   ├── scoring.py              # Skorlama
│   └── main.py                 # Ana akış
├── notebooks/
│   └── analysis_notebook.ipynb
└── tests/
    └── test_basic.py
```

### Kod İskeleti Detayları

Kod iskeleti ayrı dosyalarda sağlanacaktır. Bu README'de yapı ve konsept açıklanmıştır.

---

## 🎓 ÖĞRENME KAYNAKLARI

### Python ve Veri Bilimi
- Pandas dokümantasyonu: https://pandas.pydata.org/
- NumPy dokümantasyonu: https://numpy.org/

### NLP ve Transformers
- Hugging Face kursu: https://huggingface.co/course
- Transformers dokümantasyonu: https://huggingface.co/docs/transformers

### Finansal Veri
- yfinance dokümantasyonu: https://github.com/ranaroussi/yfinance
- Alpha Vantage API: https://www.alphavantage.co/documentation/

### Makine Öğrenmesi
- Scikit-learn: https://scikit-learn.org/stable/
- XGBoost: https://xgboost.readthedocs.io/

---

## ⚠️ ÖNEMLİ NOTLAR

1. **Yasal Uyarı**: Bu sistem sadece eğitim ve araştırma amaçlıdır. Yatırım tavsiyesi değildir.
2. **API Limitleri**: Ücretsiz API'lerin rate limit'lerine dikkat edin.
3. **Veri Doğruluğu**: Finansal verilerin doğruluğunu her zaman doğrulayın.
4. **Gizlilik**: API key'lerinizi asla public repository'lere yüklemeyin (`.env` dosyası kullanın).

---

## 📝 LİSANS

Bu proje eğitim amaçlıdır. Kendi sorumluluğunuzda kullanın.

---

## 🤝 KATKIDA BULUNMA

Projeyi geliştirmek için:
1. Fork edin
2. Feature branch oluşturun
3. Değişikliklerinizi commit edin
4. Pull request gönderin

---

**İyi çalışmalar! 🚀**

