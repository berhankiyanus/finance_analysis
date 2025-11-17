"""
Sektörel Analiz ve Korelasyon Modülü

Hisseler arası (örn: THYAO vs PGSUS) ve hisse-emtia (örn: EREGL vs. Demir Cevheri Fiyatları)
korelasyonlarını analiz eder. Hangi sektörün "ucuz" veya "pahalı" kaldığını gösteren
bir "Sektör Rotasyonu" aracı geliştirir.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance yüklü değil. Sektörel analiz kullanılamayacak.")


# Türkiye BIST sektör tanımlamaları
BIST_SECTORS = {
    'Teknoloji': ['THYAO', 'LOGO', 'NETAS'],
    'Finans': ['GARAN', 'AKBNK', 'ISCTR', 'YKBNK', 'HALKB'],
    'Sanayi': ['EREGL', 'TUPRS', 'SASA', 'PETKM'],
    'Enerji': ['TUPRS', 'PETKM', 'AEFES'],
    'İnşaat': ['ENKAI', 'GOLTS', 'IZINV'],
    'Gıda': ['ULKER', 'PENGD', 'BANVT'],
    'Perakende': ['MIGRS', 'BIMAS', 'SOKM'],
    'Ulaştırma': ['THYAO', 'PGSUS', 'DOAS']
}

# ABD sektör tanımlamaları
US_SECTORS = {
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA'],
    'Financials': ['JPM', 'BAC', 'WFC', 'GS', 'MS'],
    'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABT', 'MRK'],
    'Consumer Discretionary': ['AMZN', 'TSLA', 'NKE', 'HD', 'MCD'],
    'Energy': ['XOM', 'CVX', 'SLB', 'COP', 'EOG'],
    'Industrials': ['BA', 'CAT', 'GE', 'HON', 'UPS']
}


def calculate_correlation(
    ticker1: str,
    ticker2: str,
    period: str = "1y",
    method: str = "pearson"
) -> Dict:
    """
    İki hisse arasındaki korelasyonu hesaplar.
    
    Parametreler:
    ------------
    ticker1 : str
        İlk hisse kodu
    ticker2 : str
        İkinci hisse kodu
    period : str
        Veri periyodu (varsayılan: "1y")
    method : str
        Korelasyon yöntemi: 'pearson', 'spearman', 'kendall'
    
    Döndürür:
    --------
    dict
        Korelasyon sonuçları: {'correlation', 'p_value', 'period', 'data_points'}
    """
    
    if not YFINANCE_AVAILABLE:
        return {'error': 'yfinance yüklü değil'}
    
    try:
        # Fiyat verilerini çek
        stock1 = yf.Ticker(ticker1)
        stock2 = yf.Ticker(ticker2)
        
        hist1 = stock1.history(period=period)
        hist2 = stock2.history(period=period)
        
        if hist1.empty or hist2.empty:
            return {'error': 'Fiyat verisi bulunamadı'}
        
        # Kapanış fiyatlarını al
        prices1 = hist1['Close']
        prices2 = hist2['Close']
        
        # Tarihleri hizala
        common_dates = prices1.index.intersection(prices2.index)
        if len(common_dates) < 30:
            return {'error': 'Yeterli ortak veri noktası yok'}
        
        prices1_aligned = prices1.loc[common_dates]
        prices2_aligned = prices2.loc[common_dates]
        
        # Getiri hesapla (günlük)
        returns1 = prices1_aligned.pct_change().dropna()
        returns2 = prices2_aligned.pct_change().dropna()
        
        # Tarihleri tekrar hizala
        common_returns = returns1.index.intersection(returns2.index)
        returns1 = returns1.loc[common_returns]
        returns2 = returns2.loc[common_returns]
        
        if len(returns1) < 20:
            return {'error': 'Yeterli getiri verisi yok'}
        
        # Korelasyon hesapla
        if method == 'pearson':
            correlation = returns1.corr(returns2)
        elif method == 'spearman':
            correlation = returns1.corr(returns2, method='spearman')
        else:
            correlation = returns1.corr(returns2, method='kendall')
        
        # P-value hesapla (basit yaklaşım)
        from scipy.stats import pearsonr
        try:
            corr_coef, p_value = pearsonr(returns1, returns2)
        except:
            p_value = None
        
        return {
            'ticker1': ticker1,
            'ticker2': ticker2,
            'correlation': float(correlation),
            'p_value': float(p_value) if p_value else None,
            'period': period,
            'data_points': len(returns1),
            'method': method,
            'interpretation': _interpret_correlation(correlation)
        }
        
    except Exception as e:
        return {'error': str(e)}


def _interpret_correlation(corr: float) -> str:
    """
    Korelasyon değerini yorumlar.
    """
    abs_corr = abs(corr)
    
    if abs_corr >= 0.7:
        strength = "Güçlü"
    elif abs_corr >= 0.4:
        strength = "Orta"
    elif abs_corr >= 0.2:
        strength = "Zayıf"
    else:
        strength = "Çok Zayıf"
    
    direction = "pozitif" if corr > 0 else "negatif"
    
    return f"{strength} {direction} korelasyon"


def analyze_sector_correlation(
    sector_tickers: List[str],
    period: str = "1y"
) -> pd.DataFrame:
    """
    Bir sektör içindeki hisseler arası korelasyon matrisini hesaplar.
    
    Parametreler:
    ------------
    sector_tickers : list
        Sektör içindeki hisse kodları
    period : str
        Veri periyodu
    
    Döndürür:
    --------
    pd.DataFrame
        Korelasyon matrisi
    """
    
    if not YFINANCE_AVAILABLE:
        return pd.DataFrame()
    
    if len(sector_tickers) < 2:
        return pd.DataFrame()
    
    try:
        # Tüm hisselerin fiyat verilerini çek
        price_data = {}
        for ticker in sector_tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                if not hist.empty:
                    price_data[ticker] = hist['Close']
            except:
                continue
        
        if len(price_data) < 2:
            return pd.DataFrame()
        
        # DataFrame oluştur
        price_df = pd.DataFrame(price_data)
        
        # Getiri hesapla
        returns_df = price_df.pct_change().dropna()
        
        # Korelasyon matrisi
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
        
    except Exception as e:
        print(f"⚠️  Sektör korelasyon analizi hatası: {e}")
        return pd.DataFrame()


def calculate_sector_rotation(
    sectors: Dict[str, List[str]],
    period: str = "3mo",
    country: str = "TR"
) -> Dict[str, float]:
    """
    Sektör rotasyonu analizi - hangi sektörler "ucuz" veya "pahalı" kaldı.
    
    Parametreler:
    ------------
    sectors : dict
        Sektör adı -> hisse listesi mapping'i
    period : str
        Analiz periyodu (varsayılan: "3mo")
    country : str
        Ülke kodu: "TR" veya "US"
    
    Döndürür:
    --------
    dict
        Her sektör için performans skoru (0-100)
    """
    
    if not YFINANCE_AVAILABLE:
        return {}
    
    sector_performance = {}
    
    for sector_name, tickers in sectors.items():
        try:
            # Sektör içindeki hisselerin performansını hesapla
            performances = []
            
            for ticker in tickers[:5]:  # İlk 5 hisse
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period=period)
                    
                    if not hist.empty and len(hist) > 10:
                        # Dönem başı ve sonu fiyatları
                        start_price = hist['Close'].iloc[0]
                        end_price = hist['Close'].iloc[-1]
                        
                        # Getiri
                        return_pct = (end_price / start_price - 1) * 100
                        performances.append(return_pct)
                except:
                    continue
            
            if performances:
                # Sektör ortalama performansı
                avg_performance = np.mean(performances)
                
                # 0-100 arası normalize et (basit yaklaşım)
                # -20% -> 0, +20% -> 100
                normalized_score = max(0, min(100, (avg_performance + 20) / 40 * 100))
                
                sector_performance[sector_name] = {
                    'avg_return': avg_performance,
                    'score': normalized_score,
                    'tickers_analyzed': len(performances)
                }
        except Exception as e:
            print(f"⚠️  {sector_name} sektörü analizi hatası: {e}")
            continue
    
    return sector_performance


def find_arbitrage_opportunities(
    ticker1: str,
    ticker2: str,
    period: str = "1y",
    threshold: float = 0.3
) -> Dict:
    """
    İki hisse arasında arbitraj fırsatları arar (spread analizi).
    
    Parametreler:
    ------------
    ticker1 : str
        İlk hisse kodu
    ticker2 : str
        İkinci hisse kodu
    period : str
        Veri periyodu
    threshold : float
        Spread eşiği (varsayılan: 0.3 = %30)
    
    Döndürür:
    --------
    dict
        Arbitraj fırsatları analizi
    """
    
    if not YFINANCE_AVAILABLE:
        return {'error': 'yfinance yüklü değil'}
    
    try:
        # Fiyat verilerini çek
        stock1 = yf.Ticker(ticker1)
        stock2 = yf.Ticker(ticker2)
        
        hist1 = stock1.history(period=period)
        hist2 = stock2.history(period=period)
        
        if hist1.empty or hist2.empty:
            return {'error': 'Fiyat verisi bulunamadı'}
        
        # Tarihleri hizala
        common_dates = hist1.index.intersection(hist2.index)
        if len(common_dates) < 30:
            return {'error': 'Yeterli ortak veri noktası yok'}
        
        prices1 = hist1.loc[common_dates, 'Close']
        prices2 = hist2.loc[common_dates, 'Close']
        
        # Fiyat oranı (spread)
        ratio = prices1 / prices2
        
        # Spread istatistikleri
        mean_ratio = ratio.mean()
        std_ratio = ratio.std()
        current_ratio = ratio.iloc[-1]
        
        # Z-score (mevcut spread'in ortalamadan ne kadar sapma gösterdiği)
        z_score = (current_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0
        
        # Arbitraj sinyali
        opportunity = None
        if abs(z_score) > threshold:
            if z_score > threshold:
                opportunity = f"{ticker1} {ticker2}'ye göre pahalı görünüyor (satım fırsatı)"
            else:
                opportunity = f"{ticker1} {ticker2}'ye göre ucuz görünüyor (alım fırsatı)"
        
        return {
            'ticker1': ticker1,
            'ticker2': ticker2,
            'current_ratio': float(current_ratio),
            'mean_ratio': float(mean_ratio),
            'std_ratio': float(std_ratio),
            'z_score': float(z_score),
            'opportunity': opportunity,
            'data_points': len(ratio)
        }
        
    except Exception as e:
        return {'error': str(e)}


def analyze_commodity_correlation(
    ticker: str,
    commodity_symbol: str,
    period: str = "1y"
) -> Dict:
    """
    Hisse-emtia korelasyonunu analiz eder (örn: EREGL vs. Demir Cevheri).
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    commodity_symbol : str
        Emtia sembolü (yfinance formatında, örn: "CL=F" = Crude Oil, "GC=F" = Gold)
    period : str
        Veri periyodu
    
    Döndürür:
    --------
    dict
        Hisse-emtia korelasyon sonuçları
    """
    
    return calculate_correlation(ticker, commodity_symbol, period=period)


if __name__ == "__main__":
    print("=== Sektörel Analiz ve Korelasyon Modülü Test ===\n")
    
    if not YFINANCE_AVAILABLE:
        print("❌ yfinance yüklü değil. Testler atlanıyor.")
    else:
        # 1. İki hisse arası korelasyon
        print("1. İki Hisse Arası Korelasyon:")
        corr_result = calculate_correlation("THYAO", "PGSUS", period="6mo")
        print(corr_result)
        print()
        
        # 2. Sektör korelasyon matrisi
        print("2. Finans Sektörü Korelasyon Matrisi:")
        fin_corr = analyze_sector_correlation(BIST_SECTORS['Finans'], period="6mo")
        if not fin_corr.empty:
            print(fin_corr)
        print()
        
        # 3. Sektör rotasyonu
        print("3. BIST Sektör Rotasyonu (Son 3 Ay):")
        rotation = calculate_sector_rotation(BIST_SECTORS, period="3mo", country="TR")
        for sector, data in rotation.items():
            print(f"   {sector}: {data['avg_return']:.2f}% (Skor: {data['score']:.1f}/100)")
        print()
        
        # 4. Arbitraj fırsatları
        print("4. Arbitraj Fırsatları Analizi:")
        arb_result = find_arbitrage_opportunities("THYAO", "PGSUS", period="6mo")
        print(arb_result)

