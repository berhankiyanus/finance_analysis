#!/bin/bash
# GitHub'a Yükleme ve Deploy Scripti

echo "=========================================="
echo "🚀 GitHub Deploy Scripti"
echo "=========================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Git kontrolü
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git yüklü değil!${NC}"
    echo "   macOS: brew install git"
    echo "   veya: https://git-scm.com/downloads"
    exit 1
fi

echo -e "${GREEN}✅ Git bulundu${NC}"

# Proje dizininde miyiz?
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ app.py bulunamadı. Proje kök dizininde olduğunuzdan emin olun.${NC}"
    exit 1
fi

# Git repository kontrolü
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Git repository bulunamadı. Oluşturuluyor...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository oluşturuldu${NC}"
fi

# Remote kontrolü
if ! git remote | grep -q "origin"; then
    echo ""
    echo -e "${YELLOW}⚠️  GitHub remote bulunamadı.${NC}"
    echo ""
    echo "Lütfen GitHub'da bir repository oluşturun:"
    echo "  1. https://github.com adresine gidin"
    echo "  2. 'New repository' butonuna tıklayın"
    echo "  3. Repository adını girin (örn: finance-analysis)"
    echo "  4. 'Public' seçin"
    echo "  5. 'Create repository' tıklayın"
    echo ""
    read -p "GitHub repository URL'inizi girin (örn: https://github.com/kullanici/finance-analysis.git): " repo_url
    
    if [ -z "$repo_url" ]; then
        echo -e "${RED}❌ Repository URL'i gerekli!${NC}"
        exit 1
    fi
    
    git remote add origin "$repo_url"
    echo -e "${GREEN}✅ Remote eklendi${NC}"
fi

# Dosyaları ekle
echo ""
echo -e "${YELLOW}📦 Dosyalar ekleniyor...${NC}"
git add .

# Commit mesajı
echo ""
read -p "Commit mesajı girin (varsayılan: 'Update'): " commit_msg
commit_msg=${commit_msg:-Update}

# Commit yap
echo ""
echo -e "${YELLOW}💾 Commit yapılıyor...${NC}"
git commit -m "$commit_msg"

# Branch kontrolü
current_branch=$(git branch --show-current)
if [ -z "$current_branch" ]; then
    git branch -M main
    current_branch="main"
fi

# Push
echo ""
echo -e "${YELLOW}🚀 GitHub'a push ediliyor...${NC}"
echo ""

if git push -u origin "$current_branch"; then
    echo ""
    echo -e "${GREEN}✅ Başarıyla GitHub'a yüklendi!${NC}"
    echo ""
    echo "=========================================="
    echo "📝 Sonraki Adımlar:"
    echo "=========================================="
    echo ""
    echo "1. https://streamlit.io/cloud adresine gidin"
    echo "2. GitHub hesabınızla giriş yapın"
    echo "3. 'New app' butonuna tıklayın"
    echo "4. Repository'nizi seçin"
    echo "5. Main file path: app.py"
    echo "6. 'Deploy' butonuna tıklayın"
    echo ""
    echo "Detaylı rehber için: DEPLOY_REHBERI.md dosyasına bakın"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Push başarısız!${NC}"
    echo ""
    echo "Olası nedenler:"
    echo "  - GitHub kimlik doğrulama hatası"
    echo "  - Repository URL'i yanlış"
    echo "  - İnternet bağlantısı sorunu"
    echo ""
    echo "Çözüm:"
    echo "  - Personal Access Token kullanın (DEPLOY_REHBERI.md'ye bakın)"
    echo "  - Repository URL'ini kontrol edin: git remote -v"
    exit 1
fi

