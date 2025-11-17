# Streamlit Cloud'da Logs ve Hata Analizi Rehberi

## 📊 Streamlit Cloud'da Logs'a Nasıl Bakılır?

### ⚠️ ÖNEMLİ: Logs'a Uygulama Sayfasından Değil, Dashboard'dan Erişilir!

### Yöntem 1: Dashboard'dan

1. **Streamlit Cloud Dashboard'a gidin**
   - Yeni bir sekmede şu adrese gidin: **https://share.streamlit.io/**
   - VEYA: **https://cloud.streamlit.io/**
   - GitHub hesabınızla giriş yapın (eğer giriş yapmadıysanız)

2. **Dashboard'da uygulamanızı bulun**
   - Ana sayfada deploy edilmiş tüm uygulamalarınız listelenir
   - Uygulamanızın adını/URL'sini bulun
   - Üzerine **tıklayın** (açmak için değil, detay sayfasına gitmek için)

3. **Logs'a erişim yolları:**

   **A) Sekmeler varsa:**
   - Açılan sayfada üstte sekmeler görünür:
     - **"Overview"** (varsayılan)
     - **"Logs"** ← Buna tıklayın!
     - **"Settings"**
     - **"Secrets"**
   
   **B) Sekmeler yoksa (yeni arayüz):**
   - Sağ tarafta veya alt kısımda **"Logs"** butonu/sekmesi olabilir
   - Veya **"⋮"** (üç nokta) menüsünde **"View logs"** olabilir
   - Veya sol menüde **"Logs"** linki olabilir
   
   **C) Alternatif:**
   - URL'yi manuel olarak değiştirin:
     - `https://share.streamlit.io/[username]/[app-name]` → 
     - `https://share.streamlit.io/[username]/[app-name]/logs`
   
4. **Logs'u inceleyin**
   - Tüm konsol çıktıları burada görünür
   - Python print() mesajları burada görünür
   - Hata mesajları (traceback) burada görünür
   - Gerçek zamanlı güncellenir

### ❌ Uygulama Sayfasından Logs Görünmez

- Streamlit uygulamanızın kendi sayfasında (örn: `financeanalysis-xxx.streamlit.app`)
- Sağ üstteki **"⋮"** menüsünde "View logs" seçeneği **YOKTUR**
- Logs'a sadece **Dashboard'dan** erişilir

## 🔍 Logs'ta Ne Aranmalı?

### API Key Kontrolü

Aşağıdaki mesajları arayın:

**✅ Başarılı:**
```
✅ NEWS_API_KEY bulundu: 11dede7c7e...
✅ 25 haber bulundu (bugün dahil son 30 gün).
   En yeni haber: 2024-11-17 14:30
```

**❌ Hata:**
```
⚠️ NEWS_API_KEY bulunamadı!
   .env dosyası yolu: /mount/src/finance_analysis/.env
   .env dosyası var mı: False
```

**❌ API Hatası:**
```
❌ NewsAPI hatası: 401 Client Error: Unauthorized
   Hata detayı: Your API key is invalid.
   ⚠️  API key geçersiz! Lütfen .env dosyasındaki NEWS_API_KEY'i kontrol edin.
```

### Analiz Süreci

**Veri Toplama:**
```
📥 1. Veri toplanıyor...
   📰 Haberler çekiliyor...
✅ 25 haber bulundu (bugün dahil son 30 gün).
   💰 Fiyat verisi çekiliyor...
✅ 252 günlük fiyat verisi çekildi.
```

**Sentiment Analizi:**
```
🤖 2. Sentiment analizi yapılıyor...
✅ Sentiment analizi tamamlandı. Skor: 65.23/100
```

**Finansal Analiz:**
```
📈 3. Finansal analiz yapılıyor...
✅ Finansal analiz tamamlandı. Skor: 72.15/100
```

### Hata Mesajları

**Import Hatası:**
```
ModuleNotFoundError: No module named 'xyz'
```
→ `requirements.txt` dosyasına paket eklenmeli

**API Hatası:**
```
requests.exceptions.RequestException: ...
```
→ İnternet bağlantısı veya API key sorunu

**Veri Hatası:**
```
KeyError: 'sentiment_class'
```
→ Veri formatı sorunu

## 🛠️ Logs Filtreleme

Streamlit Cloud logs'ta:
- **Arama yapabilirsiniz:** Ctrl+F (Windows) veya Cmd+F (Mac)
- **Scroll yapabilirsiniz:** En alttaki yeni loglar otomatik görünür
- **Refresh:** Sayfayı yenileyerek yeni logları görebilirsiniz

## 📝 Örnek Log Çıktısı

Başarılı bir analiz için örnek log:

```
============================================================
🔍 Apple (AAPL) ANALİZİ BAŞLIYOR...
============================================================

📥 1. Veri toplanıyor...
   📰 Haberler çekiliyor...
✅ NEWS_API_KEY bulundu: 11dede7c7e...
✅ 25 haber bulundu (bugün dahil son 30 gün).
   En yeni haber: 2024-11-17 14:30
   💰 Fiyat verisi çekiliyor...
✅ 252 günlük fiyat verisi çekildi.
✅ Veri toplama tamamlandı.

🤖 2. Sentiment analizi yapılıyor...
✅ Sentiment analizi tamamlandı. Skor: 65.23/100

📈 3. Finansal analiz yapılıyor...
✅ Finansal analiz tamamlandı. Skor: 72.15/100

🎯 4. Genel durum skoru hesaplanıyor...
✅ Genel durum skoru: 69.50/100

🔮 5. Yön tahmini yapılıyor...
✅ Kural Tabanlı Tahmin: up (65.00% güven)

📝 6. Rapor oluşturuluyor...
```

## ⚠️ Yaygın Hatalar ve Çözümleri

### 1. "NEWS_API_KEY bulunamadı"
**Çözüm:** Streamlit Cloud secrets'a TOML formatında ekleyin:
```toml
NEWS_API_KEY = "your_key_here"
```

### 2. "ModuleNotFoundError"
**Çözüm:** `requirements.txt` dosyasına eksik paketi ekleyin ve yeniden deploy edin

### 3. "API rate limit exceeded"
**Çözüm:** NewsAPI ücretsiz planı günde 100 istek sınırına sahip. Bekleyin veya plan yükseltin

### 4. "Connection timeout"
**Çözüm:** İnternet bağlantısı sorunu. Biraz bekleyip tekrar deneyin

## 💡 İpuçları

1. **Logs'u sürekli açık tutun:** Analiz yaparken logs penceresini açık tutun
2. **Hata mesajlarını kopyalayın:** Tam hata mesajını kopyalayıp arayın
3. **Timestamp'lere dikkat edin:** Logs'ta zaman damgaları var, hangi işlemde hata olduğunu görebilirsiniz
4. **Scroll yapın:** En alttaki yeni loglar genellikle en önemli olanlardır

