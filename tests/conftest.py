"""
Pytest Configuration ve Mock Fixtures

Harici servis çağrılarını mock'lar.
Test hızını artırır ve ağ bağımlılığını kaldırır.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os


@pytest.fixture
def mock_newsapi_response():
    """NewsAPI mock yanıtı."""
    return {
        'status': 'ok',
        'totalResults': 10,
        'articles': [
            {
                'title': 'Test News Article 1',
                'description': 'Test description 1',
                'content': 'Test content 1',
                'publishedAt': (datetime.now() - timedelta(days=1)).isoformat(),
                'source': {'name': 'Test Source'},
                'url': 'https://example.com/news1'
            },
            {
                'title': 'Test News Article 2',
                'description': 'Test description 2',
                'content': 'Test content 2',
                'publishedAt': (datetime.now() - timedelta(days=2)).isoformat(),
                'source': {'name': 'Test Source'},
                'url': 'https://example.com/news2'
            }
        ]
    }


@pytest.fixture
def mock_yfinance_ticker():
    """yfinance Ticker mock'u."""
    mock_ticker = Mock()
    
    # Info mock
    mock_ticker.info = {
        'longName': 'Test Company Inc.',
        'shortName': 'Test Co',
        'symbol': 'TEST'
    }
    
    # History mock
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    mock_hist = pd.DataFrame({
        'Open': [100] * 100,
        'High': [105] * 100,
        'Low': [95] * 100,
        'Close': [102] * 100,
        'Volume': [1000000] * 100,
        'Adj Close': [102] * 100
    }, index=dates)
    mock_ticker.history.return_value = mock_hist
    
    return mock_ticker


@pytest.fixture
def mock_price_dataframe():
    """Fiyat verisi DataFrame mock'u."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    return pd.DataFrame({
        'date': dates,
        'open': [100] * 100,
        'high': [105] * 100,
        'low': [95] * 100,
        'close': [102] * 100,
        'volume': [1000000] * 100,
        'adjusted_close': [102] * 100
    })


@pytest.fixture
def mock_news_dataframe():
    """Haber verisi DataFrame mock'u."""
    return pd.DataFrame({
        'title': ['Test News 1', 'Test News 2', 'Test News 3'],
        'summary': ['Summary 1', 'Summary 2', 'Summary 3'],
        'published_at': [
            datetime.now() - timedelta(days=1),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=3)
        ],
        'source': ['Test Source'] * 3,
        'url': ['https://example.com/1', 'https://example.com/2', 'https://example.com/3'],
        'sentiment_class': ['positive', 'negative', 'neutral'],
        'sentiment_confidence': [0.8, 0.7, 0.5],
        'relevance_score': [0.9, 0.8, 0.7]
    })


@pytest.fixture
def mock_sentiment_analyzer():
    """SentimentAnalyzer mock'u."""
    mock_analyzer = Mock()
    
    def mock_analyze(text):
        return {
            'class': 'positive' if 'good' in text.lower() else 'negative' if 'bad' in text.lower() else 'neutral',
            'confidence': 0.8,
            'score': 0.5 if 'good' in text.lower() else -0.5 if 'bad' in text.lower() else 0.0
        }
    
    mock_analyzer.analyze_sentiment = mock_analyze
    mock_analyzer.models = {'en': Mock(), 'tr': Mock()}
    mock_analyzer.use_gemini = False
    mock_analyzer.gemini_model = None
    
    return mock_analyzer


@pytest.fixture
def mock_http_client():
    """HTTP client mock'u."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {'status': 'ok', 'data': []}
    mock_response.raise_for_status = Mock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_gemini_model():
    """Gemini model mock'u."""
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = '{"class": "positive", "confidence": 0.8}'
    mock_model.generate_content.return_value = mock_response
    return mock_model


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Test için env var'ları mock'la."""
    monkeypatch.setenv('NEWS_API_KEY', 'test_news_api_key')
    monkeypatch.setenv('GEMINI_API_KEY', 'test_gemini_api_key')
    monkeypatch.setenv('TCMB_API_KEY', 'test_tcmb_api_key')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')


@pytest.fixture
def mock_config_validator():
    """ConfigValidator mock'u."""
    with patch('src.config_validator.ConfigValidator') as mock:
        mock.validate_config.return_value = (True, {
            'valid': True,
            'missing_required': [],
            'missing_optional': [],
            'found_keys': [
                {'key': 'NEWS_API_KEY', 'name': 'NewsAPI', 'masked': '***'}
            ],
            'warnings': []
        })
        yield mock


# Test için yavaş işaretleyici
def pytest_configure(config):
    """Pytest yapılandırması."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

