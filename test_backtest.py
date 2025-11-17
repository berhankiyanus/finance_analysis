"""
Backtesting Test Script

Bu script, backtesting modülünü test eder ve örnek sonuçlar gösterir.
"""

import sys
from pathlib import Path

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from src.backtesting import BacktestEngine, run_walk_forward_backtest
import pandas as pd

def test_simple_backtest():
    """Basit backtest testi"""
    print("="*60)
    print("TEST 1: Basit Backtest")
    print("="*60)
    
    # Test verisi oluştur
    test_price_data = pd.DataFrame({
        'close': [100, 105, 110, 108, 112, 115, 113, 118, 120, 125, 130, 128, 132, 135, 140],
        'open': [100, 104, 109, 107, 111, 114, 112, 117, 119, 124, 129, 127, 131, 134, 139],
        'high': [102, 106, 111, 109, 113, 116, 114, 119, 121, 126, 131, 129, 133, 136, 141],
        'low': [99, 103, 108, 106, 110, 113, 111, 116, 118, 123, 128, 126, 130, 133, 138],
        'volume': [1000] * 15
    }, index=pd.date_range('2024-01-01', periods=15, freq='D'))
    
    test_signals = pd.DataFrame({
        'direction': ['up', 'up', 'neutral', 'up', 'up', 'down', 'up', 'up', 'up', 'up', 'up', 'up', 'up', 'up', 'up'],
        'overall_score': [70, 75, 50, 65, 80, 40, 60, 75, 80, 85, 80, 75, 85, 90, 95],
        'confidence': [0.7, 0.8, 0.5, 0.6, 0.9, 0.4, 0.7, 0.8, 0.9, 0.9, 0.8, 0.7, 0.9, 0.95, 0.95]
    }, index=test_price_data.index)
    
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run_backtest(test_price_data, test_signals)
    
    print("\n📊 Backtest Sonuçları:")
    print(f"  Başlangıç Sermayesi: {result['initial_capital']:,.2f} TL")
    print(f"  Final Sermayesi: {result['final_capital']:,.2f} TL")
    print(f"  Toplam Getiri: {result['total_return']:.2f}%")
    print(f"  Buy & Hold Getiri: {result['buy_hold_return']:.2f}%")
    print(f"  Fazla Getiri: {result['excess_return']:.2f}%")
    print(f"  Sharpe Oranı: {result['sharpe_ratio']:.2f}")
    print(f"  Sortino Oranı: {result['sortino_ratio']:.2f}")
    print(f"  Max Drawdown: {result['max_drawdown']:.2f}%")
    print(f"  Toplam İşlem: {result['total_trades']}")
    print(f"  Kazanan İşlem: {result['winning_trades']}")
    print(f"  Kaybeden İşlem: {result['losing_trades']}")
    print(f"  Kazanma Oranı: {result['win_rate']:.2f}%")
    print(f"  Toplam Kâr: {result['total_profit']:,.2f} TL")
    print(f"  Ortalama Kâr: {result['avg_profit']:,.2f} TL")
    
    if result['trades']:
        print("\n📈 İşlemler:")
        for i, trade in enumerate(result['trades'][:5], 1):  # İlk 5 işlem
            print(f"  {i}. {trade['date']} - {trade['action'].upper()}: {trade.get('shares', 0):.2f} hisse @ {trade['price']:.2f} TL")
            if 'profit' in trade:
                print(f"     Kâr/Zarar: {trade['profit']:,.2f} TL")
    
    print("\n✅ Basit backtest testi tamamlandı!\n")


def test_walk_forward_backtest():
    """Walk-forward backtest testi (gerçek veri ile)"""
    print("="*60)
    print("TEST 2: Walk-Forward Backtest (Gerçek Veri)")
    print("="*60)
    print("\n⚠️  Bu test gerçek API çağrıları yapar ve zaman alabilir.\n")
    
    # Kullanıcıdan onay al
    response = input("Devam etmek istiyor musunuz? (e/h): ")
    if response.lower() != 'e':
        print("Test atlandı.")
        return
    
    try:
        result = run_walk_forward_backtest(
            ticker="AAPL",
            company_name="Apple",
            train_period=126,  # 6 ay
            test_period=21,  # 1 ay
            step_size=21  # 1 ay
        )
        
        if 'error' in result:
            print(f"❌ Hata: {result['error']}")
            return
        
        print("\n📊 Walk-Forward Backtest Sonuçları:")
        print(f"  Toplam İterasyon: {result['iterations']}")
        print(f"  Ortalama Getiri: {result['avg_return']:.2f}%")
        print(f"  Ortalama Sharpe Oranı: {result['avg_sharpe_ratio']:.2f}")
        print(f"  Ortalama Max Drawdown: {result['avg_max_drawdown']:.2f}%")
        print(f"  Ortalama Kazanma Oranı: {result['avg_win_rate']:.2f}%")
        print(f"  Toplam İşlem: {result['total_trades']}")
        
        print("\n✅ Walk-forward backtest testi tamamlandı!\n")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BACKTESTING MODÜLÜ TEST SÜİTİ")
    print("="*60 + "\n")
    
    # Test 1: Basit backtest
    test_simple_backtest()
    
    # Test 2: Walk-forward backtest (opsiyonel)
    print("\n" + "="*60)
    test_walk_forward_backtest()

