# 🚀 Sprint 1 MVP Kullanım Kılavuzu

Bu kılavuz, Sprint 1 MVP'yi çalıştırmak için gereken adımları açıklar.

## 📋 Ön Hazırlık

### 1. Virtual Environment Aktifleştirme

Terminal'de proje dizinine gidin ve virtual environment'ı aktifleştirin:

```bash
cd /Users/berhankiyanus/Desktop/Finance
source venv/bin/activate
```

### 2. Gerekli Paketleri Yükleme

Temel paketleri yükleyin (XGBoost opsiyonel, şimdilik RandomForest kullanacağız):

```bash
pip install pandas numpy scikit-learn lightgbm yfinance requests python-dotenv fastapi uvicorn streamlit plotly
```

**Not:** Eğer XGBoost hatası alırsanız, şimdilik atlayabilirsiniz. RandomForest kullanacağız.

## 🎯 Adım 1: Demo Model Eğitimi

Terminal'de (venv aktifken):

```bash
python scripts/train_demo_models.py
```

Bu komut:
- THYAO, AAPL, MSFT için demo modeller eğitir
- Modelleri `models/` klasörüne kaydeder
- Yaklaşık 2-5 dakika sürebilir

**Beklenen Çıktı:**
```
============================================================
DEMO MODELLER EĞİTİLİYOR
============================================================

📊 THYAO.IS (Türk Hava Yolları) için model eğitiliyor...
   📥 Veri çekiliyor...
   ✅ Model başarıyla eğitildi: models/price_predictor_thyao_is.pkl
```

## 🎯 Adım 2: FastAPI'yi Başlatma

**Yeni bir terminal penceresi açın** (venv aktifken):

```bash
cd /Users/berhankiyanus/Desktop/Finance
source venv/bin/activate
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Beklenen Çıktı:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
✅ Demo model yüklendi: models/price_predictor_thyao_is.pkl
INFO:     Application startup complete.
```

**Not:** Bu terminal penceresini açık tutun! FastAPI çalışmaya devam etmeli.

## 🎯 Adım 3: Streamlit'i Başlatma

**Başka bir yeni terminal penceresi açın** (venv aktifken):

```bash
cd /Users/berhankiyanus/Desktop/Finance
source venv/bin/activate
streamlit run app.py
```

**Beklenen Çıktı:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Tarayıcı otomatik açılır. Açılmazsa, `http://localhost:8501` adresine gidin.

## 🎯 Adım 4: MVP'yi Test Etme

1. Streamlit arayüzünde sol menüden **"🚀 MVP Tahmin (Sprint 1)"** sayfasını seçin

2. **"Hisse Kodu"** alanına `THYAO` yazın

3. **"🔮 Tahmin Al"** butonuna tıklayın

4. Sonuçları görün:
   - 🟢 **BUY** (Al) - Yeşil
   - 🔴 **SELL** (Sat) - Kırmızı  
   - 🟡 **HOLD** (Bekle) - Sarı
   - Güven seviyesi (confidence)
   - Model kullanıldı mı?

## 🔧 Sorun Giderme

### Model Eğitimi Başarısız Olursa

- XGBoost hatası alırsanız: `train_demo_models.py` içinde `model_type="random_forest"` kullanın
- Veri çekme hatası: İnternet bağlantınızı kontrol edin
- TCMB verisi hatası: Normal, dummy veri kullanılacak

### FastAPI Bağlantı Hatası

- FastAPI çalışıyor mu kontrol edin: `http://127.0.0.1:8000/health` adresine tarayıcıdan gidin
- Port 8000 kullanımda mı? Farklı port deneyin: `--port 8001`

### Streamlit Bağlantı Hatası

- FastAPI'nin çalıştığından emin olun
- Sidebar'daki "FastAPI URL" alanını kontrol edin (varsayılan: `http://127.0.0.1:8000`)

## 📝 Hızlı Test (API'yi Doğrudan Test Etme)

FastAPI çalışırken, başka bir terminal'de:

```bash
curl -X POST "http://127.0.0.1:8000/predict/THYAO"
```

JSON response almalısınız:
```json
{
  "signal": "BUY",
  "confidence": 0.75,
  "direction": "up",
  "model_used": true
}
```

## ✅ Başarı Kriterleri

Sprint 1 MVP başarılı sayılır eğer:
- ✅ Demo model eğitildi (`models/` klasöründe `.pkl` dosyası var)
- ✅ FastAPI çalışıyor (`/health` endpoint'i çalışıyor)
- ✅ Streamlit'ten tahmin alınabiliyor
- ✅ "BUY" veya "SELL" sinyali görülebiliyor

## 🎉 Sonraki Adımlar

Sprint 1 başarılı olduktan sonra:
- Sprint 2: "Neden?" sorusunu cevaplama (Gemini raporu, SHAP)
- Sprint 3: Platformlaştırma ve MLOps

