"""
Şeytanın Avukatı Modülü

Kullanıcı bir hisseyi analiz ettiğinde ve sonuç "AL" çıktığında,
sadece negatif verileri ve riskleri bulmaya odaklanır.
Bu, kullanıcıyı aşırı güven (confirmation bias) tuzağından korur.
"""

import os
from typing import Dict, Optional
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# Gemini API için
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️  google-generativeai yüklü değil. Şeytanın Avukatı modu Gemini olmadan çalışamaz.")


def analyze_why_not_to_buy(
    ticker: str,
    company_name: str,
    analysis_results: Dict,
    gemini_model=None
) -> Dict:
    """
    "Neden almamalıyım?" analizi yapar.
    Sadece negatif verileri ve riskleri vurgular.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    company_name : str
        Şirket adı
    analysis_results : dict
        Analiz sonuçları (sentiment_score, financial_score, news_df, vb.)
    gemini_model : object
        Gemini model instance'ı (opsiyonel)
    
    Döndürür:
    --------
    dict
        Risk analizi ve neden almamalıyım gerekçeleri
    """
    if not GEMINI_AVAILABLE or gemini_model is None:
        # Gemini yoksa, rule-based analiz yap
        return _analyze_risks_rule_based(ticker, company_name, analysis_results)
    
    try:
        # Analiz sonuçlarını topla
        sentiment_score = analysis_results.get('sentiment_score', 50.0)
        financial_score = analysis_results.get('financial_score', 50.0)
        overall_score = analysis_results.get('overall_score', 50.0)
        
        # Haberleri al
        news_df = analysis_results.get('news_df', None)
        negative_news = []
        if news_df is not None and not news_df.empty:
            # Negatif haberleri filtrele
            if 'sentiment_class' in news_df.columns:
                negative_news = news_df[news_df['sentiment_class'] == 'negative'].head(5)
            elif 'sentiment' in news_df.columns:
                negative_news = news_df[news_df['sentiment'] < 0].head(5)
        
        # Teknik göstergeler
        feature_vector = analysis_results.get('feature_vector', {})
        rsi = feature_vector.get('rsi', 50.0)
        volatility = feature_vector.get('volatility', 0.0)
        
        # Fiyat verisi
        price_df = analysis_results.get('price_df', None)
        price_change_30d = analysis_results.get('price_change_30d', 0.0)
        
        # Negatif haber özeti
        negative_news_summary = ""
        if not negative_news.empty:
            negative_news_summary = "\n".join([
                f"- {row.get('title', 'Başlık yok')}" 
                for _, row in negative_news.iterrows()
            ])
        
        # Gemini'ye sor
        prompt = f"""
Sen bir "Şeytanın Avukatı" (Devil's Advocate) finansal analistisin. 
Görevin, bir yatırımcıyı aşırı güven (confirmation bias) tuzağından korumaktır.

Bir yatırımcı, {company_name} ({ticker}) hissesini almayı düşünüyor.
Analiz sonuçları genel olarak olumlu görünüyor, ancak sen sadece RİSKLERİ ve NEGATİF YÖNLERİ bulmalısın.

**Mevcut Analiz Sonuçları:**
- Genel Skor: {overall_score:.1f}/100
- Sentiment Skoru: {sentiment_score:.1f}/100
- Finansal Skor: {financial_score:.1f}/100
- RSI: {rsi:.1f}
- Son 30 Günlük Değişim: {price_change_30d:+.2f}%

**Negatif Haberler:**
{negative_news_summary if negative_news_summary else "Negatif haber bulunamadı"}

**Görevin:**
Bu hisseyi ALMAMAK için en güçlü 5 gerekçeyi bul. Sadece riskleri, olumsuzlukları ve endişe verici noktaları vurgula.
Pozitif yönleri görmezden gel, sadece "Neden almamalıyım?" sorusuna odaklan.

Yanıtı şu JSON formatında ver:
{{
    "risks": [
        {{
            "title": "Risk başlığı",
            "description": "Detaylı açıklama",
            "severity": "high" | "medium" | "low",
            "evidence": "Kanıt veya veri"
        }}
    ],
    "summary": "Genel risk özeti (2-3 cümle)",
    "recommendation": "ALMA veya BEKLE önerisi"
}}
"""
        
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # JSON'u parse et
        import json
        import re
        
        # JSON bloğunu bul
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # JSON bulunamazsa, metni parse et
            result = {
                'risks': [
                    {
                        'title': 'Analiz Hatası',
                        'description': response_text,
                        'severity': 'medium',
                        'evidence': 'Gemini yanıtı parse edilemedi'
                    }
                ],
                'summary': response_text[:200],
                'recommendation': 'BEKLE'
            }
        
        return {
            'success': True,
            'risks': result.get('risks', []),
            'summary': result.get('summary', ''),
            'recommendation': result.get('recommendation', 'BEKLE'),
            'ticker': ticker,
            'company_name': company_name
        }
        
    except Exception as e:
        logger.error(f"Şeytanın Avukatı analizi hatası: {e}")
        # Fallback: Rule-based analiz
        return _analyze_risks_rule_based(ticker, company_name, analysis_results)


def _analyze_risks_rule_based(
    ticker: str,
    company_name: str,
    analysis_results: Dict
) -> Dict:
    """
    Rule-based risk analizi (Gemini yoksa kullanılır).
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    company_name : str
        Şirket adı
    analysis_results : dict
        Analiz sonuçları
    
    Döndürür:
    --------
    dict
        Risk analizi
    """
    risks = []
    
    # Skor analizi
    overall_score = analysis_results.get('overall_score', 50.0)
    sentiment_score = analysis_results.get('sentiment_score', 50.0)
    financial_score = analysis_results.get('financial_score', 50.0)
    
    # Risk 1: Düşük skorlar
    if overall_score < 50:
        risks.append({
            'title': 'Düşük Genel Skor',
            'description': f'Genel skor {overall_score:.1f}/100, bu yatırım için yeterli değil.',
            'severity': 'high',
            'evidence': f'Genel skor: {overall_score:.1f}/100'
        })
    
    # Risk 2: Negatif sentiment
    if sentiment_score < 40:
        risks.append({
            'title': 'Negatif Haber Sentiment',
            'description': f'Sentiment skoru {sentiment_score:.1f}/100, piyasada olumsuz algı var.',
            'severity': 'high',
            'evidence': f'Sentiment skoru: {sentiment_score:.1f}/100'
        })
    
    # Risk 3: RSI aşırı alım
    feature_vector = analysis_results.get('feature_vector', {})
    rsi = feature_vector.get('rsi', 50.0)
    if rsi > 70:
        risks.append({
            'title': 'RSI Aşırı Alım',
            'description': f'RSI {rsi:.1f}, hisse aşırı alım bölgesinde. Düşüş riski yüksek.',
            'severity': 'medium',
            'evidence': f'RSI: {rsi:.1f}'
        })
    
    # Risk 4: Yüksek volatilite
    volatility = feature_vector.get('volatility', 0.0)
    if volatility > 0.05:  # %5'ten fazla
        risks.append({
            'title': 'Yüksek Volatilite',
            'description': f'Volatilite {volatility:.2%}, fiyat dalgalanmaları yüksek. Riskli.',
            'severity': 'medium',
            'evidence': f'Volatilite: {volatility:.2%}'
        })
    
    # Risk 5: Fiyat düşüşü
    price_change_30d = analysis_results.get('price_change_30d', 0.0)
    if price_change_30d < -10:
        risks.append({
            'title': 'Son 30 Günde Büyük Düşüş',
            'description': f'Son 30 günde {price_change_30d:.2f}% düşüş var. Trend olumsuz.',
            'severity': 'high',
            'evidence': f'30 günlük değişim: {price_change_30d:.2f}%'
        })
    
    # Risk 6: Dummy veri kullanımı
    if analysis_results.get('is_dummy_news', False):
        risks.append({
            'title': 'Dummy Veri Kullanımı',
            'description': 'Analiz dummy (test) verisi ile yapıldı. Sonuçlar güvenilir değil.',
            'severity': 'high',
            'evidence': 'Dummy haber verisi tespit edildi'
        })
    
    if analysis_results.get('dummy_price_data_detected', False):
        risks.append({
            'title': 'Dummy Fiyat Verisi',
            'description': 'Fiyat verisi dummy (test) verisi. Analiz güvenilir değil.',
            'severity': 'high',
            'evidence': 'Dummy fiyat verisi tespit edildi'
        })
    
    # Özet
    if not risks:
        summary = "Belirgin bir risk tespit edilmedi. Ancak yine de dikkatli olun."
        recommendation = "DİKKATLİ AL"
    else:
        high_risks = [r for r in risks if r['severity'] == 'high']
        if high_risks:
            summary = f"{len(high_risks)} yüksek risk tespit edildi. Yatırım yapmadan önce dikkatlice değerlendirin."
            recommendation = "ALMA"
        else:
            summary = f"{len(risks)} orta seviye risk tespit edildi. Dikkatli olun."
            recommendation = "BEKLE"
    
    return {
        'success': True,
        'risks': risks,
        'summary': summary,
        'recommendation': recommendation,
        'ticker': ticker,
        'company_name': company_name,
        'method': 'rule_based'
    }


if __name__ == "__main__":
    # Test
    print("=== Şeytanın Avukatı Test ===\n")
    
    # Test analiz sonuçları
    test_results = {
        'sentiment_score': 45.0,
        'financial_score': 55.0,
        'overall_score': 50.0,
        'feature_vector': {
            'rsi': 75.0,
            'volatility': 0.06
        },
        'price_change_30d': -12.5,
        'news_df': pd.DataFrame({
            'title': ['Negatif Haber 1', 'Negatif Haber 2'],
            'sentiment_class': ['negative', 'negative']
        })
    }
    
    result = _analyze_risks_rule_based("THYAO", "Türk Hava Yolları", test_results)
    
    print(f"Öneri: {result['recommendation']}")
    print(f"\nÖzet: {result['summary']}")
    print(f"\nRiskler ({len(result['risks'])}):")
    for i, risk in enumerate(result['risks'], 1):
        print(f"{i}. [{risk['severity'].upper()}] {risk['title']}")
        print(f"   {risk['description']}")

