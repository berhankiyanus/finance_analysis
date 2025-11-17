# 🚀 Sprint 1 MVP - Hızlı Başlangıç

## ✅ Adım 1: Demo Modeller Eğitildi

Modeller başarıyla eğitildi:
- ✅ `models/price_predictor_aapl.pkl`
- ✅ `models/price_predictor_msft.pkl`
- ✅ `models/price_predictor_thyao_is.pkl`

## 🎯 Adım 2: FastAPI'yi Başlat

**Yeni bir terminal penceresi açın** ve şu komutları çalıştırın:

```bash
cd /Users/berhankiyanus/Desktop/Finance
source venv/bin/activate
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Beklenen çıktı:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ Demo model yüklendi: models/price_predictor_thyao_is.pkl
INFO:     Application startup complete.
```

**⚠️ ÖNEMLİ:** Bu terminal penceresini **AÇIK TUTUN**! FastAPI çalışmaya devam etmeli.

## 🎯 Adım 3: Streamlit'i Başlat

**Başka bir yeni terminal penceresi açın** ve şu komutları çalıştırın:

```bash
cd /Users/berhankiyanus/Desktop/Finance
source venv/bin/activate
streamlit run app.py
```

**Beklenen çıktı:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
```

Tarayıcı otomatik açılır. Açılmazsa, `http://localhost:8501` adresine gidin.

## 🎯 Adım 4: MVP'yi Test Et

1. Streamlit arayüzünde sol menüden **"🚀 MVP Tahmin (Sprint 1)"** sayfasını seçin

2. **"Hisse Kodu"** alanına `THYAO` yazın (veya `AAPL`, `MSFT`)

3. **"🔮 Tahmin Al"** butonuna tıklayın

4. Sonuçları görün:
   - 🟢 **BUY** (Al) - Yeşil renk
   - 🔴 **SELL** (Sat) - Kırmızı renk
   - 🟡 **HOLD** (Bekle) - Sarı renk
   - Güven seviyesi (confidence)
   - Model kullanıldı mı? (✅ Evet / ❌ Hayır)

## 🔍 API'yi Doğrudan Test Etme

FastAPI çalışırken, başka bir terminal'de:

```bash
curl -X POST "http://127.0.0.1:8000/predict/THYAO"
```

Veya tarayıcıdan:
- `http://127.0.0.1:8000/docs` - Swagger UI (interaktif API dokümantasyonu)
- `http://127.0.0.1:8000/health` - Sağlık kontrolü

## ⚠️ Sorun Giderme

### FastAPI Bağlantı Hatası

- FastAPI çalışıyor mu? `http://127.0.0.1:8000/health` adresine tarayıcıdan gidin
- Port 8000 kullanımda mı? Farklı port deneyin: `--port 8001`

### Streamlit Bağlantı Hatası

- FastAPI'nin çalıştığından emin olun
- Sidebar'daki "FastAPI URL" alanını kontrol edin (varsayılan: `http://127.0.0.1:8000`)

### Model Bulunamadı Hatası

- `models/` klasöründe `.pkl` dosyaları var mı kontrol edin
- Model eğitimi başarılı oldu mu? `python scripts/train_demo_models.py` tekrar çalıştırın

## ✅ Başarı Kriterleri

Sprint 1 MVP başarılı sayılır eğer:
- ✅ FastAPI çalışıyor (`/health` endpoint'i çalışıyor)
- ✅ Streamlit'ten tahmin alınabiliyor
- ✅ "BUY" veya "SELL" sinyali görülebiliyor
- ✅ JSON response'da `signal`, `confidence`, `direction` alanları var

## 🎉 Sonraki Adımlar

Sprint 1 başarılı olduktan sonra:
- Sprint 2: "Neden?" sorusunu cevaplama (Gemini raporu, SHAP)
- Sprint 3: Platformlaştırma ve MLOps

