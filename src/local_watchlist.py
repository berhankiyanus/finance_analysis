"""
Yerel İzleme Listesi Modülü

Firebase olmadan çalışan basit watchlist sistemi.
Veriler session_state veya JSON dosyasında saklanır.
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

# Watchlist dosyası yolu
WATCHLIST_FILE = Path(__file__).parent.parent / "data" / "watchlist.json"


def ensure_watchlist_dir():
    """Watchlist dizinini oluşturur."""
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_watchlist() -> List[Dict]:
    """
    İzleme listesini yükler (JSON dosyasından veya session_state'den).
    
    Döndürür:
    --------
    list
        Watchlist öğeleri: [{'ticker': 'AAPL', 'company_name': 'Apple', 'added_date': '...'}, ...]
    """
    try:
        # Önce session_state'den dene (Streamlit için)
        try:
            import streamlit as st
            if 'watchlist' in st.session_state:
                return st.session_state.watchlist
        except:
            pass
        
        # Session state yoksa JSON dosyasından yükle
        if WATCHLIST_FILE.exists():
            with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('items', [])
        
        return []
    except Exception as e:
        print(f"⚠️  Watchlist yüklenirken hata: {e}")
        return []


def save_watchlist(items: List[Dict]):
    """
    İzleme listesini kaydeder (JSON dosyasına ve session_state'e).
    
    Parametreler:
    ------------
    items : list
        Watchlist öğeleri
    """
    try:
        ensure_watchlist_dir()
        
        # JSON dosyasına kaydet
        data = {
            'items': items,
            'last_updated': datetime.now().isoformat()
        }
        with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Session state'e de kaydet (Streamlit için)
        try:
            import streamlit as st
            st.session_state.watchlist = items
        except:
            pass
        
        print(f"✅ Watchlist kaydedildi ({len(items)} öğe).")
    except Exception as e:
        print(f"⚠️  Watchlist kaydedilirken hata: {e}")


def add_to_watchlist(ticker: str, company_name: str) -> bool:
    """
    İzleme listesine hisse ekler.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu (örn: "AAPL", "THYAO.IS")
    company_name : str
        Şirket adı
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    try:
        items = load_watchlist()
        
        # Zaten var mı kontrol et
        if any(item.get('ticker') == ticker for item in items):
            print(f"⚠️  {ticker} zaten izleme listesinde.")
            return False
        
        # Yeni öğe ekle
        new_item = {
            'ticker': ticker,
            'company_name': company_name,
            'added_date': datetime.now().isoformat()
        }
        items.append(new_item)
        
        save_watchlist(items)
        print(f"✅ {ticker} ({company_name}) izleme listesine eklendi.")
        return True
    except Exception as e:
        print(f"❌ Watchlist'e eklenirken hata: {e}")
        return False


def remove_from_watchlist(ticker: str) -> bool:
    """
    İzleme listesinden hisse çıkarır.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    try:
        items = load_watchlist()
        
        # Öğeyi bul ve çıkar
        original_count = len(items)
        items = [item for item in items if item.get('ticker') != ticker]
        
        if len(items) < original_count:
            save_watchlist(items)
            print(f"✅ {ticker} izleme listesinden çıkarıldı.")
            return True
        else:
            print(f"⚠️  {ticker} izleme listesinde bulunamadı.")
            return False
    except Exception as e:
        print(f"❌ Watchlist'ten çıkarılırken hata: {e}")
        return False


def get_watchlist() -> List[Dict]:
    """
    İzleme listesini döndürür.
    
    Döndürür:
    --------
    list
        Watchlist öğeleri
    """
    return load_watchlist()


def clear_watchlist():
    """İzleme listesini temizler."""
    try:
        save_watchlist([])
        print("✅ Watchlist temizlendi.")
    except Exception as e:
        print(f"❌ Watchlist temizlenirken hata: {e}")


if __name__ == "__main__":
    print("=== Yerel Watchlist Modülü Test ===\n")
    
    # Test
    print("1. Watchlist'e ekleme:")
    add_to_watchlist("AAPL", "Apple Inc.")
    add_to_watchlist("THYAO.IS", "Türk Hava Yolları")
    
    print("\n2. Watchlist'i görüntüleme:")
    items = get_watchlist()
    for item in items:
        print(f"   • {item['ticker']}: {item['company_name']}")
    
    print("\n3. Watchlist'ten çıkarma:")
    remove_from_watchlist("AAPL")
    
    print("\n4. Güncel watchlist:")
    items = get_watchlist()
    for item in items:
        print(f"   • {item['ticker']}: {item['company_name']}")

