# 🚀 AI Borsa Analisti - Faz 2: Hafıza ve Derinleşme

**Tarih:** 20 Kasım 2024  
**Durum:** MVP Tamamlandı → Gelişmiş Özellikler Fazına Geçiş

---

## 📋 Proje Durumu

### ✅ Tamamlananlar (MVP Fazı)

- ✅ Veri toplama (NewsAPI, Google News RSS, KAP)
- ✅ Sentiment analizi (FinBERT + Türkçe BERT + Gemini)
- ✅ Finansal analiz (teknik göstergeler, RSI, MACD, vb.)
- ✅ Temel ML modeli (RandomForest/XGBoost)
- ✅ Streamlit arayüzü
- ✅ FastAPI backend
- ✅ MLOps altyapısı (MLflow, data drift monitoring)

### 🎯 Yeni Hedefler (Faz 2)

Proje artık bir "araba" gibi çalışıyor. Şimdi eklememiz gerekenler:

1. **Dikiz Aynası (RAG/Memory):** Geçmişi görüp ona göre sürmesi için
2. **Yol Bilgisayarı (PDF Parser):** Detaylı raporları okuyup riskleri önceden söylemesi için
3. **Gelişmiş Motor (LSTM/Time-Series):** Daha akıllı tahminler için
4. **Navigasyon Sistemi (What-If):** Senaryo analizi için

---

## 🧠 FAZ 1: "Tarihsel Hafıza" (RAG Mimarisi) - ÖNCELİKLİ

**Hedef:** Siyasi ve ekonomik haberleri geçmişteki benzerleriyle kıyaslayarak piyasa tepkisini öngörmek.

### ✅ Tamamlananlar

- [x] `chromadb` ve `sentence-transformers` requirements.txt'e eklendi
- [x] `src/vector_memory.py` modülü oluşturuldu
- [x] `HistoricalMemory` sınıfı implementasyonu
- [x] Embedding modeli entegrasyonu (`paraphrase-multilingual-MiniLM-L12-v2`)
- [x] Benzer olay arama fonksiyonu
- [x] Gemini için bağlam metni oluşturma
- [x] `app.py`'ye "Geçmiş Benzer Olaylar" bölümü eklendi

### 📝 Yapılacaklar

- [ ] Geçmiş verileri toplama scripti (`populate_historical_data()`)
- [ ] Otomatik veri yükleme (cron job veya scheduled task)
- [ ] BIST100 değişim verilerini otomatik çekme
- [ ] Siyasi haberleri otomatik kategorize etme ve kaydetme

### 🔧 Kullanım

```python
from src.vector_memory import HistoricalMemory

# Memory instance'ı oluştur
memory = HistoricalMemory()

# Geçmiş olay ekle
memory.add_historical_event(
    news_text="Ekonomi Bakanı istifa etti",
    news_title="Ekonomi Bakanı İstifa Etti",
    date="2020-01-15",
    bist100_change=-2.3,
    category="political"
)

# Benzer olayları bul
similar = memory.find_similar_events(
    current_news="Maliye Bakanı istifa etti",
    current_title="Maliye Bakanı İstifa Etti",
    top_k=5
)
```

---

## 📄 FAZ 2: Derin Belge Analizi (PDF Parsing)

**Hedef:** KAP bildirimlerinin ve Faaliyet Raporlarının içini okuyarak detaylı temel analiz yapmak.

### ✅ Tamamlananlar

- [x] `pypdf`, `PyPDF2`, `pdfplumber` requirements.txt'e eklendi
- [x] `src/pdf_parser.py` modülü oluşturuldu
- [x] `PDFParser` sınıfı implementasyonu
- [x] PDF indirme fonksiyonu
- [x] Metin çıkarma (pypdf + pdfplumber fallback)
- [x] Metin chunking (Gemini token limiti için)
- [x] Gemini ile otomatik analiz (riskler, fırsatlar, önemli metrikler)

### 📝 Yapılacaklar

- [ ] KAP scraper ile PDF linklerini otomatik bulma
- [ ] PDF cache mekanizması (aynı PDF'i tekrar indirmeme)
- [ ] OCR desteği (görsel PDF'ler için)
- [ ] Tablo çıkarma (mali tablolar için)
- [ ] `app.py`'ye PDF analiz sonuçlarını gösterme

### 🔧 Kullanım

```python
from src.pdf_parser import PDFParser

parser = PDFParser()

# KAP PDF'ini parse et
result = parser.parse_kap_pdf(
    kap_url="https://www.kap.org.tr/tr/Bildirim/123456",
    report_title="Faaliyet Raporu"
)

if result['success']:
    print(result['analysis']['summary'])
    print(result['analysis']['risks'])
    print(result['analysis']['opportunities'])
```

---

## 🤖 FAZ 3: Model İyileştirmeleri (Zaman Serisi)

**Hedef:** Sadece "Yön" değil, "Fiyat" ve "Volatilite" tahmini.

### ✅ Tamamlananlar

- [x] Sentiment hareketli ortalamaları (`hisse_duygu_ma_3/7/14/30`)
- [x] Sentiment momentum ve volatilite özellikleri
- [x] Piyasa duygu skorları için hareketli ortalamalar
- [x] `compute_features()` fonksiyonuna sentiment özellikleri eklendi

### 📝 Yapılacaklar

- [ ] LSTM (Long Short-Term Memory) modeli implementasyonu
- [ ] Multi-modal model (metin + sayısal veri)
- [ ] Volatilite tahmin modeli (GARCH benzeri)
- [ ] Fiyat tahmin modeli (regression)
- [ ] Model ensemble (RandomForest + LSTM + XGBoost)

### 🔧 Özellik Mühendisliği

```python
# Yeni özellikler (financial_analysis.py'de eklendi):
- hisse_duygu_ma_3/7/14/30  # Sentiment hareketli ortalamaları
- hisse_duygu_momentum       # Sentiment trend hızı
- hisse_duygu_volatility     # Sentiment değişkenliği
- piyasa_duygu_ma_3/7/14/30 # Piyasa sentiment hareketli ortalamaları
- piyasa_duygu_momentum      # Piyasa sentiment trend hızı
- piyasa_duygu_volatility    # Piyasa sentiment değişkenliği
```

---

## 🌐 FAZ 4: Arayüz ve Otonomi

**Hedef:** Kullanıcıyı sürekli takip etmekten kurtarmak.

### ✅ Tamamlananlar

- [x] Senaryo Analizi (What-If) sekmesi eklendi
- [x] Faiz, USD/TRY, Enflasyon değişim simülasyonu
- [x] Basit korelasyon bazlı tahmin
- [x] Görselleştirme (bar chart)

### 📝 Yapılacaklar

- [ ] Daha gelişmiş korelasyon modelleri
- [ ] Sektör bazlı etki analizi
- [ ] Otomatik izleme ajanı (Telegram/E-posta uyarıları)
- [ ] Scheduled reports (haftalık/aylık özet)
- [ ] Portföy risk analizi

### 🔧 Senaryo Analizi Kullanımı

1. Streamlit'te "🎛️ Senaryo Analizi" sekmesine git
2. Slider'ları ayarla:
   - Faiz Oranı Değişimi: %-5 ile %+5 arası
   - USD/TRY Değişimi: %-20 ile %+20 arası
   - Enflasyon Değişimi: %-5 ile %+5 arası
3. Otomatik olarak tahmini fiyat ve etki detayları gösterilir

---

## 🛠️ Hemen Yapılacaklar Listesi (Action Plan)

### Öncelik 1: RAG Mimarisi Tamamlama

- [ ] `populate_historical_data()` fonksiyonunu test et
- [ ] Geçmiş 5 yılın siyasi haberlerini topla
- [ ] BIST100 değişim verilerini otomatik çek
- [ ] Veritabanını doldur (en az 100-200 olay)

### Öncelik 2: PDF Parser Entegrasyonu

- [ ] KAP scraper'ı PDF linklerini bulacak şekilde güncelle
- [ ] `app.py`'ye PDF analiz sonuçlarını göster
- [ ] Faaliyet raporlarını otomatik analiz et

### Öncelik 3: Model İyileştirmeleri

- [ ] LSTM modeli implementasyonu (opsiyonel, uzun vadeli)
- [ ] Mevcut modeli sentiment özellikleriyle yeniden eğit
- [ ] Backtesting sonuçlarını karşılaştır

### Öncelik 4: Kullanıcı Deneyimi

- [ ] Senaryo analizini geliştir (daha doğru korelasyonlar)
- [ ] Otomatik uyarı sistemi (Telegram bot)
- [ ] Scheduled reports

---

## 📊 Başarı Metrikleri

### RAG Mimarisi

- ✅ Benzer olay bulma başarı oranı: >80%
- ✅ Ortalama benzerlik skoru: >0.7
- ✅ Veritabanı boyutu: >100 olay

### PDF Parser

- ✅ PDF parse başarı oranı: >90%
- ✅ Analiz kalitesi: Risk/fırsat tespit doğruluğu >70%
- ✅ İşlem süresi: <30 saniye/PDF

### Model İyileştirmeleri

- ✅ Tahmin doğruluğu: >60% (mevcut: ~55%)
- ✅ Fiyat tahmin hatası: <5% (MAPE)
- ✅ Volatilite tahmin hatası: <10%

### Senaryo Analizi

- ✅ Kullanıcı memnuniyeti: >4/5
- ✅ Senaryo doğruluğu: Gerçek piyasa ile korelasyon >0.6

---

## 🎓 Öğrenme Kaynakları

### RAG Mimarisi

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Tutorial](https://www.pinecone.io/learn/retrieval-augmented-generation/)

### PDF Parsing

- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [pdfplumber Tutorial](https://github.com/jsvine/pdfplumber)

### Time-Series Models

- [LSTM for Time Series](https://machinelearningmastery.com/lstm-for-time-series-prediction-in-python/)
- [PyTorch Time Series](https://pytorch.org/tutorials/beginner/transformer_tutorial.html)

---

## 🚀 Sonuç

Bu yol haritası, projeyi bir "hobi projesi" olmaktan çıkarıp ciddi bir **"yatırım asistanı"**na dönüştürecek. 

**Öncelik sırası:**
1. RAG Mimarisi (Tarihsel Hafıza) - **EN ÖNEMLİ**
2. PDF Parser (Derin Analiz)
3. Model İyileştirmeleri
4. Senaryo Analizi (zaten eklendi, geliştirilecek)

**Bol şans! 🚀**

