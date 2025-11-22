# Test Rehberi

Bu dizin, projenin test dosyalarını içerir.

## Test Yapısı

### Mock'lu Testler (Hızlı)
- `test_data_collection_mocked.py` - Data collection mock testleri
- `test_main_mocked.py` - Main modül mock testleri
- `test_sentiment_analysis_mocked.py` - Sentiment analysis mock testleri

### Entegrasyon Testleri (Yavaş)
- Gerçek API çağrıları yapan testler
- `@pytest.mark.slow` ile işaretlenmiş
- `@pytest.mark.integration` ile işaretlenmiş

### Fixtures
- `conftest.py` - Tüm testler için ortak fixtures ve mock'lar

## Test Çalıştırma

### Sadece Hızlı Testler (Mock'lu)
```bash
pytest tests/ -v -m "unit"
```

### Sadece Yavaş Testler (Entegrasyon)
```bash
pytest tests/ -v -m "slow"
```

### Tüm Testler
```bash
pytest tests/ -v
```

### Belirli Bir Test Dosyası
```bash
pytest tests/test_data_collection_mocked.py -v
```

### Coverage ile
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Markers

- `@pytest.mark.unit` - Birim testleri (mock'lu, hızlı)
- `@pytest.mark.integration` - Entegrasyon testleri (gerçek API)
- `@pytest.mark.slow` - Yavaş testler (gerçek API çağrıları)

## Mock'lar

### conftest.py Fixtures
- `mock_newsapi_response` - NewsAPI mock yanıtı
- `mock_yfinance_ticker` - yfinance Ticker mock'u
- `mock_price_dataframe` - Fiyat verisi DataFrame
- `mock_news_dataframe` - Haber verisi DataFrame
- `mock_sentiment_analyzer` - SentimentAnalyzer mock'u
- `mock_http_client` - HTTP client mock'u
- `mock_gemini_model` - Gemini model mock'u
- `mock_env_vars` - Env var mock'ları (otomatik)

## Notlar

- Mock'lu testler harici servis çağrılarını yapmaz, çok hızlıdır
- Entegrasyon testleri gerçek API key'ler gerektirir
- CI/CD'de sadece unit testler çalıştırılabilir (hızlı)
- Entegrasyon testleri manuel veya nightly build'de çalıştırılabilir

