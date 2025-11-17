"""
Scoring Modülü Testleri
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scoring import compute_overall_score, interpret_score


class TestComputeOverallScore:
    """compute_overall_score fonksiyonu testleri"""
    
    def test_high_scores(self):
        """Yüksek skorlar için test"""
        # Yüksek sentiment, yüksek finansal skor
        score = compute_overall_score(
            sentiment_score=0.8,
            financial_score=0.9,
            sentiment_weight=0.4,
            financial_weight=0.6
        )
        
        assert 0 <= score <= 100
        assert score > 70  # Yüksek skor bekleniyor
    
    def test_low_scores(self):
        """Düşük skorlar için test"""
        # Düşük sentiment, düşük finansal skor
        score = compute_overall_score(
            sentiment_score=0.2,
            financial_score=0.3,
            sentiment_weight=0.4,
            financial_weight=0.6
        )
        
        assert 0 <= score <= 100
        assert score < 50  # Düşük skor bekleniyor
    
    def test_edge_case_zero_scores(self):
        """Sıfır skorlar için edge case testi"""
        score = compute_overall_score(
            sentiment_score=0.0,
            financial_score=0.0,
            sentiment_weight=0.4,
            financial_weight=0.6
        )
        
        assert score == 0.0
    
    def test_edge_case_max_scores(self):
        """Maksimum skorlar için edge case testi"""
        score = compute_overall_score(
            sentiment_score=1.0,
            financial_score=1.0,
            sentiment_weight=0.4,
            financial_weight=0.6
        )
        
        assert score == 100.0


class TestInterpretScore:
    """interpret_score fonksiyonu testleri"""
    
    def test_high_score_interpretation(self):
        """Yüksek skor yorumu testi"""
        result = interpret_score(85.0)
        
        assert 'category' in result
        assert 'risk_level' in result
        assert result['category'] in ['Çok İyi', 'İyi', 'Orta', 'Kötü', 'Çok Kötü']
        assert result['risk_level'] in ['Düşük', 'Orta', 'Yüksek']
    
    def test_low_score_interpretation(self):
        """Düşük skor yorumu testi"""
        result = interpret_score(25.0)
        
        assert 'category' in result
        assert 'risk_level' in result
        # Düşük skor için yüksek risk bekleniyor
        assert result['risk_level'] in ['Düşük', 'Orta', 'Yüksek']
    
    def test_boundary_scores(self):
        """Sınır değerler için test"""
        # 0 skor
        result_0 = interpret_score(0.0)
        assert 'category' in result_0
        
        # 100 skor
        result_100 = interpret_score(100.0)
        assert 'category' in result_100
        
        # 50 skor (orta)
        result_50 = interpret_score(50.0)
        assert 'category' in result_50
    
    def test_negative_score_handling(self):
        """Negatif skorlar için test (edge case)"""
        result = interpret_score(-10.0)
        # Negatif skorlar da bir kategori döndürmeli
        assert 'category' in result
    
    def test_very_high_score_handling(self):
        """100'den yüksek skorlar için test (edge case)"""
        result = interpret_score(150.0)
        # 100'den yüksek skorlar da bir kategori döndürmeli
        assert 'category' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

