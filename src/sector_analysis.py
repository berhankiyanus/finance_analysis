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
    
    if len(sector_tickers) < 2:
        return pd.DataFrame()
    
    try:
        # Projenin standart get_price_data fonksiyonunu kullan
        try:
            from .data_collection import get_price_data
        except ImportError:
            from src.data_collection import get_price_data
        
        # Tüm hisselerin fiyat verilerini çek
        price_data = {}
        for ticker in sector_tickers:
            try:
                # Türk hisseleri için .IS uzantısı ekle (eğer yoksa)
                ticker_formatted = ticker if '.IS' in ticker or ticker.endswith('.IS') else (ticker + '.IS' if len(ticker) == 5 and ticker.isalpha() else ticker)
                
                df = get_price_data(ticker_formatted, period=period)
                if not df.empty and 'close' in df.columns:
                    # Index'i datetime'a çevir (eğer 'date' kolonu varsa)
                    if 'date' in df.columns:
                        df = df.set_index('date')
                        df.index = pd.to_datetime(df.index)
                    elif not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)
                    
                    # Tarihleri normalize et
                    df.index = df.index.normalize()
                    
                    # Close fiyatlarını al
                    price_data[ticker] = df['close']
            except Exception as e:
                print(f"⚠️  {ticker} için veri çekilemedi: {e}")
                continue
        
        if len(price_data) < 2:
            error_msg = f"Yeterli fiyat verisi bulunamadı (sadece {len(price_data)} hisse başarılı: {list(price_data.keys())})"
            print(f"⚠️  {error_msg}")
            # Hata mesajını içeren özel DataFrame döndür
            error_df = pd.DataFrame()
            error_df.attrs = {'error': error_msg}
            return error_df
        
        # Tüm tarihleri birleştir
        all_dates = set()
        for ticker, series in price_data.items():
            all_dates.update(series.index)
            print(f"   {ticker}: {len(series)} gün veri")
        
        if len(all_dates) == 0:
            error_msg = "Hiç tarih bulunamadı"
            print(f"⚠️  {error_msg}")
            error_df = pd.DataFrame()
            error_df.attrs = {'error': error_msg}
            return error_df
        
        # Yeni index oluştur
        new_index = pd.DatetimeIndex(sorted(all_dates))
        print(f"   Toplam {len(new_index)} benzersiz tarih")
        
        # DataFrame oluştur ve reindex et
        price_df = pd.DataFrame(price_data)
        price_df = price_df.reindex(new_index)
        
        # Eksik değerleri forward fill ile doldur
        price_df = price_df.ffill()
        
        # Hala eksik değerleri drop et
        price_df = price_df.dropna()
        
        if len(price_df) < 30:
            error_msg = f"Yeterli ortak veri noktası yok (sadece {len(price_df)} gün, {len(price_data)} hisse)"
            print(f"⚠️  {error_msg}")
            error_df = pd.DataFrame()
            error_df.attrs = {'error': error_msg}
            return error_df
        
        # Getiri hesapla
        returns_df = price_df.pct_change().dropna()
        
        if len(returns_df) < 10:
            error_msg = f"Yeterli getiri verisi yok (sadece {len(returns_df)} gün)"
            print(f"⚠️  {error_msg}")
            error_df = pd.DataFrame()
            error_df.attrs = {'error': error_msg}
            return error_df
        
        # Korelasyon matrisi
        correlation_matrix = returns_df.corr()
        
        if correlation_matrix.empty:
            error_msg = "Korelasyon matrisi boş"
            print(f"⚠️  {error_msg}")
            error_df = pd.DataFrame()
            error_df.attrs = {'error': error_msg}
            return error_df
        
        print(f"✅ Korelasyon matrisi oluşturuldu: {correlation_matrix.shape}")
        return correlation_matrix
        
    except Exception as e:
        print(f"⚠️  Sektör korelasyon analizi hatası: {e}")
        import traceback
        traceback.print_exc()
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
    
    try:
        # Projenin standart get_price_data fonksiyonunu kullan
        try:
            from .data_collection import get_price_data
        except ImportError:
            from src.data_collection import get_price_data
        
        # Türk hisseleri için .IS uzantısı ekle (eğer yoksa)
        ticker1_formatted = ticker1 if '.IS' in ticker1 or ticker1.endswith('.IS') else (ticker1 + '.IS' if len(ticker1) == 5 and ticker1.isalpha() else ticker1)
        ticker2_formatted = ticker2 if '.IS' in ticker2 or ticker2.endswith('.IS') else (ticker2 + '.IS' if len(ticker2) == 5 and ticker2.isalpha() else ticker2)
        
        # Fiyat verilerini çek
        df1 = get_price_data(ticker1_formatted, period=period)
        df2 = get_price_data(ticker2_formatted, period=period)
        
        if df1.empty or df2.empty:
            return {'error': f'Fiyat verisi bulunamadı ({ticker1} veya {ticker2})'}
        
        # Index'i datetime'a çevir (eğer 'date' kolonu varsa)
        if 'date' in df1.columns:
            df1 = df1.set_index('date')
        if 'date' in df2.columns:
            df2 = df2.set_index('date')
        
        # Index'i DatetimeIndex'e çevir ve normalize et (sadece tarih, saat olmadan)
        if not isinstance(df1.index, pd.DatetimeIndex):
            df1.index = pd.to_datetime(df1.index)
        if not isinstance(df2.index, pd.DatetimeIndex):
            df2.index = pd.to_datetime(df2.index)
        
        # Tarihleri normalize et (sadece tarih kısmı)
        df1.index = df1.index.normalize()
        df2.index = df2.index.normalize()
        
        # 'close' kolonunu kontrol et
        if 'close' not in df1.columns:
            return {'error': f'{ticker1} için "close" kolonu bulunamadı. Mevcut kolonlar: {list(df1.columns)}'}
        if 'close' not in df2.columns:
            return {'error': f'{ticker2} için "close" kolonu bulunamadı. Mevcut kolonlar: {list(df2.columns)}'}
        
        # Tarihleri hizala - daha esnek yaklaşım
        # Önce intersection dene
        common_dates = df1.index.intersection(df2.index)
        
        # Eğer intersection yeterli değilse, reindex ile birleştir
        if len(common_dates) < 30:
            # Tüm tarihleri birleştir
            all_dates = df1.index.union(df2.index).sort_values()
            
            # Her iki DataFrame'i aynı index'e göre reindex et
            df1_reindexed = df1.reindex(all_dates)
            df2_reindexed = df2.reindex(all_dates)
            
            # Eksik değerleri forward fill ile doldur
            df1_reindexed = df1_reindexed.ffill()
            df2_reindexed = df2_reindexed.ffill()
            
            # Hala eksik değerleri drop et
            valid_mask = df1_reindexed['close'].notna() & df2_reindexed['close'].notna()
            df1_reindexed = df1_reindexed[valid_mask]
            df2_reindexed = df2_reindexed[valid_mask]
            
            if len(df1_reindexed) < 30:
                return {'error': f'Yeterli ortak veri noktası yok (sadece {len(df1_reindexed)} gün). {ticker1}: {len(df1)} gün, {ticker2}: {len(df2)} gün'}
            
            prices1 = df1_reindexed['close']
            prices2 = df2_reindexed['close']
        else:
            prices1 = df1.loc[common_dates, 'close']
            prices2 = df2.loc[common_dates, 'close']
        
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

