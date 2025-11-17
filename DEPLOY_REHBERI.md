# GitHub ve Streamlit Cloud Deploy Rehberi 🚀

Bu rehber, projenizi GitHub'a yükleyip Streamlit Cloud'da yayınlamanız için adım adım talimatlar içerir.

## 📋 Ön Gereksinimler

1. **GitHub Hesabı**: https://github.com adresinden ücretsiz hesap oluşturun
2. **Git Kurulumu**: Bilgisayarınızda Git yüklü olmalı
3. **Streamlit Cloud Hesabı**: GitHub hesabınızla giriş yapabilirsiniz

---

## 🔷 ADIM 1: Git Kurulumu ve Kontrolü

### Git Kurulu mu?

Terminal'de kontrol edin:

```bash
git --version
```

Eğer hata alırsanız, Git'i yükleyin:

**macOS:**
```bash
# Homebrew ile
brew install git

# Veya Xcode Command Line Tools ile
xcode-select --install
```

**Windows:**
- https://git-scm.com/download/win adresinden indirin

### Git Yapılandırması

İlk kez kullanıyorsanız:

```bash
git config --global user.name "Adınız Soyadınız"
git config --global user.email "email@example.com"
```

---

## 🔷 ADIM 2: GitHub'da Yeni Repository Oluşturma

1. **GitHub'a giriş yapın**: https://github.com
2. **Sağ üst köşede** "+" butonuna tıklayın
3. **"New repository"** seçin
4. **Repository bilgilerini doldurun**:
   - **Repository name**: `finance-analysis` (veya istediğiniz isim)
   - **Description**: "Finansal Analiz ve Haber Sentiment Analizi Sistemi"
   - **Public** seçin (Streamlit Cloud ücretsiz tier için gerekli)
   - **Initialize with README** seçmeyin (zaten README'miz var)
5. **"Create repository"** butonuna tıklayın

---

## 🔷 ADIM 3: Projeyi GitHub'a Yükleme

### 3.1. Proje Klasöründe Git Başlatma

Terminal'de proje klasörüne gidin:

```bash
cd /Users/berhankiyanus/finance
```

Git repository'sini başlatın:

```bash
git init
```

### 3.2. Dosyaları Ekleyin

Önce `.gitignore` dosyasının olduğundan emin olun (zaten var):

```bash
# Tüm dosyaları staging area'ya ekle
git add .

# Durumu kontrol edin
git status
```

### 3.3. İlk Commit

```bash
git commit -m "İlk commit: Finansal analiz sistemi eklendi"
```

### 3.4. GitHub Repository'sini Bağlayın

GitHub'da oluşturduğunuz repository'nin URL'sini kullanın:

```bash
# Örnek (kendi repository URL'inizi kullanın):
git remote add origin https://github.com/KULLANICI_ADI/finance-analysis.git

# Remote'u kontrol edin
git remote -v
```

**Not**: `KULLANICI_ADI` yerine kendi GitHub kullanıcı adınızı yazın.

### 3.5. Dosyaları GitHub'a Yükleyin

```bash
# Ana branch'i main olarak ayarlayın
git branch -M main

# GitHub'a push edin
git push -u origin main
```

**İlk kez push ediyorsanız**, GitHub kullanıcı adı ve şifreniz istenebilir. 
Eğer 2FA (iki faktörlü doğrulama) aktifse, Personal Access Token kullanmanız gerekebilir.

---

## 🔷 ADIM 4: Personal Access Token (Gerekirse)

Eğer şifre ile push edemiyorsanız:

1. **GitHub** → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. **"Generate new token"** → **"Generate new token (classic)"**
3. **Token adı**: `finance-project`
4. **Expiration**: İstediğiniz süre
5. **Scopes**: `repo` seçin
6. **"Generate token"** tıklayın
7. **Token'ı kopyalayın** (bir daha gösterilmeyecek!)

Push ederken şifre yerine bu token'ı kullanın.

---

## 🔷 ADIM 5: Streamlit Cloud'a Deploy Etme

### 5.1. Streamlit Cloud'a Giriş

1. **https://streamlit.io/cloud** adresine gidin
2. **"Sign up"** veya **"Get started"** butonuna tıklayın
3. **"Continue with GitHub"** seçin
4. GitHub hesabınızla giriş yapın
5. Streamlit Cloud'a erişim izni verin

### 5.2. Yeni App Oluşturma

1. **"New app"** butonuna tıklayın
2. **Repository seçin**: GitHub'daki repository'nizi seçin
3. **Branch**: `main` (veya `master`)
4. **Main file path**: `app.py`
5. **App URL**: Otomatik oluşturulur (veya özel isim verebilirsiniz)

### 5.3. Advanced Settings (Opsiyonel)

**"Advanced settings"** tıklayın:

- **Python version**: `3.9` veya `3.10` (önerilir)
- **Secrets**: API key'leriniz varsa buraya ekleyin (opsiyonel)

**Secrets ekleme örneği**:
```
NEWS_API_KEY=your_api_key_here
```

### 5.4. Deploy!

**"Deploy"** butonuna tıklayın!

Streamlit Cloud:
1. Repository'nizi klonlar
2. `requirements.txt` dosyasından paketleri yükler
3. `app.py` dosyasını çalıştırır
4. URL'nizi oluşturur

**İlk deploy 2-5 dakika sürebilir.**

---

## 🔷 ADIM 6: Deploy Sonrası Kontroller

### 6.1. Uygulamanızı Açın

Streamlit Cloud dashboard'unda uygulamanızın URL'sine tıklayın.

### 6.2. Hataları Kontrol Edin

Eğer hata varsa:

1. **Streamlit Cloud dashboard** → **App** → **"Manage app"**
2. **"Logs"** sekmesine bakın
3. Hata mesajlarını okuyun

### 6.3. Yaygın Hatalar ve Çözümleri

#### "ModuleNotFoundError"

`requirements.txt` dosyasında eksik paket var. Ekleyin ve tekrar push edin:

```bash
git add requirements.txt
git commit -m "Eksik paket eklendi"
git push
```

Streamlit Cloud otomatik olarak yeniden deploy eder.

#### "File not found"

Dosya yollarını kontrol edin. Streamlit Cloud'da root dizin proje kök dizinidir.

#### API Key Hatası

Secrets'e API key ekleyin (Advanced settings → Secrets).

---

## 🔷 ADIM 7: Güncellemeleri Yayınlama

Kodunuzu güncellediğinizde:

```bash
# Değişiklikleri ekle
git add .

# Commit yap
git commit -m "Yeni özellik eklendi"

# GitHub'a push et
git push
```

Streamlit Cloud **otomatik olarak yeniden deploy eder** (birkaç dakika sürebilir).

---

## 📝 Özet Komutlar

### İlk Kurulum

```bash
cd /Users/berhankiyanus/finance
git init
git add .
git commit -m "İlk commit"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADI/finance-analysis.git
git push -u origin main
```

### Güncellemeler

```bash
git add .
git commit -m "Açıklayıcı mesaj"
git push
```

---

## 🎯 Hızlı Kontrol Listesi

- [ ] Git kurulu ve yapılandırılmış
- [ ] GitHub hesabı oluşturuldu
- [ ] GitHub'da repository oluşturuldu
- [ ] Proje GitHub'a push edildi
- [ ] Streamlit Cloud hesabı oluşturuldu
- [ ] Streamlit Cloud'da app oluşturuldu
- [ ] Deploy başarılı
- [ ] Uygulama çalışıyor

---

## 🆘 Sorun Giderme

### "Permission denied"

```bash
# SSH key kullanın veya Personal Access Token kullanın
```

### "Repository not found"

- Repository URL'ini kontrol edin
- Repository'nin public olduğundan emin olun

### "Deploy failed"

- Streamlit Cloud logs'u kontrol edin
- `requirements.txt` dosyasını kontrol edin
- Python versiyonunu kontrol edin

### "Module not found"

- `requirements.txt` dosyasına eksik paketi ekleyin
- Tekrar push edin

---

## 💡 İpuçları

1. **`.env` dosyasını GitHub'a yüklemeyin**: Zaten `.gitignore`'da var
2. **API key'leri secrets'a ekleyin**: Streamlit Cloud → Advanced settings
3. **Büyük dosyaları yüklemeyin**: Model dosyaları için Git LFS kullanın
4. **README.md'yi güncel tutun**: Proje açıklaması için önemli

---

## 🎉 Başarılı Deploy Sonrası

Artık uygulamanız:
- ✅ Herkese açık URL'de çalışıyor
- ✅ GitHub'da kaynak kodları mevcut
- ✅ Otomatik deploy aktif
- ✅ Paylaşılabilir durumda

**Tebrikler! 🚀**

---

## 📚 Ek Kaynaklar

- [Git Dokümantasyonu](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Cloud FAQ](https://docs.streamlit.io/streamlit-community-cloud/get-started/faq)

---

**Sorularınız varsa, yukarıdaki kaynaklara bakabilir veya GitHub Issues açabilirsiniz!**

