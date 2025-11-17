"""
FastAPI Servisi

Streamlit uygulamasındaki prediction_model.py'yi API servisine dönüştürür.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import sys
from pathlib import Path

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.prediction_model import PriceDirectionPredictor
from src.financial_analysis import create_feature_vector
from src.data_collection import get_price_data
from src.financial_analysis import compute_features

app = FastAPI(
    title="AI Borsa Analisti API",
    description="Finansal analiz ve fiyat yönü tahmini için REST API",
    version="1.0.0"
)


class PredictionRequest(BaseModel):
    """Tahmin isteği modeli"""
    hisse_kodu: str
    company_name: Optional[str] = None
    use_model: bool = True  # ML modeli kullanılsın mı?


class PredictionResponse(BaseModel):
    """Tahmin yanıt modeli"""
    hisse_kodu: str
    tahmin_sinyal: str  # 'AL', 'SAT', 'TUT'
    skor: float  # 0-100 arası
    guven: str  # 'Yüksek', 'Orta', 'Düşük'
    confidence: float  # 0-1 arası
    direction: Optional[str] = None  # 'up', 'down', 'neutral'
    probabilities: Optional[Dict[str, float]] = None
    feature_vector: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


@app.get("/")
async def root():
    """API kök endpoint'i"""
    return {
        "message": "AI Borsa Analisti API",
        "version": "1.0.0",
        "endpoints": {
            "/predict": "POST - Fiyat yönü tahmini",
            "/health": "GET - API sağlık kontrolü"
        }
    }


@app.get("/health")
async def health_check():
    """API sağlık kontrolü"""
    return {
        "status": "healthy",
        "message": "API çalışıyor"
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_direction(request: PredictionRequest):
    """
    Fiyat yönü tahmini yapar.
    
    Parametreler:
    ------------
    request : PredictionRequest
        Tahmin isteği (hisse_kodu, company_name, use_model)
    
    Döndürür:
    --------
    PredictionResponse
        Tahmin sonuçları (sinyal, skor, güven, vb.)
    """
    
    try:
        ticker = request.hisse_kodu.upper()
        company_name = request.company_name or ticker
        
        # 1. Fiyat verisini çek
        try:
            price_df = get_price_data(ticker, period="1y")
            if price_df.empty:
                raise HTTPException(
                    status_code=404,
                    detail=f"{ticker} için fiyat verisi bulunamadı."
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Fiyat verisi çekilirken hata: {str(e)}"
            )
        
        # 2. Feature'ları hesapla
        try:
            price_df_with_features = compute_features(price_df)
            feature_vector = create_feature_vector(price_df_with_features)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Feature hesaplama hatası: {str(e)}"
            )
        
        # 3. Model tahmini (eğer isteniyorsa)
        if request.use_model:
            model_path = f"models/price_predictor_{ticker.lower().replace('.', '_')}.pkl"
            
            if os.path.exists(model_path):
                try:
                    predictor = PriceDirectionPredictor(model_path=model_path)
                    prediction = predictor.predict(feature_vector)
                    
                    direction = prediction.get('direction', 'neutral')
                    confidence = prediction.get('confidence', 0.5)
                    probabilities = prediction.get('probabilities', {})
                    
                    # Sinyal belirleme
                    if direction == 'up':
                        tahmin_sinyal = 'AL'
                    elif direction == 'down':
                        tahmin_sinyal = 'SAT'
                    else:
                        tahmin_sinyal = 'TUT'
                    
                    # Güven seviyesi
                    if confidence >= 0.7:
                        guven = 'Yüksek'
                    elif confidence >= 0.5:
                        guven = 'Orta'
                    else:
                        guven = 'Düşük'
                    
                    # Skor (confidence'den türet)
                    skor = confidence * 100
                    
                    return PredictionResponse(
                        hisse_kodu=ticker,
                        tahmin_sinyal=tahmin_sinyal,
                        skor=skor,
                        guven=guven,
                        confidence=confidence,
                        direction=direction,
                        probabilities=probabilities,
                        feature_vector=feature_vector,
                        message=f"Model tahmini: {direction} (güven: {confidence:.1%})"
                    )
                    
                except Exception as e:
                    # Model hatası - rule-based fallback
                    return _rule_based_prediction(ticker, feature_vector, str(e))
            else:
                # Model yok - rule-based fallback
                return _rule_based_prediction(
                    ticker, 
                    feature_vector, 
                    f"Model bulunamadı: {model_path}"
                )
        else:
            # Model kullanılmayacak - rule-based
            return _rule_based_prediction(ticker, feature_vector, "Model kullanımı kapalı")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tahmin yapılırken hata: {str(e)}"
        )


def _rule_based_prediction(ticker: str, feature_vector: Dict, reason: str) -> PredictionResponse:
    """
    Kural tabanlı tahmin (model yoksa veya hata varsa).
    """
    # Basit kural tabanlı mantık
    rsi = feature_vector.get('rsi_14', 50)
    macd = feature_vector.get('macd', 0)
    return_30d = feature_vector.get('return_30d', 0)
    
    # Sinyal belirleme
    if rsi < 30 and macd > 0 and return_30d < -5:
        tahmin_sinyal = 'AL'  # Aşırı satım, alım fırsatı
        skor = 65.0
        guven = 'Orta'
        confidence = 0.65
        direction = 'up'
    elif rsi > 70 and macd < 0 and return_30d > 5:
        tahmin_sinyal = 'SAT'  # Aşırı alım, satım sinyali
        skor = 35.0
        guven = 'Orta'
        confidence = 0.35
        direction = 'down'
    else:
        tahmin_sinyal = 'TUT'  # Bekle ve gör
        skor = 50.0
        guven = 'Düşük'
        confidence = 0.5
        direction = 'neutral'
    
    return PredictionResponse(
        hisse_kodu=ticker,
        tahmin_sinyal=tahmin_sinyal,
        skor=skor,
        guven=guven,
        confidence=confidence,
        direction=direction,
        probabilities=None,
        feature_vector=feature_vector,
        message=f"Kural tabanlı tahmin (Model kullanılamadı: {reason})"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

