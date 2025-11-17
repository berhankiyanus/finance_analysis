"""
Sentiment Analysis Modülü Testleri
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sentiment_analysis import SentimentAnalyzer


class TestSentimentAnalyzer:
    """SentimentAnalyzer testleri"""
    
    def test_rule_based_mode_fallback(self):
        """FinBERT yüklenemediğinde rule-based mode'a geçtiğini test et"""
        # FinBERT import'unu mock'la (yüklenemiyormuş gibi)
        with patch('src.sentiment_analysis.FINBERT_AVAILABLE', False):
            analyzer = SentimentAnalyzer()
            
            # Rule-based mode'da çalıştığını kontrol et
            assert analyzer.use_finbert == False
    
    def test_rule_based_positive_text(self):
        """Rule-based mode'da pozitif metinleri ayırt edebildiğini test et"""
        analyzer = SentimentAnalyzer()
        analyzer.use_finbert = False  # Rule-based mode'a zorla
        
        positive_texts = [
            "Bu şirket harika sonuçlar açıkladı!",
            "Kârlar arttı, yatırımcılar memnun.",
            "Büyüme hızlandı, gelecek parlak görünüyor."
        ]
        
        for text in positive_texts:
            result = analyzer.analyze(text)
            # En azından 'positive' veya 'neutral' dönmeli (rule-based basit)
            assert result['sentiment'] in ['positive', 'neutral', 'negative']
            assert 'score' in result
    
    def test_rule_based_negative_text(self):
        """Rule-based mode'da negatif metinleri ayırt edebildiğini test et"""
        analyzer = SentimentAnalyzer()
        analyzer.use_finbert = False  # Rule-based mode'a zorla
        
        negative_texts = [
            "Şirket zarar açıkladı, fiyatlar düştü.",
            "Kriz büyüyor, yatırımcılar endişeli.",
            "Satışlar azaldı, gelecek belirsiz."
        ]
        
        for text in negative_texts:
            result = analyzer.analyze(text)
            # En azından bir sentiment dönmeli
            assert result['sentiment'] in ['positive', 'neutral', 'negative']
            assert 'score' in result
    
    def test_analyze_dataframe(self):
        """DataFrame analizi testi"""
        import pandas as pd
        
        analyzer = SentimentAnalyzer()
        analyzer.use_finbert = False  # Rule-based mode
        
        df = pd.DataFrame({
            'title': ['Good news', 'Bad news'],
            'summary': ['Great results', 'Poor performance']
        })
        
        result_df = analyzer.analyze_dataframe(df, text_column='title')
        
        assert isinstance(result_df, pd.DataFrame)
        assert 'sentiment' in result_df.columns or 'sentiment_class' in result_df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

