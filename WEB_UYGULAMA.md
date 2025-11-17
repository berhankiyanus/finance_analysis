# Web Uygulaması Kullanım Kılavuzu 🌐

Bu kılavuz, Streamlit web arayüzünü nasıl kullanacağınızı açıklar.

## 🚀 Hızlı Başlangıç

### 1. Gerekli Paketleri Yükleyin

```bash
# Virtual environment aktifleştirin
source venv/bin/activate

# Streamlit ve görselleştirme paketlerini yükleyin
pip install streamlit plotly
```

### 2. Web Uygulamasını Başlatın

```bash
streamlit run app.py
```

Tarayıcınızda otomatik olarak açılacak (genelde http://localhost:8501)

## 📱 Kullanım

### Ana Sayfa - Analiz

1. **Şirket Bilgileri**:
   - Şirket adı girin (örn: "Apple")
   - Borsa kodunu girin (örn: "AAPL")

2. **Analiz Parametreleri**:
   - **Haber Analizi Periyodu**: Kaç gün geriye gidilecek (7-90 gün)
   - **Haber Ağırlığı**: Sentiment skorunun ağırlığı (0.0-1.0)
   - **Finansal Ağırlık**: Finansal skorun ağırlığı (0.0-1.0)
   - ⚠️ Ağırlıkların toplamı 1.0 olmalı!

3. **Analiz Yap** butonuna tıklayın

4. **Sonuçları İnceleyin**:
   - Skorlar (Sentiment, Finansal, Genel Durum)
   - Yorum ve öneriler
   - Yön tahmini
   - Detaylı rapor
   - Grafikler (fiyat, hacim, sentiment dağılımı)
   - Haber listesi

### Model Eğitimi Sayfası

1. **Eğitim Parametreleri**:
   - **Borsa Kodu**: Model eğitilecek şirket
   - **Veri Periyodu**: 1y, 2y, 3y, 5y
   - **Model Tipi**: Random Forest (önerilir), XGBoost, Gradient Boosting, Logistic
   - **Tahmin Periyodu**: Kaç gün sonrasını tahmin edeceğiz (3-10 gün)

2. **Model Eğit** butonuna tıklayın

3. **Sonuçları İnceleyin**:
   - Eğitim accuracy'si
   - Feature importance listesi
   - Feature importance grafiği

### Geçmiş Analizler

Eğitilmiş modellerin listesini gösterir (geliştirilme aşamasında).

## 🎨 Özellikler

### Görselleştirmeler

- **Fiyat Grafiği**: Kapanış fiyatı ve hareketli ortalamalar
- **Hacim Grafiği**: İşlem hacmi
- **Sentiment Dağılımı**: Pozitif/negatif/nötr haber sayıları
- **Skor Karşılaştırması**: Tüm skorların karşılaştırması
- **Feature Importance**: ML modeli için en önemli feature'lar

### İnteraktif Özellikler

- Tüm grafikler Plotly ile interaktif (zoom, pan, hover)
- Detaylı raporlar expandable bölümlerde
- Haber listesi filtrelenebilir

## ⚙️ Yapılandırma

### Port Değiştirme

```bash
streamlit run app.py --server.port 8502
```

### Tema Değiştirme

Streamlit'in kendi ayarlarından tema değiştirebilirsiniz (sağ üst köşe menü).

## 🐛 Sorun Giderme

### "ModuleNotFoundError: No module named 'streamlit'"

```bash
pip install streamlit plotly
```

### "Port already in use"

Farklı bir port kullanın:
```bash
streamlit run app.py --server.port 8502
```

### Grafikler görünmüyor

Plotly'nin yüklü olduğundan emin olun:
```bash
pip install plotly
```

### Model eğitimi çalışmıyor

scikit-learn ve xgboost'un yüklü olduğundan emin olun:
```bash
pip install scikit-learn xgboost
```

## 📊 Örnek Kullanım Senaryoları

### Senaryo 1: Hızlı Analiz

1. Ana sayfaya git
2. "Apple" ve "AAPL" gir
3. Varsayılan parametreleri kullan
4. "Analiz Yap" tıkla
5. Sonuçları incele

### Senaryo 2: Detaylı Analiz

1. Ana sayfaya git
2. Şirket bilgilerini gir
3. Haber periyodunu 60 güne çıkar
4. Ağırlıkları ayarla (örn: 0.3 haber, 0.7 finansal)
5. Analiz yap
6. Detaylı raporu oku
7. Grafikleri incele

### Senaryo 3: Model Eğitimi

1. Model Eğitimi sayfasına git
2. "AAPL" gir
3. "2y" periyot seç
4. "random_forest" model tipi seç
5. "Model Eğit" tıkla
6. Feature importance'ı incele
7. Ana sayfaya dön ve analiz yap (eğitilmiş model otomatik kullanılacak)

## 🚀 Production Deployment

### Streamlit Cloud (Ücretsiz)

1. GitHub'a projeyi yükleyin
2. https://streamlit.io/cloud adresine gidin
3. GitHub repo'nuzu bağlayın
4. `app.py` dosyasını seçin
5. Deploy edin!

### Docker ile

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Heroku

1. `Procfile` oluşturun:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

2. Heroku'ya deploy edin

## 📝 Notlar

- İlk analiz biraz zaman alabilir (model indirme, veri çekme)
- API key olmadan da çalışır (dummy veri kullanılır)
- Eğitilmiş modeller `models/` klasöründe saklanır
- Tüm grafikler interaktif (zoom, pan, hover)

## 🆘 Yardım

Sorun yaşıyorsanız:
1. Terminal'deki hata mesajlarını kontrol edin
2. Gerekli paketlerin yüklü olduğundan emin olun
3. Virtual environment'ın aktif olduğundan emin olun

---

**İyi kullanımlar! 🚀**

