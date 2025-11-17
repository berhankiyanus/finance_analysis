"""
MLflow Model Kaydı Modülü

Model eğitim denemelerini MLflow ile kaydeder.
"""

import os
from typing import Dict, Optional
from datetime import datetime

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    print("⚠️  MLflow yüklü değil. Model kaydı kullanılamayacak.")


def log_model_training(
    model,
    metrics: Dict[str, float],
    model_path: str,
    feature_names: list,
    ticker: str,
    model_type: str,
    run_name: Optional[str] = None
):
    """
    Model eğitim denemesini MLflow'a kaydeder.
    
    Parametreler:
    ------------
    model
        Eğitilmiş model (sklearn, xgboost, lightgbm, vb.)
    metrics : dict
        Metrikler: {'backtest_sharpe_ratio', 'test_accuracy', 'test_rmse', vb.}
    model_path : str
        Model dosyası yolu
    feature_names : list
        Feature isimleri
    ticker : str
        Borsa kodu
    model_type : str
        Model tipi ('random_forest', 'xgboost', 'lightgbm', vb.)
    run_name : str, optional
        Run adı (varsayılan: ticker_model_type_timestamp)
    """
    
    if not MLFLOW_AVAILABLE:
        print("⚠️  MLflow yüklü değil. Model kaydı atlanıyor.")
        return
    
    # MLflow tracking URI'yi ayarla (eğer belirtilmemişse)
    if not os.getenv('MLFLOW_TRACKING_URI'):
        # Local file store (varsayılan)
        mlflow.set_tracking_uri("file:./mlruns")
    
    # Run adı
    if not run_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"{ticker}_{model_type}_{timestamp}"
    
    # MLflow run başlat
    with mlflow.start_run(run_name=run_name):
        # Parametreleri logla
        mlflow.log_params({
            'ticker': ticker,
            'model_type': model_type,
            'n_features': len(feature_names),
            'feature_names': ','.join(feature_names[:10])  # İlk 10 feature
        })
        
        # Metrikleri logla
        mlflow.log_metrics(metrics)
        
        # Model artifact'ini logla
        if os.path.exists(model_path):
            mlflow.log_artifact(model_path, artifact_path="models")
        
        # Model'i MLflow'a kaydet (model registry için)
        if hasattr(model, 'predict'):
            # Sklearn modelleri için
            try:
                mlflow.sklearn.log_model(
                    model,
                    "model",
                    registered_model_name=f"{ticker}_{model_type}"
                )
            except:
                # Eğer sklearn formatında değilse, sadece artifact olarak kaydet
                mlflow.log_artifact(model_path, artifact_path="models")
        
        # Run bilgilerini yazdır
        run_id = mlflow.active_run().info.run_id
        print(f"✅ MLflow run kaydedildi: {run_name} (Run ID: {run_id})")
        print(f"   Metrikler: {metrics}")


def log_backtest_results(
    backtest_results: Dict,
    ticker: str,
    model_type: str
):
    """
    Backtest sonuçlarını MLflow'a kaydeder.
    
    Parametreler:
    ------------
    backtest_results : dict
        Backtest sonuçları: {'total_return', 'sharpe_ratio', 'max_drawdown', vb.}
    ticker : str
        Borsa kodu
    model_type : str
        Model tipi
    """
    
    if not MLFLOW_AVAILABLE:
        print("⚠️  MLflow yüklü değil. Backtest sonuçları kaydedilemedi.")
        return
    
    # MLflow tracking URI'yi ayarla
    if not os.getenv('MLFLOW_TRACKING_URI'):
        mlflow.set_tracking_uri("file:./mlruns")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{ticker}_{model_type}_backtest_{timestamp}"
    
    with mlflow.start_run(run_name=run_name):
        # Backtest metriklerini logla
        mlflow.log_metrics({
            'backtest_total_return': backtest_results.get('total_return', 0),
            'backtest_sharpe_ratio': backtest_results.get('sharpe_ratio', 0),
            'backtest_max_drawdown': backtest_results.get('max_drawdown', 0),
            'backtest_win_rate': backtest_results.get('win_rate', 0)
        })
        
        mlflow.log_params({
            'ticker': ticker,
            'model_type': model_type,
            'backtest_type': 'walk_forward'
        })
        
        run_id = mlflow.active_run().info.run_id
        print(f"✅ Backtest sonuçları MLflow'a kaydedildi: {run_name} (Run ID: {run_id})")


if __name__ == "__main__":
    print("=== MLflow Model Kaydı Modülü Test ===\n")
    
    if not MLFLOW_AVAILABLE:
        print("⚠️  MLflow yüklü değil.")
        print("   Yüklemek için: pip install mlflow")
    else:
        # Test
        print("1. MLflow tracking URI kontrolü:")
        tracking_uri = mlflow.get_tracking_uri()
        print(f"   Tracking URI: {tracking_uri}")
        
        print("\n2. Test run oluşturma:")
        with mlflow.start_run(run_name="test_run"):
            mlflow.log_param("test_param", "test_value")
            mlflow.log_metric("test_metric", 0.95)
            print("   ✅ Test run başarılı")

