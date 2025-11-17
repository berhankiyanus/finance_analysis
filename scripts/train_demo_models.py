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

from src.prediction_model import train_price_direction_model
from src.utils import ensure_directory_exists


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
            
            # Modeli eğit (kısa periyot - demo için)
            predictor = train_price_direction_model(
                ticker=ticker,
                period="1y",  # Demo için kısa periyot
                model_type="random_forest",
                future_days=5,
                save_path=str(model_path)
            )
            
            trained_models.append((ticker, str(model_path)))
            print(f"   ✅ Model başarıyla eğitildi: {model_path}")
            
        except Exception as e:
            failed_models.append((ticker, str(e)))
            print(f"   ❌ Model eğitimi başarısız: {e}")
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

