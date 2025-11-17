"""
Demo Modeller Eğitme Scripti

Birkaç popüler hisse için küçük demo modeller eğitir.
Bu script, projeyi ilk kez kullananlar için örnek modeller oluşturur.
"""

import sys
import os
from pathlib import Path

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prediction_model import train_price_direction_model, PriceDirectionPredictor
from src.data_collection import get_stock_data
from src.tcmb_data import get_policy_rate
from src.financial_analysis import create_features, create_feature_vector
from src.utils import ensure_directory_exists
import pandas as pd


def main():
    """Demo modelleri eğit"""
    
    # Demo hisseler (ABD ve Türk hisseleri)
    demo_tickers = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft Corporation"),
        ("THYAO.IS", "Türk Hava Yolları"),
    ]
    
    print("=" * 60)
    print("DEMO MODELLER EĞİTİLİYOR")
    print("=" * 60)
    print()
    
    # Models dizinini oluştur
    models_dir = ensure_directory_exists('models')
    
    trained_models = []
    failed_models = []
    
    for ticker, company_name in demo_tickers:
        print(f"\n📊 {ticker} ({company_name}) için model eğitiliyor...")
        
        try:
            model_path = models_dir / f"price_predictor_{ticker.lower().replace('.', '_')}.pkl"
            
            # 1. Veri çek
            print(f"   📥 Veri çekiliyor...")
            stock_df = get_stock_data(ticker, period="1y")
            if stock_df.empty:
                print(f"   ⚠️  {ticker} için veri bulunamadı, atlanıyor.")
                failed_models.append((ticker, "Veri bulunamadı"))
                continue
            
            # 2. TCMB verisi çek (Türk hisseleri için)
            tcmb_df = None
            if ticker.endswith('.IS') or len(ticker) == 5:
                print(f"   📥 TCMB verisi çekiliyor...")
                try:
                    tcmb_df = get_policy_rate(months=12)
                    if not tcmb_df.empty:
                        tcmb_df = tcmb_df.set_index('date')
                except Exception as e:
                    print(f"   ⚠️  TCMB verisi çekilemedi: {e}")
            
            # 3. Özellikleri oluştur
            print(f"   🔧 Özellikler oluşturuluyor...")
            features_df = create_features(stock_df, tcmb_df)
            
            # 4. Modeli eğit
            print(f"   🤖 Model eğitiliyor...")
            predictor = train_price_direction_model(
                ticker=ticker,
                period="1y",
                model_type="lightgbm" if ticker != "AAPL" else "random_forest",  # LightGBM varsa kullan
                future_days=5,
                save_path=str(model_path)
            )
            
            trained_models.append((ticker, str(model_path)))
            print(f"   ✅ Model başarıyla eğitildi: {model_path}")
            
        except Exception as e:
            failed_models.append((ticker, str(e)))
            print(f"   ❌ Model eğitimi başarısız: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Özet
    print("\n" + "=" * 60)
    print("EĞİTİM ÖZETİ")
    print("=" * 60)
    print(f"✅ Başarılı: {len(trained_models)} model")
    for ticker, path in trained_models:
        print(f"   - {ticker}: {path}")
    
    if failed_models:
        print(f"\n❌ Başarısız: {len(failed_models)} model")
        for ticker, error in failed_models:
            print(f"   - {ticker}: {error}")
    
    print("\n💡 Kullanım:")
    print("   Bu modeller app.py ve api/main.py tarafından otomatik olarak kullanılacak.")
    print("   Daha fazla hisse için: python train_model.py <TICKER> --period 2y")


if __name__ == "__main__":
    main()

