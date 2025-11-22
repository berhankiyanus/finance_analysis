"""
Yatırım Kurulu (Investment Board)

Boğa, Ayı ve Hakem ajanlarını bir araya getirir ve tartışma simülasyonu yapar.
"""

from typing import Dict, Optional
from .bull_agent import BullAgent
from .bear_agent import BearAgent
from .referee_agent import RefereeAgent
from src.logger_config import setup_logger

logger = setup_logger(__name__)


class InvestmentBoard:
    """
    Yatırım Kurulu - 3 ajanın tartışmasını simüle eder
    """
    
    def __init__(self, gemini_model=None):
        """
        Yatırım kurulunu başlatır.
        
        Parametreler:
        ------------
        gemini_model : object
            Gemini model instance'ı (opsiyonel)
        """
        self.bull = BullAgent(gemini_model)
        self.bear = BearAgent(gemini_model)
        self.referee = RefereeAgent(gemini_model)
        self.gemini_model = gemini_model
    
    def conduct_meeting(self, analysis_results: Dict) -> Dict:
        """
        Yatırım kurulu toplantısını yapar.
        
        Parametreler:
        ------------
        analysis_results : dict
            Analiz sonuçları
        
        Döndürür:
        --------
        dict
            Toplantı sonuçları ve nihai karar
        """
        logger.info("🏛️ Yatırım Kurulu toplantısı başlatılıyor...")
        
        # Boğa görüşü
        logger.info("🐂 Boğa ajanı görüşünü sunuyor...")
        bull_opinion = self.bull.analyze(analysis_results)
        
        # Ayı görüşü
        logger.info("🐻 Ayı ajanı görüşünü sunuyor...")
        bear_opinion = self.bear.analyze(analysis_results)
        
        # Hakem kararı
        logger.info("⚖️ Hakem ajanı karar veriyor...")
        final_decision = self.referee.make_final_decision(
            bull_opinion,
            bear_opinion,
            analysis_results
        )
        
        # Toplantı özeti
        meeting_summary = self._create_meeting_summary(
            bull_opinion,
            bear_opinion,
            final_decision
        )
        
        return {
            'success': True,
            'bull_opinion': bull_opinion,
            'bear_opinion': bear_opinion,
            'final_decision': final_decision,
            'meeting_summary': meeting_summary,
            'ticker': analysis_results.get('ticker', 'N/A'),
            'company_name': analysis_results.get('company_name', 'N/A')
        }
    
    def _create_meeting_summary(
        self,
        bull_opinion: Dict,
        bear_opinion: Dict,
        final_decision: Dict
    ) -> str:
        """
        Toplantı özeti oluşturur.
        """
        summary = f"""
# 🏛️ Yatırım Kurulu Toplantı Özeti

## 🐂 Boğa (Bull) Görüşü
**Öneri:** {bull_opinion.get('recommendation', 'AL')}
**Güven:** {bull_opinion.get('confidence', 0.5):.1%}

**Pozitif Noktalar:**
{chr(10).join(f"- {point}" for point in bull_opinion.get('positive_points', []))}

**Alım Fırsatları:**
{chr(10).join(f"- {opp}" for opp in bull_opinion.get('buying_opportunities', []))}

**Özet:** {bull_opinion.get('summary', '')}

---

## 🐻 Ayı (Bear) Görüşü
**Öneri:** {bear_opinion.get('recommendation', 'BEKLE')}
**Güven:** {bear_opinion.get('confidence', 0.5):.1%}

**Riskler:**
{chr(10).join(f"- {risk}" for risk in bear_opinion.get('risks', []))}

**Satış Gerekçeleri:**
{chr(10).join(f"- {reason}" for reason in bear_opinion.get('selling_reasons', []))}

**Özet:** {bear_opinion.get('summary', '')}

---

## ⚖️ Hakem (Referee) Nihai Kararı
**Öneri:** {final_decision.get('final_recommendation', 'BEKLE')}
**Güven:** {final_decision.get('confidence', 0.5):.1%}

**Gerekçe:** {final_decision.get('reasoning', '')}

**Ağırlıklar:**
- Boğa görüşü: {final_decision.get('bull_weight', 0.5):.0%}
- Ayı görüşü: {final_decision.get('bear_weight', 0.5):.0%}

**Özet:** {final_decision.get('summary', '')}
"""
        
        return summary


if __name__ == "__main__":
    # Test
    print("=== Yatırım Kurulu Test ===\n")
    
    test_results = {
        'ticker': 'THYAO',
        'company_name': 'Türk Hava Yolları',
        'overall_score': 65.0,
        'sentiment_score': 70.0,
        'financial_score': 60.0,
        'feature_vector': {'rsi': 45.0}
    }
    
    board = InvestmentBoard()
    meeting = board.conduct_meeting(test_results)
    
    print(meeting['meeting_summary'])

