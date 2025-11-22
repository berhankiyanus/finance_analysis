"""
Model Cache Modülü

CLI/servis katmanında model yaşam döngüsünü yönetir.
Streamlit'teki @st.cache_resource gibi çalışır.
"""

from typing import Optional
import threading
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# Global cache (singleton pattern)
_sentiment_analyzer: Optional[object] = None
_political_classifier: Optional[object] = None
_lock = threading.Lock()


def get_sentiment_analyzer(use_gemini: bool = True, force_reload: bool = False):
    """
    SentimentAnalyzer singleton döndürür.
    
    Parametreler:
    ------------
    use_gemini : bool
        Gemini API kullanılsın mı?
    force_reload : bool
        Cache'i atla ve yeni model yükle (varsayılan: False)
    
    Döndürür:
    --------
    SentimentAnalyzer
        Cache'lenmiş veya yeni yüklenmiş SentimentAnalyzer
    """
    global _sentiment_analyzer
    
    with _lock:
        if _sentiment_analyzer is None or force_reload:
            logger.info("SentimentAnalyzer yükleniyor (ilk kez veya force_reload=True)...")
            from src.sentiment_analysis import SentimentAnalyzer
            _sentiment_analyzer = SentimentAnalyzer(use_gemini=use_gemini)
            logger.info("✅ SentimentAnalyzer cache'e eklendi.")
        else:
            logger.debug("SentimentAnalyzer cache'den döndürülüyor.")
    
    return _sentiment_analyzer


def get_political_classifier(force_reload: bool = False):
    """
    PoliticalClassifier singleton döndürür.
    
    Parametreler:
    ------------
    force_reload : bool
        Cache'i atla ve yeni model yükle (varsayılan: False)
    
    Döndürür:
    --------
    PoliticalClassifier veya None
        Cache'lenmiş veya yeni yüklenmiş PoliticalClassifier
    """
    global _political_classifier
    
    try:
        from src.political_classifier import PoliticalClassifier
    except ImportError:
        logger.debug("PoliticalClassifier modülü bulunamadı.")
        return None
    
    with _lock:
        if _political_classifier is None or force_reload:
            logger.info("PoliticalClassifier yükleniyor (ilk kez veya force_reload=True)...")
            _political_classifier = PoliticalClassifier()
            logger.info("✅ PoliticalClassifier cache'e eklendi.")
        else:
            logger.debug("PoliticalClassifier cache'den döndürülüyor.")
    
    return _political_classifier


def clear_cache():
    """
    Tüm model cache'lerini temizler.
    """
    global _sentiment_analyzer, _political_classifier
    
    with _lock:
        _sentiment_analyzer = None
        _political_classifier = None
        logger.info("Model cache temizlendi.")


def is_sentiment_analyzer_cached() -> bool:
    """
    SentimentAnalyzer cache'de mi kontrol eder.
    
    Döndürür:
    --------
    bool
        True ise cache'de var
    """
    return _sentiment_analyzer is not None

