"""
Haber Kaynağı Çeşitliliği Modülü

NewsAPI'ye alternatif haber kaynakları sağlar.
Rate limit veya API key eksikliğinde otomatik fallback.
"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
import os
from src.logger_config import setup_logger
from src.http_client import get_http_client

logger = setup_logger(__name__)


class NewsSourceManager:
    """
    Çoklu haber kaynağı yöneticisi.
    """
    
    def __init__(self):
        self.sources = []
        self._setup_sources()
    
    def _setup_sources(self):
        """Haber kaynaklarını yapılandırır."""
        # 1. NewsAPI (birincil)
        if os.getenv('NEWS_API_KEY'):
            self.sources.append(NewsAPISource())
        
        # 2. Yahoo Finance RSS (ücretsiz, sınırsız)
        self.sources.append(YahooRSSSource())
        
        # 3. Financial Modeling Prep (opsiyonel)
        if os.getenv('FMP_API_KEY'):
            self.sources.append(FMPSource())
        
        # 4. Finnhub (opsiyonel)
        if os.getenv('FINNHUB_API_KEY'):
            self.sources.append(FinnhubSource())
        
        logger.info(f"{len(self.sources)} haber kaynağı yapılandırıldı")
    
    def get_news(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        days_back: int = 30,
        max_articles: int = 50
    ) -> pd.DataFrame:
        """
        Tüm kaynaklardan haber toplar (fallback mekanizması ile).
        
        Parametreler:
        ------------
        company_name : str
            Şirket adı
        ticker : str, optional
            Borsa kodu
        days_back : int
            Kaç gün geriye gidilecek
        max_articles : int
            Maksimum haber sayısı
        
        Döndürür:
        --------
        pd.DataFrame
            Toplanan haberler
        """
        all_articles = []
        seen_urls = set()
        
        for source in self.sources:
            try:
                logger.info(f"{source.name} kaynağından haber toplanıyor...")
                articles = source.fetch_news(
                    company_name=company_name,
                    ticker=ticker,
                    days_back=days_back
                )
                
                # Duplicate kontrolü
                new_articles = []
                for article in articles:
                    url = article.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        new_articles.append(article)
                
                all_articles.extend(new_articles)
                logger.info(f"✅ {source.name}: {len(new_articles)} yeni haber bulundu (toplam: {len(all_articles)})")
                
                # Yeterli haber varsa dur
                if len(all_articles) >= max_articles:
                    logger.info(f"Yeterli haber toplandı ({len(all_articles)}), durduruluyor.")
                    break
                    
            except Exception as e:
                logger.warning(f"{source.name} kaynağından haber alınamadı: {e}")
                continue
        
        if not all_articles:
            logger.warning("Hiçbir kaynaktan haber bulunamadı!")
            return pd.DataFrame(columns=['title', 'summary', 'published_at', 'source', 'url', 'relevance_score'])
        
        # DataFrame oluştur
        df = pd.DataFrame(all_articles)
        df['published_at'] = pd.to_datetime(df['published_at'])
        df = df.sort_values('published_at', ascending=False).head(max_articles)
        
        logger.info(f"✅ Toplam {len(df)} haber toplandı")
        return df


class NewsSource:
    """Haber kaynağı base sınıfı."""
    
    def __init__(self, name: str):
        self.name = name
    
    def fetch_news(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict]:
        """Haber çeker (alt sınıflar implement eder)."""
        raise NotImplementedError


class NewsAPISource(NewsSource):
    """NewsAPI kaynağı."""
    
    def __init__(self):
        super().__init__("NewsAPI")
        self.api_key = os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch_news(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict]:
        """NewsAPI'den haber çeker."""
        if not self.api_key:
            return []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Arama terimi
        query = company_name
        if ticker:
            ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
            query = f"{query} OR {ticker_clean}"
        
        params = {
            'q': query,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'sortBy': 'publishedAt',
            'pageSize': 100,
            'apiKey': self.api_key
        }
        
        try:
            http_client = get_http_client()
            response = http_client.get(self.base_url, params=params)
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.warning(f"NewsAPI hatası: {data.get('message', 'Bilinmeyen hata')}")
                return []
            
            articles = []
            for item in data.get('articles', []):
                articles.append({
                    'title': item.get('title', ''),
                    'summary': item.get('description', ''),
                    'published_at': item.get('publishedAt', ''),
                    'source': item.get('source', {}).get('name', 'NewsAPI'),
                    'url': item.get('url', ''),
                    'relevance_score': 0.9
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"NewsAPI hatası: {e}")
            return []


class YahooRSSSource(NewsSource):
    """Yahoo Finance RSS kaynağı (ücretsiz, sınırsız)."""
    
    def __init__(self):
        super().__init__("Yahoo Finance RSS")
        self.base_url = "https://feeds.finance.yahoo.com/rss/2.0/headline"
    
    def fetch_news(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict]:
        """Yahoo Finance RSS'den haber çeker."""
        try:
            import feedparser
            
            # Ticker varsa ticker ile, yoksa şirket adı ile
            search_term = ticker.replace('.IS', '').replace('.', '').upper() if ticker else company_name
            
            # Yahoo Finance RSS URL'i
            url = f"{self.base_url}?s={search_term}&region=US&lang=en-US"
            
            feed = feedparser.parse(url)
            
            articles = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for entry in feed.entries:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                    if pub_date < cutoff_date:
                        continue
                    
                    articles.append({
                        'title': entry.title,
                        'summary': entry.get('summary', entry.title),
                        'published_at': pub_date,
                        'source': 'Yahoo Finance',
                        'url': entry.link,
                        'relevance_score': 0.8
                    })
                except:
                    continue
            
            return articles
            
        except Exception as e:
            logger.warning(f"Yahoo RSS hatası: {e}")
            return []


class FMPSource(NewsSource):
    """Financial Modeling Prep API kaynağı."""
    
    def __init__(self):
        super().__init__("Financial Modeling Prep")
        self.api_key = os.getenv('FMP_API_KEY')
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def fetch_news(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict]:
        """FMP API'den haber çeker."""
        if not self.api_key or not ticker:
            return []
        
        ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
        
        try:
            url = f"{self.base_url}/stock_news"
            params = {
                'tickers': ticker_clean,
                'limit': 50,
                'apikey': self.api_key
            }
            
            http_client = get_http_client()
            response = http_client.get(url, params=params)
            data = response.json()
            
            articles = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for item in data:
                try:
                    pub_date = datetime.fromisoformat(item['publishedDate'].replace('Z', '+00:00'))
                    if pub_date < cutoff_date:
                        continue
                    
                    articles.append({
                        'title': item.get('title', ''),
                        'summary': item.get('text', ''),
                        'published_at': pub_date,
                        'source': 'Financial Modeling Prep',
                        'url': item.get('url', ''),
                        'relevance_score': 0.85
                    })
                except:
                    continue
            
            return articles
            
        except Exception as e:
            logger.warning(f"FMP API hatası: {e}")
            return []


class FinnhubSource(NewsSource):
    """Finnhub API kaynağı."""
    
    def __init__(self):
        super().__init__("Finnhub")
        self.api_key = os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
    
    def fetch_news(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict]:
        """Finnhub API'den haber çeker."""
        if not self.api_key or not ticker:
            return []
        
        ticker_clean = ticker.replace('.IS', '').replace('.', '').upper()
        
        try:
            url = f"{self.base_url}/company-news"
            params = {
                'symbol': ticker_clean,
                'from': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d'),
                'token': self.api_key
            }
            
            http_client = get_http_client()
            response = http_client.get(url, params=params)
            data = response.json()
            
            articles = []
            for item in data:
                try:
                    pub_date = datetime.fromtimestamp(item['datetime'])
                    articles.append({
                        'title': item.get('headline', ''),
                        'summary': item.get('summary', ''),
                        'published_at': pub_date,
                        'source': 'Finnhub',
                        'url': item.get('url', ''),
                        'relevance_score': 0.85
                    })
                except:
                    continue
            
            return articles
            
        except Exception as e:
            logger.warning(f"Finnhub API hatası: {e}")
            return []


# Global instance
_news_manager = None


def get_news_from_all_sources(
    company_name: str,
    ticker: Optional[str] = None,
    days_back: int = 30,
    max_articles: int = 50
) -> pd.DataFrame:
    """
    Tüm haber kaynaklarından haber toplar (kolay kullanım için).
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı
    ticker : str, optional
        Borsa kodu
    days_back : int
        Kaç gün geriye gidilecek
    max_articles : int
        Maksimum haber sayısı
    
    Döndürür:
    --------
    pd.DataFrame
        Toplanan haberler
    """
    global _news_manager
    
    if _news_manager is None:
        _news_manager = NewsSourceManager()
    
    return _news_manager.get_news(
        company_name=company_name,
        ticker=ticker,
        days_back=days_back,
        max_articles=max_articles
    )

