"""
Gemini API Raporlama Modülü

Gemini API kullanarak otomatik finansal analist raporları oluşturur.
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai paketi yüklü değil. Gemini API kullanılamayacak.")


def generate_analyst_report(
    company_name: str,
    ticker: str,
    technical_signal: str,
    top_features: List[tuple],
    hisse_sentiment_score: float,
    hisse_news_summary: str,
    piyasa_sentiment_score: float,
    piyasa_news_summary: str,
    gemini_model=None,
    historical_context: str = ""
) -> str:
    """
    Gemini API kullanarak otomatik analist raporu oluşturur.
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı
    ticker : str
        Borsa kodu
    technical_signal : str
        Teknik model sinyali ('AL', 'SAT', 'TUT')
    top_features : list
        En önemli feature'lar [(feature_name, shap_value), ...]
    hisse_sentiment_score : float
        Hisse bazlı duygu skoru (0-1)
    hisse_news_summary : str
        Hisse bazlı haber özeti
    piyasa_sentiment_score : float
        Piyasa geneli duygu skoru (0-1)
    piyasa_news_summary : str
        Piyasa geneli haber özeti
    gemini_model
        Gemini API modeli (eğer varsa)
    
    Döndürür:
    --------
    str
        Analist raporu (Türkçe, 1 paragraf)
    """
    
    if not gemini_model:
        # Gemini modeli yoksa basit rapor
        return _generate_simple_report(
            company_name, ticker, technical_signal, top_features,
            hisse_sentiment_score, hisse_news_summary,
            piyasa_sentiment_score, piyasa_news_summary
        )
    
    try:
        # Top feature'ları formatla
        feature_text = "\n".join([
            f"- {name}: {value:.4f}" for name, value in top_features[:5]
        ])
        
        prompt = f"""Sen, Türkiye piyasaları (BIST) konusunda uzmanlaşmış, deneyimli bir kıdemli borsa analistisin. 
Görevin, sana vereceğim yapılandırılmış verileri analiz ederek, bir yatırımcıya yönelik doğal dilde, 
akıcı ve profesyonel bir (1 paragraflık) günlük analiz bülteni yazmak. 

KESİNLİKLE yatırım tavsiyesi verme, sadece mevcut durumu ve model sinyallerini yorumla.

ŞİRKET: {company_name} ({ticker})

TEKNİK MODEL SİNYALİ: {technical_signal}

MODELİN DAYANDIĞI EN ÖNEMLİ ÖZELLİKLER (XAI):
{feature_text}

HİSSE BAZLI DUYGU SKORU: {hisse_sentiment_score:.2f} ({'Pozitif' if hisse_sentiment_score > 0.6 else 'Negatif' if hisse_sentiment_score < 0.4 else 'Nötr'})

HİSSE HABER ÖZETİ (AI): {hisse_news_summary}

GENEL PİYASA DUYGU SKORU: {piyasa_sentiment_score:.2f} ({'Pozitif' if piyasa_sentiment_score > 0.6 else 'Negatif' if piyasa_sentiment_score < 0.4 else 'Nötr'})

PİYASA HABER ÖZETİ (AI): {piyasa_news_summary}

{historical_context if historical_context else ""}

GÖREVİN:
Yukarıdaki verileri kullanarak, {company_name} ({ticker}) hissesi için bugünün analiz bültenini yaz. 
Rapor şunları içermeli:
1. Teknik model sinyalinin yorumu
2. En önemli faktörlerin (feature'ların) etkisi
3. Hisse bazlı haberlerin etkisi
4. Genel piyasa durumunun etkisi
5. Genel değerlendirme

Raporu:
- Türkçe yaz
- 1 paragraf (yaklaşık 150-200 kelime)
- Profesyonel ve objektif ton
- Yatırım tavsiyesi VERME
- Sadece mevcut durumu analiz et

Raporu doğrudan yaz, başka hiçbir açıklama ekleme."""
        
        response = gemini_model.generate_content(prompt)
        report = response.text.strip()
        
        # Eğer JSON formatında gelirse extract et
        if "```" in report:
            report = report.split("```")[-1].strip()
            if report.startswith("json"):
                report = report[4:].strip()
        
        return report
        
    except Exception as e:
        print(f"⚠️  Gemini rapor oluşturma hatası: {e}")
        return _generate_simple_report(
            company_name, ticker, technical_signal, top_features,
            hisse_sentiment_score, hisse_news_summary,
            piyasa_sentiment_score, piyasa_news_summary
        )


def _generate_simple_report(
    company_name: str,
    ticker: str,
    technical_signal: str,
    top_features: List[tuple],
    hisse_sentiment_score: float,
    hisse_news_summary: str,
    piyasa_sentiment_score: float,
    piyasa_news_summary: str
) -> str:
    """
    Gemini olmadan basit rapor oluşturur.
    """
    signal_text = {
        'AL': 'alım',
        'SAT': 'satım',
        'TUT': 'tutma'
    }.get(technical_signal, technical_signal)
    
    hisse_sentiment_text = 'pozitif' if hisse_sentiment_score > 0.6 else 'negatif' if hisse_sentiment_score < 0.4 else 'nötr'
    piyasa_sentiment_text = 'pozitif' if piyasa_sentiment_score > 0.6 else 'negatif' if piyasa_sentiment_score < 0.4 else 'nötr'
    
    top_feature_names = [name for name, _ in top_features[:3]]
    
    report = f"""
{company_name} ({ticker}) için teknik model {signal_text} sinyali veriyor. 
Modelin en önemli dayanakları: {', '.join(top_feature_names)}. 
Hisse bazlı haberler {hisse_sentiment_text} bir ton taşırken ({hisse_news_summary[:100]}...), 
genel piyasa durumu {piyasa_sentiment_text} görünüyor ({piyasa_news_summary[:100]}...). 
Yatırımcıların mevcut durumu dikkatle değerlendirmesi önerilir.
""".strip()
    
    return report


def summarize_news_headlines(
    news_headlines: List[Dict],
    gemini_model=None
) -> str:
    """
    Haber başlıklarını analiz ederek özet oluşturur.
    
    Parametreler:
    ------------
    news_headlines : list
        Her haber için dict: {'title': str, 'summary': str, 'sentiment': str}
    gemini_model
        Gemini API modeli (eğer varsa)
    
    Döndürür:
    --------
    str
        Haber özeti (2-3 cümle)
    """
    
    if not news_headlines:
        return "Son dönemde önemli bir haber bulunamadı."
    
    if not gemini_model:
        # Basit özet
        return _generate_simple_news_summary(news_headlines)
    
    try:
        # İlk 15 haberi al
        headlines_text = []
        for i, news in enumerate(news_headlines[:15], 1):
            title = news.get('title', '')
            summary = news.get('summary', '')
            sentiment = news.get('sentiment', 'neutral')
            headlines_text.append(f"{i}. [{sentiment.upper()}] {title}\n   {summary[:150]}")
        
        prompt = f"""Aşağıdaki {len(headlines_text)} ekonomi haber başlığını ve kısa özetini analiz et. 
Türk yatırımcılar için piyasayı etkileyecek en önemli 3 ana temayı belirle ve 
bunları 2-3 cümlelik tek bir paragrafta özetle.

HABERLER:
{chr(10).join(headlines_text)}

Özeti Türkçe olarak, doğrudan yaz. Başka hiçbir açıklama ekleme."""
        
        response = gemini_model.generate_content(prompt)
        summary = response.text.strip()
        
        # Eğer JSON formatında gelirse extract et
        if "```" in summary:
            summary = summary.split("```")[-1].strip()
        
        return summary
        
    except Exception as e:
        print(f"⚠️  Gemini haber özetleme hatası: {e}")
        return _generate_simple_news_summary(news_headlines)


def _generate_simple_news_summary(news_headlines: List[Dict]) -> str:
    """
    Basit haber özeti oluşturur.
    """
    if not news_headlines:
        return "Son dönemde önemli bir haber bulunamadı."
    
    # Sentiment dağılımı
    sentiments = [news.get('sentiment', 'neutral') for news in news_headlines[:10]]
    pos_count = sentiments.count('positive')
    neg_count = sentiments.count('negative')
    neu_count = sentiments.count('neutral')
    
    if pos_count > neg_count:
        sentiment_text = "genel olarak pozitif"
    elif neg_count > pos_count:
        sentiment_text = "genel olarak negatif"
    else:
        sentiment_text = "karışık"
    
    # İlk birkaç haberin başlıklarını al
    titles = [news.get('title', '')[:50] for news in news_headlines[:3]]
    
    summary = f"Son dönemde {len(news_headlines)} haber bulundu. Haberler {sentiment_text} bir ton taşıyor. "
    summary += f"Öne çıkan konular: {', '.join(titles)}."
    
    return summary


if __name__ == "__main__":
    print("=== Gemini API Raporlama Modülü Test ===\n")
    
    # Test
    if GEMINI_AVAILABLE:
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            # Model isimlerini sırayla dene (en güncelden eskiye)
            model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
            gemini_model = None
            
            for model_name in model_names:
                try:
                    gemini_model = genai.GenerativeModel(model_name)
                    # Test et
                    test_response = gemini_model.generate_content("Test")
                    if test_response and test_response.text:
                        print(f"✅ Gemini API yüklendi: {model_name}")
                        break
                except Exception as model_error:
                    print(f"⚠️  {model_name} modeli çalışmadı: {model_error}")
                    continue
            
            if gemini_model is None:
                print("⚠️  Hiçbir Gemini modeli çalışmadı. Basit rapor kullanılacak.")
            
            print("1. Analist Raporu Test:")
            report = generate_analyst_report(
                company_name="Türk Hava Yolları",
                ticker="THYAO",
                technical_signal="AL",
                top_features=[("RSI", 0.15), ("Hacim", 0.12), ("MACD", 0.10)],
                hisse_sentiment_score=0.85,
                hisse_news_summary="THYAO, filo genişletme planlarını açıkladı.",
                piyasa_sentiment_score=0.30,
                piyasa_news_summary="TCMB'nin beklenenden yüksek faiz artırımı yapabileceği beklentisi.",
                gemini_model=gemini_model
            )
            print(report)
            
            print("\n2. Haber Özetleme Test:")
            news = [
                {'title': 'TCMB faiz kararı', 'summary': 'Merkez bankası faiz oranını artırdı', 'sentiment': 'negative'},
                {'title': 'BIST100 yükseldi', 'summary': 'Endeks günü yükselişle kapattı', 'sentiment': 'positive'}
            ]
            summary = summarize_news_headlines(news, gemini_model)
            print(summary)
        else:
            print("⚠️  GEMINI_API_KEY bulunamadı.")
    else:
        print("⚠️  Gemini API yüklü değil.")

