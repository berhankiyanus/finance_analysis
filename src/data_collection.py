"""
Veri Toplama Modülü

Bu modül, şirketler hakkında haber ve finansal veri toplar.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import time
import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Gemini API için
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# .env dosyasından API key'leri yükle
# Proje kök dizinini bul (.env dosyasının olduğu yer)
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)


def get_company_name(ticker: str) -> str:
    """
    Hisse kodundan şirket tam adını çeker (yfinance kullanarak).
    
    Örn: 'THYAO.IS' -> 'Turk Hava Yollari Ao' veya 'Türk Hava Yolları'
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu (örn: "THYAO.IS", "AAPL", "KCHOL")
    
    Döndürür:
    --------
    str
        Şirket tam adı (bulunamazsa ticker'ın temizlenmiş hali)
    """
    try:
        # Türk hisseleri için .IS uzantısı ekle (eğer yoksa)
        ticker_formatted = ticker
        if not ('.IS' in ticker or ticker.endswith('.IS')):
            if len(ticker) == 5 and ticker.isalpha() and ticker.isupper():
                ticker_formatted = ticker + '.IS'
        
        stock = yf.Ticker(ticker_formatted)
        info = stock.info
        
        # Önce longName'i dene, yoksa shortName'i al
        company_name = info.get('longName') or info.get('shortName') or info.get('name')
        
        # Eğer yfinance isim bulamazsa, kodun kendisini döndür (veya .IS uzantısını temizle)
        if not company_name:
            return ticker.replace(".IS", "").replace(".", "")
        
        # Gereksiz uzun ifadeleri temizle (isteğe bağlı)
        clean_name = company_name.replace("Anonim Sirketi", "").replace("A.S.", "").replace("Anonim Şirketi", "").strip()
        
        # Türkçe karakterleri koru ama gereksiz kısaltmaları temizle
        if clean_name:
            print(f"✅ Şirket adı bulundu: {ticker} -> {clean_name}")
            return clean_name
        
        return ticker.replace(".IS", "").replace(".", "")
        
    except Exception as e:
        print(f"⚠️  Şirket ismi alınamadı ({ticker}): {e}")
        # Hata durumunda ticker'ın temizlenmiş halini döndür
        return ticker.replace(".IS", "").replace(".", "")


def get_news(company_name: str, days_back: int = 30, api_key: Optional[str] = None, ticker: Optional[str] = None) -> pd.DataFrame:
    """
    Şirket hakkında son haberleri toplar.
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı (örn: "Apple", "Microsoft"). Eğer ticker verilmişse ve company_name eksikse, otomatik çekilir.
    days_back : int
        Kaç gün geriye gidilecek (varsayılan: 30)
    api_key : str, optional
        NewsAPI key'i. Eğer verilmezse .env dosyasından okunur.
    ticker : str, optional
        Borsa kodu (örn: "AAPL", "MSFT"). Şirket adını otomatik çekmek ve relevance hesaplamasında kullanılır.
    
    Döndürür:
    --------
    pd.DataFrame
        Kolonlar: 'title', 'summary', 'content', 'published_at', 'source', 'url', 'relevance_score'
    """
    
    # Eğer ticker verilmişse ve company_name eksik/generikse, yfinance'den şirket adını çek
    if ticker and (not company_name or company_name == ticker or len(company_name) <= 5):
        print(f"🔍 Şirket adı eksik/generik, yfinance'den çekiliyor: {ticker}")
        fetched_name = get_company_name(ticker)
        if fetched_name and fetched_name != ticker.replace(".IS", "").replace(".", ""):
            company_name = fetched_name
            print(f"✅ Şirket adı güncellendi: {company_name}")
    
    # API key'i al
    if api_key is None:
        api_key = os.getenv('NEWS_API_KEY')
    
    # Debug: API key kontrolü
    if api_key:
        print(f"✅ NEWS_API_KEY bulundu: {api_key[:10]}...")
    else:
        print("⚠️  NEWS_API_KEY bulunamadı!")
        print(f"   .env dosyası yolu: {env_path}")
        print(f"   .env dosyası var mı: {env_path.exists()}")
        if env_path.exists():
            print(f"   .env içeriği (ilk 50 karakter): {env_path.read_text()[:50]}")
    
    # Eğer API key yoksa, dummy veri döndür (test amaçlı)
    if api_key is None:
        print("⚠️  NEWS_API_KEY bulunamadı. Dummy (test) veri kullanılıyor.")
        print("   📝 Gerçek haberler için:")
        print("   1. https://newsapi.org/ adresinden ücretsiz API key alın")
        print("   2. Proje kök dizininde .env dosyası oluşturun")
        print("   3. .env dosyasına şunu ekleyin: NEWS_API_KEY=your_api_key_here")
        print("   4. Uygulamayı yeniden başlatın")
        return _get_dummy_news(company_name, days_back)
    
    # NewsAPI'den haber çek
    try:
        # Tarih aralığını hesapla
        # end_date bugünün sonuna kadar (anlık haberler dahil)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # NewsAPI isteği - farklı arama stratejileri dene
        url = "https://newsapi.org/v2/everything"
        
        # Arama terimlerini hazırla (farklı varyasyonlar dene)
        # ÖNEMLİ: NewsAPI'de arama yaparken hem şirket adı hem ticker hem de kombinasyonlar kullanılır
        search_terms = []
        
        # Ticker sembolü varsa ÖNCE ekle (en spesifik - öncelikli)
        if ticker:
            # Ticker'ı temizle (.IS gibi uzantıları kaldır)
            ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
            search_terms.append(ticker_clean)  # En başa ekle (öncelikli)
            # Ticker + company_name kombinasyonları
            search_terms.append(f"{ticker_clean} {company_name}")
            search_terms.append(f"{company_name} {ticker_clean}")
            # Ticker + "stock" veya "shares" gibi finansal terimler
            search_terms.append(f"{ticker_clean} stock")
            search_terms.append(f"{ticker_clean} shares")
        
        # Şirket adını ekle
        search_terms.append(company_name)
        
        # Türkçe şirket adları için özel işlem (Koç, Sabancı, vb.)
        # Türkçe karakterleri İngilizce karşılıklarına çevir
        turkish_to_english = {
            'ç': 'c', 'Ç': 'C',
            'ğ': 'g', 'Ğ': 'G',
            'ı': 'i', 'İ': 'I',
            'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S',
            'ü': 'u', 'Ü': 'U'
        }
        
        # Türkçe karakterleri çevir
        company_name_english = company_name
        for turkish, english in turkish_to_english.items():
            company_name_english = company_name_english.replace(turkish, english)
        
        # Eğer çevrilmiş versiyon farklıysa, onu da ekle
        if company_name_english != company_name:
            search_terms.append(company_name_english)
        
        # Türk şirketleri için bilinen İngilizce alternatif isimler
        turkish_company_aliases = {
            'Koç Holding': ['Koc Holding', 'Koc Group', 'Koc', 'KCHOL', 'Koc Holding A.S.', 'Koc Holding AS'],
            'Sabancı Holding': ['Sabanci Holding', 'Sabanci Group', 'Sabanci', 'SAHOL', 'Sabanci Holding A.S.'],
            'Türk Hava Yolları': ['Turkish Airlines', 'THY', 'THYAO', 'Turkish Airlines Inc'],
            'Garanti BBVA': ['Garanti Bank', 'Garanti', 'GARAN', 'Garanti BBVA Bank'],
            'Akbank': ['Akbank', 'AKBNK', 'Akbank T.A.S.'],
            'İş Bankası': ['Is Bankasi', 'Is Bank', 'ISCTR', 'Is Bankasi A.S.'],
            'BİST': ['BIST', 'Borsa Istanbul', 'Istanbul Stock Exchange'],
        }
        
        # Şirket adı için alternatif isimler varsa ekle
        for turkish_name, aliases in turkish_company_aliases.items():
            if turkish_name.lower() in company_name.lower() or company_name.lower() in turkish_name.lower():
                search_terms.extend(aliases)
                break
        
        # "Holding" kelimesini kaldırarak da dene (daha genel arama)
        if 'holding' in company_name.lower():
            search_terms.append(company_name.lower().replace('holding', '').strip())
            search_terms.append(company_name_english.lower().replace('holding', '').strip())
            # Örnek: "Koç Holding" -> "Koc Holding" ve "Koc"
            if ' ' in company_name_english:
                words = company_name_english.split()
                first_word = words[0]
                if first_word not in search_terms:
                    search_terms.append(first_word)
                # İkinci kelimeyi de ekle (örn: "Holding")
                if len(words) > 1:
                    second_word = words[1]
                    if second_word not in search_terms:
                        search_terms.append(second_word)
        
        # Duplicate'leri temizle (sırayı koruyarak) - önce temizle, sonra eklemelere devam et
        search_terms = list(dict.fromkeys(search_terms))
        
        # Şirket adı ve ticker kombinasyonları (duplicate kontrolünden sonra)
        if ticker and company_name:
            ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
            # Farklı kombinasyonlar dene
            combinations = [
                f"{company_name} {ticker_clean}",
                f"{ticker_clean} {company_name}",
                f"{company_name_english} {ticker_clean}" if company_name_english != company_name else None
            ]
            for combo in combinations:
                if combo and combo not in search_terms:
                    search_terms.append(combo)
        
        # Son duplicate temizliği
        search_terms = list(dict.fromkeys(search_terms))
        
        print(f"🔍 Toplam {len(search_terms)} arama terimi hazırlandı: {search_terms[:15]}...")  # İlk 15'ini göster
        
        # Finansal etkisi olan haberler için arama terimleri ekle
        # Bu terimler şirket hakkında finansal haberleri bulmaya yardımcı olur
        financial_keywords = [
            "earnings", "profit", "revenue", "financial results", "quarterly results",
            "stock price", "share price", "trading", "market", "investment",
            "growth", "decline", "loss", "gain", "dividend", "acquisition", "merger"
        ]
        
        # Türkçe finansal terimler (Türk şirketleri için)
        turkish_financial_keywords = [
            "kar", "zarar", "gelir", "finansal sonuçlar", "çeyreklik sonuçlar",
            "hisse fiyatı", "borsa", "yatırım", "büyüme", "düşüş", "temettü", "satın alma", "birleşme"
        ]
        
        # Şirket adı + finansal terim kombinasyonları (İngilizce)
        if company_name:
            for keyword in financial_keywords[:5]:  # İlk 5 finansal terim
                search_terms.append(f"{company_name} {keyword}")
        
        # Ticker + finansal terim kombinasyonları (İngilizce)
        if ticker:
            ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
            for keyword in financial_keywords[:5]:
                search_terms.append(f"{ticker_clean} {keyword}")
        
        # Türk şirketleri için Türkçe finansal terimler
        if ticker and (ticker.endswith('.IS') or len(ticker.replace('.IS', '')) == 5):
            ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
            for keyword in turkish_financial_keywords[:5]:
                search_terms.append(f"{ticker_clean} {keyword}")
                if company_name:
                    search_terms.append(f"{company_name} {keyword}")
        
        # NewsAPI'den haber çek - TÜM arama terimlerini dene (daha fazla haber bulmak için)
        articles = []
        seen_urls = set()  # Duplicate haberleri önlemek için
        total_results = 0
        
        # Strateji 1: Dil parametresi olmadan geniş arama - TÜM terimleri dene
        print(f"🔍 {len(search_terms)} arama terimi ile geniş arama yapılıyor...")
        print(f"   📋 İlk 10 arama terimi: {search_terms[:10]}")
        
        # Ticker varsa öncelikli olarak dene (daha spesifik)
        priority_terms = []
        other_terms = []
        if ticker:
            ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
            for term in search_terms:
                if ticker_clean in term.upper() or term.upper() == ticker_clean:
                    priority_terms.append(term)
                else:
                    other_terms.append(term)
        else:
            other_terms = search_terms
        
        # Öncelikli terimleri önce dene
        search_terms_ordered = priority_terms + other_terms
        
        for search_term in search_terms_ordered:
            params = {
                'q': search_term,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'sortBy': 'publishedAt',
                'pageSize': 100,
                'apiKey': api_key
            }
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # API yanıtını kontrol et
                api_status = data.get('status', 'unknown')
                if api_status != 'ok':
                    error_msg = data.get('message', 'Bilinmeyen hata')
                    error_code = data.get('code', 'Bilinmiyor')
                    if error_code == 'apiKeyInvalid':
                        print(f"❌ NewsAPI hatası: API key geçersiz!")
                        print("   ⚠️  Lütfen Streamlit secrets'taki NEWS_API_KEY'i kontrol edin.")
                        return _get_dummy_news(company_name, days_back)
                    elif error_code == 'rateLimited':
                        print(f"❌ NewsAPI hatası: API limiti aşıldı!")
                        print("   ⚠️  Ücretsiz plan günde 100 istek sınırına sahip.")
                        return _get_dummy_news(company_name, days_back)
                    else:
                        print(f"⚠️  NewsAPI hatası: {error_msg} (Kod: {error_code})")
                        continue  # Bir sonraki arama terimini dene
                
                # Sonuçları topla (duplicate kontrolü ile)
                found_articles = data.get('articles', [])
                found_total = data.get('totalResults', 0)
                
                if found_articles:
                    # Duplicate kontrolü yap
                    new_articles = []
                    for article in found_articles:
                        article_url = article.get('url', '').strip()
                        if article_url and article_url not in seen_urls:
                            seen_urls.add(article_url)
                            new_articles.append(article)
                    
                    articles.extend(new_articles)
                    total_results = max(total_results, found_total)
                    print(f"✅ '{search_term}' için {len(new_articles)} yeni haber bulundu (toplam: {len(articles)})")
                else:
                    print(f"⚠️  '{search_term}' için 0 haber bulundu")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  '{search_term}' araması sırasında hata: {e}")
                continue  # Bir sonraki arama terimini dene
        
        # Strateji 2: Eğer hala yeterli haber yoksa, language parametresi ile dene
        if len(articles) < 20:  # Eğer 20'den az haber varsa, İngilizce arama da yap
            print(f"🔄 İngilizce haberler için ek arama yapılıyor...")
            for search_term in search_terms[:5]:  # İlk 5 terim için
                params = {
                    'q': search_term,
                    'from': start_date.strftime('%Y-%m-%d'),
                    'to': end_date.strftime('%Y-%m-%d'),
                    'sortBy': 'publishedAt',
                    'language': 'en',
                    'pageSize': 100,
                    'apiKey': api_key
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('status') == 'ok':
                        found_articles = data.get('articles', [])
                        if found_articles:
                            # Duplicate kontrolü
                            new_articles = []
                            for article in found_articles:
                                article_url = article.get('url', '').strip()
                                if article_url and article_url not in seen_urls:
                                    seen_urls.add(article_url)
                                    new_articles.append(article)
                            
                            articles.extend(new_articles)
                            total_results = max(total_results, data.get('totalResults', 0))
                            print(f"✅ '{search_term}' için {len(new_articles)} yeni İngilizce haber bulundu (toplam: {len(articles)})")
                except:
                    continue
        
        print(f"📊 NewsAPI yanıtı: {total_results} toplam haber bulundu, {len(articles)} benzersiz haber toplandı")
        print(f"   📅 Tarih aralığı: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
        print(f"   🔍 Arama terimleri: {len(search_terms)} farklı terim kullanıldı")
        print(f"   🤖 Gemini API ile alakalı haberler filtreleniyor...")
        
        if not articles:
            if total_results == 0:
                print(f"⚠️  NewsAPI'de '{company_name}' için son {days_back} günde haber bulunamadı.")
                print(f"   💡 İpucu: Şirket adını İngilizce veya ticker sembolü ile deneyin (örn: 'AAPL' yerine 'Apple Inc.')")
                print(f"   ℹ️  API key çalışıyor, ancak bu şirket için haber bulunamadı.")
                
                # NewsAPI başarısız - KAP raporlarını dene (Türk şirketleri için)
                # Türk hisseleri: .IS uzantılı veya 5 karakterli (KCHOL, THYAO, vb.)
                ticker_clean_for_check = ticker.replace('.IS', '').replace('.', '').upper() if ticker else ''
                is_turkish_stock = ticker and (
                    ticker.endswith('.IS') or 
                    len(ticker_clean_for_check) == 5 or
                    (len(ticker_clean_for_check) >= 4 and ticker_clean_for_check.isalpha())
                )
                
                if is_turkish_stock:
                    print(f"   🔄 NewsAPI'de haber yok, KAP raporları deneniyor (Türk hissesi: {ticker_clean_for_check})...")
                    try:
                        from .kap_scraper import get_kap_financial_reports
                    except ImportError:
                        try:
                            from src.kap_scraper import get_kap_financial_reports
                        except ImportError:
                            get_kap_financial_reports = None
                    
                    if get_kap_financial_reports:
                        try:
                            ticker_clean = ticker.replace('.IS', '').upper()
                            # KAP limit'ini artır (daha fazla rapor bulmak için)
                            kap_reports = get_kap_financial_reports(ticker_clean, limit=20)
                            
                            if kap_reports and len(kap_reports) > 0:
                                print(f"   ✅ {len(kap_reports)} KAP raporu bulundu, haber formatına çevriliyor...")
                                # KAP raporlarını haber formatına çevir
                                news_list = []
                                for report in kap_reports:
                                    news_list.append({
                                        'title': report.get('title', 'KAP Bildirimi'),
                                        'summary': report.get('title', ''),
                                        'content': report.get('title', ''),
                                        'published_at': report.get('date', datetime.now()),
                                        'source': 'KAP (Kamuyu Aydınlatma Platformu)',
                                        'url': report.get('link', ''),
                                        'relevance_score': 0.8
                                    })
                                
                                if news_list:
                                    news_df = pd.DataFrame(news_list)
                                    print(f"   ✅ {len(news_df)} haber KAP'tan alındı!")
                                    return news_df
                        except Exception as kap_error:
                            print(f"   ⚠️  KAP raporları alınamadı: {kap_error}")
                
                # KAP da yoksa boş DataFrame döndür (dummy veri değil)
                return pd.DataFrame(columns=['title', 'summary', 'content', 'published_at', 'source', 'url', 'relevance_score'])
            else:
                print(f"⚠️  NewsAPI'de {total_results} haber bulundu ama döndürülemedi (sayfalama sorunu olabilir).")
                print("⚠️  Dummy veri kullanılıyor.")
                return _get_dummy_news(company_name, days_back)
        
        news_list = []
        
        # Gemini API'yi bir kez configure et (eğer mevcut ve kullanılacaksa)
        gemini_model = None
        gemini_working = False
        if GEMINI_AVAILABLE:
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)
                    # Gemini 1.5 Flash modelini kullan (gemini-pro artık kullanılamıyor)
                    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                    # Gemini API'nin çalıştığını test et
                    try:
                        test_response = gemini_model.generate_content("Test: Sayı 1")
                        if test_response and test_response.text:
                            gemini_working = True
                            print("✅ Gemini API çalışıyor ve hazır (relevance kontrolü için).")
                        else:
                            print("⚠️  Gemini API yanıt vermedi (test başarısız).")
                    except Exception as test_error:
                        print(f"⚠️  Gemini API test hatası: {test_error}")
                        print("   Relevance kontrolü Gemini olmadan yapılacak.")
                except Exception as e:
                    print(f"⚠️  Gemini API yapılandırılamadı: {e}")
            else:
                print("ℹ️  GEMINI_API_KEY bulunamadı. Relevance kontrolü basit yöntemle yapılacak.")
        else:
            print("ℹ️  Gemini API yüklü değil. Relevance kontrolü basit yöntemle yapılacak.")
        
        # Her bir article'ı güvenli şekilde işle
        for article in articles:
            if not article or not isinstance(article, dict):
                continue  # Geçersiz article'ı atla
            
            # Title kontrolü - title yoksa veya çok kısaysa atla
            title = article.get('title', '').strip() if article.get('title') else ''
            if not title or len(title) < 10:
                continue  # Geçersiz title'ı atla
            
            try:
                summary = article.get('description', '').strip() if article.get('description') else ''
                content = article.get('content', '').strip() if article.get('content') else ''
                
                # Relevance score hesapla - şirket adı ve ticker'ın haber içinde geçip geçmediğini kontrol et
                company_lower = company_name.lower()
                title_lower = title.lower()
                summary_lower = summary.lower()
                content_lower = content.lower()
                
                relevance_score = 0.0
                
                # 1. Başlıkta şirket adı geçiyorsa yüksek relevance
                if company_lower in title_lower:
                    relevance_score += 0.5
                
                # 2. Özet veya içerikte şirket adı geçiyorsa orta relevance
                if company_lower in summary_lower or company_lower in content_lower:
                    relevance_score += 0.3
                
                # 3. Ticker sembolü kontrolü (büyük harflerle)
                # Eğer ticker parametresi verilmişse kullan, yoksa company_name'in kendisi ticker olabilir
                ticker_to_check = ticker if ticker else (company_name if company_name.isupper() and len(company_name) <= 5 else None)
                
                if ticker_to_check:
                    ticker_upper = ticker_to_check.upper()
                    # Başlıkta ticker geçiyorsa yüksek relevance
                    if ticker_upper in title:
                        relevance_score += 0.4
                    # Özet veya içerikte ticker geçiyorsa orta relevance
                    if ticker_upper in summary or ticker_upper in content:
                        relevance_score += 0.3
                    # Ticker'ın küçük harfli versiyonu da kontrol et
                    ticker_lower = ticker_to_check.lower()
                    if ticker_lower in title_lower or ticker_lower in summary_lower or ticker_lower in content_lower:
                        relevance_score += 0.2
                
                # 4. Şirket adının kısaltılmış versiyonları (örn: "Apple Inc." -> "Apple")
                # Şirket adında boşluk varsa, ilk kelimeyi de kontrol et
                if ' ' in company_name:
                    first_word = company_name.split()[0].lower()
                    if first_word in title_lower or first_word in summary_lower or first_word in content_lower:
                        relevance_score += 0.1
                
                # Gemini API ile relevance ve finansal etki kontrolü (TÜM haberler için)
                # Bu sayede sadece alakalı ve finansal etkisi olan haberler seçilir
                gemini_relevance_score = None
                financial_impact_score = None
                if gemini_model and gemini_working:
                    try:
                        # Haber metnini hazırla (daha fazla içerik)
                        news_text = f"{title}\n\n{summary}\n\n{content[:800]}"  # İlk 800 karakter
                        
                        # Gemini'ye relevance ve finansal etki kontrolü için prompt
                        relevance_prompt = f"""Sen bir finansal analiz uzmanısın. Aşağıdaki haberin "{company_name}" şirketi için finansal açıdan ne kadar önemli olduğunu değerlendir.

ŞİRKET: {company_name}
TICKER: {ticker if ticker else 'Belirtilmemiş'}

HABER:
{news_text}

GÖREVİN:
Bu haberin "{company_name}" şirketi için finansal açıdan önemli olup olmadığını belirle. Haber:
1. Şirket hakkında mı? (şirket adı, ticker, iş operasyonları)
2. Şirketin borsa performansına, fiyatına, değerine etkisi var mı?
3. Finansal sonuçlar, kâr/zarar, yatırım, büyüme, düşüş, kriz, başarı gibi konular içeriyor mu?

ÖNEMLİ KRİTERLER:
- ✅ ALKALI VE ÖNEMLİ: Şirket hakkında finansal sonuçlar, kâr/zarar, yatırım, büyüme, düşüş, fiyat hareketleri, borsa performansı, iş geliştirmeleri, sorunlar, krizler
- ❌ ALKASIZ VEYA ÖNEMSİZ: Sadece genel piyasa haberleri, şirket adı geçiyor ama finansal etkisi yok, rutin duyurular, sosyal sorumluluk projeleri (finansal etkisi yoksa), genel sektör haberleri

Yanıtını SADECE şu formatta JSON olarak ver:
{{
    "is_relevant": true veya false,
    "relevance_score": 0.0 ile 1.0 arası (ne kadar alakalı - şirket hakkında mı?),
    "financial_impact": 0.0 ile 1.0 arası (finansal etkisi ne kadar? - borsa/fiyat/kâr/zarar etkisi),
    "has_financial_impact": true veya false (finansal etkisi var mı?),
    "reason": "Kısa açıklama (Türkçe, 1-2 cümle)"
}}

SADECE JSON yanıt ver, başka hiçbir şey yazma."""
                        
                        response = gemini_model.generate_content(relevance_prompt)
                        response_text = response.text.strip()
                        
                        # JSON'u extract et
                        if "```json" in response_text:
                            response_text = response_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in response_text:
                            response_text = response_text.split("```")[1].split("```")[0].strip()
                        
                        result = json.loads(response_text)
                        
                        gemini_relevance_score = float(result.get('relevance_score', 0.0))
                        financial_impact_score = float(result.get('financial_impact', 0.0))
                        has_financial_impact = result.get('has_financial_impact', False)
                        is_relevant = result.get('is_relevant', False)
                        
                        # Finansal etkisi olmayan haberleri filtrele
                        if not has_financial_impact and financial_impact_score < 0.3:
                            print(f"🤖 Gemini: '{title[:50]}...' -> Finansal etkisi yok, filtreleniyor (impact: {financial_impact_score:.2f})")
                            continue  # Finansal etkisi olmayan haberi atla
                        
                        # Hem relevance hem finansal etkiyi dikkate al
                        if is_relevant and has_financial_impact:
                            # Kombine score: relevance (40%) + financial_impact (60%)
                            combined_score = (gemini_relevance_score * 0.4) + (financial_impact_score * 0.6)
                            relevance_score = max(relevance_score, combined_score)
                            print(f"🤖 Gemini: '{title[:50]}...' -> Alakalı ve finansal etkisi var (relevance: {gemini_relevance_score:.2f}, impact: {financial_impact_score:.2f}, combined: {combined_score:.2f})")
                        elif is_relevant:
                            # Alakalı ama finansal etkisi düşük - relevance score'u kullan
                            relevance_score = max(relevance_score, gemini_relevance_score * 0.7)  # Düşük ağırlık
                            print(f"🤖 Gemini: '{title[:50]}...' -> Alakalı ama finansal etkisi düşük (relevance: {gemini_relevance_score:.2f})")
                        else:
                            # Alakasız - relevance score'u düşür
                            relevance_score = min(relevance_score, gemini_relevance_score)
                            print(f"🤖 Gemini: '{title[:50]}...' -> Alakasız (score: {gemini_relevance_score:.2f})")
                            
                    except Exception as e:
                        # Gemini hatası - normal relevance score'u kullan
                        pass
                
                # Eğer Gemini kontrolü yapıldıysa, onun skorlarını kullan
                # Eğer yapılmadıysa, basit relevance score'u kullan
                if gemini_relevance_score is not None:
                    # Gemini kontrolü yapıldı - onun skorlarını kullan
                    # Eğer finansal etkisi yoksa veya çok düşükse, atla
                    if financial_impact_score is not None and financial_impact_score < 0.25:
                        continue  # Finansal etkisi çok düşük, atla
                    # Relevance threshold'u biraz düşür (daha fazla haber geçsin)
                    if relevance_score < 0.35:
                        continue  # Alakasız haberi atla
                else:
                    # Gemini kontrolü yapılmadı - basit relevance score kullan
                    if relevance_score < 0.4:
                        continue  # Alakasız haberi atla
                
                news_list.append({
                    'title': title,
                    'summary': summary,
                    'content': content,
                    'published_at': pd.to_datetime(article.get('publishedAt', datetime.now())),
                    'source': article.get('source', {}).get('name', 'Unknown') if isinstance(article.get('source'), dict) else 'Unknown',
                    'url': article.get('url', '').strip() if article.get('url') else '',
                    'relevance_score': relevance_score
                })
            except Exception as e:
                print(f"⚠️  Haber işlenirken hata: {e}")
                continue  # Bu article'ı atla ve devam et
        
        # DataFrame oluştur
        if not news_list:
            print(f"⚠️  NewsAPI'den haber döndü ama geçerli haber bulunamadı.")
            # KAP raporlarını dene (Türk şirketleri için)
            ticker_clean_for_kap = ticker.replace('.IS', '').replace('.', '').upper() if ticker else ''
            is_turkish_stock = ticker and (
                ticker.endswith('.IS') or 
                len(ticker_clean_for_kap) == 5 or
                (len(ticker_clean_for_kap) >= 4 and ticker_clean_for_kap.isalpha())
            )
            
            if is_turkish_stock:
                print(f"   🔄 KAP raporları deneniyor (Türk hissesi: {ticker_clean_for_kap})...")
                try:
                    from .kap_scraper import get_kap_financial_reports
                except ImportError:
                    try:
                        from src.kap_scraper import get_kap_financial_reports
                    except ImportError:
                        get_kap_financial_reports = None
                
                if get_kap_financial_reports:
                    try:
                        # KAP limit'ini artır (daha fazla rapor bulmak için)
                        kap_reports = get_kap_financial_reports(ticker_clean_for_kap, limit=20)
                        
                        if kap_reports and len(kap_reports) > 0:
                            print(f"   ✅ {len(kap_reports)} KAP raporu bulundu, haber formatına çevriliyor...")
                            # KAP raporlarını haber formatına çevir
                            kap_news_list = []
                            for report in kap_reports:
                                kap_news_list.append({
                                    'title': report.get('title', 'KAP Bildirimi'),
                                    'summary': report.get('title', ''),
                                    'content': report.get('title', ''),
                                    'published_at': report.get('date', datetime.now()),
                                    'source': 'KAP (Kamuyu Aydınlatma Platformu)',
                                    'url': report.get('link', ''),
                                    'relevance_score': 0.8
                                })
                            
                            if kap_news_list:
                                kap_df = pd.DataFrame(kap_news_list)
                                print(f"   ✅ {len(kap_df)} haber KAP'tan alındı!")
                                return kap_df
                    except Exception as kap_error:
                        print(f"   ⚠️  KAP raporları alınamadı: {kap_error}")
                        import traceback
                        traceback.print_exc()
            
            print("⚠️  Dummy veri kullanılıyor.")
            return _get_dummy_news(company_name, days_back)
        
        news_df = pd.DataFrame(news_list)
        
        # Boş DataFrame kontrolü
        if news_df.empty:
            print(f"⚠️  NewsAPI'den haber döndü ama DataFrame boş.")
            # KAP raporlarını dene (Türk şirketleri için)
            ticker_clean_for_kap = ticker.replace('.IS', '').replace('.', '').upper() if ticker else ''
            is_turkish_stock = ticker and (
                ticker.endswith('.IS') or 
                len(ticker_clean_for_kap) == 5 or
                (len(ticker_clean_for_kap) >= 4 and ticker_clean_for_kap.isalpha())
            )
            
            if is_turkish_stock:
                print(f"   🔄 KAP raporları deneniyor (Türk hissesi: {ticker_clean_for_kap})...")
                try:
                    from .kap_scraper import get_kap_financial_reports
                except ImportError:
                    try:
                        from src.kap_scraper import get_kap_financial_reports
                    except ImportError:
                        get_kap_financial_reports = None
                
                if get_kap_financial_reports:
                    try:
                        # KAP limit'ini artır (daha fazla rapor bulmak için)
                        kap_reports = get_kap_financial_reports(ticker_clean_for_kap, limit=20)
                        
                        if kap_reports and len(kap_reports) > 0:
                            print(f"   ✅ {len(kap_reports)} KAP raporu bulundu, haber formatına çevriliyor...")
                            # KAP raporlarını haber formatına çevir
                            kap_news_list = []
                            for report in kap_reports:
                                kap_news_list.append({
                                    'title': report.get('title', 'KAP Bildirimi'),
                                    'summary': report.get('title', ''),
                                    'content': report.get('title', ''),
                                    'published_at': report.get('date', datetime.now()),
                                    'source': 'KAP (Kamuyu Aydınlatma Platformu)',
                                    'url': report.get('link', ''),
                                    'relevance_score': 0.8
                                })
                            
                            if kap_news_list:
                                kap_df = pd.DataFrame(kap_news_list)
                                print(f"   ✅ {len(kap_df)} haber KAP'tan alındı!")
                                return kap_df
                    except Exception as kap_error:
                        print(f"   ⚠️  KAP raporları alınamadı: {kap_error}")
                        import traceback
                        traceback.print_exc()
            
            print("⚠️  Dummy veri kullanılıyor.")
            return _get_dummy_news(company_name, days_back)
        
        # Kolon kontrolü - 'title' kolonu yoksa hata ver
        if 'title' not in news_df.columns:
            print(f"⚠️  NewsAPI'den dönen veri formatı beklenenden farklı. Kolonlar: {list(news_df.columns)}")
            print(f"⚠️  Dummy veri kullanılıyor.")
            return _get_dummy_news(company_name, days_back)
        
        # Boş haberleri filtrele (güvenli şekilde)
        if 'title' in news_df.columns:
            # NaN ve boş string kontrolü
            news_df = news_df[news_df['title'].notna() & (news_df['title'].astype(str).str.len() > 10)]
        else:
            print(f"⚠️  'title' kolonu bulunamadı. Dummy veri kullanılıyor.")
            return _get_dummy_news(company_name, days_back)
        
        # Tarihe göre sırala (en yeni önce)
        if not news_df.empty and 'published_at' in news_df.columns:
            news_df = news_df.sort_values('published_at', ascending=False).reset_index(drop=True)
        
        if news_df.empty:
            print(f"⚠️  Filtreleme sonrası haber kalmadı.")
            # KAP raporlarını dene (Türk şirketleri için)
            ticker_clean_for_kap = ticker.replace('.IS', '').replace('.', '').upper() if ticker else ''
            is_turkish_stock = ticker and (
                ticker.endswith('.IS') or 
                len(ticker_clean_for_kap) == 5 or
                (len(ticker_clean_for_kap) >= 4 and ticker_clean_for_kap.isalpha())
            )
            
            if is_turkish_stock:
                print(f"   🔄 KAP raporları deneniyor (Türk hissesi: {ticker_clean_for_kap})...")
                try:
                    from .kap_scraper import get_kap_financial_reports
                except ImportError:
                    try:
                        from src.kap_scraper import get_kap_financial_reports
                    except ImportError:
                        get_kap_financial_reports = None
                
                if get_kap_financial_reports:
                    try:
                        # KAP limit'ini artır (daha fazla rapor bulmak için)
                        kap_reports = get_kap_financial_reports(ticker_clean_for_kap, limit=20)
                        
                        if kap_reports and len(kap_reports) > 0:
                            print(f"   ✅ {len(kap_reports)} KAP raporu bulundu, haber formatına çevriliyor...")
                            # KAP raporlarını haber formatına çevir
                            kap_news_list = []
                            for report in kap_reports:
                                kap_news_list.append({
                                    'title': report.get('title', 'KAP Bildirimi'),
                                    'summary': report.get('title', ''),
                                    'content': report.get('title', ''),
                                    'published_at': report.get('date', datetime.now()),
                                    'source': 'KAP (Kamuyu Aydınlatma Platformu)',
                                    'url': report.get('link', ''),
                                    'relevance_score': 0.8
                                })
                            
                            if kap_news_list:
                                kap_df = pd.DataFrame(kap_news_list)
                                print(f"   ✅ {len(kap_df)} haber KAP'tan alındı!")
                                return kap_df
                    except Exception as kap_error:
                        print(f"   ⚠️  KAP raporları alınamadı: {kap_error}")
                        import traceback
                        traceback.print_exc()
            
            print("⚠️  Dummy veri kullanılıyor.")
            return _get_dummy_news(company_name, days_back)
        
        print(f"✅ {len(news_df)} haber bulundu (bugün dahil son {days_back} gün).")
        if not news_df.empty and 'published_at' in news_df.columns:
            latest_news_date = news_df['published_at'].max()
            print(f"   En yeni haber: {latest_news_date.strftime('%Y-%m-%d %H:%M')}")
        
        return news_df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ NewsAPI hatası: {e}")
        error_code = None
        error_message = None
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_message = error_data.get('message', 'Bilinmeyen hata')
                error_code = error_data.get('code', 'unknown')
                print(f"   Hata detayı: {error_message}")
                if error_code == 'apiKeyInvalid':
                    print("   ⚠️  API key geçersiz! Lütfen .env dosyasındaki NEWS_API_KEY'i kontrol edin.")
                elif error_code == 'rateLimited':
                    print("   ⚠️  API limiti aşıldı! Ücretsiz plan günde 100 istek sınırına sahip.")
            except:
                pass
        
        # NewsAPI başarısız olursa, KAP raporlarını kullan (Türk şirketleri için)
        if ticker and (ticker.endswith('.IS') or len(ticker.replace('.IS', '')) == 5):
            print("   🔄 NewsAPI başarısız, KAP raporları deneniyor...")
            try:
                from .kap_scraper import get_kap_financial_reports
            except ImportError:
                try:
                    from src.kap_scraper import get_kap_financial_reports
                except ImportError:
                    get_kap_financial_reports = None
            
            if get_kap_financial_reports:
                try:
                    ticker_clean = ticker.replace('.IS', '').upper()
                    # KAP limit'ini artır (daha fazla rapor bulmak için)
                    kap_reports = get_kap_financial_reports(ticker_clean, limit=20)
                    
                    if kap_reports and len(kap_reports) > 0:
                        print(f"   ✅ {len(kap_reports)} KAP raporu bulundu, haber formatına çevriliyor...")
                        # KAP raporlarını haber formatına çevir
                        news_list = []
                        for report in kap_reports:
                            news_list.append({
                                'title': report.get('title', 'KAP Bildirimi'),
                                'summary': report.get('title', ''),
                                'content': report.get('title', ''),
                                'published_at': report.get('date', datetime.now()),
                                'source': 'KAP (Kamuyu Aydınlatma Platformu)',
                                'url': report.get('link', ''),
                                'relevance_score': 0.8  # KAP raporları yüksek relevans
                            })
                        
                        if news_list:
                            news_df = pd.DataFrame(news_list)
                            print(f"   ✅ {len(news_df)} haber KAP'tan alındı!")
                            return news_df
                except Exception as kap_error:
                    print(f"   ⚠️  KAP raporları alınamadı: {kap_error}")
        
        # KAP da başarısız olursa dummy veri
        print("⚠️  NewsAPI ve KAP başarısız, dummy veri kullanılıyor.")
        return _get_dummy_news(company_name, days_back)
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        
        # NewsAPI başarısız olursa, KAP raporlarını kullan (Türk şirketleri için)
        if ticker and (ticker.endswith('.IS') or len(ticker.replace('.IS', '')) == 5):
            print("   🔄 KAP raporları deneniyor...")
            try:
                from .kap_scraper import get_kap_financial_reports
            except ImportError:
                try:
                    from src.kap_scraper import get_kap_financial_reports
                except ImportError:
                    get_kap_financial_reports = None
            
            if get_kap_financial_reports:
                try:
                    ticker_clean = ticker.replace('.IS', '').upper()
                    # KAP limit'ini artır (daha fazla rapor bulmak için)
                    kap_reports = get_kap_financial_reports(ticker_clean, limit=20)
                    
                    if kap_reports and len(kap_reports) > 0:
                        print(f"   ✅ {len(kap_reports)} KAP raporu bulundu!")
                        # KAP raporlarını haber formatına çevir
                        news_list = []
                        for report in kap_reports:
                            news_list.append({
                                'title': report.get('title', 'KAP Bildirimi'),
                                'summary': report.get('title', ''),
                                'content': report.get('title', ''),
                                'published_at': report.get('date', datetime.now()),
                                'source': 'KAP (Kamuyu Aydınlatma Platformu)',
                                'url': report.get('link', ''),
                                'relevance_score': 0.8
                            })
                        
                        if news_list:
                            news_df = pd.DataFrame(news_list)
                            return news_df
                except Exception as kap_error:
                    print(f"   ⚠️  KAP raporları alınamadı: {kap_error}")
        
        print("⚠️  Dummy veri kullanılıyor.")
        return _get_dummy_news(company_name, days_back)


def _get_dummy_news(company_name: str, days_back: int) -> pd.DataFrame:
    """
    Test amaçlı dummy haber verisi üretir.
    """
    dummy_news = [
        {
            'title': f'{company_name} şirketi güçlü finansal sonuçlar açıkladı',
            'summary': f'{company_name} son çeyrekte beklentileri aşan kâr açıkladı.',
            'content': f'{company_name} şirketi...',
            'published_at': datetime.now() - timedelta(days=2),
            'source': 'Dummy News',
            'url': 'https://example.com/news1',
            'relevance_score': 0.9
        },
        {
            'title': f'{company_name} için yeni yatırım fırsatları',
            'summary': f'Analistler {company_name} için olumlu görünüm belirtiyor.',
            'content': f'{company_name} hakkında...',
            'published_at': datetime.now() - timedelta(days=5),
            'source': 'Dummy News',
            'url': 'https://example.com/news2',
            'relevance_score': 0.8
        },
        {
            'title': f'{company_name} piyasada volatilite yaşıyor',
            'summary': f'{company_name} hisseleri son günlerde dalgalı seyir izliyor.',
            'content': f'{company_name} için...',
            'published_at': datetime.now() - timedelta(days=10),
            'source': 'Dummy News',
            'url': 'https://example.com/news3',
            'relevance_score': 0.7
        }
    ]
    
    return pd.DataFrame(dummy_news)


def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Hisse için OHLCV verisini çeker (get_price_data için alias).
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu (örn: "AAPL", "THYAO.IS", "KCHOL")
    period : str
        Veri periyodu (örn: "1mo", "3mo", "6mo", "1y", "2y", "5y")
    
    Döndürür:
    --------
    pd.DataFrame
        Kolonlar: 'date', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close'
    """
    return get_price_data(ticker, period)


def get_price_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Şirket için fiyat verisi çeker.
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu (örn: "AAPL", "THYAO.IS", "KCHOL")
    period : str
        Veri periyodu (örn: "1mo", "3mo", "6mo", "1y", "2y", "5y")
    
    Döndürür:
    --------
    pd.DataFrame
        Kolonlar: 'date', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close'
    """
    
    try:
        # Türk hisseleri için .IS uzantısı ekle (eğer yoksa)
        # 5 karakterli ve sadece harf içeren hisseler için .IS ekle
        ticker_formatted = ticker
        if not ('.IS' in ticker or ticker.endswith('.IS')):
            if len(ticker) == 5 and ticker.isalpha() and ticker.isupper():
                ticker_formatted = ticker + '.IS'
                print(f"📊 Türk hissesi tespit edildi: {ticker} -> {ticker_formatted}")
        
        # yfinance ile veri çek
        stock = yf.Ticker(ticker_formatted)
        hist = stock.history(period=period)
        
        if hist.empty:
            print(f"⚠️  {ticker} için veri bulunamadı. Dummy veri kullanılıyor.")
            return _get_dummy_price_data(ticker)
        
        # Kolon isimlerini standartlaştır
        hist.reset_index(inplace=True)
        hist.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        
        # Adjusted close ekle (eğer yoksa close'u kullan)
        if 'Adj Close' in hist.columns:
            hist['adjusted_close'] = hist['Adj Close']
        else:
            hist['adjusted_close'] = hist['close']
        
        # Sadece gerekli kolonları seç
        price_df = hist[['date', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close']].copy()
        
        # Tarihi datetime'a çevir
        price_df['date'] = pd.to_datetime(price_df['date'])
        
        # Tarihe göre sırala
        price_df.sort_values('date', inplace=True)
        price_df.reset_index(drop=True, inplace=True)
        
        print(f"✅ {len(price_df)} günlük fiyat verisi çekildi.")
        return price_df
        
    except Exception as e:
        print(f"❌ Fiyat verisi çekilirken hata: {e}")
        print("⚠️  Dummy veri kullanılıyor.")
        return _get_dummy_price_data(ticker)


def _get_dummy_price_data(ticker: str) -> pd.DataFrame:
    """
    Test amaçlı dummy fiyat verisi üretir.
    """
    # Son 100 gün için dummy veri
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    # Basit bir random walk simülasyonu
    import numpy as np
    np.random.seed(42)
    
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, len(dates))  # Günlük %0.1 ortalama getiri, %2 volatilite
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    price_df = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates)),
        'adjusted_close': prices
    })
    
    return price_df


def get_fundamentals(ticker: str) -> Optional[Dict]:
    """
    Şirket için kapsamlı finansal göstergeleri çeker.
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu
    
    Döndürür:
    --------
    dict veya None
        Finansal göstergeler (P/E, gelir büyümesi, kâr marjı, bilanço, gelir tablosu vb.)
    """
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Temel finansal oranlar
        fundamentals = {
            # Fiyat Oranları
            'pe_ratio': info.get('trailingPE', None),
            'forward_pe': info.get('forwardPE', None),
            'peg_ratio': info.get('pegRatio', None),
            'price_to_book': info.get('priceToBook', None),
            'price_to_sales': info.get('priceToSalesTrailing12Months', None),
            'ev_to_revenue': info.get('enterpriseToRevenue', None),
            'ev_to_ebitda': info.get('enterpriseToEbitda', None),
            
            # Piyasa Değeri
            'market_cap': info.get('marketCap', None),
            'enterprise_value': info.get('enterpriseValue', None),
            'shares_outstanding': info.get('sharesOutstanding', None),
            'float_shares': info.get('floatShares', None),
            
            # Büyüme Oranları
            'revenue_growth': info.get('revenueGrowth', None),
            'earnings_growth': info.get('earningsQuarterlyGrowth', None),
            'earnings_yearly_growth': info.get('earningsGrowth', None),
            'revenue_per_share': info.get('revenuePerShare', None),
            
            # Kârlılık Oranları
            'profit_margin': info.get('profitMargins', None),
            'gross_margin': info.get('grossMargins', None),
            'operating_margin': info.get('operatingMargins', None),
            'ebitda_margin': info.get('ebitdaMargins', None),
            'roe': info.get('returnOnEquity', None),
            'roa': info.get('returnOnAssets', None),
            'roic': info.get('returnOnInvestedCapital', None),
            
            # Finansal Sağlık
            'debt_to_equity': info.get('debtToEquity', None),
            'debt_to_assets': info.get('debtToAssets', None),
            'current_ratio': info.get('currentRatio', None),
            'quick_ratio': info.get('quickRatio', None),
            'cash_per_share': info.get('totalCashPerShare', None),
            'book_value': info.get('bookValue', None),
            
            # Likidite
            'total_cash': info.get('totalCash', None),
            'total_debt': info.get('totalDebt', None),
            'total_revenue': info.get('totalRevenue', None),
            'free_cashflow': info.get('freeCashflow', None),
            
            # Temettü
            'dividend_yield': info.get('dividendYield', None),
            'payout_ratio': info.get('payoutRatio', None),
            'dividend_rate': info.get('dividendRate', None),
            
            # Diğer
            'beta': info.get('beta', None),
            '52_week_high': info.get('fiftyTwoWeekHigh', None),
            '52_week_low': info.get('fiftyTwoWeekLow', None),
            'target_price': info.get('targetMeanPrice', None),
        }
        
        # Finansal tabloları çek (bilanço, gelir tablosu, nakit akış)
        try:
            # Bilanço (Balance Sheet)
            balance_sheet = stock.balance_sheet
            if not balance_sheet.empty:
                # Son dönem bilanço verileri
                latest_bs = balance_sheet.iloc[:, 0] if len(balance_sheet.columns) > 0 else pd.Series()
                fundamentals['balance_sheet'] = {
                    'total_assets': latest_bs.get('Total Assets', None),
                    'total_liabilities': latest_bs.get('Total Liab', None),
                    'total_equity': latest_bs.get('Stockholders Equity', None),
                    'cash_and_equivalents': latest_bs.get('Cash And Cash Equivalents', None),
                    'total_debt_bs': latest_bs.get('Total Debt', None),
                }
            
            # Gelir Tablosu (Income Statement)
            income_stmt = stock.financials
            if not income_stmt.empty:
                latest_is = income_stmt.iloc[:, 0] if len(income_stmt.columns) > 0 else pd.Series()
                fundamentals['income_statement'] = {
                    'total_revenue': latest_is.get('Total Revenue', None),
                    'gross_profit': latest_is.get('Gross Profit', None),
                    'operating_income': latest_is.get('Operating Income', None),
                    'net_income': latest_is.get('Net Income', None),
                    'ebitda': latest_is.get('EBITDA', None),
                    'eps': latest_is.get('Diluted EPS', None),
                }
            
            # Nakit Akış Tablosu (Cash Flow)
            cashflow = stock.cashflow
            if not cashflow.empty:
                latest_cf = cashflow.iloc[:, 0] if len(cashflow.columns) > 0 else pd.Series()
                fundamentals['cash_flow'] = {
                    'operating_cashflow': latest_cf.get('Total Cash From Operating Activities', None),
                    'investing_cashflow': latest_cf.get('Total Cashflows From Investing Activities', None),
                    'financing_cashflow': latest_cf.get('Total Cash From Financing Activities', None),
                    'free_cashflow_cf': latest_cf.get('Free Cash Flow', None),
                }
        except Exception as e:
            print(f"⚠️  Finansal tablolar çekilirken hata: {e}")
        
        # None değerleri filtrele (sadece temel göstergeler için)
        basic_fundamentals = {k: v for k, v in fundamentals.items() if k not in ['balance_sheet', 'income_statement', 'cash_flow'] and v is not None}
        
        # Finansal tabloları ekle (None olsa bile)
        if 'balance_sheet' in fundamentals:
            basic_fundamentals['balance_sheet'] = fundamentals['balance_sheet']
        if 'income_statement' in fundamentals:
            basic_fundamentals['income_statement'] = fundamentals['income_statement']
        if 'cash_flow' in fundamentals:
            basic_fundamentals['cash_flow'] = fundamentals['cash_flow']
        
        if basic_fundamentals:
            print(f"✅ {len([k for k in basic_fundamentals.keys() if k not in ['balance_sheet', 'income_statement', 'cash_flow']])} finansal gösterge bulundu.")
            if 'balance_sheet' in basic_fundamentals:
                print(f"   📊 Bilanço verisi eklendi")
            if 'income_statement' in basic_fundamentals:
                print(f"   💰 Gelir tablosu verisi eklendi")
            if 'cash_flow' in basic_fundamentals:
                print(f"   💵 Nakit akış tablosu verisi eklendi")
            return basic_fundamentals
        else:
            print("⚠️  Finansal gösterge bulunamadı.")
            return None
            
    except Exception as e:
        print(f"⚠️  Finansal gösterge çekilirken hata: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_all_data_for_stock(
    ticker: str,
    company_name: str,
    period: str = "1y",
    days_back: int = 30,
    include_kap: bool = True,
    include_google_search: bool = True,
    include_macro: bool = True
) -> Dict:
    """
    Bir hisse senedi için tüm verileri toplayan "orkestra şefi" fonksiyonu.
    
    Bu fonksiyon, farklı veri kaynaklarından (yfinance, NewsAPI, KAP, Google Search, TCMB)
    veri toplayıp birleştirir.
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu (örn: "THYAO", "AAPL")
    company_name : str
        Şirket adı (örn: "Türk Hava Yolları", "Apple")
    period : str
        Fiyat verisi periyodu (varsayılan: "1y")
    days_back : int
        Kaç gün geriye gidilecek (haberler için, varsayılan: 30)
    include_kap : bool
        KAP verileri dahil edilsin mi? (varsayılan: True, sadece TR için)
    include_google_search : bool
        Google Search haberleri dahil edilsin mi? (varsayılan: True)
    include_macro : bool
        Makroekonomik veriler dahil edilsin mi? (varsayılan: True)
    
    Döndürür:
    --------
    dict
        Tüm verileri içeren sözlük:
        {
            'price_df': pd.DataFrame,
            'news_df': pd.DataFrame,
            'fundamentals': dict,
            'kap_reports': list,
            'google_news': list,
            'macro_data': dict
        }
    """
    
    print(f"\n{'='*60}")
    print(f"📊 {company_name} ({ticker}) için veri toplama başlatılıyor...")
    print(f"{'='*60}\n")
    
    results = {
        'ticker': ticker,
        'company_name': company_name,
        'price_df': pd.DataFrame(),
        'news_df': pd.DataFrame(),
        'fundamentals': None,
        'kap_reports': [],
        'google_news': [],
        'macro_data': {}
    }
    
    # 1. Fiyat verileri (yfinance)
    print("1️⃣  Fiyat verileri çekiliyor...")
    try:
        results['price_df'] = get_price_data(ticker, period=period)
        if not results['price_df'].empty:
            print(f"   ✅ {len(results['price_df'])} günlük fiyat verisi çekildi.")
        else:
            print("   ⚠️  Fiyat verisi bulunamadı.")
    except Exception as e:
        print(f"   ❌ Fiyat verisi çekilirken hata: {e}")
    
    # 2. Haberler (NewsAPI + Google Search + KAP - Akıllı Arama)
    print("\n2️⃣  Haberler çekiliyor (Akıllı Arama ile)...")
    try:
        # Önce şirket adını otomatik çek (eğer eksikse veya generikse)
        if not company_name or company_name == ticker or len(company_name) <= 5:
            print("   🔍 Şirket adı eksik/generik, yfinance'den çekiliyor...")
            company_name = get_company_name(ticker)
            results['company_name'] = company_name
            print(f"   ✅ Şirket adı: {company_name}")
        
        # NewsAPI ile haber çek (otomatik şirket adı ile)
        print("   📰 NewsAPI deneniyor...")
        results['news_df'] = get_news(company_name, days_back=days_back, ticker=ticker)
        
        # Eğer NewsAPI'de yeterli haber yoksa, Google Search'ü dene
        if results['news_df'].empty or len(results['news_df']) < 3:
            print("   🔄 NewsAPI'de yeterli haber yok, Google Search deneniyor...")
            try:
                from .google_search import search_market_news
            except ImportError:
                try:
                    from src.google_search import search_market_news
                except ImportError:
                    search_market_news = None
            
            if search_market_news:
                try:
                    # Akıllı arama sorguları (şirket adı + Türkçe terimler)
                    ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
                    search_queries = [
                        f"{company_name} hisse haberleri",
                        f"{ticker_clean} borsa yorum",
                        f"{company_name} finansal sonuçlar",
                        f"{ticker_clean} kar zarar",
                        f"{company_name} borsa",
                        f"{ticker_clean} hisse",
                        f"{company_name} yatırım",
                        f"{ticker_clean} analiz"
                    ]
                    
                    google_news = []
                    for query in search_queries:
                        try:
                            news = search_market_news([query], num_results=5)
                            if news:
                                google_news.extend(news)
                                if len(google_news) >= 10:  # Daha fazla haber bulmak için limit artırıldı
                                    break
                        except Exception as query_error:
                            print(f"   ⚠️  '{query}' sorgusu için hata: {query_error}")
                            continue
                    
                    if google_news:
                        # Google Search haberlerini DataFrame formatına çevir
                        google_news_list = []
                        for news_item in google_news:
                            google_news_list.append({
                                'title': news_item.get('title', ''),
                                'summary': news_item.get('snippet', ''),
                                'content': news_item.get('snippet', ''),
                                'published_at': news_item.get('published_at', datetime.now()),
                                'source': news_item.get('source', 'Google Search'),
                                'url': news_item.get('link', ''),
                                'relevance_score': 0.7  # Google Search haberleri için orta relevance
                            })
                        
                        google_df = pd.DataFrame(google_news_list)
                        if not results['news_df'].empty:
                            # Mevcut haberlerle birleştir (duplicate kontrolü ile)
                            combined_df = pd.concat([results['news_df'], google_df], ignore_index=True)
                            # URL'e göre duplicate'leri temizle
                            results['news_df'] = combined_df.drop_duplicates(subset=['url'], keep='first')
                        else:
                            results['news_df'] = google_df
                        print(f"   ✅ Google Search'ten {len(google_news)} haber eklendi.")
                except Exception as google_error:
                    print(f"   ⚠️  Google Search hatası: {google_error}")
                    import traceback
                    traceback.print_exc()
        
        # Eğer hala haber yoksa, KAP raporlarını dene (get_news içinde de denenmiş olabilir ama tekrar deneyelim)
        if results['news_df'].empty:
            print("   🔄 Haber bulunamadı, KAP raporları deneniyor...")
            ticker_clean_for_kap = ticker.replace('.IS', '').replace('.', '').upper()
            is_turkish_stock = ticker and (
                ticker.endswith('.IS') or 
                len(ticker_clean_for_kap) == 5 or
                (len(ticker_clean_for_kap) >= 4 and ticker_clean_for_kap.isalpha())
            )
            
            if is_turkish_stock:
                try:
                    from .kap_scraper import get_kap_financial_reports
                except ImportError:
                    try:
                        from src.kap_scraper import get_kap_financial_reports
                    except ImportError:
                        get_kap_financial_reports = None
                
                if get_kap_financial_reports:
                    try:
                        # KAP limit'ini artır (daha fazla rapor bulmak için)
                        kap_reports = get_kap_financial_reports(ticker_clean_for_kap, limit=20)
                        
                        if kap_reports and len(kap_reports) > 0:
                            print(f"   ✅ {len(kap_reports)} KAP raporu bulundu, haber formatına çevriliyor...")
                            # KAP raporlarını haber formatına çevir
                            kap_news_list = []
                            for report in kap_reports:
                                kap_news_list.append({
                                    'title': report.get('title', 'KAP Bildirimi'),
                                    'summary': report.get('title', ''),
                                    'content': report.get('title', ''),
                                    'published_at': report.get('date', datetime.now()),
                                    'source': 'KAP (Kamuyu Aydınlatma Platformu)',
                                    'url': report.get('link', ''),
                                    'relevance_score': 0.8
                                })
                            
                            if kap_news_list:
                                kap_df = pd.DataFrame(kap_news_list)
                                results['news_df'] = kap_df
                                print(f"   ✅ {len(kap_df)} haber KAP'tan alındı!")
                    except Exception as kap_error:
                        print(f"   ⚠️  KAP raporları alınamadı: {kap_error}")
                        import traceback
                        traceback.print_exc()
        
        if not results['news_df'].empty:
            print(f"   ✅ Toplam {len(results['news_df'])} haber bulundu (NewsAPI + Google Search + KAP).")
        else:
            print("   ⚠️  Haber bulunamadı (NewsAPI, Google Search ve KAP denendi).")
    except Exception as e:
        print(f"   ❌ Haber çekilirken hata: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Finansal göstergeler (yfinance)
    print("\n3️⃣  Finansal göstergeler çekiliyor...")
    try:
        results['fundamentals'] = get_fundamentals(ticker)
        if results['fundamentals']:
            print(f"   ✅ Finansal göstergeler çekildi.")
        else:
            print("   ⚠️  Finansal gösterge bulunamadı.")
    except Exception as e:
        print(f"   ❌ Finansal gösterge çekilirken hata: {e}")
    
    # 4. KAP raporları (sadece TR için)
    if include_kap and (ticker.endswith('.IS') or len(ticker) == 5):
        print("\n4️⃣  KAP raporları çekiliyor...")
        try:
            from .kap_scraper import get_kap_financial_reports
        except ImportError:
            from src.kap_scraper import get_kap_financial_reports
        
        try:
            # KAP limit'ini artır (daha fazla rapor bulmak için)
            results['kap_reports'] = get_kap_financial_reports(ticker, limit=20)
            if results['kap_reports']:
                print(f"   ✅ {len(results['kap_reports'])} KAP raporu bulundu.")
            else:
                print("   ⚠️  KAP raporu bulunamadı.")
        except Exception as e:
            print(f"   ❌ KAP raporu çekilirken hata: {e}")
    else:
        print("\n4️⃣  KAP raporları atlandı (TR hissesi değil veya kapalı).")
    
    # 5. Google Search haberleri (opsiyonel - API key gerekli)
    if include_google_search:
        print("\n5️⃣  Google Search'ten haberler çekiliyor...")
        try:
            from .google_search import search_market_news
        except ImportError:
            try:
                from src.google_search import search_market_news
            except ImportError:
                print("   ⚠️  google_search modülü bulunamadı. Google Search atlanıyor.")
                search_market_news = None
        
        if search_market_news:
            try:
                # Hisse bazlı arama
                stock_keywords = [ticker, company_name]
                results['google_news'] = search_market_news(stock_keywords, num_results=10)
                if results.get('google_news'):
                    print(f"   ✅ {len(results['google_news'])} Google Search haberi bulundu.")
                else:
                    print("   ⚠️  Google Search'ten haber bulunamadı (API key eksik olabilir).")
            except Exception as e:
                print(f"   ⚠️  Google Search hatası: {e}")
                results['google_news'] = []
        else:
            results['google_news'] = []
    else:
        results['google_news'] = []
        print("\n5️⃣  Google Search atlandı (include_google_search=False).")
    
    # 6. Makroekonomik veriler
    if include_macro:
        print("\n6️⃣  Makroekonomik veriler çekiliyor...")
        try:
            from .macro_data import get_macroeconomic_data
        except ImportError:
            from src.macro_data import get_macroeconomic_data
        
        try:
            # Ülke belirle (ticker'a göre)
            country = "TR" if (ticker.endswith('.IS') or len(ticker) == 5) else "US"
            results['macro_data'] = get_macroeconomic_data(country=country)
            if results['macro_data']:
                print(f"   ✅ {len(results['macro_data'])} makro gösterge bulundu.")
            else:
                print("   ⚠️  Makro veri bulunamadı.")
        except Exception as e:
            print(f"   ❌ Makro veri çekilirken hata: {e}")
    else:
        print("\n6️⃣  Makroekonomik veriler atlandı.")
    
    # Özet
    print(f"\n{'='*60}")
    print("📊 Veri Toplama Özeti:")
    print(f"   • Fiyat verisi: {'✅' if not results['price_df'].empty else '❌'}")
    print(f"   • NewsAPI haberleri: {'✅' if not results['news_df'].empty else '❌'} ({len(results['news_df'])} haber)")
    print(f"   • Finansal göstergeler: {'✅' if results['fundamentals'] else '❌'}")
    print(f"   • KAP raporları: {'✅' if results['kap_reports'] else '❌'} ({len(results['kap_reports'])} rapor)")
    print(f"   • Google haberleri: {'✅' if results['google_news'] else '❌'} ({len(results['google_news'])} haber)")
    print(f"   • Makro veriler: {'✅' if results['macro_data'] else '❌'} ({len(results['macro_data'])} gösterge)")
    print(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    # Test
    print("=== Veri Toplama Modülü Test ===\n")
    
    # Orkestra şefi testi
    print("🎯 Orkestra Şefi Fonksiyonu Testi:")
    all_data = get_all_data_for_stock(
        ticker="THYAO",
        company_name="Türk Hava Yolları",
        period="6mo",
        days_back=30
    )
    print("\n✅ Tüm veriler toplandı!")
    
    # Ayrı testler
    print("\n" + "="*60)
    print("Ayrı Fonksiyon Testleri:")
    print("="*60)
    
    # Haber testi
    print("\n1. Haber toplama testi:")
    news_df = get_news("Apple", days_back=7)
    print(news_df.head())
    print()
    
    # Fiyat testi
    print("2. Fiyat verisi testi:")
    price_df = get_price_data("AAPL", period="6mo")
    print(price_df.head())
    print()
    
    # Finansal gösterge testi
    print("3. Finansal gösterge testi:")
    fundamentals = get_fundamentals("AAPL")
    print(fundamentals)

