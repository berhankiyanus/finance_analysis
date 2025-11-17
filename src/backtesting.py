"""
Backtesting Modülü

Bu modül, modelin ürettiği sinyallere göre geçmişe dönük sanal alım-satım işlemleri
simüle eder ve finansal performans metriklerini hesaplar.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from .financial_analysis import compute_features, create_feature_vector
    from .scoring import predict_direction, compute_overall_score, interpret_score
    from .sentiment_analysis import aggregate_sentiment
    from .data_collection import get_news, get_price_data
except ImportError:
    from src.financial_analysis import compute_features, create_feature_vector
    from src.scoring import predict_direction, compute_overall_score, interpret_score
    from src.sentiment_analysis import aggregate_sentiment
    from src.data_collection import get_news, get_price_data


class BacktestEngine:
    """
    Backtesting motoru - geçmiş veriler üzerinde strateji testi yapar.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,  # %0.1 komisyon
        slippage: float = 0.0005  # %0.05 slippage
    ):
        """
        Backtest engine'i başlatır.
        
        Parametreler:
        ------------
        initial_capital : float
            Başlangıç sermayesi (varsayılan: 100,000 TL)
        commission : float
            İşlem komisyonu (varsayılan: 0.001 = %0.1)
        slippage : float
            Slippage (gerçek fiyat ile işlem fiyatı arasındaki fark, varsayılan: 0.0005 = %0.05)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
    def signal_to_action(
        self,
        direction: str,
        overall_score: float,
        confidence: float,
        current_position: str = 'cash'
    ) -> str:
        """
        Model sinyalini alım/satım/tut kararına çevirir.
        
        Parametreler:
        ------------
        direction : str
            'up', 'down', veya 'neutral'
        overall_score : float
            Genel durum skoru (0-100)
        confidence : float
            Tahmin güveni (0-1)
        current_position : str
            Mevcut pozisyon ('cash', 'long', 'short')
        
        Döndürür:
        --------
        str
            'buy', 'sell', veya 'hold'
        """
        
        # Eğer güven çok düşükse, mevcut pozisyonu koru
        if confidence < 0.4:
            if current_position == 'cash':
                return 'hold'
            elif current_position == 'long':
                return 'hold'  # Pozisyonu koru
            else:
                return 'hold'
        
        # Skor ve yön bazlı karar
        if direction == 'up' and overall_score >= 60 and confidence >= 0.5:
            if current_position == 'cash':
                return 'buy'
            elif current_position == 'long':
                return 'hold'  # Zaten long pozisyondayız
            else:
                return 'buy'  # Short'tan long'a geç
        elif direction == 'down' and overall_score < 40 and confidence >= 0.5:
            if current_position == 'long':
                return 'sell'  # Long pozisyonu kapat
            elif current_position == 'cash':
                return 'hold'  # Short yapmıyoruz (sadece long stratejisi)
            else:
                return 'hold'
        elif overall_score < 30:  # Çok zayıf skor
            if current_position == 'long':
                return 'sell'  # Zararı durdur
            else:
                return 'hold'
        else:
            # Nötr veya belirsiz - mevcut pozisyonu koru
            return 'hold'
    
    def run_backtest(
        self,
        price_df: pd.DataFrame,
        signals_df: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Backtest çalıştırır.
        
        Parametreler:
        ------------
        price_df : pd.DataFrame
            Fiyat verisi (OHLCV)
        signals_df : pd.DataFrame
            Sinyaller (tarih, direction, overall_score, confidence kolonları)
        start_date : str, optional
            Başlangıç tarihi (YYYY-MM-DD)
        end_date : str, optional
            Bitiş tarihi (YYYY-MM-DD)
        
        Döndürür:
        --------
        dict
            Backtest sonuçları ve metrikler
        """
        
        # Tarih filtreleme
        if start_date:
            price_df = price_df[price_df.index >= start_date]
            signals_df = signals_df[signals_df.index >= start_date]
        if end_date:
            price_df = price_df[price_df.index <= end_date]
            signals_df = signals_df[signals_df.index <= end_date]
        
        # Sinyalleri fiyat verisi ile birleştir
        merged_df = price_df.join(signals_df, how='inner')
        
        if merged_df.empty:
            return {
                'error': 'Tarih aralığında veri bulunamadı',
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'total_trades': 0
            }
        
        # Backtest simülasyonu
        capital = self.initial_capital
        position = 'cash'  # 'cash', 'long'
        shares = 0
        entry_price = 0.0
        
        trades = []
        equity_curve = []
        
        for idx, row in merged_df.iterrows():
            current_price = row['close']
            
            # Sinyal varsa işlem yap
            if pd.notna(row.get('direction')):
                direction = row['direction']
                overall_score = row.get('overall_score', 50.0)
                confidence = row.get('confidence', 0.5)
                
                action = self.signal_to_action(direction, overall_score, confidence, position)
                
                if action == 'buy' and position == 'cash':
                    # Alım yap
                    shares = capital / (current_price * (1 + self.slippage))
                    cost = shares * current_price * (1 + self.slippage) * (1 + self.commission)
                    capital -= cost
                    position = 'long'
                    entry_price = current_price * (1 + self.slippage)
                    
                    trades.append({
                        'date': idx,
                        'action': 'buy',
                        'price': current_price,
                        'shares': shares,
                        'capital': capital
                    })
                
                elif action == 'sell' and position == 'long':
                    # Satış yap
                    revenue = shares * current_price * (1 - self.slippage) * (1 - self.commission)
                    capital += revenue
                    profit = revenue - (shares * entry_price)
                    
                    trades.append({
                        'date': idx,
                        'action': 'sell',
                        'price': current_price,
                        'shares': shares,
                        'profit': profit,
                        'capital': capital
                    })
                    
                    shares = 0
                    position = 'cash'
                    entry_price = 0.0
            
            # Equity hesapla (mevcut pozisyon değeri + nakit)
            if position == 'long':
                current_equity = capital + (shares * current_price)
            else:
                current_equity = capital
            
            equity_curve.append({
                'date': idx,
                'equity': current_equity,
                'position': position
            })
        
        # Son pozisyonu kapat (eğer varsa)
        if position == 'long' and len(merged_df) > 0:
            last_price = merged_df.iloc[-1]['close']
            revenue = shares * last_price * (1 - self.slippage) * (1 - self.commission)
            capital += revenue
            profit = revenue - (shares * entry_price)
            
            trades.append({
                'date': merged_df.index[-1],
                'action': 'sell',
                'price': last_price,
                'shares': shares,
                'profit': profit,
                'capital': capital
            })
            
            equity_curve[-1]['equity'] = capital
        
        # Metrikleri hesapla
        equity_df = pd.DataFrame(equity_curve)
        equity_df.set_index('date', inplace=True)
        
        # Toplam getiri
        total_return = (capital / self.initial_capital - 1) * 100
        
        # Günlük getiriler
        equity_df['returns'] = equity_df['equity'].pct_change()
        daily_returns = equity_df['returns'].dropna()
        
        # Sharpe Oranı (risk-free rate = 0 varsayımı)
        if len(daily_returns) > 0 and daily_returns.std() > 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)  # Yıllık
        else:
            sharpe_ratio = 0.0
        
        # Sortino Oranı (sadece negatif getirileri dikkate alır)
        negative_returns = daily_returns[daily_returns < 0]
        if len(negative_returns) > 0 and negative_returns.std() > 0:
            sortino_ratio = (daily_returns.mean() / negative_returns.std()) * np.sqrt(252)
        else:
            sortino_ratio = 0.0
        
        # Maksimum Düşüş (Max Drawdown)
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax']
        max_drawdown = equity_df['drawdown'].min() * 100  # Yüzde olarak
        
        # İşlem istatistikleri
        buy_trades = [t for t in trades if t['action'] == 'buy']
        sell_trades = [t for t in trades if t['action'] == 'sell']
        
        total_trades = len(buy_trades)
        winning_trades = len([t for t in sell_trades if t.get('profit', 0) > 0])
        losing_trades = len([t for t in sell_trades if t.get('profit', 0) < 0])
        
        if winning_trades + losing_trades > 0:
            win_rate = (winning_trades / (winning_trades + losing_trades)) * 100
        else:
            win_rate = 0.0
        
        total_profit = sum([t.get('profit', 0) for t in sell_trades])
        avg_profit = total_profit / len(sell_trades) if len(sell_trades) > 0 else 0.0
        
        # Buy and Hold karşılaştırması
        if len(price_df) > 0:
            buy_hold_return = ((price_df.iloc[-1]['close'] / price_df.iloc[0]['close']) - 1) * 100
        else:
            buy_hold_return = 0.0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'excess_return': total_return - buy_hold_return,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'trades': trades,
            'equity_curve': equity_df,
            'start_date': merged_df.index[0] if len(merged_df) > 0 else None,
            'end_date': merged_df.index[-1] if len(merged_df) > 0 else None
        }


def run_walk_forward_backtest(
    ticker: str,
    company_name: str,
    train_period: int = 252,  # 1 yıl (iş günü)
    test_period: int = 63,  # 3 ay
    step_size: int = 21,  # 1 ay
    sentiment_weight: float = 0.4,
    financial_weight: float = 0.6
) -> Dict:
    """
    Walk-Forward Validation ile backtest yapar (look-ahead bias'tan kaçınır).
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu
    company_name : str
        Şirket adı
    train_period : int
        Eğitim periyodu (iş günü sayısı)
    test_period : int
        Test periyodu (iş günü sayısı)
    step_size : int
        Her iterasyonda kaç gün ilerlenecek
    sentiment_weight : float
        Haber ağırlığı
    financial_weight : float
        Finansal ağırlık
    
    Döndürür:
    --------
    dict
        Walk-forward backtest sonuçları
    """
    
    print(f"\n{'='*60}")
    print(f"🔄 WALK-FORWARD BACKTEST BAŞLIYOR")
    print(f"{'='*60}\n")
    print(f"Ticker: {ticker}")
    print(f"Eğitim Periyodu: {train_period} iş günü (~{train_period/21:.1f} ay)")
    print(f"Test Periyodu: {test_period} iş günü (~{test_period/21:.1f} ay)")
    print(f"Adım Boyutu: {step_size} iş günü (~{step_size/21:.1f} ay)\n")
    
    # Fiyat verisini çek (yeterince uzun bir periyot)
    total_period = train_period + test_period + (step_size * 10)  # Yeterli veri için
    price_df = get_price_data(ticker, period=f"{int(total_period/252*12)}mo")
    
    if price_df.empty or len(price_df) < train_period + test_period:
        return {
            'error': f'Yeterli veri yok. Gerekli: {train_period + test_period} gün, Mevcut: {len(price_df)} gün'
        }
    
    # Walk-forward iterasyonları
    engine = BacktestEngine()
    all_results = []
    
    start_idx = train_period
    iteration = 0
    
    while start_idx + test_period <= len(price_df):
        iteration += 1
        train_end = start_idx
        test_start = start_idx
        test_end = min(start_idx + test_period, len(price_df))
        
        print(f"\n📊 İterasyon {iteration}")
        print(f"   Eğitim: {price_df.index[0]} - {price_df.index[train_end-1]}")
        print(f"   Test: {price_df.index[test_start]} - {price_df.index[test_end-1]}")
        
        # Test periyodu için sinyaller oluştur
        test_price_df = price_df.iloc[test_start:test_end].copy()
        signals_list = []
        
        for idx, row in test_price_df.iterrows():
            # O güne kadar olan verilerle analiz yap (look-ahead bias yok)
            historical_price = price_df.iloc[:test_start + list(test_price_df.index).index(idx)].copy()
            
            if len(historical_price) < 30:
                continue
            
            # Feature'ları hesapla
            price_with_features = compute_features(historical_price)
            feature_vector = create_feature_vector(price_with_features, None)
            
            # Haber analizi (son 30 gün)
            try:
                news_df = get_news(company_name, days_back=30, ticker=ticker)
                if not news_df.empty:
                    from src.sentiment_analysis import SentimentAnalyzer, analyze_news_sentiment
                    analyzer = SentimentAnalyzer()
                    news_with_sentiment = analyze_news_sentiment(news_df, analyzer)
                    sentiment_score = aggregate_sentiment(news_with_sentiment)
                else:
                    sentiment_score = 50.0
            except:
                sentiment_score = 50.0
            
            # Finansal skor
            from src.financial_analysis import compute_financial_score
            financial_score = compute_financial_score(feature_vector)
            
            # Genel skor
            overall_score = compute_overall_score(
                sentiment_score, financial_score,
                sentiment_weight, financial_weight
            )
            
            # Yön tahmini
            direction_pred = predict_direction(feature_vector)
            
            signals_list.append({
                'date': idx,
                'direction': direction_pred['direction'],
                'overall_score': overall_score,
                'confidence': direction_pred.get('confidence', 0.5)
            })
        
        if not signals_list:
            start_idx += step_size
            continue
        
        signals_df = pd.DataFrame(signals_list)
        signals_df.set_index('date', inplace=True)
        
        # Backtest çalıştır
        result = engine.run_backtest(
            test_price_df,
            signals_df,
            start_date=str(test_price_df.index[0]),
            end_date=str(test_price_df.index[-1])
        )
        
        if 'error' not in result:
            all_results.append(result)
            print(f"   ✅ Getiri: {result['total_return']:.2f}% | Sharpe: {result['sharpe_ratio']:.2f} | Max DD: {result['max_drawdown']:.2f}%")
        
        start_idx += step_size
    
    if not all_results:
        return {'error': 'Hiçbir iterasyon tamamlanamadı'}
    
    # Tüm iterasyonların ortalaması
    avg_return = np.mean([r['total_return'] for r in all_results])
    avg_sharpe = np.mean([r['sharpe_ratio'] for r in all_results])
    avg_max_dd = np.mean([r['max_drawdown'] for r in all_results])
    avg_win_rate = np.mean([r['win_rate'] for r in all_results])
    
    total_trades_all = sum([r['total_trades'] for r in all_results])
    
    return {
        'iterations': len(all_results),
        'avg_return': avg_return,
        'avg_sharpe_ratio': avg_sharpe,
        'avg_max_drawdown': avg_max_dd,
        'avg_win_rate': avg_win_rate,
        'total_trades': total_trades_all,
        'individual_results': all_results
    }


if __name__ == "__main__":
    # Test
    print("=== Backtesting Modülü Test ===\n")
    
    # Basit test
    test_price_data = pd.DataFrame({
        'close': [100, 105, 110, 108, 112, 115, 113, 118, 120, 125],
        'open': [100, 104, 109, 107, 111, 114, 112, 117, 119, 124],
        'high': [102, 106, 111, 109, 113, 116, 114, 119, 121, 126],
        'low': [99, 103, 108, 106, 110, 113, 111, 116, 118, 123],
        'volume': [1000] * 10
    }, index=pd.date_range('2024-01-01', periods=10, freq='D'))
    
    test_signals = pd.DataFrame({
        'direction': ['up', 'up', 'neutral', 'up', 'up', 'down', 'up', 'up', 'up', 'up'],
        'overall_score': [70, 75, 50, 65, 80, 40, 60, 75, 80, 85],
        'confidence': [0.7, 0.8, 0.5, 0.6, 0.9, 0.4, 0.7, 0.8, 0.9, 0.9]
    }, index=test_price_data.index)
    
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run_backtest(test_price_data, test_signals)
    
    print("Backtest Sonuçları:")
    print(f"  Toplam Getiri: {result['total_return']:.2f}%")
    print(f"  Sharpe Oranı: {result['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {result['max_drawdown']:.2f}%")
    print(f"  Toplam İşlem: {result['total_trades']}")
    print(f"  Kazanma Oranı: {result['win_rate']:.2f}%")

