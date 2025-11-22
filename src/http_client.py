"""
Güvenli HTTP İstemci Modülü

Tüm harici servis çağrıları için timeout, retry ve backoff desteği.
"""

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
import logging

from src.logger_config import setup_logger

logger = setup_logger(__name__, log_to_file=False)


class SafeHTTPClient:
    """
    Timeout, retry ve backoff desteği olan HTTP istemci.
    """
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        retry_on: tuple = (500, 502, 503, 504, 429)
    ):
        """
        Güvenli HTTP istemci oluşturur.
        
        Parametreler:
        ------------
        timeout : int
            İstek timeout'u (saniye, varsayılan: 30)
        max_retries : int
            Maksimum yeniden deneme sayısı (varsayılan: 3)
        backoff_factor : float
            Backoff çarpanı (varsayılan: 1.0)
        retry_on : tuple
            Hangi HTTP kodlarında retry yapılacak (varsayılan: 5xx ve 429)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Retry stratejisi
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=retry_on,
            allowed_methods=["GET", "POST"],
            raise_on_status=False
        )
        
        # HTTP adapter
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # Session oluştur
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        Güvenli GET isteği yapar.
        
        Parametreler:
        ------------
        url : str
            İstek URL'i
        params : dict, optional
            Query parametreleri
        headers : dict, optional
            HTTP başlıkları
        **kwargs
            Diğer requests.get() parametreleri
        
        Döndürür:
        --------
        requests.Response
            HTTP yanıtı
        
        Yükseltir:
        --------
        requests.exceptions.RequestException
            İstek başarısız olursa
        """
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  İstek timeout: {url} (timeout: {self.timeout}s)")
            raise
        except requests.exceptions.HTTPError as e:
            logger.warning(f"❌ HTTP hatası: {e.response.status_code} - {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ İstek hatası: {e} - {url}")
            raise
    
    def post(
        self,
        url: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> requests.Response:
        """
        Güvenli POST isteği yapar.
        
        Parametreler:
        ------------
        url : str
            İstek URL'i
        json : dict, optional
            JSON body
        data : dict, optional
            Form data
        headers : dict, optional
            HTTP başlıkları
        **kwargs
            Diğer requests.post() parametreleri
        
        Döndürür:
        --------
        requests.Response
            HTTP yanıtı
        
        Yükseltir:
        --------
        requests.exceptions.RequestException
            İstek başarısız olursa
        """
        try:
            response = self.session.post(
                url,
                json=json,
                data=data,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  İstek timeout: {url} (timeout: {self.timeout}s)")
            raise
        except requests.exceptions.HTTPError as e:
            logger.warning(f"❌ HTTP hatası: {e.response.status_code} - {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ İstek hatası: {e} - {url}")
            raise


# Varsayılan istemci (singleton)
_default_client = None


def get_http_client() -> SafeHTTPClient:
    """
    Varsayılan HTTP istemcisini döndürür (singleton).
    
    Döndürür:
    --------
    SafeHTTPClient
        Yapılandırılmış HTTP istemci
    """
    global _default_client
    if _default_client is None:
        _default_client = SafeHTTPClient(
            timeout=int(os.getenv('HTTP_TIMEOUT', '30')),
            max_retries=int(os.getenv('HTTP_MAX_RETRIES', '3')),
            backoff_factor=float(os.getenv('HTTP_BACKOFF_FACTOR', '1.0'))
        )
    return _default_client


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator: Fonksiyon çağrıları için retry ve backoff desteği.
    
    Parametreler:
    ------------
    max_retries : int
        Maksimum yeniden deneme sayısı
    backoff_factor : float
        Backoff çarpanı (her denemede bekleme süresi = backoff_factor * 2^attempt)
    exceptions : tuple
        Hangi exception'larda retry yapılacak
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(
                            f"⚠️  {func.__name__} başarısız (deneme {attempt + 1}/{max_retries}). "
                            f"{wait_time:.1f}s bekleniyor..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ {func.__name__} {max_retries} denemeden sonra başarısız oldu.")
            raise last_exception
        return wrapper
    return decorator

