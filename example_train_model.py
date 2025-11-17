"""
Model Eğitimi Örnekleri

Bu dosya, farklı şirketler için model eğitimi örnekleri içerir.
"""

from src.prediction_model import train_price_direction_model, PriceDirectionPredictor
from src.data_collection import get_price_data
from src.financial_analysis import compute_features, create_feature_vector

def example_1_train_apple():
    """Apple için Random Forest modeli eğit"""
    print("="*60)
    print("ÖRNEK 1: Apple için Random Forest Modeli")
    print("="*60)
    
    predictor = train_price_direction_model(
        ticker="AAPL",
        period="2y",
        model_type="random_forest",
        future_days=5,
        save_path="models/price_predictor_aapl.pkl"
    )
    
    print("\n✅ Model eğitildi ve kaydedildi!")
    return predictor


def example_2_train_microsoft():
    """Microsoft için XGBoost modeli eğit"""
    print("="*60)
    print("ÖRNEK 2: Microsoft için XGBoost Modeli")
    print("="*60)
    
    predictor = train_price_direction_model(
        ticker="MSFT",
        period="2y",
        model_type="xgboost",
        future_days=5,
        save_path="models/price_predictor_msft.pkl"
    )
    
    print("\n✅ Model eğitildi ve kaydedildi!")
    return predictor


def example_3_use_trained_model():
    """Eğitilmiş modeli kullan"""
    print("="*60)
    print("ÖRNEK 3: Eğitilmiş Modeli Kullanma")
    print("="*60)
    
    # Modeli yükle
    predictor = PriceDirectionPredictor(model_path="models/price_predictor_aapl.pkl")
    
    # Güncel veri al
    price_df = get_price_data("AAPL", period="1y")
    price_df_feat = compute_features(price_df)
    feature_vector = create_feature_vector(price_df_feat)
    
    # Tahmin yap
    prediction = predictor.predict(feature_vector)
    
    print(f"\n🔮 Tahmin Sonuçları:")
    print(f"   Yön: {prediction['direction']}")
    print(f"   Güven: {prediction['confidence']:.2%}")
    print(f"   Olasılıklar:")
    for direction, prob in prediction['probabilities'].items():
        print(f"     {direction}: {prob:.2%}")


def example_4_feature_importance():
    """Feature importance analizi"""
    print("="*60)
    print("ÖRNEK 4: Feature Importance Analizi")
    print("="*60)
    
    predictor = PriceDirectionPredictor(model_path="models/price_predictor_aapl.pkl")
    importance_df = predictor.get_feature_importance()
    
    print("\n📊 En Önemli 15 Feature:")
    print(importance_df.head(15).to_string(index=False))


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_num = sys.argv[1]
    else:
        print("Kullanım: python3 example_train_model.py <örnek_numara>")
        print("\nÖrnekler:")
        print("  1 - Apple için Random Forest modeli eğit")
        print("  2 - Microsoft için XGBoost modeli eğit")
        print("  3 - Eğitilmiş modeli kullan")
        print("  4 - Feature importance analizi")
        sys.exit(0)
    
    if example_num == "1":
        example_1_train_apple()
    elif example_num == "2":
        example_2_train_microsoft()
    elif example_num == "3":
        example_3_use_trained_model()
    elif example_num == "4":
        example_4_feature_importance()
    else:
        print(f"Bilinmeyen örnek: {example_num}")

