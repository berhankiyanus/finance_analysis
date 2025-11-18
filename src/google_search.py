"""
Google Search Entegrasyonu Modülü

Piyasa haberlerini Google Search üzerinden çeker.
Not: Google Custom Search API veya alternatif servisler kullanılabilir.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# .env dosyasından API key'leri yükle
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)


def search_google_news(query: str, num_results: int = 10, 
                      api_key: Optional[str] = None,
                      search_engine_id: Optional[str] = None,
                      use_custom_search: bool = True,
                      days_back: int = 7) -> List[Dict]:
    """
    Google Search API kullanarak haber araması yapar.
    
    Parametreler:
    ------------
    query : str
        Arama sorgusu
    num_results : int
        Kaç sonuç getirilecek (varsayılan: 10)
    api_key : str, optional
        Google Custom Search API anahtarı
    search_engine_id : str, optional
        Google Custom Search Engine ID
    use_custom_search : bool
        Google Custom Search API kullanılsın mı? (varsayılan: True)
    
    Döndürür:
    --------
    list
        Her haber için dict: {'title', 'link', 'snippet', 'source', 'date'}
    """
    
    if use_custom_search:
        return _search_with_custom_search_api(query, num_results, api_key, search_engine_id, days_back)
    else:
        # Alternatif: DuckDuckGo veya başka bir servis
        return _search_with_alternative(query, num_results)


def _search_with_custom_search_api(query: str, num_results: int,
                                   api_key: Optional[str],
                                   search_engine_id: Optional[str],
                                   days_back: int = 7) -> List[Dict]:
    """
    Google Custom Search API kullanarak arama yapar.
    """
    
    # API key ve Engine ID'yi .env'den al
    if api_key is None:
        api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    if search_engine_id is None:
        search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not api_key or not search_engine_id:
        print("⚠️  Google Custom Search API key veya Engine ID bulunamadı.")
        print("   Alternatif yöntem kullanılıyor veya dummy veri döndürülüyor.")
        return _get_dummy_search_results(query, num_results)
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Türkçe kaynaklara öncelik ver (Türk şirketleri için)
        # Query'de Türkçe karakterler varsa veya .IS uzantılı ticker varsa Türkçe arama yap
        is_turkish_query = any(char in query for char in 'çğıöşüÇĞIİÖŞÜ') or '.IS' in query.upper()
        
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': query,
            'num': min(num_results, 10),  # Google API maksimum 10 sonuç döndürür
            'dateRestrict': f'd{days_back}' if days_back <= 30 else 'm1'  # Son X gün veya 1 ay
        }
        
        # Türkçe sorgular için dil parametresi ekle
        if is_turkish_query:
            params['lr'] = 'lang_tr'  # Türkçe sonuçlara öncelik
            params['cr'] = 'countryTR'  # Türkiye kaynaklarına öncelik
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        items = data.get('items', [])
        
        for item in items:
            # Sadece ekonomi sitelerinden gelen haberleri filtrele
            link = item.get('link', '')
            allowed_domains = ['bloomberght.com', 'ekonomim.com', 'dunya.com', 
                             'hurriyet.com.tr', 'milliyet.com.tr', 'sozcu.com.tr',
                             'ntv.com.tr', 'cnnturk.com', 'aa.com.tr']
            
            if not any(domain in link for domain in allowed_domains):
                continue
            
            results.append({
                'title': item.get('title', ''),
                'link': link,
                'snippet': item.get('snippet', ''),
                'source': _extract_domain(link),
                'date': datetime.now()  # Google API tarih bilgisi vermiyor
            })
        
        if results:
            print(f"✅ '{query}' için {len(results)} haber bulundu.")
        else:
            print(f"⚠️  '{query}' için uygun haber bulunamadı.")
            return _get_dummy_search_results(query, num_results)
        
        return results[:num_results]
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Google Search API hatası: {e}")
        return _get_dummy_search_results(query, num_results)
    except Exception as e:
        print(f"❌ Google Search parse hatası: {e}")
        return _get_dummy_search_results(query, num_results)


def _search_with_alternative(query: str, num_results: int) -> List[Dict]:
    """
    Alternatif arama yöntemi (DuckDuckGo veya başka servisler).
    """
    try:
        # DuckDuckGo kullanımı (örnek)
        # Not: Gerçek implementasyon için duckduckgo-search veya benzeri kütüphane gerekebilir
        print("⚠️  Alternatif arama yöntemi henüz implement edilmedi.")
        print("   Google Custom Search API kullanmanız önerilir.")
        return _get_dummy_search_results(query, num_results)
    except Exception as e:
        print(f"❌ Alternatif arama hatası: {e}")
        return _get_dummy_search_results(query, num_results)


def _extract_domain(url: str) -> str:
    """
    URL'den domain adını çıkarır.
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return url


def _get_dummy_search_results(query: str, num_results: int) -> List[Dict]:
    """
    Test amaçlı dummy arama sonuçları.
    """
    dummy_results = []
    
    sources = ['bloomberght.com', 'ekonomim.com', 'dunya.com']
    titles = [
        f"TCMB Faiz Kararı: {query} ile ilgili gelişmeler",
        f"BIST100 Endeksi {query} etkisi altında",
        f"Ekonomi Haberleri: {query} analizi",
        f"Piyasa Güncellemesi: {query}",
        f"Yatırım Analizi: {query} değerlendirmesi"
    ]
    
    for i in range(min(num_results, len(titles))):
        dummy_results.append({
            'title': titles[i % len(titles)],
            'link': f"https://{sources[i % len(sources)]}/haber-{i+1}",
            'snippet': f"{query} ile ilgili önemli gelişmeler ve analizler...",
            'source': sources[i % len(sources)],
            'date': datetime.now() - timedelta(hours=i)
        })
    
    return dummy_results


def search_market_news(keywords: List[str], num_results: int = 10,
                      api_key: Optional[str] = None,
                      search_engine_id: Optional[str] = None) -> List[Dict]:
    """
    Piyasa haberlerini aramak için özel fonksiyon.
    
    Parametreler:
    ------------
    keywords : list
        Arama anahtar kelimeleri (örn: ['TCMB', 'faiz', 'BIST100'])
    num_results : int
        Her anahtar kelime için kaç sonuç (varsayılan: 10)
    api_key : str, optional
        Google Custom Search API anahtarı. Eğer None ise .env'den okunur.
    search_engine_id : str, optional
        Google Custom Search Engine ID. Eğer None ise .env'den okunur.
    
    Döndürür:
    --------
    list
        Tüm haberler (duplicate'ler filtrelenmiş). API key yoksa boş liste döner.
    """
    
    # API key ve Engine ID'yi .env'den al (eğer parametre olarak verilmemişse)
    if api_key is None:
        api_key = os.getenv('GOOGLE_CSE_API_KEY') or os.getenv('GOOGLE_SEARCH_API_KEY')
    if search_engine_id is None:
        search_engine_id = os.getenv('GOOGLE_CSE_ID') or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    # API key veya Engine ID yoksa hata fırlatma, sadece uyarı log'u bas ve boş liste döndür
    if not api_key or not search_engine_id:
        print("⚠️  Google Search API key veya Engine ID bulunamadı.")
        print("   Google Search özelliği devre dışı. Sadece NewsAPI kullanılacak.")
        print("   💡 Google Custom Search API key almak için: https://developers.google.com/custom-search/v1/overview")
        return []
    
    try:
        all_results = []
        seen_links = set()
        
        # Anahtar kelimeleri birleştir
        query = " ".join(keywords)  # "VE" yerine boşluk kullan (daha esnek arama)
        
        results = search_google_news(
            query=query,
            num_results=num_results,
            api_key=api_key,
            search_engine_id=search_engine_id
        )
        
        # Duplicate'leri filtrele
        for result in results:
            link = result.get('link', '')
            if link not in seen_links:
                seen_links.add(link)
                # Formatı normalize et (published_at ekle)
                normalized_result = {
                    "title": result.get('title', ''),
                    "link": link,
                    "snippet": result.get('snippet', ''),
                    "source": result.get('source', _extract_domain(link)),
                    "published_at": result.get('date')  # datetime veya None
                }
                all_results.append(normalized_result)
        
        if all_results:
            print(f"✅ Google Search'ten {len(all_results)} benzersiz haber bulundu.")
        return all_results
        
    except Exception as e:
        print(f"⚠️  Google Search hatası: {e}")
        print("   Google Search özelliği devre dışı. Sadece NewsAPI kullanılacak.")
        return []


if __name__ == "__main__":
    print("=== Google Search Modülü Test ===\n")
    
    # Test
    print("1. Piyasa haberleri araması:")
    keywords = ['TCMB', 'faiz kararı', 'BIST100']
    results = search_market_news(keywords, num_results=10)
    
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Kaynak: {result['source']}")
        print(f"   Link: {result['link']}")
        print(f"   Özet: {result['snippet'][:100]}...")

