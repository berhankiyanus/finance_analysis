"""
Rakip Analizi Modülü

Seçilen hissenin otomatik olarak en büyük rakibini bulur
ve ikisinin rasyolarını, sentimentlerini yan yana karşılaştırır.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from src.logger_config import setup_logger

logger = setup_logger(__name__)


# Sektör bazlı rakip eşleştirmeleri (Türkiye BIST için)
BIST_COMPETITORS = {
    'THYAO': ['PGSUS', 'TAVHL'],  # Havacılık
    'GARAN': ['AKBNK', 'ISCTR', 'YKBNK'],  # Bankacılık
    'AKBNK': ['GARAN', 'ISCTR', 'YKBNK'],  # Bankacılık
    'ISCTR': ['GARAN', 'AKBNK', 'YKBNK'],  # Bankacılık
    'TUPRS': ['PETKM', 'AYGAZ'],  # Petrol
    'EREGL': ['KRDMD', 'CEMTS'],  # Demir-Çelik
    'SASA': ['KLKIM', 'YUNSA'],  # Tekstil
    'BIMAS': ['MIGRS', 'SOKM'],  # Perakende
    'MIGRS': ['BIMAS', 'SOKM'],  # Perakende
    'SOKM': ['BIMAS', 'MIGRS'],  # Perakende
    'KCHOL': ['TOASO', 'FROTO'],  # Otomotiv
    'TOASO': ['KCHOL', 'FROTO'],  # Otomotiv
    'FROTO': ['KCHOL', 'TOASO'],  # Otomotiv
    'ARCLK': ['VESTEL', 'BFREN'],  # Beyaz Eşya
    'VESTEL': ['ARCLK', 'BFREN'],  # Beyaz Eşya
}

# Sektör bilgileri (yfinance'den alınabilir)
SECTOR_MAPPING = {
    'THYAO': 'Havacılık',
    'PGSUS': 'Havacılık',
    'TAVHL': 'Havacılık',
    'GARAN': 'Bankacılık',
    'AKBNK': 'Bankacılık',
    'ISCTR': 'Bankacılık',
    'YKBNK': 'Bankacılık',
    'TUPRS': 'Petrol',
    'PETKM': 'Petrol',
    'EREGL': 'Demir-Çelik',
    'KRDMD': 'Demir-Çelik',
}


def find_competitor(ticker: str) -> Optional[str]:
    """
    Bir hisse için en büyük rakibini bulur.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    
    Döndürür:
    --------
    str veya None
        Rakip hisse kodu
    """
    # .IS uzantısını temizle
    ticker_clean = ticker.replace('.IS', '').upper()
    
    # Önce BIST_COMPETITORS'tan bak
    if ticker_clean in BIST_COMPETITORS:
        competitors = BIST_COMPETITORS[ticker_clean]
        # İlk rakibi döndür (en büyük rakip)
        return competitors[0] if competitors else None
    
    # Sektör bazlı eşleştirme
    sector = SECTOR_MAPPING.get(ticker_clean)
    if sector:
        # Aynı sektördeki diğer hisseleri bul
        sector_tickers = [t for t, s in SECTOR_MAPPING.items() if s == sector and t != ticker_clean]
        if sector_tickers:
            return sector_tickers[0]
    
    # yfinance'den sektör bilgisi çek (fallback)
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        
        sector = info.get('sector')
        industry = info.get('industry')
        
        if sector or industry:
            logger.info(f"{ticker} sektörü: {sector}, endüstri: {industry}")
            # Burada daha gelişmiş bir rakip bulma algoritması olabilir
            # Şimdilik None döndür
            return None
            
    except Exception as e:
        logger.warning(f"Rakip bulunamadı ({ticker}): {e}")
        return None
    
    return None


def compare_companies(
    ticker1: str,
    ticker2: str,
    company_name1: str,
    company_name2: str,
    analysis_results1: Dict,
    analysis_results2: Optional[Dict] = None
) -> Dict:
    """
    İki şirketi head-to-head karşılaştırır.
    
    Parametreler:
    ------------
    ticker1 : str
        İlk hisse kodu
    ticker2 : str
        İkinci hisse kodu (rakip)
    company_name1 : str
        İlk şirket adı
    company_name2 : str
        İkinci şirket adı
    analysis_results1 : dict
        İlk şirket analiz sonuçları
    analysis_results2 : dict
        İkinci şirket analiz sonuçları (opsiyonel, yoksa çekilir)
    
    Döndürür:
    --------
    dict
        Karşılaştırma sonuçları
    """
    # İkinci şirket analizi yoksa çek
    if analysis_results2 is None:
        try:
            from src.main import analyze_company
            analysis_results2 = analyze_company(
                company_name=company_name2,
                ticker=ticker2,
                days_back=30
            )
        except Exception as e:
            logger.error(f"Rakip analizi çekilemedi ({ticker2}): {e}")
            return {
                'success': False,
                'error': f'Rakip analizi çekilemedi: {str(e)}'
            }
    
    # Skorları karşılaştır
    comparison = {
        'success': True,
        'company1': {
            'ticker': ticker1,
            'name': company_name1,
            'overall_score': analysis_results1.get('overall_score', 0),
            'sentiment_score': analysis_results1.get('sentiment_score', 0),
            'financial_score': analysis_results1.get('financial_score', 0),
            'direction': analysis_results1.get('direction_prediction', {}).get('direction', 'HOLD'),
            'confidence': analysis_results1.get('direction_prediction', {}).get('confidence', 0.5)
        },
        'company2': {
            'ticker': ticker2,
            'name': company_name2,
            'overall_score': analysis_results2.get('overall_score', 0),
            'sentiment_score': analysis_results2.get('sentiment_score', 0),
            'financial_score': analysis_results2.get('financial_score', 0),
            'direction': analysis_results2.get('direction_prediction', {}).get('direction', 'HOLD'),
            'confidence': analysis_results2.get('direction_prediction', {}).get('confidence', 0.5)
        },
        'winner': None,
        'comparison_summary': ''
    }
    
    # Kazananı belirle
    score1 = comparison['company1']['overall_score']
    score2 = comparison['company2']['overall_score']
    
    if score1 > score2 + 5:  # 5 puan fark varsa
        comparison['winner'] = ticker1
        comparison['comparison_summary'] = f"{company_name1} ({ticker1}) daha yüksek skora sahip ({score1:.1f} vs {score2:.1f})"
    elif score2 > score1 + 5:
        comparison['winner'] = ticker2
        comparison['comparison_summary'] = f"{company_name2} ({ticker2}) daha yüksek skora sahip ({score2:.1f} vs {score1:.1f})"
    else:
        comparison['winner'] = 'TIE'
        comparison['comparison_summary'] = f"İki şirket de benzer skorlara sahip ({score1:.1f} vs {score2:.1f})"
    
    # Fiyat karşılaştırması
    try:
        from src.data_collection import get_price_data
        
        price1 = get_price_data(ticker1, period="1mo")
        price2 = get_price_data(ticker2, period="1mo")
        
        if not price1.empty and not price2.empty:
            current_price1 = price1.iloc[-1]['close']
            current_price2 = price2.iloc[-1]['close']
            
            change1 = ((current_price1 - price1.iloc[0]['close']) / price1.iloc[0]['close']) * 100
            change2 = ((current_price2 - price2.iloc[0]['close']) / price2.iloc[0]['close']) * 100
            
            comparison['company1']['current_price'] = float(current_price1)
            comparison['company1']['price_change_1mo'] = float(change1)
            comparison['company2']['current_price'] = float(current_price2)
            comparison['company2']['price_change_1mo'] = float(change2)
            
    except Exception as e:
        logger.warning(f"Fiyat karşılaştırması yapılamadı: {e}")
    
    return comparison


if __name__ == "__main__":
    # Test
    print("=== Rakip Analizi Test ===\n")
    
    # THYAO için rakip bul
    competitor = find_competitor("THYAO")
    print(f"THYAO'nun rakibi: {competitor}")
    
    if competitor:
        print(f"\nKarşılaştırma yapılıyor...")
        # Burada gerçek analiz sonuçları gerekir, test için atlanıyor

