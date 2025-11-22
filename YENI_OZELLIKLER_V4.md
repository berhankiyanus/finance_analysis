# 🚀 Yeni Özellikler - V4 SaaS Dönüşümü

## ✅ Tamamlanan Özellikler

### 1. 📦 Stale Data Manager
**Dosya:** `src/stale_data_manager.py`

**Açıklama:** API hatası durumunda dummy veri yerine en son kaydedilmiş veriyi gösterir.

**Kullanım:**
```python
from src.stale_data_manager import get_stale_data_manager

manager = get_stale_data_manager()
data, metadata = manager.get_data_with_fallback(
    data_type="price_data",
    identifier="THYAO",
    fetch_func=get_price_data,
    ticker="THYAO",
    period="1mo"
)

if metadata.get('is_stale'):
    st.warning(f"⚠️ {metadata.get('warning', 'Veriler güncel değil')}")
```

**Not:** `data_collection.py`'ye entegre edilmesi gerekiyor (gelecek güncelleme).

---

### 2. 😈 Şeytanın Avukatı Modu
**Dosya:** `src/devils_advocate.py`

**Açıklama:** AL sinyali verildiğinde, sadece riskleri ve negatif yönleri gösterir. Kullanıcıyı confirmation bias tuzağından korur.

**Kullanım:**
```python
from src.devils_advocate import analyze_why_not_to_buy

analysis = analyze_why_not_to_buy(
    ticker="THYAO",
    company_name="Türk Hava Yolları",
    analysis_results=results,
    gemini_model=gemini_model
)
```

**UI:** `app.py` içinde direction prediction kısmında "😈 Neden Almamalıyım?" butonu eklendi.

---

### 3. ⚔️ Rakip Analizi
**Dosya:** `src/competitor_analysis.py`

**Açıklama:** Seçilen hissenin otomatik olarak en büyük rakibini bulur ve head-to-head karşılaştırma yapar.

**Kullanım:**
```python
from src.competitor_analysis import find_competitor, compare_companies

competitor = find_competitor("THYAO")  # "PGSUS" döner
comparison = compare_companies(
    ticker1="THYAO",
    ticker2="PGSUS",
    company_name1="Türk Hava Yolları",
    company_name2="Pegasus",
    analysis_results1=results1,
    analysis_results2=results2
)
```

**UI:** `app.py` içinde yeni tab: "⚔️ Rakip Analizi"

**Desteklenen Hisseler:**
- THYAO, PGSUS, TAVHL (Havacılık)
- GARAN, AKBNK, ISCTR, YKBNK (Bankacılık)
- TUPRS, PETKM (Petrol)
- EREGL, KRDMD (Demir-Çelik)
- Ve daha fazlası...

---

### 4. 🔍 KAP Dedektifi
**Dosya:** `src/kap_detective.py`

**Açıklama:** Faaliyet raporlarındaki dil değişimini analiz eder. Endişe verici ifadeleri tespit eder.

**Kullanım:**
```python
from src.kap_detective import analyze_language_change, detect_red_flags

analysis = analyze_language_change(
    current_report_text="Mevcut çeyrek raporu metni...",
    previous_report_text="Önceki çeyrek raporu metni...",
    gemini_model=gemini_model
)

red_flags = detect_red_flags("Rapor metni...")
```

**UI:** `app.py` içinde yeni tab: "🔍 KAP Dedektifi"

**Özellikler:**
- Dil tonu karşılaştırması (daha endişeli mi? daha iyimser mi?)
- Belirsizlik ifadesi tespiti
- Olumsuz kelime kullanımı analizi
- Kırmızı bayrak tespiti

---

### 5. 👔 Insider Trading Takibi
**Dosya:** `src/insider_trading.py`

**Açıklama:** KAP bildirimlerinden "Pay Alım Satım Bildirimi" haberlerini özel olarak ayrıştırır.

**Kullanım:**
```python
from src.insider_trading import get_insider_trading_from_kap

insider_analysis = get_insider_trading_from_kap("THYAO", limit=20)

insider_trades = insider_analysis.get('insider_trades', [])
sentiment = insider_analysis.get('sentiment', {})
```

**UI:** `app.py` içinde yeni tab: "👔 Insider Trading"

**Özellikler:**
- Yönetici pay alım/satım tespiti
- Sentiment analizi (alım eğilimi mi? satım eğilimi mi?)
- Yüksek pozisyonlu yöneticilerin işlemlerini önceliklendirme

---

## 📋 Yol Haritası

### Kısa Vade (1 Hafta)
- [ ] Stale Data Manager'ı `data_collection.py`'ye entegre et
- [ ] Sektör Rotasyonu Isı Haritası (Sankey diagram)
- [ ] Agentic AI (Yatırım Kurulu)

### Orta Vade (2-4 Hafta)
- [ ] Knowledge Graph (Neden-sonuç ilişkileri)
- [ ] Time-Series Transformers (PatchTST)
- [ ] Alternatif Veri Kaynakları (YouTube, Google Trends)

### Uzun Vade (1-2 Ay)
- [ ] Streamlit/Backend Ayrımı (Decoupling)
- [ ] PostgreSQL + TimescaleDB
- [ ] CI/CD Otomasyonu

---

## 🎯 Kullanım Örnekleri

### Şeytanın Avukatı Modu
1. Bir hisse analiz edin (örn: THYAO)
2. Yön tahmini "AL" (YÜKSELİŞ) çıktığında
3. "😈 Neden Almamalıyım?" butonuna tıklayın
4. Risk analizi ve neden almamalıyım gerekçelerini görün

### Rakip Analizi
1. Bir hisse analiz edin (örn: THYAO)
2. "⚔️ Rakip Analizi" tab'ına gidin
3. "🔄 Rakip Analizini Çalıştır" butonuna tıklayın
4. THYAO vs PGSUS karşılaştırmasını görün

### KAP Dedektifi
1. Bir Türk hissesi analiz edin (örn: THYAO)
2. "🔍 KAP Dedektifi" tab'ına gidin
3. "🔍 Dil Değişimini Analiz Et" butonuna tıklayın
4. Çeyrek raporları arası dil değişimini görün

### Insider Trading
1. Bir Türk hissesi analiz edin (örn: THYAO)
2. "👔 Insider Trading" tab'ına gidin
3. "🔍 Insider Trading Analizini Çalıştır" butonuna tıklayın
4. Yönetici pay alım/satım işlemlerini görün

---

## 🔧 Teknik Detaylar

### Stale Data Manager
- Cache dizini: `data/stale_cache/`
- Maksimum veri yaşı: 24 saat (varsayılan)
- Format: JSON (DataFrame'ler dict'e çevrilir)

### Şeytanın Avukatı
- Gemini API kullanır (fallback: rule-based)
- Sadece negatif verileri vurgular
- Risk seviyeleri: high, medium, low

### Rakip Analizi
- BIST_COMPETITORS dictionary'si ile eşleştirme
- Sektör bazlı fallback
- yfinance ile sektör bilgisi çekme (opsiyonel)

### KAP Dedektifi
- Gemini API ile dil analizi
- Rule-based kırmızı bayrak tespiti
- Belirsizlik ifadesi sayımı

### Insider Trading
- KAP bildirimlerinden regex ile tespit
- Alım/satım ayrımı
- Yönetici pozisyonu tespiti

---

## 📝 Notlar

- Tüm yeni modüller `src/` dizininde
- UI entegrasyonları `app.py` içinde
- Gemini API key gerekli (KAP Dedektifi, Şeytanın Avukatı için)
- Türk hisseleri için optimize edilmiş (KAP, Insider Trading)

---

**Son Güncelleme:** 2024-11-22
**Versiyon:** V4.0.0

