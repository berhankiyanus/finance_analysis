"""
Skorlama ve Raporlama Modülü

Bu modül, sentiment ve finansal skorları birleştirerek genel durum skoru üretir
ve Türkçe rapor oluşturur.
"""

from typing import Dict, Optional, List
try:
    from .financial_analysis import compute_financial_score, create_feature_vector
    from .sentiment_analysis import aggregate_sentiment
    from .gemini_reporting import generate_analyst_report, summarize_news_headlines
except ImportError:
    from src.financial_analysis import compute_financial_score, create_feature_vector
    from src.sentiment_analysis import aggregate_sentiment
    from src.gemini_reporting import generate_analyst_report, summarize_news_headlines
import pandas as pd
import os


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


def generate_detailed_report(
    company_name: str,
    ticker: str,
    sentiment_score: float,
    financial_score: float,
    overall_score: float,
    news_df: pd.DataFrame,
    interpretation: Dict[str, str],
    direction_prediction: Dict[str, any],
    feature_vector: Dict,
    price_change_30d: Optional[float] = None
) -> Dict[str, any]:
    """
    Detaylı analiz raporu oluşturur - hangi haberler ve faktörler yüzünden
    al/sat önerisi verildiğini açıklar.
    
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
    news_df : pd.DataFrame
        Sentiment analizi yapılmış haberler DataFrame'i
    interpretation : dict
        interpret_score() fonksiyonunun döndürdüğü yorum
    direction_prediction : dict
        Yön tahmini sonuçları
    feature_vector : dict
        Finansal feature vektörü
    price_change_30d : float, optional
        Son 30 günlük fiyat değişimi
    
    Döndürür:
    --------
    dict
        Detaylı rapor içeriği
    """
    
    report = {
        'summary': '',
        'news_analysis': [],
        'financial_analysis': [],
        'recommendation_reasons': [],
        'key_factors': []
    }
    
    # 1. ÖZET
    direction_emoji = {"up": "📈", "down": "📉", "neutral": "➡️"}
    direction_text = {"up": "YÜKSELİŞ", "down": "DÜŞÜŞ", "neutral": "YATAY"}
    
    summary_parts = [
        f"## {company_name} ({ticker}) - Detaylı Analiz Raporu\n",
        f"### 🎯 Genel Durum: {overall_score:.1f}/100",
        f"**Kategori:** {interpretation['category']}",
        f"**Risk Seviyesi:** {interpretation['risk_level']}\n",
        f"### {direction_emoji.get(direction_prediction.get('direction', 'neutral'), '❓')} Yön Tahmini: {direction_text.get(direction_prediction.get('direction', 'neutral'), 'BİLİNMEYEN')}",
        f"**Güven:** {direction_prediction.get('confidence', 0):.1%}",
        f"**Neden:** {direction_prediction.get('reason', 'Belirtilmemiş')}\n"
    ]
    
    # 2. HABER ANALİZİ
    if not news_df.empty and 'sentiment_class' in news_df.columns:
        # Alakasız haberleri filtrele (relevance score kontrolü)
        news_df_filtered = news_df.copy()
        if 'relevance_score' in news_df_filtered.columns:
            # Sadece alakalı haberleri kullan (0.3'ten yüksek relevance)
            news_df_filtered = news_df_filtered[news_df_filtered['relevance_score'] >= 0.3].copy()
        
        # Pozitif haberler (sadece alakalı olanlar)
        positive_news = news_df_filtered[news_df_filtered['sentiment_class'] == 'positive'].copy()
        negative_news = news_df_filtered[news_df_filtered['sentiment_class'] == 'negative'].copy()
        neutral_news = news_df_filtered[news_df_filtered['sentiment_class'] == 'neutral'].copy()
        
        # Toplam haber sayısı (sadece alakalı olanlar)
        total_relevant_news = len(news_df_filtered)
        
        # En etkili haberler (yüksek confidence + yeni tarih)
        if not news_df.empty and 'published_at' in news_df.columns:
            # DataFrame'i kopyala (değişiklik yapmak için)
            news_df_work = news_df.copy()
            
            # Relevance score kontrolü - alakasız haberleri filtrele
            if 'relevance_score' in news_df_work.columns:
                # Sadece yüksek relevance score'a sahip haberleri göster (0.3'ten yüksek)
                news_df_work = news_df_work[news_df_work['relevance_score'] >= 0.3].copy()
            
            # Tarih farkını hesapla (gün cinsinden)
            max_date = news_df_work['published_at'].max() if not news_df_work.empty else None
            if pd.notna(max_date) and not news_df_work.empty:
                news_df_work['days_ago'] = (max_date - news_df_work['published_at']).dt.days
                max_days = news_df_work['days_ago'].max() if news_df_work['days_ago'].max() > 0 else 30
                # Yeni haberler daha yüksek ağırlık alır
                news_df_work['recency_score'] = 1 - (news_df_work['days_ago'] / max(max_days, 1))
                news_df_work['recency_score'] = news_df_work['recency_score'].clip(0, 1)
                
                # Relevance score'u normalize et (0-1 arası)
                if 'relevance_score' in news_df_work.columns:
                    relevance_norm = news_df_work['relevance_score'].clip(0, 1)
                else:
                    relevance_norm = pd.Series([1.0] * len(news_df_work), index=news_df_work.index)
                
                # Impact score: relevance (40%) + confidence (40%) + recency (20%)
                # Alakalı haberler daha yüksek impact alır
                news_df_work['impact_score'] = (
                    relevance_norm * 0.4 + 
                    news_df_work['sentiment_confidence'] * 0.4 + 
                    news_df_work['recency_score'] * 0.2
                )
            else:
                # Relevance score varsa onu kullan
                if 'relevance_score' in news_df_work.columns:
                    relevance_norm = news_df_work['relevance_score'].clip(0, 1)
                    news_df_work['impact_score'] = (
                        relevance_norm * 0.5 + 
                        news_df_work['sentiment_confidence'] * 0.5
                    )
                else:
                    news_df_work['impact_score'] = news_df_work['sentiment_confidence']
            
            # En etkili haberleri seç (en az 5 haber, ama daha fazla varsa 10'a kadar)
            top_count = min(10, len(news_df_work))
            if top_count > 0:
                top_news = news_df_work.nlargest(top_count, 'impact_score')
            else:
                top_news = pd.DataFrame()
            
            report['news_analysis'] = []
            for idx, row in top_news.iterrows():
                sentiment_emoji = "🟢" if row['sentiment_class'] == 'positive' else \
                                 "🔴" if row['sentiment_class'] == 'negative' else "🟡"
                
                news_date = row['published_at'].strftime('%Y-%m-%d') if pd.notna(row['published_at']) else 'Bilinmiyor'
                
                report['news_analysis'].append({
                    'title': row.get('title', 'Başlık yok'),
                    'sentiment': row['sentiment_class'],
                    'sentiment_emoji': sentiment_emoji,
                    'confidence': row.get('sentiment_confidence', 0),
                    'date': news_date,
                    'impact': 'Yüksek' if row['impact_score'] > 0.7 else 'Orta' if row['impact_score'] > 0.4 else 'Düşük'
                })
        
        # Haber istatistikleri (sadece alakalı haberler)
        summary_parts.append("### 📰 Haber Analizi Özeti")
        if total_relevant_news > 0:
            summary_parts.append(f"- **Toplam Alakalı Haber:** {total_relevant_news}")
            pos_pct = (len(positive_news)/total_relevant_news*100) if total_relevant_news > 0 else 0
            neg_pct = (len(negative_news)/total_relevant_news*100) if total_relevant_news > 0 else 0
            neu_pct = (len(neutral_news)/total_relevant_news*100) if total_relevant_news > 0 else 0
            summary_parts.append(f"- **Pozitif Haberler:** {len(positive_news)} ({pos_pct:.1f}%)")
            summary_parts.append(f"- **Negatif Haberler:** {len(negative_news)} ({neg_pct:.1f}%)")
            summary_parts.append(f"- **Nötr Haberler:** {len(neutral_news)} ({neu_pct:.1f}%)")
        else:
            total_news = len(news_df) if not news_df.empty else 0
            summary_parts.append(f"- **Toplam Haber:** {total_news}")
            pos_pct = (len(positive_news)/total_news*100) if total_news > 0 else 0
            neg_pct = (len(negative_news)/total_news*100) if total_news > 0 else 0
            neu_pct = (len(neutral_news)/total_news*100) if total_news > 0 else 0
            summary_parts.append(f"- **Pozitif Haberler:** {len(positive_news)} ({pos_pct:.1f}%)")
            summary_parts.append(f"- **Negatif Haberler:** {len(negative_news)} ({neg_pct:.1f}%)")
            summary_parts.append(f"- **Nötr Haberler:** {len(neutral_news)} ({neu_pct:.1f}%)")
        summary_parts.append(f"- **Sentiment Skoru:** {sentiment_score:.1f}/100\n")
        
        # Sentiment yorumu
        if sentiment_score >= 70:
            summary_parts.append("✅ **Haberler çok olumlu:** Şirket hakkında genel olarak pozitif haber akışı var.")
        elif sentiment_score >= 50:
            summary_parts.append("⚠️ **Haberler karışık:** Hem olumlu hem olumsuz haberler mevcut.")
        else:
            summary_parts.append("❌ **Haberler olumsuz:** Şirket hakkında genel olarak negatif haber akışı var.")
        summary_parts.append("")
    
    # 3. FİNANSAL ANALİZ
    summary_parts.append("### 💰 Finansal Analiz")
    summary_parts.append(f"- **Finansal Sağlık Skoru:** {financial_score:.1f}/100\n")
    
    financial_factors = []
    
    # RSI analizi
    rsi = feature_vector.get('rsi_14', 50)
    if rsi > 70:
        financial_factors.append({
            'factor': 'RSI (Göreceli Güç Endeksi)',
            'value': f"{rsi:.1f}",
            'status': '⚠️ Aşırı Alım',
            'impact': 'Negatif - Fiyat aşırı yükselmiş olabilir, düzeltme riski var'
        })
    elif rsi < 30:
        financial_factors.append({
            'factor': 'RSI (Göreceli Güç Endeksi)',
            'value': f"{rsi:.1f}",
            'status': '📈 Aşırı Satım',
            'impact': 'Pozitif - Fiyat aşırı düşmüş olabilir, toparlanma fırsatı var'
        })
    elif 30 <= rsi <= 70:
        financial_factors.append({
            'factor': 'RSI (Göreceli Güç Endeksi)',
            'value': f"{rsi:.1f}",
            'status': '✅ Normal',
            'impact': 'Nötr - Sağlıklı seviyede'
        })
    
    # Getiri analizi
    # return_30d zaten yüzde olarak geliyor (financial_analysis.py'de * 100 yapılıyor)
    return_30d = feature_vector.get('return_30d', 0)
    if return_30d > 5:
        financial_factors.append({
            'factor': '30 Günlük Getiri',
            'value': f"{return_30d:+.2f}%",
            'status': '📈 Güçlü Yükseliş',
            'impact': 'Pozitif - Son dönemde güçlü performans'
        })
    elif return_30d < -5:
        financial_factors.append({
            'factor': '30 Günlük Getiri',
            'value': f"{return_30d:+.2f}%",
            'status': '📉 Güçlü Düşüş',
            'impact': 'Negatif - Son dönemde zayıf performans'
        })
    
    # Volatilite analizi
    # volatility_30d zaten yüzde olarak geliyor (financial_analysis.py'de * 100 yapılıyor)
    volatility = feature_vector.get('volatility_30d', 0)
    if volatility > 3:
        financial_factors.append({
            'factor': 'Volatilite (30 Gün)',
            'value': f"{volatility:.2f}%",
            'status': '⚠️ Yüksek',
            'impact': 'Negatif - Yüksek risk, fiyat dalgalanmaları fazla'
        })
    elif volatility < 1:
        financial_factors.append({
            'factor': 'Volatilite (30 Gün)',
            'value': f"{volatility:.2f}%",
            'status': '✅ Düşük',
            'impact': 'Pozitif - Düşük risk, istikrarlı seyir'
        })
    
    # Fiyat vs MA analizi
    price_vs_ma20 = feature_vector.get('price_vs_ma20', 0)
    if price_vs_ma20 > 5:
        financial_factors.append({
            'factor': 'Fiyat vs 20 Günlük Ortalama',
            'value': f"{price_vs_ma20:+.2f}%",
            'status': '📈 Üstünde',
            'impact': 'Pozitif - Fiyat ortalamanın üstünde, yükseliş trendi'
        })
    elif price_vs_ma20 < -5:
        financial_factors.append({
            'factor': 'Fiyat vs 20 Günlük Ortalama',
            'value': f"{price_vs_ma20:+.2f}%",
            'status': '📉 Altında',
            'impact': 'Negatif - Fiyat ortalamanın altında, düşüş trendi'
        })
    
    report['financial_analysis'] = financial_factors
    
    for factor in financial_factors:
        summary_parts.append(f"- **{factor['factor']}:** {factor['value']} - {factor['status']}")
        summary_parts.append(f"  → {factor['impact']}")
    summary_parts.append("")
    
    # 4. ÖNERİ NEDENLERİ
    summary_parts.append("### 💡 Al/Sat Önerisi Nedenleri\n")
    
    recommendation_reasons = []
    
    # Sentiment bazlı nedenler
    if sentiment_score >= 70:
        recommendation_reasons.append({
            'type': 'Haber',
            'reason': f'Pozitif haber akışı güçlü ({sentiment_score:.1f}/100). Şirket hakkında olumlu haberler ağırlıkta.',
            'impact': 'Pozitif'
        })
    elif sentiment_score < 40:
        recommendation_reasons.append({
            'type': 'Haber',
            'reason': f'Negatif haber akışı yüksek ({sentiment_score:.1f}/100). Şirket hakkında olumsuz haberler ağırlıkta.',
            'impact': 'Negatif'
        })
    
    # Finansal bazlı nedenler
    if financial_score >= 70:
        recommendation_reasons.append({
            'type': 'Finansal',
            'reason': f'Finansal göstergeler güçlü ({financial_score:.1f}/100). Teknik analiz olumlu sinyaller veriyor.',
            'impact': 'Pozitif'
        })
    elif financial_score < 40:
        recommendation_reasons.append({
            'type': 'Finansal',
            'reason': f'Finansal göstergeler zayıf ({financial_score:.1f}/100). Teknik analiz olumsuz sinyaller veriyor.',
            'impact': 'Negatif'
        })
    
    # Yön tahmini bazlı nedenler
    direction = direction_prediction.get('direction', 'neutral')
    if direction == 'up':
        recommendation_reasons.append({
            'type': 'Tahmin',
            'reason': f"ML modeli veya teknik analiz yükseliş tahmini yapıyor ({direction_prediction.get('confidence', 0):.1%} güven).",
            'impact': 'Pozitif'
        })
    elif direction == 'down':
        recommendation_reasons.append({
            'type': 'Tahmin',
            'reason': f"ML modeli veya teknik analiz düşüş tahmini yapıyor ({direction_prediction.get('confidence', 0):.1%} güven).",
            'impact': 'Negatif'
        })
    
    report['recommendation_reasons'] = recommendation_reasons
    
    for reason in recommendation_reasons:
        emoji = "✅" if reason['impact'] == 'Pozitif' else "❌" if reason['impact'] == 'Negatif' else "⚠️"
        summary_parts.append(f"{emoji} **{reason['type']}:** {reason['reason']}")
    summary_parts.append("")
    
    # 5. ÖNEMLİ FAKTÖRLER
    summary_parts.append("### 🔑 En Önemli Faktörler\n")
    
    key_factors = []
    
    # En yüksek etkili haberler
    if report['news_analysis']:
        top_positive = [n for n in report['news_analysis'] if n['sentiment'] == 'positive'][:2]
        top_negative = [n for n in report['news_analysis'] if n['sentiment'] == 'negative'][:2]
        
        if top_positive:
            key_factors.append({
                'type': 'Pozitif Haber',
                'description': f"'{top_positive[0]['title'][:60]}...' gibi olumlu haberler sentiment skorunu yükseltiyor."
            })
        if top_negative:
            key_factors.append({
                'type': 'Negatif Haber',
                'description': f"'{top_negative[0]['title'][:60]}...' gibi olumsuz haberler sentiment skorunu düşürüyor."
            })
    
    # En önemli finansal faktörler
    if financial_factors:
        top_financial = sorted(financial_factors, key=lambda x: abs(float(x['value'].replace('%', '').replace('+', ''))), reverse=True)[:2]
        for factor in top_financial:
            key_factors.append({
                'type': 'Finansal Gösterge',
                'description': f"{factor['factor']} ({factor['value']}) - {factor['impact']}"
            })
    
    report['key_factors'] = key_factors
    
    for i, factor in enumerate(key_factors[:5], 1):
        summary_parts.append(f"{i}. **{factor['type']}:** {factor['description']}")
    summary_parts.append("")
    
    # 6. SONUÇ
    summary_parts.append("### 📋 Sonuç ve Öneri\n")
    summary_parts.append(interpretation['recommendation'])
    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("⚠️ **ÖNEMLİ UYARI:** Bu rapor sadece eğitim ve araştırma amaçlıdır. Yatırım tavsiyesi değildir. Yatırım kararlarınızı kendi araştırmanız ve uzman görüşü ile alın.")
    
    report['summary'] = '\n'.join(summary_parts)
    
    # Gemini API ile otomatik analist raporu (eğer API key varsa)
    use_gemini = os.getenv('GEMINI_API_KEY') is not None
    if use_gemini:
        try:
            # Gemini modeli yükle
            try:
                import google.generativeai as genai
                gemini_api_key = os.getenv('GEMINI_API_KEY')
                if gemini_api_key:
                    genai.configure(api_key=gemini_api_key)
                    # Gemini 1.5 Pro modelini kullan (gemini-pro artık kullanılamıyor)
                    gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                    
                    # Top feature'ları al (SHAP değerleri varsa)
                    top_features = []
                    if 'shap_values' in feature_vector:
                        shap_dict = feature_vector['shap_values']
                        top_features = sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
                    else:
                        # Feature importance'dan al
                        top_features = sorted(feature_vector.items(), key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)[:5]
                    
                    # Hisse bazlı haber özeti
                    hisse_news = []
                    piyasa_news = []
                    if not news_df.empty:
                        # Makro/mikro sınıflandırması varsa kullan
                        if 'news_context' in news_df.columns:
                            hisse_news = news_df[news_df['news_context'] == 'Hisse Bazlı'].to_dict('records')
                            piyasa_news = news_df[news_df['news_context'] == 'Piyasa Geneli'].to_dict('records')
                        else:
                            # Yoksa tüm haberleri hisse bazlı say
                            hisse_news = news_df.to_dict('records')
                    
                    # Haber özetleri
                    hisse_news_summary = summarize_news_headlines(
                        [{'title': n.get('title', ''), 'summary': n.get('summary', ''), 'sentiment': n.get('sentiment_class', 'neutral')} 
                         for n in hisse_news[:10]],
                        gemini_model=gemini_model
                    ) if hisse_news else "Hisse bazlı önemli haber bulunamadı."
                    
                    piyasa_news_summary = summarize_news_headlines(
                        [{'title': n.get('title', ''), 'summary': n.get('summary', ''), 'sentiment': n.get('sentiment_class', 'neutral')} 
                         for n in piyasa_news[:10]],
                        gemini_model=gemini_model
                    ) if piyasa_news else "Piyasa geneli önemli haber bulunamadı."
                    
                    # Hisse sentiment skoru (0-1 arası)
                    if hisse_news:
                        hisse_sentiment = sum(n.get('sentiment_score', 0) for n in hisse_news) / len(hisse_news)
                        hisse_sentiment = (hisse_sentiment + 1) / 2  # -1/+1'den 0-1'e normalize et
                    else:
                        hisse_sentiment = 0.5
                    
                    # Piyasa sentiment skoru
                    if piyasa_news:
                        piyasa_sentiment = sum(n.get('sentiment_score', 0) for n in piyasa_news) / len(piyasa_news)
                        piyasa_sentiment = (piyasa_sentiment + 1) / 2
                    else:
                        piyasa_sentiment = 0.5
                    
                    # Teknik sinyal
                    direction_map = {'up': 'AL', 'down': 'SAT', 'neutral': 'TUT'}
                    technical_signal = direction_map.get(direction_prediction.get('direction', 'neutral'), 'TUT')
                    
                    # Gemini raporu oluştur
                    gemini_report = generate_analyst_report(
                        company_name=company_name,
                        ticker=ticker,
                        technical_signal=technical_signal,
                        top_features=top_features,
                        hisse_sentiment_score=hisse_sentiment,
                        hisse_news_summary=hisse_news_summary,
                        piyasa_sentiment_score=piyasa_sentiment,
                        piyasa_news_summary=piyasa_news_summary,
                        gemini_model=gemini_model
                    )
                    
                    report['gemini_analyst_report'] = gemini_report
                    report['hisse_news_summary'] = hisse_news_summary
                    report['piyasa_news_summary'] = piyasa_news_summary
                    
            except ImportError:
                pass  # Gemini yüklü değil
            except Exception as e:
                print(f"⚠️  Gemini rapor oluşturma hatası: {e}")
        except Exception as e:
            print(f"⚠️  Gemini entegrasyonu hatası: {e}")
    
    return report


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

