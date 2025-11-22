# 🔍 Mevcut Durum Analizi ve Yol Haritası Açıklaması

Bu dokümantasyon, projenin mevcut durumunu, eksikliklerini ve bunların nasıl giderileceğini detaylıca açıklar.

---

## 📊 Mevcut Durum Değerlendirmesi (Gap Analizi)

### 🟡 Siyasi Analiz - Kısmen Var

**Durum:** `political_classifier.py` modülü çalışıyor ve haberleri kategorize edebiliyor.

**Ne Yapıyor?**
- Haberi okuyor: "Ekonomi Bakanı istifa etti"
- Kategorize ediyor: `category: 'political'`, `subcategory: 'government_stability'`
- Etki skoru veriyor: `political_impact_score: 0.75`
- Beklenen tepkiyi tahmin ediyor: `expected_market_reaction: 'negative'`

**Sorun: "Hafıza Eksikliği"**

Şu an sistem her haberi **"ilk kez görüyormuş gibi"** analiz ediyor. Örneğin:

```
Yeni Haber: "Ekonomi Bakanı istifa etti"
Sistem: "Bu siyasi bir haber, negatif etkisi olabilir"
```

Ama sistem şunu **bilmiyor**:
- 2020'de benzer bir istifa olduğunda BIST100 %2.3 düştü
- 2018'de başka bir istifa olduğunda BIST100 %1.5 düştü
- 2015'te benzer bir olayda BIST100 %3.1 düştü

**Çözüm: Vektör Veritabanı (RAG Mimarisi)**

Sisteme bir "hafıza" ekleyeceğiz. Geçmiş siyasi olayları ve o günkü borsa tepkilerini saklayacağız. Yeni bir haber geldiğinde:

1. **Benzer geçmiş olayları bul** (vektör benzerliği ile)
2. **Geçmişte ne olduğunu göster** (BIST100 ne kadar değişti?)
3. **Gemini'ye sor:** "Geçmişte benzer olaylarda borsa düşmüş, şimdi ne olur?"

---

### ✅ Finansal Analiz - Çok İyi

**Durum:** `src/financial_analysis.py` modülü gelişmiş özelliklere sahip.

**Ne Yapıyor?**
- ✅ Enflasyon muhasebesi: Nominal büyümeyi enflasyondan arındırıp reel büyümeyi hesaplıyor
- ✅ Sektör kıyaslaması: Şirketin rasyolarını sektör ortalamalarıyla karşılaştırıyor
- ✅ Teknik indikatörler: RSI, MACD, Bollinger Bands, vb.
- ✅ Finansal skor: 0-100 arası sağlık skoru

**Örnek:**
```python
# Enflasyon muhasebesi
metrics = calculate_inflation_adjusted_metrics(
    revenue_series=revenue_data,  # Şirket cirosu
    inflation_series=inflation_data  # TCMB enflasyon verisi
)

# Çıktı:
{
    'nominal_growth': 25.0,  # Nominal büyüme %25
    'real_growth': 5.0,      # Reel büyüme %5 (enflasyondan arındırılmış)
    'inflation_impact': 20.0,  # Enflasyon etkisi %20
    'is_real_growth_positive': True  # Reel büyüme pozitif
}
```

**Yorum:** Bu özellikler Türk borsası için kritik. Enflasyonist ortamda nominal büyüme yanıltıcı olabilir.

---

### ✅ Güvenilirlik (MLOps) - Harika

**Durum:** Profesyonel bir model yönetim yapısı kurulmuş.

**Ne Yapıyor?**
- ✅ **MLflow:** Model versiyonlama ve takip
- ✅ **Data Drift Monitoring:** Modelin "bayatlamasını" tespit ediyor
- ✅ **Otomatik Yeniden Eğitim:** Model performansı düşerse uyarı veriyor

**Örnek:**
```python
# scripts/mlflow_training.py
# Model eğitildiğinde MLflow'a kaydediliyor
mlflow.log_model(model, "price_predictor")
mlflow.log_metrics({"accuracy": 0.65, "precision": 0.70})

# scripts/data_drift_monitoring.py
# Model performansı düşerse uyarı veriyor
if drift_detected:
    send_alert("Model performansı düştü, yeniden eğitim gerekli!")
```

**Yorum:** Bu, projenin "amatör araç"tan "profesyonel ürün"e geçişini gösteren en önemli özellik.

---

### ✅ Strateji - İyi

**Durum:** `backtesting.py` ile gerçekçi performans testi yapılabiliyor.

**Ne Yapıyor?**
- ✅ **Walk-Forward Test:** Modeli geçmişte test ediyor (gerçekçi senaryo)
- ✅ **Performans Metrikleri:** Sharpe Ratio, Max Drawdown, Win Rate
- ✅ **Strateji Optimizasyonu:** Farklı parametrelerle test edip en iyisini buluyor

**Örnek:**
```python
results = run_walk_forward_backtest(
    ticker="THYAO",
    train_period=252,  # 1 yıl eğitim
    test_period=63,    # 3 ay test
    step_size=21       # Her ay yeni test
)

# Çıktı:
{
    'total_return': 15.3,  # Toplam getiri %15.3
    'sharpe_ratio': 1.2,   # Risk-ayarlı getiri
    'max_drawdown': -8.5,  # En büyük düşüş %8.5
    'win_rate': 0.58       # Kazanma oranı %58
}
```

**Yorum:** Bu, modelin gerçek piyasada nasıl performans göstereceğini tahmin etmek için kritik.

---

### 🟠 Mimari - Geçiş Aşamasında

**Durum:** Backend (FastAPI) var ama Frontend (Streamlit) hala doğrudan `src` klasöründen import yapıyor.

**Sorun:**
- `app.py` (Streamlit) → `src/main.py` → `src/data_collection.py` (doğrudan import)
- Bu, modüler bir yapı değil, "monolitik" bir yapı

**Hedef:**
```
Frontend (React/Next.js)
    ↓ HTTP/WebSocket
Backend (FastAPI)
    ↓ API Calls
src/ (Business Logic)
    ↓
Vector DB / Time-Series DB
```

**Yorum:** Şu an çalışıyor ama ölçeklenebilir değil. Büyük projelerde Frontend ve Backend ayrılmalı.

---

## 🗺️ Yeni Yol Haritası: "Bilişsel Zeka ve Ölçeklenme"

### 🧠 FAZ 1: Hafıza Sistemi (RAG Mimarisi)

**Hedef:** Sisteme "geçmişi hatırlama" yeteneği kazandırmak.

#### 1.1. Vektör Veritabanı Kurulumu (ChromaDB)

**Ne Yapacağız?**

1. **Geçmiş Verileri Topla:**
   - Son 10 yılın siyasi haberleri
   - O günkü BIST100 kapanış fiyatı
   - BIST100 değişim yüzdesi

2. **Vektörleştir:**
   - Her haberi embedding'e çevir (sentence-transformers)
   - ChromaDB'ye kaydet

3. **Benzer Olayları Bul:**
   - Yeni haber geldiğinde, vektör benzerliği ile geçmiş olayları bul
   - En benzer 5 olayı getir

4. **Korelasyon Hesapla:**
   - Geçmiş olaylarda BIST100 ne kadar değişti?
   - Ortalama değişim nedir?
   - Gemini'ye sor: "Geçmişte böyle olduğunda borsa düşmüş, şimdi ne olur?"

**Kod Yapısı:**
```python
# src/vector_db/historical_correlator.py
class HistoricalEventCorrelator:
    def __init__(self):
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection("political_events")
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    def add_historical_event(self, news_text: str, date: str, bist100_change: float):
        """Geçmiş olayı veritabanına ekle"""
        embedding = self.embedder.encode(news_text)
        self.collection.add(
            embeddings=[embedding.tolist()],
            documents=[news_text],
            metadatas=[{
                'date': date,
                'bist100_change': bist100_change,
                'event_type': 'political'
            }],
            ids=[f"event_{date}_{hash(news_text)}"]
        )
    
    def find_similar_events(self, current_news: str, top_k: int = 5):
        """Benzer geçmiş olayları bul"""
        query_embedding = self.embedder.encode(current_news)
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        similar_events = []
        for i, doc in enumerate(results['documents'][0]):
            similar_events.append({
                'event': doc,
                'date': results['metadatas'][0][i]['date'],
                'bist100_change': results['metadatas'][0][i]['bist100_change'],
                'similarity': 1 - results['distances'][0][i]  # Cosine distance'ı similarity'ye çevir
            })
        
        return similar_events
```

**Kullanım Örneği:**
```python
from src.vector_db.historical_correlator import HistoricalEventCorrelator

correlator = HistoricalEventCorrelator()

# Yeni haber geldiğinde
current_news = "Ekonomi Bakanı istifa etti"

# Benzer geçmiş olayları bul
similar_events = correlator.find_similar_events(current_news, top_k=5)

# Çıktı:
[
    {
        'event': '2020-01-15: Ekonomi Bakanı X istifa etti',
        'date': '2020-01-15',
        'bist100_change': -2.3,  # BIST100 %2.3 düştü
        'similarity': 0.89
    },
    {
        'event': '2018-05-20: Maliye Bakanı Y istifa etti',
        'date': '2018-05-20',
        'bist100_change': -1.5,
        'similarity': 0.82
    },
    # ... 3 tane daha
]

# Gemini'ye sor
prompt = f"""
Şu anki olay: {current_news}

Geçmişte benzer olaylar:
{similar_events}

Geçmişte benzer olaylarda BIST100 ortalama %{avg_change:.2f} değişti.
Bu seferki beklenti nedir? Neden?
"""

gemini_response = gemini_model.generate_content(prompt)
# Çıktı: "Geçmişte benzer istifalar borsayı ortalama %2.1 düşürdü. 
#         Ancak şu anki ekonomik ortam farklı olduğu için 
#         beklenen düşüş %1.5-2.0 arası olabilir."
```

#### 1.2. Veri Toplama Script'i

**Ne Yapacağız?**

Geçmiş 10 yılın siyasi haberlerini ve BIST100 verilerini toplayıp veritabanına yükleyeceğiz.

**Kod:**
```python
# scripts/populate_historical_events.py
def collect_historical_data():
    """Geçmiş 10 yılın verilerini topla"""
    
    # 1. BIST100 fiyat verilerini çek (yfinance)
    bist100 = yf.Ticker("XU100.IS")
    hist = bist100.history(period="10y")
    
    # 2. Her gün için siyasi haberleri bul (NewsAPI arşiv)
    for date in pd.date_range(start="2014-01-01", end="2024-01-01", freq="D"):
        # O günkü siyasi haberleri bul
        news = get_news(
            company_name="Türkiye",  # Genel siyasi haberler
            days_back=1,
            api_key=NEWS_API_KEY
        )
        
        # Sadece siyasi haberleri filtrele
        political_news = news[news['political_category'] == 'political']
        
        # BIST100 değişimini hesapla
        if date in hist.index:
            prev_date = hist.index[hist.index < date][-1] if len(hist.index[hist.index < date]) > 0 else None
            if prev_date:
                change = (hist.loc[date, 'Close'] / hist.loc[prev_date, 'Close'] - 1) * 100
                
                # Her siyasi haberi veritabanına ekle
                for _, news_row in political_news.iterrows():
                    correlator.add_historical_event(
                        news_text=news_row['title'] + " " + news_row['summary'],
                        date=date.strftime("%Y-%m-%d"),
                        bist100_change=change
                    )
```

---

### 🧠 FAZ 2: Makroekonomik Korelasyon Motoru

**Hedef:** Her sektörün makroekonomik göstergelerle (faiz, dolar, enflasyon) olan korelasyonunu hesaplamak.

**Ne Yapacağız?**

```python
# src/macro_correlation.py
def calculate_sector_macro_correlation(
    sector_tickers: List[str],  # Örn: ["AKBNK", "GARAN", "ISCTR"] (Bankacılık)
    macro_indicators: Dict[str, pd.Series]  # {'interest_rate': Series, 'usd_try': Series, ...}
) -> Dict[str, float]:
    """
    Sektörün makroekonomik göstergelerle korelasyonunu hesaplar.
    
    Örnek:
    {
        'interest_rate': -0.65,  # Faiz artarsa sektör düşer (negatif korelasyon)
        'usd_try': 0.45,         # Dolar artarsa sektör yükselir (pozitif korelasyon)
        'inflation': -0.30        # Enflasyon artarsa sektör hafif düşer
    }
    """
    # Sektör endeksi oluştur (tüm hisselerin ortalaması)
    sector_prices = []
    for ticker in sector_tickers:
        stock = yf.Ticker(f"{ticker}.IS")
        hist = stock.history(period="2y")
        if not hist.empty:
            sector_prices.append(hist['Close'])
    
    if not sector_prices:
        return {}
    
    sector_index = pd.concat(sector_prices, axis=1).mean(axis=1)
    sector_returns = sector_index.pct_change()
    
    # Her makro gösterge ile korelasyon hesapla
    correlations = {}
    for indicator_name, indicator_series in macro_indicators.items():
        # Gösterge değişim oranını hesapla
        indicator_returns = indicator_series.pct_change()
        
        # Tarihleri hizala
        aligned_returns = pd.concat([sector_returns, indicator_returns], axis=1).dropna()
        
        if len(aligned_returns) > 30:  # En az 30 veri noktası
            correlation = aligned_returns.iloc[:, 0].corr(aligned_returns.iloc[:, 1])
            correlations[indicator_name] = correlation
    
    return correlations
```

**Kullanım:**
```python
# Bankacılık sektörü için
banking_tickers = ["AKBNK", "GARAN", "ISCTR", "YKBNK", "HALKB"]
macro_data = {
    'interest_rate': tcmb_data['interest_rate'],
    'usd_try': tcmb_data['usd_try'],
    'inflation': tcmb_data['inflation']
}

correlations = calculate_sector_macro_correlation(banking_tickers, macro_data)

# Çıktı:
{
    'interest_rate': -0.65,  # Faiz artarsa bankalar düşer
    'usd_try': 0.45,         # Dolar artarsa bankalar yükselir
    'inflation': -0.30        # Enflasyon artarsa bankalar hafif düşer
}

# Tahmin:
# "TCMB faizi %50'den %55'e çıkarırsa, bankacılık endeksi yaklaşık %3.25 düşer"
# (0.65 * 5 puan faiz artışı = 3.25 puan düşüş)
```

---

### 🧠 FAZ 3: Çok Modlu (Multi-Modal) Tahmin Modeli

**Hedef:** Fiyat verisi + Haber verisi + Makro veriyi tek bir modelde birleştirmek.

**Şu Anki Durum:**
- Fiyat verisi → `compute_features()` → Feature vektörü
- Haber verisi → `sentiment_analysis.py` → Sentiment skoru
- İkisi ayrı ayrı hesaplanıp `scoring.py` içinde basit ağırlıklarla birleştiriliyor

**Hedef:**
- Fiyat verisi → LSTM katmanı → Feature embedding
- Haber verisi → BERT/FinBERT → Text embedding
- Makro veri → Dense katman → Macro embedding
- Üçü birleştirilip → Final Dense katman → Tahmin

**Kod Yapısı:**
```python
# src/multimodal_predictor.py
import torch
import torch.nn as nn
from transformers import AutoModel

class MultimodalPricePredictor(nn.Module):
    def __init__(self):
        super().__init__()
        
        # Kol 1: Fiyat zaman serisi (LSTM)
        self.price_lstm = nn.LSTM(
            input_size=20,  # 20 feature (RSI, MACD, vb.)
            hidden_size=64,
            num_layers=2,
            batch_first=True
        )
        
        # Kol 2: Haber metni (BERT)
        self.news_bert = AutoModel.from_pretrained('ProsusAI/finbert')
        self.news_dense = nn.Linear(768, 64)  # BERT çıktısı 768 boyutlu
        
        # Kol 3: Makro veri (Dense)
        self.macro_dense = nn.Linear(5, 32)  # 5 makro gösterge (faiz, dolar, enflasyon, vb.)
        
        # Birleştirme katmanı
        self.fusion = nn.Linear(64 + 64 + 32, 128)
        self.final_predictor = nn.Linear(128, 3)  # 3 sınıf: up, down, neutral
    
    def forward(self, price_seq, news_embeddings, macro_features):
        # Kol 1: Fiyat
        price_out, _ = self.price_lstm(price_seq)
        price_out = price_out[:, -1, :]  # Son zaman adımını al
        
        # Kol 2: Haber
        news_out = self.news_bert(**news_embeddings).last_hidden_state[:, 0, :]  # [CLS] token
        news_out = self.news_dense(news_out)
        
        # Kol 3: Makro
        macro_out = self.macro_dense(macro_features)
        
        # Birleştir
        fused = torch.cat([price_out, news_out, macro_out], dim=1)
        fused = torch.relu(self.fusion(fused))
        
        # Tahmin
        prediction = self.final_predictor(fused)
        return prediction
```

---

## 🎯 Özet: Ne Yapmalısın?

### Hemen (Bu Hafta):

1. **ChromaDB Kurulumu:**
   ```bash
   pip install chromadb sentence-transformers
   ```

2. **Vektör Veritabanı Modülü Oluştur:**
   - `src/vector_db/` klasörü oluştur
   - `historical_correlator.py` dosyasını yaz
   - Geçmiş 1 yılın verilerini toplayıp veritabanına yükle (test için)

3. **Siyasi Analiz Modülünü Güncelle:**
   - `political_classifier.py`'yi `historical_correlator` ile entegre et
   - Yeni haber geldiğinde geçmiş olayları bul ve Gemini'ye sor

### Kısa Vadede (1-2 Hafta):

1. **Makroekonomik Korelasyon Motoru:**
   - `src/macro_correlation.py` dosyasını oluştur
   - Her sektör için korelasyon katsayılarını hesapla

2. **Veri Toplama Script'i:**
   - `scripts/populate_historical_events.py` oluştur
   - Geçmiş 10 yılın verilerini topla (bir kere çalıştır, sonra günlük güncelle)

### Orta Vadede (1 Ay):

1. **Multi-Modal Model:**
   - PyTorch ile hibrit model tasarla
   - Eğit ve test et

2. **Frontend-Backend Ayrımı:**
   - React/Next.js frontend oluştur
   - FastAPI backend'i genişlet

---

## 💡 Sonuç

**Şu Anki Durum:** MVP+ (Gelişmiş Prototip)
- ✅ Temel özellikler çalışıyor
- ✅ Finansal analiz gelişmiş
- ✅ MLOps yapısı kurulmuş
- ⚠️ Siyasi analiz "hafızasız"

**Hedef:** Profesyonel Fintech Ürünü
- ✅ Siyasi analiz "hafızalı" (RAG)
- ✅ Makroekonomik korelasyon motoru
- ✅ Multi-modal tahmin modeli
- ✅ Modern web arayüzü

**En Kritik Eksik:** **Hafıza**. Siyasi analiz modülü çalışıyor ama geçmişi hatırlamıyor. ChromaDB ile bu sorunu çözebilirsin.

**Sonraki Adım:** `src/vector_db/historical_correlator.py` dosyasını oluştur ve test et! 🚀

