# macOS Gatekeeper Çözümleri

## ⚠️ ÖNEMLİ UYARI

**Gatekeeper'ı tamamen kapatmak GÜVENLİK RİSKİ oluşturur!** Önce alternatif çözümleri deneyin.

## ✅ Önerilen Çözümler (Güvenli)

### 1. Tek Satırlık Python Komutu (EN İYİ - Şu an kullanıyoruz)

```bash
cd /Users/berhankiyanus/Desktop/Finance
/opt/homebrew/opt/python@3.14/bin/python3.14 -c "import sys; sys.path.insert(0, '/Users/berhankiyanus/Desktop/Finance/venv/lib/python3.14/site-packages'); import os; os.chdir('/Users/berhankiyanus/Desktop/Finance'); from streamlit.web.cli import main; sys.argv = ['streamlit', 'run', 'app.py']; main()"
```

**Avantajlar:**
- ✅ Güvenli (Gatekeeper açık kalır)
- ✅ Dosya okuma gerektirmez
- ✅ Çalışıyor

### 2. Script'e İzin Verme (Önerilen)

Belirli script'lere izin verebilirsiniz:

```bash
# Script'i çalıştırılabilir yap
chmod +x BASLAT_STREAMLIT_DIRECT.sh

# Gatekeeper'dan muaf tut (sadece bu script için)
sudo xattr -rd com.apple.quarantine BASLAT_STREAMLIT_DIRECT.sh
```

### 3. Terminal'e İzin Verme

**Sistem Ayarları** → **Gizlilik ve Güvenlik** → **Tam Disk Erişimi** → Terminal'i ekleyin.

## ⚠️ Gatekeeper'ı Kapatma (ÖNERİLMEZ)

### Yöntem 1: Geçici Olarak Kapatma

```bash
# Gatekeeper'ı geçici olarak kapat (sadece bu terminal için)
sudo spctl --master-disable
```

**Kapatmak için:**
```bash
# Gatekeeper'ı tekrar aç
sudo spctl --master-enable
```

### Yöntem 2: Kalıcı Olarak Kapatma (ÇOK RİSKLİ!)

```bash
# Gatekeeper'ı tamamen kapat (ÖNERİLMEZ!)
sudo spctl --master-disable
```

**Güvenlik Riskleri:**
- ❌ Kötü amaçlı yazılımlar çalışabilir
- ❌ İmzalanmamış uygulamalar otomatik çalışır
- ❌ Sistem güvenliği azalır

## 🎯 Önerilen Yaklaşım

**Şu anki çözümümüz (tek satırlık Python komutu) en güvenli ve çalışan yöntem!**

Gatekeeper'ı kapatmak yerine:
1. ✅ Tek satırlık Python komutunu kullanın (şu an çalışıyor)
2. ✅ Script kullanın: `bash BASLAT_STREAMLIT_DIRECT.sh`
3. ✅ Terminal'e tam disk erişimi verin (daha güvenli)

## 📝 Notlar

- Gatekeeper macOS'un güvenlik özelliğidir
- Kapatmak yerine izin vermek daha güvenlidir
- Şu anki çözümümüz Gatekeeper açıkken çalışıyor

