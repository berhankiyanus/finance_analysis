"""
Tarihsel Hafıza Modülü (RAG Mimarisi)

Geçmiş siyasi ve ekonomik haberleri vektör veritabanında saklar ve
yeni haberler geldiğinde benzer geçmiş olayları bulur.
Bu, "Geçmişte benzer bir olay olduğunda borsa ne tepki verdi?" sorusunu yanıtlar.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import chromadb
from chromadb.config import Settings
from pathlib import Path
import json

# Sentence Transformers için
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  sentence-transformers paketi yüklü değil. Vektör veritabanı kullanılamayacak.")
    print("   💡 Yüklemek için: pip install sentence-transformers")

# Proje kök dizini
project_root = Path(__file__).parent.parent
vector_db_path = project_root / "data" / "vector_db"


class HistoricalMemory:
    """
    Tarihsel haberleri ve piyasa tepkilerini saklayan vektör veritabanı sınıfı.
    """
    
    def __init__(self, collection_name: str = "political_events"):
        """
        Vektör veritabanını başlatır.
        
        Parametreler:
        ------------
        collection_name : str
            ChromaDB collection adı
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.available = False
            print("⚠️  Sentence Transformers yüklü değil. Tarihsel hafıza kullanılamayacak.")
            return
        
        self.available = True
        self.collection_name = collection_name
        
        # Embedding modelini yükle (Türkçe-İngilizce çok dilli model)
        try:
            print("📥 Embedding modeli yükleniyor...")
            self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("✅ Embedding modeli yüklendi.")
        except Exception as e:
            print(f"⚠️  Embedding modeli yüklenemedi: {e}")
            self.available = False
            return
        
        # ChromaDB client'ı başlat
        try:
            # Persistent client (veriler diskte saklanır)
            vector_db_path.mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(vector_db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Collection'ı al veya oluştur
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Tarihsel siyasi ve ekonomik olaylar"}
            )
            
            print(f"✅ ChromaDB bağlantısı kuruldu: {collection_name}")
            print(f"   📊 Mevcut kayıt sayısı: {self.collection.count()}")
            
        except Exception as e:
            print(f"⚠️  ChromaDB başlatılamadı: {e}")
            self.available = False
    
    def add_historical_event(
        self,
        news_text: str,
        news_title: str,
        date: str,
        bist100_change: float,
        ticker: Optional[str] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Geçmiş bir olayı veritabanına ekler.
        
        Parametreler:
        ------------
        news_text : str
            Haber metni
        news_title : str
            Haber başlığı
        date : str
            Tarih (YYYY-MM-DD formatında)
        bist100_change : float
            O günkü BIST100 değişimi (yüzde olarak, örn: -2.3)
        ticker : str, optional
            İlgili hisse kodu
        category : str, optional
            Olay kategorisi (political, economic, etc.)
        metadata : dict, optional
            Ek metadata
        
        Döndürür:
        --------
        bool
            Başarılı ise True
        """
        if not self.available:
            return False
        
        try:
            # Haber metnini birleştir
            full_text = f"{news_title}\n\n{news_text}"
            
            # Embedding oluştur
            embedding = self.embedder.encode(full_text).tolist()
            
            # Metadata hazırla
            event_metadata = {
                'date': date,
                'bist100_change': str(bist100_change),
                'title': news_title[:200],  # ChromaDB metadata limiti için kısalt
                'category': category or 'unknown',
                'ticker': ticker or '',
                **(metadata or {})
            }
            
            # Unique ID oluştur
            event_id = f"event_{date}_{hash(news_title) % 1000000}"
            
            # Veritabanına ekle
            self.collection.add(
                embeddings=[embedding],
                documents=[full_text],
                metadatas=[event_metadata],
                ids=[event_id]
            )
            
            print(f"✅ Tarihsel olay eklendi: {date} - {news_title[:50]}... (BIST100: {bist100_change:+.2f}%)")
            return True
            
        except Exception as e:
            print(f"⚠️  Tarihsel olay eklenirken hata: {e}")
            return False
    
    def find_similar_events(
        self,
        current_news: str,
        current_title: str = "",
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        Yeni haber için benzer geçmiş olayları bulur.
        
        Parametreler:
        ------------
        current_news : str
            Mevcut haber metni
        current_title : str
            Mevcut haber başlığı
        top_k : int
            Kaç benzer olay getirilecek (varsayılan: 5)
        min_similarity : float
            Minimum benzerlik skoru (0-1 arası, varsayılan: 0.5)
        
        Döndürür:
        --------
        list
            Benzer olaylar listesi:
            [
                {
                    'event': 'Haber metni',
                    'date': '2020-01-15',
                    'bist100_change': -2.3,
                    'similarity': 0.89,
                    'category': 'political',
                    'title': 'Haber başlığı'
                },
                ...
            ]
        """
        if not self.available:
            return []
        
        try:
            # Mevcut haberi embedding'e çevir
            full_text = f"{current_title}\n\n{current_news}" if current_title else current_news
            query_embedding = self.embedder.encode(full_text).tolist()
            
            # Benzer olayları ara
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Sonuçları formatla
            similar_events = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    # Distance'ı similarity'ye çevir (ChromaDB cosine distance kullanır)
                    # Distance 0 = tam benzer, 2 = tamamen farklı
                    distance = results['distances'][0][i]
                    similarity = 1 - (distance / 2)  # Normalize et
                    
                    if similarity >= min_similarity:
                        metadata = results['metadatas'][0][i]
                        similar_events.append({
                            'event': results['documents'][0][i],
                            'date': metadata.get('date', 'Unknown'),
                            'bist100_change': float(metadata.get('bist100_change', 0)),
                            'similarity': similarity,
                            'category': metadata.get('category', 'unknown'),
                            'title': metadata.get('title', ''),
                            'ticker': metadata.get('ticker', '')
                        })
            
            # Similarity'ye göre sırala (yüksekten düşüğe)
            similar_events.sort(key=lambda x: x['similarity'], reverse=True)
            
            if similar_events:
                print(f"✅ {len(similar_events)} benzer geçmiş olay bulundu.")
                for event in similar_events[:3]:  # İlk 3'ünü göster
                    print(f"   📅 {event['date']}: {event['title'][:50]}... (BIST100: {event['bist100_change']:+.2f}%, Benzerlik: {event['similarity']:.2f})")
            
            return similar_events
            
        except Exception as e:
            print(f"⚠️  Benzer olaylar aranırken hata: {e}")
            return []
    
    def get_historical_context(
        self,
        current_news: str,
        current_title: str = "",
        top_k: int = 5
    ) -> str:
        """
        Gemini için bağlam (context) metni oluşturur.
        
        Parametreler:
        ------------
        current_news : str
            Mevcut haber metni
        current_title : str
            Mevcut haber başlığı
        top_k : int
            Kaç benzer olay kullanılacak
        
        Döndürür:
        --------
        str
            Gemini'ye verilecek bağlam metni
        """
        similar_events = self.find_similar_events(current_news, current_title, top_k)
        
        if not similar_events:
            return ""
        
        # Ortalama BIST100 değişimini hesapla
        avg_change = sum(e['bist100_change'] for e in similar_events) / len(similar_events)
        
        # Bağlam metni oluştur
        context = f"""
GEÇMİŞTE BENZER OLAYLAR:

"""
        for i, event in enumerate(similar_events, 1):
            context += f"""
{i}. {event['date']}: {event['title']}
   - BIST100 Değişimi: {event['bist100_change']:+.2f}%
   - Benzerlik: {event['similarity']:.1%}
   - Kategori: {event['category']}

"""
        
        context += f"""
ÖZET:
- Geçmişte benzer {len(similar_events)} olayda BIST100 ortalama {avg_change:+.2f}% değişti.
- En yüksek etki: {max(similar_events, key=lambda x: abs(x['bist100_change']))['bist100_change']:+.2f}%
- En düşük etki: {min(similar_events, key=lambda x: abs(x['bist100_change']))['bist100_change']:+.2f}%

"""
        
        return context
    
    def batch_add_events(self, events: List[Dict]) -> int:
        """
        Birden fazla olayı toplu olarak ekler.
        
        Parametreler:
        ------------
        events : list
            Her olay için dict:
            {
                'news_text': str,
                'news_title': str,
                'date': str,
                'bist100_change': float,
                'ticker': str (optional),
                'category': str (optional)
            }
        
        Döndürür:
        --------
        int
            Başarıyla eklenen olay sayısı
        """
        if not self.available:
            return 0
        
        success_count = 0
        for event in events:
            if self.add_historical_event(
                news_text=event.get('news_text', ''),
                news_title=event.get('news_title', ''),
                date=event.get('date', ''),
                bist100_change=event.get('bist100_change', 0.0),
                ticker=event.get('ticker'),
                category=event.get('category')
            ):
                success_count += 1
        
        print(f"✅ {success_count}/{len(events)} olay başarıyla eklendi.")
        return success_count


def populate_historical_data(
    start_date: str = "2014-01-01",
    end_date: str = None,
    limit_per_day: int = 5
) -> int:
    """
    Geçmiş verileri toplayıp vektör veritabanına yükler.
    
    Bu fonksiyon, geçmiş 5-10 yılın siyasi haberlerini ve o günkü BIST100
    değişimlerini toplayıp veritabanına kaydeder.
    
    Parametreler:
    ------------
    start_date : str
        Başlangıç tarihi (YYYY-MM-DD)
    end_date : str
        Bitiş tarihi (None ise bugün)
    limit_per_day : int
        Her gün için maksimum haber sayısı
    
    Döndürür:
    --------
    int
        Eklenen toplam olay sayısı
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📥 Geçmiş veriler toplanıyor: {start_date} - {end_date}")
    
    # Memory instance'ı oluştur
    memory = HistoricalMemory()
    if not memory.available:
        print("❌ Vektör veritabanı kullanılamıyor.")
        return 0
    
    # BIST100 fiyat verilerini çek
    try:
        import yfinance as yf
        bist100 = yf.Ticker("XU100.IS")
        hist = bist100.history(period="10y")
        
        if hist.empty:
            print("⚠️  BIST100 verisi çekilemedi.")
            return 0
        
        print(f"✅ BIST100 verisi çekildi: {len(hist)} gün")
        
    except Exception as e:
        print(f"⚠️  BIST100 verisi çekilemedi: {e}")
        return 0
    
    # Her gün için haberleri topla ve ekle
    total_added = 0
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    for date in date_range:
        date_str = date.strftime("%Y-%m-%d")
        
        # O günkü BIST100 değişimini hesapla
        if date_str in hist.index.strftime("%Y-%m-%d").values:
            date_idx = hist.index[hist.index.strftime("%Y-%m-%d") == date_str]
            if len(date_idx) > 0:
                current_idx = date_idx[0]
                prev_idx = hist.index[hist.index < current_idx]
                
                if len(prev_idx) > 0:
                    prev_date = prev_idx[-1]
                    change = (hist.loc[current_idx, 'Close'] / hist.loc[prev_date, 'Close'] - 1) * 100
                    
                    # O günkü siyasi haberleri bul (NewsAPI veya Google News RSS)
                    try:
                        from src.data_collection import get_news
                        from src.political_classifier import classify_news_political_impact
                        
                        news_df = get_news("Türkiye", days_back=1, ticker="XU100")
                        
                        # Sadece siyasi haberleri filtrele
                        political_news = []
                        for _, row in news_df.iterrows():
                            classification = classify_news_political_impact(
                                news_text=row.get('summary', ''),
                                news_title=row.get('title', '')
                            )
                            
                            if classification.get('category') == 'political':
                                political_news.append({
                                    'news_text': row.get('summary', ''),
                                    'news_title': row.get('title', ''),
                                    'date': date_str,
                                    'bist100_change': change,
                                    'category': 'political'
                                })
                        
                        # İlk N haberini ekle
                        for news in political_news[:limit_per_day]:
                            if memory.add_historical_event(**news):
                                total_added += 1
                    
                    except Exception as e:
                        # Hata durumunda sessizce devam et
                        pass
    
    print(f"✅ Toplam {total_added} tarihsel olay eklendi.")
    return total_added


if __name__ == "__main__":
    print("=== Tarihsel Hafıza Modülü Test ===\n")
    
    # Memory instance'ı oluştur
    memory = HistoricalMemory()
    
    if not memory.available:
        print("❌ Vektör veritabanı kullanılamıyor.")
        exit(1)
    
    # Test: Örnek olay ekle
    print("\n1. Test olayı ekleniyor...")
    memory.add_historical_event(
        news_text="Ekonomi Bakanı istifa etti. Hükümet krizi yaşanıyor.",
        news_title="Ekonomi Bakanı İstifa Etti",
        date="2020-01-15",
        bist100_change=-2.3,
        category="political"
    )
    
    # Test: Benzer olayları bul
    print("\n2. Benzer olaylar aranıyor...")
    similar = memory.find_similar_events(
        current_news="Maliye Bakanı istifa etti",
        current_title="Maliye Bakanı İstifa Etti",
        top_k=3
    )
    
    print(f"\n✅ {len(similar)} benzer olay bulundu:")
    for event in similar:
        print(f"   - {event['date']}: {event['title']} (BIST100: {event['bist100_change']:+.2f}%, Benzerlik: {event['similarity']:.2f})")
    
    # Test: Bağlam metni
    print("\n3. Bağlam metni oluşturuluyor...")
    context = memory.get_historical_context(
        current_news="Bakan istifa etti",
        current_title="Bakan İstifa Etti"
    )
    print(context)

