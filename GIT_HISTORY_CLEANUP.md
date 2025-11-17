# Git Geçmişinden API Key Temizleme Rehberi

## ⚠️ ÖNEMLİ GÜVENLİK UYARISI

API key'iniz GitHub'da görünmüş durumda. **HEMEN** şunları yapmalısınız:

### 1. API Key'leri Revoke Edin (HEMEN!)

#### Gemini API Key:
1. https://makersuite.google.com/app/apikey adresine gidin
2. Mevcut API key'inizi **SİLİN** veya **REVOKE EDİN**
3. Yeni bir API key oluşturun
4. Yeni key'i `.env` dosyasına ekleyin

#### NewsAPI Key:
1. https://newsapi.org/account adresine gidin
2. Mevcut API key'inizi **REVOKE EDİN**
3. Yeni bir API key oluşturun
4. Yeni key'i `.env` dosyasına ekleyin

### 2. Git Geçmişini Temizleme

Git geçmişinden API key'leri tamamen silmek için aşağıdaki yöntemlerden birini kullanın:

#### Yöntem 1: BFG Repo-Cleaner (Önerilen - Daha Kolay)

1. **BFG Repo-Cleaner'ı indirin:**
   ```bash
   brew install bfg  # Mac için
   # veya
   # https://rtyley.github.io/bfg-repo-cleaner/ adresinden indirin
   ```

2. **API key'leri temizleyin:**
   ```bash
   cd /Users/berhankiyanus/Desktop/Finance
   
   # Gemini API key'i temizle
   bfg --replace-text <(echo "YOUR_GEMINI_API_KEY==>REMOVED")
   
   # NewsAPI key'i temizle
   bfg --replace-text <(echo "YOUR_NEWS_API_KEY==>REMOVED")
   
   # Git geçmişini güncelle
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. **Force push yapın (DİKKATLİ!):**
   ```bash
   git push origin --force --all
   ```

#### Yöntem 2: git filter-branch (Manuel)

```bash
cd /Users/berhankiyanus/Desktop/Finance

# Gemini API key'i temizle
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch STREAMLIT_CLOUD_GEMINI_API_KEY.md" \
  --prune-empty --tag-name-filter cat -- --all

# NewsAPI key'i temizle (eğer başka dosyalarda varsa)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch STREAMLIT_CLOUD_API_KEY.md" \
  --prune-empty --tag-name-filter cat -- --all

# Geçmişi temizle
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

#### Yöntem 3: GitHub'da Private Repository Yapın (Geçici Çözüm)

1. GitHub repository'nizi **Private** yapın
2. API key'lerini revoke edin
3. Yeni key'ler oluşturun

### 3. Kontrol

Temizleme işleminden sonra:

```bash
# Git geçmişinde API key arayın
git log --all -p -S "YOUR_GEMINI_API_KEY" | head -20
git log --all -p -S "YOUR_NEWS_API_KEY" | head -20
```

Eğer hiçbir sonuç çıkmazsa, temizleme başarılı demektir.

## ⚠️ UYARI

- Force push yapmadan önce **tüm değişikliklerinizi commit edin**
- Force push yaptıktan sonra, diğer geliştiriciler repository'yi yeniden clone etmeli
- API key'leri **ASLA** tekrar commit etmeyin
- `.env` dosyasının `.gitignore`'da olduğundan emin olun

## 📝 .gitignore Kontrolü

`.env` dosyasının `.gitignore`'da olduğundan emin olun:

```bash
cat .gitignore | grep -i env
```

Eğer yoksa, ekleyin:

```bash
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

