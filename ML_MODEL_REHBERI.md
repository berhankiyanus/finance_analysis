# ML Modeli Eğitimi Rehberi 🤖

Bu rehber, fiyat yönü tahmini için makine öğrenmesi modeli eğitmeyi açıklar.

## 📋 Genel Bakış

Sistem şu anda **hazır modeller** kullanıyor (eğitim yok). Ancak isterseniz:

1. **Fiyat Yönü Tahmini Modeli** eğitebilirsiniz (Random Forest, XGBoost vb.)
2. **FinBERT Fine-tuning** yapabilirsiniz (Türkçe için - ileri seviye)

## 🚀 Fiyat Yönü Tahmini Modeli

### Ne Yapar?

Geçmiş fiyat verilerinden ve feature'lardan öğrenerek, önümüzdeki 5-10 gün için fiyat yönünü tahmin eder:
- **up**: Fiyat yükselecek (%2'den fazla)
- **down**: Fiyat düşecek (%2'den fazla)
- **neutral**: Yatay seyir

### Hızlı Başlangıç

#### 1. Gerekli Paketleri Yükleyin

```bash
pip install scikit-learn xgboost
```

#### 2. Model Eğitin

```bash
# Apple için model eğit
python3 train_model.py AAPL --period 2y --model-type random_forest

# Microsoft için XGBoost modeli
python3 train_model.py MSFT --period 2y --model-type xgboost

# Türk şirketi için
python3 train_model.py THYAO.IS --period 2y
```

#### 3. Eğitilmiş Modeli Kullanın

Model eğitildikten sonra, ana analiz sisteminde otomatik kullanılacak:

```bash
python3 -m src.main "Apple" "AAPL" 30
```

Sistem eğitilmiş modeli bulursa onu kullanır, bulamazsa kural tabanlı tahmin yapar.

### Detaylı Kullanım

#### Python Kodundan

```python
from src.prediction_model import train_price_direction_model, PriceDirectionPredictor

# Model eğit
predictor = train_price_direction_model(
    ticker="AAPL",
    period="2y",  # 2 yıllık veri
    model_type="random_forest",
    future_days=5,  # 5 gün sonrasını tahmin et
    save_path="models/price_predictor_aapl.pkl"
)

# Modeli yükle ve kullan
predictor = PriceDirectionPredictor(model_path="models/price_predictor_aapl.pkl")

# Feature vektörü ile tahmin yap
from src.financial_analysis import create_feature_vector
from src.data_collection import get_price_data, compute_features

price_df = get_price_data("AAPL", period="1y")
price_df_feat = compute_features(price_df)
feature_vector = create_feature_vector(price_df_feat)

prediction = predictor.predict(feature_vector)
print(f"Yön: {prediction['direction']}")
print(f"Güven: {prediction['confidence']:.2%}")
```

### Model Tipleri

#### 1. Random Forest (Önerilen - Başlangıç)
```bash
python3 train_model.py AAPL --model-type random_forest
```
- ✅ Hızlı eğitim
- ✅ Feature importance sağlar
- ✅ Overfitting'e karşı dayanıklı

#### 2. XGBoost (En İyi Performans)
```bash
python3 train_model.py AAPL --model-type xgboost
```
- ✅ Genelde en iyi accuracy
- ⚠️ Daha uzun eğitim süresi
- ⚠️ Hyperparameter tuning gerekebilir

#### 3. Gradient Boosting
```bash
python3 train_model.py AAPL --model-type gradient_boosting
```
- ✅ İyi performans
- ⚠️ XGBoost'tan biraz daha yavaş

#### 4. Logistic Regression (Basit)
```bash
python3 train_model.py AAPL --model-type logistic
```
- ✅ Çok hızlı
- ✅ Yorumlanabilir
- ⚠️ Non-linear ilişkileri yakalayamaz

### Model Parametreleri

```bash
python3 train_model.py AAPL \
    --period 2y \              # Veri periyodu (1y, 2y, 5y)
    --model-type random_forest \  # Model tipi
    --future-days 5 \           # Kaç gün sonrasını tahmin et
    --save-path models/my_model.pkl  # Kayıt yolu
```

### Model Değerlendirme

Eğitim sırasında şunları göreceksiniz:

```
📚 Model eğitiliyor (random_forest)...
   Train seti: 400 örnek
   Validation seti: 50 örnek
   Test seti: 50 örnek

✅ Eğitim tamamlandı!
   Train Accuracy: 65.25%
   Validation Accuracy: 62.00%
   Test Accuracy: 60.00%

📈 En Önemli 10 Feature:
   feature              importance
   return_30d           0.234567
   rsi_14               0.189012
   volatility_30d       0.156789
   ...
```

### Feature Importance Analizi

Hangi feature'ların en önemli olduğunu görmek için:

```python
from src.prediction_model import PriceDirectionPredictor

predictor = PriceDirectionPredictor(model_path="models/price_predictor_aapl.pkl")
importance_df = predictor.get_feature_importance()
print(importance_df.head(10))
```

## 🎓 Model Eğitimi İpuçları

### 1. Yeterli Veri

- **Minimum**: 100 günlük veri
- **Önerilen**: 1-2 yıllık veri
- **İdeal**: 3-5 yıllık veri

### 2. Veri Kalitesi

- Eksik verileri doldurun
- Outlier'ları kontrol edin
- Zaman serisi tutarlılığını sağlayın

### 3. Model Seçimi

- **Başlangıç**: Random Forest
- **Performans**: XGBoost
- **Hız**: Logistic Regression

### 4. Overfitting Önleme

- Validation seti kullanın
- Test accuracy'yi kontrol edin
- Train ve test accuracy arasındaki farkı izleyin

### 5. Hyperparameter Tuning (İleri Seviye)

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(
    RandomForestClassifier(),
    param_grid,
    cv=TimeSeriesSplit(n_splits=3)
)
grid_search.fit(X_train, y_train)
```

## 📊 Model Performansını İyileştirme

### 1. Daha Fazla Feature

- Haber sentiment verisi ekleyin
- Teknik göstergeler ekleyin (MACD, Bollinger Bands)
- Sektör/genel piyasa göstergeleri ekleyin

### 2. Feature Engineering

- Lag feature'ları (geçmiş değerler)
- Rolling statistics
- Zaman bazlı feature'lar (ay, hafta günü)

### 3. Ensemble Modeller

Birden fazla modeli birleştirin:

```python
# Birden fazla model eğit
rf_model = train_price_direction_model("AAPL", model_type="random_forest")
xgb_model = train_price_direction_model("AAPL", model_type="xgboost")

# Tahminleri birleştir (voting)
```

## ⚠️ Önemli Notlar

1. **Gelecek Sızıntısı (Future Leakage)**: Gelecekteki verileri kullanmayın!
2. **Zaman Serisi**: Rastgele train/test split kullanmayın, zaman bazlı yapın
3. **Backtesting**: Model performansını geçmiş veri üzerinde test edin
4. **Yatırım Tavsiyesi Değil**: Bu modeller sadece eğitim amaçlıdır

## 🔮 FinBERT Fine-tuning (İleri Seviye)

Türkçe finansal haberler için FinBERT'i fine-tune etmek isterseniz:

### Gereksinimler

1. Etiketlenmiş Türkçe finansal haber verisi
2. GPU (önerilir)
3. Transformers ve PyTorch

### Örnek Kod Yapısı

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments

# Model ve tokenizer yükle
model_name = "dbmdz/bert-base-turkish-cased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=3)

# Eğitim verisi hazırla
# ... (tokenization, dataset oluşturma)

# Eğit
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    logging_dir='./logs',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

trainer.train()
```

Bu kısım şu anda implement edilmemiş, ancak gerekirse eklenebilir.

## 📚 Kaynaklar

- [Scikit-learn Dokümantasyonu](https://scikit-learn.org/stable/)
- [XGBoost Dokümantasyonu](https://xgboost.readthedocs.io/)
- [Transformers Fine-tuning](https://huggingface.co/docs/transformers/training)

## 🆘 Sorun Giderme

### "scikit-learn yüklü değil" Hatası

```bash
pip install scikit-learn xgboost
```

### "Yeterli veri yok" Hatası

Daha uzun periyot kullanın:
```bash
python3 train_model.py AAPL --period 5y
```

### Model Performansı Düşük

- Daha fazla veri toplayın
- Farklı model tipi deneyin
- Feature engineering yapın
- Hyperparameter tuning yapın

---

**Başarılar! 🚀**

