"""
Stale Data Manager Modülü

API hatası durumunda dummy veri yerine en son kaydedilmiş veriyi (stale data) gösterir.
Kullanıcıya veri güncelliği hakkında bilgi verir.
"""

import os
import json
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# Stale data dizini
project_root = Path(__file__).parent.parent
STALE_DATA_DIR = project_root / "data" / "stale_cache"
STALE_DATA_DIR.mkdir(parents=True, exist_ok=True)


class StaleDataManager:
    """
    Stale (bayat) veri yönetimi sınıfı.
    API hatası durumunda en son kaydedilmiş veriyi gösterir.
    """
    
    def __init__(self, max_age_hours: int = 24):
        """
        Stale data manager'ı başlatır.
        
        Parametreler:
        ------------
        max_age_hours : int
            Maksimum veri yaşı (saat). Bu süreden eski veriler kullanılmaz.
        """
        self.max_age_hours = max_age_hours
        self.stale_data_dir = STALE_DATA_DIR
    
    def _get_cache_path(self, data_type: str, identifier: str) -> Path:
        """
        Cache dosya yolunu döndürür.
        
        Parametreler:
        ------------
        data_type : str
            Veri tipi (örn: "price_data", "news_data")
        identifier : str
            Veri tanımlayıcısı (örn: ticker, company_name)
        
        Döndürür:
        --------
        Path
            Cache dosya yolu
        """
        safe_identifier = identifier.replace('.', '_').replace('/', '_')
        return self.stale_data_dir / f"{data_type}_{safe_identifier}.json"
    
    def save_data(
        self,
        data_type: str,
        identifier: str,
        data: Any,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Veriyi cache'e kaydeder.
        
        Parametreler:
        ------------
        data_type : str
            Veri tipi
        identifier : str
            Veri tanımlayıcısı
        data : Any
            Kaydedilecek veri (DataFrame veya dict)
        metadata : dict
            Ek metadata (opsiyonel)
        
        Döndürür:
        --------
        bool
            Başarılı mı?
        """
        try:
            cache_path = self._get_cache_path(data_type, identifier)
            
            # DataFrame'i dict'e çevir
            if isinstance(data, pd.DataFrame):
                data_dict = {
                    'data': data.to_dict('records'),
                    'columns': list(data.columns),
                    'index': data.index.tolist() if hasattr(data.index, 'tolist') else None
                }
            else:
                data_dict = {'data': data}
            
            # Metadata ekle
            save_data = {
                'data': data_dict,
                'metadata': metadata or {},
                'saved_at': datetime.now().isoformat(),
                'data_type': data_type,
                'identifier': identifier
            }
            
            # JSON'a kaydet
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.debug(f"Stale data kaydedildi: {data_type} - {identifier}")
            return True
            
        except Exception as e:
            logger.warning(f"Stale data kaydedilemedi: {e}")
            return False
    
    def get_stale_data(
        self,
        data_type: str,
        identifier: str,
        max_age_hours: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Cache'den stale veriyi okur.
        
        Parametreler:
        ------------
        data_type : str
            Veri tipi
        identifier : str
            Veri tanımlayıcısı
        max_age_hours : int
            Maksimum veri yaşı (saat). None ise self.max_age_hours kullanılır.
        
        Döndürür:
        --------
        dict veya None
            Stale veri ve metadata, veya None (yoksa veya çok eskiyse)
        """
        try:
            cache_path = self._get_cache_path(data_type, identifier)
            
            if not cache_path.exists():
                return None
            
            # JSON'dan oku
            with open(cache_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # Veri yaşını kontrol et
            saved_at = datetime.fromisoformat(saved_data['saved_at'])
            age_hours = (datetime.now() - saved_at).total_seconds() / 3600
            
            max_age = max_age_hours or self.max_age_hours
            if age_hours > max_age:
                logger.debug(f"Stale data çok eski ({age_hours:.1f} saat), kullanılmıyor")
                return None
            
            # DataFrame'i geri yükle
            data_dict = saved_data['data']
            if 'columns' in data_dict:
                # DataFrame
                df = pd.DataFrame(data_dict['data'])
                if data_dict.get('index'):
                    df.index = pd.to_datetime(data_dict['index'])
                saved_data['data'] = df
            else:
                # Dict veya diğer
                saved_data['data'] = data_dict['data']
            
            saved_data['age_hours'] = age_hours
            saved_data['is_stale'] = age_hours > 1  # 1 saatten eski ise stale
            
            return saved_data
            
        except Exception as e:
            logger.warning(f"Stale data okunamadı: {e}")
            return None
    
    def get_data_with_fallback(
        self,
        data_type: str,
        identifier: str,
        fetch_func,
        *args,
        **kwargs
    ) -> tuple[Any, Dict]:
        """
        Veriyi çeker, başarısız olursa stale data kullanır.
        
        Parametreler:
        ------------
        data_type : str
            Veri tipi
        identifier : str
            Veri tanımlayıcısı
        fetch_func : callable
            Veri çekme fonksiyonu
        *args, **kwargs
            fetch_func'a geçirilecek parametreler
        
        Döndürür:
        --------
        tuple
            (veri, metadata_dict)
            metadata_dict içinde: 'is_stale', 'age_hours', 'last_updated' bilgileri var
        """
        metadata = {
            'is_stale': False,
            'age_hours': 0.0,
            'last_updated': datetime.now().isoformat(),
            'source': 'api'
        }
        
        try:
            # Önce API'den çekmeyi dene
            data = fetch_func(*args, **kwargs)
            
            # Başarılıysa cache'e kaydet
            if data is not None:
                self.save_data(data_type, identifier, data, metadata)
                return data, metadata
            
        except Exception as e:
            logger.warning(f"API'den veri çekilemedi ({data_type} - {identifier}): {e}")
        
        # API başarısız oldu, stale data'yı dene
        stale_data = self.get_stale_data(data_type, identifier)
        
        if stale_data:
            logger.info(f"⚠️ Stale data kullanılıyor: {data_type} - {identifier} ({stale_data['age_hours']:.1f} saat önce)")
            metadata.update({
                'is_stale': True,
                'age_hours': stale_data['age_hours'],
                'last_updated': stale_data['saved_at'],
                'source': 'stale_cache',
                'warning': f"Veriler güncel değil (Son güncelleme: {stale_data['age_hours']:.1f} saat önce)"
            })
            return stale_data['data'], metadata
        else:
            # Stale data da yok, hata döndür
            logger.error(f"❌ Veri bulunamadı: {data_type} - {identifier} (API hatası ve stale data yok)")
            raise ValueError(f"{data_type} verisi çekilemedi ve cache'de de yok. Lütfen daha sonra tekrar deneyin.")


# Global instance
_stale_data_manager = None


def get_stale_data_manager() -> StaleDataManager:
    """
    Stale data manager instance'ını döndürür (singleton pattern).
    
    Döndürür:
    --------
    StaleDataManager
        Stale data manager instance'ı
    """
    global _stale_data_manager
    if _stale_data_manager is None:
        _stale_data_manager = StaleDataManager()
    return _stale_data_manager


if __name__ == "__main__":
    # Test
    print("=== Stale Data Manager Test ===\n")
    
    manager = get_stale_data_manager()
    
    # Test verisi kaydet
    test_df = pd.DataFrame({
        'date': pd.date_range(end=datetime.now(), periods=10, freq='D'),
        'value': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    })
    
    print("1. Test verisi kaydediliyor...")
    manager.save_data("test_data", "TEST", test_df)
    
    # Stale data oku
    print("2. Stale data okunuyor...")
    stale = manager.get_stale_data("test_data", "TEST")
    
    if stale:
        print(f"   ✅ Veri bulundu: {stale['age_hours']:.2f} saat önce kaydedilmiş")
        print(f"   📊 Veri: {len(stale['data'])} satır")
    else:
        print("   ❌ Veri bulunamadı")

