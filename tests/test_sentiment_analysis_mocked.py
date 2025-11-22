"""
Sentiment Analysis Modülü Testleri (Mock'lu)

Harici model yüklemelerini mock'lar, hızlı test sağlar.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
from pathlib import Path

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.sentiment_analysis import SentimentAnalyzer


@pytest.mark.unit
class TestSentimentAnalysisMocked:
    """Sentiment analysis testleri (mock'lu)."""
    
    @patch('src.sentiment_analysis.pipeline')
    @patch('src.sentiment_analysis.torch')
    def test_sentiment_analyzer_init_mocked(self, mock_torch, mock_pipeline):
        """SentimentAnalyzer başlatma testi (mock'lu)."""
        # Mock setup
        mock_torch.device.return_value = Mock()
        mock_torch.cuda.is_available.return_value = False
        
        mock_en_pipeline = Mock()
        mock_en_pipeline.return_value = [{'label': 'positive', 'score': 0.8}]
        
        mock_tr_pipeline = Mock()
        mock_tr_pipeline.return_value = [{'label': 'POSITIVE', 'score': 0.7}]
        
        mock_pipeline.side_effect = [mock_en_pipeline, mock_tr_pipeline]
        
        # Test
        analyzer = SentimentAnalyzer(use_gemini=False)
        
        # Assertions
        assert analyzer is not None
        assert analyzer.device is not None
    
    @patch('src.sentiment_analysis.pipeline')
    @patch('src.sentiment_analysis.torch')
    def test_analyze_sentiment_english_mocked(self, mock_torch, mock_pipeline):
        """İngilizce sentiment analizi testi (mock'lu)."""
        # Mock setup
        mock_torch.device.return_value = Mock()
        mock_torch.cuda.is_available.return_value = False
        
        mock_en_pipeline = Mock()
        mock_en_pipeline.return_value = [{'label': 'positive', 'score': 0.8}]
        
        mock_pipeline.return_value = mock_en_pipeline
        
        # Test
        analyzer = SentimentAnalyzer(use_gemini=False)
        result = analyzer.analyze_sentiment("This is a positive news about the company.")
        
        # Assertions
        assert isinstance(result, dict)
        assert 'class' in result
        assert 'confidence' in result
        assert 'score' in result
    
    @patch('src.sentiment_analysis.pipeline')
    @patch('src.sentiment_analysis.torch')
    def test_analyze_sentiment_turkish_mocked(self, mock_torch, mock_pipeline):
        """Türkçe sentiment analizi testi (mock'lu)."""
        # Mock setup
        mock_torch.device.return_value = Mock()
        mock_torch.cuda.is_available.return_value = False
        
        mock_en_pipeline = Mock()
        mock_tr_pipeline = Mock()
        mock_tr_pipeline.return_value = [{'label': 'POSITIVE', 'score': 0.7}]
        
        mock_pipeline.side_effect = [mock_en_pipeline, mock_tr_pipeline]
        
        # Test
        analyzer = SentimentAnalyzer(use_gemini=False)
        result = analyzer.analyze_sentiment("Şirket için olumlu bir haber.")
        
        # Assertions
        assert isinstance(result, dict)
        assert 'class' in result


@pytest.mark.integration
@pytest.mark.slow
class TestSentimentAnalysisIntegration:
    """Sentiment analysis entegrasyon testleri (gerçek modeller, yavaş)."""
    
    def test_analyze_sentiment_real_model(self):
        """Gerçek model ile sentiment analizi testi (yavaş)."""
        # Model yükleme zaman alabilir, sadece gerekirse çalıştır
        analyzer = SentimentAnalyzer(use_gemini=False)
        
        result = analyzer.analyze_sentiment("This is a positive news.")
        
        assert isinstance(result, dict)
        assert 'class' in result
        assert result['class'] in ['positive', 'negative', 'neutral']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])

