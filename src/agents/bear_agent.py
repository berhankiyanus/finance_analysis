"""
Ayı (Bear) Ajanı

Riskleri, olumsuzlukları ve satış gerekçelerini savunur.
"""

from typing import Dict, Optional
from src.logger_config import setup_logger

logger = setup_logger(__name__)


class BearAgent:
    """
    Ayı (Bear) Ajanı - Pesimist yatırım görüşü
    """
    
    def __init__(self, gemini_model=None):
        """
        Ayı ajanını başlatır.
        
        Parametreler:
        ------------
        gemini_model : object
            Gemini model instance'ı (opsiyonel)
        """
        self.gemini_model = gemini_model
        self.name = "Ayı (Bear)"
        self.role = "Risk Analiz Uzmanı"
    
    def analyze(self, analysis_results: Dict) -> Dict:
        """
        Analiz sonuçlarını sadece negatif açıdan yorumlar.
        
        Parametreler:
        ------------
        analysis_results : dict
            Analiz sonuçları
        
        Döndürür:
        --------
        dict
            Ayı ajanının görüşü
        """
        if self.gemini_model:
            return self._analyze_with_gemini(analysis_results)
        
        return self._analyze_rule_based(analysis_results)
    
    def _analyze_with_gemini(self, analysis_results: Dict) -> Dict:
        """
        Gemini ile analiz yapar.
        """
        try:
            ticker = analysis_results.get('ticker', 'N/A')
            company_name = analysis_results.get('company_name', 'N/A')
            
            prompt = f"""
Sen bir "Ayı" (Bear) yatırım uzmanısın. Görevin, {company_name} ({ticker}) hissesi için SADECE RİSKLERİ ve SATIŞ gerekçelerini bulmak.

**Analiz Sonuçları:**
- Genel Skor: {analysis_results.get('overall_score', 50.0):.1f}/100
- Sentiment Skoru: {analysis_results.get('sentiment_score', 50.0):.1f}/100
- Finansal Skor: {analysis_results.get('financial_score', 50.0):.1f}/100

**Görevin:**
1. Sadece riskleri ve olumsuzlukları vurgula
2. Satış gerekçelerini bul
3. Negatif haberleri öne çıkar
4. Pozitif verileri görmezden gel veya minimize et
5. Neden SATILMALI veya BEKLENMELİ sorusuna odaklan

Yanıtı şu JSON formatında ver:
{{
    "recommendation": "SAT" | "BEKLE",
    "confidence": 0.0-1.0,
    "risks": ["Risk 1", "Risk 2"],
    "selling_reasons": ["Gerekçe 1", "Gerekçe 2"],
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
                    'recommendation': 'BEKLE',
                    'confidence': 0.6,
                    'risks': ['Gemini analizi tamamlandı'],
                    'selling_reasons': [],
                    'summary': response_text[:200]
                }
            
            return {
                'agent': self.name,
                'role': self.role,
                'recommendation': result.get('recommendation', 'BEKLE'),
                'confidence': result.get('confidence', 0.6),
                'risks': result.get('risks', []),
                'selling_reasons': result.get('selling_reasons', []),
                'summary': result.get('summary', ''),
                'method': 'gemini'
            }
            
        except Exception as e:
            logger.warning(f"Ayı ajanı Gemini analizi hatası: {e}")
            return self._analyze_rule_based(analysis_results)
    
    def _analyze_rule_based(self, analysis_results: Dict) -> Dict:
        """
        Rule-based analiz (Gemini yoksa).
        """
        overall_score = analysis_results.get('overall_score', 50.0)
        sentiment_score = analysis_results.get('sentiment_score', 50.0)
        financial_score = analysis_results.get('financial_score', 50.0)
        
        risks = []
        selling_reasons = []
        
        # Riskler
        if overall_score < 50:
            risks.append(f"Düşük genel skor ({overall_score:.1f}/100)")
            selling_reasons.append("Zayıf temel analiz")
        
        if sentiment_score < 50:
            risks.append(f"Negatif sentiment ({sentiment_score:.1f}/100)")
            selling_reasons.append("Olumsuz haber akışı")
        
        if financial_score < 50:
            risks.append(f"Zayıf finansal durum ({financial_score:.1f}/100)")
            selling_reasons.append("Finansal göstergeler endişe verici")
        
        # RSI kontrolü
        feature_vector = analysis_results.get('feature_vector', {})
        rsi = feature_vector.get('rsi', 50.0)
        if rsi > 70:
            risks.append(f"RSI aşırı alım bölgesinde ({rsi:.1f})")
            selling_reasons.append("Teknik olarak satış sinyali")
        
        if not risks:
            risks.append("Potansiyel düşüş riski")
        
        confidence = min(0.9, 0.5 + (50 - overall_score) / 100)
        recommendation = 'SAT' if overall_score < 40 else 'BEKLE'
        
        return {
            'agent': self.name,
            'role': self.role,
            'recommendation': recommendation,
            'confidence': confidence,
            'risks': risks,
            'selling_reasons': selling_reasons,
            'summary': f"{analysis_results.get('company_name', 'Hisse')} için riskler mevcut. Dikkatli olunmalı.",
            'method': 'rule_based'
        }

