"""
Sistem Test Dosyası

Bu dosya, sistemin tüm bileşenlerini test eder.
"""

import sys
import os

print("="*60)
print("FİNANSAL ANALİZ SİSTEMİ - TEST")
print("="*60)
print()

# Test 1: Modül import testi
print("📦 TEST 1: Modül Import Testi")
print("-" * 60)
try:
    from src.data_collection import get_news, get_price_data, get_fundamentals
    print("✅ data_collection modülü başarıyla yüklendi")
except Exception as e:
    print(f"❌ data_collection modülü yüklenemedi: {e}")
    sys.exit(1)

try:
    from src.sentiment_analysis import SentimentAnalyzer
    print("✅ sentiment_analysis modülü başarıyla yüklendi")
except Exception as e:
    print(f"❌ sentiment_analysis modülü yüklenemedi: {e}")
    sys.exit(1)

try:
    from src.financial_analysis import compute_features, create_feature_vector
    print("✅ financial_analysis modülü başarıyla yüklendi")
except Exception as e:
    print(f"❌ financial_analysis modülü yüklenemedi: {e}")
    sys.exit(1)

try:
    from src.scoring import compute_overall_score, interpret_score
    print("✅ scoring modülü başarıyla yüklendi")
except Exception as e:
    print(f"❌ scoring modülü yüklenemedi: {e}")
    sys.exit(1)

try:
    from src.main import analyze_company
    print("✅ main modülü başarıyla yüklendi")
except Exception as e:
    print(f"❌ main modülü yüklenemedi: {e}")
    sys.exit(1)

print()

# Test 2: Veri toplama testi
print("📥 TEST 2: Veri Toplama Testi")
print("-" * 60)
try:
    print("   Haber verisi test ediliyor...")
    news_df = get_news("Apple", days_back=7)
    print(f"   ✅ {len(news_df)} haber bulundu")
    if not news_df.empty:
        print(f"   Örnek haber: {news_df.iloc[0]['title'][:50]}...")
except Exception as e:
    print(f"   ❌ Haber toplama hatası: {e}")

try:
    print("   Fiyat verisi test ediliyor...")
    price_df = get_price_data("AAPL", period="1mo")
    print(f"   ✅ {len(price_df)} günlük fiyat verisi bulundu")
    if not price_df.empty:
        print(f"   Son fiyat: ${price_df.iloc[-1]['close']:.2f}")
except Exception as e:
    print(f"   ❌ Fiyat verisi hatası: {e}")

print()

# Test 3: Sentiment analizi testi
print("🤖 TEST 3: Sentiment Analizi Testi")
print("-" * 60)
try:
    print("   Sentiment analyzer yükleniyor...")
    analyzer = SentimentAnalyzer()
    print("   ✅ Sentiment analyzer hazır")
    
    test_text = "Şirket güçlü kâr açıkladı ve hisseleri yükseldi."
    result = analyzer.analyze_sentiment(test_text)
    print(f"   Test metin: '{test_text}'")
    print(f"   Sonuç: {result['class']} (güven: {result['confidence']:.2%})")
except Exception as e:
    print(f"   ❌ Sentiment analizi hatası: {e}")

print()

# Test 4: Finansal analiz testi
print("📈 TEST 4: Finansal Analiz Testi")
print("-" * 60)
try:
    print("   Feature hesaplama test ediliyor...")
    price_df = get_price_data("AAPL", period="3mo")
    price_df_with_features = compute_features(price_df)
    print(f"   ✅ {len(price_df_with_features.columns)} kolon oluşturuldu")
    
    feature_vector = create_feature_vector(price_df_with_features)
    print(f"   ✅ Feature vektörü oluşturuldu ({len(feature_vector)} feature)")
    print(f"   Örnek feature'lar: return_30d={feature_vector.get('return_30d', 0):.2f}%, "
          f"rsi_14={feature_vector.get('rsi_14', 0):.2f}")
except Exception as e:
    print(f"   ❌ Finansal analiz hatası: {e}")

print()

# Test 5: Skorlama testi
print("🎯 TEST 5: Skorlama Testi")
print("-" * 60)
try:
    sentiment_score = 65.0
    financial_score = 72.0
    overall_score = compute_overall_score(sentiment_score, financial_score)
    interpretation = interpret_score(overall_score)
    
    print(f"   Sentiment Skoru: {sentiment_score}/100")
    print(f"   Finansal Skor: {financial_score}/100")
    print(f"   Genel Durum Skoru: {overall_score:.2f}/100")
    print(f"   Kategori: {interpretation['category']}")
    print(f"   Risk Seviyesi: {interpretation['risk_level']}")
    print("   ✅ Skorlama sistemi çalışıyor")
except Exception as e:
    print(f"   ❌ Skorlama hatası: {e}")

print()

# Test 6: Tam analiz testi (küçük)
print("🚀 TEST 6: Tam Analiz Testi (Mini)")
print("-" * 60)
try:
    print("   Apple için mini analiz yapılıyor (7 gün)...")
    results = analyze_company(
        company_name="Apple",
        ticker="AAPL",
        days_back=7,  # Hızlı test için sadece 7 gün
        sentiment_weight=0.4,
        financial_weight=0.6
    )
    
    print("   ✅ Analiz tamamlandı!")
    print(f"   • Genel Skor: {results['overall_score']:.2f}/100")
    print(f"   • Haber Sayısı: {results['news_count']}")
    print(f"   • Fiyat Verisi: {len(results['price_df'])} gün")
    print()
    print("   Rapor özeti:")
    print(results['summary'][:500] + "...")
    
except Exception as e:
    print(f"   ❌ Tam analiz hatası: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("✅ TÜM TESTLER TAMAMLANDI!")
print("="*60)
print()
print("💡 İpucu: Şimdi şu komutları deneyebilirsiniz:")
print("   python3 -m src.main \"Apple\" \"AAPL\" 30")
print("   python3 example_usage.py")

