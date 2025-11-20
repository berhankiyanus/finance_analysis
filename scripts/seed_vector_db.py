"""
Vektör Veritabanını Geçmiş Verilerle Doldurma Scripti

Son 5 yılın önemli siyasi ve ekonomik olaylarını ve o günkü BIST100 değişimlerini
ChromaDB'ye yükler.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.vector_memory import HistoricalMemory
import yfinance as yf


def get_bist100_change(date: str) -> float:
    """
    Belirli bir tarihteki BIST100 değişimini hesaplar.
    
    Parametreler:
    ------------
    date : str
        Tarih (YYYY-MM-DD formatında)
    
    Döndürür:
    --------
    float
        BIST100 değişimi (yüzde olarak)
    """
    try:
        bist100 = yf.Ticker("XU100.IS")
        hist = bist100.history(period="10y")
        
        if hist.empty:
            return 0.0
        
        # Tarihi datetime'a çevir
        target_date = pd.to_datetime(date)
        
        # O günkü ve önceki günün fiyatını bul
        if target_date in hist.index:
            current_idx = hist.index.get_loc(target_date)
            if current_idx > 0:
                prev_idx = current_idx - 1
                prev_price = hist.iloc[prev_idx]['Close']
                current_price = hist.iloc[current_idx]['Close']
                change = (current_price / prev_price - 1) * 100
                return change
        
        # Tam tarih bulunamazsa en yakın tarihi bul
        closest_date = hist.index[hist.index <= target_date]
        if len(closest_date) > 0:
            current_date = closest_date[-1]
            current_idx = hist.index.get_loc(current_date)
            if current_idx > 0:
                prev_idx = current_idx - 1
                prev_price = hist.iloc[prev_idx]['Close']
                current_price = hist.iloc[current_idx]['Close']
                change = (current_price / prev_price - 1) * 100
                return change
        
        return 0.0
    except Exception as e:
        print(f"⚠️  BIST100 değişimi hesaplanamadı ({date}): {e}")
        return 0.0


def get_historical_events() -> list:
    """
    Geçmiş önemli olayları döndürür.
    
    Bu fonksiyon manuel olarak önemli olayları içerir.
    İleride NewsAPI veya başka kaynaklardan otomatik çekilebilir.
    
    Döndürür:
    --------
    list
        Her olay için dict:
        {
            'news_title': str,
            'news_text': str,
            'date': str,
            'category': str,
            'ticker': str (optional)
        }
    """
    events = [
        # 2024 Olayları
        {
            'news_title': 'TCMB Faiz Kararı: Politika Faizi %45\'e Yükseltildi',
            'news_text': 'Türkiye Cumhuriyet Merkez Bankası (TCMB) Para Politikası Kurulu, politika faizini %45\'e yükseltti. Bu karar, enflasyonla mücadele kapsamında alındı.',
            'date': '2024-01-25',
            'category': 'economic',
            'ticker': None
        },
        {
            'news_title': 'Seçim Sonuçları Açıklandı',
            'news_text': 'Cumhurbaşkanlığı seçimleri sonuçlandı. Yeni hükümet kuruldu.',
            'date': '2023-05-28',
            'category': 'political',
            'ticker': None
        },
        {
            'news_title': 'Dolar/TL Kuru Rekor Seviyeye Ulaştı',
            'news_text': 'Dolar/TL kuru tarihi rekor seviyeye ulaştı. Piyasalarda belirsizlik hakim.',
            'date': '2023-08-14',
            'category': 'economic',
            'ticker': None
        },
        {
            'news_title': 'Ekonomi Bakanı İstifa Etti',
            'news_text': 'Ekonomi Bakanı görevinden istifa etti. Hükümet krizi yaşanıyor.',
            'date': '2023-11-01',
            'category': 'political',
            'ticker': None
        },
        {
            'news_title': 'TCMB Faiz Kararı: Politika Faizi %25\'e Düşürüldü',
            'news_text': 'TCMB Para Politikası Kurulu, politika faizini %25\'e düşürdü. Bu karar, büyüme odaklı politika değişikliği olarak yorumlandı.',
            'date': '2022-09-22',
            'category': 'economic',
            'ticker': None
        },
        {
            'news_title': 'Erken Seçim Kararı Alındı',
            'news_text': 'Cumhurbaşkanı erken seçim kararı aldı. Siyasi belirsizlik arttı.',
            'date': '2023-03-10',
            'category': 'political',
            'ticker': None
        },
        {
            'news_title': 'Enflasyon Verisi Açıklandı: %80\'i Aştı',
            'news_text': 'TÜİK enflasyon verisini açıkladı. Yıllık enflasyon %80\'i aştı.',
            'date': '2022-10-03',
            'category': 'economic',
            'ticker': None
        },
        {
            'news_title': 'Dış Politika Kriz: AB ile İlişkiler Gerildi',
            'news_text': 'AB ile ilişkilerde gerilim arttı. Dış politika krizi yaşanıyor.',
            'date': '2022-06-15',
            'category': 'political',
            'ticker': None
        },
        {
            'news_title': 'TCMB Başkanı Değişti',
            'news_text': 'TCMB Başkanı görevinden ayrıldı. Yeni başkan atandı.',
            'date': '2021-03-20',
            'category': 'political',
            'ticker': None
        },
        {
            'news_title': 'Pandemi Sonrası Ekonomi Toplantısı',
            'news_text': 'Pandemi sonrası ekonomi toplantısı yapıldı. Yeni ekonomik paket açıklandı.',
            'date': '2021-05-10',
            'category': 'economic',
            'ticker': None
        },
        {
            'news_title': 'Seçim Sonuçları: Yeni Hükümet Kuruldu',
            'news_text': 'Seçim sonuçları açıklandı. Yeni hükümet kuruldu ve ekonomi bakanı atandı.',
            'date': '2023-06-03',
            'category': 'political',
            'ticker': None
        },
        {
            'news_title': 'TCMB Faiz Kararı: Politika Faizi %30\'a Yükseltildi',
            'news_text': 'TCMB Para Politikası Kurulu, politika faizini %30\'a yükseltti. Bu karar, enflasyonla mücadele kapsamında alındı.',
            'date': '2023-08-24',
            'category': 'economic',
            'ticker': None
        },
        {
            'news_title': 'Döviz Kuru Müdahalesi',
            'news_text': 'TCMB döviz kuru müdahalesi yaptı. Piyasalarda dalgalanma yaşandı.',
            'date': '2022-12-20',
            'category': 'economic',
            'ticker': None
        },
        {
            'news_title': 'Bakanlar Kurulu Toplantısı: Ekonomi Paketi',
            'news_text': 'Bakanlar Kurulu toplantısında yeni ekonomi paketi açıklandı. Piyasalar olumlu tepki verdi.',
            'date': '2023-09-15',
            'category': 'political',
            'ticker': None
        },
        {
            'news_title': 'TCMB Faiz Kararı: Politika Faizi %50\'ye Yükseltildi',
            'news_text': 'TCMB Para Politikası Kurulu, politika faizini %50\'ye yükseltti. Bu karar, enflasyonla mücadele kapsamında alındı.',
            'date': '2024-03-21',
            'category': 'economic',
            'ticker': None
        },
    ]
    
    return events


def seed_vector_database():
    """
    Vektör veritabanını geçmiş verilerle doldurur.
    """
    print("🚀 Vektör Veritabanı Doldurma İşlemi Başlatılıyor...\n")
    
    # Memory instance'ı oluştur
    memory = HistoricalMemory()
    
    if not memory.available:
        print("❌ Vektör veritabanı kullanılamıyor.")
        print("   💡 ChromaDB ve sentence-transformers paketlerinin yüklü olduğundan emin olun.")
        return
    
    # Geçmiş olayları al
    events = get_historical_events()
    print(f"📋 {len(events)} geçmiş olay bulundu.\n")
    
    # Her olay için BIST100 değişimini hesapla ve ekle
    success_count = 0
    failed_count = 0
    
    for i, event in enumerate(events, 1):
        print(f"[{i}/{len(events)}] İşleniyor: {event['date']} - {event['news_title'][:50]}...")
        
        # BIST100 değişimini hesapla
        bist100_change = get_bist100_change(event['date'])
        
        if abs(bist100_change) < 0.01:
            print(f"   ⚠️  BIST100 değişimi hesaplanamadı veya çok küçük. Atlanıyor.")
            failed_count += 1
            continue
        
        # Olayı veritabanına ekle
        if memory.add_historical_event(
            news_text=event['news_text'],
            news_title=event['news_title'],
            date=event['date'],
            bist100_change=bist100_change,
            ticker=event.get('ticker'),
            category=event['category']
        ):
            print(f"   ✅ Eklendi (BIST100: {bist100_change:+.2f}%)")
            success_count += 1
        else:
            print(f"   ❌ Eklenemedi")
            failed_count += 1
    
    print(f"\n✅ İşlem Tamamlandı!")
    print(f"   • Başarılı: {success_count}")
    print(f"   • Başarısız: {failed_count}")
    print(f"   • Toplam Kayıt: {memory.collection.count()}")
    
    # Test: Benzer olay arama
    print("\n🧪 Test: Benzer Olay Arama")
    test_news = "TCMB faiz kararı açıklandı. Politika faizi yükseltildi."
    similar = memory.find_similar_events(
        current_news=test_news,
        current_title="TCMB Faiz Kararı",
        top_k=3
    )
    
    if similar:
        print(f"   ✅ {len(similar)} benzer olay bulundu:")
        for event in similar:
            print(f"      - {event['date']}: {event['title'][:50]}... (BIST100: {event['bist100_change']:+.2f}%, Benzerlik: {event['similarity']:.2f})")
    else:
        print("   ⚠️  Benzer olay bulunamadı.")


if __name__ == "__main__":
    seed_vector_database()

