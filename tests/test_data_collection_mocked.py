"""
Data Collection Modülü Testleri (Mock'lu)

Harici servis çağrılarını mock'lar, hızlı test sağlar.
"""

import pytest
import pandas as pd
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_collection import get_news, get_price_data, get_company_name


@pytest.mark.unit
class TestDataCollectionMocked:
    """Data collection testleri (mock'lu)."""
    
    @patch('src.data_collection.get_http_client')
    @patch('src.data_collection.os.getenv')
    def test_get_news_with_mock_newsapi(self, mock_getenv, mock_http_client, mock_newsapi_response):
        """NewsAPI mock ile haber toplama testi."""
        # Mock setup
        mock_getenv.return_value = 'test_api_key'
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.json.return_value = mock_newsapi_response
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        mock_http_client.return_value = mock_client
        
        # Test
        news_df = get_news('Apple', days_back=30, api_key='test_key', ticker='AAPL')
        
        # Assertions
        assert isinstance(news_df, pd.DataFrame)
        assert len(news_df) > 0
        assert 'title' in news_df.columns
        assert 'summary' in news_df.columns
    
    @patch('yfinance.Ticker')
    def test_get_price_data_with_mock_yfinance(self, mock_ticker_class, mock_yfinance_ticker):
        """yfinance mock ile fiyat verisi testi."""
        # Mock setup
        mock_ticker_class.return_value = mock_yfinance_ticker
        
        # Test
        price_df, is_real = get_price_data('AAPL', period='1y', use_dummy_on_failure=False)
        
        # Assertions
        assert isinstance(price_df, pd.DataFrame)
        assert is_real is True
        assert 'date' in price_df.columns
        assert 'close' in price_df.columns
        assert len(price_df) > 0
    
    @patch('yfinance.Ticker')
    def test_get_company_name_with_mock(self, mock_ticker_class, mock_yfinance_ticker):
        """Şirket adı çekme testi (mock'lu)."""
        # Mock setup
        mock_ticker_class.return_value = mock_yfinance_ticker
        
        # Test
        company_name = get_company_name('AAPL')
        
        # Assertions
        assert company_name is not None
        assert isinstance(company_name, str)
        assert len(company_name) > 0


@pytest.mark.integration
class TestDataCollectionIntegration:
    """Data collection entegrasyon testleri (gerçek API çağrıları, yavaş)."""
    
    @pytest.mark.slow
    def test_get_news_real_api(self):
        """Gerçek NewsAPI ile haber toplama testi (yavaş)."""
        # Sadece API key varsa çalıştır
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            pytest.skip("NEWS_API_KEY bulunamadı, test atlanıyor")
        
        news_df = get_news('Apple', days_back=7, api_key=api_key, ticker='AAPL')
        
        assert isinstance(news_df, pd.DataFrame)
        # API key varsa en azından boş DataFrame dönmeli (dummy değil)
        assert 'title' in news_df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

