"""
Ülke/Bölge Tespit Modülü

Ticker sembolünden ülke/bölge kodunu tespit eder.
"""

from typing import Optional
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# Ticker uzantılarından ülke/bölge haritası
TICKER_COUNTRY_MAP = {
    # Türkiye
    '.IS': 'TR',
    # İngiltere
    '.L': 'GB',
    '.LN': 'GB',
    # Hong Kong
    '.HK': 'HK',
    # Japonya
    '.T': 'JP',
    # Almanya
    '.DE': 'DE',
    '.F': 'DE',
    # Fransa
    '.PA': 'FR',
    # İsviçre
    '.SW': 'CH',
    '.VX': 'CH',
    # Avustralya
    '.AX': 'AU',
    # Kanada
    '.TO': 'CA',
    '.V': 'CA',
    # Brezilya
    '.SA': 'BR',
    # Güney Kore
    '.KS': 'KR',
    # Hindistan
    '.NS': 'IN',
    '.BO': 'IN',
    # Çin
    '.SS': 'CN',
    '.SZ': 'CN',
    # ABD (varsayılan, uzantı yoksa)
    '': 'US'
}


def detect_country_from_ticker(ticker: str) -> str:
    """
    Ticker sembolünden ülke/bölge kodunu tespit eder.
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu (örn: "AAPL", "THYAO.IS", "VOD.L", "0700.HK")
    
    Döndürür:
    --------
    str
        ISO ülke kodu (örn: "US", "TR", "GB", "HK")
        Bulunamazsa "US" (varsayılan)
    """
    ticker_upper = ticker.upper()
    
    # Uzantıları kontrol et (uzun olandan kısa olana)
    sorted_extensions = sorted(TICKER_COUNTRY_MAP.keys(), key=len, reverse=True)
    
    for ext in sorted_extensions:
        if ext and ticker_upper.endswith(ext):
            country = TICKER_COUNTRY_MAP[ext]
            logger.debug(f"Ticker '{ticker}' → Ülke: {country} (uzantı: {ext})")
            return country
    
    # Uzantı yoksa, uzunluk ve format kontrolü
    # Türk hisseleri: 5 karakter, sadece harf, büyük harf
    if len(ticker) == 5 and ticker.isalpha() and ticker.isupper():
        logger.debug(f"Ticker '{ticker}' → Türk hissesi olabilir (5 karakter, sadece harf)")
        return 'TR'
    
    # Varsayılan: ABD
    logger.debug(f"Ticker '{ticker}' → Varsayılan ülke: US")
    return 'US'


def get_country_name(country_code: str) -> str:
    """
    Ülke kodundan ülke adını döndürür.
    
    Parametreler:
    ------------
    country_code : str
        ISO ülke kodu (örn: "US", "TR", "GB")
    
    Döndürür:
    --------
    str
        Ülke adı (örn: "United States", "Turkey", "United Kingdom")
    """
    country_names = {
        'US': 'United States',
        'TR': 'Turkey',
        'GB': 'United Kingdom',
        'HK': 'Hong Kong',
        'JP': 'Japan',
        'DE': 'Germany',
        'FR': 'France',
        'CH': 'Switzerland',
        'AU': 'Australia',
        'CA': 'Canada',
        'BR': 'Brazil',
        'KR': 'South Korea',
        'IN': 'India',
        'CN': 'China'
    }
    return country_names.get(country_code, country_code)

