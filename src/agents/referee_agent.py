"""
Hakem (Referee) Ajanı

Boğa ve Ayı ajanlarını dinler ve nihai kararı verir.
"""

from typing import Dict, List, Optional
from src.logger_config import setup_logger

logger = setup_logger(__name__)


class RefereeAgent:
    """
    Hakem (Referee) Ajanı - Nihai karar verici
    """
    
    def __init__(self, gemini_model=None):
        """
        Hakem ajanını başlatır.
        
        Parametreler:
        ------------
        gemini_model : object
            Gemini model instance'ı (opsiyonel)
        """
        self.gemini_model = gemini_model
        self.name = "Hakem (Referee)"
        self.role = "Nihai Karar Verici"
    
    def make_final_decision(
        self,
        bull_opinion: Dict,
        bear_opinion: Dict,
        analysis_results: Dict
    ) -> Dict:
        """
        Boğa ve Ayı ajanlarının görüşlerini değerlendirerek nihai kararı verir.
        
        Parametreler:
        ------------
        bull_opinion : dict
            Boğa ajanının görüşü
        bear_opinion : dict
            Ayı ajanının görüşü
        analysis_results : dict
            Orijinal analiz sonuçları
        
        Döndürür:
        --------
        dict
            Nihai karar ve gerekçesi
        """
        if self.gemini_model:
            return self._decide_with_gemini(bull_opinion, bear_opinion, analysis_results)
        
        return self._decide_rule_based(bull_opinion, bear_opinion, analysis_results)
    
    def _decide_with_gemini(
        self,
        bull_opinion: Dict,
        bear_opinion: Dict,
        analysis_results: Dict
    ) -> Dict:
        """
        Gemini ile nihai karar verir.
        """
        try:
            ticker = analysis_results.get('ticker', 'N/A')
            company_name = analysis_results.get('company_name', 'N/A')
            
            prompt = f"""
Sen bir "Hakem" (Referee) yatırım uzmanısın. Görevin, iki farklı görüşü dinleyip nihai kararı vermek.

**{company_name} ({ticker}) Hissesi İçin:**

**BOĞA (Bull) Görüşü:**
- Öneri: {bull_opinion.get('recommendation', 'AL')}
- Güven: {bull_opinion.get('confidence', 0.5):.1%}
- Pozitif Noktalar: {', '.join(bull_opinion.get('positive_points', []))}
- Alım Fırsatları: {', '.join(bull_opinion.get('buying_opportunities', []))}
- Özet: {bull_opinion.get('summary', '')}

**AYI (Bear) Görüşü:**
- Öneri: {bear_opinion.get('recommendation', 'BEKLE')}
- Güven: {bear_opinion.get('confidence', 0.5):.1%}
- Riskler: {', '.join(bear_opinion.get('risks', []))}
- Satış Gerekçeleri: {', '.join(bear_opinion.get('selling_reasons', []))}
- Özet: {bear_opinion.get('summary', '')}

**Görevin:**
1. Her iki görüşü objektif olarak değerlendir
2. Hangisinin daha güçlü argümanları olduğunu belirle
3. Nihai kararı ver (AL, SAT, BEKLE)
4. Kararını gerekçelendir

Yanıtı şu JSON formatında ver:
{{
    "final_recommendation": "AL" | "SAT" | "BEKLE",
    "confidence": 0.0-1.0,
    "reasoning": "Karar gerekçesi (2-3 cümle)",
    "bull_weight": 0.0-1.0,
    "bear_weight": 0.0-1.0,
    "summary": "Genel özet"
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
                    'final_recommendation': 'BEKLE',
                    'confidence': 0.5,
                    'reasoning': 'Her iki görüş de dengeli',
                    'bull_weight': 0.5,
                    'bear_weight': 0.5,
                    'summary': response_text[:200]
                }
            
            return {
                'agent': self.name,
                'role': self.role,
                'final_recommendation': result.get('final_recommendation', 'BEKLE'),
                'confidence': result.get('confidence', 0.5),
                'reasoning': result.get('reasoning', ''),
                'bull_weight': result.get('bull_weight', 0.5),
                'bear_weight': result.get('bear_weight', 0.5),
                'summary': result.get('summary', ''),
                'method': 'gemini'
            }
            
        except Exception as e:
            logger.warning(f"Hakem ajanı Gemini kararı hatası: {e}")
            return self._decide_rule_based(bull_opinion, bear_opinion, analysis_results)
    
    def _decide_rule_based(
        self,
        bull_opinion: Dict,
        bear_opinion: Dict,
        analysis_results: Dict
    ) -> Dict:
        """
        Rule-based nihai karar (Gemini yoksa).
        """
        overall_score = analysis_results.get('overall_score', 50.0)
        
        bull_confidence = bull_opinion.get('confidence', 0.5)
        bear_confidence = bear_opinion.get('confidence', 0.5)
        
        # Ağırlıklı karar
        if overall_score > 60:
            bull_weight = 0.7
            bear_weight = 0.3
            final_recommendation = 'AL'
        elif overall_score < 40:
            bull_weight = 0.3
            bear_weight = 0.7
            final_recommendation = 'SAT'
        else:
            bull_weight = 0.5
            bear_weight = 0.5
            final_recommendation = 'BEKLE'
        
        confidence = (bull_confidence * bull_weight) + (bear_confidence * bear_weight)
        
        reasoning = f"Genel skor {overall_score:.1f}/100. Boğa görüşü {bull_weight:.0%}, Ayı görüşü {bear_weight:.0%} ağırlıkta."
        
        return {
            'agent': self.name,
            'role': self.role,
            'final_recommendation': final_recommendation,
            'confidence': confidence,
            'reasoning': reasoning,
            'bull_weight': bull_weight,
            'bear_weight': bear_weight,
            'summary': f"Nihai karar: {final_recommendation} (Güven: {confidence:.1%})",
            'method': 'rule_based'
        }

