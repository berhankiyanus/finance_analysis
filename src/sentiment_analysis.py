"""
NLP / Sentiment Analizi Modülü

Bu modül, haber metinlerine sentiment analizi uygular.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import warnings
import os
import json
warnings.filterwarnings('ignore')

# Gemini API için
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai paketi yüklü değil. Gemini API kullanılamayacak.")


class SentimentAnalyzer:
    """
    Haber metinleri için sentiment analizi yapan sınıf.
    """
    
    def __init__(self, model_name: str = "ProsusAI/finbert", use_gemini: bool = True):
        """
        Sentiment analiz modelini yükler.
        
        Parametreler:
        ------------
        model_name : str
            Hugging Face model adı
        use_gemini : bool
            Gemini API kullanılsın mı? (varsayılan: True)
        """
        print(f"📥 Sentiment modeli yükleniyor: {model_name}...")
        
        # FinBERT modelini yükle
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()  # Evaluation modu
            
            # GPU varsa kullan
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            
            print(f"✅ FinBERT modeli yüklendi. Cihaz: {self.device}")
            
        except Exception as e:
            print(f"⚠️  FinBERT modeli yüklenemedi: {e}")
            print("⚠️  Basit kural tabanlı sentiment kullanılacak.")
            self.model = None
            self.tokenizer = None
        
        # Gemini API'yi yükle
        self.use_gemini = use_gemini and GEMINI_AVAILABLE
        self.gemini_model = None
        
        if self.use_gemini:
            try:
                # Gemini API key'ini al
                gemini_api_key = os.getenv('GEMINI_API_KEY')
                if gemini_api_key:
                    genai.configure(api_key=gemini_api_key)
                    # Gemini 1.5 Flash modelini kullan (daha hızlı ve ücretsiz katmanda erişilebilir)
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                    print("✅ Gemini API yüklendi ve yapılandırıldı.")
                else:
                    print("⚠️  GEMINI_API_KEY bulunamadı. Gemini API kullanılamayacak.")
                    print("   💡 Gemini API key'i almak için: https://makersuite.google.com/app/apikey")
                    self.use_gemini = False
            except Exception as e:
                print(f"⚠️  Gemini API yüklenemedi: {e}")
                self.use_gemini = False
    
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
        
        # 1. Önce Gemini API'ye sor (daha iyi context anlama için)
        if self.use_gemini and self.gemini_model is not None:
            gemini_result = self._analyze_with_gemini(text)
            if gemini_result:
                # Gemini başarılı, sonucu kullan
                return gemini_result
            # Gemini başarısız olursa FinBERT'e geç
        
        # 2. Gemini yoksa veya başarısız olduysa FinBERT kullan
        if self.model is not None:
            finbert_result = self._analyze_with_model(text)
            return finbert_result
        else:
            # FinBERT de yoksa kural tabanlı sentiment (fallback)
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
            # Model zaten metni anlıyor, threshold'u çok düşük tutuyoruz
            
            # Her zaman pozitif/negatif olasılıklarını kontrol et
            # Neutral sadece gerçekten nötr olduğunda seçilmeli
            diff = abs(pos_prob - neg_prob)
            
            # Eğer pozitif veya negatif olasılığı neutral'dan daha yüksekse, onu tercih et
            if pos_prob > neu_prob and pos_prob > neg_prob:
                predicted_class = 'positive'
                confidence = pos_prob
            elif neg_prob > neu_prob and neg_prob > pos_prob:
                predicted_class = 'negative'
                confidence = neg_prob
            # Eğer neutral en yüksekse ama pozitif/negatif arasında anlamlı fark varsa
            elif predicted_class == 'neutral' and diff > 0.05:  # %5'ten fazla fark (daha agresif)
                if pos_prob > neg_prob:
                    predicted_class = 'positive'
                    confidence = pos_prob
                else:
                    predicted_class = 'negative'
                    confidence = neg_prob
            # Eğer pozitif/negatif olasılıkları eşitse ama neutral'dan yüksekse
            elif pos_prob > 0.20 or neg_prob > 0.20:  # En az %20 olasılık varsa (daha agresif)
                if pos_prob > neg_prob:
                    predicted_class = 'positive'
                    confidence = pos_prob
                else:
                    predicted_class = 'negative'
                    confidence = neg_prob
            # Son çare: Eğer pozitif/negatif arasında %3'ten fazla fark varsa, onu kullan
            elif diff > 0.03 and (pos_prob > 0.15 or neg_prob > 0.15):
                if pos_prob > neg_prob:
                    predicted_class = 'positive'
                    confidence = pos_prob * 0.8  # Biraz daha düşük güven
                else:
                    predicted_class = 'negative'
                    confidence = neg_prob * 0.8
            
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
    
    def _analyze_with_gemini(self, text: str) -> Optional[Dict]:
        """
        Gemini API ile sentiment analizi yapar.
        
        Parametreler:
        ------------
        text : str
            Analiz edilecek metin
        
        Döndürür:
        --------
        dict veya None
            Sentiment sonucu veya hata durumunda None
        """
        if not self.gemini_model:
            return None
        
        try:
            # Gemini'ye gönderilecek prompt (daha detaylı ve finansal odaklı, daha agresif)
            prompt = f"""Sen bir finansal analiz uzmanısın. Aşağıdaki finansal haber metnini dikkatlice oku ve sentiment (duygu) analizi yap.

HABER METNİ:
{text}

GÖREVİN:
Bu haberin şirket için finansal açıdan pozitif, negatif veya nötr olduğunu belirle. Haberi bağlamıyla birlikte değerlendir:
- Pozitif: Kâr artışı, büyüme, başarı, olumlu gelişmeler, fiyat yükselişi, güçlü performans, yatırım, genişleme, işbirliği, ödül, başarılı sonuçlar
- Negatif: Zarar, düşüş, başarısızlık, olumsuz gelişmeler, fiyat düşüşü, zayıf performans, kayıp, sorun, dava, kriz, eleştiri
- Nötr: SADECE gerçekten tarafsız, bilgilendirici haberler (örnek: rutin duyurular, teknik bilgiler, genel piyasa haberleri)

KRİTİK KURALLAR:
1. NÖTR sınıfını MÜMKÜN OLDUĞUNCA AZ KULLAN. Sadece gerçekten hiçbir finansal etkisi olmayan, tamamen tarafsız haberler için nötr kullan.
2. Eğer haber şirket hakkında herhangi bir pozitif veya negatif bilgi içeriyorsa (kâr, büyüme, zarar, düşüş vb.), MUTLAKA pozitif veya negatif olarak sınıflandır.
3. Finansal sonuçlar, yatırımlar, iş geliştirmeleri, başarılar, sorunlar, kayıplar gibi konular MUTLAKA pozitif veya negatif olmalı, nötr olmamalı.
4. Sadece gerçekten hiçbir finansal anlamı olmayan, tamamen bilgilendirici haberler için nötr kullan.

ÖNEMLİ: Haberi gerçekten oku ve anla. Sadece kelime eşleştirmesi yapma. Haberin gerçek anlamını ve finansal etkisini değerlendir. NÖTR sınıfını çok dikkatli kullan.

Yanıtını SADECE şu formatta JSON olarak ver (başka hiçbir açıklama ekleme):
{{
    "class": "positive" veya "negative" veya "neutral",
    "confidence": 0.0 ile 1.0 arası bir sayı (ne kadar emin olduğun),
    "probs": {{
        "positive": 0.0 ile 1.0 arası (pozitif olma olasılığı),
        "negative": 0.0 ile 1.0 arası (negatif olma olasılığı),
        "neutral": 0.0 ile 1.0 arası (nötr olma olasılığı)
    }},
    "reason": "Kısa açıklama - neden bu sentiment? (Türkçe, 1-2 cümle)"
}}

SADECE JSON yanıt ver, başka hiçbir şey yazma."""

            # Gemini'ye gönder
            response = self.gemini_model.generate_content(prompt)
            
            # Yanıtı parse et
            response_text = response.text.strip()
            
            # JSON'u extract et (eğer markdown code block içindeyse)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # JSON parse et
            try:
                result = json.loads(response_text)
                
                # Sonucu normalize et
                class_name = result.get('class', 'neutral').lower()
                if class_name not in ['positive', 'negative', 'neutral']:
                    class_name = 'neutral'
                
                confidence = float(result.get('confidence', 0.5))
                confidence = max(0.0, min(1.0, confidence))
                
                probs = result.get('probs', {})
                pos_prob = float(probs.get('positive', 0.33))
                neg_prob = float(probs.get('negative', 0.33))
                neu_prob = float(probs.get('neutral', 0.34))
                
                # Normalize et (toplam 1.0 olmalı)
                total = pos_prob + neg_prob + neu_prob
                if total > 0:
                    pos_prob /= total
                    neg_prob /= total
                    neu_prob /= total
                else:
                    pos_prob = neg_prob = neu_prob = 0.33
                
                # Debug: İlk birkaç çağrıda göster
                if not hasattr(self, '_gemini_debug_count'):
                    self._gemini_debug_count = 0
                if self._gemini_debug_count < 3:
                    reason = result.get('reason', 'Belirtilmemiş')
                    print(f"🤖 Gemini API kullanıldı: '{text[:50]}...' -> {class_name} (confidence: {confidence:.2f})")
                    print(f"   💭 Neden: {reason}")
                    self._gemini_debug_count += 1
                
                return {
                    'class': class_name,
                    'confidence': confidence,
                    'probs': {
                        'positive': pos_prob,
                        'negative': neg_prob,
                        'neutral': neu_prob
                    }
                }
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Gemini API yanıtı parse edilemedi: {e}")
                print(f"   Yanıt: {response_text[:200]}")
                return None
                
        except Exception as e:
            print(f"⚠️  Gemini API hatası: {e}")
            return None
    
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
    # Daha agresif: Neutral yüksek olsa bile, pozitif/negatif farkını kullan
    diff = pos_prob - neg_prob
    
    # Eğer pozitif veya negatif olasılığı neutral'dan yüksekse, onu kullan
    if pos_prob > neu_prob or neg_prob > neu_prob:
        # Pozitif/negatif tercih edilmeli
        score = diff * confidence
        # Skoru normalize et (-1 ile +1 arası)
        return max(-1.0, min(1.0, score))
    elif abs(diff) > 0.05:  # %5'ten fazla fark varsa (çok agresif)
        # Neutral yüksek ama fark var, yine de kullan
        score = diff * confidence * 0.8  # Biraz daha düşük ağırlık
        return max(-1.0, min(1.0, score))
    else:
        # Gerçekten nötr
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
    
    # Duplicate index'leri temizle (reindex hatasını önlemek için)
    news_df = news_df.reset_index(drop=True)
    
    # Alakasız haberleri filtrele (relevance score kontrolü)
    news_df_filtered = news_df.copy()
    if 'relevance_score' in news_df_filtered.columns:
        # Sadece alakalı haberleri kullan (0.3'ten yüksek relevance)
        news_df_filtered = news_df_filtered[news_df_filtered['relevance_score'] >= 0.3].copy()
        # Index'i reset et (duplicate labels hatasını önlemek için)
        news_df_filtered = news_df_filtered.reset_index(drop=True)
    
    # Eğer filtreleme sonrası haber kalmadıysa, tüm haberleri kullan
    if news_df_filtered.empty:
        news_df_filtered = news_df.copy()
        news_df_filtered = news_df_filtered.reset_index(drop=True)
    
    # Daha yeni haberler daha yüksek ağırlık alır
    if 'published_at' in news_df_filtered.columns:
        min_date = news_df_filtered['published_at'].min()
        max_date = news_df_filtered['published_at'].max()
        
        if (max_date - min_date).days > 0:
            # Her haber için ağırlık: (gün farkı + 1) / max_gün_farkı
            news_df_filtered['days_from_min'] = (news_df_filtered['published_at'] - min_date).dt.days + 1
            max_days = news_df_filtered['days_from_min'].max()
            news_df_filtered['weight'] = news_df_filtered['days_from_min'] / max_days
        else:
            news_df_filtered['weight'] = 1.0
    else:
        news_df_filtered['weight'] = 1.0
    
    # Ağırlıklı ortalama
    weighted_sum = (news_df_filtered['sentiment_score'] * news_df_filtered['weight']).sum()
    total_weight = news_df_filtered['weight'].sum()
    
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


def classify_news_context_and_sentiment(
    title: str,
    content: str,
    company_name: Optional[str] = None,
    ticker: Optional[str] = None,
    gemini_model=None
) -> Dict:
    """
    Haberi "Piyasa Geneli" veya "Hisse Bazlı" olarak sınıflandırır ve duygusunu belirler.
    
    Parametreler:
    ------------
    title : str
        Haber başlığı
    content : str
        Haber içeriği (veya özet)
    company_name : str, optional
        Şirket adı (hisse bazlı analiz için)
    ticker : str, optional
        Borsa kodu (hisse bazlı analiz için)
    gemini_model
        Gemini API modeli (eğer varsa)
    
    Döndürür:
    --------
    dict
        {
            'baglam': 'Piyasa Geneli' veya 'Hisse Bazlı',
            'duygu': 'Pozitif', 'Negatif' veya 'Nötr',
            'confidence': 0-1 arası güven skoru
        }
    """
    
    # Gemini API kullan
    if gemini_model:
        try:
            news_text = f"{title}\n\n{content[:1000]}"  # İlk 1000 karakter
            
            prompt = f"""Sen bir kıdemli finansal analistsin ve Türkiye piyasaları konusunda uzmansın. 
Sana bir haber başlığı ve metni vereceğim. Görevin, bu haberin finansal etkisini iki kategoride değerlendirmek:

Bağlam: Bu haber 'Piyasa Geneli' (BIST100, ekonomi, faiz, politika, genel piyasa trendleri) için mi, 
yoksa 'Hisse Bazlı' (sadece belirli bir şirketle ilgili) mi?

Duygu: Bu bağlamda, haberin tonu 'Pozitif', 'Negatif' veya 'Nötr' mü?

ÖRNEKLER:
- 'TCMB faiz artırımına gitti' → Bağlam: Piyasa Geneli, Duygu: Negatif (bankalar hariç)
- 'X Şirketi rekor kâr açıkladı' → Bağlam: Hisse Bazlı, Duygu: Pozitif
- 'BIST100 endeksi yükseldi' → Bağlam: Piyasa Geneli, Duygu: Pozitif
- 'THYAO yeni uçak siparişi verdi' → Bağlam: Hisse Bazlı, Duygu: Pozitif

ŞİRKET BİLGİSİ:
{f"Şirket: {company_name}" if company_name else ""}
{f"Ticker: {ticker}" if ticker else ""}

HABER:
{news_text}

Çıktıyı SADECE şu JSON formatında ver:
{{
    "baglam": "Piyasa Geneli" veya "Hisse Bazlı",
    "duygu": "Pozitif" veya "Negatif" veya "Nötr",
    "confidence": 0.0 ile 1.0 arası güven skoru,
    "reason": "Kısa açıklama (Türkçe, 1 cümle)"
}}

SADECE JSON yanıt ver, başka hiçbir şey yazma."""
            
            response = gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON'u extract et
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
            return {
                'baglam': result.get('baglam', 'Piyasa Geneli'),
                'duygu': result.get('duygu', 'Nötr'),
                'confidence': float(result.get('confidence', 0.5)),
                'reason': result.get('reason', '')
            }
            
        except Exception as e:
            print(f"⚠️  Gemini context/sentiment analizi hatası: {e}")
            # Fallback: Basit kural tabanlı
            return _classify_with_rules(title, content, company_name, ticker)
    else:
        # Gemini yoksa kural tabanlı
        return _classify_with_rules(title, content, company_name, ticker)


def _classify_with_rules(
    title: str,
    content: str,
    company_name: Optional[str] = None,
    ticker: Optional[str] = None
) -> Dict:
    """
    Kural tabanlı basit sınıflandırma (Gemini yoksa).
    """
    text = f"{title} {content}".lower()
    
    # Piyasa geneli anahtar kelimeleri
    macro_keywords = [
        'tcmb', 'faiz', 'enflasyon', 'bist100', 'bist 100', 'endeks',
        'piyasa', 'ekonomi', 'politika', 'merkez bankası', 'döviz',
        'dolar', 'euro', 'altın', 'petrol', 'borsa', 'genel'
    ]
    
    # Hisse bazlı anahtar kelimeleri
    micro_keywords = [
        'şirket', 'hisse', 'senedi', 'hisse senedi', 'hissedar',
        'kâr', 'zarar', 'gelir', 'satış', 'üretim', 'fabrika',
        'yönetim', 'ceo', 'genel müdür', 'yönetim kurulu'
    ]
    
    macro_count = sum(1 for keyword in macro_keywords if keyword in text)
    micro_count = sum(1 for keyword in micro_keywords if keyword in text)
    
    # Şirket adı veya ticker geçiyorsa hisse bazlı
    if company_name and company_name.lower() in text:
        micro_count += 2
    if ticker and ticker.lower() in text:
        micro_count += 2
    
    # Bağlam belirleme
    if micro_count > macro_count:
        baglam = 'Hisse Bazlı'
    else:
        baglam = 'Piyasa Geneli'
    
    # Duygu belirleme (basit)
    positive_words = ['yükseldi', 'arttı', 'büyüme', 'kâr', 'başarı', 'rekor', 'iyi', 'pozitif']
    negative_words = ['düştü', 'azaldı', 'zarar', 'kayıp', 'kriz', 'düşüş', 'kötü', 'negatif']
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    if pos_count > neg_count:
        duygu = 'Pozitif'
    elif neg_count > pos_count:
        duygu = 'Negatif'
    else:
        duygu = 'Nötr'
    
    return {
        'baglam': baglam,
        'duygu': duygu,
        'confidence': 0.6,  # Kural tabanlı için düşük güven
        'reason': f'Kural tabanlı analiz: {baglam} ({duygu})'
    }


def analyze_news_sentiment(
    news_df: pd.DataFrame, 
    analyzer: SentimentAnalyzer = None,
    company_name: Optional[str] = None,
    ticker: Optional[str] = None,
    use_context_classification: bool = True
) -> pd.DataFrame:
    """
    Haber DataFrame'ine sentiment analizi uygular (makro/mikro sınıflandırma ile).
    
    Parametreler:
    ------------
    news_df : pd.DataFrame
        'title' ve 'summary' kolonları olmalı
    analyzer : SentimentAnalyzer, optional
        Eğer verilmezse yeni bir tane oluşturulur
    company_name : str, optional
        Şirket adı (makro/mikro sınıflandırma için)
    ticker : str, optional
        Borsa kodu (makro/mikro sınıflandırma için)
    use_context_classification : bool
        Makro/mikro sınıflandırma yapılsın mı? (varsayılan: True)
    
    Döndürür:
    --------
    pd.DataFrame
        Orijinal DataFrame + sentiment kolonları + 'news_context', 'context_sentiment' kolonları
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
        text_parts = []
        
        # 1. Başlık (her zaman ekle)
        if title:
            text_parts.append(title)
        
        # 2. Özet (başlıktan farklıysa ve yeterince uzunsa ekle)
        if summary and summary != title and len(summary) > 20:
            text_parts.append(summary)
        
        # 3. İçerik (ilk 800 karakter - daha fazla context için)
        if content and len(content) > 50:
            content_snippet = content[:800].strip()
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
        
        result_dict = {
            'sentiment_class': sentiment_result['class'],
            'sentiment_confidence': sentiment_result['confidence'],
            'sentiment_score': score
        }
        
        # Makro/Mikro sınıflandırma (eğer isteniyorsa)
        if use_context_classification:
            context_result = classify_news_context_and_sentiment(
                title=title,
                content=content or summary,
                company_name=company_name,
                ticker=ticker,
                gemini_model=analyzer.gemini_model if hasattr(analyzer, 'gemini_model') else None
            )
            
            result_dict['news_context'] = context_result['baglam']
            result_dict['context_sentiment'] = context_result['duygu']
            result_dict['context_confidence'] = context_result['confidence']
            result_dict['context_reason'] = context_result.get('reason', '')
        
        results.append(result_dict)
    
    # Sonuçları DataFrame'e ekle
    sentiment_df = pd.DataFrame(results)
    news_df_with_sentiment = pd.concat([news_df.reset_index(drop=True), sentiment_df], axis=1)
    
    return news_df_with_sentiment


def analyze_stock_news(
    news_list: List[Dict],
    analyzer: SentimentAnalyzer = None,
    company_name: Optional[str] = None,
    ticker: Optional[str] = None
) -> float:
    """
    Sadece hisse bazlı (KAP, Google Search(THYAO)) haberleri analiz edip hisse_duygu_skoru üretir.
    
    Parametreler:
    ------------
    news_list : List[Dict]
        Haber listesi. Her dict 'title', 'summary', 'content' içermeli.
        Ayrıca 'news_context' veya 'source' kolonu varsa, 'Hisse Bazlı' olanları filtreler.
    analyzer : SentimentAnalyzer, optional
        Eğer verilmezse yeni bir tane oluşturulur
    company_name : str, optional
        Şirket adı (filtreleme için)
    ticker : str, optional
        Borsa kodu (filtreleme için)
    
    Döndürür:
    --------
    float
        0-100 arası normalize edilmiş hisse_duygu_skoru
    """
    
    if analyzer is None:
        analyzer = SentimentAnalyzer()
    
    # Haber listesini DataFrame'e çevir
    if isinstance(news_list, pd.DataFrame):
        news_df = news_list.copy()
    else:
        news_df = pd.DataFrame(news_list)
    
    if news_df.empty:
        return 50.0  # Nötr skor
    
    # Hisse bazlı haberleri filtrele
    stock_news = []
    
    for idx, row in news_df.iterrows():
        # 1. news_context kolonu varsa ve 'Hisse Bazlı' ise
        if 'news_context' in row and row['news_context'] == 'Hisse Bazlı':
            stock_news.append(row)
            continue
        
        # 2. source kolonu varsa ve KAP veya şirket adı/ticker içeriyorsa
        source = str(row.get('source', '')).lower()
        if 'kap' in source or (company_name and company_name.lower() in source) or (ticker and ticker.lower() in source):
            stock_news.append(row)
            continue
        
        # 3. Başlık veya içerikte şirket adı/ticker geçiyorsa
        title = str(row.get('title', '')).lower()
        summary = str(row.get('summary', '')).lower()
        content = str(row.get('content', '')).lower()
        
        text_combined = f"{title} {summary} {content}"
        
        if (company_name and company_name.lower() in text_combined) or \
           (ticker and ticker.lower() in text_combined):
            stock_news.append(row)
            continue
    
    if not stock_news:
        # Eğer hiç hisse bazlı haber yoksa, tüm haberleri kullan (fallback)
        stock_news = news_df.to_dict('records')
    
    # Sentiment analizi yap
    stock_news_df = pd.DataFrame(stock_news)
    # Duplicate index'leri temizle (reindex hatasını önlemek için)
    stock_news_df = stock_news_df.reset_index(drop=True)
    stock_news_with_sentiment = analyze_news_sentiment(
        stock_news_df,
        analyzer=analyzer,
        company_name=company_name,
        ticker=ticker,
        use_context_classification=True
    )
    
    # Toplam skor
    hisse_duygu_skoru = aggregate_sentiment(stock_news_with_sentiment)
    
    print(f"✅ Hisse bazlı haber analizi: {len(stock_news)} haber, Skor: {hisse_duygu_skoru:.2f}/100")
    
    return hisse_duygu_skoru


def analyze_market_news(
    news_list: List[Dict],
    analyzer: SentimentAnalyzer = None
) -> float:
    """
    Sadece genel piyasa (TCMB, faiz, enflasyon, BIST100) haberlerini analiz edip piyasa_duygu_skoru üretir.
    
    Parametreler:
    ------------
    news_list : List[Dict]
        Haber listesi. Her dict 'title', 'summary', 'content' içermeli.
        Ayrıca 'news_context' kolonu varsa, 'Piyasa Geneli' olanları filtreler.
    analyzer : SentimentAnalyzer, optional
        Eğer verilmezse yeni bir tane oluşturulur
    
    Döndürür:
    --------
    float
        0-100 arası normalize edilmiş piyasa_duygu_skoru
    """
    
    if analyzer is None:
        analyzer = SentimentAnalyzer()
    
    # Haber listesini DataFrame'e çevir
    if isinstance(news_list, pd.DataFrame):
        news_df = news_list.copy()
    else:
        news_df = pd.DataFrame(news_list)
    
    if news_df.empty:
        return 50.0  # Nötr skor
    
    # Piyasa geneli haberleri filtrele
    market_news = []
    
    # Piyasa geneli anahtar kelimeler
    market_keywords = [
        'tcmb', 'faiz', 'enflasyon', 'tüfe', 'üfe', 'bist100', 'bist 100',
        'borsa istanbul', 'piyasa', 'ekonomi', 'politika', 'merkez bankası',
        'interest rate', 'inflation', 'market', 'economy', 'central bank'
    ]
    
    for idx, row in news_df.iterrows():
        # 1. news_context kolonu varsa ve 'Piyasa Geneli' ise
        if 'news_context' in row and row['news_context'] == 'Piyasa Geneli':
            market_news.append(row)
            continue
        
        # 2. Başlık veya içerikte piyasa geneli anahtar kelimeler geçiyorsa
        title = str(row.get('title', '')).lower()
        summary = str(row.get('summary', '')).lower()
        content = str(row.get('content', '')).lower()
        
        text_combined = f"{title} {summary} {content}"
        
        if any(keyword in text_combined for keyword in market_keywords):
            market_news.append(row)
            continue
    
    if not market_news:
        # Eğer hiç piyasa geneli haber yoksa, tüm haberleri kullan (fallback)
        market_news = news_df.to_dict('records')
    
    # Sentiment analizi yap
    market_news_df = pd.DataFrame(market_news)
    # Duplicate index'leri temizle (reindex hatasını önlemek için)
    market_news_df = market_news_df.reset_index(drop=True)
    market_news_with_sentiment = analyze_news_sentiment(
        market_news_df,
        analyzer=analyzer,
        use_context_classification=True
    )
    
    # Toplam skor
    piyasa_duygu_skoru = aggregate_sentiment(market_news_with_sentiment)
    
    print(f"✅ Piyasa geneli haber analizi: {len(market_news)} haber, Skor: {piyasa_duygu_skoru:.2f}/100")
    
    return piyasa_duygu_skoru


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
    
    # Hisse bazlı ve piyasa geneli test
    print("\n\n3. Hisse Bazlı vs Piyasa Geneli Analiz:")
    test_news_mixed = pd.DataFrame({
        'title': [
            'THYAO rekor kâr açıkladı',
            'TCMB faiz artırımı yaptı',
            'THYAO yeni uçak siparişi',
            'BIST100 endeksi yükseldi',
            'THYAO yolcu sayısı arttı'
        ],
        'summary': [
            'THYAO şirketi beklentileri aştı',
            'Merkez Bankası politika faizini artırdı',
            'THYAO yeni uçak siparişi verdi',
            'BIST100 endeksi güne yükselişle başladı',
            'THYAO yolcu sayısında artış'
        ],
        'published_at': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'])
    })
    
    hisse_skoru = analyze_stock_news(test_news_mixed, analyzer, company_name="THYAO", ticker="THYAO")
    piyasa_skoru = analyze_market_news(test_news_mixed, analyzer)
    
    print(f"\nHisse Bazlı Duygu Skoru: {hisse_skoru:.2f}/100")
    print(f"Piyasa Geneli Duygu Skoru: {piyasa_skoru:.2f}/100")

