"""
Cache Manager Modülü

Redis kullanarak sık sorgulanan verileri önbelleğe alır.
Performans artışı sağlar ve API çağrılarını azaltır.
"""

import os
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# .env dosyasını yükle
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Redis import (opsiyonel)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("⚠️  Redis yüklü değil. Cache kullanılamayacak. pip install redis")

# Redis bağlantısı
_redis_client = None


def get_redis_client() -> Optional[Any]:
    """
    Redis client'ı döndürür (singleton pattern).
    
    Döndürür:
    --------
    redis.Redis veya None
        Redis client instance'ı veya None (Redis yoksa)
    """
    global _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Bağlantıyı test et
            _redis_client.ping()
            logger.info("✅ Redis bağlantısı kuruldu")
            
        except Exception as e:
            logger.warning(f"⚠️  Redis bağlantısı kurulamadı: {e}")
            logger.info("   💡 Redis yoksa, cache devre dışı kalacak (sistem normal çalışır)")
            _redis_client = None
    
    return _redis_client


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Cache key oluşturur.
    
    Parametreler:
    ------------
    prefix : str
        Key prefix (örn: "sentiment", "price_data")
    *args, **kwargs
        Key'i oluşturmak için kullanılacak parametreler
    
    Döndürür:
    --------
    str
        Cache key
    """
    # Parametreleri string'e çevir ve hash'le
    key_parts = [prefix]
    
    for arg in args:
        key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")
    
    key_string = "|".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    return f"finance:{prefix}:{key_hash}"


def cache_get(key: str) -> Optional[Any]:
    """
    Cache'den veri okur.
    
    Parametreler:
    ------------
    key : str
        Cache key
    
    Döndürür:
    --------
    Any veya None
        Cache'deki veri veya None (yoksa)
    """
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        cached_data = client.get(key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Cache okuma hatası ({key}): {e}")
    
    return None


def cache_set(key: str, value: Any, ttl: int = 900) -> bool:
    """
    Cache'e veri yazar.
    
    Parametreler:
    ------------
    key : str
        Cache key
    value : Any
        Cache'lenecek veri (JSON serializable olmalı)
    ttl : int
        Time-to-live (saniye cinsinden, varsayılan: 900 = 15 dakika)
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        json_data = json.dumps(value, default=str)  # default=str: datetime gibi tipleri string'e çevir
        client.setex(key, ttl, json_data)
        return True
    except Exception as e:
        logger.warning(f"Cache yazma hatası ({key}): {e}")
        return False


def cache_delete(key: str) -> bool:
    """
    Cache'den veri siler.
    
    Parametreler:
    ------------
    key : str
        Cache key
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache silme hatası ({key}): {e}")
        return False


def cache_clear_pattern(pattern: str) -> int:
    """
    Belirli bir pattern'e uyan tüm cache'leri siler.
    
    Parametreler:
    ------------
    pattern : str
        Redis pattern (örn: "finance:sentiment:*")
    
    Döndürür:
    --------
    int
        Silinen key sayısı
    """
    client = get_redis_client()
    if client is None:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.warning(f"Cache pattern silme hatası ({pattern}): {e}")
        return 0


# Özel cache fonksiyonları (kullanım kolaylığı için)

def get_cached_sentiment(ticker: str, days_back: int = 30) -> Optional[Dict]:
    """
    Sentiment skorunu cache'den okur.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    days_back : int
        Kaç gün geriye gidilecek
    
    Döndürür:
    --------
    dict veya None
        Cache'deki sentiment verisi
    """
    key = _generate_cache_key("sentiment", ticker, days_back=days_back)
    return cache_get(key)


def set_cached_sentiment(ticker: str, sentiment_data: Dict, days_back: int = 30, ttl: int = 900) -> bool:
    """
    Sentiment skorunu cache'e yazar.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    sentiment_data : dict
        Sentiment verisi
    days_back : int
        Kaç gün geriye gidildi
    ttl : int
        Cache süresi (saniye, varsayılan: 900 = 15 dakika)
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    key = _generate_cache_key("sentiment", ticker, days_back=days_back)
    return cache_set(key, sentiment_data, ttl=ttl)


def get_cached_price_data(ticker: str, period: str = "1y") -> Optional[Any]:
    """
    Fiyat verisini cache'den okur.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    period : str
        Veri periyodu
    
    Döndürür:
    --------
    Any veya None
        Cache'deki fiyat verisi
    """
    key = _generate_cache_key("price_data", ticker, period=period)
    return cache_get(key)


def set_cached_price_data(ticker: str, price_data: Any, period: str = "1y", ttl: int = 300) -> bool:
    """
    Fiyat verisini cache'e yazar.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    price_data : Any
        Fiyat verisi (DataFrame serializable olmalı)
    period : str
        Veri periyodu
    ttl : int
        Cache süresi (saniye, varsayılan: 300 = 5 dakika)
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    key = _generate_cache_key("price_data", ticker, period=period)
    
    # DataFrame'i dict'e çevir (JSON serializable yap)
    if hasattr(price_data, 'to_dict'):
        price_data = price_data.to_dict('records')
    
    return cache_set(key, price_data, ttl=ttl)


def get_cached_news(company_name: str, ticker: str, days_back: int = 30) -> Optional[Any]:
    """
    Haber verisini cache'den okur.
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı
    ticker : str
        Hisse kodu
    days_back : int
        Kaç gün geriye gidilecek
    
    Döndürür:
    --------
    Any veya None
        Cache'deki haber verisi
    """
    key = _generate_cache_key("news", company_name, ticker, days_back=days_back)
    return cache_get(key)


def set_cached_news(company_name: str, ticker: str, news_data: Any, days_back: int = 30, ttl: int = 1800) -> bool:
    """
    Haber verisini cache'e yazar.
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı
    ticker : str
        Hisse kodu
    news_data : Any
        Haber verisi
    days_back : int
        Kaç gün geriye gidildi
    ttl : int
        Cache süresi (saniye, varsayılan: 1800 = 30 dakika)
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    key = _generate_cache_key("news", company_name, ticker, days_back=days_back)
    
    # DataFrame'i dict'e çevir
    if hasattr(news_data, 'to_dict'):
        news_data = news_data.to_dict('records')
    
    return cache_set(key, news_data, ttl=ttl)


def get_cached_technical_analysis(ticker: str) -> Optional[Dict]:
    """
    Teknik analiz verisini cache'den okur.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    
    Döndürür:
    --------
    dict veya None
        Cache'deki teknik analiz verisi
    """
    key = _generate_cache_key("technical", ticker)
    return cache_get(key)


def set_cached_technical_analysis(ticker: str, technical_data: Dict, ttl: int = 300) -> bool:
    """
    Teknik analiz verisini cache'e yazar.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    technical_data : dict
        Teknik analiz verisi
    ttl : int
        Cache süresi (saniye, varsayılan: 300 = 5 dakika)
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    key = _generate_cache_key("technical", ticker)
    return cache_set(key, technical_data, ttl=ttl)


# Cache istatistikleri
def get_cache_stats() -> Dict:
    """
    Cache istatistiklerini döndürür.
    
    Döndürür:
    --------
    dict
        Cache istatistikleri
    """
    client = get_redis_client()
    if client is None:
        return {
            'available': False,
            'message': 'Redis not available'
        }
    
    try:
        info = client.info('stats')
        keys = client.keys('finance:*')
        
        return {
            'available': True,
            'total_keys': len(keys),
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100
        }
    except Exception as e:
        logger.warning(f"Cache istatistikleri alınırken hata: {e}")
        return {
            'available': True,
            'error': str(e)
        }


if __name__ == "__main__":
    # Test
    print("=== Cache Manager Test ===\n")
    
    # Redis bağlantısını test et
    client = get_redis_client()
    if client:
        print("✅ Redis bağlantısı başarılı")
        
        # Test verisi yaz
        test_key = "finance:test:key"
        test_data = {"test": "data", "timestamp": "2024-01-01"}
        cache_set(test_key, test_data, ttl=60)
        print(f"✅ Test verisi yazıldı: {test_key}")
        
        # Test verisi oku
        cached = cache_get(test_key)
        if cached:
            print(f"✅ Test verisi okundu: {cached}")
        else:
            print("❌ Test verisi okunamadı")
        
        # Cache istatistikleri
        stats = get_cache_stats()
        print(f"\n📊 Cache İstatistikleri:")
        print(f"   • Toplam Key: {stats.get('total_keys', 0)}")
        print(f"   • Hit Rate: {stats.get('hit_rate', 0):.2f}%")
        
        # Test verisini sil
        cache_delete(test_key)
        print(f"✅ Test verisi silindi")
    else:
        print("⚠️  Redis kullanılamıyor (opsiyonel, sistem normal çalışır)")

