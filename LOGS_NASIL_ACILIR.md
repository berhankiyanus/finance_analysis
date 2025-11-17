# Streamlit Cloud'da Logs Nasıl Açılır? (Adım Adım)

## 🎯 Hızlı Yol

1. **Yeni bir sekme açın** (mevcut uygulama sekmesini kapatmayın)
2. **Şu adrese gidin:** https://share.streamlit.io/
3. **GitHub ile giriş yapın** (eğer giriş yapmadıysanız)
4. **Uygulamanızı bulun ve tıklayın**
5. **"Logs" sekmesine tıklayın**

## 📸 Görsel Adımlar

### Adım 1: Dashboard'a Git
```
Tarayıcınızda yeni sekme açın
↓
https://share.streamlit.io/ yazın
↓
Enter'a basın
```

### Adım 2: Giriş Yap
```
GitHub hesabınızla giriş yapın
(Eğer zaten giriş yaptıysanız bu adımı atlayın)
```

### Adım 3: Uygulamanızı Bulun
```
Dashboard'da uygulamalarınız listelenir:
┌─────────────────────────────┐
│ 📊 financeanalysis-xxx     │
│    financeanalysis-xxx...   │ ← Buna tıklayın
│    Last deployed: 2h ago    │
└─────────────────────────────┘
```

### Adım 4: Logs Sekmesine Tıklayın
```
Uygulama detay sayfası açılır:
┌─────────────────────────────────┐
│ [Overview] [Logs] [Settings]    │ ← "Logs"e tıklayın
│                                  │
│ Logs içeriği burada görünür     │
└─────────────────────────────────┘
```

## 🔍 Logs'ta Ne Göreceksiniz?

Logs sekmesinde şunları göreceksiniz:

```
✅ NEWS_API_KEY bulundu: 11dede7c7e...
✅ 25 haber bulundu (bugün dahil son 30 gün).
   En yeni haber: 2024-11-17 14:30

📥 1. Veri toplanıyor...
   📰 Haberler çekiliyor...
   💰 Fiyat verisi çekiliyor...
```

VEYA hata varsa:

```
⚠️ NEWS_API_KEY bulunamadı!
   .env dosyası yolu: /mount/src/finance_analysis/.env
   .env dosyası var mı: False
```

## ❓ Sık Sorulan Sorular

### "View logs" seçeneğini göremiyorum
**Cevap:** Uygulama sayfasında (streamlit.app) "View logs" yoktur. Dashboard'dan (share.streamlit.io) erişilir.

### Dashboard'da uygulamamı göremiyorum
**Cevap:** 
- Doğru GitHub hesabıyla giriş yaptığınızdan emin olun
- Uygulamanın deploy edildiğinden emin olun
- Sayfayı yenileyin (F5)

### Logs boş görünüyor
**Cevap:**
- Analiz yapın, sonra logs'a bakın
- Sayfayı yenileyin
- Biraz bekleyin (logs gerçek zamanlı güncellenir)

### Logs'ta eski mesajlar görünüyor
**Cevap:**
- En alttaki mesajlar en yeni olanlardır
- Scroll yaparak en alta inin
- Sayfayı yenileyin

## 💡 İpucu

Logs'u sürekli açık tutmak için:
1. Dashboard'da logs sekmesini açın
2. Yeni sekmede uygulamanızı açın
3. İki sekmeyi yan yana kullanın
4. Analiz yaparken logs'u izleyin

