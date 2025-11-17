"""
Model Açıklanabilirliği Modülü

Bu modül, SHAP ve LIME kullanarak model tahminlerini açıklar.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️  SHAP yüklü değil. Model açıklanabilirliği sınırlı olacak.")
    print("   Yüklemek için: pip install shap")

try:
    import lime
    import lime.lime_tabular
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    print("⚠️  LIME yüklü değil. LIME açıklamaları kullanılamayacak.")
    print("   Yüklemek için: pip install lime")


def explain_prediction_shap(
    model,
    feature_vector: Dict,
    feature_names: List[str],
    scaler,
    background_data: Optional[np.ndarray] = None,
    model_type: str = "random_forest"
) -> Dict:
    """
    SHAP kullanarak tahmin açıklaması yapar.
    
    Parametreler:
    ------------
    model : object
        Eğitilmiş ML modeli
    feature_vector : dict
        Feature vektörü
    feature_names : list
        Feature isimleri listesi
    scaler : object
        Feature scaler
    background_data : np.ndarray, optional
        Background veri (SHAP için referans)
    model_type : str
        Model tipi
    
    Döndürür:
    --------
    dict
        SHAP değerleri ve açıklamalar
    """
    
    if not SHAP_AVAILABLE:
        return {
            'error': 'SHAP yüklü değil',
            'shap_values': {},
            'top_features': []
        }
    
    try:
        # Feature vektörünü array'e çevir
        X = np.array([[feature_vector.get(name, 0) for name in feature_names]])
        X_scaled = scaler.transform(X)
        
        # Background data hazırla
        if background_data is None:
            # Basit background: feature_vector'ın etrafında küçük varyasyonlar
            background_size = 50
            background = np.random.normal(
                loc=X_scaled[0],
                scale=0.1,
                size=(background_size, len(feature_names))
            )
        else:
            background = background_data
        
        # SHAP explainer oluştur
        if model_type in ['random_forest', 'xgboost', 'gradient_boosting']:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_scaled)
            
            # Multi-class için en yüksek sınıfın SHAP değerlerini al
            if isinstance(shap_values, list):
                # En yüksek olasılıklı sınıfı bul
                prediction = model.predict(X_scaled)[0]
                class_idx = list(model.classes_).index(prediction)
                shap_values = shap_values[class_idx]
            
            shap_values = shap_values[0]  # İlk örnek
        else:
            # Diğer modeller için KernelExplainer
            explainer = shap.KernelExplainer(
                model.predict_proba,
                background
            )
            shap_values = explainer.shap_values(X_scaled[0])
            
            # En yüksek olasılıklı sınıf için SHAP değerleri
            if isinstance(shap_values, list):
                prediction = model.predict(X_scaled)[0]
                class_idx = list(model.classes_).index(prediction)
                shap_values = shap_values[class_idx]
        
        # Feature isimleri ile eşleştir
        shap_dict = {
            name: float(value)
            for name, value in zip(feature_names, shap_values)
        }
        
        # En önemli feature'ları sırala
        sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        
        return {
            'shap_values': shap_dict,
            'top_features': sorted_features[:10],  # En önemli 10 feature
            'feature_names': feature_names,
            'feature_values': {name: feature_vector.get(name, 0) for name in feature_names}
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'shap_values': {},
            'top_features': []
        }


def explain_prediction_lime(
    model,
    feature_vector: Dict,
    feature_names: List[str],
    scaler,
    training_data: np.ndarray,
    num_features: int = 10
) -> Dict:
    """
    LIME kullanarak tahmin açıklaması yapar.
    
    Parametreler:
    ------------
    model : object
        Eğitilmiş ML modeli
    feature_vector : dict
        Feature vektörü
    feature_names : list
        Feature isimleri listesi
    scaler : object
        Feature scaler
    training_data : np.ndarray
        Eğitim verisi (LIME için gerekli)
    num_features : int
        Gösterilecek feature sayısı
    
    Döndürür:
    --------
    dict
        LIME açıklamaları
    """
    
    if not LIME_AVAILABLE:
        return {
            'error': 'LIME yüklü değil',
            'explanations': []
        }
    
    try:
        # Feature vektörünü array'e çevir
        X = np.array([[feature_vector.get(name, 0) for name in feature_names]])
        X_scaled = scaler.transform(X)
        
        # LIME explainer oluştur
        explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data,
            feature_names=feature_names,
            mode='classification',
            discretize_continuous=True
        )
        
        # Açıklama yap
        explanation = explainer.explain_instance(
            X_scaled[0],
            model.predict_proba,
            num_features=num_features
        )
        
        # Açıklamaları dict'e çevir
        explanations = []
        for feature, weight in explanation.as_list():
            explanations.append({
                'feature': feature,
                'weight': float(weight)
            })
        
        return {
            'explanations': explanations,
            'top_features': explanations[:num_features]
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'explanations': []
        }


def format_explanation_for_display(shap_result: Dict, prediction: Dict) -> str:
    """
    SHAP sonuçlarını kullanıcı dostu formatta gösterir.
    
    Parametreler:
    ------------
    shap_result : dict
        SHAP açıklama sonuçları
    prediction : dict
        Model tahmini
    
    Döndürür:
    --------
    str
        Formatlanmış açıklama metni
    """
    
    if 'error' in shap_result or not shap_result.get('top_features'):
        return "Model açıklaması mevcut değil."
    
    direction = prediction.get('direction', 'neutral')
    confidence = prediction.get('confidence', 0.0)
    
    # Yön çevirisi
    direction_map = {
        'up': 'YÜKSELİŞ',
        'down': 'DÜŞÜŞ',
        'neutral': 'NÖTR'
    }
    direction_tr = direction_map.get(direction, direction.upper())
    
    lines = [
        f"**Model Tahmini:** {direction_tr} ({confidence:.1%} güven)",
        "",
        "**En Önemli Etkenler:**"
    ]
    
    # Top 5 feature'ı göster
    for i, (feature, shap_value) in enumerate(shap_result['top_features'][:5], 1):
        feature_value = shap_result['feature_values'].get(feature, 0)
        impact_pct = abs(shap_value) / sum(abs(v) for _, v in shap_result['top_features']) * 100
        
        # Etki yönü
        if shap_value > 0:
            impact_direction = "📈 Pozitif etki"
        else:
            impact_direction = "📉 Negatif etki"
        
        lines.append(
            f"{i}. **{feature}**: {impact_direction} ({impact_pct:.1f}% etki)\n"
            f"   Mevcut değer: {feature_value:.2f}"
        )
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Model Açıklanabilirliği Modülü Test ===\n")
    
    if SHAP_AVAILABLE:
        print("✅ SHAP yüklü")
    else:
        print("❌ SHAP yüklü değil")
    
    if LIME_AVAILABLE:
        print("✅ LIME yüklü")
    else:
        print("❌ LIME yüklü değil")

