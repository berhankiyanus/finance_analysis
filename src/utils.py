"""
Yardımcı fonksiyonlar modülü
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Logger oluştur
logger = logging.getLogger(__name__)


def load_api_key_from_streamlit_or_env(
    key_name: str,
    sidebar_label: Optional[str] = None,
    required: bool = False,
    default_value: Optional[str] = None
) -> Optional[str]:
    """
    API key'i Streamlit secrets veya .env dosyasından yükler.
    
    Parametreler:
    ------------
    key_name : str
        API key'in adı (örn: "NEWS_API_KEY")
    sidebar_label : str, optional
        Sidebar'da gösterilecek etiket (None ise key_name kullanılır)
    required : bool
        Zorunlu mu? (True ise key yoksa hata gösterir)
    default_value : str, optional
        Varsayılan değer
    
    Döndürür:
    --------
    str veya None
        API key değeri
    """
    import streamlit as st
    
    # Sidebar label belirle
    if sidebar_label is None:
        sidebar_label = key_name
    
    api_key = None
    
    # 1. Streamlit Cloud secrets'tan dene
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            api_key = st.secrets[key_name]
            os.environ[key_name] = api_key
            if sidebar_label:
                st.sidebar.success(f"✅ {sidebar_label} Streamlit secrets'tan yüklendi")
            logger.info(f"{key_name} loaded from Streamlit secrets")
    except Exception as e:
        logger.debug(f"Streamlit secrets not available: {e}")
    
    # 2. .env dosyasından dene
    if api_key is None:
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'
        
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            api_key = os.getenv(key_name)
            if api_key:
                if sidebar_label:
                    st.sidebar.success(f"✅ {sidebar_label} .env dosyasından yüklendi")
                logger.info(f"{key_name} loaded from .env file")
            else:
                if sidebar_label and required:
                    st.sidebar.warning(f"⚠️ .env dosyası var ama {sidebar_label} bulunamadı")
        else:
            if sidebar_label and required:
                st.sidebar.warning(f"⚠️ .env dosyası bulunamadı")
    
    # 3. Environment variable'dan dene
    if api_key is None:
        api_key = os.getenv(key_name)
        if api_key:
            if sidebar_label:
                st.sidebar.info(f"ℹ️ {sidebar_label} environment variable'dan yüklendi")
            logger.info(f"{key_name} loaded from environment variable")
    
    # 4. Default değer kullan
    if api_key is None and default_value:
        api_key = default_value
        logger.debug(f"{key_name} using default value")
    
    # 5. Son kontrol
    if api_key:
        os.environ[key_name] = api_key
    elif required:
        if sidebar_label:
            st.sidebar.error(f"❌ {sidebar_label} bulunamadı! Lütfen Streamlit secrets veya .env dosyasına ekleyin.")
        logger.error(f"{key_name} not found and is required")
    else:
        if sidebar_label:
            st.sidebar.info(f"ℹ️ {sidebar_label} bulunamadı (opsiyonel)")
        logger.info(f"{key_name} not found (optional)")
    
    return api_key


def ensure_directory_exists(directory_path: str) -> Path:
    """
    Dizin yoksa oluşturur.
    
    Parametreler:
    ------------
    directory_path : str
        Dizin yolu
    
    Döndürür:
    --------
    Path
        Dizin Path objesi
    """
    dir_path = Path(directory_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Directory ensured: {dir_path}")
    return dir_path

