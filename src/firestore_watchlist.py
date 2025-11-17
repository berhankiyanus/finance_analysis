"""
Firestore Watchlist Modülü

Kullanıcıların hisse senedi izleme listesi oluşturmasını sağlar.
Google Firebase Firestore kullanır.
"""

import os
from typing import List, Optional, Dict
from datetime import datetime

try:
    from google.cloud import firestore
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    print("⚠️  google-cloud-firestore paketi yüklü değil. Firestore kullanılamayacak.")


def get_firestore_client():
    """
    Firestore client'ı döndürür.
    
    Döndürür:
    --------
    firestore.Client veya None
    """
    if not FIRESTORE_AVAILABLE:
        return None
    
    try:
        # Google Cloud credentials'ı kontrol et
        # 1. Environment variable'dan
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            db = firestore.Client()
            return db
        
        # 2. Default credentials (gcloud auth application-default login)
        try:
            db = firestore.Client()
            return db
        except Exception:
            print("⚠️  Firestore credentials bulunamadı.")
            print("   💡 Google Cloud credentials ayarlayın veya GOOGLE_APPLICATION_CREDENTIALS environment variable'ını set edin.")
            return None
            
    except Exception as e:
        print(f"⚠️  Firestore client oluşturulamadı: {e}")
        return None


def save_watchlist(user_id: str, tickers: List[str]) -> bool:
    """
    Kullanıcının izleme listesini Firestore'a kaydeder.
    
    Parametreler:
    ------------
    user_id : str
        Kullanıcı ID'si
    tickers : list
        İzleme listesindeki ticker'lar (örn: ['THYAO', 'EREGL', 'TUPRS'])
    
    Döndürür:
    --------
    bool
        Başarılı ise True
    """
    
    db = get_firestore_client()
    if not db:
        print("⚠️  Firestore client mevcut değil. Watchlist kaydedilemedi.")
        return False
    
    try:
        # Watchlist koleksiyonuna kaydet
        watchlist_ref = db.collection('watchlist').document(user_id)
        watchlist_ref.set({
            'tickers': tickers,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_at': watchlist_ref.get().to_dict().get('created_at', firestore.SERVER_TIMESTAMP) if watchlist_ref.get().exists else firestore.SERVER_TIMESTAMP
        })
        
        print(f"✅ Watchlist kaydedildi: {user_id} -> {tickers}")
        return True
        
    except Exception as e:
        print(f"❌ Watchlist kaydedilirken hata: {e}")
        return False


def get_watchlist(user_id: str) -> List[str]:
    """
    Kullanıcının izleme listesini Firestore'dan okur.
    
    Parametreler:
    ------------
    user_id : str
        Kullanıcı ID'si
    
    Döndürür:
    --------
    list
        İzleme listesindeki ticker'lar
    """
    
    db = get_firestore_client()
    if not db:
        print("⚠️  Firestore client mevcut değil. Watchlist okunamadı.")
        return []
    
    try:
        watchlist_ref = db.collection('watchlist').document(user_id)
        doc = watchlist_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            tickers = data.get('tickers', [])
            print(f"✅ Watchlist okundu: {user_id} -> {tickers}")
            return tickers
        else:
            print(f"ℹ️  Watchlist bulunamadı: {user_id}")
            return []
            
    except Exception as e:
        print(f"❌ Watchlist okunurken hata: {e}")
        return []


def add_to_watchlist(user_id: str, ticker: str) -> bool:
    """
    İzleme listesine yeni bir ticker ekler.
    
    Parametreler:
    ------------
    user_id : str
        Kullanıcı ID'si
    ticker : str
        Eklenecek ticker (örn: 'THYAO')
    
    Döndürür:
    --------
    bool
        Başarılı ise True
    """
    
    current_watchlist = get_watchlist(user_id)
    
    if ticker not in current_watchlist:
        current_watchlist.append(ticker)
        return save_watchlist(user_id, current_watchlist)
    else:
        print(f"ℹ️  Ticker zaten watchlist'te: {ticker}")
        return True


def remove_from_watchlist(user_id: str, ticker: str) -> bool:
    """
    İzleme listesinden bir ticker çıkarır.
    
    Parametreler:
    ------------
    user_id : str
        Kullanıcı ID'si
    ticker : str
        Çıkarılacak ticker
    
    Döndürür:
    --------
    bool
        Başarılı ise True
    """
    
    current_watchlist = get_watchlist(user_id)
    
    if ticker in current_watchlist:
        current_watchlist.remove(ticker)
        return save_watchlist(user_id, current_watchlist)
    else:
        print(f"ℹ️  Ticker watchlist'te yok: {ticker}")
        return True


if __name__ == "__main__":
    print("=== Firestore Watchlist Modülü Test ===\n")
    
    if not FIRESTORE_AVAILABLE:
        print("⚠️  google-cloud-firestore yüklü değil.")
        print("   Yüklemek için: pip install google-cloud-firestore")
    else:
        # Test
        test_user_id = "test_user_123"
        
        print(f"1. Watchlist kaydetme: {test_user_id}")
        success = save_watchlist(test_user_id, ['THYAO', 'EREGL', 'TUPRS'])
        print(f"   Sonuç: {'✅ Başarılı' if success else '❌ Başarısız'}")
        
        print(f"\n2. Watchlist okuma: {test_user_id}")
        watchlist = get_watchlist(test_user_id)
        print(f"   Watchlist: {watchlist}")
        
        print(f"\n3. Watchlist'e ekleme: {test_user_id} -> 'AKBNK'")
        success = add_to_watchlist(test_user_id, 'AKBNK')
        print(f"   Sonuç: {'✅ Başarılı' if success else '❌ Başarısız'}")
        print(f"   Güncel watchlist: {get_watchlist(test_user_id)}")
        
        print(f"\n4. Watchlist'ten çıkarma: {test_user_id} -> 'AKBNK'")
        success = remove_from_watchlist(test_user_id, 'AKBNK')
        print(f"   Sonuç: {'✅ Başarılı' if success else '❌ Başarısız'}")
        print(f"   Güncel watchlist: {get_watchlist(test_user_id)}")

