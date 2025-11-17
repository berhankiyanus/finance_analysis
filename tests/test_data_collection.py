"""
Data Collection Modülü Testleri
"""

import pytest
import os
from unittest.mock import patch, MagicMock
import pandas as pd

# Test için src modülünü import et
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_collection import get_news, get_price_data


class TestGetNews:
    """get_news fonksiyonu testleri"""
    
    def test_get_news_without_api_key_returns_dummy(self):
        """NEWS_API_KEY olmadan get_news çağrısında dummy veri döndüğünü test et"""
        # API key'i geçici olarak kaldır
        original_key = os.environ.get('NEWS_API_KEY')
        if 'NEWS_API_KEY' in os.environ:
            del os.environ['NEWS_API_KEY']
        
        try:
            # get_news çağrısı yap
            news_df = get_news("Apple", days_back=7)
            
            # Dummy veri döndüğünü kontrol et
            assert isinstance(news_df, pd.DataFrame)
            assert not news_df.empty
            assert 'title' in news_df.columns
            assert 'summary' in news_df.columns
            
        finally:
            # API key'i geri yükle
            if original_key:
                os.environ['NEWS_API_KEY'] = original_key
    
    @patch('src.data_collection.requests.get')
    def test_get_news_with_api_key(self, mock_get):
        """API key ile get_news çağrısını test et"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'ok',
            'totalResults': 1,
            'articles': [{
                'title': 'Test News',
                'description': 'Test Description',
                'content': 'Test Content',
                'publishedAt': '2024-01-01T00:00:00Z',
                'source': {'name': 'Test Source'},
                'url': 'https://test.com/news'
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # API key'i set et
        os.environ['NEWS_API_KEY'] = 'test_key'
        
        try:
            news_df = get_news("Apple", days_back=7)
            assert isinstance(news_df, pd.DataFrame)
        finally:
            if 'NEWS_API_KEY' in os.environ:
                del os.environ['NEWS_API_KEY']


class TestGetPriceData:
    """get_price_data fonksiyonu testleri"""
    
    @patch('src.data_collection.yf.Ticker')
    def test_get_price_data_success(self, mock_ticker):
        """Başarılı fiyat verisi çekme testi"""
        # Mock yfinance response
        mock_hist = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [103, 104, 105],
            'Volume': [1000000, 1100000, 1200000],
            'Adj Close': [103, 104, 105]
        }, index=pd.date_range('2024-01-01', periods=3))
        
        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist
        mock_ticker.return_value = mock_stock
        
        # Test
        price_df = get_price_data("AAPL", period="1mo")
        
        assert isinstance(price_df, pd.DataFrame)
        assert not price_df.empty
        assert 'date' in price_df.columns
        assert 'close' in price_df.columns
    
    @patch('src.data_collection.yf.Ticker')
    def test_get_price_data_empty_returns_dummy(self, mock_ticker):
        """Boş veri döndüğünde dummy veri döndüğünü test et"""
        # Mock empty response
        mock_stock = MagicMock()
        mock_stock.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_stock
        
        # Test
        price_df = get_price_data("INVALID", period="1mo")
        
        assert isinstance(price_df, pd.DataFrame)
        # Dummy veri de olsa en azından bir DataFrame dönmeli
        assert 'date' in price_df.columns or len(price_df) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

