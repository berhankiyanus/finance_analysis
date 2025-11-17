# GitHub'a Dosya Yükleme - Adım Adım 🚀

Dosyalarınızı GitHub'a yüklemek için şu adımları izleyin:

## ✅ ADIM 1: GitHub Repository URL'inizi Bulun

1. GitHub'da repository'nize gidin
2. Yeşil **"Code"** butonuna tıklayın
3. URL'i kopyalayın (örnek: `https://github.com/kullanici-adi/finance-analysis.git`)

## ✅ ADIM 2: Terminal'de Şu Komutları Çalıştırın

Terminal'i açın ve proje klasörüne gidin:

```bash
cd /Users/berhankiyanus/finance
```

### 2.1. Dosyaları Git'e Ekleyin

```bash
git add .
```

### 2.2. Commit Yapın

```bash
git commit -m "İlk commit: Finansal analiz sistemi"
```

### 2.3. Branch Adını Ayarlayın

```bash
git branch -M main
```

### 2.4. GitHub Repository'yi Bağlayın

**ÖNEMLİ**: `KULLANICI_ADI` ve `REPO_ADI` kısmını kendi bilgilerinizle değiştirin!

```bash
git remote add origin https://github.com/KULLANICI_ADI/REPO_ADI.git
```

**Örnek:**
```bash
git remote add origin https://github.com/berhankiyanus/finance-analysis.git
```

### 2.5. GitHub'a Yükleyin

```bash
git push -u origin main
```

## 🔐 Kimlik Doğrulama

İlk kez push ederken GitHub kullanıcı adı ve şifreniz istenebilir.

**Eğer 2FA (iki faktörlü doğrulama) aktifse:**
- Şifre yerine **Personal Access Token** kullanmanız gerekir
- Token oluşturma: GitHub → Settings → Developer settings → Personal access tokens

## ✅ Başarılı Olursa

Terminal'de şunu göreceksiniz:

```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
Writing objects: 100% (XX/XX), done.
To https://github.com/kullanici-adi/repo.git
 * [new branch]      main -> main
```

GitHub'da repository'nizi yenileyin - tüm dosyalarınız orada olacak!

## ⚠️ Hata Alırsanız

### "remote origin already exists"

Repository zaten bağlı. Şunu yapın:

```bash
git remote remove origin
git remote add origin https://github.com/KULLANICI_ADI/REPO_ADI.git
```

### "Permission denied"

Personal Access Token kullanın (yukarıda açıklandı).

### "Repository not found"

- Repository URL'ini kontrol edin
- Repository'nin public olduğundan emin olun
- Repository'nin var olduğundan emin olun

---

**Sorun yaşarsanız, hata mesajını paylaşın!**

