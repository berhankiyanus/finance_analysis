"""
Model Eğitimi Scripti

Bu script, fiyat yönü tahmini için ML modeli eğitir.
"""

import sys
import os
import argparse
from pathlib import Path

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from src.prediction_model import train_price_direction_model


def main():
    parser = argparse.ArgumentParser(
        description='Fiyat yönü tahmini için ML modeli eğitir'
    )
    
    parser.add_argument(
        'ticker',
        type=str,
        help='Borsa kodu (örn: AAPL, MSFT, THYAO.IS)'
    )
    
    parser.add_argument(
        '--period',
        type=str,
        default='2y',
        help='Veri periyodu (varsayılan: 2y). Örnekler: 1y, 2y, 5y'
    )
    
    parser.add_argument(
        '--model-type',
        type=str,
        default='random_forest',
        choices=['random_forest', 'xgboost', 'gradient_boosting', 'logistic'],
        help='Model tipi (varsayılan: random_forest)'
    )
    
    parser.add_argument(
        '--future-days',
        type=int,
        default=5,
        help='Kaç gün sonrasını tahmin edeceğiz (varsayılan: 5)'
    )
    
    parser.add_argument(
        '--save-path',
        type=str,
        default=None,
        help='Model kayıt yolu (varsayılan: models/price_predictor_{ticker}.pkl)'
    )
    
    args = parser.parse_args()
    
    # Model kayıt yolu
    if args.save_path is None:
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        args.save_path = str(models_dir / f'price_predictor_{args.ticker.lower().replace(".", "_")}.pkl')
    
    try:
        # Modeli eğit
        predictor = train_price_direction_model(
            ticker=args.ticker,
            period=args.period,
            model_type=args.model_type,
            future_days=args.future_days,
            save_path=args.save_path
        )
        
        print(f"\n✅ Model başarıyla eğitildi ve kaydedildi: {args.save_path}")
        print(f"\n💡 Kullanım örneği:")
        print(f"   from src.prediction_model import PriceDirectionPredictor")
        print(f"   predictor = PriceDirectionPredictor(model_path='{args.save_path}')")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

