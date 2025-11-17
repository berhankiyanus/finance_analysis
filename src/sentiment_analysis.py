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
        
        # Model varsa kullan
        if self.model is not None:
            return self._analyze_with_model(text)
        else:
            # Basit kural tabanlı sentiment
            return self._analyze_with_rules(text)
    
    def _analyze_with_model(self, text: str) -> Dict:
        """
        Transformer modeli ile sentiment analizi.
        """
        try:
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
            
            return {
                'class': predicted_class,
                'confidence': confidence,
                'probs': {
                    'positive': float(probs[0]),
                    'negative': float(probs[1]),
                    'neutral': float(probs[2])
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
        
        # Pozitif kelimeler
        positive_words = [
            'artış', 'yükseliş', 'büyüme', 'kâr', 'başarı', 'güçlü', 'iyi',
            'olumlu', 'yükseldi', 'arttı', 'kazandı', 'başarılı',
            'increase', 'growth', 'profit', 'success', 'strong', 'good',
            'positive', 'rose', 'gained', 'successful'
        ]
        
        # Negatif kelimeler
        negative_words = [
            'düşüş', 'kayıp', 'zarar', 'zayıf', 'kötü', 'olumsuz', 'düştü',
            'azaldı', 'kaybetti', 'başarısız', 'risk', 'tehlike',
            'decrease', 'loss', 'weak', 'bad', 'negative', 'fell', 'declined',
            'lost', 'failed', 'risk', 'danger'
        ]
        
        # Kelime sayılarını hesapla
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Skor hesapla
        total_words = len(text.split())
        if total_words == 0:
            total_words = 1
        
        pos_score = pos_count / total_words
        neg_score = neg_count / total_words
        
        # Sınıf belirle
        if pos_score > neg_score and pos_score > 0.01:
            class_name = 'positive'
            confidence = min(0.9, pos_score * 10)
        elif neg_score > pos_score and neg_score > 0.01:
            class_name = 'negative'
            confidence = min(0.9, neg_score * 10)
        else:
            class_name = 'neutral'
            confidence = 0.5
        
        # Olasılıkları normalize et
        total = pos_score + neg_score + 0.1
        probs = {
            'positive': pos_score / total,
            'negative': neg_score / total,
            'neutral': 0.1 / total
        }
        
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
    if sentiment_result['class'] == 'positive':
        # Pozitif sınıf için: olasılık * 1
        return sentiment_result['probs']['positive']
    elif sentiment_result['class'] == 'negative':
        # Negatif sınıf için: olasılık * -1
        return -sentiment_result['probs']['negative']
    else:  # neutral
        return 0.0


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
        # Başlık ve özeti birleştir
        text = f"{row.get('title', '')} {row.get('summary', '')}"
        
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

