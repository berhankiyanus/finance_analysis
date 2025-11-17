"""
Fiyat Yönü Tahmini için ML Modeli

Bu modül, geçmiş verilerden öğrenerek gelecek fiyat yönünü tahmin eden
makine öğrenmesi modellerini içerir.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import pickle
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, mean_squared_error, r2_score
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn yüklü değil. ML modelleri kullanılamayacak.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except (ImportError, Exception) as e:
    XGBOOST_AVAILABLE = False
    print(f"⚠️  XGBoost yüklü değil veya çalışmıyor: {e}")
    print("   RandomForest kullanılacak.")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except (ImportError, Exception) as e:
    LIGHTGBM_AVAILABLE = False
    print(f"⚠️  LightGBM yüklü değil veya çalışmıyor: {type(e).__name__}")
    print("   RandomForest kullanılacak.")


class PriceDirectionPredictor:
    """
    Fiyat yönü tahmini için ML modeli sınıfı.
    """
    
    def __init__(self, model_type: str = "random_forest", model_path: Optional[str] = None, 
                 task_type: str = "classification"):
        """
        Model oluşturur veya kaydedilmiş modeli yükler.
        
        Parametreler:
        ------------
        model_type : str
            Model tipi: 'random_forest', 'xgboost', 'lightgbm', 'gradient_boosting', 'logistic'
        model_path : str, optional
            Kaydedilmiş model dosyası yolu
        task_type : str
            Görev tipi: 'classification' (yön tahmini) veya 'regression' (getiri tahmini)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn yüklü değil. 'pip install scikit-learn xgboost' komutu ile yükleyin.")
        
        self.model_type = model_type
        self.task_type = task_type  # 'classification' veya 'regression'
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.model = None
        self.feature_names = None
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._create_model()
    
    def _create_model(self):
        """Model oluşturur (classification veya regression)."""
        if self.task_type == "classification":
            if self.model_type == "random_forest":
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            elif self.model_type == "xgboost":
                if not XGBOOST_AVAILABLE:
                    print("⚠️  XGBoost kullanılamıyor, RandomForest kullanılıyor.")
                    self.model_type = "random_forest"
                    self.model = RandomForestClassifier(
                        n_estimators=100,
                        max_depth=10,
                        min_samples_split=5,
                        min_samples_leaf=2,
                        random_state=42,
                        n_jobs=-1
                    )
                else:
                    self.model = xgb.XGBClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        random_state=42,
                        eval_metric='mlogloss'
                    )
            elif self.model_type == "lightgbm":
                if not LIGHTGBM_AVAILABLE:
                    raise ImportError("LightGBM yüklü değil. 'pip install lightgbm' komutu ile yükleyin.")
                self.model = lgb.LGBMClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbose=-1
                )
            elif self.model_type == "gradient_boosting":
                self.model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                )
            elif self.model_type == "logistic":
                self.model = LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    multi_class='multinomial'
                )
            else:
                raise ValueError(f"Bilinmeyen model tipi: {self.model_type}")
        
        elif self.task_type == "regression":
            if self.model_type == "random_forest":
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            elif self.model_type == "xgboost":
                self.model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                )
            elif self.model_type == "lightgbm":
                if not LIGHTGBM_AVAILABLE:
                    raise ImportError("LightGBM yüklü değil. 'pip install lightgbm' komutu ile yükleyin.")
                self.model = lgb.LGBMRegressor(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    verbose=-1
                )
            elif self.model_type == "gradient_boosting":
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    random_state=42
                )
            elif self.model_type == "logistic":
                self.model = LinearRegression()
            else:
                raise ValueError(f"Bilinmeyen model tipi: {self.model_type}")
        else:
            raise ValueError(f"Bilinmeyen görev tipi: {self.task_type}")
    
    def prepare_training_data(
        self,
        price_df: pd.DataFrame,
        news_sentiment_df: Optional[pd.DataFrame] = None,
        future_days: int = 5,
        min_history_days: int = 30
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Eğitim verisi hazırlar.
        
        Parametreler:
        ------------
        price_df : pd.DataFrame
            Feature'ları hesaplanmış fiyat DataFrame'i
        news_sentiment_df : pd.DataFrame, optional
            Haber sentiment verisi (tarih bazlı)
        future_days : int
            Kaç gün sonrasını tahmin edeceğiz (varsayılan: 5)
        min_history_days : int
            Minimum geçmiş veri günü (varsayılan: 30)
        
        Döndürür:
        --------
        X : np.ndarray
            Feature matrisi
        y : np.ndarray
            Hedef değişken (yön: 'up', 'down', 'neutral')
        feature_names : List[str]
            Feature isimleri
        """
        
        try:
            from .financial_analysis import create_feature_vector
        except ImportError:
            from src.financial_analysis import create_feature_vector
        
        X_list = []
        y_list = []
        feature_names = None
        
        # Her gün için feature ve hedef oluştur
        for i in range(min_history_days, len(price_df) - future_days):
            # Geçmiş veriye göre feature çıkar
            historical_data = price_df.iloc[:i+1].copy()
            features = create_feature_vector(historical_data)
            
            # Haber sentiment ekle (eğer varsa)
            if news_sentiment_df is not None:
                # O güne kadar olan haberlerin sentiment ortalaması
                current_date = price_df.iloc[i]['date']
                past_news = news_sentiment_df[
                    news_sentiment_df['published_at'] <= current_date
                ]
                if not past_news.empty:
                    avg_sentiment = past_news['sentiment_score'].mean()
                    features['news_sentiment_avg'] = avg_sentiment
                else:
                    features['news_sentiment_avg'] = 0.0
            
            # Feature isimlerini kaydet (ilk iterasyonda)
            if feature_names is None:
                feature_names = list(features.keys())
            
            # Feature vektörünü oluştur (sıralı)
            feature_vector = [features.get(name, 0) for name in feature_names]
            X_list.append(feature_vector)
            
            # Hedef değişkeni hesapla
            current_price = price_df.iloc[i]['close']
            future_prices = price_df.iloc[i+1:i+future_days+1]['close']
            
            if self.task_type == "classification":
                # Yön sınıflandırması
                future_price = price_df.iloc[i + future_days]['close']
                return_pct = (future_price / current_price - 1) * 100
                
                if return_pct > 2.0:  # %2'den fazla artış
                    y_list.append('up')
                elif return_pct < -2.0:  # %2'den fazla düşüş
                    y_list.append('down')
                else:  # Yatay
                    y_list.append('neutral')
            
            elif self.task_type == "regression":
                # Sonraki 5 gün içindeki maksimum getiri (next_5_day_max_return)
                max_future_price = future_prices.max()
                max_return_pct = (max_future_price / current_price - 1) * 100
                y_list.append(max_return_pct)
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        self.feature_names = feature_names
        
        return X, y, feature_names
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        validation_size: float = 0.1
    ) -> Dict:
        """
        Modeli eğitir.
        
        Parametreler:
        ------------
        X : np.ndarray
            Feature matrisi
        y : np.ndarray
            Hedef değişken
        test_size : float
            Test seti oranı (varsayılan: 0.2)
        validation_size : float
            Validation seti oranı (varsayılan: 0.1)
        
        Döndürür:
        --------
        dict
            Eğitim sonuçları (accuracy, classification_report vb.)
        """
        
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn yüklü değil.")
        
        # Zaman bazlı ayrım (önemli: rastgele değil!)
        n_samples = len(X)
        n_test = int(n_samples * test_size)
        n_val = int(n_samples * validation_size)
        
        # Train/Val/Test ayrımı
        X_train = X[:-(n_test + n_val)]
        y_train = y[:-(n_test + n_val)]
        
        X_val = X[-(n_test + n_val):-n_test] if n_val > 0 else X_train[-n_val:]
        y_val = y[-(n_test + n_val):-n_test] if n_val > 0 else y_train[-n_val:]
        
        X_test = X[-n_test:]
        y_test = y[-n_test:]
        
        # Feature'ları normalize et
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val) if n_val > 0 else None
        X_test_scaled = self.scaler.transform(X_test)
        
        # Label encoding: Sadece classification için gerekli
        if self.task_type == "classification":
            y_train_encoded = self.label_encoder.fit_transform(y_train)
            y_val_encoded = self.label_encoder.transform(y_val) if n_val > 0 else None
            y_test_encoded = self.label_encoder.transform(y_test)
        else:
            # Regression için encoding gerekmez
            y_train_encoded = y_train
            y_val_encoded = y_val if n_val > 0 else None
            y_test_encoded = y_test
        
        # Modeli eğit
        print(f"📚 Model eğitiliyor ({self.model_type}, {self.task_type})...")
        print(f"   Train seti: {len(X_train)} örnek")
        if n_val > 0:
            print(f"   Validation seti: {len(X_val)} örnek")
        print(f"   Test seti: {len(X_test)} örnek")
        
        self.model.fit(X_train_scaled, y_train_encoded)
        self.is_trained = True
        
        # Değerlendirme
        if self.task_type == "classification":
            # Classification metrikleri
            train_pred_encoded = self.model.predict(X_train_scaled)
            train_pred = self.label_encoder.inverse_transform(train_pred_encoded)
            train_acc = accuracy_score(y_train, train_pred)
            
            val_acc = None
            if X_val_scaled is not None:
                val_pred_encoded = self.model.predict(X_val_scaled)
                val_pred = self.label_encoder.inverse_transform(val_pred_encoded)
                val_acc = accuracy_score(y_val, val_pred)
            
            test_pred_encoded = self.model.predict(X_test_scaled)
            test_pred = self.label_encoder.inverse_transform(test_pred_encoded)
            test_acc = accuracy_score(y_test, test_pred)
            
            # Sonuçları topla
            results = {
                'train_accuracy': train_acc,
                'validation_accuracy': val_acc,
                'test_accuracy': test_acc,
                'train_predictions': train_pred,
                'test_predictions': test_pred,
                'y_train': y_train,
                'y_test': y_test,
                'classification_report': classification_report(y_test, test_pred, output_dict=True),
                'confusion_matrix': confusion_matrix(y_test, test_pred).tolist()
            }
        
        else:
            # Regression metrikleri
            train_pred = self.model.predict(X_train_scaled)
            train_mse = mean_squared_error(y_train, train_pred)
            train_r2 = r2_score(y_train, train_pred)
            train_rmse = np.sqrt(train_mse)
            
            val_mse = None
            val_r2 = None
            val_rmse = None
            if X_val_scaled is not None:
                val_pred = self.model.predict(X_val_scaled)
                val_mse = mean_squared_error(y_val, val_pred)
                val_r2 = r2_score(y_val, val_pred)
                val_rmse = np.sqrt(val_mse)
            
            test_pred = self.model.predict(X_test_scaled)
            test_mse = mean_squared_error(y_test, test_pred)
            test_r2 = r2_score(y_test, test_pred)
            test_rmse = np.sqrt(test_mse)
            
            # Sonuçları topla
            results = {
                'train_mse': train_mse,
                'train_rmse': train_rmse,
                'train_r2': train_r2,
                'validation_mse': val_mse,
                'validation_rmse': val_rmse,
                'validation_r2': val_r2,
                'test_mse': test_mse,
                'test_rmse': test_rmse,
                'test_r2': test_r2,
                'train_predictions': train_pred,
                'test_predictions': test_pred,
                'y_train': y_train,
                'y_test': y_test
            }
        
        print(f"\n✅ Eğitim tamamlandı!")
        if self.task_type == "classification":
            print(f"   Train Accuracy: {results['train_accuracy']:.2%}")
            if results.get('validation_accuracy'):
                print(f"   Validation Accuracy: {results['validation_accuracy']:.2%}")
            print(f"   Test Accuracy: {results['test_accuracy']:.2%}")
        else:
            print(f"   Train RMSE: {results['train_rmse']:.4f}, R²: {results['train_r2']:.4f}")
            if results.get('validation_rmse'):
                print(f"   Validation RMSE: {results['validation_rmse']:.4f}, R²: {results['validation_r2']:.4f}")
            print(f"   Test RMSE: {results['test_rmse']:.4f}, R²: {results['test_r2']:.4f}")
        
        return results
    
    def predict(self, feature_vector: Dict) -> Dict:
        """
        Tek bir örnek için tahmin yapar.
        
        Parametreler:
        ------------
        feature_vector : dict
            Feature vektörü (create_feature_vector() çıktısı)
        
        Döndürür:
        --------
        dict
            Classification için: 'direction', 'probabilities', 'confidence'
            Regression için: 'predicted_return', 'predicted_value'
        """
        
        if not self.is_trained:
            raise ValueError("Model henüz eğitilmedi. Önce train() metodunu çağırın.")
        
        if self.feature_names is None:
            raise ValueError("Feature isimleri tanımlı değil.")
        
        # Feature vektörünü sıralı array'e çevir
        X = np.array([[feature_vector.get(name, 0) for name in self.feature_names]])
        
        # Normalize et
        X_scaled = self.scaler.transform(X)
        
        if self.task_type == "classification":
            # Classification tahmini
            prediction_encoded = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Tahmini decode et (sayısal değerden string'e)
            prediction = self.label_encoder.inverse_transform([prediction_encoded])[0]
            
            # Sınıf isimlerini decode et
            class_names = self.label_encoder.inverse_transform(self.model.classes_)
            prob_dict = {class_name: float(prob) for class_name, prob in zip(class_names, probabilities)}
            confidence = float(max(probabilities))
            
            return {
                'direction': prediction,
                'probabilities': prob_dict,
                'confidence': confidence
            }
        
        else:
            # Regression tahmini
            predicted_value = self.model.predict(X_scaled)[0]
            
            return {
                'predicted_return': float(predicted_value),  # Yüzde getiri
                'predicted_value': float(predicted_value)
            }
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Feature importance'ları döndürür.
        
        Döndürür:
        --------
        pd.DataFrame
            Feature isimleri ve importance değerleri
        """
        
        if not self.is_trained:
            raise ValueError("Model henüz eğitilmedi.")
        
        if not hasattr(self.model, 'feature_importances_'):
            raise ValueError(f"{self.model_type} modeli feature importance desteklemiyor.")
        
        importances = self.model.feature_importances_
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def explain_prediction_shap(
        self,
        feature_vector: Dict,
        background_data: Optional[np.ndarray] = None,
        max_evals: int = 100
    ) -> Dict:
        """
        SHAP kullanarak tahmin açıklaması yapar.
        
        Parametreler:
        ------------
        feature_vector : dict
            Feature vektörü
        background_data : np.ndarray, optional
            Background veri (SHAP için referans). Eğer yoksa, feature_vector'dan oluşturulur.
        max_evals : int
            Maksimum SHAP değerlendirme sayısı (varsayılan: 100)
        
        Döndürür:
        --------
        dict
            SHAP değerleri ve açıklamalar
        """
        
        if not self.is_trained:
            raise ValueError("Model henüz eğitilmedi.")
        
        try:
            import shap
        except ImportError:
            raise ImportError("SHAP yüklü değil. 'pip install shap' komutu ile yükleyin.")
        
        # Feature vektörünü array'e çevir
        X = np.array([[feature_vector.get(name, 0) for name in self.feature_names]])
        X_scaled = self.scaler.transform(X)
        
        # Background data hazırla
        if background_data is None:
            # Basit background: feature_vector'ın etrafında küçük varyasyonlar
            background_size = min(50, max_evals)
            background = np.random.normal(
                loc=X_scaled[0],
                scale=0.1,
                size=(background_size, len(self.feature_names))
            )
        else:
            background = background_data
        
        # SHAP explainer oluştur
        try:
            # Tree-based modeller için TreeExplainer
            if self.model_type in ['random_forest', 'xgboost', 'lightgbm', 'gradient_boosting']:
                explainer = shap.TreeExplainer(self.model)
                shap_values = explainer.shap_values(X_scaled)
                
                if self.task_type == "classification":
                    # Multi-class için en yüksek sınıfın SHAP değerlerini al
                    if isinstance(shap_values, list):
                        # En yüksek olasılıklı sınıfı bul
                        prediction_raw = self.model.predict(X_scaled)[0]
                        # Numpy array'i scalar'a çevir
                        if isinstance(prediction_raw, np.ndarray):
                            prediction = int(prediction_raw.item())
                        else:
                            prediction = int(prediction_raw)
                        class_idx = list(self.model.classes_).index(prediction)
                        shap_values = shap_values[class_idx]
                    
                    # İlk örneği al - array ise ilk elemanı, zaten scalar ise direkt kullan
                    if isinstance(shap_values, np.ndarray):
                        if len(shap_values.shape) > 1:
                            shap_values = shap_values[0]
                        else:
                            shap_values = shap_values
                    else:
                        shap_values = shap_values
                else:
                    # Regression için direkt kullan
                    if isinstance(shap_values, np.ndarray):
                        if len(shap_values.shape) > 1:
                            shap_values = shap_values[0]
                        else:
                            shap_values = shap_values
                    else:
                        shap_values = shap_values
            else:
                # Diğer modeller için KernelExplainer
                if self.task_type == "classification":
                    predict_func = self.model.predict_proba
                else:
                    predict_func = self.model.predict
                
                explainer = shap.KernelExplainer(
                    predict_func,
                    background,
                    max_evals=max_evals
                )
                shap_values = explainer.shap_values(X_scaled[0])
                
                if self.task_type == "classification":
                    # En yüksek olasılıklı sınıf için SHAP değerleri
                    if isinstance(shap_values, list):
                        prediction_raw = self.model.predict(X_scaled)[0]
                        # Numpy array'i scalar'a çevir
                        if isinstance(prediction_raw, np.ndarray):
                            prediction = int(prediction_raw.item())
                        else:
                            prediction = int(prediction_raw)
                        class_idx = list(self.model.classes_).index(prediction)
                        shap_values = shap_values[class_idx]
        except Exception as e:
            print(f"⚠️  SHAP hesaplama hatası: {e}")
            # Fallback: Feature importance kullan
            importances = self.model.feature_importances_ if hasattr(self.model, 'feature_importances_') else np.ones(len(self.feature_names))
            shap_values = importances * (X_scaled[0] - background.mean(axis=0))
        
        # Feature isimleri ile eşleştir
        # shap_values'ı numpy array'den Python list'e çevir
        if isinstance(shap_values, np.ndarray):
            if shap_values.size == 1:
                # Tek bir değer varsa, feature sayısı kadar tekrarla (fallback)
                shap_values_list = [float(shap_values.item())] * len(self.feature_names)
            else:
                shap_values_list = shap_values.tolist() if shap_values.ndim > 0 else [float(shap_values.item())]
        elif isinstance(shap_values, (list, tuple)):
            shap_values_list = list(shap_values)
        else:
            # Scalar değer - tüm feature'lar için aynı değeri kullan (fallback)
            shap_values_list = [float(shap_values)] * len(self.feature_names)
        
        # Eğer liste uzunluğu feature sayısından farklıysa, düzelt
        if len(shap_values_list) != len(self.feature_names):
            if len(shap_values_list) == 1:
                shap_values_list = shap_values_list * len(self.feature_names)
            elif len(shap_values_list) > len(self.feature_names):
                shap_values_list = shap_values_list[:len(self.feature_names)]
            else:
                # Eksik feature'lar için 0 ekle
                shap_values_list.extend([0.0] * (len(self.feature_names) - len(shap_values_list)))
        
        shap_dict = {
            name: float(value)
            for name, value in zip(self.feature_names, shap_values_list)
        }
        
        # En önemli feature'ları sırala
        sorted_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Tahmin bilgisi
        prediction = self.predict(feature_vector)
        
        return {
            'shap_values': shap_dict,
            'top_features': sorted_features[:10],  # En önemli 10 feature
            'prediction': prediction,
            'feature_names': self.feature_names,
            'feature_values': {name: feature_vector.get(name, 0) for name in self.feature_names}
        }
    
    def save_model(self, filepath: str):
        """
        Modeli kaydeder.
        
        Parametreler:
        ------------
        filepath : str
            Kayıt dosyası yolu
        """
        
        if not self.is_trained:
            raise ValueError("Eğitilmemiş model kaydedilemez.")
        
        # Dizini oluştur (yoksa)
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'trained_date': datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✅ Model kaydedildi: {filepath}")
    
    def load_model(self, filepath: str):
        """
        Kaydedilmiş modeli yükler.
        
        Parametreler:
        ------------
        filepath : str
            Model dosyası yolu
        """
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoder = model_data.get('label_encoder', LabelEncoder())
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        
        print(f"✅ Model yüklendi: {filepath}")
        print(f"   Eğitim tarihi: {model_data.get('trained_date', 'Bilinmiyor')}")


def train_price_direction_model(
    ticker: str,
    period: str = "2y",
    model_type: str = "random_forest",
    future_days: int = 5,
    save_path: Optional[str] = None
) -> PriceDirectionPredictor:
    """
    Fiyat yönü tahmini modeli eğitir (kolay kullanım için wrapper fonksiyonu).
    
    Parametreler:
    ------------
    ticker : str
        Borsa kodu
    period : str
        Veri periyodu (varsayılan: "2y")
    model_type : str
        Model tipi (varsayılan: "random_forest")
    future_days : int
        Kaç gün sonrasını tahmin edeceğiz
    save_path : str, optional
        Model kayıt yolu
    
    Döndürür:
    --------
    PriceDirectionPredictor
        Eğitilmiş model
    """
    
    from src.data_collection import get_price_data
    from src.financial_analysis import compute_features
    
    print(f"🚀 {ticker} için fiyat yönü tahmini modeli eğitiliyor...")
    print(f"   Periyot: {period}")
    print(f"   Model tipi: {model_type}")
    print(f"   Tahmin periyodu: {future_days} gün\n")
    
    # Veri topla
    print("📥 Veri toplanıyor...")
    price_df = get_price_data(ticker, period=period)
    
    if len(price_df) < 100:
        raise ValueError(f"Yeterli veri yok. En az 100 günlük veri gerekli. Mevcut: {len(price_df)}")
    
    # Feature'ları hesapla
    print("📊 Feature'lar hesaplanıyor...")
    price_df_with_features = compute_features(price_df)
    
    # Model oluştur
    predictor = PriceDirectionPredictor(model_type=model_type)
    
    # Eğitim verisi hazırla
    print("🔧 Eğitim verisi hazırlanıyor...")
    X, y, feature_names = predictor.prepare_training_data(
        price_df_with_features,
        future_days=future_days
    )
    
    print(f"   Toplam örnek sayısı: {len(X)}")
    print(f"   Feature sayısı: {len(feature_names)}")
    print(f"   Sınıf dağılımı:")
    unique, counts = np.unique(y, return_counts=True)
    for cls, count in zip(unique, counts):
        print(f"     {cls}: {count} ({count/len(y)*100:.1f}%)")
    print()
    
    # Modeli eğit
    results = predictor.train(X, y)
    
    # Feature importance göster
    print("\n📈 En Önemli 10 Feature:")
    importance_df = predictor.get_feature_importance()
    print(importance_df.head(10).to_string(index=False))
    
    # Modeli kaydet
    if save_path:
        predictor.save_model(save_path)
    
    return predictor


if __name__ == "__main__":
    # Test
    print("=== Fiyat Yönü Tahmini Modeli Test ===\n")
    
    if not SKLEARN_AVAILABLE:
        print("❌ scikit-learn yüklü değil. Test edilemiyor.")
        print("   Yüklemek için: pip install scikit-learn xgboost")
    else:
        try:
            # Model eğit
            predictor = train_price_direction_model(
                ticker="AAPL",
                period="2y",
                model_type="random_forest",
                future_days=5,
                save_path="models/price_predictor_aapl.pkl"
            )
            
            # Test tahmini
            print("\n🔮 Test Tahmini:")
            from src.financial_analysis import create_feature_vector
            from src.data_collection import get_price_data, compute_features
            
            price_df = get_price_data("AAPL", period="1y")
            price_df_feat = compute_features(price_df)
            feature_vector = create_feature_vector(price_df_feat)
            
            prediction = predictor.predict(feature_vector)
            print(f"   Yön: {prediction['direction']}")
            print(f"   Güven: {prediction['confidence']:.2%}")
            print(f"   Olasılıklar: {prediction['probabilities']}")
            
        except Exception as e:
            print(f"❌ Hata: {e}")
            import traceback
            traceback.print_exc()

