"""
Finansal Analiz Modülü

Bu modül, fiyat verilerinden feature'lar çıkarır ve finansal skor hesaplar.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    RSI (Relative Strength Index) hesaplar.
    
    Parametreler:
    ------------
    prices : pd.Series
        Fiyat serisi (genelde 'close')
    period : int
        RSI periyodu (varsayılan: 14)
    
    Döndürür:
    --------
    pd.Series
        RSI değerleri (0-100 arası)
    """
    delta = prices.diff()
    
    # Kazanç ve kayıpları ayır
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # RS (Relative Strength) hesapla
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence) hesaplar.
    
    Parametreler:
    ------------
    prices : pd.Series
        Fiyat serisi
    fast : int
        Hızlı EMA periyodu
    slow : int
        Yavaş EMA periyodu
    signal : int
        Sinyal çizgisi periyodu
    
    Döndürür:
    --------
    dict
        'macd', 'signal', 'histogram' serileri
    """
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_histogram = macd - macd_signal
    
    return {
        'macd': macd,
        'signal': macd_signal,
        'histogram': macd_histogram
    }


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_mult: float = 2.0) -> Dict[str, pd.Series]:
    """
    Bollinger Bands hesaplar.
    
    Parametreler:
    ------------
    prices : pd.Series
        Fiyat serisi
    period : int
        Hareketli ortalama periyodu
    std_mult : float
        Standart sapma çarpanı
    
    Döndürür:
    --------
    dict
        'upper', 'middle', 'lower' serileri
    """
    middle = prices.rolling(period).mean()
    std = prices.rolling(period).std()
    
    upper = middle + (std * std_mult)
    lower = middle - (std * std_mult)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def compute_features(price_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fiyat verisinden feature'lar üretir.
    
    Parametreler:
    ------------
    price_df : pd.DataFrame
        'date', 'open', 'high', 'low', 'close', 'volume' kolonları olmalı
    
    Döndürür:
    --------
    pd.DataFrame
        Orijinal DataFrame + feature kolonları
    """
    
    df = price_df.copy()
    
    # Günlük getiri
    df['daily_return'] = df['close'].pct_change()
    
    # Son X günlük kümülatif getiri
    for period in [5, 10, 20, 30]:
        df[f'return_{period}d'] = df['close'].pct_change(period)
    
    # Volatilite (standart sapma)
    for period in [5, 10, 20, 30]:
        df[f'volatility_{period}d'] = df['daily_return'].rolling(period).std()
    
    # Basit hareketli ortalamalar
    for period in [5, 10, 20, 50, 200]:
        df[f'ma_{period}'] = df['close'].rolling(period).mean()
    
    # Üssel hareketli ortalamalar (EMA)
    for period in [12, 26]:
        df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
    
    # RSI
    df['rsi_14'] = calculate_rsi(df['close'], period=14)
    
    # MACD
    macd_data = calculate_macd(df['close'])
    df['macd'] = macd_data['macd']
    df['macd_signal'] = macd_data['signal']
    df['macd_histogram'] = macd_data['histogram']
    
    # Bollinger Bands
    bb_data = calculate_bollinger_bands(df['close'])
    df['bb_upper'] = bb_data['upper']
    df['bb_middle'] = bb_data['middle']
    df['bb_lower'] = bb_data['lower']
    
    # Fiyatın MA'lara göre konumu (yüzde fark)
    for period in [10, 20, 50]:
        df[f'price_vs_ma{period}'] = (df['close'] / df[f'ma_{period}'] - 1) * 100
    
    # Hacim ortalaması
    df['volume_ma_20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma_20']
    
    return df


def normalize_financial_metrics(fundamentals: Dict) -> Dict:
    """
    Finansal göstergeleri 0-100 arası skora çevirir.
    
    Parametreler:
    ------------
    fundamentals : dict
        Finansal göstergeler (P/E, gelir büyümesi, kâr marjı vb.)
    
    Döndürür:
    --------
    dict
        'individual_scores': Her gösterge için skor
        'overall_score': Genel finansal skor (0-100)
    """
    
    scores = {}
    
    # P/E oranı: Düşük P/E genelde iyi (tersine çevir)
    if 'pe_ratio' in fundamentals and fundamentals['pe_ratio'] is not None:
        pe = fundamentals['pe_ratio']
        if pe > 0:
            # P/E 0-50 arası normal kabul edilir
            pe_score = max(0, min(100, (50 - pe) / 50 * 100))
            scores['pe_score'] = pe_score
    
    # Gelir büyümesi: Yüksek büyüme iyi
    if 'revenue_growth' in fundamentals and fundamentals['revenue_growth'] is not None:
        growth = fundamentals['revenue_growth'] * 100  # Yüzdeye çevir
        # %0-50 arası büyüme normal
        growth_score = max(0, min(100, growth / 50 * 100))
        scores['growth_score'] = growth_score
    
    # Kâr marjı: Yüksek marj iyi
    if 'profit_margin' in fundamentals and fundamentals['profit_margin'] is not None:
        margin = fundamentals['profit_margin'] * 100  # Yüzdeye çevir
        # %0-30 arası marj normal
        margin_score = max(0, min(100, margin / 30 * 100))
        scores['margin_score'] = margin_score
    
    # Borç/Özsermaye: Düşük oran iyi
    if 'debt_to_equity' in fundamentals and fundamentals['debt_to_equity'] is not None:
        de_ratio = fundamentals['debt_to_equity']
        # 0-2 arası normal
        de_score = max(0, min(100, (2 - de_ratio) / 2 * 100))
        scores['de_score'] = de_score
    
    # Cari oran: 1-3 arası ideal
    if 'current_ratio' in fundamentals and fundamentals['current_ratio'] is not None:
        cr = fundamentals['current_ratio']
        if 1 <= cr <= 3:
            cr_score = 100
        elif cr < 1:
            cr_score = cr * 100  # 1'in altı kötü
        else:
            cr_score = max(0, 100 - (cr - 3) * 20)  # 3'ün üstü de kötü
        scores['current_ratio_score'] = cr_score
    
    # ROE (Özsermaye kârlılığı): Yüksek iyi
    if 'roe' in fundamentals and fundamentals['roe'] is not None:
        roe = fundamentals['roe'] * 100  # Yüzdeye çevir
        # %0-30 arası normal
        roe_score = max(0, min(100, roe / 30 * 100))
        scores['roe_score'] = roe_score
    
    # Tüm skorların ortalaması
    if scores:
        overall_score = sum(scores.values()) / len(scores)
    else:
        overall_score = 50.0  # Nötr skor
    
    return {
        'individual_scores': scores,
        'overall_score': overall_score
    }


def create_feature_vector(price_df: pd.DataFrame, fundamentals: Optional[Dict] = None) -> Dict:
    """
    Tüm feature'ları birleştirerek tek bir vektör oluşturur.
    
    Parametreler:
    ------------
    price_df : pd.DataFrame
        Feature'ları hesaplanmış fiyat DataFrame'i
    fundamentals : dict, optional
        Temel finansal göstergeler
    
    Döndürür:
    --------
    dict
        Feature vektörü
    """
    
    if price_df.empty:
        return {}
    
    # En son günün verisi
    latest = price_df.iloc[-1]
    
    features = {
        # Getiri feature'ları
        'return_5d': latest.get('return_5d', 0) * 100,  # Yüzdeye çevir
        'return_10d': latest.get('return_10d', 0) * 100,
        'return_30d': latest.get('return_30d', 0) * 100,
        
        # Volatilite
        'volatility_10d': latest.get('volatility_10d', 0) * 100,
        'volatility_30d': latest.get('volatility_30d', 0) * 100,
        
        # Hareketli ortalamalar (fiyatın MA'lara göre konumu)
        'price_vs_ma10': latest.get('price_vs_ma10', 0),
        'price_vs_ma20': latest.get('price_vs_ma20', 0),
        'price_vs_ma50': latest.get('price_vs_ma50', 0),
        
        # Teknik göstergeler
        'rsi_14': latest.get('rsi_14', 50),
        'macd': latest.get('macd', 0),
        'macd_histogram': latest.get('macd_histogram', 0),
        
        # Hacim
        'volume_ratio': latest.get('volume_ratio', 1.0),
    }
    
    # Finansal göstergeler varsa ekle
    if fundamentals:
        fin_scores = normalize_financial_metrics(fundamentals)
        features['financial_score'] = fin_scores['overall_score']
        # Bireysel skorları da ekle
        for key, value in fin_scores['individual_scores'].items():
            features[key] = value
    
    return features


def compute_financial_score(feature_vector: Dict) -> float:
    """
    Feature vektöründen finansal sağlık skoru hesaplar.
    
    Parametreler:
    ------------
    feature_vector : dict
        create_feature_vector() fonksiyonunun döndürdüğü vektör
    
    Döndürür:
    --------
    float
        0-100 arası finansal sağlık skoru
    """
    
    scores = []
    weights = []
    
    # Getiri skoru (son 30 günlük getiri)
    return_30d = feature_vector.get('return_30d', 0)  # Zaten yüzde
    # %-20 ile %+20 arası normal, bunun dışı ekstrem
    # %0 getiri = 50 skor, %+20 = 100 skor, %-20 = 0 skor
    return_score = max(0, min(100, 50 + return_30d * 2.5))
    scores.append(return_score)
    weights.append(0.3)  # %30 ağırlık
    
    # Volatilite skoru (düşük volatilite iyi)
    vol_30d = feature_vector.get('volatility_30d', 0)  # Zaten yüzde
    # %0-5 arası volatilite normal
    vol_score = max(0, min(100, 100 - vol_30d * 10))
    scores.append(vol_score)
    weights.append(0.2)  # %20 ağırlık
    
    # RSI skoru (30-70 arası sağlıklı)
    rsi = feature_vector.get('rsi_14', 50)
    if 30 <= rsi <= 70:
        rsi_score = 100 - abs(rsi - 50) * 2  # 50'ye yakın = yüksek skor
    else:
        rsi_score = max(0, 100 - abs(rsi - 50) * 1.5)  # Aşırı değerler düşük skor
    scores.append(rsi_score)
    weights.append(0.2)  # %20 ağırlık
    
    # Fiyat vs MA skoru (fiyat MA'nın üstündeyse iyi)
    price_vs_ma20 = feature_vector.get('price_vs_ma20', 0)
    ma_score = max(0, min(100, 50 + price_vs_ma20 * 2))
    scores.append(ma_score)
    weights.append(0.3)  # %30 ağırlık
    
    # Finansal göstergeler varsa ekle
    if 'financial_score' in feature_vector:
        fin_score = feature_vector['financial_score']
        scores.append(fin_score)
        weights.append(0.5)  # %50 ağırlık (daha önemli)
        
        # Diğer ağırlıkları normalize et
        total_other_weight = sum(weights[:-1])
        weights = [w / total_other_weight * 0.5 for w in weights[:-1]] + [0.5]
    
    # Ağırlıklı ortalama
    total_score = sum(score * weight for score, weight in zip(scores, weights))
    total_weight = sum(weights)
    
    return total_score / total_weight if total_weight > 0 else 50.0


if __name__ == "__main__":
    # Test
    print("=== Finansal Analiz Modülü Test ===\n")
    
    # Dummy fiyat verisi
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='D')
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = [base_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    price_df = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.99 for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    # Feature'ları hesapla
    print("1. Feature hesaplama:")
    price_df_with_features = compute_features(price_df)
    print(f"Toplam {len(price_df_with_features.columns)} kolon oluşturuldu.")
    print(f"Feature kolonları: {[c for c in price_df_with_features.columns if c not in price_df.columns]}")
    
    # Feature vektörü
    print("\n2. Feature vektörü:")
    feature_vector = create_feature_vector(price_df_with_features)
    print(feature_vector)
    
    # Finansal skor
    print("\n3. Finansal skor:")
    financial_score = compute_financial_score(feature_vector)
    print(f"Finansal Sağlık Skoru: {financial_score:.2f}/100")
    
    # Finansal göstergeler ile test
    print("\n4. Finansal göstergeler ile test:")
    fundamentals = {
        'pe_ratio': 15.0,
        'revenue_growth': 0.10,  # %10
        'profit_margin': 0.15,   # %15
        'debt_to_equity': 0.5
    }
    feature_vector_with_fund = create_feature_vector(price_df_with_features, fundamentals)
    financial_score_with_fund = compute_financial_score(feature_vector_with_fund)
    print(f"Finansal Sağlık Skoru (göstergelerle): {financial_score_with_fund:.2f}/100")

