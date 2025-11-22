"""
KAP Dedektifi Modülü

Faaliyet raporlarındaki metinlerde "satır arası" okuma yapar.
Geçen çeyrek raporuyla bu çeyrek raporu arasındaki dil değişimini analiz eder.
Daha endişeli, daha belirsiz ifadeler vb. tespit eder.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# Gemini API için
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️  google-generativeai yüklü değil. KAP Dedektifi Gemini olmadan çalışamaz.")


def analyze_language_change(
    current_report_text: str,
    previous_report_text: Optional[str] = None,
    gemini_model=None
) -> Dict:
    """
    İki rapor arasındaki dil değişimini analiz eder.
    
    Parametreler:
    ------------
    current_report_text : str
        Mevcut çeyrek raporu metni
    previous_report_text : str
        Önceki çeyrek raporu metni (opsiyonel)
    gemini_model : object
        Gemini model instance'ı
    
    Döndürür:
    --------
    dict
        Dil değişimi analizi
    """
    if not GEMINI_AVAILABLE or gemini_model is None:
        return {
            'success': False,
            'error': 'Gemini API kullanılamıyor',
            'method': 'gemini_unavailable'
        }
    
    try:
        if previous_report_text:
            # İki raporu karşılaştır
            prompt = f"""
Sen bir finansal dil analiz uzmanısın. İki faaliyet raporu arasındaki dil değişimini analiz et.

**ÖNCEKİ ÇEYREK RAPORU:**
{previous_report_text[:5000]}  # İlk 5000 karakter

**MEVCUT ÇEYREK RAPORU:**
{current_report_text[:5000]}  # İlk 5000 karakter

**Görevin:**
1. Dil tonunu karşılaştır (daha endişeli mi? daha iyimser mi?)
2. Belirsizlik ifadelerini tespit et ("belirsizlik", "risk", "zorluk" kelimeleri artmış mı?)
3. Olumsuz kelime kullanımını karşılaştır
4. Yönetim kurulu ifadelerindeki değişimi analiz et

Yanıtı şu JSON formatında ver:
{{
    "tone_change": "more_concerned" | "more_optimistic" | "similar",
    "uncertainty_increase": 0.0-1.0,
    "negative_word_increase": 0.0-1.0,
    "key_changes": [
        "Değişiklik 1",
        "Değişiklik 2"
    ],
    "red_flags": [
        "Kırmızı bayrak 1",
        "Kırmızı bayrak 2"
    ],
    "summary": "Genel özet"
}}
"""
        else:
            # Sadece mevcut raporu analiz et
            prompt = f"""
Sen bir finansal dil analiz uzmanısın. Bir faaliyet raporundaki endişe verici ifadeleri tespit et.

**RAPOR:**
{current_report_text[:5000]}  # İlk 5000 karakter

**Görevin:**
1. Belirsizlik ifadelerini tespit et
2. Risk vurgularını bul
3. Olumsuz kelime kullanımını analiz et
4. Yönetim kurulu ifadelerindeki endişe seviyesini değerlendir

Yanıtı şu JSON formatında ver:
{{
    "uncertainty_score": 0.0-1.0,
    "risk_mentions": ["Risk 1", "Risk 2"],
    "negative_keywords": ["Kelime 1", "Kelime 2"],
    "concern_level": "high" | "medium" | "low",
    "red_flags": [
        "Kırmızı bayrak 1",
        "Kırmızı bayrak 2"
    ],
    "summary": "Genel özet"
}}
"""
        
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        
        # JSON'u parse et
        import json
        import re
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                'error': 'JSON parse edilemedi',
                'raw_response': response_text[:500]
            }
        
        return {
            'success': True,
            'analysis': result,
            'method': 'gemini_comparison' if previous_report_text else 'gemini_single'
        }
        
    except Exception as e:
        logger.error(f"KAP Dedektifi analizi hatası: {e}")
        return {
            'success': False,
            'error': str(e),
            'method': 'error'
        }


def detect_red_flags(text: str) -> List[str]:
    """
    Metindeki kırmızı bayrakları (red flags) tespit eder.
    
    Parametreler:
    ------------
    text : str
        Analiz edilecek metin
    
    Döndürür:
    --------
    list
        Tespit edilen kırmızı bayraklar
    """
    text_lower = text.lower()
    red_flags = []
    
    # Endişe verici ifadeler
    concern_keywords = [
        'belirsizlik', 'belirsiz', 'risk', 'tehlike', 'zorluk', 'zorlaşmak',
        'düşüş', 'azalma', 'kayıp', 'zarar', 'endişe', 'kaygı',
        'beklentilerin altında', 'hedefin altında', 'tahminin altında',
        'olumsuz etki', 'negatif etki', 'olumsuz gelişme'
    ]
    
    for keyword in concern_keywords:
        if keyword in text_lower:
            # Cümleyi bul
            sentences = text.split('.')
            for sentence in sentences:
                if keyword in sentence.lower():
                    red_flags.append(f"'{keyword}' ifadesi: {sentence.strip()[:100]}")
                    break
    
    # Belirsizlik ifadeleri
    uncertainty_keywords = [
        'olabilir', 'olmayabilir', 'muhtemel', 'olası', 'belki',
        'tahmin', 'beklenti', 'umut', 'umuluyor'
    ]
    
    uncertainty_count = sum(1 for kw in uncertainty_keywords if kw in text_lower)
    if uncertainty_count > 10:
        red_flags.append(f"Yüksek belirsizlik ifadesi sayısı: {uncertainty_count}")
    
    return red_flags[:10]  # İlk 10'u döndür


if __name__ == "__main__":
    # Test
    print("=== KAP Dedektifi Test ===\n")
    
    current_report = """
    Şirketimiz 2024 yılının ilk çeyreğinde önemli zorluklarla karşılaştı.
    Enerji maliyetlerindeki artış ve döviz kurlarındaki belirsizlik nedeniyle
    kâr marjlarımız beklentilerin altında kaldı. Gelecek dönem için belirsizlikler devam ediyor.
    """
    
    previous_report = """
    Şirketimiz 2023 yılının son çeyreğinde güçlü bir performans sergiledi.
    Enerji maliyetleri kontrol altında ve kâr marjlarımız hedeflerimizi aştı.
    Gelecek dönem için iyimseriz.
    """
    
    red_flags = detect_red_flags(current_report)
    print(f"Tespit edilen kırmızı bayraklar: {len(red_flags)}")
    for flag in red_flags:
        print(f"  - {flag}")

