# 🗺️ Borsa & AI Entegrasyonu - Detaylı Yol Haritası

Bu belge, mevcut finance_analysis projesini; siyasi, makroekonomik ve şirkete özel verileri birleştiren kapsamlı bir öngörü motoruna dönüştürmek için hazırlanmıştır.

## 🛑 Mevcut Durum Analizi (Gap Analysis)

| Özellik | Mevcut Durum | Hedeflenen Durum | Eksiklik/Yapılması Gereken |
|---------|--------------|------------------|----------------------------|
| **Veri Kaynağı** | yfinance, NewsAPI, Google Search | Ücretli/Profesyonel API'ler (FMP, Matriks/Foreks), Resmi Gazete, TCMB, Twitter | Veri çeşitliliği ve güvenilirliği artırılmalı. |
| **Siyasi Analiz** | Genel haber sentimenti (Pozitif/Negatif) | Olay Bazlı Etki Analizi (Event Study) | Siyasi olayların tarihsel piyasa tepkileriyle eşleştirilmesi. |
| **Tahmin Modeli** | Yön Tahmini (Classification - Up/Down) | Fiyat Hedefi & Volatilite Tahmini (Regression/Time-Series) | Sadece "artacak" değil, "ne kadar ve ne zaman" sorularına yanıt aranmalı. |
| **Veri Tabanı** | CSV/Pickle/Firestore (Basit) | Vektör Veritabanı + Time-Series DB | Haberlerin anlamsal aranması ve büyük finansal verinin saklanması. |
| **Arayüz** | Streamlit (Prototip) | Modern Web App (React/Next.js + FastAPI) | Özelleştirilebilir, interaktif ve hızlı bir kullanıcı deneyimi. |

---

## 🗓️ FAZ 1: Gelişmiş Veri Altyapısı ve "Politik Bağlam" (Hafta 1-3)

Siyasi haberlerin etkisini ölçmek için sadece kelimelere değil, **anlama** odaklanmalısın.

### 1.1. Vektör Veritabanı Entegrasyonu (RAG Mimarisi)

**Sorun:** Siyasi haberleri sadece "iyi/kötü" diye etiketlemek yetmez. **"Geçmişte benzer bir siyasi olay olduğunda borsa ne tepki verdi?"** sorusunu yanıtlamalısın.

**Teknoloji:** ChromaDB veya Pinecone

**İşlem:**

1. Geçmiş 10 yılın siyasi haberlerini ve o günkü BIST100 hareketlerini topla.
2. Haberleri embedding (vektör) haline getirip veritabanına kaydet.
3. Yeni bir siyasi haber geldiğinde, veritabanından "benzer geçmiş olayları" getir.
4. LLM'e (Gemini) şunu sor: *"Şu an X olayı oldu. Geçmişte benzer Y ve Z olaylarında borsa %3 düşmüş. Bu seferki beklenti nedir?"*

**Kod Yapısı:**
```
src/
  ├── vector_db/
  │   ├── __init__.py
  │   ├── chroma_client.py      # ChromaDB bağlantısı
  │   ├── news_embedder.py      # Haberleri embedding'e çevir
  │   └── historical_correlator.py  # Geçmiş olayları bul ve korelasyon hesapla
```

**Örnek Kullanım:**
```python
from src.vector_db.historical_correlator import HistoricalEventCorrelator

correlator = HistoricalEventCorrelator()
similar_events = correlator.find_similar_events(
    current_news="Bakan istifa etti",
    top_k=5
)
# Çıktı: [{"event": "2020-01-15: Bakan X istifa etti", "bist100_change": -2.3%, "similarity": 0.89}, ...]
```

### 1.2. Makroekonomik Korelasyon Motoru

`src/macro_data.py` dosyasını geliştir. Sadece faizi çekmek yetmez, **faizin sektörlere etkisini** hesaplamalısın.

**Görev:** Her sektörün (Bankacılık, Sanayi, GYO) faiz, dolar kuru ve enflasyon ile olan tarihsel korelasyon katsayısını hesaplayan bir modül yaz.

**Çıktı:** *"Faiz artarsa Bankalar X, GYO'lar Y etkilenir"* gibi dinamik katsayılar.

**Kod Yapısı:**
```python
# src/macro_correlation.py
def calculate_sector_macro_correlation(
    sector_tickers: List[str],
    macro_indicators: Dict[str, pd.Series]
) -> Dict[str, float]:
    """
    Sektörün makroekonomik göstergelerle korelasyonunu hesaplar.
    
    Örnek:
    {
        'interest_rate': -0.65,  # Faiz artarsa sektör düşer
        'usd_try': 0.45,         # Dolar artarsa sektör yükselir
        'inflation': -0.30        # Enflasyon artarsa sektör hafif düşer
    }
    """
```

### 1.3. Siyasi Haber Sınıflandırıcı

Haberleri sadece "Pozitif/Negatif" değil, **"Siyasi", "Ekonomik", "Şirket"** diye kategorize eden bir sınıflandırıcı ekle.

**Yeni Modül:** `src/political_classifier.py`

```python
def classify_news_category(news_text: str) -> Dict:
    """
    Haberi kategorize eder ve siyasi etki skorunu hesaplar.
    
    Çıktı:
    {
        'category': 'political',  # political, economic, company, market
        'subcategory': 'government_stability',  # government_stability, foreign_policy, etc.
        'political_impact_score': 0.75,  # 0-1 arası
        'market_relevance': 0.90  # Piyasaya ne kadar etkili?
    }
    """
```

---

## 🧠 FAZ 2: Derin Öğrenme ve Hibrit Modelleme (Hafta 4-6)

Mevcut Random Forest modelin iyi bir başlangıç, ancak karmaşık ilişkileri (örneğin bilanço + haber + grafik) birleştirmek için **hibrit bir yapıya** geçmelisin.

### 2.1. Çok Modlu (Multi-Modal) Tahmin Modeli

Şu an verileri (haber, fiyat) ayrı ayrı işleyip `scoring.py` içinde basit ağırlıklarla birleştiriyorsun. Bunu **tek bir modele öğretmelisin**.

**Yapı:**

```
Kol 1 (Sayısal): Fiyatlar, indikatörler, bilanço rasyoları -> LSTM veya GRU katmanı
Kol 2 (Metinsel): Haber embedding'leri (BERT/FinBERT çıktısı) -> Dense katman
Birleşim: İki kolun çıktılarını birleştirip (Concatenate) nihai kararı veren bir yapay sinir ağı
```

**Yeni Modül:** `src/multimodal_predictor.py`

```python
class MultimodalPricePredictor:
    """
    Fiyat verisi + Haber verisi + Makro veriyi birleştiren hibrit model.
    """
    def __init__(self):
        # LSTM katmanı (fiyat zaman serisi için)
        self.price_lstm = LSTM(...)
        
        # Dense katman (haber embedding'leri için)
        self.news_dense = Dense(...)
        
        # Birleştirme katmanı
        self.fusion_layer = Concatenate()([price_output, news_output])
        self.final_predictor = Dense(...)
```

### 2.2. Bilanço Analizini Derinleştirme

`financial_analysis.py` içindeki temel rasyoları (F/K, PD/DD) geliştirmelisin.

**Eklemeler:**

1. **Trend Analizi:** Şirketin cirosu enflasyondan arındırıldığında reel olarak büyüyor mu?
2. **Sektör Kıyaslaması:** Şirketin rasyolarını, kendi sektör ortalamasıyla dinamik olarak kıyasla.

**Yeni Fonksiyonlar:**
```python
# src/financial_analysis.py
def calculate_inflation_adjusted_growth(revenue_series: pd.Series, inflation_series: pd.Series) -> float:
    """Enflasyondan arındırılmış büyüme oranı"""

def compare_with_sector_averages(ticker: str, sector: str) -> Dict:
    """Sektör ortalamalarıyla kıyaslama"""
```

### 2.3. Volatilite ve Risk Tahmini

Sadece "yukarı/aşağı" değil, **"ne kadar riskli?"** sorusunu da yanıtlamalısın.

**Yeni Modül:** `src/volatility_predictor.py`

```python
def predict_volatility(
    price_history: pd.DataFrame,
    news_sentiment: float,
    macro_indicators: Dict
) -> Dict:
    """
    Gelecek 30 günlük volatilite tahmini.
    
    Çıktı:
    {
        'expected_volatility': 0.25,  # %25 volatilite bekleniyor
        'risk_level': 'high',  # high, medium, low
        'confidence_interval': (0.20, 0.30)  # %95 güven aralığı
    }
    """
```

---

## 💻 FAZ 3: Web Tasarımı ve Kullanıcı Deneyimi (Hafta 7-9)

Streamlit prototip aşaması için harika, ancak "tasarım" dediğin noktada özelleşmiş bir Frontend gerekir.

### 3.1. Backend API (FastAPI) Geliştirmesi

Mevcut `api/main.py` dosyanı genişlet.

**Yeni Endpoint'ler:**

```python
# api/main.py
@app.post("/news-impact")
async def analyze_news_impact(news_text: str, ticker: str):
    """
    Haberin hisseye etkisini analiz eder.
    - Siyasi mi? Ekonomik mi?
    - Geçmişte benzer olaylar ne yaptı?
    - Beklenen fiyat etkisi nedir?
    """

@app.get("/technical-forecast/{ticker}")
async def get_technical_forecast(ticker: str, period: str = "30d"):
    """
    Teknik analiz + AI sinyalleri.
    - Fiyat hedefi
    - Destek/direnç seviyeleri
    - AL/SAT sinyalleri
    """

@app.post("/fundamental-score")
async def calculate_fundamental_score(ticker: str):
    """
    Temel analiz skoru.
    - Bilanço analizi
    - Sektör kıyaslaması
    - Enflasyon etkisi
    """

@app.websocket("/live-updates")
async def live_updates(websocket: WebSocket):
    """
    Canlı veri akışı.
    - Anlık haber bildirimleri
    - Fiyat güncellemeleri
    - AI sinyal değişiklikleri
    """
```

### 3.2. Modern Frontend (React veya Next.js)

Kullanıcıya profesyonel bir "Terminal" hissi ver.

**Dashboard Bileşenleri:**

- **Sol Panel:** Canlı haber akışı (Siyasi/Şirket ayrımı yapılmış)
- **Orta Panel:** TradingView grafikleri (Lightweight Charts kütüphanesi) üzerine AI sinyallerinin ("Burada al çünkü faiz kararı açıklandı") işlenmesi
- **Sağ Panel:** "AI Analist Özeti" (Gemini'den gelen metin raporu)

**Klasör Yapısı:**
```
frontend/
  ├── src/
  │   ├── components/
  │   │   ├── NewsFeed.tsx
  │   │   ├── PriceChart.tsx
  │   │   ├── AISignals.tsx
  │   │   └── AnalystReport.tsx
  │   ├── services/
  │   │   └── api.ts
  │   └── App.tsx
```

---

## ⚙️ FAZ 4: Otomasyon ve MLOps (Hafta 10+)

Sistemi canlı tutmak ve kendi kendine öğrenmesini sağlamak.

### 4.1. Sürekli Öğrenme (Continuous Learning)

Modelin tahminlerini kaydet. Gerçekleşen fiyatlarla tahminleri kıyasla. Haftada bir modeli yeni verilerle otomatik olarak yeniden eğit.

**Yeni Modül:** `scripts/auto_retrain.py`

```python
def auto_retrain_model():
    """
    Haftalık otomatik model yeniden eğitimi.
    - Yeni verileri topla
    - Model performansını değerlendir
    - Eğer performans düşmüşse, modeli yeniden eğit
    - MLflow'a kaydet
    """
```

**Cron Job:**
```bash
# Her Pazar gecesi 02:00'de çalıştır
0 2 * * 0 cd /path/to/project && python scripts/auto_retrain.py
```

### 4.2. Uyarı Sistemi

Kullanıcı, *"Faiz kararı sonrası Bankacılık endeksi %2 düşerse bana haber ver"* gibi karmaşık senaryolar kurabilsin.

**Yeni Modül:** `src/alert_system.py`

```python
class AlertEngine:
    """
    Karmaşık senaryo bazlı uyarı sistemi.
    """
    def create_alert(
        self,
        condition: str,  # "interest_rate_change > 0.5 AND banking_index_change < -0.02"
        notification_method: str  # "email", "sms", "push"
    ):
        """
        Kullanıcı tanımlı uyarı oluşturur.
        """
```

---

## 🛠️ Hemen Yapman Gereken Pratik Düzenlemeler (Kod Bazlı)

Mevcut kodlarında şu an yapabileceğin hızlı iyileştirmeler:

### 1. Siyasi Haber Sınıflandırıcı Ekle

**Dosya:** `src/political_classifier.py` (YENİ)

```python
"""
Siyasi haberleri kategorize eden ve etki skorunu hesaplayan modül.
"""

import os
from typing import Dict, Optional
import google.generativeai as genai

def classify_news_political_impact(news_text: str, news_title: str = "") -> Dict:
    """
    Haberi siyasi/ekonomik/şirket kategorisine ayırır ve etki skorunu hesaplar.
    
    Parametreler:
    ------------
    news_text : str
        Haber metni
    news_title : str
        Haber başlığı (opsiyonel)
    
    Döndürür:
    --------
    dict
        {
            'category': 'political',  # political, economic, company, market
            'subcategory': 'government_stability',  # government_stability, foreign_policy, economic_policy, etc.
            'political_impact_score': 0.75,  # 0-1 arası
            'market_relevance': 0.90,  # Piyasaya ne kadar etkili? (0-1)
            'expected_market_reaction': 'negative',  # positive, negative, neutral
            'confidence': 0.85
        }
    """
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        # Gemini yoksa basit kural tabanlı sınıflandırma
        return _simple_political_classifier(news_text, news_title)
    
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
Aşağıdaki haber metnini analiz et ve şu bilgileri JSON formatında döndür:

1. **Kategori:** Haber siyasi mi, ekonomik mi, şirket bazlı mı, yoksa genel piyasa haberi mi?
   - "political": Siyasi olaylar (hükümet, bakan, seçim, dış politika)
   - "economic": Ekonomik politika (faiz, enflasyon, bütçe)
   - "company": Belirli bir şirket hakkında
   - "market": Genel piyasa haberi

2. **Alt Kategori (siyasi ise):**
   - "government_stability": Hükümet istikrarı
   - "foreign_policy": Dış politika
   - "economic_policy": Ekonomi yönetimi
   - "election": Seçim
   - "other": Diğer

3. **Siyasi Etki Skoru:** 0-1 arası (siyasi değilse 0)

4. **Piyasa İlgisi:** Bu haberin borsaya etkisi ne kadar? 0-1 arası

5. **Beklenen Piyasa Tepkisi:** "positive", "negative", "neutral"

6. **Güven:** Analiz güvenilirliği 0-1 arası

Haber Başlığı: {news_title}
Haber Metni: {news_text[:1000]}

Sadece JSON formatında yanıt ver, başka açıklama yapma:
{{
    "category": "...",
    "subcategory": "...",
    "political_impact_score": 0.0-1.0,
    "market_relevance": 0.0-1.0,
    "expected_market_reaction": "...",
    "confidence": 0.0-1.0
}}
"""
        
        response = model.generate_content(prompt)
        # JSON parse et
        import json
        import re
        json_match = re.search(r'\{[^}]+\}', response.text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return _simple_political_classifier(news_text, news_title)
            
    except Exception as e:
        print(f"⚠️  Gemini siyasi sınıflandırma hatası: {e}")
        return _simple_political_classifier(news_text, news_title)


def _simple_political_classifier(news_text: str, news_title: str = "") -> Dict:
    """
    Basit kural tabanlı siyasi sınıflandırma (Gemini yoksa).
    """
    text_lower = (news_title + " " + news_text).lower()
    
    # Siyasi anahtar kelimeler
    political_keywords = ['bakan', 'hükümet', 'cumhurbaşkanı', 'başbakan', 'seçim', 
                         'milletvekili', 'parti', 'koalisyon', 'istifa', 'güvenoyu',
                         'dış politika', 'diplomasi', 'anayasa', 'meclis']
    
    # Ekonomik anahtar kelimeler
    economic_keywords = ['faiz', 'enflasyon', 'tcmb', 'merkez bankası', 'bütçe',
                        'maliye', 'hazine', 'borç', 'açık']
    
    political_score = sum(1 for keyword in political_keywords if keyword in text_lower) / len(political_keywords)
    economic_score = sum(1 for keyword in economic_keywords if keyword in text_lower) / len(economic_keywords)
    
    if political_score > 0.3:
        category = 'political'
        subcategory = 'government_stability' if 'istifa' in text_lower or 'güvenoyu' in text_lower else 'other'
    elif economic_score > 0.3:
        category = 'economic'
        subcategory = 'economic_policy'
    else:
        category = 'market'
        subcategory = 'other'
    
    return {
        'category': category,
        'subcategory': subcategory,
        'political_impact_score': political_score,
        'market_relevance': max(political_score, economic_score),
        'expected_market_reaction': 'negative' if 'istifa' in text_lower or 'kriz' in text_lower else 'neutral',
        'confidence': 0.6  # Basit sınıflandırma için düşük güven
    }
```

### 2. Enflasyon Muhasebesi Ekle

**Dosya:** `src/financial_analysis.py` (GÜNCELLEME)

```python
def calculate_inflation_adjusted_metrics(
    revenue_series: pd.Series,
    inflation_series: pd.Series,
    start_date: str = None
) -> Dict:
    """
    Enflasyondan arındırılmış finansal metrikler hesaplar.
    
    Türk borsası için kritik: Nominal büyüme yanıltıcı olabilir.
    """
    # Enflasyon oranını hesapla
    inflation_rate = inflation_series.pct_change().mean()
    
    # Reel büyüme = Nominal büyüme - Enflasyon
    nominal_growth = revenue_series.pct_change().mean()
    real_growth = nominal_growth - inflation_rate
    
    return {
        'nominal_growth': nominal_growth,
        'real_growth': real_growth,
        'inflation_impact': inflation_rate,
        'is_real_growth_positive': real_growth > 0
    }
```

### 3. Vektör Veritabanı Entegrasyonu (ChromaDB)

**Yeni Modül:** `src/vector_db/` klasörü

**requirements.txt'e ekle:**
```
chromadb>=0.4.0
sentence-transformers>=2.2.0
```

---

## 📊 Öncelik Sırası (Hemen Başla)

### Hafta 1-2: Temel İyileştirmeler
1. ✅ Siyasi haber sınıflandırıcı ekle (`src/political_classifier.py`)
2. ✅ Enflasyon muhasebesi ekle (`src/financial_analysis.py`)
3. ✅ ChromaDB entegrasyonu başlat (`src/vector_db/`)

### Hafta 3-4: Veri Altyapısı
1. Geçmiş 5 yılın siyasi haberlerini topla ve vektör veritabanına kaydet
2. Tarihsel olay korelasyonu modülü yaz
3. Makroekonomik korelasyon motoru geliştir

### Hafta 5-6: Model Geliştirme
1. Multi-modal tahmin modeli tasarla
2. Volatilite tahmini ekle
3. Model performansını değerlendir ve iyileştir

### Hafta 7+: Ürünleştirme
1. FastAPI endpoint'lerini genişlet
2. Modern frontend tasarla
3. Sürekli öğrenme sistemi kur

---

## 🎯 Başarı Kriterleri

Proje başarılı sayılır eğer:

- ✅ Siyasi haberler otomatik olarak kategorize ediliyor
- ✅ Geçmiş benzer olaylar bulunup korelasyon hesaplanıyor
- ✅ Model tahminleri %60+ doğrulukta
- ✅ Kullanıcı karmaşık senaryolar oluşturabiliyor
- ✅ Sistem otomatik olarak öğreniyor ve güncelleniyor

---

## 📚 Kaynaklar ve Referanslar

- **ChromaDB Dokümantasyonu:** https://docs.trychroma.com/
- **Gemini API:** https://ai.google.dev/docs
- **TradingView Lightweight Charts:** https://www.tradingview.com/lightweight-charts/
- **FastAPI WebSocket:** https://fastapi.tiangolo.com/advanced/websockets/

---

## 💡 Sonuç

Bu yol haritası, projeni "amatör bir analiz aracı"ndan "profesyonel bir Fintech ürünü"ne dönüştürecek. Adım adım ilerleyerek, her fazın çıktılarını test edip kullanıcı geri bildirimlerine göre yönlendirebilirsin.

**Önemli:** Tüm fazları aynı anda yapmaya çalışma. Önce FAZ 1'i tamamla, test et, sonra FAZ 2'ye geç.

