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
    
    # Ağırlıklar
    weights = {
        'news': 0.25,
        'forum': 0.20,
        'sentiment': 0.25,
        'volume': 0.15,
        'price': 0.15
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
    
    # Forum postlarını çek (örnek - gerçek uygulamada API kullanılmalı)
    forum_posts = []
    try:
        # Örnek forum URL (gerçek uygulamada değiştirilmeli)
        # forum_url = f"https://www.hisse.net/forum/search?q={ticker}"
        # forum_posts = scrape_forum_posts(forum_url, [ticker, company_name], max_posts=20)
        pass
    except:
        pass
    
    # Sentiment analizi
    if SENTIMENT_AVAILABLE and forum_posts:
        try:
            analyzer = SentimentAnalyzer()
            posts_df = pd.DataFrame(forum_posts)
            posts_with_sentiment = analyze_news_sentiment(posts_df, analyzer)
            
            # Ortalama sentiment
            avg_sentiment = posts_with_sentiment['sentiment_score'].mean() if 'sentiment_score' in posts_with_sentiment.columns else 0.5
            
            # Trend (son 3 gün vs önceki 3 gün)
            if 'date' in posts_with_sentiment.columns and len(posts_with_sentiment) > 5:
                recent_posts = posts_with_sentiment[
                    posts_with_sentiment['date'] >= datetime.now() - timedelta(days=3)
                ]
                older_posts = posts_with_sentiment[
                    (posts_with_sentiment['date'] >= datetime.now() - timedelta(days=6)) &
                    (posts_with_sentiment['date'] < datetime.now() - timedelta(days=3))
                ]
                
                recent_sentiment = recent_posts['sentiment_score'].mean() if not recent_posts.empty else 0.5
                older_sentiment = older_posts['sentiment_score'].mean() if not older_posts.empty else 0.5
                
                trend = "Yükseliş" if recent_sentiment > older_sentiment else "Düşüş" if recent_sentiment < older_sentiment else "Stabil"
            else:
                trend = "Belirsiz"
        except:
            avg_sentiment = 0.5
            trend = "Belirsiz"
    else:
        avg_sentiment = 0.5
        trend = "Belirsiz"
    
    # Hype skoru (basit hesaplama)
    hype_score = calculate_hype_score(
        ticker=ticker,
        news_count=len(forum_posts),
        forum_mentions=len(forum_posts),
        sentiment_score=avg_sentiment
    )
    
    return {
        'ticker': ticker,
        'company_name': company_name,
        'current_sentiment': float(avg_sentiment),
        'trend': trend,
        'hype_score': float(hype_score),
        'forum_mentions': len(forum_posts),
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
    
    results = []
    
    for ticker in tickers:
        try:
            analysis = analyze_social_sentiment_trend(
                ticker=ticker,
                company_name=ticker,
                days_back=days_back
            )
            
            results.append({
                'ticker': ticker,
                'hype_score': analysis['hype_score'],
                'sentiment': analysis['current_sentiment'],
                'trend': analysis['trend'],
                'mentions': analysis['forum_mentions']
            })
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"⚠️  {ticker} analizi hatası: {e}")
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

