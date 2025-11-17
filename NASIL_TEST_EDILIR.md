# Nasıl Test Edilir? 🧪

Bu projeyi test etmek için birkaç yöntem var. En kolay yolu seçin:

## 🚀 Yöntem 1: Otomatik Test Scripti (ÖNERİLEN)

En kolay yol! Tek komutla her şeyi test eder:

```bash
./test_et.sh
```

Bu script:
- ✅ Virtual environment oluşturur (yoksa)
- ✅ Gerekli paketleri yükler
- ✅ Tüm modülleri test eder
- ✅ Mini bir analiz çalıştırır

**Not**: İlk çalıştırmada Transformers modeli indirilecek (birkaç yüz MB), sabırlı olun.

---

## 📝 Yöntem 2: Manuel Test (Adım Adım)

### Adım 1: Virtual Environment Oluştur

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# veya Windows: venv\Scripts\activate
```

### Adım 2: Paketleri Yükle

```bash
pip install -r requirements.txt
```

**Not**: Transformers ve PyTorch büyük paketler, yükleme biraz zaman alabilir.

### Adım 3: Test Et

#### A) Otomatik Test Scripti
```bash
python3 test_system.py
```

#### B) Tek Modül Testi
```bash
# Veri toplama modülü
python3 -m src.data_collection

# Tam analiz
python3 -m src.main "Apple" "AAPL" 30
```

#### C) Örnek Kullanım
```bash
python3 example_usage.py
```

---

## 🎯 Yöntem 3: Hızlı Test (Sadece Temel Paketler)

Eğer sadece temel özellikleri test etmek istiyorsanız:

```bash
# Virtual environment oluştur
python3 -m venv venv
source venv/bin/activate

# Sadece temel paketleri yükle (Transformers olmadan)
pip install pandas numpy yfinance requests beautifulsoup4 python-dotenv

# Test et (kural tabanlı sentiment kullanılacak)
python3 -m src.main "Apple" "AAPL" 7
```

---

## 📊 Test Sonuçları

Başarılı bir test sonucunda şunları görmelisiniz:

```
✅ Tüm modüller başarıyla yüklendi
✅ X haber bulundu
✅ X günlük fiyat verisi bulundu
✅ Sentiment analizi tamamlandı
✅ Finansal analiz tamamlandı
✅ Genel durum skoru: XX/100
```

Ve sonunda Türkçe bir rapor göreceksiniz.

---

## ⚠️ Olası Sorunlar ve Çözümleri

### 1. "ModuleNotFoundError" Hatası

**Sorun**: Paketler yüklü değil

**Çözüm**:
```bash
source venv/bin/activate  # Virtual environment'ı aktifleştir
pip install -r requirements.txt
```

### 2. "No module named 'src'" Hatası

**Sorun**: Yanlış dizinden çalıştırıyorsunuz

**Çözüm**:
```bash
cd /Users/berhankiyanus/finance  # Proje kök dizinine git
python3 -m src.main "Apple" "AAPL" 30
```

### 3. Transformers Model İndirme Hatası

**Sorun**: İnternet bağlantısı veya disk alanı

**Çözüm**: 
- İnternet bağlantınızı kontrol edin
- Model ilk kullanımda otomatik indirilir (~500MB)
- Sabırlı olun, birkaç dakika sürebilir

### 4. API Key Uyarısı

**Sorun**: `⚠️ NEWS_API_KEY bulunamadı. Dummy veri kullanılıyor.`

**Çözüm**: Bu normal! Sistem dummy veri ile çalışır. Gerçek veri için:
1. `.env` dosyası oluşturun: `cp .env.example .env`
2. NewsAPI key alın: https://newsapi.org/
3. `.env` dosyasına ekleyin: `NEWS_API_KEY=your_key_here`

---

## 🎓 Test Senaryoları

### Senaryo 1: Hızlı Test (7 gün)
```bash
python3 -m src.main "Apple" "AAPL" 7
```

### Senaryo 2: Tam Test (30 gün)
```bash
python3 -m src.main "Apple" "AAPL" 30
```

### Senaryo 3: Farklı Şirket
```bash
python3 -m src.main "Microsoft" "MSFT" 30
```

### Senaryo 4: Türk Şirketi
```bash
python3 -m src.main "Türk Hava Yolları" "THYAO.IS" 30
```

### Senaryo 5: Özel Ağırlıklar
```python
from src.main import analyze_company

results = analyze_company(
    company_name="Apple",
    ticker="AAPL",
    days_back=30,
    sentiment_weight=0.3,  # Haberlere daha az ağırlık
    financial_weight=0.7    # Finansal verilere daha fazla ağırlık
)

print(results['summary'])
```

---

## 📱 Jupyter Notebook ile Test

1. Jupyter'ı başlatın:
```bash
source venv/bin/activate
pip install jupyter plotly ipywidgets
jupyter notebook
```

2. `notebooks/analysis_notebook.ipynb` dosyasını açın

3. Hücreleri sırayla çalıştırın

---

## ✅ Başarı Kriterleri

Test başarılı sayılır eğer:

- ✅ Tüm modüller import edilebiliyor
- ✅ Haber verisi toplanabiliyor (dummy veya gerçek)
- ✅ Fiyat verisi çekilebiliyor
- ✅ Sentiment analizi yapılabiliyor
- ✅ Finansal feature'lar hesaplanabiliyor
- ✅ Skor üretilebiliyor
- ✅ Türkçe rapor oluşturulabiliyor

---

## 💡 İpuçları

1. **İlk çalıştırma**: Transformers modeli indirilecek, sabırlı olun
2. **API key**: Olmadan da test edebilirsiniz (dummy veri)
3. **Hızlı test**: `days_back=7` kullanın
4. **Tam analiz**: `days_back=30` önerilir
5. **Virtual environment**: Her zaman aktif olduğundan emin olun

---

## 🆘 Yardım

Eğer sorun yaşıyorsanız:

1. `TEST_REHberI.md` dosyasını okuyun
2. Hata mesajını tam olarak kontrol edin
3. Virtual environment'ın aktif olduğundan emin olun
4. Proje kök dizininden çalıştırdığınızdan emin olun

**Başarılar! 🚀**

