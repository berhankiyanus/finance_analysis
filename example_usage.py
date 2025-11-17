"""
Örnek Kullanım Dosyası

Bu dosya, sistemin nasıl kullanılacağını gösterir.
"""

from src.main import analyze_company

# Örnek 1: Apple analizi
print("="*60)
print("ÖRNEK 1: Apple Inc. Analizi")
print("="*60)

results_apple = analyze_company(
    company_name="Apple",
    ticker="AAPL",
    days_back=30,
    sentiment_weight=0.4,
    financial_weight=0.6
)

print(results_apple['summary'])

# Örnek 2: Microsoft analizi (farklı ağırlıklar)
print("\n" + "="*60)
print("ÖRNEK 2: Microsoft Analizi (Finansal Ağırlıklı)")
print("="*60)

results_msft = analyze_company(
    company_name="Microsoft",
    ticker="MSFT",
    days_back=30,
    sentiment_weight=0.3,  # Haberlere daha az ağırlık
    financial_weight=0.7   # Finansal verilere daha fazla ağırlık
)

print(results_msft['summary'])

# Örnek 3: Türk şirketi (THY)
print("\n" + "="*60)
print("ÖRNEK 3: Türk Hava Yolları Analizi")
print("="*60)

results_thy = analyze_company(
    company_name="Türk Hava Yolları",
    ticker="THYAO.IS",  # .IS eki Türk borsası için
    days_back=30
)

print(results_thy['summary'])

# Detaylı analiz sonuçlarına erişim
print("\n" + "="*60)
print("DETAYLI SONUÇLARA ERİŞİM ÖRNEĞİ")
print("="*60)

print(f"\nApple için:")
print(f"  • Genel Skor: {results_apple['overall_score']:.2f}/100")
print(f"  • Sentiment Skoru: {results_apple['sentiment_score']:.2f}/100")
print(f"  • Finansal Skor: {results_apple['financial_score']:.2f}/100")
print(f"  • Risk Seviyesi: {results_apple['interpretation']['risk_level']}")
print(f"  • Yön Tahmini: {results_apple['direction_prediction']['direction']}")

# Haber DataFrame'ine erişim
if not results_apple['news_df'].empty:
    print(f"\n  • İlk haber:")
    first_news = results_apple['news_df'].iloc[0]
    print(f"    Başlık: {first_news['title']}")
    print(f"    Sentiment: {first_news['sentiment_class']}")
    print(f"    Güven: {first_news['sentiment_confidence']:.2%}")

# Fiyat DataFrame'ine erişim
if not results_apple['price_df'].empty:
    print(f"\n  • Son fiyat: ${results_apple['price_df'].iloc[-1]['close']:.2f}")
    print(f"  • Son 30 günlük getiri: {results_apple['price_df'].iloc[-1].get('return_30d', 0)*100:.2f}%")
    print(f"  • RSI: {results_apple['price_df'].iloc[-1].get('rsi_14', 0):.2f}")

