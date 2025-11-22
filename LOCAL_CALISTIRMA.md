# 🖥️ Local Çalıştırma Rehberi

Streamlit Cloud'da bellek limiti hatası alıyorsanız, uygulamayı local'de çalıştırabilirsiniz.

## 🚀 Hızlı Başlatma (2 Terminal)

### Terminal 1: FastAPI'yi Başlat

```bash
cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate
venv/bin/python3 -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Veya script ile:**
```bash
cd /Users/berhankiyanus/Desktop/Finance
bash BASLAT_DIRECT.sh
```

**Beklenen çıktı:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Terminal 2: Streamlit'i Başlat

```bash
cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate
streamlit run app.py
```

**Veya script ile:**
```bash
cd /Users/berhankiyanus/Desktop/Finance
bash BASLAT_STREAMLIT_DIRECT.sh
```

**Beklenen çıktı:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
```

Tarayıcı otomatik açılır. Açılmazsa `http://localhost:8501` adresine gidin.

## ⚙️ Gereksinimler

### 1. Virtual Environment Aktifleştirme

```bash
cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate  # zsh için
# veya
source venv/bin/activate  # bash için
```

### 2. Gerekli Paketlerin Yüklü Olduğundan Emin Olun

```bash
pip install -r requirements.txt
```

**Önemli paketler:**
- `streamlit>=1.28.0`
- `fastapi>=0.104.0`
- `uvicorn[standard]>=0.24.0`
- `torch>=2.0.0`
- `transformers>=4.30.0`
- `plotly>=5.15.0`
- `feedparser>=6.0.10`

## 🔧 Sorun Giderme

### Problem: "venv/bin/python bulunamadı"

**Çözüm:**
```bash
cd /Users/berhankiyanus/Desktop/Finance
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

### Problem: "streamlit komutu bulunamadı"

**Çözüm:**
```bash
. venv/bin/activate
pip install streamlit plotly
```

### Problem: "uvicorn komutu bulunamadı"

**Çözüm:**
```bash
. venv/bin/activate
pip install fastapi "uvicorn[standard]"
```

### Problem: "ModuleNotFoundError: No module named 'torch'"

**Çözüm:**
```bash
. venv/bin/activate
pip install torch transformers
```

### Problem: "Operation not permitted"

**Çözüm:** Script yerine doğrudan Python modülü olarak çalıştırın:

**FastAPI için:**
```bash
venv/bin/python3 -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Streamlit için:**
```bash
venv/bin/python3 -m streamlit run app.py
```

## 📊 Bellek Kullanımı Optimizasyonu

Local'de çalıştırırken bellek kullanımını azaltmak için:

### 1. Model Caching Zaten Aktif

`@st.cache_resource` dekoratörü sayesinde modeller bir kez yüklenir ve cache'de kalır.

### 2. Gemini API'yi İsteğe Bağlı Kullan

`.env` dosyasında `GEMINI_API_KEY` yoksa Gemini API kullanılmaz (bellek tasarrufu).

### 3. Veri Cache'i Aktif

`@st.cache_data` ile veriler 1 saat boyunca cache'de kalır.

## 🎯 Kullanım

1. **FastAPI** çalışırken: `http://127.0.0.1:8000/docs` - API dokümantasyonu
2. **Streamlit** çalışırken: `http://localhost:8501` - Web arayüzü

## ✅ Başarı Kontrolü

- ✅ FastAPI: `http://127.0.0.1:8000/health` adresine gidin, `{"status": "ok"}` görmelisiniz
- ✅ Streamlit: Tarayıcıda `http://localhost:8501` açılmalı
- ✅ Analiz: Bir hisse kodu girip analiz yapabilmelisiniz

## 🔄 Durdurma

Her iki terminal'de de `Ctrl+C` tuşlarına basarak durdurabilirsiniz.

## 💡 İpucu

Her iki servisi de aynı anda çalıştırmak için iki ayrı terminal penceresi kullanın:
- **Terminal 1:** FastAPI (arka planda çalışır)
- **Terminal 2:** Streamlit (web arayüzü)

