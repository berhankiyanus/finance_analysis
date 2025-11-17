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


def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
    """
    Stochastic Oscillator hesaplar.
    
    Parametreler:
    ------------
    high, low, close : pd.Series
        Yüksek, düşük, kapanış fiyatları
    k_period : int
        %K periyodu (varsayılan: 14)
    d_period : int
        %D periyodu (varsayılan: 3)
    
    Döndürür:
    --------
    dict
        'stoch_k', 'stoch_d' serileri (0-100 arası)
    """
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    
    stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    stoch_d = stoch_k.rolling(d_period).mean()
    
    return {
        'stoch_k': stoch_k,
        'stoch_d': stoch_d
    }


def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Williams %R hesaplar.
    
    Parametreler:
    ------------
    high, low, close : pd.Series
        Yüksek, düşük, kapanış fiyatları
    period : int
        Periyot (varsayılan: 14)
    
    Döndürür:
    --------
    pd.Series
        Williams %R değerleri (-100 ile 0 arası)
    """
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()
    
    williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
    
    return williams_r


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average True Range (ATR) hesaplar.
    
    Parametreler:
    ------------
    high, low, close : pd.Series
        Yüksek, düşük, kapanış fiyatları
    period : int
        Periyot (varsayılan: 14)
    
    Döndürür:
    --------
    pd.Series
        ATR değerleri
    """
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(period).mean()
    
    return atr


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average Directional Index (ADX) hesaplar (basitleştirilmiş).
    
    Parametreler:
    ------------
    high, low, close : pd.Series
        Yüksek, düşük, kapanış fiyatları
    period : int
        Periyot (varsayılan: 14)
    
    Döndürür:
    --------
    pd.Series
        ADX değerleri (0-100 arası)
    """
    # True Range
    atr = calculate_atr(high, low, close, period)
    
    # Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    # ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    
    return adx


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On Balance Volume (OBV) hesaplar.
    
    Parametreler:
    ------------
    close : pd.Series
        Kapanış fiyatları
    volume : pd.Series
        Hacim
    
    Döndürür:
    --------
    pd.Series
        OBV değerleri
    """
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
    """
    Money Flow Index (MFI) hesaplar.
    
    Parametreler:
    ------------
    high, low, close : pd.Series
        Yüksek, düşük, kapanış fiyatları
    volume : pd.Series
        Hacim
    period : int
        Periyot (varsayılan: 14)
    
    Döndürür:
    --------
    pd.Series
        MFI değerleri (0-100 arası)
    """
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(period).sum()
    
    mfi = 100 - (100 / (1 + positive_flow / negative_flow))
    
    return mfi


def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """
    Commodity Channel Index (CCI) hesaplar.
    
    Parametreler:
    ------------
    high, low, close : pd.Series
        Yüksek, düşük, kapanış fiyatları
    period : int
        Periyot (varsayılan: 20)
    
    Döndürür:
    --------
    pd.Series
        CCI değerleri
    """
    typical_price = (high + low + close) / 3
    sma = typical_price.rolling(period).mean()
    mad = typical_price.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
    
    cci = (typical_price - sma) / (0.015 * mad)
    
    return cci


def calculate_momentum(close: pd.Series, period: int = 10) -> pd.Series:
    """
    Momentum hesaplar.
    
    Parametreler:
    ------------
    close : pd.Series
        Kapanış fiyatları
    period : int
        Periyot (varsayılan: 10)
    
    Döndürür:
    --------
    pd.Series
        Momentum değerleri
    """
    return close.diff(period)


def calculate_roc(close: pd.Series, period: int = 10) -> pd.Series:
    """
    Rate of Change (ROC) hesaplar.
    
    Parametreler:
    ------------
    close : pd.Series
        Kapanış fiyatları
    period : int
        Periyot (varsayılan: 10)
    
    Döndürür:
    --------
    pd.Series
        ROC değerleri (yüzde)
    """
    return close.pct_change(period) * 100


def detect_candlestick_patterns(open: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.DataFrame:
    """
    Basit candlestick pattern'leri tespit eder.
    
    Parametreler:
    ------------
    open, high, low, close : pd.Series
        Açılış, yüksek, düşük, kapanış fiyatları
    
    Döndürür:
    --------
    pd.DataFrame
        Pattern tespit sonuçları (0 veya 1)
    """
    patterns = pd.DataFrame(index=close.index)
    
    # Body ve shadow hesapla
    body = np.abs(close - open)
    upper_shadow = high - np.maximum(close, open)
    lower_shadow = np.minimum(close, open) - low
    total_range = high - low
    
    # Doji (çok küçük body)
    patterns['doji'] = ((body / total_range) < 0.1).astype(int)
    
    # Hammer (küçük body, uzun lower shadow)
    patterns['hammer'] = ((body / total_range < 0.3) & 
                          (lower_shadow > 2 * body) & 
                          (upper_shadow < body)).astype(int)
    
    # Shooting Star (küçük body, uzun upper shadow)
    patterns['shooting_star'] = ((body / total_range < 0.3) & 
                                 (upper_shadow > 2 * body) & 
                                 (lower_shadow < body)).astype(int)
    
    # Engulfing (önceki mumu tamamen kaplayan)
    prev_body = body.shift(1)
    patterns['bullish_engulfing'] = ((close > open) & 
                                      (close.shift(1) < open.shift(1)) &
                                      (close > open.shift(1)) & 
                                      (open < close.shift(1))).astype(int)
    
    patterns['bearish_engulfing'] = ((close < open) & 
                                      (close.shift(1) > open.shift(1)) &
                                      (close < open.shift(1)) & 
                                      (open > close.shift(1))).astype(int)
    
    return patterns


def create_features(stock_df: pd.DataFrame, tcmb_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Hisse ve TCMB verilerini birleştirerek özellik DataFrame'i oluşturur.
    
    Parametreler:
    ------------
    stock_df : pd.DataFrame
        Hisse fiyat verisi ('date', 'open', 'high', 'low', 'close', 'volume' kolonları)
    tcmb_df : pd.DataFrame, optional
        TCMB makroekonomik verisi ('date', 'value' kolonları - faiz, TÜFE, USD/TRY vb.)
    
    Döndürür:
    --------
    pd.DataFrame
        Teknik göstergeler ve makro verilerle zenginleştirilmiş DataFrame
    """
    # compute_features fonksiyonunu çağır (mevcut implementasyon)
    features_df = compute_features(
        stock_df,
        faiz_orani=tcmb_df['value'] if tcmb_df is not None and 'value' in tcmb_df.columns else None
    )
    
    # TCMB verisini birleştir (eğer varsa)
    if tcmb_df is not None and not tcmb_df.empty:
        # TCMB DataFrame'i hazırla
        tcmb_clean = tcmb_df.copy()
        if 'date' in tcmb_clean.columns:
            # Timezone'u kaldır (eğer varsa)
            if hasattr(tcmb_clean['date'].dtype, 'tz') and tcmb_clean['date'].dtype.tz is not None:
                tcmb_clean['date'] = pd.to_datetime(tcmb_clean['date']).dt.tz_localize(None)
            else:
                tcmb_clean['date'] = pd.to_datetime(tcmb_clean['date'])
            tcmb_clean = tcmb_clean.rename(columns={'value': 'tcmb_rate'})
            
            # Stock DataFrame'deki date'i de normalize et
            if 'date' in features_df.columns:
                features_df['date'] = pd.to_datetime(features_df['date'])
                if hasattr(features_df['date'].dtype, 'tz') and features_df['date'].dtype.tz is not None:
                    features_df['date'] = features_df['date'].dt.tz_localize(None)
            
            # Tarih üzerinden merge
            features_df = features_df.merge(
                tcmb_clean[['date', 'tcmb_rate']],
                on='date',
                how='left'
            )
            # Forward fill ile eksik değerleri doldur
            features_df['tcmb_rate'] = features_df['tcmb_rate'].fillna(method='ffill')
    
    return features_df


def compute_features(price_df: pd.DataFrame, 
                    hisse_duygu_skoru: Optional[pd.Series] = None,
                    piyasa_duygu_skoru: Optional[pd.Series] = None,
                    faiz_orani: Optional[pd.Series] = None) -> pd.DataFrame:
    """
    Fiyat verisinden feature'lar üretir (teknik + duygu özellikleri).
    
    Parametreler:
    ------------
    price_df : pd.DataFrame
        'date', 'open', 'high', 'low', 'close', 'volume' kolonları olmalı
    hisse_duygu_skoru : pd.Series, optional
        Hisse bazlı duygu skoru (0-1 arası, tarih index'li)
    piyasa_duygu_skoru : pd.Series, optional
        Piyasa geneli duygu skoru (0-1 arası, tarih index'li)
    faiz_orani : pd.Series, optional
        Faiz oranı (tarih index'li)
    
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
    
    # === GELİŞMİŞ TEKNİK GÖSTERGELER ===
    
    # Stochastic Oscillator
    stoch = calculate_stochastic(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch['stoch_k']
    df['stoch_d'] = stoch['stoch_d']
    
    # Williams %R
    df['williams_r'] = calculate_williams_r(df['high'], df['low'], df['close'])
    
    # ATR (Average True Range)
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'])
    df['atr_percent'] = (df['atr'] / df['close']) * 100  # Yüzde olarak
    
    # ADX (Average Directional Index)
    df['adx'] = calculate_adx(df['high'], df['low'], df['close'])
    
    # OBV (On Balance Volume)
    df['obv'] = calculate_obv(df['close'], df['volume'])
    df['obv_ma'] = df['obv'].rolling(20).mean()
    df['obv_trend'] = (df['obv'] > df['obv_ma']).astype(int)  # 1 = yükseliş, 0 = düşüş
    
    # Money Flow Index (MFI)
    df['mfi'] = calculate_mfi(df['high'], df['low'], df['close'], df['volume'])
    
    # Commodity Channel Index (CCI)
    df['cci'] = calculate_cci(df['high'], df['low'], df['close'])
    
    # Momentum
    df['momentum_10'] = calculate_momentum(df['close'], period=10)
    df['momentum_20'] = calculate_momentum(df['close'], period=20)
    
    # Rate of Change (ROC)
    df['roc_10'] = calculate_roc(df['close'], period=10)
    df['roc_20'] = calculate_roc(df['close'], period=20)
    
    # === CANDLESTICK PATTERNS ===
    if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
        patterns = detect_candlestick_patterns(df['open'], df['high'], df['low'], df['close'])
        for pattern_name in patterns.columns:
            df[f'pattern_{pattern_name}'] = patterns[pattern_name]
    
    # === FİYAT POZİSYON FEATURES ===
    # Fiyatın günlük aralıktaki konumu (0-1 arası, 0 = düşük, 1 = yüksek)
    df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
    df['price_position'] = df['price_position'].replace([np.inf, -np.inf], 0.5).fillna(0.5)
    
    # Fiyatın Bollinger Bands içindeki konumu
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
        bb_range = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = (df['close'] - df['bb_lower']) / bb_range
        df['bb_position'] = df['bb_position'].replace([np.inf, -np.inf], 0.5).fillna(0.5)
    
    # === ZAMAN TABANLI FEATURES ===
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek  # 0 = Pazartesi, 6 = Pazar
        df['month'] = df['date'].dt.month
        df['is_month_end'] = (df['date'].dt.is_month_end).astype(int)
        df['is_quarter_end'] = (df['date'].dt.is_quarter_end).astype(int)
    elif df.index.dtype == 'datetime64[ns]':
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        df['is_month_end'] = (df.index.is_month_end).astype(int)
        df['is_quarter_end'] = (df.index.is_quarter_end).astype(int)
    
    # === VOLATİLİTE ÖLÇÜMLERİ ===
    # Realized Volatility (daha hassas)
    df['realized_vol_10d'] = np.sqrt(252) * df['daily_return'].rolling(10).std() * 100
    df['realized_vol_30d'] = np.sqrt(252) * df['daily_return'].rolling(30).std() * 100
    
    # Parkinson Volatility (high-low kullanarak)
    df['parkinson_vol'] = np.sqrt(252 / (4 * np.log(2))) * np.sqrt(np.log(df['high'] / df['low'])**2).rolling(20).mean() * 100
    
    # === HACİM-BAZLI FEATURES ===
    # Volume Price Trend (VPT)
    df['vpt'] = (df['volume'] * df['daily_return']).cumsum()
    df['vpt_ma'] = df['vpt'].rolling(20).mean()
    df['vpt_trend'] = (df['vpt'] > df['vpt_ma']).astype(int)
    
    # Volume Weighted Average Price (VWAP) - günlük
    df['vwap'] = (df['close'] * df['volume']).rolling(20).sum() / df['volume'].rolling(20).sum()
    df['price_vs_vwap'] = (df['close'] / df['vwap'] - 1) * 100
    
    # === MOMENTUM FEATURES ===
    # Price Acceleration (momentum'un değişimi)
    df['price_acceleration'] = df['momentum_10'].diff()
    
    # === TREND STRENGTH ===
    # ADX ile trend gücü (zaten hesaplandı)
    # RSI trend (RSI'nın kendisi trend gücünü gösterir)
    
    # === MEAN REVERSION FEATURES ===
    # Fiyatın ortalamadan sapması (z-score)
    df['price_zscore_20'] = (df['close'] - df['ma_20']) / df['close'].rolling(20).std()
    df['price_zscore_50'] = (df['close'] - df['ma_50']) / df['close'].rolling(50).std()
    
    # === DUYGU VE MAKRO ÖZELLİKLERİ ===
    
    # Hisse duygu skoru (eğer verilmişse)
    if hisse_duygu_skoru is not None:
        # Tarih index'ini hizala
        if isinstance(hisse_duygu_skoru, pd.Series):
            # DataFrame'in tarih kolonuna veya index'ine göre hizala
            if 'date' in df.columns:
                df['hisse_duygu_skoru'] = df['date'].map(hisse_duygu_skoru).ffill()
            elif df.index.dtype == 'datetime64[ns]':
                df['hisse_duygu_skoru'] = df.index.to_series().map(hisse_duygu_skoru).ffill()
            else:
                df['hisse_duygu_skoru'] = hisse_duygu_skoru.reindex(df.index).ffill()
            
            # Hareketli ortalamalar
            df['hisse_duygu_ma_3'] = df['hisse_duygu_skoru'].rolling(3).mean()
            df['hisse_duygu_ma_7'] = df['hisse_duygu_skoru'].rolling(7).mean()
            df['hisse_duygu_ma_14'] = df['hisse_duygu_skoru'].rolling(14).mean()
            
            # Trend (artış/azalış)
            df['hisse_duygu_trend'] = df['hisse_duygu_skoru'].diff()
    
    # Piyasa duygu skoru (eğer verilmişse)
    if piyasa_duygu_skoru is not None:
        if isinstance(piyasa_duygu_skoru, pd.Series):
            if 'date' in df.columns:
                df['piyasa_duygu_skoru'] = df['date'].map(piyasa_duygu_skoru).ffill()
            elif df.index.dtype == 'datetime64[ns]':
                df['piyasa_duygu_skoru'] = df.index.to_series().map(piyasa_duygu_skoru).ffill()
            else:
                df['piyasa_duygu_skoru'] = piyasa_duygu_skoru.reindex(df.index).ffill()
            
            # Hareketli ortalamalar
            df['piyasa_duygu_ma_3'] = df['piyasa_duygu_skoru'].rolling(3).mean()
            df['piyasa_duygu_ma_7'] = df['piyasa_duygu_skoru'].rolling(7).mean()
            df['piyasa_duygu_ma_14'] = df['piyasa_duygu_skoru'].rolling(14).mean()
            
            # Trend
            df['piyasa_duygu_trend'] = df['piyasa_duygu_skoru'].diff()
    
    # Faiz oranı (eğer verilmişse)
    if faiz_orani is not None:
        if isinstance(faiz_orani, pd.Series):
            if 'date' in df.columns:
                df['faiz_orani'] = df['date'].map(faiz_orani).ffill()
            elif df.index.dtype == 'datetime64[ns]':
                df['faiz_orani'] = df.index.to_series().map(faiz_orani).ffill()
            else:
                df['faiz_orani'] = faiz_orani.reindex(df.index).ffill()
            
            # Faiz değişimi
            df['faiz_degisim'] = df['faiz_orani'].diff()
            
            # Faiz vs fiyat korelasyonu (rolling)
            df['faiz_fiyat_corr'] = df['close'].rolling(20).corr(df['faiz_orani'])
    
    # === DUYGU-FİYAT ETKİLEŞİMİ ===
    # Hisse duygu ile fiyat getirisi korelasyonu
    if 'hisse_duygu_skoru' in df.columns and 'daily_return' in df.columns:
        df['duygu_getiri_corr'] = df['daily_return'].rolling(10).corr(df['hisse_duygu_skoru'])
    
    # Piyasa duygu ile fiyat getirisi korelasyonu
    if 'piyasa_duygu_skoru' in df.columns and 'daily_return' in df.columns:
        df['piyasa_duygu_getiri_corr'] = df['daily_return'].rolling(10).corr(df['piyasa_duygu_skoru'])
    
    return df


def normalize_financial_metrics(fundamentals: Dict) -> Dict:
    """
    Finansal göstergeleri 0-100 arası skora çevirir (genişletilmiş versiyon).
    
    Parametreler:
    ------------
    fundamentals : dict
        Finansal göstergeler (P/E, gelir büyümesi, kâr marjı, bilanço, gelir tablosu vb.)
    
    Döndürür:
    --------
    dict
        'individual_scores': Her gösterge için skor
        'overall_score': Genel finansal skor (0-100)
    """
    
    scores = {}
    
    # === FİYAT ORANLARI ===
    # P/E oranı: Düşük P/E genelde iyi
    if 'pe_ratio' in fundamentals and fundamentals['pe_ratio'] is not None:
        pe = fundamentals['pe_ratio']
        if pe > 0:
            pe_score = max(0, min(100, (50 - pe) / 50 * 100))
            scores['pe_score'] = pe_score
    
    # Forward P/E
    if 'forward_pe' in fundamentals and fundamentals['forward_pe'] is not None:
        fpe = fundamentals['forward_pe']
        if fpe > 0:
            fpe_score = max(0, min(100, (50 - fpe) / 50 * 100))
            scores['forward_pe_score'] = fpe_score
    
    # PEG Ratio (P/E Growth): 1 civarı ideal
    if 'peg_ratio' in fundamentals and fundamentals['peg_ratio'] is not None:
        peg = fundamentals['peg_ratio']
        if peg > 0:
            # 1'e yakın = yüksek skor
            peg_score = max(0, min(100, 100 - abs(peg - 1) * 50))
            scores['peg_score'] = peg_score
    
    # Price to Book: Düşük iyi
    if 'price_to_book' in fundamentals and fundamentals['price_to_book'] is not None:
        pb = fundamentals['price_to_book']
        if pb > 0:
            pb_score = max(0, min(100, (5 - pb) / 5 * 100))
            scores['pb_score'] = pb_score
    
    # Price to Sales: Düşük iyi
    if 'price_to_sales' in fundamentals and fundamentals['price_to_sales'] is not None:
        ps = fundamentals['price_to_sales']
        if ps > 0:
            ps_score = max(0, min(100, (10 - ps) / 10 * 100))
            scores['ps_score'] = ps_score
    
    # === BÜYÜME ORANLARI ===
    # Gelir büyümesi: Yüksek büyüme iyi
    if 'revenue_growth' in fundamentals and fundamentals['revenue_growth'] is not None:
        growth = fundamentals['revenue_growth'] * 100
        growth_score = max(0, min(100, growth / 50 * 100))
        scores['growth_score'] = growth_score
    
    # Kâr büyümesi
    if 'earnings_yearly_growth' in fundamentals and fundamentals['earnings_yearly_growth'] is not None:
        earn_growth = fundamentals['earnings_yearly_growth'] * 100
        earn_growth_score = max(0, min(100, earn_growth / 50 * 100))
        scores['earnings_growth_score'] = earn_growth_score
    
    # === KÂRLILIK ORANLARI ===
    # Kâr marjı: Yüksek marj iyi
    if 'profit_margin' in fundamentals and fundamentals['profit_margin'] is not None:
        margin = fundamentals['profit_margin'] * 100
        margin_score = max(0, min(100, margin / 30 * 100))
        scores['margin_score'] = margin_score
    
    # Gross Margin
    if 'gross_margin' in fundamentals and fundamentals['gross_margin'] is not None:
        gross_margin = fundamentals['gross_margin'] * 100
        gross_score = max(0, min(100, gross_margin / 50 * 100))
        scores['gross_margin_score'] = gross_score
    
    # Operating Margin
    if 'operating_margin' in fundamentals and fundamentals['operating_margin'] is not None:
        op_margin = fundamentals['operating_margin'] * 100
        op_score = max(0, min(100, op_margin / 30 * 100))
        scores['operating_margin_score'] = op_score
    
    # EBITDA Margin
    if 'ebitda_margin' in fundamentals and fundamentals['ebitda_margin'] is not None:
        ebitda_margin = fundamentals['ebitda_margin'] * 100
        ebitda_score = max(0, min(100, ebitda_margin / 30 * 100))
        scores['ebitda_margin_score'] = ebitda_score
    
    # ROE (Özsermaye kârlılığı): Yüksek iyi
    if 'roe' in fundamentals and fundamentals['roe'] is not None:
        roe = fundamentals['roe'] * 100
        roe_score = max(0, min(100, roe / 30 * 100))
        scores['roe_score'] = roe_score
    
    # ROA (Varlık kârlılığı)
    if 'roa' in fundamentals and fundamentals['roa'] is not None:
        roa = fundamentals['roa'] * 100
        roa_score = max(0, min(100, roa / 20 * 100))
        scores['roa_score'] = roa_score
    
    # ROIC (Yatırılan sermaye kârlılığı)
    if 'roic' in fundamentals and fundamentals['roic'] is not None:
        roic = fundamentals['roic'] * 100
        roic_score = max(0, min(100, roic / 20 * 100))
        scores['roic_score'] = roic_score
    
    # === FİNANSAL SAĞLIK ===
    # Borç/Özsermaye: Düşük oran iyi
    if 'debt_to_equity' in fundamentals and fundamentals['debt_to_equity'] is not None:
        de_ratio = fundamentals['debt_to_equity']
        de_score = max(0, min(100, (2 - de_ratio) / 2 * 100))
        scores['de_score'] = de_score
    
    # Debt to Assets
    if 'debt_to_assets' in fundamentals and fundamentals['debt_to_assets'] is not None:
        da_ratio = fundamentals['debt_to_assets']
        da_score = max(0, min(100, (0.5 - da_ratio) / 0.5 * 100))
        scores['debt_to_assets_score'] = da_score
    
    # Cari oran: 1-3 arası ideal
    if 'current_ratio' in fundamentals and fundamentals['current_ratio'] is not None:
        cr = fundamentals['current_ratio']
        if 1 <= cr <= 3:
            cr_score = 100
        elif cr < 1:
            cr_score = cr * 100
        else:
            cr_score = max(0, 100 - (cr - 3) * 20)
        scores['current_ratio_score'] = cr_score
    
    # Quick Ratio
    if 'quick_ratio' in fundamentals and fundamentals['quick_ratio'] is not None:
        qr = fundamentals['quick_ratio']
        if 0.5 <= qr <= 2:
            qr_score = max(0, min(100, (qr - 0.5) / 1.5 * 100))
        else:
            qr_score = max(0, 100 - abs(qr - 1.25) * 40)
        scores['quick_ratio_score'] = qr_score
    
    # === LİKİDİTE ===
    # Free Cash Flow pozitifse iyi
    if 'free_cashflow' in fundamentals and fundamentals['free_cashflow'] is not None:
        fcf = fundamentals['free_cashflow']
        if fcf > 0:
            # Büyük FCF = yüksek skor (logaritmik ölçek)
            import math
            fcf_score = min(100, max(0, 50 + math.log10(abs(fcf) / 1e6) * 10))
            scores['fcf_score'] = fcf_score
    
    # Cash per Share
    if 'cash_per_share' in fundamentals and fundamentals['cash_per_share'] is not None:
        cps = fundamentals['cash_per_share']
        if cps > 0:
            cps_score = min(100, max(0, cps / 10 * 100))
            scores['cash_per_share_score'] = cps_score
    
    # === TEMETTÜ ===
    # Dividend Yield: Orta seviye iyi (çok yüksek riskli olabilir)
    if 'dividend_yield' in fundamentals and fundamentals['dividend_yield'] is not None:
        div_yield = fundamentals['dividend_yield'] * 100
        # %2-5 arası ideal
        if 2 <= div_yield <= 5:
            div_score = 100
        else:
            div_score = max(0, 100 - abs(div_yield - 3.5) * 20)
        scores['dividend_yield_score'] = div_score
    
    # === BİLANÇO VE GELİR TABLOSU ===
    # Bilanço analizi
    if 'balance_sheet' in fundamentals and fundamentals['balance_sheet']:
        bs = fundamentals['balance_sheet']
        # Özsermaye / Toplam Varlıklar oranı
        if bs.get('total_equity') and bs.get('total_assets'):
            if bs['total_assets'] > 0:
                equity_ratio = bs['total_equity'] / bs['total_assets']
                equity_ratio_score = max(0, min(100, equity_ratio * 200))  # %50 = 100 skor
                scores['equity_ratio_score'] = equity_ratio_score
    
    # Gelir tablosu analizi
    if 'income_statement' in fundamentals and fundamentals['income_statement']:
        is_stmt = fundamentals['income_statement']
        # Net Income pozitifse iyi
        if is_stmt.get('net_income'):
            if is_stmt['net_income'] > 0:
                ni_score = min(100, max(0, 50 + math.log10(abs(is_stmt['net_income']) / 1e6) * 10))
                scores['net_income_score'] = ni_score
    
    # Nakit akış analizi
    if 'cash_flow' in fundamentals and fundamentals['cash_flow']:
        cf = fundamentals['cash_flow']
        # Operating Cash Flow pozitifse iyi
        if cf.get('operating_cashflow'):
            if cf['operating_cashflow'] > 0:
                ocf_score = min(100, max(0, 50 + math.log10(abs(cf['operating_cashflow']) / 1e6) * 10))
                scores['operating_cf_score'] = ocf_score
    
    # Tüm skorların ağırlıklı ortalaması
    if scores:
        # Önemli göstergelere daha fazla ağırlık ver
        weights = {
            'pe_score': 1.5, 'forward_pe_score': 1.2, 'peg_score': 1.3,
            'growth_score': 1.5, 'earnings_growth_score': 1.3,
            'margin_score': 1.4, 'roe_score': 1.5, 'roa_score': 1.2, 'roic_score': 1.3,
            'de_score': 1.2, 'current_ratio_score': 1.1,
            'fcf_score': 1.3, 'operating_cf_score': 1.2,
        }
        
        weighted_sum = sum(scores.get(k, 0) * weights.get(k, 1.0) for k in scores.keys())
        total_weight = sum(weights.get(k, 1.0) for k in scores.keys())
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else sum(scores.values()) / len(scores)
    else:
        overall_score = 50.0  # Nötr skor
    
    return {
        'individual_scores': scores,
        'overall_score': overall_score
    }


def create_feature_vector(price_df: pd.DataFrame, fundamentals: Optional[Dict] = None, macro_data: Optional[Dict] = None) -> Dict:
    """
    Tüm feature'ları birleştirerek tek bir vektör oluşturur (genişletilmiş versiyon).
    
    Parametreler:
    ------------
    price_df : pd.DataFrame
        Feature'ları hesaplanmış fiyat DataFrame'i
    fundamentals : dict, optional
        Temel finansal göstergeler
    macro_data : dict, optional
        Makroekonomik veriler
    
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
        'realized_vol_10d': latest.get('realized_vol_10d', 0),
        'realized_vol_30d': latest.get('realized_vol_30d', 0),
        'parkinson_vol': latest.get('parkinson_vol', 0),
        
        # Hareketli ortalamalar (fiyatın MA'lara göre konumu)
        'price_vs_ma10': latest.get('price_vs_ma10', 0),
        'price_vs_ma20': latest.get('price_vs_ma20', 0),
        'price_vs_ma50': latest.get('price_vs_ma50', 0),
        'price_vs_vwap': latest.get('price_vs_vwap', 0),
        
        # Teknik göstergeler
        'rsi_14': latest.get('rsi_14', 50),
        'macd': latest.get('macd', 0),
        'macd_histogram': latest.get('macd_histogram', 0),
        
        # Gelişmiş teknik göstergeler
        'stoch_k': latest.get('stoch_k', 50),
        'stoch_d': latest.get('stoch_d', 50),
        'williams_r': latest.get('williams_r', -50),
        'atr_percent': latest.get('atr_percent', 0),
        'adx': latest.get('adx', 25),
        'mfi': latest.get('mfi', 50),
        'cci': latest.get('cci', 0),
        'momentum_10': latest.get('momentum_10', 0),
        'momentum_20': latest.get('momentum_20', 0),
        'roc_10': latest.get('roc_10', 0),
        'roc_20': latest.get('roc_20', 0),
        
        # Hacim
        'volume_ratio': latest.get('volume_ratio', 1.0),
        'obv_trend': latest.get('obv_trend', 0),
        'vpt_trend': latest.get('vpt_trend', 0),
        
        # Fiyat pozisyon
        'price_position': latest.get('price_position', 0.5),
        'bb_position': latest.get('bb_position', 0.5),
        
        # Mean reversion
        'price_zscore_20': latest.get('price_zscore_20', 0),
        'price_zscore_50': latest.get('price_zscore_50', 0),
        
        # Momentum
        'price_acceleration': latest.get('price_acceleration', 0),
        
        # Candlestick patterns
        'pattern_doji': latest.get('pattern_doji', 0),
        'pattern_hammer': latest.get('pattern_hammer', 0),
        'pattern_shooting_star': latest.get('pattern_shooting_star', 0),
        'pattern_bullish_engulfing': latest.get('pattern_bullish_engulfing', 0),
        'pattern_bearish_engulfing': latest.get('pattern_bearish_engulfing', 0),
    }
    
    # Duygu özellikleri (eğer varsa)
    if 'hisse_duygu_skoru' in price_df.columns:
        features['hisse_duygu_skoru'] = latest.get('hisse_duygu_skoru', 0.5)
        features['hisse_duygu_ma_3'] = latest.get('hisse_duygu_ma_3', 0.5)
        features['hisse_duygu_ma_7'] = latest.get('hisse_duygu_ma_7', 0.5)
        features['hisse_duygu_ma_14'] = latest.get('hisse_duygu_ma_14', 0.5)
        features['hisse_duygu_trend'] = latest.get('hisse_duygu_trend', 0)
    
    if 'piyasa_duygu_skoru' in price_df.columns:
        features['piyasa_duygu_skoru'] = latest.get('piyasa_duygu_skoru', 0.5)
        features['piyasa_duygu_ma_3'] = latest.get('piyasa_duygu_ma_3', 0.5)
        features['piyasa_duygu_ma_7'] = latest.get('piyasa_duygu_ma_7', 0.5)
        features['piyasa_duygu_ma_14'] = latest.get('piyasa_duygu_ma_14', 0.5)
        features['piyasa_duygu_trend'] = latest.get('piyasa_duygu_trend', 0)
    
    if 'faiz_orani' in price_df.columns:
        features['faiz_orani'] = latest.get('faiz_orani', 0)
        features['faiz_degisim'] = latest.get('faiz_degisim', 0)
        features['faiz_fiyat_corr'] = latest.get('faiz_fiyat_corr', 0)
    
    if 'duygu_getiri_corr' in price_df.columns:
        features['duygu_getiri_corr'] = latest.get('duygu_getiri_corr', 0)
    
    if 'piyasa_duygu_getiri_corr' in price_df.columns:
        features['piyasa_duygu_getiri_corr'] = latest.get('piyasa_duygu_getiri_corr', 0)
    
    # Zaman tabanlı features (eğer varsa)
    if 'day_of_week' in price_df.columns:
        features['day_of_week'] = latest.get('day_of_week', 0)
    if 'month' in price_df.columns:
        features['month'] = latest.get('month', 6)
    if 'is_month_end' in price_df.columns:
        features['is_month_end'] = latest.get('is_month_end', 0)
    if 'is_quarter_end' in price_df.columns:
        features['is_quarter_end'] = latest.get('is_quarter_end', 0)
    
    # Finansal göstergeler varsa ekle
    if fundamentals:
        fin_scores = normalize_financial_metrics(fundamentals)
        features['financial_score'] = fin_scores['overall_score']
        # Bireysel skorları da ekle
        for key, value in fin_scores['individual_scores'].items():
            features[key] = value
        
        # Önemli finansal oranları direkt ekle (normalize edilmiş)
        if 'pe_ratio' in fundamentals and fundamentals['pe_ratio']:
            features['pe_ratio'] = fundamentals['pe_ratio']
        if 'revenue_growth' in fundamentals and fundamentals['revenue_growth']:
            features['revenue_growth'] = fundamentals['revenue_growth'] * 100
        if 'profit_margin' in fundamentals and fundamentals['profit_margin']:
            features['profit_margin'] = fundamentals['profit_margin'] * 100
        if 'roe' in fundamentals and fundamentals['roe']:
            features['roe'] = fundamentals['roe'] * 100
        if 'debt_to_equity' in fundamentals and fundamentals['debt_to_equity']:
            features['debt_to_equity'] = fundamentals['debt_to_equity']
    
    # Makroekonomik veriler varsa ekle
    if macro_data:
        # Risk-free rate (10Y Treasury)
        if 'treasury_10y' in macro_data:
            features['risk_free_rate'] = macro_data['treasury_10y']
        
        # VIX (Volatilite endeksi)
        if 'vix' in macro_data:
            features['vix'] = macro_data['vix']
        
        # Dolar endeksi
        if 'dollar_index' in macro_data:
            features['dollar_index'] = macro_data['dollar_index']
        
        # USD/TRY (Türkiye için)
        if 'usd_try' in macro_data:
            features['usd_try'] = macro_data['usd_try']
    
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

