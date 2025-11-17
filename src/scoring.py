"""
Skorlama ve Raporlama Modülü

Bu modül, sentiment ve finansal skorları birleştirerek genel durum skoru üretir
ve Türkçe rapor oluşturur.
"""

from typing import Dict, Optional
try:
    from .financial_analysis import compute_financial_score, create_feature_vector
    from .sentiment_analysis import aggregate_sentiment
except ImportError:
    from src.financial_analysis import compute_financial_score, create_feature_vector
    from src.sentiment_analysis import aggregate_sentiment
import pandas as pd


def compute_overall_score(
    sentiment_score: float,
    financial_score: float,
    sentiment_weight: float = 0.4,
    financial_weight: float = 0.6
) -> float:
    """
    Haber sentiment ve finansal skorları birleştirerek genel durum skoru hesaplar.
    
    Parametreler:
    ------------
    sentiment_score : float
        0-100 arası haber sentiment skoru
    financial_score : float
        0-100 arası finansal sağlık skoru
    sentiment_weight : float
        Haber ağırlığı (varsayılan: 0.4)
    financial_weight : float
        Finansal ağırlık (varsayılan: 0.6)
    
    Döndürür:
    --------
    float
        0-100 arası genel durum skoru
    """
    
    # Ağırlıkların toplamı 1 olmalı
    total_weight = sentiment_weight + financial_weight
    if total_weight == 0:
        return 50.0  # Nötr skor
    
    sentiment_weight = sentiment_weight / total_weight
    financial_weight = financial_weight / total_weight
    
    # Ağırlıklı ortalama
    overall_score = (sentiment_score * sentiment_weight + 
                     financial_score * financial_weight)
    
    # 0-100 arasına sınırla
    overall_score = max(0, min(100, overall_score))
    
    return overall_score


def interpret_score(overall_score: float) -> Dict[str, str]:
    """
    Skoru yorumlar ve kategori belirler.
    
    Parametreler:
    ------------
    overall_score : float
        0-100 arası genel durum skoru
    
    Döndürür:
    --------
    dict
        'category', 'risk_level', 'recommendation' anahtarları
    """
    
    if overall_score >= 70:
        category = "Güçlü / Olumlu Görünüm"
        risk_level = "Düşük Risk"
        recommendation = "Şirket güçlü finansal göstergelere ve olumlu haber akışına sahip. " \
                        "Yatırımcılar için potansiyel bir fırsat olabilir, ancak her zaman " \
                        "kendi araştırmanızı yapın."
    elif overall_score >= 50:
        category = "Nötr / Karışık Görünüm"
        risk_level = "Orta Risk"
        recommendation = "Şirket karışık sinyaller veriyor. Hem olumlu hem olumsuz faktörler " \
                        "mevcut. Dikkatli takip edilmeli ve daha fazla analiz yapılmalı."
    elif overall_score >= 30:
        category = "Zayıf / Olumsuz Görünüm"
        risk_level = "Yüksek Risk"
        recommendation = "Şirket zayıf finansal göstergelere veya olumsuz haber akışına sahip. " \
                        "Yatırım yapmadan önce dikkatli değerlendirme yapılmalı."
    else:
        category = "Çok Zayıf / Kritik Durum"
        risk_level = "Çok Yüksek Risk"
        recommendation = "Şirket ciddi sorunlar yaşıyor olabilir. Finansal göstergeler ve " \
                        "haber akışı olumsuz. Yatırım yapmadan önce çok dikkatli olunmalı ve " \
                        "uzman görüşü alınmalı."
    
    return {
        'category': category,
        'risk_level': risk_level,
        'recommendation': recommendation
    }


def generate_turkish_summary(
    company_name: str,
    ticker: str,
    sentiment_score: float,
    financial_score: float,
    overall_score: float,
    news_count: int,
    interpretation: Dict[str, str],
    price_change_30d: Optional[float] = None
) -> str:
    """
    Türkçe özet rapor oluşturur.
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı
    ticker : str
        Borsa kodu
    sentiment_score : float
        Sentiment skoru
    financial_score : float
        Finansal skor
    overall_score : float
        Genel durum skoru
    news_count : int
        Analiz edilen haber sayısı
    interpretation : dict
        interpret_score() fonksiyonunun döndürdüğü yorum
    price_change_30d : float, optional
        Son 30 günlük fiyat değişimi (yüzde)
    
    Döndürür:
    --------
    str
        Formatlanmış Türkçe rapor
    """
    
    # Skor emoji'si
    if overall_score >= 70:
        score_emoji = "🟢"
    elif overall_score >= 50:
        score_emoji = "🟡"
    elif overall_score >= 30:
        score_emoji = "🟠"
    else:
        score_emoji = "🔴"
    
    # Fiyat değişimi bilgisi
    price_info = ""
    if price_change_30d is not None:
        price_change_str = f"{price_change_30d:+.2f}%"
        price_emoji = "📈" if price_change_30d > 0 else "📉" if price_change_30d < 0 else "➡️"
        price_info = f"\n   {price_emoji} Son 30 Günlük Değişim: {price_change_str}"
    
    summary = f"""
╔══════════════════════════════════════════════════════════════╗
║  {company_name.upper()} ({ticker}) - FİNANSAL ANALİZ RAPORU    ║
╚══════════════════════════════════════════════════════════════╝

{score_emoji} GENEL DURUM SKORU: {overall_score:.1f}/100
   Kategori: {interpretation['category']}
   Risk Seviyesi: {interpretation['risk_level']}

📰 HABER ANALİZİ
   Sentiment Skoru: {sentiment_score:.1f}/100
   Analiz Edilen Haber Sayısı: {news_count}
   
💰 FİNANSAL ANALİZ
   Finansal Sağlık Skoru: {financial_score:.1f}/100{price_info}

💡 ÖNERİ
   {interpretation['recommendation']}

───────────────────────────────────────────────────────────────

⚠️  ÖNEMLİ UYARI: Bu rapor sadece eğitim ve araştırma amaçlıdır.
    Yatırım tavsiyesi değildir. Yatırım kararlarınızı kendi
    araştırmanız ve uzman görüşü ile alın.

───────────────────────────────────────────────────────────────
"""
    
    return summary


def predict_direction(
    feature_vector: Dict,
    model: Optional[object] = None,
    model_path: Optional[str] = None
) -> Dict[str, any]:
    """
    Önümüzdeki kısa dönem için fiyat yönü tahmini yapar (opsiyonel).
    
    Parametreler:
    ------------
    feature_vector : dict
        Feature vektörü
    model : object, optional
        Eğitilmiş ML modeli. Eğer yoksa basit kural tabanlı tahmin yapar.
    
    Döndürür:
    --------
    dict
        'direction': 'up', 'down', veya 'neutral'
        'confidence': Güven skoru (0-1)
        'reason': Tahmin nedeni
    """
    
    # Eğer model varsa kullan
    if model is not None:
        try:
            prediction = model.predict(feature_vector)
            return prediction
        except Exception as e:
            print(f"⚠️  Model tahmini hatası: {e}")
    
    # Eğer model yolu verilmişse yükle ve kullan
    if model_path is not None:
        try:
            from src.prediction_model import PriceDirectionPredictor
            predictor = PriceDirectionPredictor(model_path=model_path)
            prediction = predictor.predict(feature_vector)
            return prediction
        except Exception as e:
            print(f"⚠️  Model yükleme/tahmin hatası: {e}")
    
    # Basit kural tabanlı tahmin
    return_30d = feature_vector.get('return_30d', 0)
    rsi = feature_vector.get('rsi_14', 50)
    price_vs_ma20 = feature_vector.get('price_vs_ma20', 0)
    
    # Momentum göstergeleri
    bullish_signals = 0
    bearish_signals = 0
    
    if return_30d > 2:  # %2'den fazla getiri
        bullish_signals += 1
    elif return_30d < -2:
        bearish_signals += 1
    
    if rsi > 50 and rsi < 70:  # Sağlıklı yükseliş
        bullish_signals += 1
    elif rsi < 50 and rsi > 30:
        bearish_signals += 1
    
    if price_vs_ma20 > 2:  # Fiyat MA'nın %2 üstünde
        bullish_signals += 1
    elif price_vs_ma20 < -2:
        bearish_signals += 1
    
    # Tahmin
    if bullish_signals > bearish_signals:
        direction = 'up'
        confidence = min(0.8, 0.5 + bullish_signals * 0.1)
        reason = "Teknik göstergeler yükseliş sinyali veriyor."
    elif bearish_signals > bullish_signals:
        direction = 'down'
        confidence = min(0.8, 0.5 + bearish_signals * 0.1)
        reason = "Teknik göstergeler düşüş sinyali veriyor."
    else:
        direction = 'neutral'
        confidence = 0.5
        reason = "Göstergeler karışık, yatay seyir bekleniyor."
    
    return {
        'direction': direction,
        'confidence': confidence,
        'reason': reason
    }


if __name__ == "__main__":
    # Test
    print("=== Skorlama Modülü Test ===\n")
    
    # Test skorları
    sentiment_score = 65.0
    financial_score = 72.0
    
    # Genel skor
    overall_score = compute_overall_score(sentiment_score, financial_score)
    print(f"Genel Durum Skoru: {overall_score:.2f}/100")
    
    # Yorum
    interpretation = interpret_score(overall_score)
    print(f"\nKategori: {interpretation['category']}")
    print(f"Risk Seviyesi: {interpretation['risk_level']}")
    print(f"Öneri: {interpretation['recommendation']}")
    
    # Türkçe özet
    summary = generate_turkish_summary(
        company_name="Apple Inc.",
        ticker="AAPL",
        sentiment_score=sentiment_score,
        financial_score=financial_score,
        overall_score=overall_score,
        news_count=15,
        interpretation=interpretation,
        price_change_30d=5.2
    )
    print("\n" + summary)

