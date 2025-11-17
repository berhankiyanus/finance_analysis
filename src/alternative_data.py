"""
Alternatif Veri ve Davranışsal Analiz Modülü

Sosyal medya ve forum analizini derinleştirir. "En çok konuşulan" veya
"duygu değişimi en hızlı olan" hisseleri belirleyen bir "Hype Metre" (Popülerlik Ölçer) oluşturur.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import time
import warnings
warnings.filterwarnings('ignore')

try:
    from src.sentiment_analysis import SentimentAnalyzer, analyze_news_sentiment
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("⚠️  Sentiment analizi modülü yüklü değil.")


def scrape_forum_posts(
    forum_url: str,
    search_keywords: List[str],
    max_posts: int = 50
) -> List[Dict]:
    """
    Forum sitelerinden (örn: "Hisse.net") ilgili postları çeker.
    
    Parametreler:
    ------------
    forum_url : str
        Forum URL'i
    search_keywords : list
        Arama anahtar kelimeleri
    max_posts : int
        Maksimum post sayısı
    
    Döndürür:
    --------
    list
        Her post için dict: {'title', 'content', 'author', 'date', 'url', 'sentiment'}
    """
    
    posts = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(forum_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Forum yapısına göre post'ları bul
        # Not: Gerçek forum yapısı değişebilir, bu genel bir yaklaşım
        post_elements = soup.find_all('div', class_='post') or \
                       soup.find_all('article') or \
                       soup.find_all('tr', class_='topic-row')
        
        for post_elem in post_elements[:max_posts]:
            try:
                # Başlık
                title_elem = post_elem.find('a') or post_elem.find('h3') or post_elem.find('td', class_='title')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                # İçerik
                content_elem = post_elem.find('div', class_='content') or \
                              post_elem.find('p') or \
                              post_elem.find('td', class_='content')
                content = content_elem.get_text(strip=True) if content_elem else ''
                
                # Anahtar kelime kontrolü
                text_combined = f"{title} {content}".lower()
                if not any(keyword.lower() in text_combined for keyword in search_keywords):
                    continue
                
                # Yazar
                author_elem = post_elem.find('span', class_='author') or \
                             post_elem.find('a', class_='author')
                author = author_elem.get_text(strip=True) if author_elem else 'Bilinmiyor'
                
                # Tarih
                date_elem = post_elem.find('time') or post_elem.find('span', class_='date')
                date_str = date_elem.get('datetime') if date_elem and date_elem.get('datetime') else \
                          (date_elem.get_text(strip=True) if date_elem else None)
                
                try:
                    if date_str:
                        date = pd.to_datetime(date_str, errors='coerce')
                    else:
                        date = datetime.now()
                except:
                    date = datetime.now()
                
                # URL
                link_elem = post_elem.find('a', href=True)
                url = link_elem['href'] if link_elem else forum_url
                if url and not url.startswith('http'):
                    url = f"{forum_url.rstrip('/')}/{url.lstrip('/')}"
                
                posts.append({
                    'title': title,
                    'content': content[:500],  # İlk 500 karakter
                    'author': author,
                    'date': date,
                    'url': url,
                    'source': 'forum'
                })
                
            except Exception as e:
                continue
        
        print(f"✅ {len(posts)} forum postu bulundu.")
        return posts[:max_posts]
        
    except Exception as e:
        print(f"⚠️  Forum scraping hatası: {e}")
        return []


def calculate_hype_score(
    ticker: str,
    news_count: int = 0,
    forum_mentions: int = 0,
    sentiment_score: float = 0.5,
    volume_change: float = 0.0,
    price_change: float = 0.0
) -> float:
    """
    Bir hisse için "Hype Metre" (Popülerlik Ölçer) skoru hesaplar.
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu
    news_count : int
        Son dönemdeki haber sayısı
    forum_mentions : int
        Forum'da bahsedilme sayısı
    sentiment_score : float
        Sentiment skoru (0-1 arası)
    volume_change : float
        Hacim değişimi (%)
    price_change : float
        Fiyat değişimi (%)
    
    Döndürür:
    --------
    float
        Hype skoru (0-100 arası)
    """
    
    # Ağırlıklar (fiyat ve hacim değişimine daha fazla ağırlık ver)
    weights = {
        'news': 0.20,
        'forum': 0.15,
        'sentiment': 0.20,
        'volume': 0.25,  # Artırıldı
        'price': 0.20    # Artırıldı
    }
    
    # Haber sayısı skoru (0-100, logaritmik ölçek)
    news_score = min(100, np.log1p(news_count) / np.log(101) * 100)
    
    # Forum bahsedilme skoru
    forum_score = min(100, np.log1p(forum_mentions) / np.log(51) * 100)
    
    # Sentiment skoru (0-1'den 0-100'e)
    sentiment_score_normalized = sentiment_score * 100
    
    # Hacim değişimi skoru (artış pozitif)
    volume_score = max(0, min(100, (volume_change + 50) / 100 * 100))
    
    # Fiyat değişimi skoru (artış pozitif)
    price_score = max(0, min(100, (price_change + 50) / 100 * 100))
    
    # Ağırlıklı ortalama
    hype_score = (
        weights['news'] * news_score +
        weights['forum'] * forum_score +
        weights['sentiment'] * sentiment_score_normalized +
        weights['volume'] * volume_score +
        weights['price'] * price_score
    )
    
    return hype_score


def analyze_social_sentiment_trend(
    ticker: str,
    company_name: str,
    days_back: int = 7
) -> Dict:
    """
    Sosyal medya ve forum'da bir hisse için sentiment trend analizi yapar.
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu
    company_name : str
        Şirket adı
    days_back : int
        Kaç gün geriye gidilecek
    
    Döndürür:
    --------
    dict
        Sentiment trend analizi: {'current_sentiment', 'trend', 'hype_score', 'mentions'}
    """
    
    # Gerçek veri toplama: NewsAPI ve fiyat verileri
    news_count = 0
    avg_sentiment = 0.5
    volume_change = 0.0
    price_change = 0.0
    forum_mentions = 0
    
    # 1. NewsAPI'den haber sayısı ve sentiment
    try:
        from src.data_collection import get_news
        import os
        
        news_df = get_news(
            company_name=company_name,
            days_back=days_back,
            ticker=ticker,
            api_key=os.getenv('NEWS_API_KEY')
        )
        
        if not news_df.empty:
            news_count = len(news_df)
            
            # Sentiment analizi yap
            if SENTIMENT_AVAILABLE:
                try:
                    analyzer = SentimentAnalyzer()
                    news_with_sentiment = analyze_news_sentiment(
                        news_df,
                        analyzer=analyzer,
                        company_name=company_name,
                        ticker=ticker
                    )
                    
                    if 'sentiment_score' in news_with_sentiment.columns:
                        avg_sentiment = news_with_sentiment['sentiment_score'].mean()
                        if pd.isna(avg_sentiment):
                            avg_sentiment = 0.5
                    else:
                        avg_sentiment = 0.5
                except Exception as e:
                    print(f"⚠️  Sentiment analizi hatası: {e}")
                    avg_sentiment = 0.5
    except Exception as e:
        print(f"⚠️  NewsAPI hatası: {e}")
    
    # 2. Fiyat verilerinden hacim ve fiyat değişimi
    try:
        from src.data_collection import get_price_data
        
        # Türk hisseleri için .IS ekle
        ticker_for_yfinance = ticker
        if len(ticker) == 5 and not ticker.endswith('.IS'):
            ticker_for_yfinance = f"{ticker}.IS"
        
        # Fiyat verisi çek (son days_back + 10 gün, karşılaştırma için)
        price_df = get_price_data(ticker_for_yfinance, period=f"{max(days_back + 10, 30)}d")
        
        if not price_df.empty and len(price_df) >= 2:
            # Son gün vs days_back gün önce
            current_price = price_df.iloc[-1]['close']
            current_volume = price_df.iloc[-1]['volume']
            
            # days_back gün önceki veri
            if len(price_df) > days_back:
                past_price = price_df.iloc[-days_back-1]['close']
                past_volume = price_df.iloc[-days_back-1]['volume']
            else:
                past_price = price_df.iloc[0]['close']
                past_volume = price_df.iloc[0]['volume']
            
            # Değişim yüzdesi
            if past_price > 0:
                price_change = ((current_price / past_price) - 1) * 100
            else:
                price_change = 0.0
            
            if past_volume > 0:
                volume_change = ((current_volume / past_volume) - 1) * 100
            else:
                volume_change = 0.0
            
            print(f"   📈 {ticker}: Fiyat değişimi: {price_change:.2f}%, Hacim değişimi: {volume_change:.2f}%")
        else:
            print(f"   ⚠️  {ticker}: Yeterli fiyat verisi yok")
    except Exception as e:
        print(f"⚠️  {ticker} fiyat verisi hatası: {e}")
    
    # 3. Forum postları (opsiyonel - şimdilik atlanıyor)
    # Gerçek forum scraping için API veya özel entegrasyon gerekli
    forum_posts = []
    
    # Trend hesaplama (sentiment'e göre)
    if avg_sentiment > 0.6:
        trend = "Yükseliş"
    elif avg_sentiment < 0.4:
        trend = "Düşüş"
    else:
        trend = "Stabil"
    
    # Hype skoru hesaplama (gerçek verilerle)
    hype_score = calculate_hype_score(
        ticker=ticker,
        news_count=news_count,
        forum_mentions=forum_mentions,
        sentiment_score=avg_sentiment,
        volume_change=volume_change,
        price_change=price_change
    )
    
    return {
        'ticker': ticker,
        'company_name': company_name,
        'current_sentiment': float(avg_sentiment),
        'trend': trend,
        'hype_score': float(hype_score),
        'forum_mentions': forum_mentions,
        'news_count': news_count,
        'interpretation': _interpret_hype_score(hype_score)
    }


def _interpret_hype_score(score: float) -> str:
    """
    Hype skorunu yorumlar.
    """
    if score >= 80:
        return "Çok Yüksek Popülerlik - Dikkatli olun (aşırı alım riski)"
    elif score >= 60:
        return "Yüksek Popülerlik - İlgi çekici"
    elif score >= 40:
        return "Orta Popülerlik - Normal seviye"
    elif score >= 20:
        return "Düşük Popülerlik - Az ilgi"
    else:
        return "Çok Düşük Popülerlik - Neredeyse hiç bahsedilmiyor"


def find_trending_stocks(
    tickers: List[str],
    days_back: int = 7
) -> pd.DataFrame:
    """
    Verilen hisse listesi içinde "trending" (popüler) olanları bulur.
    
    Parametreler:
    ------------
    tickers : list
        Hisse kodları listesi
    days_back : int
        Kaç gün geriye gidilecek
    
    Döndürür:
    --------
    pd.DataFrame
        Trending hisseler: {'ticker', 'hype_score', 'sentiment', 'trend', 'rank'}
    """
    
    # Türk hisseleri için şirket adları mapping
    TURKISH_STOCKS = {
        'THYAO': 'Türk Hava Yolları',
        'EREGL': 'Ereğli Demir Çelik',
        'TUPRS': 'Tüpraş',
        'GARAN': 'Garanti BBVA',
        'AKBNK': 'Akbank',
        'PGSUS': 'Pegasus Hava Yolları',
        'DOAS': 'Doğuş Otomotiv',
        'SASA': 'Sasa Polyester',
        'BIMAS': 'BİM',
        'MIGRS': 'Migros',
        'KOZAL': 'Koza Altın',
        'PETKM': 'Petkim',
        'SAHOL': 'Hacı Ömer Sabancı Holding',
        'KCHOL': 'Koç Holding',
        'ARCLK': 'Arçelik',
        'FROTO': 'Ford Otosan',
        'TOASO': 'Tofaş',
        'ASELS': 'Aselsan',
        'HALKB': 'Halkbank',
        'ISCTR': 'İş Bankası',
        'YKBNK': 'Yapı Kredi',
        'VAKBN': 'Vakıfbank',
        'ENKAI': 'Enka İnşaat',
        'TEKTU': 'Tekfen Holding',
        'CCOLA': 'Coca Cola İçecek'
    }
    
    results = []
    
    for ticker in tickers:
        try:
            # Şirket adını bul
            ticker_clean = ticker.strip().upper()
            company_name = TURKISH_STOCKS.get(ticker_clean, ticker_clean)
            
            print(f"📊 {ticker_clean} ({company_name}) analiz ediliyor...")
            
            analysis = analyze_social_sentiment_trend(
                ticker=ticker_clean,
                company_name=company_name,
                days_back=days_back
            )
            
            results.append({
                'ticker': ticker_clean,
                'hype_score': analysis['hype_score'],
                'sentiment': analysis['current_sentiment'],
                'trend': analysis['trend'],
                'mentions': analysis['forum_mentions'],
                'news_count': analysis.get('news_count', 0)
            })
            
            print(f"   ✅ Hype: {analysis['hype_score']:.2f}, Sentiment: {analysis['current_sentiment']:.2f}, Haber: {analysis.get('news_count', 0)}")
            
            # Rate limiting
            time.sleep(0.3)
            
        except Exception as e:
            print(f"⚠️  {ticker} analizi hatası: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not results:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    df = df.sort_values('hype_score', ascending=False)
    df['rank'] = range(1, len(df) + 1)
    
    return df


if __name__ == "__main__":
    print("=== Alternatif Veri ve Davranışsal Analiz Modülü Test ===\n")
    
    # 1. Hype skoru hesaplama
    print("1. Hype Skoru Hesaplama:")
    hype = calculate_hype_score(
        ticker="THYAO",
        news_count=15,
        forum_mentions=25,
        sentiment_score=0.75,
        volume_change=20.0,
        price_change=5.0
    )
    print(f"   THYAO Hype Skoru: {hype:.2f}/100")
    print()
    
    # 2. Trending hisseler
    print("2. Trending Hisseler:")
    trending = find_trending_stocks(["THYAO", "EREGL", "TUPRS"], days_back=7)
    if not trending.empty:
        print(trending)
    else:
        print("   ⚠️  Trending analizi yapılamadı (forum verisi gerekli)")

