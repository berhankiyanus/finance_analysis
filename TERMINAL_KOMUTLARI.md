# 🖥️ Terminal Komutları - Sprint 1 MVP

## ⚠️ Önemli Notlar

1. **Virtual Environment Aktifleştirme:**
   - zsh kullanıyorsanız: `. venv/bin/activate` (nokta ile)
   - bash kullanıyorsanız: `source venv/bin/activate`

2. **Komutlar proje kök dizininden çalıştırılmalı:**
   ```bash
   cd /Users/berhankiyanus/Desktop/Finance
   ```

## 🚀 Hızlı Başlatma (Önerilen)

### Yöntem 1: Doğrudan Script (En Kolay - Önerilen)

**FastAPI için:**
```bash
cd /Users/berhankiyanus/Desktop/Finance
./BASLAT_DIRECT.sh
```

**Streamlit için (başka bir terminal):**
```bash
cd /Users/berhankiyanus/Desktop/Finance
./BASLAT_STREAMLIT_DIRECT.sh
```

### Yöntem 2: Normal Script (activate çalışıyorsa)
```bash
cd /Users/berhankiyanus/Desktop/Finance
./BASLAT.sh
```

## 📝 Manuel Başlatma

### 1. FastAPI'yi Başlat

```bash
cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Eğer `uvicorn` bulunamazsa:**
```bash
pip install fastapi "uvicorn[standard]"
```

### 2. Streamlit'i Başlat (başka bir terminal)

```bash
cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate
streamlit run app.py
```

**Eğer `streamlit` bulunamazsa:**
```bash
pip install streamlit plotly
```

## 🔍 Sorun Giderme

### "source: operation not permitted" veya ".: operation not permitted" Hatası

Bu durumda **doğrudan venv/bin/uvicorn kullanın:**

```bash
cd /Users/berhankiyanus/Desktop/Finance
./BASLAT_DIRECT.sh
```

Veya manuel olarak:
```bash
cd /Users/berhankiyanus/Desktop/Finance
venv/bin/uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Not:** `venv/bin/uvicorn` doğrudan çalıştırılabilir, activate gerekmez!

### "command not found: uvicorn" Hatası

1. Virtual environment aktif mi kontrol edin:
   ```bash
   which python
   # Çıktı: /Users/berhankiyanus/Desktop/Finance/venv/bin/python olmalı
   ```

2. uvicorn'u yükleyin:
   ```bash
   pip install fastapi "uvicorn[standard]"
   ```

3. Tekrar deneyin:
   ```bash
   uvicorn api.main:app --reload
   ```

### "cd api && uvicorn main:app" Çalışmıyor

**YANLIŞ:** `cd api && uvicorn main:app` ❌

**DOĞRU:** Proje kök dizininden:
```bash
uvicorn api.main:app --reload
```

## ✅ Doğru Kullanım Örneği

```bash
# Terminal 1: FastAPI
Last login: Tue Nov 18 02:48:48 on ttys000
berhankiyanus@Berhan-MacBook-Pro ~ % cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
.: operation not permitted: venv/bin/activate
zsh: command not found: uvicorn
berhankiyanus@Berhan-MacBook-Pro Finance % cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
.: operation not permitted: venv/bin/activate
zsh: command not found: uvicorn
berhankiyanus@Berhan-MacBook-Pro Finance % 



# Terminal 2: Streamlit
cd /Users/berhankiyanus/Desktop/Finance
. venv/bin/activate
streamlit run app.py
```

## 🎯 Test

FastAPI çalışırken, başka bir terminal'de:
```bash
curl http://127.0.0.1:8000/health
```

Veya tarayıcıdan: `http://127.0.0.1:8000/docs`

