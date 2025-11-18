"""
FastAPI Servisi

Streamlit uygulamasındaki prediction_model.py'yi API servisine dönüştürür.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys
from pathlib import Path
import pandas as pd

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.prediction_model import PriceDirectionPredictor
from src.financial_analysis import create_feature_vector, create_features
from src.data_collection import get_price_data, get_news, get_stock_data
from src.financial_analysis import compute_features
from src.tcmb_data import get_policy_rate
from src.main import analyze_company
from src.scoring import generate_detailed_report
from src.utils import ensure_directory_exists
import os

app = FastAPI(
    title="AI Borsa Analisti API",
    description="Finansal analiz ve fiyat yönü tahmini için REST API",
    version="1.0.0"
)

# Global model cache (uygulama başlarken yüklenecek)
demo_model = None
demo_model_path = None

@app.on_event("startup")
async def load_demo_model():
    """Uygulama başlarken demo modelini yükle"""
    global demo_model, demo_model_path
    
    # Models dizinini oluştur
    ensure_directory_exists('models')
    
    # Demo model dosyasını bul (THYAO için)
    possible_paths = [
        "models/price_predictor_thyao_is.pkl",
        "models/price_predictor_thyao.pkl",
        "models/demo_model.pkl"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                demo_model = PriceDirectionPredictor(model_path=path)
                demo_model_path = path
                print(f"✅ Demo model yüklendi: {path}")
                break
            except Exception as e:
                print(f"⚠️  Model yüklenemedi ({path}): {e}")
    
    if demo_model is None:
        print("⚠️  Demo model bulunamadı. Rule-based fallback kullanılacak.")


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
            "/analyze/{hisse_kodu}": "POST - Tam analiz (veri toplama, sentiment, prediction, SHAP, Gemini)",
            "/optimize_portfolio": "POST - Portföy optimizasyonu",
            "/report/{hisse_kodu}": "GET - Analist raporu",
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
            if price_df_with_features.empty:
                raise HTTPException(
                    status_code=500,
                    detail="Feature hesaplama sonrası DataFrame boş."
                )
            feature_vector = create_feature_vector(price_df_with_features)
            if not feature_vector:
                raise HTTPException(
                    status_code=500,
                    detail="Feature vektörü oluşturulamadı (boş)."
                )
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            error_detail = f"Feature hesaplama hatası: {str(e)}\n{traceback.format_exc()}"
            print(f"❌ {error_detail}")  # Console'a yazdır
            raise HTTPException(
                status_code=500,
                detail=f"Feature hesaplama hatası: {str(e)}"
            )
        
        # 3. Model tahmini (eğer isteniyorsa)
        if request.use_model:
            # Önce demo_model'i dene (startup'ta yüklenmişse)
            predictor = None
            prediction = None
            if demo_model is not None:
                try:
                    predictor = demo_model
                    prediction = predictor.predict(feature_vector)
                    print(f"✅ Demo model tahmini başarılı: {prediction}")
                except Exception as e:
                    import traceback
                    print(f"⚠️  Demo model hatası: {e}\n{traceback.format_exc()}")
                    predictor = None
                    prediction = None
            
            # Demo model çalışmadıysa, ticker'a özel modeli dene
            if predictor is None:
                model_path = f"models/price_predictor_{ticker.lower().replace('.', '_')}.pkl"
                
                if os.path.exists(model_path):
                    try:
                        predictor = PriceDirectionPredictor(model_path=model_path)
                        prediction = predictor.predict(feature_vector)
                        print(f"✅ Ticker model tahmini başarılı: {prediction}")
                    except Exception as e:
                        import traceback
                        error_msg = f"Model hatası: {str(e)}\n{traceback.format_exc()}"
                        print(f"❌ {error_msg}")
                        # Model hatası - rule-based fallback
                        return _rule_based_prediction(ticker, feature_vector, f"Model hatası: {str(e)}")
                else:
                    # Model yok - rule-based fallback
                    return _rule_based_prediction(
                        ticker, 
                        feature_vector, 
                        f"Model bulunamadı: {model_path}. Model eğitmek için: python train_model.py {ticker} --period 2y"
                    )
            
            # Prediction başarılıysa devam et
            if predictor is not None and prediction is not None:
                # Numpy tiplerini Python native tiplerine çevir
                direction_raw = prediction.get('direction', 'neutral')
                direction = str(direction_raw) if direction_raw is not None else 'neutral'
                
                confidence_raw = prediction.get('confidence', 0.5)
                confidence = float(confidence_raw) if confidence_raw is not None else 0.5
                
                probabilities_raw = prediction.get('probabilities', {})
                # Probabilities dictionary'sindeki key'leri ve value'ları Python native yap
                probabilities = {}
                if probabilities_raw:
                    for key, value in probabilities_raw.items():
                        key_str = str(key)  # numpy string'i normal string'e çevir
                        value_float = float(value)  # numpy float'ı normal float'a çevir
                        probabilities[key_str] = value_float
                
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
                skor = float(confidence * 100)
                
                # Feature vector'daki numpy tiplerini de temizle
                feature_vector_clean = {}
                if feature_vector:
                    import numpy as np
                    for key, value in feature_vector.items():
                        if isinstance(value, (np.integer, np.int64, np.int32)):
                            feature_vector_clean[key] = int(value)
                        elif isinstance(value, (np.floating, np.float64, np.float32)):
                            feature_vector_clean[key] = float(value)
                        elif isinstance(value, np.str_):
                            feature_vector_clean[key] = str(value)
                        else:
                            feature_vector_clean[key] = value
                
                return PredictionResponse(
                    hisse_kodu=ticker,
                    tahmin_sinyal=tahmin_sinyal,
                    skor=skor,
                    guven=guven,
                    confidence=confidence,
                    direction=direction,
                    probabilities=probabilities,
                    feature_vector=feature_vector_clean,
                    message=f"Model tahmini: {direction} (güven: {confidence:.1%})"
                )
        else:
            # Model kullanılmayacak - rule-based
            return _rule_based_prediction(ticker, feature_vector, "Model kullanımı kapalı")
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_detail = f"Tahmin yapılırken hata: {str(e)}\n\nTraceback:\n{error_trace}"
        print(f"❌ API HATASI:\n{error_detail}")  # Console'a yazdır
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


@app.post("/analyze/{hisse_kodu}")
async def analyze_stock(hisse_kodu: str, company_name: Optional[str] = None, days_back: int = 30):
    """
    Belirtilen hisse için tam analiz yapar.
    
    Bu endpoint, data_collection, sentiment_analysis, prediction_model, 
    explainability ve gemini_reporting modüllerini sırayla çalıştırır.
    
    Parametreler:
    ------------
    hisse_kodu : str
        Borsa kodu (örn: "THYAO", "AAPL")
    company_name : str, optional
        Şirket adı (otomatik bulunamazsa)
    days_back : int
        Kaç gün geriye gidilecek (haberler için, varsayılan: 30)
    
    Döndürür:
    --------
    dict
        Tam analiz sonuçları: {
            'price_data': {...},
            'news_data': {...},
            'sentiment_scores': {...},
            'prediction': {...},
            'shap_explanation': {...},
            'gemini_report': {...},
            'scores': {...}
        }
    """
    
    try:
        ticker = hisse_kodu.upper()
        company_name = company_name or ticker
        
        # 1. Veri toplama
        from src.data_collection import get_all_data_for_stock
        all_data = get_all_data_for_stock(
            ticker=ticker,
            company_name=company_name,
            period="1y",
            days_back=days_back,
            include_kap=True,
            include_google_search=True,
            include_macro=True
        )
        
        # 2. Tam analiz (main.py'deki analyze_company fonksiyonu)
        results = analyze_company(
            company_name=company_name,
            ticker=ticker,
            days_back=days_back
        )
        
        # 3. SHAP açıklaması (eğer model varsa)
        shap_explanation = None
        model_path = f"models/price_predictor_{ticker.lower().replace('.', '_')}.pkl"
        if os.path.exists(model_path):
            try:
                predictor = PriceDirectionPredictor(model_path=model_path)
                feature_vector = results.get('feature_vector', {})
                if feature_vector:
                    shap_explanation = predictor.explain_prediction_shap(feature_vector)
            except Exception as e:
                shap_explanation = {"error": str(e)}
        
        # 4. Response oluştur
        return {
            "hisse_kodu": ticker,
            "company_name": company_name,
            "data": {
                "price_data": {
                    "rows": len(all_data.get('price_df', pd.DataFrame())),
                    "latest_price": float(all_data['price_df'].iloc[-1]['close']) if not all_data.get('price_df', pd.DataFrame()).empty else None
                },
                "news_data": {
                    "total_news": len(all_data.get('news_df', pd.DataFrame())),
                    "kap_reports": len(all_data.get('kap_reports', [])),
                    "google_news": len(all_data.get('google_news', []))
                },
                "macro_data": {
                    "indicators_count": len(all_data.get('macro_data', {}))
                }
            },
            "sentiment_scores": {
                "hisse_duygu_skoru": results.get('sentiment_score', 0),
                "piyasa_duygu_skoru": results.get('macro_data', {}).get('piyasa_duygu_skoru', 50.0) if isinstance(results.get('macro_data'), dict) else 50.0
            },
            "prediction": results.get('direction_prediction', {}),
            "shap_explanation": shap_explanation,
            "gemini_report": {
                "analyst_report": results.get('detailed_report', {}).get('gemini_analyst_report', ''),
                "hisse_news_summary": results.get('detailed_report', {}).get('hisse_news_summary', ''),
                "piyasa_news_summary": results.get('detailed_report', {}).get('piyasa_news_summary', '')
            },
            "scores": {
                "sentiment_score": results.get('sentiment_score', 0),
                "financial_score": results.get('financial_score', 0),
                "overall_score": results.get('overall_score', 0)
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analiz yapılırken hata: {str(e)}"
        )


@app.post("/optimize_portfolio")
async def optimize_portfolio(request: Dict[str, Any]):
    """
    Portföy optimizasyonu yapar.
    
    Parametreler:
    ------------
    request : dict
        {
            "tickers": ["THYAO", "EREGL", "TUPRS"],
            "optimization_type": "max_sharpe" veya "min_volatility",
            "risk_free_rate": 0.02 (opsiyonel),
            "total_portfolio_value": 100000.0 (opsiyonel)
        }
    
    Döndürür:
    --------
    dict
        Optimal portföy ağırlıkları ve metrikler
    """
    
    try:
        from src.portfolio_optimization import calculate_optimal_portfolio_weights
        from src.data_collection import get_price_data
        import pandas as pd
        
        tickers = request.get('tickers', [])
        if not tickers:
            raise HTTPException(
                status_code=400,
                detail="tickers listesi boş olamaz"
            )
        
        optimization_type = request.get('optimization_type', 'max_sharpe')
        risk_free_rate = request.get('risk_free_rate', 0.02)
        total_portfolio_value = request.get('total_portfolio_value', 100000.0)
        
        # Fiyat verilerini topla
        price_data_dict = {}
        for ticker in tickers:
            ticker_clean = ticker.strip().upper()
            # Türk hisseleri için .IS ekle
            ticker_for_yfinance = ticker_clean
            if len(ticker_clean) == 5 and not ticker_clean.endswith('.IS'):
                ticker_for_yfinance = f"{ticker_clean}.IS"
            
            try:
                price_df = get_price_data(ticker_for_yfinance, period="1y")
                if not price_df.empty:
                    price_data_dict[ticker_clean] = price_df['close']
            except Exception as e:
                print(f"⚠️  {ticker_clean} fiyat verisi çekilemedi: {e}")
        
        if not price_data_dict:
            raise HTTPException(
                status_code=404,
                detail="Hiçbir hisse için fiyat verisi bulunamadı"
            )
        
        # DataFrame oluştur
        price_data_df = pd.DataFrame(price_data_dict)
        
        # Optimizasyon yap
        result = calculate_optimal_portfolio_weights(
            price_data=price_data_df,
            risk_free_rate=risk_free_rate,
            optimization_type=optimization_type,
            total_portfolio_value=total_portfolio_value
        )
        
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        return {
            "tickers": tickers,
            "optimization_type": result.get('optimization_type', optimization_type),
            "weights": result.get('weights', {}),
            "metrics": {
                "expected_annual_return": result.get('expected_annual_return', 0),
                "annual_volatility": result.get('annual_volatility', 0),
                "sharpe_ratio": result.get('sharpe_ratio', 0)
            },
            "discrete_allocations": result.get('discrete_allocations', {}),
            "remaining_cash": result.get('remaining_cash', 0)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Portföy optimizasyonu yapılırken hata: {str(e)}"
        )


@app.get("/report/{hisse_kodu}")
async def get_analyst_report(hisse_kodu: str, company_name: Optional[str] = None):
    """
    Belirtilen hisse için detaylı analist raporu döner.
    
    Parametreler:
    ------------
    hisse_kodu : str
        Borsa kodu (örn: "THYAO", "AAPL")
    company_name : str, optional
        Şirket adı (otomatik bulunamazsa)
    
    Döndürür:
    --------
    dict
        Detaylı analist raporu (Gemini AI ile oluşturulmuş)
    """
    
    try:
        ticker = hisse_kodu.upper()
        company_name = company_name or ticker
        
        # Tam analiz yap
        results = analyze_company(
            company_name=company_name,
            ticker=ticker,
            days_back=30
        )
        
        # Detaylı rapor varsa döndür
        if 'detailed_report' in results and results['detailed_report']:
            detailed_report = results['detailed_report']
            
            return {
                "hisse_kodu": ticker,
                "company_name": company_name,
                "report": {
                    "summary": detailed_report.get('summary', ''),
                    "gemini_analyst_report": detailed_report.get('gemini_analyst_report', ''),
                    "hisse_news_summary": detailed_report.get('hisse_news_summary', ''),
                    "piyasa_news_summary": detailed_report.get('piyasa_news_summary', ''),
                    "news_analysis": detailed_report.get('news_analysis', []),
                    "financial_analysis": detailed_report.get('financial_analysis', []),
                    "recommendation_reasons": detailed_report.get('recommendation_reasons', []),
                    "key_factors": detailed_report.get('key_factors', [])
                },
                "scores": {
                    "sentiment_score": results.get('sentiment_score', 0),
                    "financial_score": results.get('financial_score', 0),
                    "overall_score": results.get('overall_score', 0)
                },
                "prediction": results.get('direction_prediction', {})
            }
        else:
            # Basit rapor
            return {
                "hisse_kodu": ticker,
                "company_name": company_name,
                "report": {
                    "summary": results.get('summary', 'Rapor oluşturulamadı.'),
                    "gemini_analyst_report": None
                },
                "scores": {
                    "sentiment_score": results.get('sentiment_score', 0),
                    "financial_score": results.get('financial_score', 0),
                    "overall_score": results.get('overall_score', 0)
                },
                "prediction": results.get('direction_prediction', {})
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Rapor oluşturulurken hata: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

