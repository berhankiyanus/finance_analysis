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


def get_news(company_name: str, days_back: int = 30, api_key: Optional[str] = None, ticker: Optional[str] = None) -> pd.DataFrame:
    """
    Şirket hakkında son haberleri toplar.
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı (örn: "Apple", "Microsoft")
    days_back : int
        Kaç gün geriye gidilecek (varsayılan: 30)
    api_key : str, optional
        NewsAPI key'i. Eğer verilmezse .env dosyasından okunur.
    ticker : str, optional
        Borsa kodu (örn: "AAPL", "MSFT"). Relevance hesaplamasında kullanılır.
    
    Döndürür:
    --------
    pd.DataFrame
        Kolonlar: 'title', 'summary', 'content', 'published_at', 'source', 'url', 'relevance_score'
    """
    
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
        search_terms = [company_name]
        
        # Ticker sembolü varsa arama terimlerine ekle
        if ticker:
            search_terms.append(ticker)
            # Ticker'ın küçük harfli versiyonunu da ekle
            if ticker.isupper():
                search_terms.append(ticker.lower())
        
        # Eğer şirket adı büyük harflerle yazılmışsa (ticker sembolü olabilir), küçük harfe çevir
        if company_name.isupper() and len(company_name) <= 5:
            if company_name not in search_terms:  # Zaten eklenmemişse
                search_terms.append(company_name.lower())
        
        # Şirket adı ve ticker'ı birleştirerek de ara (örn: "Apple AAPL")
        if ticker and company_name:
            combined_search = f"{company_name} {ticker}"
            search_terms.append(combined_search)
        
        # NewsAPI'den haber çek - farklı stratejiler dene
        articles = []
        total_results = 0
        
        # Strateji 1: Dil parametresi olmadan geniş arama
        for search_term in search_terms:
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
                
                # Sonuçları topla
                found_articles = data.get('articles', [])
                found_total = data.get('totalResults', 0)
                
                if found_articles:
                    articles.extend(found_articles)
                    total_results = max(total_results, found_total)
                    print(f"✅ '{search_term}' için {len(found_articles)} haber bulundu")
                    break  # Haber bulundu, diğer aramalara gerek yok
                else:
                    print(f"⚠️  '{search_term}' için 0 haber bulundu")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️  '{search_term}' araması sırasında hata: {e}")
                continue  # Bir sonraki arama terimini dene
        
        # Strateji 2: Eğer hala haber bulunamadıysa, language parametresi ile dene
        if not articles:
            print(f"🔄 Alternatif arama stratejisi deneniyor...")
            for search_term in search_terms:
                # Önce İngilizce haberler
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
                            articles.extend(found_articles)
                            total_results = max(total_results, data.get('totalResults', 0))
                            print(f"✅ '{search_term}' için {len(found_articles)} İngilizce haber bulundu")
                            break
                except:
                    continue
        
        print(f"📊 NewsAPI yanıtı: {total_results} toplam haber bulundu, {len(articles)} haber döndürüldü")
        print(f"   📅 Tarih aralığı: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
        print(f"   🔍 Arama terimi: '{company_name}'")
        
        if not articles:
            if total_results == 0:
                print(f"⚠️  NewsAPI'de '{company_name}' için son {days_back} günde haber bulunamadı.")
                print(f"   💡 İpucu: Şirket adını İngilizce veya ticker sembolü ile deneyin (örn: 'AAPL' yerine 'Apple Inc.')")
                print(f"   ℹ️  API key çalışıyor, ancak bu şirket için haber bulunamadı.")
                # API key çalışıyor ama haber yok - boş DataFrame döndür (dummy veri değil)
                return pd.DataFrame(columns=['title', 'summary', 'content', 'published_at', 'source', 'url', 'relevance_score'])
            else:
                print(f"⚠️  NewsAPI'de {total_results} haber bulundu ama döndürülemedi (sayfalama sorunu olabilir).")
                print("⚠️  Dummy veri kullanılıyor.")
                return _get_dummy_news(company_name, days_back)
        
        news_list = []
        
        # Gemini API'yi bir kez configure et (eğer mevcut ve kullanılacaksa)
        gemini_model = None
        if GEMINI_AVAILABLE:
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)
                    gemini_model = genai.GenerativeModel('gemini-pro')
                    print("🤖 Gemini API relevance kontrolü için hazır.")
                except Exception as e:
                    print(f"⚠️  Gemini API yapılandırılamadı: {e}")
        
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
                
                # Gemini API ile relevance kontrolü (eğer mevcut ve relevance score düşükse)
                gemini_relevance_score = None
                if gemini_model and relevance_score < 0.5:
                    try:
                        # Haber metnini hazırla
                        news_text = f"{title}\n\n{summary}\n\n{content[:500]}"  # İlk 500 karakter
                        
                        # Gemini'ye relevance kontrolü için prompt
                        relevance_prompt = f"""Sen bir finansal analiz uzmanısın. Aşağıdaki haberin "{company_name}" şirketi ile ne kadar alakalı olduğunu değerlendir.

ŞİRKET: {company_name}
TICKER: {ticker if ticker else 'Belirtilmemiş'}

HABER:
{news_text}

GÖREVİN:
Bu haberin "{company_name}" şirketi ile alakalı olup olmadığını belirle. Haber şirket hakkında mı, yoksa sadece genel bir haber mi?

Yanıtını SADECE şu formatta JSON olarak ver:
{{
    "is_relevant": true veya false,
    "relevance_score": 0.0 ile 1.0 arası bir sayı (ne kadar alakalı),
    "reason": "Kısa açıklama (Türkçe, 1 cümle)"
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
                        
                        if result.get('is_relevant', False):
                            gemini_relevance_score = float(result.get('relevance_score', 0.5))
                            # Gemini'nin relevance score'unu kullan (daha güvenilir)
                            relevance_score = max(relevance_score, gemini_relevance_score)
                            print(f"🤖 Gemini: '{title[:50]}...' -> Alakalı (score: {gemini_relevance_score:.2f})")
                        else:
                            # Gemini alakasız diyorsa, relevance score'u düşür
                            gemini_relevance_score = float(result.get('relevance_score', 0.0))
                            relevance_score = min(relevance_score, gemini_relevance_score)
                            print(f"🤖 Gemini: '{title[:50]}...' -> Alakasız (score: {gemini_relevance_score:.2f})")
                            
                    except Exception as e:
                        # Gemini hatası - normal relevance score'u kullan
                        pass
                
                # Eğer relevance çok düşükse (0.3'ten az), haber alakasız olabilir - atla
                if relevance_score < 0.3:
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
            print(f"⚠️  NewsAPI'den haber döndü ama geçerli haber bulunamadı. Dummy veri kullanılıyor.")
            return _get_dummy_news(company_name, days_back)
        
        news_df = pd.DataFrame(news_list)
        
        # Boş DataFrame kontrolü
        if news_df.empty:
            print(f"⚠️  NewsAPI'den haber döndü ama DataFrame boş. Dummy veri kullanılıyor.")
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
            print(f"⚠️  Filtreleme sonrası haber kalmadı. Dummy veri kullanılıyor.")
            return _get_dummy_news(company_name, days_back)
        
        print(f"✅ {len(news_df)} haber bulundu (bugün dahil son {days_back} gün).")
        if not news_df.empty and 'published_at' in news_df.columns:
            latest_news_date = news_df['published_at'].max()
            print(f"   En yeni haber: {latest_news_date.strftime('%Y-%m-%d %H:%M')}")
        
        return news_df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ NewsAPI hatası: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   Hata detayı: {error_data.get('message', 'Bilinmeyen hata')}")
                if error_data.get('code') == 'apiKeyInvalid':
                    print("   ⚠️  API key geçersiz! Lütfen .env dosyasındaki NEWS_API_KEY'i kontrol edin.")
                elif error_data.get('code') == 'rateLimited':
                    print("   ⚠️  API limiti aşıldı! Ücretsiz plan günde 100 istek sınırına sahip.")
            except:
                pass
        print("⚠️  Dummy veri kullanılıyor.")
        return _get_dummy_news(company_name, days_back)
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
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


def get_price_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Şirket için fiyat verisi çeker.
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu (örn: "AAPL", "THYAO.IS")
    period : str
        Veri periyodu (örn: "1mo", "3mo", "6mo", "1y", "2y", "5y")
    
    Döndürür:
    --------
    pd.DataFrame
        Kolonlar: 'date', 'open', 'high', 'low', 'close', 'volume', 'adjusted_close'
    """
    
    try:
        # yfinance ile veri çek
        stock = yf.Ticker(ticker)
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
    Şirket için temel finansal göstergeleri çeker (opsiyonel).
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu
    
    Döndürür:
    --------
    dict veya None
        Finansal göstergeler (P/E, gelir büyümesi, kâr marjı vb.)
    """
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # İlgili göstergeleri çıkar
        fundamentals = {
            'pe_ratio': info.get('trailingPE', None),
            'market_cap': info.get('marketCap', None),
            'revenue_growth': info.get('revenueGrowth', None),
            'profit_margin': info.get('profitMargins', None),
            'debt_to_equity': info.get('debtToEquity', None),
            'current_ratio': info.get('currentRatio', None),
            'roe': info.get('returnOnEquity', None)
        }
        
        # None değerleri filtrele
        fundamentals = {k: v for k, v in fundamentals.items() if v is not None}
        
        if fundamentals:
            print(f"✅ {len(fundamentals)} finansal gösterge bulundu.")
            return fundamentals
        else:
            print("⚠️  Finansal gösterge bulunamadı.")
            return None
            
    except Exception as e:
        print(f"⚠️  Finansal gösterge çekilirken hata: {e}")
        return None


if __name__ == "__main__":
    # Test
    print("=== Veri Toplama Modülü Test ===\n")
    
    # Haber testi
    print("1. Haber toplama testi:")
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

