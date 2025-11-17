"""
NLP / Sentiment Analizi Modülü

Bu modül, haber metinlerine sentiment analizi uygular.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import warnings
warnings.filterwarnings('ignore')


class SentimentAnalyzer:
    """
    Haber metinleri için sentiment analizi yapan sınıf.
    """
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        """
        Sentiment analiz modelini yükler.
        
        Parametreler:
        ------------
        model_name : str
            Hugging Face model adı
        """
        print(f"📥 Sentiment modeli yükleniyor: {model_name}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()  # Evaluation modu
            
            # GPU varsa kullan
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
            print(f"✅ Model yüklendi. Cihaz: {self.device}")
            
        except Exception as e:
            print(f"⚠️  Model yüklenemedi: {e}")
            print("⚠️  Basit kural tabanlı sentiment kullanılacak.")
            self.model = None
            self.tokenizer = None
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Tek bir metin için sentiment analizi yapar.
        
        Parametreler:
        ------------
        text : str
            Analiz edilecek metin
        
        Döndürür:
        --------
        dict
            'class': 'positive', 'negative', veya 'neutral'
            'confidence': Olasılık değeri (0-1)
            'probs': Her sınıf için olasılık
        """
        
        if not text or len(text.strip()) < 5:
            return {
                'class': 'neutral',
                'confidence': 0.5,
                'probs': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
            }
        
        # Model varsa kullan (FinBERT - metni anlayarak analiz yapar)
        if self.model is not None:
            result = self._analyze_with_model(text)
            # Debug: Model kullanıldığını göster (sadece ilk birkaç çağrıda)
            if not hasattr(self, '_debug_count'):
                self._debug_count = 0
            if self._debug_count < 3:
                print(f"🔍 FinBERT modeli kullanıldı: '{text[:50]}...' -> {result['class']} (confidence: {result['confidence']:.2f})")
                self._debug_count += 1
            return result
        else:
            # Model yüklenemedi, kural tabanlı sentiment (fallback)
            print("⚠️  FinBERT modeli yüklenemedi, kural tabanlı analiz kullanılıyor.")
            return self._analyze_with_rules(text)
    
    def _analyze_with_model(self, text: str) -> Dict:
        """
        Transformer modeli ile sentiment analizi.
        """
        try:
            # Metni temizle ve uzunluğunu kontrol et
            text = text.strip()
            # Çok kısa metinler için bile model'i dene (FinBERT kısa metinleri de anlayabilir)
            # Sadece gerçekten boş veya çok kısa ise kural tabanlı analize geç
            if len(text) < 5:
                # Gerçekten çok kısa, kural tabanlı analiz
                return self._analyze_with_rules(text)
            
            # Metni tokenize et
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Model'e gönder
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Olasılıkları hesapla
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            probs = probs.cpu().numpy()[0]
            
            # Sınıf isimleri (FinBERT: 0=positive, 1=negative, 2=neutral)
            classes = ['positive', 'negative', 'neutral']
            predicted_class_idx = np.argmax(probs)
            predicted_class = classes[predicted_class_idx]
            confidence = float(probs[predicted_class_idx])
            
            # Eğer confidence çok düşükse (0.4'ten az) ve pozitif/negatif olasılıkları yakınsa,
            # kural tabanlı analizi de dene ve karşılaştır
            pos_prob = float(probs[0])
            neg_prob = float(probs[1])
            neu_prob = float(probs[2])
            
            # FinBERT modelinin çıktılarını daha iyi yorumla
            # Model zaten metni anlıyor, sadece threshold'u düşürmemiz gerekiyor
            
            # Eğer neutral olasılığı yüksekse ama pozitif/negatif arasında anlamlı fark varsa,
            # pozitif/negatif'i tercih et (model metni anlamış demektir)
            if predicted_class == 'neutral':
                # Pozitif ve negatif arasındaki farka bak
                diff = abs(pos_prob - neg_prob)
                
                # Eğer pozitif veya negatif olasılığı neutral'dan daha yüksekse ve fark anlamlıysa
                if pos_prob > neu_prob and pos_prob > neg_prob + 0.05:  # %5'ten fazla fark
                    predicted_class = 'positive'
                    confidence = pos_prob
                elif neg_prob > neu_prob and neg_prob > pos_prob + 0.05:  # %5'ten fazla fark
                    predicted_class = 'negative'
                    confidence = neg_prob
                elif diff > 0.10:  # %10'dan fazla fark varsa (daha agresif)
                    if pos_prob > neg_prob:
                        predicted_class = 'positive'
                        confidence = pos_prob
                    else:
                        predicted_class = 'negative'
                        confidence = neg_prob
            
            return {
                'class': predicted_class,
                'confidence': confidence,
                'probs': {
                    'positive': pos_prob,
                    'negative': neg_prob,
                    'neutral': neu_prob
                }
            }
            
        except Exception as e:
            print(f"⚠️  Model analizi hatası: {e}")
            return self._analyze_with_rules(text)
    
    def _analyze_with_rules(self, text: str) -> Dict:
        """
        Basit kural tabanlı sentiment analizi (fallback).
        """
        text_lower = text.lower()
        
        # Pozitif kelimeler (daha kapsamlı liste)
        positive_words = [
            'artış', 'yükseliş', 'büyüme', 'kâr', 'başarı', 'güçlü', 'iyi',
            'olumlu', 'yükseldi', 'arttı', 'kazandı', 'başarılı', 'yükselme',
            'ilerleme', 'gelişme', 'iyileşme', 'kazanç', 'getiri', 'fayda',
            'avantaj', 'üstün', 'mükemmel', 'harika', 'süper', 'rekor',
            'increase', 'growth', 'profit', 'success', 'strong', 'good',
            'positive', 'rose', 'gained', 'successful', 'up', 'gain',
            'improve', 'better', 'excellent', 'great', 'surge', 'rally',
            'boost', 'rise', 'climb', 'soar', 'jump', 'advance'
        ]
        
        # Negatif kelimeler (daha kapsamlı liste)
        negative_words = [
            'düşüş', 'kayıp', 'zarar', 'zayıf', 'kötü', 'olumsuz', 'düştü',
            'azaldı', 'kaybetti', 'başarısız', 'risk', 'tehlike', 'düşme',
            'gerileme', 'kriz', 'sorun', 'problem', 'hata', 'başarısızlık',
            'kayıp', 'zarar', 'zarar', 'kayıp', 'düşüş', 'düşme', 'azalma',
            'decrease', 'loss', 'weak', 'bad', 'negative', 'fell', 'declined',
            'lost', 'failed', 'risk', 'danger', 'down', 'drop', 'fall',
            'crash', 'plunge', 'sink', 'tumble', 'slump', 'downturn',
            'recession', 'crisis', 'problem', 'issue', 'concern', 'worry'
        ]
        
        # Kelime sayılarını hesapla
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Skor hesapla (kelime sayısına göre normalize et)
        total_words = len(text.split())
        if total_words == 0:
            total_words = 1
        
        # Daha agresif threshold - daha az kelime ile de pozitif/negatif tespit et
        pos_score = pos_count / max(total_words, 10)  # En az 10 kelimeye normalize et
        neg_score = neg_count / max(total_words, 10)
        
        # Sınıf belirle (daha düşük threshold)
        if pos_count > 0 and pos_count >= neg_count:
            class_name = 'positive'
            confidence = min(0.85, 0.5 + (pos_count * 0.1))
        elif neg_count > 0 and neg_count > pos_count:
            class_name = 'negative'
            confidence = min(0.85, 0.5 + (neg_count * 0.1))
        else:
            class_name = 'neutral'
            confidence = 0.5
        
        # Olasılıkları normalize et
        total = pos_count + neg_count + 1  # +1 neutral için
        if total == 0:
            total = 1
        
        probs = {
            'positive': pos_count / total,
            'negative': neg_count / total,
            'neutral': 1 / total if pos_count == 0 and neg_count == 0 else 0.3
        }
        
        # Normalize et
        prob_total = sum(probs.values())
        if prob_total > 0:
            probs = {k: v / prob_total for k, v in probs.items()}
        
        return {
            'class': class_name,
            'confidence': confidence,
            'probs': probs
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Birden fazla metin için batch sentiment analizi.
        
        Parametreler:
        ------------
        texts : List[str]
            Analiz edilecek metin listesi
        
        Döndürür:
        --------
        List[Dict]
            Her metin için sentiment sonucu
        """
        results = []
        for text in texts:
            result = self.analyze_sentiment(text)
            results.append(result)
        return results


def news_to_score(sentiment_result: Dict) -> float:
    """
    Sentiment sonucunu -1 ile +1 arası skora çevirir.
    
    Parametreler:
    ------------
    sentiment_result : dict
        analyze_sentiment() fonksiyonunun döndürdüğü sonuç
    
    Döndürür:
    --------
    float
        -1 (çok negatif) ile +1 (çok pozitif) arası skor
    """
    probs = sentiment_result.get('probs', {})
    pos_prob = probs.get('positive', 0.0)
    neg_prob = probs.get('negative', 0.0)
    neu_prob = probs.get('neutral', 0.0)
    
    # Confidence ile ağırlıklandır
    confidence = sentiment_result.get('confidence', 0.5)
    
    # Pozitif ve negatif olasılıklar arasındaki farkı kullan
    # Eğer neutral çok yüksekse ama pozitif/negatif arasında fark varsa, onu kullan
    if neu_prob > 0.7:
        # Neutral çok yüksek, ama pozitif/negatif farkına bak
        diff = pos_prob - neg_prob
        if abs(diff) > 0.1:  # %10'dan fazla fark varsa
            return diff * confidence
        else:
            return 0.0
    else:
        # Normal durum: pozitif ve negatif olasılıklar arasındaki fark
        score = pos_prob - neg_prob
        # Confidence ile ağırlıklandır
        return score * confidence


def aggregate_sentiment(news_df: pd.DataFrame) -> float:
    """
    Haberleri tarih bazlı ağırlıklandırarak toplam sentiment skoru hesaplar.
    
    Parametreler:
    ------------
    news_df : pd.DataFrame
        'sentiment_score' ve 'published_at' kolonları olmalı
    
    Döndürür:
    --------
    float
        0-100 arası normalize edilmiş sentiment skoru
    """
    
    if news_df.empty or 'sentiment_score' not in news_df.columns:
        return 50.0  # Nötr skor
    
    # Daha yeni haberler daha yüksek ağırlık alır
    if 'published_at' in news_df.columns:
        min_date = news_df['published_at'].min()
        max_date = news_df['published_at'].max()
        
        if (max_date - min_date).days > 0:
            # Her haber için ağırlık: (gün farkı + 1) / max_gün_farkı
            news_df['days_from_min'] = (news_df['published_at'] - min_date).dt.days + 1
            max_days = news_df['days_from_min'].max()
            news_df['weight'] = news_df['days_from_min'] / max_days
        else:
            news_df['weight'] = 1.0
    else:
        news_df['weight'] = 1.0
    
    # Ağırlıklı ortalama
    weighted_sum = (news_df['sentiment_score'] * news_df['weight']).sum()
    total_weight = news_df['weight'].sum()
    
    if total_weight == 0:
        weighted_avg = 0.0
    else:
        weighted_avg = weighted_sum / total_weight
    
    # -1 ile +1 arası skoru 0-100 arasına normalize et
    # -1 -> 0, 0 -> 50, +1 -> 100
    normalized_score = (weighted_avg + 1) * 50
    
    # 0-100 arasına sınırla
    normalized_score = max(0, min(100, normalized_score))
    
    return normalized_score


def analyze_news_sentiment(news_df: pd.DataFrame, analyzer: SentimentAnalyzer = None) -> pd.DataFrame:
    """
    Haber DataFrame'ine sentiment analizi uygular.
    
    Parametreler:
    ------------
    news_df : pd.DataFrame
        'title' ve 'summary' kolonları olmalı
    analyzer : SentimentAnalyzer, optional
        Eğer verilmezse yeni bir tane oluşturulur
    
    Döndürür:
    --------
    pd.DataFrame
        Orijinal DataFrame + 'sentiment_class', 'sentiment_confidence', 'sentiment_score' kolonları
    """
    
    if analyzer is None:
        analyzer = SentimentAnalyzer()
    
    # Her haber için sentiment analizi
    results = []
    
    for idx, row in news_df.iterrows():
        # Başlık, özet ve içeriği birleştir (daha iyi analiz için)
        title = str(row.get('title', '')).strip()
        summary = str(row.get('summary', '')).strip()
        content = str(row.get('content', '')).strip()
        
        # Metinleri birleştir (boş olanları atla)
        # FinBERT modeli için daha uzun ve anlamlı metinler daha iyi sonuç verir
        text_parts = []
        
        # 1. Başlık (her zaman ekle)
        if title:
            text_parts.append(title)
        
        # 2. Özet (başlıktan farklıysa ve yeterince uzunsa ekle)
        if summary and summary != title and len(summary) > 20:
            text_parts.append(summary)
        
        # 3. İçerik (ilk 800 karakter - daha fazla context için)
        if content and len(content) > 50:
            # İçeriğin ilk 800 karakterini al (model max 512 token alır ama daha fazla context iyidir)
            content_snippet = content[:800].strip()
            # Eğer içerik özetten farklıysa ekle
            if content_snippet != summary:
                text_parts.append(content_snippet)
        
        text = " ".join(text_parts).strip()
        
        # Eğer metin hala çok kısa ise, en azından başlık ve özeti birleştir
        if len(text) < 30:
            if title and summary and summary != title:
                text = f"{title}. {summary}"
            elif title:
                text = title
            else:
                text = summary if summary else ""
        
        # Sentiment analizi
        sentiment_result = analyzer.analyze_sentiment(text)
        
        # Skora çevir
        score = news_to_score(sentiment_result)
        
        results.append({
            'sentiment_class': sentiment_result['class'],
            'sentiment_confidence': sentiment_result['confidence'],
            'sentiment_score': score
        })
    
    # Sonuçları DataFrame'e ekle
    sentiment_df = pd.DataFrame(results)
    news_df_with_sentiment = pd.concat([news_df.reset_index(drop=True), sentiment_df], axis=1)
    
    return news_df_with_sentiment


if __name__ == "__main__":
    # Test
    print("=== Sentiment Analizi Modülü Test ===\n")
    
    # Analyzer oluştur
    analyzer = SentimentAnalyzer()
    
    # Test metinleri
    test_texts = [
        "Şirket güçlü kâr açıkladı ve hisseleri yükseldi.",
        "Şirket zarar etti ve fiyatlar düştü.",
        "Şirket normal seyrini sürdürüyor."
    ]
    
    print("1. Tekil metin analizi:")
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"\nMetin: {text}")
        print(f"Sonuç: {result}")
    
    # Haber DataFrame testi
    print("\n\n2. Haber DataFrame analizi:")
    test_news = pd.DataFrame({
        'title': ['Güçlü sonuçlar', 'Zarar açıklandı', 'Normal seyir'],
        'summary': ['Şirket beklentileri aştı', 'Şirket kayıp yaşadı', 'Piyasa stabil'],
        'published_at': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
    })
    
    news_with_sentiment = analyze_news_sentiment(test_news, analyzer)
    print(news_with_sentiment[['title', 'sentiment_class', 'sentiment_score']])
    
    # Toplam skor
    total_score = aggregate_sentiment(news_with_sentiment)
    print(f"\nToplam Sentiment Skoru: {total_score:.2f}/100")

