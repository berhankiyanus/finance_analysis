# Streamlit Cloud Erişim Sorunu Çözümü

## ❌ Hata: "You do not have access to this app"

Bu hata, uygulamanın farklı bir GitHub hesabıyla deploy edildiği veya erişim izniniz olmadığı anlamına gelir.

## 🔧 Çözümler

### Çözüm 1: Doğru GitHub Hesabına Giriş Yapın

1. **Streamlit Cloud'dan çıkış yapın**
   - Sağ üstteki profil ikonuna tıklayın
   - "Sign out" seçin

2. **Uygulamayı deploy eden GitHub hesabıyla giriş yapın**
   - Uygulamayı hangi GitHub hesabıyla deploy ettiniz?
   - O hesaba giriş yapın

3. **Tekrar dashboard'a gidin**
   - https://share.streamlit.io/
   - Artık uygulamanızı görebilmelisiniz

### Çözüm 2: Uygulamayı Yeniden Deploy Edin

Eğer hangi hesapta olduğunu bilmiyorsanız:

1. **GitHub'da repository'nizi kontrol edin**
   - Hangi GitHub hesabında repository var?
   - O hesabı kullanın

2. **Streamlit Cloud'da yeni deploy yapın**
   - https://share.streamlit.io/
   - "New app" butonuna tıklayın
   - Repository'nizi seçin
   - Deploy edin

### Çözüm 3: Logs Olmadan API Key Kontrolü

Logs'a erişemeseniz bile, API key'in çalışıp çalışmadığını kontrol edebilirsiniz:

#### A) Sidebar'dan Kontrol

1. **Uygulamanızı açın** (streamlit.app URL'si)
2. **Sol sidebar'a bakın**
3. **API key durumunu görün:**
   - ✅ "API Key Streamlit secrets'tan yüklendi" → Çalışıyor
   - ❌ "NEWS_API_KEY bulunamadı!" → Çalışmıyor

#### B) Analiz Sonuçlarından Kontrol

1. **Bir analiz yapın** (örn: Apple, AAPL)
2. **Sonuçlara bakın:**

   **API Key ÇALIŞIYORSA:**
   - ✅ 10+ haber bulunur
   - ✅ Haber kaynakları gerçek (Reuters, Bloomberg, vb.)
   - ✅ "Dummy News" kaynaklı haber YOK
   - ✅ Uyarı mesajı YOK veya "Çok az haber" bilgi mesajı

   **API Key ÇALIŞMIYORSA:**
   - ❌ 3 veya daha az haber
   - ❌ Tüm haberlerin kaynağı "Dummy News"
   - ❌ "Dummy (test) verisi kullanılıyor" uyarısı

## 🎯 Hızlı Test

1. **Uygulamanızı açın**
2. **Apple için analiz yapın**
3. **"En Etkili Haberler" bölümüne bakın**
4. **Haber kaynaklarını kontrol edin:**
   - "Dummy News" → API key çalışmıyor
   - "Reuters", "Bloomberg", "CNN" vb. → API key çalışıyor ✅

## 📝 Not

Logs'a erişemeseniz bile, uygulama çalışıyorsa ve analiz yapabiliyorsanız, API key durumunu yukarıdaki yöntemlerle kontrol edebilirsiniz.

