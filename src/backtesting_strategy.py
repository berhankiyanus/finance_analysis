"""
Backtesting.py Kütüphanesi Entegrasyonu

backtesting.py kütüphanesini kullanarak strateji sınıfları oluşturur.
"""

import pandas as pd
import numpy as np

try:
    from backtesting import Strategy, Backtest
    from backtesting.lib import crossover
    BACKTESTING_AVAILABLE = True
except ImportError:
    BACKTESTING_AVAILABLE = False
    print("⚠️  backtesting.py kütüphanesi yüklü değil. 'pip install backtesting' komutu ile yükleyin.")


if BACKTESTING_AVAILABLE:
    class MLSignalStrategy(Strategy):
        """
        ML modelinden gelen sinyallere göre işlem yapan strateji.
        
        DataFrame'de 'signal' sütunu olmalı:
        - 1 = AL (BUY)
        - -1 = SAT (SELL)
        - 0 veya NaN = HOLD (işlem yapma)
        """
        
        # Strateji parametreleri
        stop_loss = 0.02  # %2 stop loss
        take_profit = 0.05  # %5 take profit
        
        def init(self):
            """
            Strateji başlatma - gerekli hesaplamaları yap
            """
            # Signal sütununu al
            self.signal = self.data.signal
            
            # Stop loss ve take profit seviyeleri
            self.stop_loss_pct = self.stop_loss
            self.take_profit_pct = self.take_profit
        
        def next(self):
            """
            Her bar'da çağrılan fonksiyon - işlem mantığı
            """
            # Mevcut sinyal
            current_signal = self.signal[-1]
            
            # Eğer sinyal yoksa veya 0 ise, işlem yapma
            if pd.isna(current_signal) or current_signal == 0:
                return
            
            # AL sinyali (1)
            if current_signal == 1:
                # Eğer pozisyon yoksa, al
                if not self.position:
                    self.buy()
                # Eğer kısa pozisyon varsa, kapat ve al
                elif self.position.is_short:
                    self.position.close()
                    self.buy()
            
            # SAT sinyali (-1)
            elif current_signal == -1:
                # Eğer pozisyon yoksa, kısa sat
                if not self.position:
                    self.sell()
                # Eğer uzun pozisyon varsa, kapat ve kısa sat
                elif self.position.is_long:
                    self.position.close()
                    self.sell()
            
            # Stop loss ve take profit kontrolü (uzun pozisyon için)
            if self.position.is_long:
                entry_price = self.position.entry_price
                current_price = self.data.Close[-1]
                
                # Stop loss
                if current_price <= entry_price * (1 - self.stop_loss_pct):
                    self.position.close()
                
                # Take profit
                elif current_price >= entry_price * (1 + self.take_profit_pct):
                    self.position.close()
            
            # Stop loss ve take profit kontrolü (kısa pozisyon için)
            elif self.position.is_short:
                entry_price = self.position.entry_price
                current_price = self.data.Close[-1]
                
                # Stop loss (kısa için ters)
                if current_price >= entry_price * (1 + self.stop_loss_pct):
                    self.position.close()
                
                # Take profit (kısa için ters)
                elif current_price <= entry_price * (1 - self.take_profit_pct):
                    self.position.close()
    
    
    class SimpleMAStrategy(Strategy):
        """
        Basit hareketli ortalama crossover stratejisi (örnek).
        """
        
        # Strateji parametreleri
        fast_period = 10
        slow_period = 30
        
        def init(self):
            """
            Strateji başlatma
            """
            # Hareketli ortalamaları hesapla
            self.fast_ma = self.I(lambda x: pd.Series(x).rolling(self.fast_period).mean(), self.data.Close)
            self.slow_ma = self.I(lambda x: pd.Series(x).rolling(self.slow_period).mean(), self.data.Close)
        
        def next(self):
            """
            Her bar'da çağrılan fonksiyon
            """
            # Hızlı MA yavaş MA'yı yukarı keserse AL
            if crossover(self.fast_ma, self.slow_ma):
                if not self.position:
                    self.buy()
            
            # Hızlı MA yavaş MA'yı aşağı keserse SAT
            elif crossover(self.slow_ma, self.fast_ma):
                if self.position:
                    self.position.close()


def run_backtesting_strategy(price_df: pd.DataFrame, 
                            signal_column: str = 'signal',
                            strategy_class=None,
                            **strategy_params) -> dict:
    """
    backtesting.py kütüphanesini kullanarak strateji backtest'i çalıştırır.
    
    Parametreler:
    ------------
    price_df : pd.DataFrame
        OHLCV verisi + signal sütunu
    signal_column : str
        Sinyal sütunu adı (varsayılan: 'signal')
    strategy_class : class
        Kullanılacak strateji sınıfı (varsayılan: MLSignalStrategy)
    **strategy_params
        Strateji parametreleri
    
    Döndürür:
    --------
    dict
        Backtest sonuçları: {'total_return', 'sharpe_ratio', 'max_drawdown', 'trades', 'equity_curve'}
    """
    
    if not BACKTESTING_AVAILABLE:
        raise ImportError("backtesting.py kütüphanesi yüklü değil. 'pip install backtesting' komutu ile yükleyin.")
    
    # DataFrame'i backtesting.py formatına çevir
    # backtesting.py 'Open', 'High', 'Low', 'Close', 'Volume' bekler
    bt_df = price_df.copy()
    
    # Kolon isimlerini standartlaştır
    column_mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in bt_df.columns:
            bt_df[new_col] = bt_df[old_col]
    
    # Gerekli kolonları seç
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if signal_column in bt_df.columns:
        required_cols.append(signal_column)
    
    bt_df = bt_df[required_cols].copy()
    
    # Index'i datetime yap (eğer değilse)
    if not isinstance(bt_df.index, pd.DatetimeIndex):
        if 'date' in bt_df.columns:
            bt_df.index = pd.to_datetime(bt_df['date'])
        else:
            bt_df.index = pd.date_range(start='2020-01-01', periods=len(bt_df), freq='D')
    
    # Strateji sınıfını seç
    if strategy_class is None:
        strategy_class = MLSignalStrategy
    
    # Backtest oluştur
    bt = Backtest(bt_df, strategy_class, cash=100000, commission=0.001)
    
    # Strateji parametrelerini ayarla
    if strategy_params:
        bt_strategy = bt.run(**strategy_params)
    else:
        bt_strategy = bt.run()
    
    # Sonuçları çıkar
    results = {
        'total_return': bt_strategy['Return [%]'] / 100,  # Yüzdeyi ondalığa çevir
        'sharpe_ratio': bt_strategy.get('Sharpe Ratio', None),
        'max_drawdown': bt_strategy.get('Max. Drawdown [%]', None) / 100 if bt_strategy.get('Max. Drawdown [%]', None) else None,
        'win_rate': bt_strategy.get('Win Rate [%]', None) / 100 if bt_strategy.get('Win Rate [%]', None) else None,
        'total_trades': bt_strategy.get('# Trades', 0),
        'equity_curve': bt_strategy._trades if hasattr(bt_strategy, '_trades') else None,
        'full_results': bt_strategy
    }
    
    return results


if __name__ == "__main__":
    print("=== Backtesting.py Entegrasyonu Test ===\n")
    
    if not BACKTESTING_AVAILABLE:
        print("❌ backtesting.py kütüphanesi yüklü değil.")
        print("   Yüklemek için: pip install backtesting")
    else:
        import pandas as pd
        import numpy as np
        
        # Test verisi oluştur
        dates = pd.date_range(start='2020-01-01', periods=252, freq='D')
        np.random.seed(42)
        
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        test_df = pd.DataFrame({
            'open': prices,
            'high': [p * 1.01 for p in prices],
            'low': [p * 0.99 for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates)),
            'signal': np.random.choice([-1, 0, 1], len(dates), p=[0.1, 0.8, 0.1])  # %10 AL, %10 SAT, %80 HOLD
        }, index=dates)
        
        print("1. ML Signal Stratejisi Test:")
        results = run_backtesting_strategy(test_df, signal_column='signal')
        
        print(f"\nSonuçlar:")
        print(f"  Toplam Getiri: {results['total_return']:.2%}")
        print(f"  Sharpe Oranı: {results['sharpe_ratio']:.2f}" if results['sharpe_ratio'] else "  Sharpe Oranı: N/A")
        print(f"  Max Drawdown: {results['max_drawdown']:.2%}" if results['max_drawdown'] else "  Max Drawdown: N/A")
        print(f"  Win Rate: {results['win_rate']:.2%}" if results['win_rate'] else "  Win Rate: N/A")
        print(f"  Toplam İşlem: {results['total_trades']}")

