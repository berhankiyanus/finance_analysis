#!/bin/bash
# GitHub Repository Bağlama Scripti

echo "=========================================="
echo "🔗 GitHub Repository Bağlama"
echo "=========================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Remote kontrolü
if git remote | grep -q "origin"; then
    current_remote=$(git remote get-url origin)
    echo -e "${YELLOW}⚠️  Zaten bir remote var:${NC}"
    echo "   $current_remote"
    echo ""
    read -p "Değiştirmek ister misiniz? (y/n): " change_remote
    if [ "$change_remote" = "y" ]; then
        git remote remove origin
        echo -e "${GREEN}✅ Eski remote kaldırıldı${NC}"
    else
        echo "Mevcut remote kullanılacak."
        exit 0
    fi
fi

echo ""
echo "GitHub repository URL'inizi girin:"
echo "   Örnek: https://github.com/kullanici-adi/finance-analysis.git"
echo ""
read -p "Repository URL: " repo_url

if [ -z "$repo_url" ]; then
    echo -e "${RED}❌ URL gerekli!${NC}"
    exit 1
fi

# Remote ekle
git remote add origin "$repo_url"

echo ""
echo -e "${GREEN}✅ Remote eklendi: $repo_url${NC}"
echo ""

# Push yapmak ister misiniz?
read -p "Şimdi GitHub'a push yapmak ister misiniz? (y/n): " push_now

if [ "$push_now" = "y" ]; then
    echo ""
    echo -e "${YELLOW}🚀 GitHub'a push ediliyor...${NC}"
    echo ""
    
    if git push -u origin main; then
        echo ""
        echo -e "${GREEN}✅ Başarıyla GitHub'a yüklendi!${NC}"
        echo ""
        echo "Repository'nizi şu adresten görebilirsiniz:"
        echo "   ${repo_url%.git}"
    else
        echo ""
        echo -e "${RED}❌ Push başarısız!${NC}"
        echo ""
        echo "Olası nedenler:"
        echo "  - Kimlik doğrulama hatası (Personal Access Token gerekebilir)"
        echo "  - Repository URL'i yanlış"
        echo "  - İnternet bağlantısı sorunu"
        echo ""
        echo "Çözüm için: GITHUB_PUSH_ADIMLARI.md dosyasına bakın"
    fi
else
    echo ""
    echo "Manuel push için şu komutu kullanın:"
    echo "   git push -u origin main"
fi

