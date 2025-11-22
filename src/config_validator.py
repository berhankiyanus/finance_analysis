"""
Yapılandırma Doğrulama Modülü

API anahtarları ve gerekli yapılandırmaları doğrular.
Streamlit ve CLI'da aynı davranışı sağlar.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dotenv import load_dotenv
from src.logger_config import setup_logger, mask_api_key

logger = setup_logger(__name__)

# Proje kök dizini
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'

# .env dosyasını yükle
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.debug(f".env dosyası yüklendi: {env_path}")
else:
    logger.warning(f".env dosyası bulunamadı: {env_path}")


class ConfigValidator:
    """
    Yapılandırma doğrulama sınıfı.
    """
    
    # Zorunlu API anahtarları (opsiyonel: REQUIRE_* env var ile kontrol edilir)
    REQUIRED_KEYS = {
        'NEWS_API_KEY': {
            'name': 'NewsAPI',
            'url': 'https://newsapi.org/',
            'description': 'Haber toplama için gerekli',
            'required': os.getenv('REQUIRE_NEWS_API_KEY', 'false').lower() == 'true'
        },
        'GEMINI_API_KEY': {
            'name': 'Google Gemini',
            'url': 'https://ai.google.dev/',
            'description': 'AI analiz ve sentiment için (opsiyonel)',
            'required': os.getenv('REQUIRE_GEMINI_API_KEY', 'false').lower() == 'true'
        },
        'TCMB_API_KEY': {
            'name': 'TCMB EVDS',
            'url': 'https://evds2.tcmb.gov.tr/',
            'description': 'Türkiye makroekonomik veriler için (opsiyonel)',
            'required': os.getenv('REQUIRE_TCMB_API_KEY', 'false').lower() == 'true'
        }
    }
    
    @classmethod
    def validate_config(cls, raise_on_missing: bool = False) -> Tuple[bool, Dict[str, any]]:
        """
        Yapılandırmayı doğrular.
        
        Parametreler:
        ------------
        raise_on_missing : bool
            Zorunlu anahtar eksikse Exception fırlatılsın mı? (varsayılan: False)
        
        Döndürür:
        --------
        Tuple[bool, Dict]
            (Başarılı mı?, Detaylı sonuçlar)
        """
        results = {
            'valid': True,
            'missing_required': [],
            'missing_optional': [],
            'found_keys': [],
            'warnings': []
        }
        
        for key_name, key_info in cls.REQUIRED_KEYS.items():
            api_key = os.getenv(key_name)
            
            if api_key:
                results['found_keys'].append({
                    'key': key_name,
                    'name': key_info['name'],
                    'masked': mask_api_key(api_key)
                })
                logger.debug(f"✅ {key_info['name']} anahtarı bulundu: {mask_api_key(api_key)}")
            else:
                if key_info['required']:
                    results['missing_required'].append({
                        'key': key_name,
                        'name': key_info['name'],
                        'url': key_info['url'],
                        'description': key_info['description']
                    })
                    results['valid'] = False
                    logger.error(f"❌ ZORUNLU: {key_info['name']} anahtarı bulunamadı!")
                else:
                    results['missing_optional'].append({
                        'key': key_name,
                        'name': key_info['name'],
                        'url': key_info['url'],
                        'description': key_info['description']
                    })
                    logger.warning(f"⚠️  Opsiyonel: {key_info['name']} anahtarı bulunamadı")
        
        # .env dosyası kontrolü
        if not env_path.exists():
            results['warnings'].append({
                'type': 'env_file_missing',
                'message': f'.env dosyası bulunamadı: {env_path}',
                'solution': 'Proje kök dizininde .env dosyası oluşturun'
            })
        
        # Zorunlu anahtar eksikse
        if results['missing_required']:
            error_msg = "Zorunlu API anahtarları eksik:\n"
            for missing in results['missing_required']:
                error_msg += f"  - {missing['name']} ({missing['key']}): {missing['description']}\n"
                error_msg += f"    Al: {missing['url']}\n"
            
            logger.error(error_msg)
            
            if raise_on_missing:
                raise ValueError(error_msg)
        
        return results['valid'], results
    
    @classmethod
    def get_config_summary(cls) -> str:
        """
        Yapılandırma özetini döndürür (kullanıcıya gösterilebilir).
        
        Döndürür:
        --------
        str
            Yapılandırma özeti
        """
        is_valid, results = cls.validate_config()
        
        summary = "📋 Yapılandırma Durumu\n"
        summary += "=" * 60 + "\n\n"
        
        # Bulunan anahtarlar
        if results['found_keys']:
            summary += "✅ Bulunan API Anahtarları:\n"
            for key_info in results['found_keys']:
                summary += f"   • {key_info['name']}: {key_info['masked']}\n"
            summary += "\n"
        
        # Eksik opsiyonel anahtarlar
        if results['missing_optional']:
            summary += "⚠️  Eksik Opsiyonel Anahtarlar:\n"
            for missing in results['missing_optional']:
                summary += f"   • {missing['name']} ({missing['key']})\n"
                summary += f"     {missing['description']}\n"
                summary += f"     Al: {missing['url']}\n"
            summary += "\n"
        
        # Eksik zorunlu anahtarlar
        if results['missing_required']:
            summary += "❌ Eksik Zorunlu Anahtarlar:\n"
            for missing in results['missing_required']:
                summary += f"   • {missing['name']} ({missing['key']})\n"
                summary += f"     {missing['description']}\n"
                summary += f"     Al: {missing['url']}\n"
            summary += "\n"
        
        # Uyarılar
        if results['warnings']:
            summary += "⚠️  Uyarılar:\n"
            for warning in results['warnings']:
                summary += f"   • {warning['message']}\n"
                summary += f"     Çözüm: {warning['solution']}\n"
            summary += "\n"
        
        # Genel durum
        if is_valid:
            summary += "✅ Yapılandırma geçerli!\n"
        else:
            summary += "❌ Yapılandırma geçersiz! Lütfen eksik anahtarları ekleyin.\n"
        
        return summary
    
    @classmethod
    def check_news_api_key(cls) -> bool:
        """
        NewsAPI anahtarının varlığını kontrol eder.
        
        Döndürür:
        --------
        bool
            Anahtar varsa True
        """
        return os.getenv('NEWS_API_KEY') is not None
    
    @classmethod
    def check_gemini_api_key(cls) -> bool:
        """
        Gemini API anahtarının varlığını kontrol eder.
        
        Döndürür:
        --------
        bool
            Anahtar varsa True
        """
        return os.getenv('GEMINI_API_KEY') is not None


def validate_config_on_startup(raise_on_missing: bool = False) -> Tuple[bool, Dict]:
    """
    Uygulama başlangıcında yapılandırmayı doğrular.
    
    Parametreler:
    ------------
    raise_on_missing : bool
        Zorunlu anahtar eksikse Exception fırlatılsın mı?
    
    Döndürür:
    --------
    Tuple[bool, Dict]
        (Yapılandırma geçerli mi?, Detaylı sonuçlar)
    """
    logger.info("Yapılandırma doğrulanıyor...")
    is_valid, results = ConfigValidator.validate_config(raise_on_missing=raise_on_missing)
    
    if is_valid:
        logger.info("✅ Yapılandırma geçerli!")
    else:
        logger.warning("⚠️  Yapılandırma eksik veya geçersiz!")
        logger.info(ConfigValidator.get_config_summary())
    
    return is_valid, results


if __name__ == "__main__":
    # Test
    summary = ConfigValidator.get_config_summary()
    logger.info(summary)
    print(summary)  # CLI için print kullan
    
    logger.info("\n" + "=" * 60)
    is_valid, results = ConfigValidator.validate_config()
    
    result_text = f"\nGeçerli mi? {is_valid}"
    result_text += f"\nBulunan anahtarlar: {len(results['found_keys'])}"
    result_text += f"\nEksik opsiyonel: {len(results['missing_optional'])}"
    result_text += f"\nEksik zorunlu: {len(results['missing_required'])}"
    
    logger.info(result_text)
    print(result_text)  # CLI için print kullan

