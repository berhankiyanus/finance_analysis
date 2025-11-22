"""
Main Modülü Testleri (Mock'lu)

analyze_company fonksiyonunu mock'lu testlerle test eder.
"""

import pytest
import pandas as pd
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import analyze_company


@pytest.mark.unit
class TestMainMocked:
    """Main modül testleri (mock'lu)."""
    
    @patch('src.main.get_sentiment_analyzer')
    @patch('src.main.get_news')
    @patch('src.main.get_price_data')
    @patch('src.main.get_fundamentals')
    @patch('src.main.get_macroeconomic_data')
    @patch('src.main.analyze_news_sentiment')
    @patch('src.main.compute_features')
    @patch('src.main.compute_overall_score')
    @patch('src.main.predict_direction')
    def test_analyze_company_mocked(
        self,
        mock_predict,
        mock_overall_score,
        mock_compute_features,
        mock_analyze_sentiment,
        mock_get_macro,
        mock_get_fundamentals,
        mock_get_price,
        mock_get_news,
        mock_get_analyzer,
        mock_sentiment_analyzer,
        mock_news_dataframe,
        mock_price_dataframe
    ):
        """analyze_company fonksiyonu mock testi."""
        # Mock setup
        mock_get_news.return_value = mock_news_dataframe
        mock_get_price.return_value = (mock_price_dataframe, True)
        mock_get_fundamentals.return_value = {'pe_ratio': 20.0, 'market_cap': 1000000}
        mock_get_macro.return_value = {'inflation': 2.5, 'interest_rate': 3.0}
        mock_get_analyzer.return_value = mock_sentiment_analyzer
        
        mock_analyze_sentiment.return_value = mock_news_dataframe.copy()
        mock_analyze_sentiment.return_value['sentiment_class'] = ['positive', 'negative', 'neutral']
        mock_analyze_sentiment.return_value['sentiment_confidence'] = [0.8, 0.7, 0.5]
        
        mock_compute_features.return_value = mock_price_dataframe.copy()
        mock_overall_score.return_value = 75.0
        mock_predict.return_value = {
            'direction': 'up',
            'confidence': 0.8,
            'reason': 'Test reason'
        }
        
        # Test
        results = analyze_company(
            company_name='Test Company',
            ticker='TEST',
            days_back=30
        )
        
        # Assertions
        assert isinstance(results, dict)
        assert 'overall_score' in results
        assert 'sentiment_score' in results
        assert 'financial_score' in results
        assert 'news_df' in results
        assert 'price_df' in results
        assert results['overall_score'] == 75.0


@pytest.mark.integration
@pytest.mark.slow
class TestMainIntegration:
    """Main modül entegrasyon testleri (gerçek API, yavaş)."""
    
    def test_analyze_company_real_api(self):
        """Gerçek API ile analiz testi (yavaş, opsiyonel)."""
        # Sadece API key'ler varsa çalıştır
        if not os.getenv('NEWS_API_KEY'):
            pytest.skip("NEWS_API_KEY bulunamadı, test atlanıyor")
        
        # Basit bir test (küçük veri seti)
        results = analyze_company(
            company_name='Apple',
            ticker='AAPL',
            days_back=7  # Kısa süre, hızlı test
        )
        
        assert isinstance(results, dict)
        assert 'overall_score' in results


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

