# GitHub'a Yükleme - Adım Adım Kullanım Kılavuzu 📝

Bu rehber, `github_deploy.sh` scriptini nasıl kullanacağınızı gösterir.

## 🖥️ Terminal Nedir?

Terminal, bilgisayarınızda komut yazabileceğiniz bir pencere. macOS'ta "Terminal" uygulaması, Windows'ta "Command Prompt" veya "PowerShell".

## 📍 ADIM 1: Terminal'i Açın

### macOS:
1. **Spotlight** açın: `Cmd + Space` tuşlarına basın
2. **"Terminal"** yazın
3. **Enter** tuşuna basın

Veya:
- **Applications** → **Utilities** → **Terminal**

### Windows:
1. **Windows tuşu + R**
2. **"cmd"** yazın
3. **Enter** tuşuna basın

## 📍 ADIM 2: Proje Klasörüne Gidin

Terminal açıldıktan sonra, proje klasörünüze gitmeniz gerekir.

### Yöntem 1: cd Komutu ile

Terminal'de şunu yazın ve Enter'a basın:

```bash
cd /Users/berhankiyanus/finance
```

**Önemli**: Bu tam yol. Eğer projeniz farklı bir yerdeyse, o yolu kullanın.

### Yöntem 2: Finder'dan Sürükle-Bırak (macOS)

1. **Finder**'da proje klasörünü bulun (`finance` klasörü)
2. Terminal penceresine şunu yazın: `cd ` (cd'den sonra boşluk var!)
3. Finder'daki `finance` klasörünü Terminal penceresine **sürükleyip bırakın**
4. **Enter** tuşuna basın

### Yöntem 3: Terminal'de Klasöre Sağ Tık (macOS)

1. Finder'da `finance` klasörüne **sağ tıklayın**
2. **"Services"** → **"New Terminal at Folder"** seçin
3. Terminal otomatik olarak o klasörde açılır

## 📍 ADIM 3: Nerede Olduğunuzu Kontrol Edin

Terminal'de şunu yazın:

```bash
pwd
```

Bu komut, şu anda hangi klasörde olduğunuzu gösterir.

**Beklenen çıktı:**
```
/Users/berhankiyanus/finance
```

Eğer farklı bir yerdeyseniz, ADIM 2'yi tekrar yapın.

## 📍 ADIM 4: Dosyaları Kontrol Edin

Hangi dosyaların olduğunu görmek için:

```bash
ls
```

**Beklenen çıktıda şunları görmelisiniz:**
- `app.py`
- `github_deploy.sh`
- `README.md`
- `src/` klasörü
- vb.

## 📍 ADIM 5: Script'i Çalıştırın

Artık script'i çalıştırabilirsiniz:

```bash
./github_deploy.sh
```

**Ne yazdınız?**
- `./` = "Bu klasördeki"
- `github_deploy.sh` = "Bu dosyayı çalıştır"

**Enter** tuşuna basın!

## 🎯 Tam Örnek (Terminal'de Gördüğünüz)

Terminal'de şöyle görünecek:

```bash
berhankiyanus@MacBook-Pro ~ % cd /Users/berhankiyanus/finance
berhankiyanus@MacBook-Pro finance % ./github_deploy.sh
==========================================
🚀 GitHub Deploy Scripti
==========================================

✅ Git bulundu
📦 Dosyalar ekleniyor...
💾 Commit yapılıyor...
🚀 GitHub'a push ediliyor...
```

## ⚠️ Hata Alırsanız

### "Permission denied"

Script çalıştırma izni yok. Şunu yazın:

```bash
chmod +x github_deploy.sh
```

Sonra tekrar deneyin:

```bash
./github_deploy.sh
```

### "No such file or directory"

Yanlış klasördesiniz. ADIM 2'yi tekrar yapın.

### "command not found: git"

Git yüklü değil. Şunu yazın:

```bash
# macOS
brew install git

# veya
xcode-select --install
```

## 📝 Alternatif: Manuel Adımlar

Eğer script çalışmazsa, adımları manuel yapabilirsiniz:

```bash
# 1. Git repository başlat (ilk kez)
git init

# 2. Dosyaları ekle
git add .

# 3. Commit yap
git commit -m "İlk commit"

# 4. Branch adını ayarla
git branch -M main

# 5. GitHub repository'yi bağla (URL'i kendi repository'nizle değiştirin)
git remote add origin https://github.com/KULLANICI_ADI/finance-analysis.git

# 6. GitHub'a yükle
git push -u origin main
```

## 🎓 Terminal Komutları Özeti

| Komut | Ne Yapar |
|-------|----------|
| `pwd` | Nerede olduğunuzu gösterir |
| `ls` | Klasördeki dosyaları listeler |
| `cd klasör_adı` | O klasöre gider |
| `cd ..` | Bir üst klasöre çıkar |
| `./dosya.sh` | Script dosyasını çalıştırır |
| `chmod +x dosya.sh` | Script'e çalıştırma izni verir |

## 💡 İpuçları

1. **Terminal'de yazarken**: Büyük/küçük harf önemli! `github_deploy.sh` ≠ `Github_Deploy.sh`
2. **Yol gösterici**: Terminal'de `~` işareti "home klasörü" demektir
3. **Otomatik tamamlama**: Terminal'de `Tab` tuşuna basarak dosya/klasör isimlerini otomatik tamamlayabilirsiniz
4. **Önceki komutlar**: `↑` (yukarı ok) tuşu ile önceki komutları görebilirsiniz

## 🆘 Hala Sorun mu Var?

1. **Terminal'i kapatıp açın**
2. **Proje klasörüne tekrar gidin** (`cd /Users/berhankiyanus/finance`)
3. **Dosyaları kontrol edin** (`ls`)
4. **Script'i çalıştırın** (`./github_deploy.sh`)

---

**Başarılar! 🚀**

