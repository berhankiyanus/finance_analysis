"""
Insider Trading Takibi Modülü

KAP bildirimlerinden "Pay Alım Satım Bildirimi" haberlerini özel olarak ayrıştırır.
Şirket patronunun veya yöneticilerinin kendi hissesini alması
en güçlü "AL" sinyallerinden biridir.
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from src.logger_config import setup_logger

logger = setup_logger(__name__)


def detect_insider_trading(kap_reports: List[Dict]) -> List[Dict]:
    """
    KAP bildirimlerinden insider trading (içeriden öğrenenlerin işlemleri) tespit eder.
    
    Parametreler:
    ------------
    kap_reports : list
        KAP bildirimi listesi (kap_scraper.py'den gelen format)
    
    Döndürür:
    --------
    list
        Insider trading tespit edilen bildirimler
    """
    insider_trades = []
    
    # Insider trading ile ilgili anahtar kelimeler
    insider_keywords = [
        'pay alım', 'pay satım', 'hisse alım', 'hisse satım',
        'hisse senedi alım', 'hisse senedi satım',
        'yönetim kurulu üyesi', 'genel müdür', 'başkan',
        'içeriden öğrenen', 'insider', 'yönetici',
        'kendi payını', 'kendi hissesini', 'kendi paylarını'
    ]
    
    # Alım/satım belirten kelimeler
    buy_keywords = ['alım', 'aldı', 'satın aldı', 'edindi']
    sell_keywords = ['satım', 'sattı', 'sattığı', 'elden çıkardı']
    
    for report in kap_reports:
        title = report.get('title', '').lower()
        report_type = report.get('type', '').lower()
        
        # Başlıkta insider trading belirtisi var mı?
        has_insider_keyword = any(keyword in title for keyword in insider_keywords)
        is_trading_notification = 'alım' in title or 'satım' in title
        
        if has_insider_keyword or is_trading_notification:
            # Alım mı satım mı?
            is_buy = any(keyword in title for keyword in buy_keywords)
            is_sell = any(keyword in title for keyword in sell_keywords)
            
            # Yönetici pozisyonu tespit et
            position = None
            if 'başkan' in title:
                position = 'Başkan'
            elif 'genel müdür' in title:
                position = 'Genel Müdür'
            elif 'yönetim kurulu' in title:
                position = 'Yönetim Kurulu Üyesi'
            
            # Miktar tespit et (basit regex)
            amount_match = re.search(r'(\d+[\.,]?\d*)\s*(pay|hisse|lot|adet)', title)
            amount = None
            if amount_match:
                amount = amount_match.group(1)
            
            insider_trades.append({
                'title': report.get('title', ''),
                'date': report.get('date', ''),
                'link': report.get('link', ''),
                'type': report.get('type', ''),
                'action': 'BUY' if is_buy else 'SELL' if is_sell else 'UNKNOWN',
                'position': position,
                'amount': amount,
                'confidence': 'high' if (has_insider_keyword and (is_buy or is_sell)) else 'medium'
            })
    
    return insider_trades


def analyze_insider_sentiment(insider_trades: List[Dict]) -> Dict:
    """
    Insider trading işlemlerinden genel sentiment çıkarır.
    
    Parametreler:
    ------------
    insider_trades : list
        Insider trading işlemleri
    
    Döndürür:
    --------
    dict
        Insider trading sentiment analizi
    """
    if not insider_trades:
        return {
            'sentiment': 'neutral',
            'score': 0.0,
            'message': 'Insider trading işlemi bulunamadı'
        }
    
    buy_count = sum(1 for trade in insider_trades if trade['action'] == 'BUY')
    sell_count = sum(1 for trade in insider_trades if trade['action'] == 'SELL')
    
    total = len(insider_trades)
    
    # Sentiment hesapla
    if buy_count > sell_count * 2:
        sentiment = 'very_positive'
        score = 0.8
        message = f"Güçlü alım sinyali: {buy_count} alım, {sell_count} satım"
    elif buy_count > sell_count:
        sentiment = 'positive'
        score = 0.6
        message = f"Alım eğilimi: {buy_count} alım, {sell_count} satım"
    elif sell_count > buy_count * 2:
        sentiment = 'very_negative'
        score = -0.8
        message = f"Güçlü satım sinyali: {sell_count} satım, {buy_count} alım"
    elif sell_count > buy_count:
        sentiment = 'negative'
        score = -0.6
        message = f"Satım eğilimi: {sell_count} satım, {buy_count} alım"
    else:
        sentiment = 'neutral'
        score = 0.0
        message = f"Dengeli: {buy_count} alım, {sell_count} satım"
    
    # Yüksek pozisyonlu yöneticilerin işlemleri daha önemli
    high_position_trades = [t for t in insider_trades if t.get('position') in ['Başkan', 'Genel Müdür']]
    if high_position_trades:
        high_buy = sum(1 for t in high_position_trades if t['action'] == 'BUY')
        high_sell = sum(1 for t in high_position_trades if t['action'] == 'SELL')
        
        if high_buy > high_sell:
            score += 0.2  # Yüksek pozisyonlu alım ekstra pozitif
            message += f" (Yüksek pozisyonlu yöneticiler: {high_buy} alım)"
        elif high_sell > high_buy:
            score -= 0.2  # Yüksek pozisyonlu satım ekstra negatif
            message += f" (Yüksek pozisyonlu yöneticiler: {high_sell} satım)"
    
    return {
        'sentiment': sentiment,
        'score': max(-1.0, min(1.0, score)),  # -1 ile 1 arasına sınırla
        'message': message,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'total_trades': total,
        'high_position_trades': len(high_position_trades)
    }


def get_insider_trading_from_kap(ticker: str, limit: int = 20) -> Dict:
    """
    KAP'tan insider trading bildirimlerini çeker ve analiz eder.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    limit : int
        Maksimum bildirim sayısı
    
    Döndürür:
    --------
    dict
        Insider trading analizi
    """
    try:
        from src.kap_scraper import get_kap_financial_reports
        
        # KAP bildirimlerini çek
        kap_reports = get_kap_financial_reports(ticker.replace('.IS', ''), limit=limit)
        
        # Insider trading tespit et
        insider_trades = detect_insider_trading(kap_reports)
        
        # Sentiment analizi
        sentiment = analyze_insider_sentiment(insider_trades)
        
        return {
            'success': True,
            'insider_trades': insider_trades,
            'sentiment': sentiment,
            'ticker': ticker
        }
        
    except Exception as e:
        logger.error(f"Insider trading analizi hatası ({ticker}): {e}")
        return {
            'success': False,
            'error': str(e),
            'insider_trades': [],
            'sentiment': {
                'sentiment': 'neutral',
                'score': 0.0,
                'message': 'Analiz yapılamadı'
            }
        }


if __name__ == "__main__":
    # Test
    print("=== Insider Trading Test ===\n")
    
    test_reports = [
        {
            'title': 'Yönetim Kurulu Başkanı Pay Alım Bildirimi',
            'date': '2024-01-15',
            'link': 'https://www.kap.org.tr/...',
            'type': 'Pay Alım Satım Bildirimi'
        },
        {
            'title': 'Genel Müdür Pay Satım Bildirimi',
            'date': '2024-01-10',
            'link': 'https://www.kap.org.tr/...',
            'type': 'Pay Alım Satım Bildirimi'
        }
    ]
    
    trades = detect_insider_trading(test_reports)
    print(f"Tespit edilen insider trading: {len(trades)}")
    for trade in trades:
        print(f"  - {trade['action']}: {trade['title']}")
    
    sentiment = analyze_insider_sentiment(trades)
    print(f"\nSentiment: {sentiment['sentiment']} (skor: {sentiment['score']:.2f})")
    print(f"Mesaj: {sentiment['message']}")

