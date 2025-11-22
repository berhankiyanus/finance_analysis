"""
Yapılandırılabilir Logging Modülü

Tüm modüller için merkezi logging sistemi.
Print yerine yapılandırılabilir logger kullanır.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Proje kök dizini
project_root = Path(__file__).parent.parent
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """JSON formatında log çıktısı için formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Exception bilgisi varsa ekle
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_format: bool = False
) -> logging.Logger:
    """
    Yapılandırılabilir logger oluşturur.
    
    Parametreler:
    ------------
    name : str
        Logger adı (genellikle __name__)
    level : str, optional
        Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        Varsayılan: LOG_LEVEL env var veya INFO
    log_to_file : bool
        Dosyaya log yazılsın mı? (varsayılan: True)
    log_to_console : bool
        Konsola log yazılsın mı? (varsayılan: True)
    json_format : bool
        JSON formatında log yazılsın mı? (varsayılan: False)
    
    Döndürür:
    --------
    logging.Logger
        Yapılandırılmış logger
    """
    logger = logging.getLogger(name)
    
    # Logger zaten yapılandırılmışsa, mevcut handler'ları temizle
    if logger.handlers:
        logger.handlers.clear()
    
    # Log seviyesi
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_file = log_dir / f"{name.replace('.', '_')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Dosyaya tüm seviyeler
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def mask_api_key(api_key: Optional[str], show_chars: int = 0) -> str:
    """
    API key'i maskele (güvenlik için).
    
    Parametreler:
    ------------
    api_key : str, optional
        API key
    show_chars : int
        Baştan kaç karakter gösterilecek (varsayılan: 0, hiç gösterme)
    
    Döndürür:
    --------
    str
        Maskelenmiş API key veya "***" (yoksa)
    """
    if not api_key:
        return "***"
    
    if show_chars > 0 and len(api_key) > show_chars:
        return api_key[:show_chars] + "*" * (len(api_key) - show_chars)
    
    return "***"


# Varsayılan logger (modül seviyesinde)
default_logger = setup_logger('finance_analysis', log_to_file=False)

