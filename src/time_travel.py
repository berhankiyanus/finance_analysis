"""
Time Travel Analysis Modülü

Geçmiş bir tarihe tıklandığında o günkü analizi gösterir.
"Eğer o gün sistem çalışsaydı ne derdi?" sorusunu yanıtlar.
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from src.logger_config import setup_logger

logger = setup_logger(__name__)


def analyze_historical_date(
    ticker: str,
    target_date: str,
    company_name: Optional[str] = None
) -> Dict:
    """
    Geçmiş bir tarih için analiz yapar.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    target_date : str
        Hedef tarih (YYYY-MM-DD)
    company_name : str
        Şirket adı (opsiyonel)
    
    Döndürür:
    --------
    dict
        O günkü analiz sonuçları
    """
    target_dt = pd.to_datetime(target_date)
    today = datetime.now()
    
    if target_dt > today:
        raise ValueError("Gelecek tarih için analiz yapılamaz")
    
    logger.info(f"🕐 Time Travel Analysis: {ticker} - {target_date}")
    
    # O günkü fiyat verisini çek (target_date'e kadar olan veriler)
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        
        # Tarih aralığını hesapla (target_date'ten 1 yıl öncesine kadar)
        start_date = (target_dt - timedelta(days=365)).strftime("%Y-%m-%d")
        end_date = target_date
        
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            raise ValueError(f"{target_date} için fiyat verisi bulunamadı")
        
        # O günkü fiyatı al
        if target_dt.date() in hist.index.date:
            target_idx = hist.index[hist.index.date == target_dt.date()][0]
        else:
            # Tam tarih bulunamazsa, en yakın tarihi bul
            closest_idx = hist.index.get_indexer([target_dt], method='nearest')[0]
            target_idx = hist.index[closest_idx]
        
        target_price = hist.loc[target_idx, 'Close']
        target_volume = hist.loc[target_idx, 'Volume']
        
        # O günkü teknik göstergeleri hesapla
        from src.financial_analysis import compute_features
        
        # target_date'e kadar olan verilerle feature'ları hesapla
        price_df = hist[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        price_df.reset_index(inplace=True)
        price_df.rename(columns={'Date': 'date'}, inplace=True)
        
        # Sadece target_date'e kadar olan verileri kullan
        price_df = price_df[price_df['date'] <= target_dt]
        
        if len(price_df) < 30:
            raise ValueError(f"Yetersiz veri: {len(price_df)} gün (minimum 30 gün gerekli)")
        
        # Feature'ları hesapla (sentiment skorları olmadan)
        price_df_with_features = compute_features(price_df)
        
        # O günkü feature vektörünü al (son satır)
        feature_vector = price_df_with_features.iloc[-1].to_dict()
        
        # O günkü haberleri çek (target_date civarındaki haberler)
        from src.data_collection import get_news
        
        days_back = min((today - target_dt).days, 7)  # Maksimum 7 gün geriye git
        if days_back < 0:
            days_back = 7
        
        news_df = get_news(
            company_name or ticker,
            days_back=days_back,
            ticker=ticker
        )
        
        # Sadece target_date civarındaki haberleri filtrele
        if not news_df.empty:
            news_df['published_at'] = pd.to_datetime(news_df['published_at'])
            # target_date ± 3 gün içindeki haberler
            date_range_start = target_dt - timedelta(days=3)
            date_range_end = target_dt + timedelta(days=1)
            
            day_news = news_df[
                (news_df['published_at'] >= date_range_start) &
                (news_df['published_at'] <= date_range_end)
            ]
        else:
            day_news = pd.DataFrame()
        
        # O günkü sentiment analizi
        sentiment_score = 50.0  # Varsayılan nötr
        if not day_news.empty:
            from src.sentiment_analysis import analyze_news_sentiment, aggregate_sentiment
            from src.model_cache import get_sentiment_analyzer
            
            analyzer = get_sentiment_analyzer(use_gemini=True)
            news_with_sentiment = analyze_news_sentiment(
                day_news,
                analyzer,
                company_name=company_name or ticker,
                ticker=ticker
            )
            sentiment_score = aggregate_sentiment(news_with_sentiment)
        
        # O günkü finansal skor
        from src.financial_analysis import create_feature_vector, compute_financial_score
        
        feature_vector_full = create_feature_vector(price_df_with_features, None, None)
        financial_score = compute_financial_score(feature_vector_full)
        
        # O günkü genel skor
        from src.scoring import compute_overall_score
        
        overall_score = compute_overall_score(
            sentiment_score,
            financial_score,
            sentiment_weight=0.4,
            financial_weight=0.6
        )
        
        # O günkü yön tahmini (eğer model varsa)
        from src.scoring import predict_direction
        
        model_path = f"models/price_predictor_{ticker.lower().replace('.', '_')}.pkl"
        if Path(model_path).exists():
            direction_prediction = predict_direction(feature_vector_full, model_path=model_path)
        else:
            direction_prediction = predict_direction(feature_vector_full)
        
        # Sonraki günlerin fiyat değişimini hesapla (gerçek veri ile karşılaştırma)
        future_dates = [target_dt + timedelta(days=i) for i in [1, 7, 30]]
        future_changes = {}
        
        for future_date in future_dates:
            if future_date <= today:
                try:
                    future_hist = stock.history(start=future_date.strftime("%Y-%m-%d"), end=(future_date + timedelta(days=1)).strftime("%Y-%m-%d"))
                    if not future_hist.empty:
                        future_price = future_hist.iloc[0]['Close']
                        change = ((future_price - target_price) / target_price) * 100
                        days_diff = (future_date - target_dt).days
                        future_changes[f"{days_diff}_day"] = {
                            'date': future_date.strftime("%Y-%m-%d"),
                            'price': float(future_price),
                            'change_percent': float(change)
                        }
                except:
                    pass
        
        # Sonuçları birleştir
        results = {
            'ticker': ticker,
            'company_name': company_name or ticker,
            'target_date': target_date,
            'analysis_date': datetime.now().isoformat(),
            'price_data': {
                'date': target_idx.strftime("%Y-%m-%d"),
                'close': float(target_price),
                'volume': int(target_volume)
            },
            'sentiment_score': float(sentiment_score),
            'financial_score': float(financial_score),
            'overall_score': float(overall_score),
            'direction_prediction': direction_prediction,
            'news_count': len(day_news),
            'news_df': day_news.to_dict('records') if not day_news.empty else [],
            'feature_vector': feature_vector,
            'future_changes': future_changes,  # Gerçek fiyat değişimleri (doğrulama için)
            'message': f"🕐 {target_date} tarihindeki analiz: Sistem o gün çalışsaydı ne derdi?"
        }
        
        logger.info(f"✅ Time Travel Analysis tamamlandı: {target_date}")
        return results
        
    except Exception as e:
        logger.error(f"Time Travel Analysis hatası: {e}")
        raise


def compare_predictions_with_reality(
    ticker: str,
    target_date: str,
    prediction: Dict
) -> Dict:
    """
    Tahminleri gerçek fiyat değişimleri ile karşılaştırır.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    target_date : str
        Hedef tarih
    prediction : dict
        O günkü tahmin sonuçları
    
    Döndürür:
    --------
    dict
        Karşılaştırma sonuçları
    """
    target_dt = pd.to_datetime(target_date)
    
    # Gerçek fiyat değişimlerini al
    future_changes = prediction.get('future_changes', {})
    
    # Tahmin yönü
    predicted_direction = prediction.get('direction_prediction', {}).get('direction', 'HOLD')
    predicted_confidence = prediction.get('direction_prediction', {}).get('confidence', 0.5)
    
    # Gerçek yönü belirle (30 gün sonrasına göre)
    if '30_day' in future_changes:
        actual_change = future_changes['30_day']['change_percent']
        if actual_change > 5:
            actual_direction = 'BUY'
        elif actual_change < -5:
            actual_direction = 'SELL'
        else:
            actual_direction = 'HOLD'
        
        # Tahmin doğruluğu
        correct = (predicted_direction == actual_direction)
        
        return {
            'predicted_direction': predicted_direction,
            'predicted_confidence': predicted_confidence,
            'actual_direction': actual_direction,
            'actual_change_30d': actual_change,
            'correct': correct,
            'accuracy': '✅ Doğru' if correct else '❌ Yanlış'
        }
    
    return {
        'predicted_direction': predicted_direction,
        'predicted_confidence': predicted_confidence,
        'actual_direction': None,
        'message': '30 gün sonrası verisi henüz mevcut değil'
    }


if __name__ == "__main__":
    # Test
    print("=== Time Travel Analysis Test ===\n")
    
    # Örnek: 2023-10-26 tarihindeki THYAO analizi
    try:
        results = analyze_historical_date(
            ticker="THYAO.IS",
            target_date="2023-10-26",
            company_name="Türk Hava Yolları"
        )
        
        print(f"✅ Analiz tamamlandı!")
        print(f"   📅 Tarih: {results['target_date']}")
        print(f"   💰 Fiyat: {results['price_data']['close']:.2f} TL")
        print(f"   📊 Genel Skor: {results['overall_score']:.1f}/100")
        print(f"   🎯 Tahmin: {results['direction_prediction'].get('direction', 'N/A')}")
        print(f"   📰 Haber Sayısı: {results['news_count']}")
        
        # Gerçek fiyat değişimleri ile karşılaştır
        comparison = compare_predictions_with_reality(
            ticker="THYAO.IS",
            target_date="2023-10-26",
            prediction=results
        )
        
        if 'actual_direction' in comparison:
            print(f"\n🔍 Tahmin Doğruluğu:")
            print(f"   Tahmin: {comparison['predicted_direction']} ({comparison['predicted_confidence']:.1%})")
            print(f"   Gerçek: {comparison['actual_direction']} ({comparison['actual_change_30d']:+.2f}%)")
            print(f"   Sonuç: {comparison['accuracy']}")
        
    except Exception as e:
        print(f"❌ Hata: {e}")

