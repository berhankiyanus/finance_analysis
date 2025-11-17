# Streamlit Cloud'da API Key Ekleme Rehberi

## 🚀 Streamlit Cloud'da NEWS_API_KEY Ekleme

### Yöntem 1: Streamlit Cloud Web Arayüzünden (Önerilen)

1. **Streamlit Cloud Dashboard'a gidin**
   - https://share.streamlit.io/ adresine gidin
   - Giriş yapın

2. **Uygulamanızı seçin**
   - Deploy edilmiş uygulamanızı bulun
   - Üç nokta (⋮) menüsüne tıklayın
   - **"Settings"** veya **"Secrets"** seçeneğine tıklayın

3. **Secrets bölümüne gidin**
   - Sol menüden **"Secrets"** sekmesine tıklayın
   - Veya **"Advanced settings"** altında **"Secrets"** bölümünü bulun

4. **API Key'i ekleyin (TOML formatında)**
   - Aşağıdaki formatta ekleyin (TOML formatı zorunlu):
   ```toml
   NEWS_API_KEY = "your_news_api_key_here"
   ```
   
   **ÖNEMLİ:** 
   - TOML formatı kullanılmalı (tırnak işareti gerekli)
   - Eşittir işaretinden önce ve sonra boşluk olabilir
   - Değer tırnak içinde olmalı: `"..."`
   - Her satırda bir secret olmalı
   
   **YANLIŞ format (hata verir):**
   ```
   NEWS_API_KEY=your_news_api_key_here
   ```
   
   **DOĞRU format:**
   ```toml
   NEWS_API_KEY = "your_news_api_key_here"
   ```

5. **Kaydedin**
   - **"Save"** veya **"Deploy"** butonuna tıklayın
   - Uygulama otomatik olarak yeniden deploy edilecek

### Yöntem 2: secrets.toml Dosyası ile (GitHub üzerinden)

1. **Proje kök dizininde `.streamlit` klasörü oluşturun**
   ```bash
   mkdir -p .streamlit
   ```

2. **`.streamlit/secrets.toml` dosyası oluşturun**
   ```toml
   NEWS_API_KEY = "your_news_api_key_here"
   ```

3. **GitHub'a push edin**
   ```bash
   git add .streamlit/secrets.toml
   git commit -m "Add NEWS_API_KEY to secrets"
   git push
   ```

4. **Streamlit Cloud otomatik olarak yeniden deploy edecek**

⚠️ **GÜVENLİK UYARISI:** 
- `.streamlit/secrets.toml` dosyasını `.gitignore`'a eklemeyin (Streamlit Cloud için gerekli)
- Ancak bu dosyayı public repository'de tutmayın veya gerçek API key'lerinizi kullanmayın
- Test için dummy key kullanabilirsiniz

## ✅ Kontrol

API key eklendikten sonra:

1. **Uygulamayı yenileyin** (F5 veya Ctrl+R)
2. **Sol sidebar'da kontrol edin:**
   - ✅ "API Key Streamlit secrets'tan yüklendi" görünmeli
   - ❌ "NEWS_API_KEY bulunamadı" görünmemeli

3. **Analiz yapın:**
   - Bir şirket için analiz yapın
   - Artık gerçek haberler çekilecek
   - "Dummy News" kaynaklı haberler görünmemeli

## 🔧 Sorun Giderme

### API Key hala yüklenmiyorsa:

1. **Secrets formatını kontrol edin (TOML formatı zorunlu):**
   - ✅ `NEWS_API_KEY = "key"` (doğru - TOML formatı)
   - ❌ `NEWS_API_KEY=key` (yanlış - TOML formatı değil)
   - ❌ `NEWS_API_KEY = key` (yanlış - tırnak yok)
   - ✅ `NEWS_API_KEY="key"` (doğru - tırnak var)

2. **Uygulamayı yeniden deploy edin:**
   - Streamlit Cloud dashboard'da **"Reboot app"** butonuna tıklayın

3. **Tarayıcı cache'ini temizleyin:**
   - Hard refresh: Ctrl+Shift+R (Windows) veya Cmd+Shift+R (Mac)

4. **Konsol çıktısını kontrol edin (Logs):**
   - Streamlit Cloud dashboard'da uygulamanızı seçin
   - Üst menüde **"Logs"** sekmesine tıklayın
   - Veya uygulama sayfasında sağ üstte **"⋮"** (üç nokta) menüsünden **"View logs"** seçin
   - API key ile ilgili mesajları arayın:
     - `✅ NEWS_API_KEY bulundu: ...`
     - `⚠️ NEWS_API_KEY bulunamadı!`
     - `✅ X haber bulundu`
     - `❌ NewsAPI hatası: ...`

## 📝 Notlar

- Streamlit Cloud ücretsiz planında secrets kullanımı sınırsızdır
- API key'ler güvenli bir şekilde saklanır ve environment variable olarak uygulamaya aktarılır
- Değişiklikler genellikle 1-2 dakika içinde aktif olur

