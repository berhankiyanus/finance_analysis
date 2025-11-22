"""
Ana Uygulama

Bu modül, tüm bileşenleri birleştirerek tam analiz akışını çalıştırır.
"""

import sys
import os
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime

# Basitleştirilmiş import mekanizması
# ÖNEMLİ: PYTHONPATH ayarlanmalı veya paket olarak yüklenmeli
# Streamlit Cloud için: sys.path'e proje kök dizini eklenmeli

from pathlib import Path

# Proje kök dizinini bul ve sys.path'e ekle
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Tek tip import stratejisi: absolute import (src.module)
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

# Logging
from src.logger_config import setup_logger
logger = setup_logger(__name__)

# Yapılandırma doğrulama (opsiyonel: uygulama başlangıcında)
try:
    from src.config_validator import validate_config_on_startup
    
    # Uygulama başlangıcında yapılandırmayı doğrula (sadece uyarı, exception fırlatmaz)
    # Zorunlu anahtarlar için REQUIRE_* env var'larını kullanın
    _, _ = validate_config_on_startup(raise_on_missing=False)
except ImportError:
    # Config validator yoksa sessizce devam et
    pass
except Exception as e:
    # Hata durumunda sessizce devam et (Streamlit Cloud uyumluluğu için)
    logger.warning(f"Yapılandırma doğrulama hatası: {e}")


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
    
    logger.info(f"\n{'='*60}")
    logger.info(f"{company_name} ({ticker}) ANALİZİ BAŞLIYOR...")
    
    # 1. VERİ TOPLAMA
    logger.info("1. Veri toplanıyor...")
    
    # Haberler (cache ile)
    logger.info("Haberler çekiliyor...")
    try:
        from src.cache_manager import get_cached_news, set_cached_news
        cached_news = get_cached_news(company_name, ticker, days_back)
        if cached_news:
            logger.info("✅ Haberler cache'den alındı")
            # DataFrame'e çevir
            news_df = pd.DataFrame(cached_news)
        else:
            news_df = get_news(company_name, days_back=days_back, ticker=ticker)
            # Cache'e kaydet
            set_cached_news(company_name, ticker, news_df, days_back=days_back)
    except ImportError:
        # Cache modülü yoksa normal devam et
        news_df = get_news(company_name, days_back=days_back, ticker=ticker)
    except Exception as e:
        logger.warning(f"Cache hatası, normal devam ediliyor: {e}")
        news_df = get_news(company_name, days_back=days_back, ticker=ticker)
    
    # Dummy haber verisi kontrolü ve uyarı
    news_warning = None
    is_dummy_news = False
    if hasattr(news_df, 'attrs'):
        news_warning = news_df.attrs.get('warning')
        is_dummy_news = news_df.attrs.get('is_dummy_data', False)
        if is_dummy_news:
            logger.warning("⚠️ Dummy haber verisi kullanılıyor, skorlar güvenilir değil.")
    if news_warning:
        logger.warning(news_warning)
    
    # Fiyat verisi (cache ile)
    logger.info("Fiyat verisi çekiliyor...")
    try:
        from src.cache_manager import get_cached_price_data, set_cached_price_data
        cached_price = get_cached_price_data(ticker, period="1y")
        if cached_price:
            logger.info("✅ Fiyat verisi cache'den alındı")
            price_df = pd.DataFrame(cached_price)
            if 'date' in price_df.columns:
                price_df['date'] = pd.to_datetime(price_df['date'])
        else:
            price_df = get_price_data(ticker, period="1y")
            # Cache'e kaydet
            set_cached_price_data(ticker, price_df, period="1y")
    except ImportError:
        # Cache modülü yoksa normal devam et
        price_df = get_price_data(ticker, period="1y")
    except Exception as e:
        logger.warning(f"Cache hatası, normal devam ediliyor: {e}")
        price_df = get_price_data(ticker, period="1y")
    
    # Fiyat verisi doğrulaması
    if not isinstance(price_df, pd.DataFrame):
        msg = "Fiyat verisi beklenen DataFrame formatında değil, analiz sonlandırılıyor."
        logger.error(msg)
        raise ValueError(msg)
    
    # Gerekli kolonları kontrol et
    required_price_cols = {"date", "open", "high", "low", "close", "volume", "adjusted_close"}
    missing_cols = required_price_cols - set(price_df.columns)
    if missing_cols:
        msg = f"Fiyat verisi eksik kolonlar içeriyor ({', '.join(sorted(missing_cols))}); analiz sonlandırılıyor."
        logger.error(msg)
        raise ValueError(msg)
    
    # Boş DataFrame kontrolü
    if price_df.empty:
        msg = "Fiyat verisi boş döndü; skor hesaplaması yapılamıyor."
        logger.error(msg)
        raise ValueError(msg)
    
    # Dummy veri tespiti
    dummy_price_data_detected = False
    dummy_reasons = []
    
    # Satır sayısı kontrolü: Dummy veri genellikle 100 satır, gerçek veri 250+ satır (1 yıl için)
    if len(price_df) < 200:
        dummy_price_data_detected = True
        dummy_reasons.append(f"yetersiz satır sayısı ({len(price_df)} < 200)")
    
    # Tam olarak 100 satır ise şüpheli (dummy veri genellikle 100 satır)
    if len(price_df) == 100:
        dummy_price_data_detected = True
        dummy_reasons.append("tam olarak 100 satır (dummy veri pattern'i)")
    
    # Volatilite kontrolü: Dummy veri genellikle çok düzenli bir pattern'e sahiptir
    # Ancak bu kontrolü basit tutuyoruz, sadece satır sayısı yeterli
    
    if dummy_price_data_detected:
        logger.warning(
            "⚠️  Dummy veya yetersiz fiyat verisi tespit edildi (%s). Rapor düşük güvenle işaretlenecek.",
            ", ".join(dummy_reasons)
        )
    
    # Finansal göstergeler (opsiyonel)
    fundamentals = None
    if use_fundamentals:
        logger.info("Finansal göstergeler çekiliyor...")
        fundamentals = get_fundamentals(ticker)
    
    # Makroekonomik veriler (opsiyonel)
    macro_data = None
    try:
        logger.info("Makroekonomik veriler çekiliyor...")
        # Ülke tespiti (geliştirilmiş)
        from src.country_detector import detect_country_from_ticker, get_country_name
        country = detect_country_from_ticker(ticker)
        country_name = get_country_name(country)
        logger.info(f"Ticker '{ticker}' → Ülke: {country} ({country_name})")
        
        macro_data = get_macroeconomic_data(country=country)
        
        if macro_data:
            logger.info(f"✅ {country_name} için {len(macro_data) if isinstance(macro_data, dict) else 'N/A'} makro gösterge bulundu.")
        else:
            logger.warning(f"⚠️  {country_name} için makro veri bulunamadı.")
    except Exception as e:
        logger.error(f"Makroekonomik veri çekilirken hata (ülke: {country if 'country' in locals() else 'bilinmiyor'}): {e}", exc_info=True)
        macro_data = None
    
    logger.info("✅ Veri toplama tamamlandı.\n")
    
    # 2. SENTIMENT ANALİZİ
    logger.info("2. Sentiment analizi yapılıyor...")
    
    # Model cache kullan (singleton pattern)
    from src.model_cache import get_sentiment_analyzer
    analyzer = get_sentiment_analyzer(use_gemini=True)
    
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
                        event_count = len(historical_context.split('GEÇMİŞTE BENZER OLAYLAR')) - 1
                        logger.info(f"✅ Tarihsel hafızadan {event_count} benzer olay bulundu.")
    except ImportError:
        logger.warning("Political classifier veya vector memory modülü bulunamadı.")
    except Exception as e:
        logger.warning(f"Siyasi analiz/RAG hatası: {e}", exc_info=True)
    
    # Hisse bazlı ve piyasa geneli sentiment skorları (yeni özellik)
    try:
        hisse_duygu_skoru = analyze_stock_news(
            news_df_with_sentiment,
            analyzer=analyzer,
            company_name=company_name,
            ticker=ticker
        )
    except Exception as e:
        logger.warning(f"Hisse bazlı sentiment analizi hatası: {e}", exc_info=True)
        hisse_duygu_skoru = sentiment_score  # Fallback
    
    try:
        piyasa_duygu_skoru = analyze_market_news(
            news_df_with_sentiment,
            analyzer=analyzer
        )
    except Exception as e:
        logger.warning(f"Piyasa geneli sentiment analizi hatası: {e}", exc_info=True)
        piyasa_duygu_skoru = 50.0  # Fallback (nötr)
    
    logger.info(f"✅ Sentiment analizi tamamlandı.")
    logger.info(f"   • Genel Sentiment Skoru: {sentiment_score:.2f}/100")
    logger.info(f"   • Hisse Bazlı Duygu Skoru: {hisse_duygu_skoru:.2f}/100")
    logger.info(f"   • Piyasa Geneli Duygu Skoru: {piyasa_duygu_skoru:.2f}/100\n")
    
    # 3. FİNANSAL ANALİZ
    logger.info("📈 3. Finansal analiz yapılıyor...")
    
    # Skor güven seviyesi belirleme
    score_confidence = "normal"
    if dummy_price_data_detected:
        score_confidence = "low_due_to_dummy_price_data"
        logger.warning(
            "⚠️  Skor hesaplamaları dummy/yetersiz fiyat verisi nedeniyle düşük güvenle işaretleniyor."
        )
    
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
    
    logger.info(f"✅ Finansal analiz tamamlandı. Skor: {financial_score:.2f}/100")
    if score_confidence != "normal":
        logger.info(f"   ⚠️  Güven Seviyesi: {score_confidence}")
    logger.info("")
    
    # 4. SKORLAMA
    logger.info("🎯 4. Genel durum skoru hesaplanıyor...")
    
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
    
    logger.info(f"✅ Genel durum skoru: {overall_score:.2f}/100\n")
    
    # 5. YÖN TAHMİNİ (OPSİYONEL)
    logger.info("🔮 5. Yön tahmini yapılıyor...")
    
    # Eğitilmiş model varsa kullan
    model_path = f"models/price_predictor_{ticker.lower().replace('.', '_')}.pkl"
    if os.path.exists(model_path):
        direction_prediction = predict_direction(feature_vector, model_path=model_path)
        logger.info(f"✅ ML Model Tahmini: {direction_prediction['direction']} ({direction_prediction['confidence']:.2%} güven)\n")
    else:
        # Basit kural tabanlı tahmin
        direction_prediction = predict_direction(feature_vector)
        logger.info(f"✅ Kural Tabanlı Tahmin: {direction_prediction['direction']} ({direction_prediction['confidence']:.2%} güven)\n")
        logger.info(f"   💡 İpucu: Daha iyi tahmin için model eğitin: python3 train_model.py {ticker}")
    
    # 6. RAPOR OLUŞTURMA
    logger.info("📝 6. Rapor oluşturuluyor...\n")
    
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
        'summary': summary,
        'detailed_report': detailed_report,
        'political_impact_score': political_impact_score,
        'historical_context': historical_context,
        'score_confidence': score_confidence,
        'dummy_price_data_detected': dummy_price_data_detected,
        'price_data_quality': {
            'is_real': not dummy_price_data_detected,
            'row_count': len(price_df),
            'dummy_reasons': dummy_reasons if dummy_price_data_detected else []
        },
        'warnings': [news_warning] if news_warning else [],
        'is_dummy_news': is_dummy_news
    }
    
    # Telegram uyarıları gönder (eğer ayarlanmışsa)
    try:
        from src.notification_engine import get_notification_engine
        import os
        
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if telegram_chat_id:
            engine = get_notification_engine()
            # RSI'yi feature_vector'den al
            rsi = feature_vector.get('rsi', 50.0)
            current_price = price_df.iloc[-1]['close'] if not price_df.empty else 0.0
            price_change_30d = results.get('price_change_30d', 0.0)
            
            # Analiz sonuçlarına RSI ve fiyat bilgilerini ekle
            analysis_results_for_notification = {
                'sentiment_score': sentiment_score,
                'financial_score': financial_score,
                'overall_score': overall_score,
                'rsi': rsi,
                'current_price': current_price,
                'price_change_30d': price_change_30d,
                'direction_prediction': direction_prediction
            }
            
            # Uyarıları kontrol et ve gönder
            sent_count = engine.check_and_send_alerts(
                chat_id=telegram_chat_id,
                ticker=ticker,
                company_name=company_name,
                analysis_results=analysis_results_for_notification
            )
            
            if sent_count > 0:
                logger.info(f"✅ {sent_count} Telegram uyarısı gönderildi")
    except ImportError:
        # Notification engine yoksa sessizce devam et
        pass
    except Exception as e:
        logger.warning(f"Telegram uyarı hatası: {e}")
    
    return results


def main():
    """
    Ana fonksiyon - komut satırından çalıştırılır.
    """
    
    # Örnek kullanım
    if len(sys.argv) < 3:
        logger.info("""
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
        
        # Raporu yazdır (hem logger hem print - CLI için)
        summary = results['summary']
        logger.info(summary)
        print(summary)  # CLI için print kullan
        
        # Ek bilgiler
        details = "\n📊 DETAYLI BİLGİLER"
        details += f"\n   • Analiz edilen haber sayısı: {results['news_count']}"
        details += f"\n   • Fiyat verisi gün sayısı: {len(results['price_df'])}"
        
        if results['fundamentals']:
            details += f"\n   • Finansal gösterge sayısı: {len(results['fundamentals'])}"
        
        details += f"\n\n   • Yön tahmini: {results['direction_prediction']['direction']}"
        details += f"\n   • Tahmin nedeni: {results['direction_prediction']['reason']}"
        
        # Haber özeti
        if not results['news_df'].empty:
            details += "\n\n📰 HABER ÖZETİ (İlk 5 haber):"
            for idx, row in results['news_df'].head(5).iterrows():
                sentiment_emoji = "🟢" if row['sentiment_class'] == 'positive' else \
                                 "🔴" if row['sentiment_class'] == 'negative' else "🟡"
                details += f"\n   {sentiment_emoji} {row['title'][:60]}..."
                details += f"\n      Sentiment: {row['sentiment_class']} ({row['sentiment_confidence']:.2%})"
        
        logger.info(details)
        print(details)  # CLI için print kullan
        
    except Exception as e:
        error_msg = f"\n❌ Hata oluştu: {e}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)  # CLI için print kullan
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

