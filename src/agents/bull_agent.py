"""
Boğa (Bull) Ajanı

Sadece alım fırsatlarını ve olumlu haberleri savunur.
"""

from typing import Dict, Optional
from src.logger_config import setup_logger

logger = setup_logger(__name__)


class BullAgent:
    """
    Boğa (Bull) Ajanı - Optimist yatırım görüşü
    """
    
    def __init__(self, gemini_model=None):
        """
        Boğa ajanını başlatır.
        
        Parametreler:
        ------------
        gemini_model : object
            Gemini model instance'ı (opsiyonel)
        """
        self.gemini_model = gemini_model
        self.name = "Boğa (Bull)"
        self.role = "Optimist Yatırım Uzmanı"
    
    def analyze(self, analysis_results: Dict) -> Dict:
        """
        Analiz sonuçlarını sadece pozitif açıdan yorumlar.
        
        Parametreler:
        ------------
        analysis_results : dict
            Analiz sonuçları
        
        Döndürür:
        --------
        dict
            Boğa ajanının görüşü
        """
        ticker = analysis_results.get('ticker', 'N/A')
        company_name = analysis_results.get('company_name', 'N/A')
        overall_score = analysis_results.get('overall_score', 50.0)
        sentiment_score = analysis_results.get('sentiment_score', 50.0)
        financial_score = analysis_results.get('financial_score', 50.0)
        
        # Gemini kullanarak analiz yap
        if self.gemini_model:
            return self._analyze_with_gemini(analysis_results)
        
        # Rule-based analiz (fallback)
        return self._analyze_rule_based(analysis_results)
    
    def _analyze_with_gemini(self, analysis_results: Dict) -> Dict:
        """
        Gemini ile analiz yapar.
        """
        try:
            ticker = analysis_results.get('ticker', 'N/A')
            company_name = analysis_results.get('company_name', 'N/A')
            
            prompt = f"""
Sen bir "Boğa" (Bull) yatırım uzmanısın. Görevin, {company_name} ({ticker}) hissesi için SADECE POZİTİF yönleri ve ALIM gerekçelerini bulmak.

**Analiz Sonuçları:**
- Genel Skor: {analysis_results.get('overall_score', 50.0):.1f}/100
- Sentiment Skoru: {analysis_results.get('sentiment_score', 50.0):.1f}/100
- Finansal Skor: {analysis_results.get('financial_score', 50.0):.1f}/100

**Görevin:**
1. Sadece pozitif verileri vurgula
2. Alım fırsatlarını bul
3. Olumlu haberleri öne çıkar
4. Riskleri görmezden gel veya minimize et
5. Neden ALINMALI sorusuna odaklan

Yanıtı şu JSON formatında ver:
{{
    "recommendation": "AL",
    "confidence": 0.0-1.0,
    "positive_points": ["Pozitif nokta 1", "Pozitif nokta 2"],
    "buying_opportunities": ["Fırsat 1", "Fırsat 2"],
    "summary": "Kısa özet (2-3 cümle)"
}}
"""
            
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON parse
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    'recommendation': 'AL',
                    'confidence': 0.6,
                    'positive_points': ['Gemini analizi tamamlandı'],
                    'buying_opportunities': [],
                    'summary': response_text[:200]
                }
            
            return {
                'agent': self.name,
                'role': self.role,
                'recommendation': result.get('recommendation', 'AL'),
                'confidence': result.get('confidence', 0.6),
                'positive_points': result.get('positive_points', []),
                'buying_opportunities': result.get('buying_opportunities', []),
                'summary': result.get('summary', ''),
                'method': 'gemini'
            }
            
        except Exception as e:
            logger.warning(f"Boğa ajanı Gemini analizi hatası: {e}")
            return self._analyze_rule_based(analysis_results)
    
    def _analyze_rule_based(self, analysis_results: Dict) -> Dict:
        """
        Rule-based analiz (Gemini yoksa).
        """
        overall_score = analysis_results.get('overall_score', 50.0)
        sentiment_score = analysis_results.get('sentiment_score', 50.0)
        financial_score = analysis_results.get('financial_score', 50.0)
        
        positive_points = []
        buying_opportunities = []
        
        # Pozitif noktalar
        if overall_score > 60:
            positive_points.append(f"Genel skor yüksek ({overall_score:.1f}/100)")
            buying_opportunities.append("Güçlü temel analiz skoru")
        
        if sentiment_score > 60:
            positive_points.append(f"Pozitif sentiment ({sentiment_score:.1f}/100)")
            buying_opportunities.append("Olumlu haber akışı")
        
        if financial_score > 60:
            positive_points.append(f"Güçlü finansal durum ({financial_score:.1f}/100)")
            buying_opportunities.append("Sağlam finansal göstergeler")
        
        # RSI kontrolü
        feature_vector = analysis_results.get('feature_vector', {})
        rsi = feature_vector.get('rsi', 50.0)
        if rsi < 50:
            positive_points.append(f"RSI aşırı satım bölgesinde ({rsi:.1f})")
            buying_opportunities.append("Teknik olarak alım fırsatı")
        
        if not positive_points:
            positive_points.append("Potansiyel büyüme fırsatı")
        
        confidence = min(0.9, 0.5 + (overall_score - 50) / 100)
        
        return {
            'agent': self.name,
            'role': self.role,
            'recommendation': 'AL',
            'confidence': confidence,
            'positive_points': positive_points,
            'buying_opportunities': buying_opportunities,
            'summary': f"{company_name} için pozitif sinyaller mevcut. Alım fırsatı değerlendirilebilir.",
            'method': 'rule_based'
        }

