# Logs Sekmesi Görünmüyor - Alternatif Çözümler

## 🔍 Logs Sekmesi Görünmüyorsa Ne Yapmalı?

### Çözüm 1: URL'yi Manuel Değiştirin

1. **Dashboard'da uygulamanızı açın**
   - `https://share.streamlit.io/` adresine gidin
   - Uygulamanızı bulun ve tıklayın

2. **URL'yi kontrol edin**
   - Şu formatta olmalı: `https://share.streamlit.io/[username]/[app-name]`
   - Örnek: `https://share.streamlit.io/berhankiyanus/finance_analysis`

3. **URL'nin sonuna `/logs` ekleyin**
   - Örnek: `https://share.streamlit.io/berhankiyanus/finance_analysis/logs`
   - Enter'a basın
   - Logs sayfası açılmalı

### Çözüm 2: Uygulama Sayfasında Debug Modu

1. **Uygulamanızı açın** (streamlit.app URL'si)
2. **Sağ üstteki "⋮" menüsüne tıklayın**
3. **"Developer options"** seçin
4. **"Show error messages"** veya benzeri bir seçenek olabilir
5. Veya **"Clear cache"** yapın ve tekrar analiz yapın

### Çözüm 3: Sidebar'da API Key Durumunu Kontrol Edin

Logs'a erişemiyorsanız, en azından API key'in yüklenip yüklenmediğini kontrol edebilirsiniz:

1. **Uygulamanızı açın**
2. **Sol sidebar'a bakın**
3. **Şu mesajlardan birini görmelisiniz:**
   - ✅ "API Key Streamlit secrets'tan yüklendi"
   - ✅ "API Key .env dosyasından yüklendi"
   - ❌ "NEWS_API_KEY bulunamadı!"

### Çözüm 4: Analiz Yaparken Hata Mesajlarını İzleyin

1. **Uygulamanızda analiz yapın**
2. **Sayfada görünen hata/uyarı mesajlarına bakın:**
   - ⚠️ "Dummy (test) verisi kullanılıyor" → API key yüklenmemiş
   - ✅ "X haber bulundu" → API key çalışıyor

### Çözüm 5: Streamlit Cloud Sürümünü Kontrol Edin

Streamlit Cloud'un farklı sürümleri olabilir:

1. **https://share.streamlit.io/** (Eski arayüz)
2. **https://cloud.streamlit.io/** (Yeni arayüz)

Her ikisini de deneyin.

### Çözüm 6: Browser Console'dan Kontrol

1. **Uygulamanızı açın**
2. **F12** tuşuna basın (Developer Tools)
3. **"Console" sekmesine gidin**
4. **Analiz yapın**
5. **Console'da Python print() mesajları görünmeyebilir** (bunlar server-side)
6. **Ama JavaScript hataları görünebilir**

## 🎯 En Pratik Çözüm

**API key'in çalışıp çalışmadığını anlamak için:**

1. **Sidebar'ı kontrol edin:**
   - Sol tarafta API key durumu görünür

2. **Analiz yapın ve sonuçlara bakın:**
   - Eğer "Dummy News" kaynaklı haberler görüyorsanız → API key çalışmıyor
   - Eğer gerçek haber kaynakları görüyorsanız → API key çalışıyor

3. **Haber sayısına bakın:**
   - 3 veya daha az haber → Muhtemelen dummy veri
   - 10+ haber → Muhtemelen gerçek veri

## 📝 Not

Streamlit Cloud'un arayüzü zaman zaman değişebilir. Logs sekmesi farklı bir yerde olabilir veya farklı bir isimle adlandırılmış olabilir. En önemlisi, API key'in çalışıp çalışmadığını anlamak için sidebar ve analiz sonuçlarına bakmak yeterlidir.

