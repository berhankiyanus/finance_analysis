#!/usr/bin/env python3
"""
Otomatik Vector DB Populate Scripti

Bu script, geçmiş verileri otomatik olarak toplayıp vector veritabanına ekler.
Cron job veya scheduled task olarak çalıştırılabilir.

Kullanım:
    python3 scripts/auto_populate_vector_db.py --days-back 7
    python3 scripts/auto_populate_vector_db.py --start-date 2024-01-01 --end-date 2024-01-31
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import time

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.vector_memory import HistoricalMemory
from src.data_collection import get_news
from src.political_classifier import classify_news_political_impact
import yfinance as yf
import pandas as pd
from src.logger_config import setup_logger

logger = setup_logger(__name__)


def get_bist100_change(date_str: str, hist_df: pd.DataFrame) -> float:
    """
    Belirli bir tarihteki BIST100 değişimini hesaplar.
    
    Parametreler:
    ------------
    date_str : str
        Tarih (YYYY-MM-DD formatında)
    hist_df : pd.DataFrame
        BIST100 fiyat geçmişi
    
    Döndürür:
    --------
    float
        Yüzde değişim
    """
    try:
        target_date = pd.to_datetime(date_str)
        
        # Tarihi DataFrame'de bul
        if target_date in hist_df.index:
            current_idx = hist_df.index.get_loc(target_date)
            if current_idx > 0:
                prev_idx = current_idx - 1
                prev_price = hist_df.iloc[prev_idx]['Close']
                current_price = hist_df.iloc[current_idx]['Close']
                change = ((current_price - prev_price) / prev_price) * 100
                return change
        
        # Tarih tam olarak bulunamazsa, en yakın tarihi bul
        closest_idx = hist_df.index.get_indexer([target_date], method='nearest')[0]
        if closest_idx > 0:
            prev_idx = closest_idx - 1
            prev_price = hist_df.iloc[prev_idx]['Close']
            current_price = hist_df.iloc[closest_idx]['Close']
            change = ((current_price - prev_price) / prev_price) * 100
            return change
        
        return 0.0
    except Exception as e:
        logger.warning(f"BIST100 değişimi hesaplanırken hata ({date_str}): {e}")
        return 0.0


def populate_single_day(
    memory: HistoricalMemory,
    date_str: str,
    hist_df: pd.DataFrame,
    limit_per_day: int = 5,
    api_key: str = None
) -> int:
    """
    Tek bir gün için haberleri toplayıp vector DB'ye ekler.
    
    Parametreler:
    ------------
    memory : HistoricalMemory
        Vector DB instance'ı
    date_str : str
        Tarih (YYYY-MM-DD)
    hist_df : pd.DataFrame
        BIST100 fiyat geçmişi
    limit_per_day : int
        Maksimum haber sayısı
    api_key : str
        NewsAPI key (opsiyonel)
    
    Döndürür:
    --------
    int
        Eklenen haber sayısı
    """
    try:
        # BIST100 değişimini hesapla
        bist100_change = get_bist100_change(date_str, hist_df)
        
        # Çok küçük değişimleri atla (gürültü)
        if abs(bist100_change) < 0.1:
            return 0
        
        # O günkü haberleri çek
        # Not: get_news fonksiyonu days_back kullanıyor, bu yüzden tarih aralığı belirtmeliyiz
        target_date = pd.to_datetime(date_str)
        days_back = (datetime.now() - target_date).days
        
        if days_back < 0:
            # Gelecek tarih, atla
            return 0
        
        if days_back > 365:
            # Çok eski tarihler için NewsAPI limiti olabilir, Google News RSS kullan
            days_back = 365
        
        # Haberleri çek (Türkiye genel haberler)
        news_df = get_news(
            "Türkiye",
            days_back=min(days_back, 7),  # Son 7 gün içinde ara
            ticker="XU100",
            api_key=api_key
        )
        
        if news_df.empty:
            return 0
        
        # Tarih filtresi: Sadece o günkü haberleri al
        news_df['published_at'] = pd.to_datetime(news_df['published_at'])
        target_date_only = target_date.date()
        day_news = news_df[news_df['published_at'].dt.date == target_date_only]
        
        if day_news.empty:
            return 0
        
        # Siyasi/ekonomik haberleri filtrele ve ekle
        added_count = 0
        for _, row in day_news.iterrows():
            try:
                classification = classify_news_political_impact(
                    news_text=row.get('summary', ''),
                    news_title=row.get('title', '')
                )
                
                category = classification.get('category', 'other')
                political_score = classification.get('political_impact_score', 0.0)
                
                # Sadece siyasi veya yüksek etkili ekonomik haberleri ekle
                if category in ['political', 'economic'] or political_score > 0.5:
                    if memory.add_historical_event(
                        news_text=row.get('summary', ''),
                        news_title=row.get('title', ''),
                        date=date_str,
                        bist100_change=bist100_change,
                        ticker=None,
                        category=category
                    ):
                        added_count += 1
                        
                        if added_count >= limit_per_day:
                            break
                
                # Rate limiting (API limitlerini aşmamak için)
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Haber eklenirken hata: {e}")
                continue
        
        return added_count
        
    except Exception as e:
        logger.error(f"Gün {date_str} işlenirken hata: {e}")
        return 0


def auto_populate(
    start_date: str = None,
    end_date: str = None,
    days_back: int = 7,
    limit_per_day: int = 5,
    api_key: str = None
) -> dict:
    """
    Otomatik olarak geçmiş verileri toplayıp vector DB'ye ekler.
    
    Parametreler:
    ------------
    start_date : str
        Başlangıç tarihi (YYYY-MM-DD). None ise days_back kullanılır.
    end_date : str
        Bitiş tarihi (YYYY-MM-DD). None ise bugün.
    days_back : int
        Kaç gün geriye gidilecek (start_date None ise kullanılır).
    limit_per_day : int
        Her gün için maksimum haber sayısı.
    api_key : str
        NewsAPI key (opsiyonel, env'den de alınabilir).
    
    Döndürür:
    --------
    dict
        İşlem sonuçları
    """
    if api_key is None:
        api_key = os.getenv('NEWS_API_KEY')
    
    # Tarih aralığını belirle
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    logger.info(f"🚀 Otomatik Vector DB Populate Başlatılıyor...")
    logger.info(f"   📅 Tarih Aralığı: {start_date} - {end_date}")
    logger.info(f"   📊 Günlük Limit: {limit_per_day} haber")
    
    # Memory instance'ı oluştur
    memory = HistoricalMemory()
    if not memory.available:
        logger.error("❌ Vektör veritabanı kullanılamıyor.")
        return {
            'success': False,
            'error': 'Vector DB not available',
            'total_added': 0
        }
    
    # BIST100 fiyat verilerini çek
    try:
        logger.info("📈 BIST100 verisi çekiliyor...")
        bist100 = yf.Ticker("XU100.IS")
        hist = bist100.history(period="10y")
        
        if hist.empty:
            logger.error("⚠️  BIST100 verisi çekilemedi.")
            return {
                'success': False,
                'error': 'BIST100 data not available',
                'total_added': 0
            }
        
        logger.info(f"✅ BIST100 verisi çekildi: {len(hist)} gün")
        
    except Exception as e:
        logger.error(f"⚠️  BIST100 verisi çekilemedi: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_added': 0
        }
    
    # Tarih aralığını oluştur
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    total_days = len(date_range)
    
    logger.info(f"📅 {total_days} gün işlenecek...")
    
    # Her gün için haberleri topla ve ekle
    total_added = 0
    success_days = 0
    failed_days = 0
    
    for i, date in enumerate(date_range, 1):
        date_str = date.strftime("%Y-%m-%d")
        
        logger.info(f"[{i}/{total_days}] İşleniyor: {date_str}...")
        
        added = populate_single_day(
            memory=memory,
            date_str=date_str,
            hist_df=hist,
            limit_per_day=limit_per_day,
            api_key=api_key
        )
        
        if added > 0:
            total_added += added
            success_days += 1
            logger.info(f"   ✅ {added} haber eklendi")
        else:
            failed_days += 1
            logger.debug(f"   ⚠️  Haber bulunamadı veya eklenemedi")
        
        # Rate limiting (API limitlerini aşmamak için)
        if i % 10 == 0:
            logger.info(f"   ⏸️  Kısa mola (rate limiting)...")
            time.sleep(2)
    
    # Sonuçları özetle
    logger.info(f"\n✅ İşlem Tamamlandı!")
    logger.info(f"   • Toplam Gün: {total_days}")
    logger.info(f"   • Başarılı Gün: {success_days}")
    logger.info(f"   • Başarısız Gün: {failed_days}")
    logger.info(f"   • Toplam Eklenen Haber: {total_added}")
    logger.info(f"   • Vector DB Toplam Kayıt: {memory.collection.count()}")
    
    return {
        'success': True,
        'total_days': total_days,
        'success_days': success_days,
        'failed_days': failed_days,
        'total_added': total_added,
        'total_records': memory.collection.count()
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Otomatik Vector DB Populate Scripti",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # Son 7 günü ekle
  python3 scripts/auto_populate_vector_db.py --days-back 7
  
  # Belirli tarih aralığını ekle
  python3 scripts/auto_populate_vector_db.py --start-date 2024-01-01 --end-date 2024-01-31
  
  # Günlük limit belirle
  python3 scripts/auto_populate_vector_db.py --days-back 30 --limit-per-day 10
        """
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Başlangıç tarihi (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='Bitiş tarihi (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--days-back',
        type=int,
        default=7,
        help='Kaç gün geriye gidilecek (varsayılan: 7)'
    )
    
    parser.add_argument(
        '--limit-per-day',
        type=int,
        default=5,
        help='Her gün için maksimum haber sayısı (varsayılan: 5)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='NewsAPI key (opsiyonel, env\'den de alınabilir)'
    )
    
    args = parser.parse_args()
    
    # Script'i çalıştır
    result = auto_populate(
        start_date=args.start_date,
        end_date=args.end_date,
        days_back=args.days_back,
        limit_per_day=args.limit_per_day,
        api_key=args.api_key
    )
    
    # Sonuçları yazdır
    if result['success']:
        print(f"\n✅ Başarılı: {result['total_added']} haber eklendi")
        sys.exit(0)
    else:
        print(f"\n❌ Hata: {result.get('error', 'Bilinmeyen hata')}")
        sys.exit(1)

