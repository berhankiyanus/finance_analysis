"""
Siyasi Haber Sınıflandırıcı Modülü

Haberleri siyasi/ekonomik/şirket kategorilerine ayırır ve siyasi etki skorunu hesaplar.
Tarihsel olay korelasyonu için kritik bir bileşendir.
"""

import os
from typing import Dict, Optional
import json
import re

# Gemini API için
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai paketi yüklü değil. Basit sınıflandırma kullanılacak.")


def classify_news_political_impact(news_text: str, news_title: str = "") -> Dict:
    """
    Haberi siyasi/ekonomik/şirket kategorisine ayırır ve etki skorunu hesaplar.
    
    Parametreler:
    ------------
    news_text : str
        Haber metni
    news_title : str
        Haber başlığı (opsiyonel)
    
    Döndürür:
    --------
    dict
        {
            'category': 'political',  # political, economic, company, market
            'subcategory': 'government_stability',  # government_stability, foreign_policy, economic_policy, etc.
            'political_impact_score': 0.75,  # 0-1 arası
            'market_relevance': 0.90,  # Piyasaya ne kadar etkili? (0-1)
            'expected_market_reaction': 'negative',  # positive, negative, neutral
            'confidence': 0.85
        }
    """
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key or not GEMINI_AVAILABLE:
        # Gemini yoksa basit kural tabanlı sınıflandırma
        return _simple_political_classifier(news_text, news_title)
    
    try:
        genai.configure(api_key=gemini_api_key)
        # Model isimlerini sırayla dene
        model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        model = None
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                # Test et
                test_response = model.generate_content("Test")
                if test_response and test_response.text:
                    break
            except Exception:
                continue
        
        if model is None:
            return _simple_political_classifier(news_text, news_title)
        
        prompt = f"""
Aşağıdaki haber metnini analiz et ve şu bilgileri JSON formatında döndür:

1. **Kategori:** Haber siyasi mi, ekonomik mi, şirket bazlı mı, yoksa genel piyasa haberi mi?
   - "political": Siyasi olaylar (hükümet, bakan, seçim, dış politika)
   - "economic": Ekonomik politika (faiz, enflasyon, bütçe)
   - "company": Belirli bir şirket hakkında
   - "market": Genel piyasa haberi

2. **Alt Kategori (siyasi ise):**
   - "government_stability": Hükümet istikrarı
   - "foreign_policy": Dış politika
   - "economic_policy": Ekonomi yönetimi
   - "election": Seçim
   - "other": Diğer

3. **Siyasi Etki Skoru:** 0-1 arası (siyasi değilse 0)

4. **Piyasa İlgisi:** Bu haberin borsaya etkisi ne kadar? 0-1 arası

5. **Beklenen Piyasa Tepkisi:** "positive", "negative", "neutral"

6. **Güven:** Analiz güvenilirliği 0-1 arası

Haber Başlığı: {news_title}
Haber Metni: {news_text[:1000]}

Sadece JSON formatında yanıt ver, başka açıklama yapma:
{{
    "category": "...",
    "subcategory": "...",
    "political_impact_score": 0.0,
    "market_relevance": 0.0,
    "expected_market_reaction": "...",
    "confidence": 0.0
}}
"""
        
        response = model.generate_content(prompt)
        # JSON parse et
        json_match = re.search(r'\{[^}]+\}', response.text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            # Değerleri normalize et
            result['political_impact_score'] = float(result.get('political_impact_score', 0))
            result['market_relevance'] = float(result.get('market_relevance', 0))
            result['confidence'] = float(result.get('confidence', 0.5))
            return result
        else:
            return _simple_political_classifier(news_text, news_title)
            
    except Exception as e:
        print(f"⚠️  Gemini siyasi sınıflandırma hatası: {e}")
        return _simple_political_classifier(news_text, news_title)


def _simple_political_classifier(news_text: str, news_title: str = "") -> Dict:
    """
    Basit kural tabanlı siyasi sınıflandırma (Gemini yoksa).
    """
    text_lower = (news_title + " " + news_text).lower()
    
    # Siyasi anahtar kelimeler
    political_keywords = ['bakan', 'hükümet', 'cumhurbaşkanı', 'başbakan', 'seçim', 
                         'milletvekili', 'parti', 'koalisyon', 'istifa', 'güvenoyu',
                         'dış politika', 'diplomasi', 'anayasa', 'meclis', 'bakanlar kurulu',
                         'hükümet krizi', 'güven oylaması', 'erken seçim']
    
    # Ekonomik anahtar kelimeler
    economic_keywords = ['faiz', 'enflasyon', 'tcmb', 'merkez bankası', 'bütçe',
                        'maliye', 'hazine', 'borç', 'açık', 'döviz', 'kur', 'rezerv']
    
    # Şirket anahtar kelimeleri
    company_keywords = ['şirket', 'hisse', 'borsa', 'yatırım', 'kar', 'zarar', 'ciro',
                       'bilanço', 'temettü', 'halka arz']
    
    political_score = sum(1 for keyword in political_keywords if keyword in text_lower) / max(len(political_keywords), 1)
    economic_score = sum(1 for keyword in economic_keywords if keyword in text_lower) / max(len(economic_keywords), 1)
    company_score = sum(1 for keyword in company_keywords if keyword in text_lower) / max(len(company_keywords), 1)
    
    # Kategori belirleme
    if political_score > 0.3:
        category = 'political'
        if 'istifa' in text_lower or 'güvenoyu' in text_lower or 'kriz' in text_lower:
            subcategory = 'government_stability'
        elif 'dış' in text_lower or 'diplomasi' in text_lower:
            subcategory = 'foreign_policy'
        elif 'ekonomi' in text_lower or 'maliye' in text_lower:
            subcategory = 'economic_policy'
        elif 'seçim' in text_lower:
            subcategory = 'election'
        else:
            subcategory = 'other'
    elif economic_score > 0.3:
        category = 'economic'
        subcategory = 'economic_policy'
    elif company_score > 0.3:
        category = 'company'
        subcategory = 'financial_results'
    else:
        category = 'market'
        subcategory = 'other'
    
    # Beklenen piyasa tepkisi
    negative_keywords = ['istifa', 'kriz', 'düşüş', 'zarar', 'kayıp', 'sorun', 'skandal']
    positive_keywords = ['büyüme', 'artış', 'başarı', 'kazanç', 'iyileşme', 'yükseliş']
    
    negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)
    positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
    
    if negative_count > positive_count:
        expected_reaction = 'negative'
    elif positive_count > negative_count:
        expected_reaction = 'positive'
    else:
        expected_reaction = 'neutral'
    
    return {
        'category': category,
        'subcategory': subcategory,
        'political_impact_score': min(political_score, 1.0),
        'market_relevance': min(max(political_score, economic_score, company_score), 1.0),
        'expected_market_reaction': expected_reaction,
        'confidence': 0.6  # Basit sınıflandırma için düşük güven
    }


def batch_classify_news(news_list: list) -> list:
    """
    Birden fazla haberi toplu olarak sınıflandırır.
    
    Parametreler:
    ------------
    news_list : list
        Her haber için dict: {'title': str, 'text': str, ...}
    
    Döndürür:
    --------
    list
        Her haber için sınıflandırma sonucu eklenmiş dict'ler
    """
    results = []
    for news in news_list:
        classification = classify_news_political_impact(
            news_text=news.get('text', news.get('summary', '')),
            news_title=news.get('title', '')
        )
        # Orijinal haber dict'ine ekle
        news_with_classification = news.copy()
        news_with_classification['political_classification'] = classification
        results.append(news_with_classification)
    
    return results


if __name__ == "__main__":
    print("=== Siyasi Haber Sınıflandırıcı Test ===\n")
    
    # Test haberleri
    test_news = [
        {
            'title': 'Ekonomi Bakanı İstifa Etti',
            'text': 'Ekonomi Bakanı bugün istifa etti. Hükümet krizi yaşanıyor.'
        },
        {
            'title': 'TCMB Faiz Kararı Açıklandı',
            'text': 'Merkez Bankası faiz oranını %50\'ye yükseltti.'
        },
        {
            'title': 'THYAO Kar Açıkladı',
            'text': 'Türk Hava Yolları yılın ilk çeyreğinde rekor kar açıkladı.'
        }
    ]
    
    for news in test_news:
        print(f"\n📰 Haber: {news['title']}")
        classification = classify_news_political_impact(news['text'], news['title'])
        print(f"   Kategori: {classification['category']}")
        print(f"   Alt Kategori: {classification['subcategory']}")
        print(f"   Siyasi Etki: {classification['political_impact_score']:.2f}")
        print(f"   Piyasa İlgisi: {classification['market_relevance']:.2f}")
        print(f"   Beklenen Tepki: {classification['expected_market_reaction']}")

