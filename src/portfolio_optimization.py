"""
Portföy Optimizasyonu Modülü

PyPortfolioOpt kütüphanesini kullanarak optimal portföy ağırlıklarını hesaplar.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

try:
    from pypfopt import EfficientFrontier, risk_models, expected_returns
    from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
    PYFOLIO_AVAILABLE = True
except ImportError:
    PYFOLIO_AVAILABLE = False
    print("⚠️  PyPortfolioOpt yüklü değil. Portföy optimizasyonu kullanılamayacak.")


def calculate_optimal_portfolio_weights(
    price_data: pd.DataFrame,
    method: str = 'max_sharpe',
    risk_free_rate: float = 0.02
) -> Dict[str, float]:
    """
    Optimal portföy ağırlıklarını hesaplar.
    
    Parametreler:
    ------------
    price_data : pd.DataFrame
        Her sütun bir hisse, her satır bir tarih. Index datetime olmalı.
        Örnek: price_data['THYAO'], price_data['EREGL'], ...
    method : str
        Optimizasyon yöntemi: 'max_sharpe' (Maksimum Sharpe Oranı) veya 
        'min_volatility' (Minimum Volatilite)
    risk_free_rate : float
        Risksiz faiz oranı (varsayılan: 0.02 = %2)
    
    Döndürür:
    --------
    dict
        Her hisse için ağırlık (0-1 arası, toplamı 1)
    """
    
    if not PYFOLIO_AVAILABLE:
        raise ImportError("PyPortfolioOpt yüklü değil. 'pip install PyPortfolioOpt' komutu ile yükleyin.")
    
    if price_data.empty:
        raise ValueError("Fiyat verisi boş.")
    
    # Tarih index'ini kontrol et
    if not isinstance(price_data.index, pd.DatetimeIndex):
        raise ValueError("price_data index'i DatetimeIndex olmalı.")
    
    # Eksik değerleri temizle
    price_data = price_data.dropna()
    
    if price_data.empty:
        raise ValueError("Fiyat verisi temizlendikten sonra boş kaldı.")
    
    # Beklenen getirileri hesapla
    mu = expected_returns.mean_historical_return(price_data)
    
    # Kovaryans matrisini hesapla
    S = risk_models.sample_cov(price_data)
    
    # Efficient Frontier oluştur
    ef = EfficientFrontier(mu, S)
    
    if method == 'max_sharpe':
        # Maksimum Sharpe Oranı
        weights = ef.max_sharpe(risk_free_rate=risk_free_rate)
        cleaned_weights = ef.clean_weights()
    elif method == 'min_volatility':
        # Minimum Volatilite
        weights = ef.min_volatility()
        cleaned_weights = ef.clean_weights()
    else:
        raise ValueError(f"Bilinmeyen optimizasyon yöntemi: {method}")
    
    # Dict'e çevir (ağırlıkları normalize et)
    weights_dict = {ticker: float(weight) for ticker, weight in cleaned_weights.items()}
    
    return weights_dict


def calculate_portfolio_metrics(
    price_data: pd.DataFrame,
    weights: Dict[str, float],
    risk_free_rate: float = 0.02
) -> Dict[str, float]:
    """
    Portföy metriklerini hesaplar (getiri, volatilite, Sharpe oranı).
    
    Parametreler:
    ------------
    price_data : pd.DataFrame
        Fiyat verisi
    weights : dict
        Her hisse için ağırlık
    risk_free_rate : float
        Risksiz faiz oranı
    
    Döndürür:
    --------
    dict
        Portföy metrikleri
    """
    
    if not PYFOLIO_AVAILABLE:
        raise ImportError("PyPortfolioOpt yüklü değil.")
    
    # Beklenen getiri ve kovaryans
    mu = expected_returns.mean_historical_return(price_data)
    S = risk_models.sample_cov(price_data)
    
    # Portföy getirisi
    portfolio_return = np.sum([weights[ticker] * mu[ticker] for ticker in weights.keys()])
    
    # Portföy volatilitesi
    portfolio_variance = 0
    for ticker1 in weights.keys():
        for ticker2 in weights.keys():
            portfolio_variance += weights[ticker1] * weights[ticker2] * S.loc[ticker1, ticker2]
    portfolio_volatility = np.sqrt(portfolio_variance)
    
    # Sharpe oranı
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
    
    return {
        'expected_return': portfolio_return,
        'volatility': portfolio_volatility,
        'sharpe_ratio': sharpe_ratio
    }


def optimize_bist30_portfolio(
    price_data_dict: Dict[str, pd.DataFrame],
    method: str = 'max_sharpe',
    risk_free_rate: float = 0.02
) -> Dict:
    """
    BIST30 hisselerinin fiyat geçmişini kullanarak optimal portföy hesaplar.
    
    Parametreler:
    ------------
    price_data_dict : dict
        Her ticker için fiyat DataFrame'i
        Örnek: {'THYAO': price_df, 'EREGL': price_df, ...}
    method : str
        Optimizasyon yöntemi: 'max_sharpe' veya 'min_volatility'
    risk_free_rate : float
        Risksiz faiz oranı
    
    Döndürür:
    --------
    dict
        {
            'weights': {ticker: weight},
            'metrics': {expected_return, volatility, sharpe_ratio},
            'max_sharpe_weights': {...},  # Maksimum Sharpe için
            'min_vol_weights': {...}      # Minimum Volatilite için
        }
    """
    
    if not PYFOLIO_AVAILABLE:
        raise ImportError("PyPortfolioOpt yüklü değil.")
    
    # Tüm ticker'ların fiyat verilerini birleştir
    # Ortak tarihleri bul
    all_dates = None
    for ticker, df in price_data_dict.items():
        if all_dates is None:
            all_dates = set(df.index)
        else:
            all_dates = all_dates.intersection(set(df.index))
    
    if not all_dates:
        raise ValueError("Ortak tarih bulunamadı.")
    
    # Ortak tarihlerdeki fiyatları birleştir
    combined_data = pd.DataFrame(index=sorted(all_dates))
    
    for ticker, df in price_data_dict.items():
        # 'close' kolonunu kullan
        if 'close' in df.columns:
            combined_data[ticker] = df.loc[combined_data.index, 'close']
        else:
            # Eğer 'close' yoksa, ilk kolonu kullan
            combined_data[ticker] = df.loc[combined_data.index, df.columns[0]]
    
    # Eksik değerleri temizle
    combined_data = combined_data.dropna()
    
    if combined_data.empty:
        raise ValueError("Birleştirilmiş veri boş.")
    
    # Her iki yöntem için de hesapla
    max_sharpe_weights = calculate_optimal_portfolio_weights(
        combined_data, method='max_sharpe', risk_free_rate=risk_free_rate
    )
    
    min_vol_weights = calculate_optimal_portfolio_weights(
        combined_data, method='min_volatility', risk_free_rate=risk_free_rate
    )
    
    # Seçilen yöntem için metrikleri hesapla
    if method == 'max_sharpe':
        selected_weights = max_sharpe_weights
    else:
        selected_weights = min_vol_weights
    
    metrics = calculate_portfolio_metrics(combined_data, selected_weights, risk_free_rate)
    
    return {
        'weights': selected_weights,
        'metrics': metrics,
        'max_sharpe_weights': max_sharpe_weights,
        'min_vol_weights': min_vol_weights,
        'max_sharpe_metrics': calculate_portfolio_metrics(combined_data, max_sharpe_weights, risk_free_rate),
        'min_vol_metrics': calculate_portfolio_metrics(combined_data, min_vol_weights, risk_free_rate)
    }


if __name__ == "__main__":
    print("=== Portföy Optimizasyonu Modülü Test ===\n")
    
    if not PYFOLIO_AVAILABLE:
        print("⚠️  PyPortfolioOpt yüklü değil.")
        print("   Yüklemek için: pip install PyPortfolioOpt")
    else:
        # Test verisi oluştur
        dates = pd.date_range(start='2020-01-01', periods=252, freq='D')
        
        # 3 hisse için dummy fiyat verisi
        np.random.seed(42)
        price_data = pd.DataFrame({
            'THYAO': 100 + np.cumsum(np.random.randn(252) * 2),
            'EREGL': 50 + np.cumsum(np.random.randn(252) * 1.5),
            'TUPRS': 200 + np.cumsum(np.random.randn(252) * 3)
        }, index=dates)
        
        print("1. Maksimum Sharpe Oranı Portföyü:")
        max_sharpe_weights = calculate_optimal_portfolio_weights(price_data, method='max_sharpe')
        print(f"   Ağırlıklar: {max_sharpe_weights}")
        max_sharpe_metrics = calculate_portfolio_metrics(price_data, max_sharpe_weights)
        print(f"   Metrikler: {max_sharpe_metrics}")
        
        print("\n2. Minimum Volatilite Portföyü:")
        min_vol_weights = calculate_optimal_portfolio_weights(price_data, method='min_volatility')
        print(f"   Ağırlıklar: {min_vol_weights}")
        min_vol_metrics = calculate_portfolio_metrics(price_data, min_vol_weights)
        print(f"   Metrikler: {min_vol_metrics}")
        
        print("\n3. BIST30 Portföy Optimizasyonu:")
        price_data_dict = {
            'THYAO': pd.DataFrame({'close': price_data['THYAO']}, index=dates),
            'EREGL': pd.DataFrame({'close': price_data['EREGL']}, index=dates),
            'TUPRS': pd.DataFrame({'close': price_data['TUPRS']}, index=dates)
        }
        result = optimize_bist30_portfolio(price_data_dict, method='max_sharpe')
        print(f"   Seçilen Ağırlıklar: {result['weights']}")
        print(f"   Metrikler: {result['metrics']}")

