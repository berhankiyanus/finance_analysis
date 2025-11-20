"""
Ana Uygulama

Bu modül, tüm bileşenleri birleştirerek tam analiz akışını çalıştırır.
"""

import sys
import os
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime

# Import mekanizması - Streamlit Cloud için güvenli import
# ÖNEMLİ: Streamlit Cloud'da relative import (from .module) çalışmaz
# Bu yüzden önce absolute import (from src.module) deniyoruz

try:
    # Önce absolute import dene (Streamlit Cloud için)
    from src.data_collection import get_news, get_price_data, get_fundamentals
    from src.macro_data import get_macroeconomic_data
    from src.sentiment_analysis import (
        SentimentAnalyzer, 
        analyze_news_sentiment, 
        aggregate_sentiment,
        analyze_stock_news,
        analyze_market_news
    )
    from src.financial_analysis import compute_features, create_feature_vector, compute_financial_score
    from src.scoring import (
        compute_overall_score,
        interpret_score,
        generate_turkish_summary,
        generate_detailed_report,
        predict_direction
    )
except ImportError:
    # Absolute import başarısız oldu, relative import dene (paket içinden çalışıyorsa)
    try:
        from .data_collection import get_news, get_price_data, get_fundamentals
        from .macro_data import get_macroeconomic_data
        from .sentiment_analysis import (
            SentimentAnalyzer, 
            analyze_news_sentiment, 
            aggregate_sentiment,
            analyze_stock_news,
            analyze_market_news
        )
        from .financial_analysis import compute_features, create_feature_vector, compute_financial_score
        from .scoring import (
            compute_overall_score,
            interpret_score,
            generate_turkish_summary,
            generate_detailed_report,
            predict_direction
        )
    except (ImportError, ValueError, SystemError) as e:
        # Son çare: importlib ile doğrudan dosya import'u
        import importlib.util
        from pathlib import Path
        
        # Proje kök dizinini bul
        current_file = Path(__file__).resolve()
        src_dir = current_file.parent
        project_root = src_dir.parent
        
        # sys.path'e ekle
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Modülleri import et
        try:
            data_collection_spec = importlib.util.spec_from_file_location(
                "src.data_collection", 
                src_dir / "data_collection.py"
            )
            data_collection_module = importlib.util.module_from_spec(data_collection_spec)
            data_collection_spec.loader.exec_module(data_collection_module)
            get_news = data_collection_module.get_news
            get_price_data = data_collection_module.get_price_data
            get_fundamentals = data_collection_module.get_fundamentals
            
            macro_data_spec = importlib.util.spec_from_file_location(
                "src.macro_data",
                src_dir / "macro_data.py"
            )
            macro_data_module = importlib.util.module_from_spec(macro_data_spec)
            macro_data_spec.loader.exec_module(macro_data_module)
            get_macroeconomic_data = macro_data_module.get_macroeconomic_data
            
            sentiment_analysis_spec = importlib.util.spec_from_file_location(
                "src.sentiment_analysis",
                src_dir / "sentiment_analysis.py"
            )
            sentiment_analysis_module = importlib.util.module_from_spec(sentiment_analysis_spec)
            sentiment_analysis_spec.loader.exec_module(sentiment_analysis_module)
            SentimentAnalyzer = sentiment_analysis_module.SentimentAnalyzer
            analyze_news_sentiment = sentiment_analysis_module.analyze_news_sentiment
            aggregate_sentiment = sentiment_analysis_module.aggregate_sentiment
            analyze_stock_news = sentiment_analysis_module.analyze_stock_news
            analyze_market_news = sentiment_analysis_module.analyze_market_news
            
            financial_analysis_spec = importlib.util.spec_from_file_location(
                "src.financial_analysis",
                src_dir / "financial_analysis.py"
            )
            financial_analysis_module = importlib.util.module_from_spec(financial_analysis_spec)
            financial_analysis_spec.loader.exec_module(financial_analysis_module)
            compute_features = financial_analysis_module.compute_features
            create_feature_vector = financial_analysis_module.create_feature_vector
            compute_financial_score = financial_analysis_module.compute_financial_score
            
            scoring_spec = importlib.util.spec_from_file_location(
                "src.scoring",
                src_dir / "scoring.py"
            )
            scoring_module = importlib.util.module_from_spec(scoring_spec)
            scoring_spec.loader.exec_module(scoring_module)
            compute_overall_score = scoring_module.compute_overall_score
            interpret_score = scoring_module.interpret_score
            generate_turkish_summary = scoring_module.generate_turkish_summary
            generate_detailed_report = scoring_module.generate_detailed_report
            predict_direction = scoring_module.predict_direction
        except Exception as import_error:
            raise ImportError(f"Modüller import edilemedi: {import_error}. Orijinal hata: {e}")


def analyze_company(
    company_name: str,
    ticker: str,
    days_back: int = 30,
    sentiment_weight: float = 0.4,
    financial_weight: float = 0.6,
    use_fundamentals: bool = True
) -> dict:
    """
    Bir şirket için tam analiz yapar.
    
    Parametreler:
    ------------
    company_name : str
        Şirket adı (örn: "Apple")
    ticker : str
        Borsa kodu (örn: "AAPL")
    days_back : int
        Kaç gün geriye gidilecek (varsayılan: 30)
    sentiment_weight : float
        Haber ağırlığı (varsayılan: 0.4)
    financial_weight : float
        Finansal ağırlık (varsayılan: 0.6)
    use_fundamentals : bool
        Temel finansal göstergeleri kullan (varsayılan: True)
    
    Döndürür:
    --------
    dict
        Tüm analiz sonuçları
    """
    
    print(f"\n{'='*60}")
    print(f"🔍 {company_name} ({ticker}) ANALİZİ BAŞLIYOR...")
    print(f"{'='*60}\n")
    
    # 1. VERİ TOPLAMA
    print("📥 1. Veri toplanıyor...")
    
    # Haberler
    print("   📰 Haberler çekiliyor...")
    news_df = get_news(company_name, days_back=days_back, ticker=ticker)
    
    # Fiyat verisi
    print("   💰 Fiyat verisi çekiliyor...")
    price_df = get_price_data(ticker, period="1y")
    
    # Finansal göstergeler (opsiyonel)
    fundamentals = None
    if use_fundamentals:
        print("   📊 Finansal göstergeler çekiliyor...")
        fundamentals = get_fundamentals(ticker)
    
    # Makroekonomik veriler (opsiyonel)
    macro_data = None
    try:
        print("   🌍 Makroekonomik veriler çekiliyor...")
        # Ticker'dan ülke kodu çıkar (basit yaklaşım)
        country = "TR" if ".IS" in ticker or ticker.endswith(".IS") else "US"
        macro_data = get_macroeconomic_data(country=country)
    except Exception as e:
        print(f"   ⚠️  Makroekonomik veri çekilemedi: {e}")
        macro_data = None
    
    print("✅ Veri toplama tamamlandı.\n")
    
    # 2. SENTIMENT ANALİZİ
    print("🤖 2. Sentiment analizi yapılıyor...")
    
    analyzer = SentimentAnalyzer()
    news_df_with_sentiment = analyze_news_sentiment(
        news_df, 
        analyzer, 
        company_name=company_name,
        ticker=ticker,
        use_context_classification=True
    )
    
    # Toplam sentiment skoru
    sentiment_score = aggregate_sentiment(news_df_with_sentiment)
    
    # Siyasi analiz ve RAG (Tarihsel Hafıza) entegrasyonu
    political_impact_score = None
    historical_context = ""
    
    try:
        from src.political_classifier import classify_news_political_impact
        from src.vector_memory import HistoricalMemory
        
        # En son haberleri siyasi analiz için kullan
        if not news_df_with_sentiment.empty:
            latest_news = news_df_with_sentiment.iloc[0]
            political_analysis = classify_news_political_impact(
                news_text=latest_news.get('summary', ''),
                news_title=latest_news.get('title', '')
            )
            
            political_impact_score = political_analysis.get('political_impact_score', 0.0)
            
            # Eğer siyasi etki yüksekse, tarihsel hafızadan benzer olayları bul
            if political_impact_score > 0.5:
                memory = HistoricalMemory()
                if memory.available:
                    historical_context = memory.get_historical_context(
                        current_news=latest_news.get('summary', ''),
                        current_title=latest_news.get('title', ''),
                        top_k=3
                    )
                    if historical_context:
                        print(f"✅ Tarihsel hafızadan {len(historical_context.split('GEÇMİŞTE BENZER OLAYLAR')) - 1} benzer olay bulundu.")
    except ImportError:
        print("⚠️  Political classifier veya vector memory modülü bulunamadı.")
    except Exception as e:
        print(f"⚠️  Siyasi analiz/RAG hatası: {e}")
    
    # Hisse bazlı ve piyasa geneli sentiment skorları (yeni özellik)
    try:
        hisse_duygu_skoru = analyze_stock_news(
            news_df_with_sentiment,
            analyzer=analyzer,
            company_name=company_name,
            ticker=ticker
        )
    except Exception as e:
        print(f"⚠️  Hisse bazlı sentiment analizi hatası: {e}")
        hisse_duygu_skoru = sentiment_score  # Fallback
    
    try:
        piyasa_duygu_skoru = analyze_market_news(
            news_df_with_sentiment,
            analyzer=analyzer
        )
    except Exception as e:
        print(f"⚠️  Piyasa geneli sentiment analizi hatası: {e}")
        piyasa_duygu_skoru = 50.0  # Fallback (nötr)
    
    print(f"✅ Sentiment analizi tamamlandı.")
    print(f"   • Genel Sentiment Skoru: {sentiment_score:.2f}/100")
    print(f"   • Hisse Bazlı Duygu Skoru: {hisse_duygu_skoru:.2f}/100")
    print(f"   • Piyasa Geneli Duygu Skoru: {piyasa_duygu_skoru:.2f}/100\n")
    
    # 3. FİNANSAL ANALİZ
    print("📈 3. Finansal analiz yapılıyor...")
    
    # Hisse ve piyasa duygu skorlarını Series'e çevir (feature'lar için)
    # Her gün için aynı skoru kullan (basit yaklaşım)
    # İleride zaman serisi olarak geliştirilebilir
    hisse_duygu_series = pd.Series([hisse_duygu_skoru / 100.0] * len(price_df), index=price_df.index)
    piyasa_duygu_series = pd.Series([piyasa_duygu_skoru / 100.0] * len(price_df), index=price_df.index)
    
    # Feature'ları hesapla (hisse ve piyasa duygu skorları ile)
    price_df_with_features = compute_features(
        price_df,
        hisse_duygu_skoru=hisse_duygu_series,
        piyasa_duygu_skoru=piyasa_duygu_series
    )
    
    # Feature vektörü oluştur (fundamentals ve macro_data ile)
    feature_vector = create_feature_vector(price_df_with_features, fundamentals, macro_data)
    
    # Finansal skor
    financial_score = compute_financial_score(feature_vector)
    
    print(f"✅ Finansal analiz tamamlandı. Skor: {financial_score:.2f}/100\n")
    
    # 4. SKORLAMA
    print("🎯 4. Genel durum skoru hesaplanıyor...")
    
    overall_score = compute_overall_score(
        sentiment_score,
        financial_score,
        sentiment_weight=sentiment_weight,
        financial_weight=financial_weight,
        political_impact_score=political_impact_score
    )
    
    interpretation = interpret_score(overall_score)
    
    # Son 30 günlük fiyat değişimi
    if len(price_df) >= 30:
        price_change_30d = (price_df.iloc[-1]['close'] / price_df.iloc[-30]['close'] - 1) * 100
    else:
        price_change_30d = None
    
    print(f"✅ Genel durum skoru: {overall_score:.2f}/100\n")
    
    # 5. YÖN TAHMİNİ (OPSİYONEL)
    print("🔮 5. Yön tahmini yapılıyor...")
    
    # Eğitilmiş model varsa kullan
    model_path = f"models/price_predictor_{ticker.lower().replace('.', '_')}.pkl"
    if os.path.exists(model_path):
        direction_prediction = predict_direction(feature_vector, model_path=model_path)
        print(f"✅ ML Model Tahmini: {direction_prediction['direction']} ({direction_prediction['confidence']:.2%} güven)\n")
    else:
        # Basit kural tabanlı tahmin
        direction_prediction = predict_direction(feature_vector)
        print(f"✅ Kural Tabanlı Tahmin: {direction_prediction['direction']} ({direction_prediction['confidence']:.2%} güven)\n")
        print(f"   💡 İpucu: Daha iyi tahmin için model eğitin: python3 train_model.py {ticker}")
    
    # 6. RAPOR OLUŞTURMA
    print("📝 6. Rapor oluşturuluyor...\n")
    
    summary = generate_turkish_summary(
        company_name=company_name,
        ticker=ticker,
        sentiment_score=sentiment_score,
        financial_score=financial_score,
        overall_score=overall_score,
        news_count=len(news_df),
        interpretation=interpretation,
        price_change_30d=price_change_30d
    )
    
    # Detaylı rapor oluştur (historical_context ile)
    detailed_report = generate_detailed_report(
        company_name=company_name,
        ticker=ticker,
        sentiment_score=sentiment_score,
        financial_score=financial_score,
        overall_score=overall_score,
        news_df=news_df_with_sentiment,
        interpretation=interpretation,
        direction_prediction=direction_prediction,
        feature_vector=feature_vector,
        price_change_30d=price_change_30d,
        historical_context=historical_context
    )
    
    # Sonuçları birleştir
    results = {
        'company_name': company_name,
        'ticker': ticker,
        'sentiment_score': sentiment_score,
        'financial_score': financial_score,
        'overall_score': overall_score,
        'interpretation': interpretation,
        'fundamentals': fundamentals,
        'macro_data': macro_data,
        'direction_prediction': direction_prediction,
        'news_count': len(news_df),
        'news_df': news_df_with_sentiment,
        'price_df': price_df_with_features,
        'feature_vector': feature_vector,
        'fundamentals': fundamentals,
        'summary': summary,
        'detailed_report': detailed_report,
        'political_impact_score': political_impact_score,
        'historical_context': historical_context
    }
    
    return results


def main():
    """
    Ana fonksiyon - komut satırından çalıştırılır.
    """
    
    # Örnek kullanım
    if len(sys.argv) < 3:
        print("""
Kullanım:
    python -m src.main <şirket_adı> <ticker> [days_back] [sentiment_weight] [financial_weight]

Örnek:
    python -m src.main "Apple" "AAPL" 30 0.4 0.6
    python -m src.main "Microsoft" "MSFT" 30
    python -m src.main "THY" "THYAO.IS" 30 0.3 0.7

Parametreler:
    şirket_adı      : Şirket adı (tırnak içinde)
    ticker          : Borsa kodu (örn: AAPL, MSFT, THYAO.IS)
    days_back       : Kaç gün geriye gidilecek (varsayılan: 30)
    sentiment_weight: Haber ağırlığı (varsayılan: 0.4)
    financial_weight: Finansal ağırlık (varsayılan: 0.6)
        """)
        return
    
    company_name = sys.argv[1]
    ticker = sys.argv[2]
    days_back = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    sentiment_weight = float(sys.argv[4]) if len(sys.argv) > 4 else 0.4
    financial_weight = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6
    
    try:
        # Analiz yap
        results = analyze_company(
            company_name=company_name,
            ticker=ticker,
            days_back=days_back,
            sentiment_weight=sentiment_weight,
            financial_weight=financial_weight
        )
        
        # Raporu yazdır
        print(results['summary'])
        
        # Ek bilgiler
        print("\n📊 DETAYLI BİLGİLER")
        print(f"   • Analiz edilen haber sayısı: {results['news_count']}")
        print(f"   • Fiyat verisi gün sayısı: {len(results['price_df'])}")
        
        if results['fundamentals']:
            print(f"   • Finansal gösterge sayısı: {len(results['fundamentals'])}")
        
        print(f"\n   • Yön tahmini: {results['direction_prediction']['direction']}")
        print(f"   • Tahmin nedeni: {results['direction_prediction']['reason']}")
        
        # Haber özeti
        if not results['news_df'].empty:
            print("\n📰 HABER ÖZETİ (İlk 5 haber):")
            for idx, row in results['news_df'].head(5).iterrows():
                sentiment_emoji = "🟢" if row['sentiment_class'] == 'positive' else \
                                 "🔴" if row['sentiment_class'] == 'negative' else "🟡"
                print(f"   {sentiment_emoji} {row['title'][:60]}...")
                print(f"      Sentiment: {row['sentiment_class']} ({row['sentiment_confidence']:.2%})")
        
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

