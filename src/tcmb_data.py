"""
TCMB (Türkiye Cumhuriyet Merkez Bankası) EVDS API Modülü

TCMB'nin Elektronik Veri Dağıtım Sistemi (EVDS) üzerinden 
makroekonomik verileri çeker.
"""

import requests
import pandas as pd
from typing import Dict, Optional
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# .env dosyasından API key'leri yükle
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# EVDS kütüphanesi (opsiyonel)
try:
    import evds
    EVDS_AVAILABLE = True
except ImportError:
    EVDS_AVAILABLE = False
    print("ℹ️  evds paketi yüklü değil. Requests ile veri çekilecek.")
    print("   💡 Daha kolay kullanım için: pip install evds")


def get_tcmb_data(series_code: str, start_date: Optional[str] = None, 
                  end_date: Optional[str] = None, api_key: Optional[str] = None) -> pd.DataFrame:
    """
    TCMB EVDS API'den veri çeker.
    
    Parametreler:
    ------------
    series_code : str
        Veri serisi kodu (örn: 'TP.DK.A.01' = Politika Faizi)
    start_date : str, optional
        Başlangıç tarihi (YYYY-MM-DD formatında)
    end_date : str, optional
        Bitiş tarihi (YYYY-MM-DD formatında)
    api_key : str, optional
        TCMB EVDS API anahtarı (eğer gerekliyse)
    
    Döndürür:
    --------
    pd.DataFrame
        Tarih ve değer kolonları içeren DataFrame
    """
    
    # Tarih aralığı belirle (varsayılan: son 24 ay)
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    # API key'i .env'den al (eğer parametre olarak verilmemişse)
    if api_key is None:
        api_key = os.getenv('TCMB_API_KEY') or os.getenv('EVDS_API_KEY')
    
    # EVDS kütüphanesi varsa kullan (daha kolay)
    if EVDS_AVAILABLE and api_key:
        try:
            evds_client = evds.EVDS(api_key)
            # EVDS kütüphanesi formatı: get_data(series_code, start_date, end_date)
            data = evds_client.get_data(
                series_code,
                start_date.replace('-', ''),
                end_date.replace('-', '')
            )
            # EVDS kütüphanesi DataFrame döndürür
            if isinstance(data, pd.DataFrame) and not data.empty:
                # Tarih kolonunu kontrol et ve düzenle
                if 'Tarih' in data.columns:
                    data['date'] = pd.to_datetime(data['Tarih'], errors='coerce')
                    data = data.rename(columns={'Tarih': 'date'})
                elif 'date' not in data.columns:
                    # Tarih kolonu yoksa index'ten oluştur
                    data['date'] = pd.date_range(start=start_date, end=end_date, freq='D')[:len(data)]
                
                # Değer kolonunu bul
                value_cols = [col for col in data.columns if col != 'date' and data[col].dtype in ['float64', 'int64']]
                if value_cols:
                    data = data[['date', value_cols[0]]].copy()
                    data = data.rename(columns={value_cols[0]: 'value'})
                else:
                    data['value'] = None
                
                print(f"✅ {series_code} için {len(data)} veri noktası çekildi (EVDS kütüphanesi).")
                return data[['date', 'value']].copy()
        except Exception as evds_error:
            print(f"⚠️  EVDS kütüphanesi hatası: {evds_error}")
            print("   Requests ile denenecek...")
    
    # EVDS kütüphanesi yoksa veya hata verdi, requests ile dene
    try:
        # TCMB EVDS API endpoint (doğru format)
        base_url = "https://evds2.tcmb.gov.tr/service/evds"
        
        # API key zorunlu (TCMB EVDS API ücretsiz ama key gerektirir)
        if not api_key:
            print("⚠️  TCMB_API_KEY bulunamadı. Dummy veri kullanılıyor.")
            print("   💡 TCMB EVDS API key almak için: https://evds2.tcmb.gov.tr/")
            return _get_dummy_tcmb_data(series_code, start_date, end_date)
        
        # TCMB EVDS API formatı: series parametresi virgülle ayrılmış seri kodları
        params = {
            'series': series_code,
            'startDate': start_date.replace('-', ''),
            'endDate': end_date.replace('-', ''),
            'type': 'json',
            'key': api_key,
            'aggregationTypes': 'avg'  # Ortalama
        }
        
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # JSON yapısını DataFrame'e çevir
        if isinstance(data, dict) and 'items' in data:
            items = data['items']
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        if not items:
            print(f"⚠️  {series_code} için veri bulunamadı.")
            return _get_dummy_tcmb_data(series_code, start_date, end_date)
        
        # DataFrame oluştur
        df = pd.DataFrame(items)
        
        # Tarih kolonunu bul ve datetime'a çevir
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'tarih' in col.lower() or col == 'Tarih':
                date_col = col
                break
        
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df = df.rename(columns={date_col: 'date'})
        else:
            # Tarih kolonu yoksa index olarak ekle
            df['date'] = pd.date_range(start=start_date, end=end_date, freq='D')[:len(df)]
        
        # Değer kolonunu bul
        value_col = None
        for col in df.columns:
            if col != 'date' and df[col].dtype in ['float64', 'int64']:
                value_col = col
                break
        
        if value_col:
            df = df.rename(columns={value_col: 'value'})
            df = df[['date', 'value']].copy()
        else:
            df = df[['date']].copy()
            df['value'] = None
        
        # Tarihe göre sırala
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"✅ {series_code} için {len(df)} veri noktası çekildi.")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ TCMB verisi çekilirken hata: {e}")
        print("⚠️  Dummy veri kullanılıyor.")
        return _get_dummy_tcmb_data(series_code, start_date, end_date)
    except Exception as e:
        print(f"❌ TCMB verisi parse edilirken hata: {e}")
        return _get_dummy_tcmb_data(series_code, start_date, end_date)


def _get_dummy_tcmb_data(series_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Test amaçlı dummy TCMB verisi.
    """
    import numpy as np
    
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Aylık veri oluştur
    dates = pd.date_range(start=start, end=end, freq='M')
    
    # Seri koduna göre farklı değerler
    if 'TP.DK.A.01' in series_code or 'faiz' in series_code.lower():
        # Politika faizi: 20-50 arası
        base_value = 35.0
        values = base_value + np.random.normal(0, 5, len(dates))
    elif 'TP.FG.T1' in series_code or 'tufe' in series_code.lower() or 'enflasyon' in series_code.lower():
        # TÜFE: 30-80 arası
        base_value = 50.0
        values = base_value + np.random.normal(0, 10, len(dates))
    else:
        # Genel
        values = np.random.rand(len(dates)) * 100
    
    df = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    return df


def get_policy_rate(months: int = 24, api_key: Optional[str] = None) -> pd.DataFrame:
    """
    TCMB politika faizini çeker.
    
    Parametreler:
    ------------
    months : int
        Kaç aylık veri (varsayılan: 24)
    api_key : str, optional
        TCMB EVDS API anahtarı
    
    Döndürür:
    --------
    pd.DataFrame
        Tarih ve faiz oranı
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
    
    return get_tcmb_data('TP.DK.A.01', start_date, end_date, api_key)


def get_inflation_tufe(months: int = 24, api_key: Optional[str] = None) -> pd.DataFrame:
    """
    TÜFE (Tüketici Fiyat Endeksi) verisini çeker.
    
    Parametreler:
    ------------
    months : int
        Kaç aylık veri (varsayılan: 24)
    api_key : str, optional
        TCMB EVDS API anahtarı
    
    Döndürür:
    --------
    pd.DataFrame
        Tarih ve TÜFE değeri
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
    
    return get_tcmb_data('TP.FG.T1', start_date, end_date, api_key)


def get_usd_try_rate(months: int = 24, api_key: Optional[str] = None) -> pd.DataFrame:
    """
    USD/TRY kuru verisini çeker.
    
    Parametreler:
    ------------
    months : int
        Kaç aylık veri (varsayılan: 24)
    api_key : str, optional
        TCMB EVDS API anahtarı
    
    Döndürür:
    --------
    pd.DataFrame
        Tarih ve USD/TRY kuru
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
    
    # TCMB EVDS seri kodu: TP.DK.USD.A (USD/TRY Alış)
    return get_tcmb_data('TP.DK.USD.A', start_date, end_date, api_key)


def get_macroeconomic_indicators(api_key: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Birden fazla makroekonomik göstergeyi çeker.
    
    Parametreler:
    ------------
    api_key : str, optional
        TCMB EVDS API anahtarı
    
    Döndürür:
    --------
    dict
        Her gösterge için DataFrame
    """
    
    indicators = {
        'policy_rate': get_policy_rate(api_key=api_key),
        'inflation_tufe': get_inflation_tufe(api_key=api_key),
        'usd_try_rate': get_usd_try_rate(api_key=api_key),
    }
    
    return indicators


if __name__ == "__main__":
    print("=== TCMB Veri Toplama Modülü Test ===\n")
    
    # Test
    print("1. Politika Faizi (Son 24 ay):")
    policy_rate = get_policy_rate()
    print(policy_rate.head())
    print(f"\nSon faiz oranı: {policy_rate['value'].iloc[-1]:.2f}%")
    
    print("\n2. TÜFE (Son 24 ay):")
    inflation = get_inflation_tufe()
    print(inflation.head())
    print(f"\nSon TÜFE: {inflation['value'].iloc[-1]:.2f}")
    
    print("\n3. Tüm Makroekonomik Göstergeler:")
    indicators = get_macroeconomic_indicators()
    for name, df in indicators.items():
        print(f"\n{name}: {len(df)} veri noktası")

