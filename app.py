"""
Finansal Analiz Web Uygulaması

Streamlit ile oluşturulmuş kullanıcı dostu web arayüzü.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path
import os
# typing import'u - Streamlit Cloud uyumluluğu için
from typing import Dict, List, Any
try:
    from typing import Optional
except (ImportError, NameError):
    # Fallback: Optional yerine Union kullan
    from typing import Union
    Optional = lambda T: Union[T, None]
from dotenv import load_dotenv

# Proje kök dizinini path'e ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Streamlit Cloud için ek path düzenlemesi
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Yardımcı fonksiyonları import et (try-except ile güvenli import)
try:
    from src.utils import load_api_key_from_streamlit_or_env
except ImportError:
    # Fallback: Doğrudan modül import
    import importlib.util
    utils_path = project_root / "src" / "utils.py"
    if utils_path.exists():
        spec = importlib.util.spec_from_file_location("src.utils", utils_path)
        utils_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(utils_module)
        load_api_key_from_streamlit_or_env = utils_module.load_api_key_from_streamlit_or_env
    else:
        raise ImportError("src.utils modülü bulunamadı")

# API Key'leri yükle (refactored helper fonksiyon ile)
NEWS_API_KEY = load_api_key_from_streamlit_or_env(
    "NEWS_API_KEY",
    sidebar_label="News API Key",
    required=True
)

GEMINI_API_KEY = load_api_key_from_streamlit_or_env(
    "GEMINI_API_KEY",
    sidebar_label="Gemini API Key",
    required=False
)

if not GEMINI_API_KEY:
    st.sidebar.info("   💡 Daha iyi sentiment analizi için Gemini API key ekleyin: https://makersuite.google.com/app/apikey")

# Telegram Bot Key (opsiyonel - sessiz mod)
TELEGRAM_BOT_TOKEN = load_api_key_from_streamlit_or_env(
    "TELEGRAM_BOT_TOKEN",
    sidebar_label=None,  # Mesaj gösterme
    required=False,
    silent=True  # Opsiyonel key için sessiz mod
)

TELEGRAM_CHAT_ID = load_api_key_from_streamlit_or_env(
    "TELEGRAM_CHAT_ID",
    sidebar_label=None,  # Mesaj gösterme
    required=False,
    silent=True  # Opsiyonel key için sessiz mod
)

# Telegram uyarı ayarları (sidebar'da)
if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    with st.sidebar.expander("🔔 Telegram Uyarıları", expanded=False):
        try:
            from src.notification_engine import get_notification_engine
            
            engine = get_notification_engine()
            
            st.info("💡 Kritik olaylardan anında haberdar olun!")
            
            # Mevcut uyarıları göster
            current_alerts = engine.get_alerts(TELEGRAM_CHAT_ID)
            if current_alerts:
                st.subheader("📋 Mevcut Uyarılar")
                for i, alert in enumerate(current_alerts):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{alert.get('ticker', 'N/A')}** - {alert.get('type', 'N/A')}")
                        if alert.get('threshold'):
                            st.caption(f"Eşik: {alert['threshold']}")
                    with col2:
                        if st.button("🗑️", key=f"remove_alert_{i}"):
                            engine.remove_alert(TELEGRAM_CHAT_ID, alert.get('ticker', ''), i)
                            st.rerun()
            
            # Yeni uyarı ekle
            st.subheader("➕ Yeni Uyarı Ekle")
            alert_ticker = st.text_input("Ticker", placeholder="THYAO", key="alert_ticker")
            alert_type = st.selectbox(
                "Uyarı Tipi",
                ["sentiment", "rsi_oversold", "rsi_overbought", "price_change", "daily_summary"],
                key="alert_type",
                help="sentiment: Sentiment skoru eşik değeri, rsi_oversold: RSI < 30, rsi_overbought: RSI > 70, price_change: Fiyat değişimi, daily_summary: Günlük özet"
            )
            
            threshold = None
            if alert_type in ["sentiment", "price_change"]:
                threshold = st.number_input(
                    "Eşik Değeri",
                    min_value=0.0,
                    max_value=100.0 if alert_type == "sentiment" else 50.0,
                    value=80.0 if alert_type == "sentiment" else 5.0,
                    step=0.1,
                    key="alert_threshold"
                )
            
            if st.button("➕ Uyarı Ekle", key="add_alert"):
                if alert_ticker:
                    engine.add_alert(
                        chat_id=TELEGRAM_CHAT_ID,
                        ticker=alert_ticker.upper(),
                        alert_type=alert_type,
                        threshold=threshold,
                        enabled=True
                    )
                    st.success(f"✅ Uyarı eklendi: {alert_ticker.upper()}")
                    st.rerun()
                else:
                    st.warning("⚠️ Lütfen ticker girin!")
        except ImportError:
            st.warning("⚠️ Notification engine bulunamadı.")
        except Exception as e:
            st.warning(f"⚠️ Telegram uyarı ayarları hatası: {e}")
# Telegram uyarıları için hem token hem chat ID gerekli (sessiz mod - mesaj gösterme)
# elif TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID:
#     st.sidebar.warning("⚠️ Telegram uyarıları için hem Bot Token hem de Chat ID gerekli.")

# Yapılandırma doğrulama (Streamlit başlangıcında)
config_valid = True
config_results = {}
try:
    from src.config_validator import ConfigValidator, validate_config_on_startup
    # Uygulama başlangıcında yapılandırmayı kontrol et
    try:
        result = validate_config_on_startup(raise_on_missing=False)
        
        # Güvenli unpacking (eski versiyon uyumluluğu için)
        if result is None:
            # Fonksiyon None döndürdüyse (beklenmeyen durum)
            config_valid = True
            config_results = {}
        elif isinstance(result, tuple) and len(result) == 2:
            # Yeni versiyon: (bool, dict) tuple döndürüyor
            config_valid, config_results = result
        elif isinstance(result, bool):
            # Eski versiyon: sadece bool döndürüyor
            config_valid = result
            config_results = {}
        elif isinstance(result, dict):
            # Sadece dict döndürüyorsa (beklenmeyen durum)
            config_valid = result.get('valid', True)
            config_results = result
        else:
            # Bilinmeyen tip - güvenli varsayılan
            config_valid = True
            config_results = {}
        
        if not config_valid or (config_results and config_results.get('missing_optional')):
            # Sidebar'da yapılandırma durumunu göster
            try:
                with st.sidebar.expander("⚙️ Yapılandırma Durumu", expanded=False):
                    st.markdown(ConfigValidator.get_config_summary())
            except Exception:
                pass  # Sidebar hatası sessizce atlanır
    except Exception as config_error:
        # Yapılandırma doğrulama hatası (sessizce devam et, uygulama çalışmaya devam etsin)
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Yapılandırma doğrulama hatası: {config_error}")
        logger.debug(traceback.format_exc())
        config_valid = True  # Hata durumunda varsayılan olarak geçerli kabul et
        config_results = {}
except ImportError:
    pass  # Config validator yoksa sessizce devam et
except Exception as e:
    # Genel hata (sessizce devam et)
    pass

# Ana modülleri import et (try-except ile güvenli import)
try:
    from src.main import analyze_company
    from src.prediction_model import train_price_direction_model, PriceDirectionPredictor
    from src.data_collection import get_price_data, get_fundamentals
    # Yeni haber kaynağı modülü (fallback desteği ile)
    try:
        from src.news_sources import get_news_from_all_sources
        USE_MULTI_SOURCE_NEWS = True
    except ImportError:
        from src.data_collection import get_news
        USE_MULTI_SOURCE_NEWS = False
except ImportError as e:
    # Streamlit Cloud için fallback import
    import importlib.util
    import importlib
    
    # src.main
    main_path = project_root / "src" / "main.py"
    if main_path.exists():
        spec = importlib.util.spec_from_file_location("src.main", main_path)
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        analyze_company = main_module.analyze_company
    else:
        raise ImportError(f"src.main modülü bulunamadı: {e}")
    
    # src.prediction_model
    prediction_model_path = project_root / "src" / "prediction_model.py"
    if prediction_model_path.exists():
        spec = importlib.util.spec_from_file_location("src.prediction_model", prediction_model_path)
        prediction_model_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prediction_model_module)
        train_price_direction_model = prediction_model_module.train_price_direction_model
        PriceDirectionPredictor = prediction_model_module.PriceDirectionPredictor
    else:
        raise ImportError(f"src.prediction_model modülü bulunamadı: {e}")
    
    # src.data_collection
    data_collection_path = project_root / "src" / "data_collection.py"
    if data_collection_path.exists():
        spec = importlib.util.spec_from_file_location("src.data_collection", data_collection_path)
        data_collection_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_collection_module)
        get_price_data = data_collection_module.get_price_data
        get_fundamentals = data_collection_module.get_fundamentals
    else:
        raise ImportError(f"src.data_collection modülü bulunamadı: {e}")

import requests

# Streamlit cache decorator'ları - performans için
@st.cache_data(ttl=3600)  # 1 saat cache - yfinance'den günlük fiyat verisi
def cached_analyze_company(company_name: str, ticker: str, days_back: int, 
                          sentiment_weight: float, financial_weight: float):
    """
    Cache'lenmiş analiz fonksiyonu - aynı parametrelerle tekrar çağrıldığında cache'den döner.
    
    @st.cache_data kullanıyoruz çünkü:
    - Sonuçlar DataFrame ve dict gibi serializable veriler
    - TTL (Time To Live) = 3600 saniye (1 saat)
    - Aynı parametrelerle çağrıldığında cache'den döner
    """
    return analyze_company(
        company_name=company_name,
        ticker=ticker,
        days_back=days_back,
        sentiment_weight=sentiment_weight,
        financial_weight=financial_weight
    )

@st.cache_data(ttl=3600)  # 1 saat cache - yfinance'den günlük fiyat verisi
def cached_get_price_data(ticker: str, period: str = "1y"):
    """
    Cache'lenmiş fiyat verisi - aynı ticker için tekrar çekilmez.
    
    @st.cache_data kullanıyoruz çünkü:
    - yfinance'den gelen DataFrame serializable
    - TTL = 3600 saniye (1 saat)
    """
    return get_price_data(ticker, period)

@st.cache_data(ttl=1800)  # 30 dakika cache - haber verisi
def cached_get_news(company_name: str, days_back: int = 30, ticker=None):
    """
    Cache'lenmiş haber verisi çekme - Çoklu kaynak desteği ile.
    
    @st.cache_data kullanıyoruz çünkü:
    - Sonuçlar DataFrame (serializable)
    - TTL (Time To Live) = 1800 saniye (30 dakika)
    - Aynı parametreler için cache'den döner
    
    Yeni: Çoklu haber kaynağı desteği (NewsAPI, Yahoo RSS, FMP, Finnhub)
    """
    # Çoklu kaynak sistemi (fallback desteği ile)
    try:
        from src.news_sources import get_news_from_all_sources
        return get_news_from_all_sources(
            company_name=company_name,
            ticker=ticker,
            days_back=days_back,
            max_articles=50
        )
    except Exception as e:
        # Fallback: Eski sistem (sadece NewsAPI)
        st.warning(f"⚠️ Çoklu haber kaynağı hatası, eski sisteme dönülüyor: {e}")
        from src.data_collection import get_news
        return get_news(company_name, days_back=days_back, api_key=NEWS_API_KEY, ticker=ticker)

@st.cache_resource  # Model yükleme cache'i - uygulama çalıştığı sürece cache'de kalır
def load_predictor_model(model_path: str):
    """
    Cache'lenmiş model yükleme - model dosyası değişmediği sürece tekrar yüklenmez.
    
    @st.cache_resource kullanıyoruz çünkü:
    - Model objesi (PriceDirectionPredictor) non-serializable
    - Uygulama çalıştığı sürece memory'de kalır
    - Model dosyası değişmediği sürece tekrar yüklenmez
    """
    predictor = PriceDirectionPredictor()
    predictor.load_model(model_path)
    return predictor

@st.cache_resource  # FinBERT modeli için cache - ağır model, bir kez yüklenir
def load_sentiment_analyzer():
    """
    Cache'lenmiş sentiment analyzer - FinBERT modeli ağır olduğu için bir kez yüklenir.
    
    @st.cache_resource kullanıyoruz çünkü:
    - Transformer modeli (torch model) non-serializable
    - Model ağır (yüzlerce MB), bir kez yüklenmeli
    - Uygulama çalıştığı sürece memory'de kalır
    """
    from src.sentiment_analysis import SentimentAnalyzer
    return SentimentAnalyzer(use_gemini=bool(GEMINI_API_KEY))

# Sayfa yapılandırması
st.set_page_config(
    page_title="Finansal Analiz ve Haber Sentiment Analizi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Finansal Analiz ve AI Destekli Tahmin Sistemi"
    }
)

# Modern CSS stilleri
st.markdown("""
<style>
    /* Ana stil ayarları */
    .main {
        padding: 2rem 1rem;
    }
    
    /* Modern header */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }
    
    .sub-header {
        text-align: center;
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Modern kartlar */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 0.75rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }
    
    /* Modern butonlar */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 0.75rem;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(102, 126, 234, 0.4);
    }
    
    /* Sidebar stil */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        padding: 1rem;
    }
    
    /* Input alanları */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 0.5rem;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Başlıklar */
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700;
    }
    
    h1 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    h2 {
        font-size: 2rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        font-size: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    /* Info/Error/Success mesajları */
    .stAlert {
        border-radius: 0.75rem;
        border-left: 4px solid;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.5rem 0.5rem 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    /* Metrikler */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #e2e8f0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    
    /* Genel iyileştirmeler */
    .stMarkdown {
        line-height: 1.7;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #667eea transparent transparent transparent;
    }
</style>
""", unsafe_allow_html=True)

# Ana başlık
st.markdown('<h1 class="main-header">📊 Finansal Analiz ve AI Destekli Tahmin</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Yapay zeka destekli finansal analiz ve hisse senedi tahmin platformu</p>', unsafe_allow_html=True)

# Sidebar - Modern Navigasyon
st.sidebar.markdown("""
<div style="padding: 1rem 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 1.5rem;">
    <h2 style="margin: 0; color: #1e293b; font-size: 1.5rem; font-weight: 700;">🎯 Menü</h2>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Sayfa Seçin",
    ["🚀 MVP Tahmin (Sprint 1)", "🏠 Ana Sayfa - Analiz", "📋 İzleme Listesi", "💼 Portföy Optimizasyonu", "📊 Sektörel Analiz", "🔥 Trending Hisseler", "🤖 Model Eğitimi", "📈 Geçmiş Analizler", "ℹ️ Hakkında"],
    label_visibility="collapsed"
)

# MVP Tahmin Sayfası (Sprint 1)
if page == "🚀 MVP Tahmin (Sprint 1)":
    st.title("🚀 MVP Tahmin (Sprint 1)")
    st.markdown("---")
    
    st.info("💡 Bu sayfa Sprint 1 MVP'sini test eder. FastAPI'ye istek atarak tahmin alır.")
    
    # API URL (local için)
    api_url = st.sidebar.text_input(
        "FastAPI URL",
        value="http://127.0.0.1:8000",
        help="FastAPI sunucusunun adresi"
    )
    
    # Hisse kodu input
    ticker = st.text_input(
        "Hisse Kodu",
        value="THYAO",
        help="Örnek: THYAO, AAPL, MSFT"
    )
    
    # Tahmin butonu
    if st.button("🔮 Tahmin Al", type="primary"):
        if not ticker:
            st.error("⚠️ Lütfen bir hisse kodu girin!")
        else:
            with st.spinner(f"📡 {ticker} için tahmin alınıyor..."):
                try:
                    # API'ye istek at (POST /predict, body'de JSON)
                    response = requests.post(
                        f"{api_url}/predict",
                        json={"hisse_kodu": ticker},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Sonuçları göster
                        st.success("✅ Tahmin başarıyla alındı!")
                        
                        # FastAPI response formatını Streamlit formatına dönüştür
                        tahmin_sinyal = result.get('tahmin_sinyal', 'TUT')
                        confidence = result.get('confidence', 0.0)
                        direction = result.get('direction', 'neutral')
                        skor = result.get('skor', 0.0)
                        guven = result.get('guven', 'Düşük')
                        message = result.get('message', '')
                        
                        # Sinyal dönüşümü (AL -> BUY, SAT -> SELL, TUT -> HOLD)
                        signal_map = {'AL': 'BUY', 'SAT': 'SELL', 'TUT': 'HOLD'}
                        signal = signal_map.get(tahmin_sinyal, 'HOLD')
                        
                        # Sinyal renkleri
                        if signal == 'BUY':
                            st.success(f"🟢 **SİNYAL: {signal}** (Güven: {confidence:.1%})")
                        elif signal == 'SELL':
                            st.error(f"🔴 **SİNYAL: {signal}** (Güven: {confidence:.1%})")
                        else:
                            st.warning(f"🟡 **SİNYAL: {signal}** (Güven: {confidence:.1%})")
                        
                        # Detaylar
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Yön", direction.upper() if direction else 'NEUTRAL')
                            st.metric("Güven", f"{confidence:.1%}")
                            st.metric("Güven Seviyesi", guven)
                        with col2:
                            st.metric("Skor", f"{skor:.1f}/100")
                            if message:
                                st.caption(f"ℹ️ {message}")
                        
                        # Olasılıklar varsa göster
                        if 'probabilities' in result and result['probabilities']:
                            with st.expander("📊 Olasılık Dağılımı"):
                                probs = result['probabilities']
                                for key, value in probs.items():
                                    st.progress(value, text=f"{key}: {value:.1%}")
                        
                        # JSON göster
                        with st.expander("📄 Detaylı JSON Sonucu"):
                            st.json(result)
                    else:
                        st.error(f"❌ API hatası: {response.status_code}")
                        # Ham yanıtı göster (JSON değilse)
                        try:
                            error_json = response.json()
                            st.json(error_json)
                        except:
                            # JSON değilse ham metni göster
                            st.code(f"Ham yanıt:\n{response.text[:500]}", language="text")
                            st.warning("💡 FastAPI terminalindeki hata mesajını kontrol edin!")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ FastAPI sunucusuna bağlanılamadı!")
                    st.info("💡 FastAPI'yi başlatmak için terminalde şu komutu çalıştırın:")
                    st.code("cd api && uvicorn main:app --reload", language="bash")
                    st.info("Veya proje kök dizininden:")
                    st.code("uvicorn api.main:app --reload", language="bash")
                except Exception as e:
                    st.error(f"❌ Hata: {e}")
                    import traceback
                    st.code(traceback.format_exc(), language="python")

# Ana Sayfa - Analiz
elif page == "🏠 Ana Sayfa - Analiz":
    st.header("Şirket Analizi")
    
    # İki sütun: Giriş ve Sonuçlar
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Analiz Parametreleri")
        
        # Şirket bilgileri
        company_name = st.text_input(
            "Şirket Adı",
            value="Apple",
            help="Analiz edilecek şirket adı"
        )
        
        ticker = st.text_input(
            "Borsa Kodu (Ticker)",
            value="AAPL",
            help="Örnek: AAPL, MSFT, THYAO.IS"
        )
        
        # Analiz parametreleri
        days_back = st.slider(
            "Haber Analizi Periyodu (Gün)",
            min_value=7,
            max_value=90,
            value=30,
            help="Bugün dahil son X günün haberleri analiz edilir. Anlık haberler otomatik olarak dahil edilir."
        )
        
        sentiment_weight = st.slider(
            "Haber Ağırlığı",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            step=0.1,
            help="Haber sentiment skorunun genel skora katkısı"
        )
        
        financial_weight = st.slider(
            "Finansal Ağırlık",
            min_value=0.0,
            max_value=1.0,
            value=0.6,
            step=0.1,
            help="Finansal skorun genel skora katkısı"
        )
        
        # Normalize et
        total_weight = sentiment_weight + financial_weight
        if total_weight != 1.0:
            st.warning(f"⚠️ Ağırlıklar toplamı 1.0 olmalı. Şu an: {total_weight:.1f}")
            sentiment_weight = sentiment_weight / total_weight if total_weight > 0 else 0.4
            financial_weight = financial_weight / total_weight if total_weight > 0 else 0.6
        
        # Analiz butonu
        analyze_button = st.button("🔍 Analiz Yap", type="primary", width='stretch')
    
    with col2:
        st.subheader("📊 Sonuçlar")
        
        if analyze_button:
            if not company_name or not ticker:
                st.error("❌ Lütfen şirket adı ve borsa kodunu girin!")
            else:
                with st.spinner("🔄 Analiz yapılıyor... Bu birkaç dakika sürebilir."):
                    try:
                        # Analiz yap (cache'lenmiş versiyon)
                        results = cached_analyze_company(
                            company_name=company_name,
                            ticker=ticker,
                            days_back=days_back,
                            sentiment_weight=sentiment_weight,
                            financial_weight=financial_weight
                        )
                        
                        # Sonuçları göster
                        st.success("✅ Analiz tamamlandı!")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Veri alınamadı: API bağlantı hatası")
                        st.info("💡 Lütfen internet bağlantınızı kontrol edin ve birkaç dakika sonra tekrar deneyin.")
                        st.exception(e)
                        results = None
                    except Exception as e:
                        st.error(f"❌ Analiz sırasında hata oluştu")
                        st.info("💡 Lütfen tekrar deneyin. Sorun devam ederse, hata detaylarını kontrol edin.")
                        import traceback
                        with st.expander("🔍 Hata Detayları"):
                            st.code(traceback.format_exc(), language="python")
                        results = None
                    
                    if results is None:
                        st.stop()  # Hata durumunda devam etme
                    
                    # Tabs yapısı - v4 yol haritası gereksinimi
                    try:
                        tab_overview, tab_detailed, tab_news_report, tab_faaliyet_raporu, tab_scenario, tab_competitor, tab_kap_detective, tab_insider, tab_portfolio, tab_time_travel, tab_pdf_chat = st.tabs([
                            "📊 Genel Bakış",
                            "📈 Detaylı Analiz",
                            "📰 Haberler & Rapor",
                            "📄 Faaliyet Raporu",
                            "🎛️ Senaryo Analizi",
                            "⚔️ Rakip Analizi",
                            "🔍 KAP Dedektifi",
                            "👔 Insider Trading",
                            "💼 Portföy",
                            "🕐 Time Travel",
                            "💬 PDF Chat"
                        ])
                        
                        # API key kontrolü ve uyarı - dummy veri kontrolü
                        news_df = results.get('news_df', pd.DataFrame())
                        news_count = results.get('news_count', 0)
                        is_dummy_data = False
                        dummy_count = 0
                        
                        # Dummy veri kontrolü: Eğer haberler varsa ve tüm haberlerin kaynağı "Dummy News" ise
                        if not news_df.empty and 'source' in news_df.columns:
                            unique_sources = news_df['source'].unique()
                            # Dummy News kaynağı sayısını say
                            dummy_count = (news_df['source'] == 'Dummy News').sum()
                            if len(unique_sources) == 1 and 'Dummy News' in unique_sources:
                                is_dummy_data = True
                            elif dummy_count > 0:
                                # Bazı haberler dummy olabilir
                                st.warning(f"⚠️ **Dikkat:** {dummy_count} haber dummy (test) verisi. {len(news_df) - dummy_count} gerçek haber bulundu.")
                        elif news_df.empty and news_count == 0:
                            # Boş DataFrame ve 0 haber sayısı
                            # Eğer API key yoksa, dummy data kullanılmış olabilir
                            # Eğer API key varsa, API'den haber bulunamadı demektir (dummy data değil)
                            if NEWS_API_KEY is None:
                                is_dummy_data = True
                        
                        # Mesajları göster
                        # Önce results'tan gelen uyarıları göster
                        user_warnings = results.get('warnings', [])
                        if user_warnings:
                            for warn in user_warnings:
                                st.warning(warn)
                        
                        # Dummy haber verisi kontrolü
                        if is_dummy_data or results.get('is_dummy_news'):
                            st.warning("⚠️ **Dikkat:** Dummy haber verisi kullanılıyor, skorlar güvenilir değil. NEWS_API_KEY bulunamadı veya API isteği başarısız oldu. Gerçek haberler için NewsAPI key ekleyin ve uygulamayı yeniden başlatın.")
                        elif news_count == 0 and NEWS_API_KEY is not None:
                            # KAP ve Google Search fallback'lerinin kullanıldığını belirt
                            st.warning("⚠️ **Uyarı:** NewsAPI'de seçilen periyotta haber bulunamadı. "
                                     "**Sistem otomatik olarak şunları denedi:**\n"
                                     "• NewsAPI (çoklu arama terimleri ile)\n"
                                     "• Google Search (Türkçe kaynaklara öncelik)\n"
                                     "• KAP raporları (Türk şirketleri için)\n\n"
                                     "**Çözüm önerileri:**\n"
                                     "1. Haber analizi periyodunu artırın (örn: 7 gün yerine 30 gün)\n"
                                     "2. Şirket adını İngilizce olarak deneyin (örn: 'Apple' yerine 'Apple Inc.')\n"
                                     "3. Ticker sembolü kullanın (örn: 'AAPL')\n"
                                     "4. Farklı bir şirket adı deneyin\n"
                                     "5. Türk şirketleri için KAP raporları otomatik kullanılır")
                        elif news_count > 0 and news_count <= 3:
                            st.info("ℹ️ **Bilgi:** Çok az haber bulundu. Bu, seçilen periyotta gerçekten az haber olmasından kaynaklanıyor olabilir. Daha fazla haber için periyodu artırabilirsiniz.")
                        
                        # TAB 1: Genel Bakış
                        with tab_overview:
                            # Siyasi/Ekonomik Risk Göstergesi
                            if 'political_impact_score' in results and results.get('political_impact_score') is not None:
                                political_score = results['political_impact_score']
                                if political_score > 0.5:
                                    st.warning(f"⚠️ **Yüksek Siyasi Etki Tespit Edildi:** {political_score:.1%}")
                                    st.info("💡 Kriz zamanlarında teknik analiz etkisiz olabilir. Siyasi gelişmeleri yakından takip edin.")
                            
                            # Skorlar - Gauge Chart ile
                            col_score1, col_score2, col_score3 = st.columns(3)
                        
                        with col_score1:
                                # Sentiment Skoru - Gauge Chart
                                fig_sentiment_gauge = go.Figure(go.Indicator(
                                    mode="gauge+number+delta",
                                    value=results['sentiment_score'],
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "📰 Sentiment Skoru"},
                                    delta={'reference': 50, 'position': "top"},
                                    gauge={
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': "darkblue"},
                                        'steps': [
                                            {'range': [0, 30], 'color': "lightgray"},
                                            {'range': [30, 70], 'color': "gray"},
                                            {'range': [70, 100], 'color': "lightgreen"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': 90
                                        }
                                    }
                                ))
                                fig_sentiment_gauge.update_layout(height=250)
                                st.plotly_chart(fig_sentiment_gauge, use_container_width=True)
                        
                        with col_score2:
                                # Finansal Skor - Gauge Chart
                                fig_financial_gauge = go.Figure(go.Indicator(
                                    mode="gauge+number+delta",
                                    value=results['financial_score'],
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "💰 Finansal Skor"},
                                    delta={'reference': 50, 'position': "top"},
                                    gauge={
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': "darkgreen"},
                                        'steps': [
                                            {'range': [0, 30], 'color': "lightgray"},
                                            {'range': [30, 70], 'color': "gray"},
                                            {'range': [70, 100], 'color': "lightgreen"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': 90
                                        }
                                    }
                                ))
                                fig_financial_gauge.update_layout(height=250)
                                st.plotly_chart(fig_financial_gauge, use_container_width=True)
                        
                        with col_score3:
                                # Genel Durum Skoru - Gauge Chart
                                score_color = "darkgreen" if results['overall_score'] >= 70 else "darkred" if results['overall_score'] < 30 else "darkorange"
                                fig_overall_gauge = go.Figure(go.Indicator(
                                    mode="gauge+number+delta",
                                    value=results['overall_score'],
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "🎯 Genel Durum Skoru"},
                                    delta={'reference': 50, 'position': "top"},
                                    gauge={
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': score_color},
                                        'steps': [
                                            {'range': [0, 30], 'color': "lightcoral"},
                                            {'range': [30, 70], 'color': "lightyellow"},
                                            {'range': [70, 100], 'color': "lightgreen"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': 90
                                        }
                                    }
                                ))
                                fig_overall_gauge.update_layout(height=250)
                                st.plotly_chart(fig_overall_gauge, use_container_width=True)
                        
                        # Yorum
                        interpretation = results['interpretation']
                        st.info(f"**{interpretation['category']}** - {interpretation['risk_level']}")
                        st.write(interpretation['recommendation'])
                        
                        # Yön tahmini
                        if 'direction_prediction' in results:
                            pred = results['direction_prediction']
                            direction_emoji = {"up": "📈", "down": "📉", "neutral": "➡️"}
                            direction_tr = {"up": "YÜKSELİŞ", "down": "DÜŞÜŞ", "neutral": "NÖTR"}
                            
                            direction = pred.get('direction', 'neutral')
                            
                            col_dir1, col_dir2 = st.columns([3, 1])
                            with col_dir1:
                                st.write(f"**Yön Tahmini:** {direction_emoji.get(direction, '❓')} "
                                           f"{direction_tr.get(direction, 'NÖTR')} "
                                       f"({pred.get('confidence', 0):.1%} güven)")
                            
                            # Şeytanın Avukatı butonu (AL sinyali verildiğinde)
                            if direction in ['up', 'positive'] and pred.get('confidence', 0) > 0.6:
                                with col_dir2:
                                    if st.button("😈 Neden Almamalıyım?", key="devils_advocate_btn", help="AL sinyali verildiğinde riskleri göster"):
                                        st.session_state['show_devils_advocate'] = True
                            
                            # Şeytanın Avukatı analizi göster
                            if st.session_state.get('show_devils_advocate', False):
                                try:
                                    from src.devils_advocate import analyze_why_not_to_buy
                                    import google.generativeai as genai
                                    
                                    if GEMINI_API_KEY:
                                        genai.configure(api_key=GEMINI_API_KEY)
                                        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                                    else:
                                        gemini_model = None
                                    
                                    with st.spinner("😈 Şeytanın Avukatı analizi yapılıyor..."):
                                        devils_analysis = analyze_why_not_to_buy(
                                            ticker=ticker,
                                            company_name=company_name,
                                            analysis_results=results,
                                            gemini_model=gemini_model
                                        )
                                    
                                    if devils_analysis.get('success'):
                                        st.warning(f"**⚠️ {devils_analysis.get('recommendation', 'BEKLE')}**")
                                        st.write(devils_analysis.get('summary', ''))
                                        
                                        st.subheader("🚨 Tespit Edilen Riskler")
                                        for i, risk in enumerate(devils_analysis.get('risks', []), 1):
                                            severity_color = {
                                                'high': '🔴',
                                                'medium': '🟡',
                                                'low': '🟢'
                                            }
                                            st.write(f"{i}. {severity_color.get(risk.get('severity', 'medium'), '⚪')} **{risk.get('title', 'Risk')}**")
                                            st.caption(risk.get('description', ''))
                                            if risk.get('evidence'):
                                                st.caption(f"Kanıt: {risk.get('evidence')}")
                                        
                                        if st.button("❌ Kapat", key="close_devils_advocate"):
                                            st.session_state['show_devils_advocate'] = False
                                            st.rerun()
                                except Exception as e:
                                    st.error(f"Şeytanın Avukatı analizi hatası: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                        
                            # Hızlı fiyat grafiği (AL/SAT sinyalleri ile)
                            if not results['price_df'].empty:
                                price_df = results['price_df']
                                date_col = price_df.index if 'date' not in price_df.columns else price_df['date']
                                
                                fig_quick = go.Figure()
                                fig_quick.add_trace(go.Scatter(
                                    x=date_col,
                                    y=price_df['close'],
                                    mode='lines',
                                    name='Fiyat',
                                    line=dict(color='blue', width=2)
                                ))
                                
                                # AL/SAT sinyalleri ekle (eğer direction_prediction varsa)
                                if 'direction_prediction' in results:
                                    pred = results['direction_prediction']
                                    direction = pred.get('direction', 'neutral')
                                    
                                    # Son 10 gün için sinyal göster (örnek)
                                    if len(price_df) >= 10:
                                        # Son gün için sinyal
                                        last_date = date_col.iloc[-1] if hasattr(date_col, 'iloc') else date_col[-1]
                                        last_price = price_df['close'].iloc[-1] if hasattr(price_df['close'], 'iloc') else price_df['close'].values[-1]
                                        
                                        # Sinyal yönüne göre renk ve sembol
                                        if direction == 'up' or direction == 'positive':
                                            fig_quick.add_trace(go.Scatter(
                                                x=[last_date],
                                                y=[last_price],
                                                mode='markers+text',
                                                name='AL Sinyali',
                                                marker=dict(
                                                    symbol='triangle-up',
                                                    size=20,
                                                    color='green',
                                                    line=dict(width=2, color='darkgreen')
                                                ),
                                                text=['🟢 AL'],
                                                textposition='top center',
                                                textfont=dict(size=14, color='green', family='Arial Black')
                                            ))
                                        elif direction == 'down' or direction == 'negative':
                                            fig_quick.add_trace(go.Scatter(
                                                x=[last_date],
                                                y=[last_price],
                                                mode='markers+text',
                                                name='SAT Sinyali',
                                                marker=dict(
                                                    symbol='triangle-down',
                                                    size=20,
                                                    color='red',
                                                    line=dict(width=2, color='darkred')
                                                ),
                                                text=['🔴 SAT'],
                                                textposition='bottom center',
                                                textfont=dict(size=14, color='red', family='Arial Black')
                                            ))
                                
                                fig_quick.update_layout(
                                    title=f'{company_name} ({ticker}) - Fiyat Hareketi',
                                    xaxis_title='Tarih',
                                    yaxis_title='Fiyat',
                                    height=400,
                                    showlegend=True
                                )
                                st.plotly_chart(fig_quick, width='stretch')
                        
                        # TAB 2: Detaylı Analiz
                        with tab_detailed:
                            st.subheader("📈 Detaylı Analiz")
                            
                            # SHAP açıklaması (eğer model varsa)
                            model_path = f"models/price_predictor_{ticker.lower().replace('.', '_')}.pkl"
                            if os.path.exists(model_path):
                                try:
                                    from src.prediction_model import PriceDirectionPredictor
                                    from src.explainability import format_explanation_for_display
                                    
                                    predictor = load_predictor_model(model_path)
                                    feature_vector = results.get('feature_vector', {})
                                    
                                    if feature_vector:
                                        shap_result = predictor.explain_prediction_shap(feature_vector)
                                        
                                        st.subheader("🔍 Model Açıklaması (SHAP)")
                                        explanation_text = format_explanation_for_display(shap_result, pred if 'direction_prediction' in results else {})
                                        st.markdown(explanation_text)
                                        
                                        # SHAP değerleri grafiği
                                        if shap_result.get('top_features'):
                                            shap_df = pd.DataFrame(
                                                shap_result['top_features'][:10],
                                                columns=['Feature', 'SHAP Değeri']
                                            )
                                            
                                            fig_shap = go.Figure(data=[go.Bar(
                                                x=shap_df['SHAP Değeri'],
                                                y=shap_df['Feature'],
                                                orientation='h',
                                                marker=dict(
                                                    color=shap_df['SHAP Değeri'],
                                                    colorscale='RdYlGn',
                                                    showscale=True
                                                ),
                                                text=[f"{v:.4f}" for v in shap_df['SHAP Değeri']],
                                                textposition='auto'
                                            )])
                                            
                                            fig_shap.update_layout(
                                                title='En Önemli Feature\'lar (SHAP Değerleri)',
                                                xaxis_title='SHAP Değeri (Etki)',
                                                yaxis_title='Feature',
                                                height=400
                                            )
                                            
                                            st.plotly_chart(fig_shap, width='stretch')
                                
                                except Exception as e:
                                    st.info(f"ℹ️ Model açıklaması gösterilemedi: {str(e)}")
                            
                        # Detaylı rapor
                            if 'detailed_report' in results and results['detailed_report']:
                                detailed_report = results['detailed_report']
                                
                                st.subheader("📋 Detaylı Analiz Raporu")
                                st.markdown(detailed_report['summary'])
                                
                                # Finansal faktörler
                                if detailed_report.get('financial_analysis'):
                                    st.subheader("💰 Finansal Göstergeler")
                                    for factor in detailed_report['financial_analysis']:
                                        col1, col2, col3 = st.columns([2, 1, 3])
                                        with col1:
                                            st.write(f"**{factor['factor']}**")
                                        with col2:
                                            st.write(f"`{factor['value']}`")
                                        with col3:
                                            st.write(f"{factor['status']} - {factor['impact']}")
                                
                                # Öneri nedenleri
                                if detailed_report.get('recommendation_reasons'):
                                    st.subheader("💡 Al/Sat Önerisi Nedenleri")
                                    for reason in detailed_report['recommendation_reasons']:
                                        emoji = "✅" if reason['impact'] == 'Pozitif' else "❌" if reason['impact'] == 'Negatif' else "⚠️"
                                        st.write(f"{emoji} **{reason['type']}:** {reason['reason']}")
                                
                                # En önemli faktörler
                                if detailed_report.get('key_factors'):
                                    st.subheader("🔑 En Önemli Faktörler")
                                    for i, factor in enumerate(detailed_report['key_factors'][:5], 1):
                                        st.write(f"{i}. **{factor['type']}:** {factor['description']}")
                            
                            # Grafikler - Tabs ile organize edilmiş
                        st.subheader("📈 Görselleştirmeler")
                        
                        if not results['price_df'].empty:
                            price_df = results['price_df']
                            
                            # Tab'lar oluştur
                            tab1, tab2, tab3, tab4 = st.tabs(["📊 Fiyat Grafiği", "🕯️ Candlestick", "📈 Teknik Göstergeler", "📰 Haber Analizi"])
                            
                            with tab1:
                                # Gelişmiş fiyat grafiği
                                fig = make_subplots(
                                    rows=3, cols=1,
                                    subplot_titles=('Fiyat Hareketi', 'Hacim', 'RSI (14)'),
                                    vertical_spacing=0.08,
                                    row_heights=[0.5, 0.25, 0.25],
                                    shared_xaxes=True
                                )
                            
                                # Fiyat çizgisi
                                fig.add_trace(
                                    go.Scatter(
                                        x=price_df.index if 'date' not in price_df.columns else price_df['date'],
                                        y=price_df['close'],
                                        mode='lines',
                                        name='Kapanış Fiyatı',
                                        line=dict(color='#1f77b4', width=2),
                                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                                      'Tarih: %{x}<br>' +
                                                      'Fiyat: $%{y:.2f}<br>' +
                                                      '<extra></extra>'
                                    ),
                                    row=1, col=1
                                )
                            
                                # Hareketli ortalamalar
                                if 'ma_20' in price_df.columns:
                                    fig.add_trace(
                                        go.Scatter(
                                            x=price_df.index if 'date' not in price_df.columns else price_df['date'],
                                            y=price_df['ma_20'],
                                            mode='lines',
                                            name='MA 20',
                                            line=dict(color='orange', width=1.5, dash='dash'),
                                            hovertemplate='<b>MA 20</b><br>Fiyat: $%{y:.2f}<extra></extra>'
                                        ),
                                        row=1, col=1
                                    )
                                
                                if 'ma_50' in price_df.columns:
                                    fig.add_trace(
                                        go.Scatter(
                                                x=price_df.index if 'date' not in price_df.columns else price_df['date'],
                                                y=price_df['ma_50'],
                                                mode='lines',
                                                name='MA 50',
                                                line=dict(color='purple', width=1.5, dash='dot'),
                                                hovertemplate='<b>MA 50</b><br>Fiyat: $%{y:.2f}<extra></extra>'
                                    ),
                                    row=1, col=1
                                )
                            
                                # Hacim
                                fig.add_trace(
                                    go.Bar(
                                        x=price_df.index if 'date' not in price_df.columns else price_df['date'],
                                        y=price_df['volume'],
                                        name='Hacim',
                                        marker_color='lightblue',
                                        hovertemplate='<b>Hacim</b><br>%{y:,.0f}<extra></extra>'
                                    ),
                                    row=2, col=1
                                )
                                
                                # RSI
                                if 'rsi_14' in price_df.columns:
                                    fig.add_trace(
                                        go.Scatter(
                                            x=price_df.index if 'date' not in price_df.columns else price_df['date'],
                                            y=price_df['rsi_14'],
                                            mode='lines',
                                            name='RSI (14)',
                                            line=dict(color='red', width=2),
                                            hovertemplate='<b>RSI</b><br>%{y:.2f}<extra></extra>'
                                        ),
                                        row=3, col=1
                                    )
                                    
                                    # RSI seviyeleri (70 ve 30)
                                    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
                                    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
                                
                                fig.update_layout(
                                    title=f'{company_name} ({ticker}) - Detaylı Fiyat Analizi',
                                    height=800,
                                    showlegend=True,
                                    hovermode='x unified',
                                    xaxis_rangeslider_visible=False
                                )
                                
                                fig.update_xaxes(title_text="Tarih", row=3, col=1)
                                fig.update_yaxes(title_text="Fiyat ($)", row=1, col=1)
                                fig.update_yaxes(title_text="Hacim", row=2, col=1)
                                fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
                                
                                st.plotly_chart(fig, width='stretch', config={
                                        'displayModeBar': True,
                                        'modeBarButtonsToAdd': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'resetScale2d']
                                    })
                                
                                with tab2:
                                    # Candlestick grafiği
                                    if all(col in price_df.columns for col in ['open', 'high', 'low', 'close']):
                                        fig_candle = go.Figure(data=[go.Candlestick(
                                            x=price_df.index if 'date' not in price_df.columns else price_df['date'],
                                            open=price_df['open'],
                                            high=price_df['high'],
                                            low=price_df['low'],
                                            close=price_df['close'],
                                            name='Fiyat',
                                            increasing_line_color='green',
                                            decreasing_line_color='red'
                                        )])
                                        
                                        # Hareketli ortalamalar ekle
                                        if 'ma_20' in price_df.columns:
                                            fig_candle.add_trace(
                                                go.Scatter(
                                                    x=price_df.index if 'date' not in price_df.columns else price_df['date'],
                                                    y=price_df['ma_20'],
                                                    mode='lines',
                                                    name='MA 20',
                                                    line=dict(color='orange', width=1.5)
                                                )
                                            )
                                        
                                        fig_candle.update_layout(
                                            title=f'{company_name} ({ticker}) - Candlestick Grafiği',
                                            height=600,
                                            xaxis_rangeslider_visible=True,
                                            xaxis_rangeslider_thickness=0.05,
                                            hovermode='x unified'
                                        )
                                        
                                        fig_candle.update_xaxes(title_text="Tarih")
                                        fig_candle.update_yaxes(title_text="Fiyat ($)")
                                        
                                        st.plotly_chart(fig_candle, width='stretch', config={
                                            'displayModeBar': True,
                                            'modeBarButtonsToAdd': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'resetScale2d']
                                        })
                                    else:
                                        st.info("Candlestick grafiği için OHLC verisi gerekli.")
                                
                                with tab3:
                                    # Teknik göstergeler
                                    tech_fig = make_subplots(
                                        rows=2, cols=2,
                                        subplot_titles=('MACD', 'RSI', 'Bollinger Bands', 'Volatilite'),
                                        specs=[[{"secondary_y": False}, {"secondary_y": False}],
                                               [{"secondary_y": False}, {"secondary_y": False}]]
                                    )
                                    
                                    date_col = price_df.index if 'date' not in price_df.columns else price_df['date']
                                    
                                    # MACD
                                    if all(col in price_df.columns for col in ['macd', 'macd_signal']):
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['macd'], name='MACD', line=dict(color='blue')),
                                            row=1, col=1
                                        )
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['macd_signal'], name='Signal', line=dict(color='red')),
                                            row=1, col=1
                                        )
                                        if 'macd_hist' in price_df.columns:
                                            tech_fig.add_trace(
                                                go.Bar(x=date_col, y=price_df['macd_hist'], name='Histogram', marker_color='gray'),
                                                row=1, col=1
                                            )
                                    
                                    # RSI
                                    if 'rsi_14' in price_df.columns:
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['rsi_14'], name='RSI', line=dict(color='purple')),
                                            row=1, col=2
                                        )
                                        tech_fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=1, col=2)
                                        tech_fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=1, col=2)
                                    
                                    # Bollinger Bands
                                    if all(col in price_df.columns for col in ['bb_upper', 'bb_lower', 'bb_middle']):
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dash')),
                                            row=2, col=1
                                        )
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dash'), fill='tonexty'),
                                            row=2, col=1
                                        )
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['bb_middle'], name='BB Middle', line=dict(color='blue')),
                                            row=2, col=1
                                        )
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['close'], name='Fiyat', line=dict(color='black')),
                                            row=2, col=1
                                        )
                                    
                                    # Volatilite
                                    if 'volatility_30d' in price_df.columns:
                                        tech_fig.add_trace(
                                            go.Scatter(x=date_col, y=price_df['volatility_30d'], name='Volatilite', line=dict(color='orange'), fill='tozeroy'),
                                            row=2, col=2
                                        )
                                    
                                    tech_fig.update_layout(
                                        title='Teknik Göstergeler',
                                        height=700,
                                        showlegend=True,
                                        hovermode='x unified'
                                    )
                                    
                                    st.plotly_chart(tech_fig, width='stretch', config={
                                        'displayModeBar': True,
                                        'modeBarButtonsToAdd': ['pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'resetScale2d']
                                    })
                                
                                with tab4:
                                    # Haber analizi grafikleri
                                    if not results['news_df'].empty and 'sentiment_class' in results['news_df'].columns:
                                        news_df = results['news_df']
                                        
                                        col_news1, col_news2 = st.columns(2)
                                        
                                        with col_news1:
                                            # Sentiment dağılımı
                                            sentiment_counts = news_df['sentiment_class'].value_counts()
                                            
                                            fig_sentiment = go.Figure(data=[go.Bar(
                                                x=sentiment_counts.index,
                                                y=sentiment_counts.values,
                                                marker_color=['green', 'red', 'gray'],
                                                text=sentiment_counts.values,
                                                textposition='auto',
                                                hovertemplate='<b>%{x}</b><br>Haber Sayısı: %{y}<extra></extra>'
                                            )])
                                            
                                            fig_sentiment.update_layout(
                                                title='Haber Sentiment Dağılımı',
                                                xaxis_title='Sentiment Sınıfı',
                                                yaxis_title='Haber Sayısı',
                                height=300
                            )
                            
                                            st.plotly_chart(fig_sentiment, width='stretch')
                                        
                                        with col_news2:
                                            # Sentiment zaman serisi
                                            if 'published_at' in news_df.columns:
                                                news_df_time = news_df.copy()
                                                news_df_time['date'] = pd.to_datetime(news_df_time['published_at']).dt.date
                                                sentiment_timeseries = news_df_time.groupby(['date', 'sentiment_class']).size().unstack(fill_value=0)
                                                
                                                fig_timeseries = go.Figure()
                                                colors = {'positive': 'green', 'negative': 'red', 'neutral': 'gray'}
                                                for sentiment in sentiment_timeseries.columns:
                                                    fig_timeseries.add_trace(go.Scatter(
                                                        x=sentiment_timeseries.index,
                                                        y=sentiment_timeseries[sentiment],
                                                        mode='lines+markers',
                                                        name=sentiment,
                                                        line=dict(color=colors.get(sentiment, 'blue')),
                                                        hovertemplate=f'<b>{sentiment}</b><br>%{{y}} haber<extra></extra>'
                                                    ))
                                                
                                                fig_timeseries.update_layout(
                                                    title='Sentiment Zaman Serisi',
                                                    xaxis_title='Tarih',
                                                    yaxis_title='Haber Sayısı',
                                                    height=300,
                                                    hovermode='x unified'
                                                )
                                                
                                                st.plotly_chart(fig_timeseries, width='stretch')
                                        
                                        # Confidence dağılımı
                                        if 'sentiment_confidence' in news_df.columns:
                                            fig_confidence = go.Figure(data=[go.Histogram(
                                                x=news_df['sentiment_confidence'],
                                                nbinsx=20,
                                                marker_color='lightblue',
                                                hovertemplate='<b>Güven Aralığı</b><br>%{x:.2f}<br>Haber Sayısı: %{y}<extra></extra>'
                                            )])
                                            
                                            fig_confidence.update_layout(
                                                title='Sentiment Güven Dağılımı',
                                                xaxis_title='Güven Skoru',
                                                yaxis_title='Haber Sayısı',
                                                height=300
                                            )
                                            
                                            st.plotly_chart(fig_confidence, width='stretch')
                                    else:
                                        st.info("Haber analizi için veri bulunamadı.")
                        
                        # TAB 3: Haberler & Rapor
                        with tab_news_report:
                            st.subheader("📰 Haberler & AI Raporu")
                            
                            # Geçmiş Benzer Olaylar (RAG Mimarisi)
                            try:
                                from src.vector_memory import HistoricalMemory
                                
                                memory = HistoricalMemory()
                                if memory.available and not news_df.empty:
                                    with st.expander("🧠 Geçmiş Benzer Olaylar (Tarihsel Hafıza)", expanded=False):
                                        st.info("💡 Bu bölüm, mevcut haberleri geçmişteki benzer olaylarla karşılaştırarak piyasa tepkisini öngörmeye çalışır.")
                                        
                                        # En son haberleri analiz et
                                        if 'title' in news_df.columns and 'summary' in news_df.columns:
                                            latest_news = news_df.iloc[0] if len(news_df) > 0 else None
                                            
                                            if latest_news is not None:
                                                current_title = latest_news.get('title', '')
                                                current_summary = latest_news.get('summary', '')
                                                
                                                if current_title or current_summary:
                                                    similar_events = memory.find_similar_events(
                                                        current_news=current_summary,
                                                        current_title=current_title,
                                                        top_k=5
                                                    )
                                                    
                                                    if similar_events:
                                                        st.subheader("📅 Benzer Geçmiş Olaylar")
                                                        
                                                        # Ortalama BIST100 değişimi
                                                        avg_change = sum(e['bist100_change'] for e in similar_events) / len(similar_events)
                                                        max_change = max(similar_events, key=lambda x: abs(x['bist100_change']))
                                                        
                                                        col1, col2, col3 = st.columns(3)
                                                        with col1:
                                                            st.metric("Ortalama BIST100 Değişimi", f"{avg_change:+.2f}%")
                                                        with col2:
                                                            st.metric("En Yüksek Etki", f"{max_change['bist100_change']:+.2f}%")
                                                        with col3:
                                                            st.metric("Benzer Olay Sayısı", len(similar_events))
                                                        
                                                        st.write("**Geçmiş Olaylar:**")
                                                        for i, event in enumerate(similar_events, 1):
                                                            change_color = "🟢" if event['bist100_change'] > 0 else "🔴" if event['bist100_change'] < 0 else "🟡"
                                                            st.write(f"""
{change_color} **{i}. {event['date']}** - {event['title'][:80]}...
- **BIST100 Değişimi:** {event['bist100_change']:+.2f}%
- **Benzerlik:** {event['similarity']:.1%}
- **Kategori:** {event['category']}
""")
                                                        
                                                        # Gemini bağlam metni
                                                        context = memory.get_historical_context(
                                                            current_news=current_summary,
                                                            current_title=current_title,
                                                            top_k=5
                                                        )
                                                        
                                                        if context:
                                                            with st.expander("🤖 AI Yorumu (Geçmiş Olaylara Dayalı)", expanded=False):
                                                                st.code(context, language="text")
                                                    else:
                                                        st.info("ℹ️ Benzer geçmiş olay bulunamadı. Veritabanı henüz yeterince dolu olmayabilir.")
                                                        st.info("💡 Geçmiş verileri yüklemek için: `src/vector_memory.py` dosyasındaki `populate_historical_data()` fonksiyonunu çalıştırın.")
                            except ImportError:
                                pass  # Vector memory modülü yoksa sessizce devam et
                            except Exception as e:
                                st.warning(f"⚠️ Tarihsel hafıza hatası: {str(e)}")
                            
                            # Gemini AI Analist Raporu (eğer varsa)
                            if 'detailed_report' in results and results['detailed_report']:
                                detailed_report = results['detailed_report']
                                
                                if detailed_report.get('gemini_analyst_report'):
                                    st.subheader("🤖 AI Analist Raporu (Gemini)")
                                    st.info("💡 Bu rapor, Gemini AI tarafından otomatik olarak oluşturulmuştur.")
                                    st.markdown(detailed_report['gemini_analyst_report'])
                                    
                                    # Haber özetleri
                                    if detailed_report.get('hisse_news_summary'):
                                        with st.expander("📰 Hisse Bazlı Haber Özeti", expanded=True):
                                            st.markdown(detailed_report['hisse_news_summary'])
                                    
                                    if detailed_report.get('piyasa_news_summary'):
                                        with st.expander("🌐 Piyasa Geneli Haber Özeti", expanded=True):
                                            st.markdown(detailed_report['piyasa_news_summary'])
                                
                                # En önemli haberler
                                if detailed_report.get('news_analysis'):
                                    st.subheader("📰 En Etkili Haberler")
                                    for news in detailed_report['news_analysis'][:10]:
                                        with st.container():
                                            col1, col2 = st.columns([1, 4])
                                            with col1:
                                                st.write(f"{news.get('sentiment_emoji', '🟡')} **{news.get('sentiment', 'neutral').upper()}**")
                                                st.caption(f"Etki: {news.get('impact', 'Orta')}")
                                                st.caption(f"Güven: {news.get('confidence', 0.0):.1%}")
                                            with col2:
                                                st.write(f"**{news.get('title', 'Başlık yok')}**")
                                                st.caption(f"📅 {news.get('date', 'Bilinmiyor')}")
                                            st.divider()
                            
                            # Haber listesi
                            if not results['news_df'].empty:
                                st.subheader("📋 Tüm Haberler")
                                # Sentiment filtreleme
                                sentiment_filter = st.selectbox(
                                    "Sentiment Filtresi",
                                    ["Tümü", "Pozitif", "Negatif", "Nötr"],
                                    key="news_sentiment_filter"
                                )
                                
                                filtered_news = results['news_df'].copy()
                                if sentiment_filter != "Tümü":
                                    sentiment_map = {"Pozitif": "positive", "Negatif": "negative", "Nötr": "neutral"}
                                    if 'sentiment' in filtered_news.columns:
                                        filtered_news = filtered_news[filtered_news['sentiment'] == sentiment_map[sentiment_filter]]
                                
                                for idx, row in filtered_news.head(20).iterrows():
                                    with st.expander(f"{row.get('sentiment_emoji', '🟡')} {row.get('title', 'Başlık yok')}", expanded=False):
                                        st.write(f"**Özet:** {row.get('summary', 'Özet yok')}")
                                        st.write(f"**Kaynak:** {row.get('source', 'Bilinmiyor')}")
                                        st.write(f"**Tarih:** {row.get('published_at', 'Bilinmiyor')}")
                                        if row.get('url'):
                                            st.markdown(f"[🔗 Haberi Oku]({row['url']})")
                                        sentiment_val = row.get('sentiment', 'neutral')
                                        confidence_val = row.get('confidence', 0.0)
                                        st.write(f"**Sentiment:** {sentiment_val.upper()} ({confidence_val:.1%} güven)")
                        
                        # TAB 4: Faaliyet Raporu Analizi
                        with tab_faaliyet_raporu:
                            st.subheader("📄 Faaliyet Raporu Analizi")
                            st.info("💡 KAP'tan indirilen faaliyet raporlarını otomatik analiz eder ve riskleri tespit eder.")
                            
                            try:
                                from src.pdf_parser import PDFParser
                                from src.kap_scraper import get_kap_financial_reports
                                
                                parser = PDFParser()
                                
                                if parser.available:
                                    # Türk hissesi kontrolü
                                    is_turkish_stock = ticker.endswith('.IS') or (len(ticker) == 5 and ticker.isalpha() and ticker.isupper())
                                    
                                    if is_turkish_stock:
                                        ticker_clean = ticker.replace('.IS', '')
                                        
                                        # KAP raporlarını çek
                                        st.write("**📥 KAP Raporları Çekiliyor...**")
                                        kap_reports = get_kap_financial_reports(ticker_clean, limit=5)
                                        
                                        if kap_reports:
                                            st.success(f"✅ {len(kap_reports)} KAP raporu bulundu.")
                                            
                                            # En son faaliyet raporunu analiz et
                                            for report in kap_reports[:1]:  # İlk raporu analiz et
                                                if 'link' in report and report['link']:
                                                    st.write(f"**📄 Analiz Edilen Rapor:** {report.get('title', 'Bilinmiyor')}")
                                                    
                                                    with st.spinner("PDF analiz ediliyor..."):
                                                        pdf_result = parser.parse_kap_pdf(
                                                            kap_url=report['link'],
                                                            report_title=report.get('title', '')
                                                        )
                                                        
                                                        if pdf_result['success']:
                                                            analysis = pdf_result.get('analysis', {})
                                                            
                                                            # Özet
                                                            if analysis.get('summary'):
                                                                st.subheader("📋 Rapor Özeti")
                                                                st.write(analysis['summary'])
                                                            
                                                            # Riskler
                                                            if analysis.get('risks'):
                                                                st.subheader("⚠️ Önemli Riskler")
                                                                for i, risk in enumerate(analysis['risks'], 1):
                                                                    st.write(f"{i}. {risk}")
                                                            
                                                            # Fırsatlar
                                                            if analysis.get('opportunities'):
                                                                st.subheader("💡 Fırsatlar")
                                                                for i, opp in enumerate(analysis['opportunities'], 1):
                                                                    st.write(f"{i}. {opp}")
                                                            
                                                            # Önemli Metrikler
                                                            if analysis.get('key_metrics'):
                                                                st.subheader("📊 Önemli Metrikler")
                                                                metrics = analysis['key_metrics']
                                                                for key, value in metrics.items():
                                                                    if value:
                                                                        st.write(f"- **{key}:** {value}")
                                                            
                                                            # Yönetim Görünümü
                                                            if analysis.get('management_outlook'):
                                                                st.subheader("👔 Yönetim Görünümü")
                                                                st.write(analysis['management_outlook'])
                                                        else:
                                                            st.warning(f"⚠️ PDF analiz edilemedi: {pdf_result.get('error', 'Bilinmeyen hata')}")
                                        else:
                                            st.info("ℹ️ KAP'tan rapor bulunamadı. Bu hisse için henüz faaliyet raporu yayınlanmamış olabilir.")
                                    else:
                                        st.info("ℹ️ Faaliyet raporu analizi şu an sadece Türk hisseleri için mevcuttur.")
                            except ImportError:
                                st.warning("⚠️ PDF parser modülü bulunamadı.")
                            except Exception as e:
                                st.error(f"❌ Faaliyet raporu analizi hatası: {str(e)}")
                                st.exception(e)
                        
                        # TAB 5: Senaryo Analizi (What-If)
                        with tab_scenario:
                            st.subheader("🎛️ Senaryo Analizi (What-If)")
                            st.info("💡 Farklı makroekonomik senaryoların hisse fiyatına etkisini simüle edin.")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**📊 Makroekonomik Parametreler**")
                                
                                # Faiz oranı değişimi
                                interest_change = st.slider(
                                    "Faiz Oranı Değişimi (%)",
                                    min_value=-5.0,
                                    max_value=5.0,
                                    value=0.0,
                                    step=0.25,
                                    help="Faiz oranının kaç puan değişeceğini belirtin"
                                )
                                
                                # Dolar/TL değişimi
                                usd_change = st.slider(
                                    "USD/TRY Değişimi (%)",
                                    min_value=-20.0,
                                    max_value=20.0,
                                    value=0.0,
                                    step=1.0,
                                    help="Dolar/TL kurunun yüzde değişimini belirtin"
                                )
                                
                                # Enflasyon değişimi
                                inflation_change = st.slider(
                                    "Enflasyon Değişimi (%)",
                                    min_value=-5.0,
                                    max_value=5.0,
                                    value=0.0,
                                    step=0.25,
                                    help="Enflasyon oranının yüzde değişimini belirtin"
                                )
                            
                            with col2:
                                st.write("**📈 Senaryo Sonuçları**")
                                
                                # Mevcut fiyat
                                if not results['price_df'].empty:
                                    current_price = results['price_df'].iloc[-1]['close']
                                    
                                    # Basit korelasyon bazlı tahmin
                                    is_turkish_stock = ticker.endswith('.IS') or (len(ticker) == 5 and ticker.isalpha() and ticker.isupper())
                                    
                                    if is_turkish_stock:
                                        usd_impact = usd_change * 0.5
                                    else:
                                        usd_impact = -usd_change * 0.3
                                    
                                    interest_impact = -interest_change * 2.0
                                    inflation_impact = -inflation_change * 0.5
                                    
                                    total_impact = usd_impact + interest_impact + inflation_impact
                                    predicted_price = current_price * (1 + total_impact / 100)
                                    
                                    st.metric("Mevcut Fiyat", f"₺{current_price:.2f}" if is_turkish_stock else f"${current_price:.2f}")
                                    st.metric("Tahmini Fiyat", f"₺{predicted_price:.2f}" if is_turkish_stock else f"${predicted_price:.2f}", 
                                             delta=f"{total_impact:+.2f}%")
                                    
                                    with st.expander("📊 Etki Detayları", expanded=True):
                                        st.write(f"""
**USD/TRY Etkisi:** {usd_impact:+.2f}%
- Dolar {usd_change:+.1f}% değişirse → Hisse {usd_impact:+.2f}% etkilenir

**Faiz Etkisi:** {interest_impact:+.2f}%
- Faiz {interest_change:+.1f} puan değişirse → Hisse {interest_impact:+.2f}% etkilenir

**Enflasyon Etkisi:** {inflation_impact:+.2f}%
- Enflasyon {inflation_change:+.1f}% değişirse → Hisse {inflation_impact:+.2f}% etkilenir

**Toplam Etki:** {total_impact:+.2f}%
""")
                                        
                                        if abs(total_impact) > 10:
                                            st.warning("⚠️ **Yüksek Etki:** Bu senaryo hisse fiyatını önemli ölçüde etkileyebilir.")
                                        
                                        st.info("💡 **Not:** Bu tahminler basit korelasyon modellerine dayanmaktadır. Gerçek piyasa koşulları daha karmaşık olabilir.")
                                    
                                    fig_scenario = go.Figure()
                                    fig_scenario.add_trace(go.Bar(
                                        x=['USD/TRY', 'Faiz', 'Enflasyon', 'Toplam'],
                                        y=[usd_impact, interest_impact, inflation_impact, total_impact],
                                        marker_color=['blue', 'red', 'orange', 'green' if total_impact > 0 else 'red'],
                                        text=[f"{x:+.2f}%" for x in [usd_impact, interest_impact, inflation_impact, total_impact]],
                                        textposition='auto'
                                    ))
                                    fig_scenario.update_layout(
                                        title='Senaryo Etkisi (%)',
                                        yaxis_title='Fiyat Değişimi (%)',
                                        height=400
                                    )
                                    st.plotly_chart(fig_scenario, use_container_width=True)
                                else:
                                    st.warning("⚠️ Fiyat verisi bulunamadı. Senaryo analizi yapılamıyor.")
                        
                        # TAB 6: Rakip Analizi
                        with tab_competitor:
                            st.subheader("⚔️ Rakip Analizi")
                            st.info("💡 Seçilen hissenin en büyük rakibiyle head-to-head karşılaştırma.")
                            
                            try:
                                from src.competitor_analysis import find_competitor, compare_companies
                                
                                competitor_ticker = find_competitor(ticker)
                                
                                if competitor_ticker:
                                    st.success(f"✅ Rakip bulundu: **{competitor_ticker}**")
                                    
                                    if st.button("🔄 Rakip Analizini Çalıştır", key="run_competitor_analysis"):
                                        with st.spinner("Rakip analizi yapılıyor..."):
                                            try:
                                                competitor_name = competitor_ticker
                                                
                                                comparison = compare_companies(
                                                    ticker1=ticker,
                                                    ticker2=competitor_ticker,
                                                    company_name1=company_name,
                                                    company_name2=competitor_name,
                                                    analysis_results1=results,
                                                    analysis_results2=None
                                                )
                                                
                                                if comparison.get('success'):
                                                    col1, col2 = st.columns(2)
                                                    
                                                    with col1:
                                                        st.subheader(f"🏢 {company_name} ({ticker})")
                                                        st.metric("Genel Skor", f"{comparison['company1']['overall_score']:.1f}/100")
                                                        st.metric("Sentiment", f"{comparison['company1']['sentiment_score']:.1f}/100")
                                                        st.metric("Finansal", f"{comparison['company1']['financial_score']:.1f}/100")
                                                        st.write(f"**Yön:** {comparison['company1']['direction']} ({comparison['company1']['confidence']:.1%})")
                                                        if 'current_price' in comparison['company1']:
                                                            st.metric("Fiyat", f"₺{comparison['company1']['current_price']:.2f}", 
                                                                     delta=f"{comparison['company1'].get('price_change_1mo', 0):+.2f}%")
                                                    
                                                    with col2:
                                                        st.subheader(f"🏢 {competitor_name} ({competitor_ticker})")
                                                        st.metric("Genel Skor", f"{comparison['company2']['overall_score']:.1f}/100")
                                                        st.metric("Sentiment", f"{comparison['company2']['sentiment_score']:.1f}/100")
                                                        st.metric("Finansal", f"{comparison['company2']['financial_score']:.1f}/100")
                                                        st.write(f"**Yön:** {comparison['company2']['direction']} ({comparison['company2']['confidence']:.1%})")
                                                        if 'current_price' in comparison['company2']:
                                                            st.metric("Fiyat", f"₺{comparison['company2']['current_price']:.2f}", 
                                                                     delta=f"{comparison['company2'].get('price_change_1mo', 0):+.2f}%")
                                                    
                                                    st.divider()
                                                    
                                                    if comparison['winner'] == ticker:
                                                        st.success(f"🏆 **Kazanan:** {company_name} ({ticker})")
                                                    elif comparison['winner'] == competitor_ticker:
                                                        st.warning(f"🏆 **Kazanan:** {competitor_name} ({competitor_ticker})")
                                                    else:
                                                        st.info("🤝 **Berabere:** İki şirket de benzer skorlara sahip")
                                                    
                                                    st.write(comparison.get('comparison_summary', ''))
                                                else:
                                                    st.error(f"❌ Rakip analizi başarısız: {comparison.get('error', 'Bilinmeyen hata')}")
                                            except Exception as e:
                                                st.error(f"❌ Rakip analizi hatası: {e}")
                                                import traceback
                                                st.code(traceback.format_exc())
                                else:
                                    st.warning("⚠️ Bu hisse için rakip bulunamadı.")
                            except ImportError:
                                st.warning("⚠️ Rakip analizi modülü bulunamadı.")
                            except Exception as e:
                                st.error(f"❌ Rakip analizi hatası: {e}")
                        
                        # TAB 7: KAP Dedektifi
                        with tab_kap_detective:
                            st.subheader("🔍 KAP Dedektifi")
                            st.info("💡 Faaliyet raporlarındaki dil değişimini analiz eder.")
                            
                            try:
                                from src.kap_detective import analyze_language_change, detect_red_flags
                                from src.kap_scraper import get_kap_financial_reports
                                import google.generativeai as genai
                                
                                if GEMINI_API_KEY:
                                    genai.configure(api_key=GEMINI_API_KEY)
                                    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                                else:
                                    gemini_model = None
                                    st.warning("⚠️ Gemini API key gerekli.")
                                
                                if gemini_model:
                                    ticker_clean = ticker.replace('.IS', '')
                                    kap_reports = get_kap_financial_reports(ticker_clean, limit=10)
                                    
                                    if kap_reports:
                                        st.success(f"✅ {len(kap_reports)} KAP bildirimi bulundu.")
                                        
                                        if len(kap_reports) >= 2:
                                            if st.button("🔍 Dil Değişimini Analiz Et", key="analyze_language_change"):
                                                with st.spinner("Dil analizi yapılıyor..."):
                                                    try:
                                                        current_text = f"{kap_reports[0].get('title', '')} {kap_reports[0].get('type', '')}"
                                                        previous_text = f"{kap_reports[1].get('title', '')} {kap_reports[1].get('type', '')}"
                                                        
                                                        analysis = analyze_language_change(
                                                            current_report_text=current_text,
                                                            previous_report_text=previous_text,
                                                            gemini_model=gemini_model
                                                        )
                                                        
                                                        if analysis and analysis.get('success'):
                                                            result = analysis.get('analysis', {})
                                                            if result:
                                                                tone_change = result.get('tone_change', 'similar')
                                                                tone_emoji = {'more_concerned': '🔴', 'more_optimistic': '🟢', 'similar': '🟡'}
                                                                st.write(f"{tone_emoji.get(tone_change, '⚪')} **Ton Değişimi:** {tone_change}")
                                                                
                                                                if 'uncertainty_increase' in result:
                                                                    st.metric("Belirsizlik Artışı", f"{result['uncertainty_increase']:.2%}")
                                                                
                                                                if 'key_changes' in result and result['key_changes']:
                                                                    st.subheader("🔑 Önemli Değişiklikler")
                                                                    for change in result['key_changes']:
                                                                        st.write(f"- {change}")
                                                                
                                                                if 'red_flags' in result and result['red_flags']:
                                                                    st.subheader("🚨 Kırmızı Bayraklar")
                                                                    for flag in result['red_flags']:
                                                                        st.warning(f"⚠️ {flag}")
                                                                
                                                                if 'summary' in result:
                                                                    st.write(f"**Özet:** {result['summary']}")
                                                            else:
                                                                st.warning("⚠️ Analiz sonucu boş döndü.")
                                                        else:
                                                            error_msg = analysis.get('error', 'Bilinmeyen hata') if analysis else 'Analiz başarısız'
                                                            st.warning(f"⚠️ Dil analizi başarısız: {error_msg}")
                                                    except Exception as e:
                                                        st.error(f"❌ Dil analizi hatası: {str(e)}")
                                                        import traceback
                                                        with st.expander("🔍 Hata Detayları"):
                                                            st.code(traceback.format_exc(), language="python")
                                        
                                        # Kırmızı bayrak tespiti
                                        st.subheader("🚨 Kırmızı Bayrak Tespiti")
                                        try:
                                            all_red_flags = []
                                            for report in kap_reports[:5]:
                                                flags = detect_red_flags(report.get('title', '') + ' ' + report.get('type', ''))
                                                all_red_flags.extend(flags)
                                            
                                            if all_red_flags:
                                                for flag in all_red_flags[:10]:
                                                    st.warning(f"⚠️ {flag}")
                                            else:
                                                st.info("ℹ️ Kırmızı bayrak tespit edilmedi.")
                                        except Exception as e:
                                            st.warning(f"⚠️ Kırmızı bayrak tespiti hatası: {e}")
                                    
                                    else:
                                        st.info("ℹ️ KAP bildirimi bulunamadı.")
                            except ImportError:
                                st.warning("⚠️ KAP Dedektifi modülü bulunamadı.")
                            except Exception as e:
                                st.error(f"❌ KAP Dedektifi hatası: {e}")
                                import traceback
                                with st.expander("🔍 Hata Detayları"):
                                    st.code(traceback.format_exc(), language="python")
                        
                        # TAB 8: Insider Trading
                        with tab_insider:
                            st.subheader("👔 Insider Trading Takibi")
                            st.info("💡 Şirket yöneticilerinin pay alım/satım işlemlerini takip eder.")
                            
                            try:
                                from src.insider_trading import get_insider_trading_from_kap
                                
                                if st.button("🔍 Insider Trading Analizini Çalıştır", key="run_insider_analysis"):
                                    with st.spinner("Insider trading analizi yapılıyor..."):
                                        try:
                                            ticker_clean = ticker.replace('.IS', '')
                                            insider_analysis = get_insider_trading_from_kap(ticker_clean, limit=20)
                                            
                                            if insider_analysis and insider_analysis.get('success'):
                                                insider_trades = insider_analysis.get('insider_trades', [])
                                                sentiment = insider_analysis.get('sentiment', {})
                                                
                                                if insider_trades:
                                                    st.success(f"✅ {len(insider_trades)} insider trading işlemi tespit edildi.")
                                                    sentiment_score = sentiment.get('score', 0.0)
                                                    sentiment_type = sentiment.get('sentiment', 'neutral')
                                                    sentiment_emoji = {'very_positive': '🟢🟢', 'positive': '🟢', 'neutral': '🟡', 'negative': '🔴', 'very_negative': '🔴🔴'}
                                                    st.write(f"{sentiment_emoji.get(sentiment_type, '⚪')} **Sentiment:** {sentiment_type.upper()}")
                                                    st.metric("Sentiment Skoru", f"{sentiment_score:.2f}", 
                                                            delta=f"{sentiment.get('buy_count', 0)} alım, {sentiment.get('sell_count', 0)} satım")
                                                    st.write(sentiment.get('message', ''))
                                                    
                                                    st.subheader("📋 Insider Trading İşlemleri")
                                                    for trade in insider_trades:
                                                        action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'UNKNOWN': '⚪'}
                                                        with st.expander(f"{action_emoji.get(trade.get('action', 'UNKNOWN'), '⚪')} {trade.get('title', 'Başlık yok')}", expanded=False):
                                                            st.write(f"**Tarih:** {trade.get('date', 'Bilinmiyor')}")
                                                            st.write(f"**İşlem:** {trade.get('action', 'UNKNOWN')}")
                                                            if trade.get('position'):
                                                                st.write(f"**Pozisyon:** {trade.get('position')}")
                                                            if trade.get('amount'):
                                                                st.write(f"**Miktar:** {trade.get('amount')}")
                                                else:
                                                    st.info("ℹ️ Insider trading işlemi bulunamadı.")
                                            else:
                                                error_msg = insider_analysis.get('error', 'Bilinmeyen hata') if insider_analysis else 'Analiz başarısız'
                                                st.warning(f"⚠️ Insider trading analizi başarısız: {error_msg}")
                                        except Exception as e:
                                            st.error(f"❌ Insider trading analizi hatası: {str(e)}")
                                            import traceback
                                            with st.expander("🔍 Hata Detayları"):
                                                st.code(traceback.format_exc(), language="python")
                            except ImportError:
                                st.warning("⚠️ Insider trading modülü bulunamadı.")
                            except Exception as e:
                                st.error(f"❌ Insider trading hatası: {e}")
                                import traceback
                                with st.expander("🔍 Hata Detayları"):
                                    st.code(traceback.format_exc(), language="python")
                        
                        # TAB 9: Portföy
                        with tab_portfolio:
                            st.subheader("💼 Portföy Analizi")
                            st.info("💡 Bu hisseyi portföyünüze eklemek için 'Portföy Optimizasyonu' sayfasını kullanın.")
                            
                            # Bu hisse için portföy önerisi (basit)
                            if not results['price_df'].empty:
                                price_df = results['price_df']
                                current_price = price_df.iloc[-1]['close']
                                
                                # Türk hissesi kontrolü (.IS uzantısı veya 5 karakterli)
                                is_turkish_stock = ticker.endswith('.IS') or (len(ticker) == 5 and ticker.isalpha() and ticker.isupper())
                                price_display = f"₺{current_price:.2f}" if is_turkish_stock else f"${current_price:.2f}"
                                
                                st.metric("Mevcut Fiyat", price_display)
                                
                                # Basit portföy önerisi
                                if results['overall_score'] >= 70:
                                    st.success("✅ Bu hisse portföyünüze eklenebilir (Yüksek skor)")
                                elif results['overall_score'] < 30:
                                    st.warning("⚠️ Bu hisse portföyünüze eklenmemeli (Düşük skor)")
                                else:
                                    st.info("ℹ️ Bu hisse portföyünüze eklenebilir (Orta skor)")
                            
                            # Portföy optimizasyonu linki
                            st.markdown("---")
                            st.markdown("**💡 İpucu:** Birden fazla hisse için portföy optimizasyonu yapmak için 'Portföy Optimizasyonu' sayfasına gidin.")
                        
                        # Time Travel Analysis Tab
                        with tab_time_travel:
                            st.subheader("🕐 Time Travel Analysis")
                            st.info("💡 Geçmiş bir tarihe gidip o günkü analizi görün. 'Eğer o gün sistem çalışsaydı ne derdi?' sorusunu yanıtlar.")
                            
                            try:
                                from src.time_travel import analyze_historical_date, compare_predictions_with_reality
                                
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    target_date = st.date_input(
                                        "📅 Analiz Edilecek Tarih",
                                        value=None,
                                        min_value=pd.to_datetime("2015-01-01").date(),
                                        max_value=pd.to_datetime("today").date(),
                                        help="Geçmiş bir tarih seçin (2015'ten bugüne kadar)"
                                    )
                                
                                with col2:
                                    st.write("")  # Boşluk
                                    st.write("")  # Boşluk
                                    analyze_button = st.button("🕐 Analiz Et", type="primary")
                                
                                if analyze_button and target_date:
                                    with st.spinner(f"🕐 {target_date} tarihindeki analiz yapılıyor..."):
                                        try:
                                            time_travel_results = analyze_historical_date(
                                                ticker=ticker,
                                                target_date=target_date.strftime("%Y-%m-%d"),
                                                company_name=company_name
                                            )
                                            
                                            if not time_travel_results:
                                                st.error("❌ Time Travel Analysis sonuç döndürmedi. Lütfen tekrar deneyin.")
                                                st.stop()
                                            
                                            st.success("✅ Time Travel Analysis tamamlandı!")
                                            
                                            # O günkü bilgileri göster
                                            col_info1, col_info2, col_info3 = st.columns(3)
                                            with col_info1:
                                                st.metric(
                                                    "O Günkü Fiyat",
                                                    f"₺{time_travel_results['price_data']['close']:.2f}" if ticker.endswith('.IS') or len(ticker) == 5 else f"${time_travel_results['price_data']['close']:.2f}"
                                                )
                                            with col_info2:
                                                st.metric(
                                                    "Genel Skor",
                                                    f"{time_travel_results['overall_score']:.1f}/100"
                                                )
                                            with col_info3:
                                                st.metric(
                                                    "Haber Sayısı",
                                                    time_travel_results['news_count']
                                                )
                                            
                                            # Skorlar
                                            st.subheader("📊 O Günkü Skorlar")
                                            col_score1, col_score2 = st.columns(2)
                                            with col_score1:
                                                st.metric("Sentiment Skoru", f"{time_travel_results['sentiment_score']:.1f}/100")
                                            with col_score2:
                                                st.metric("Finansal Skor", f"{time_travel_results['financial_score']:.1f}/100")
                                            
                                            # Tahmin
                                            direction_pred = time_travel_results['direction_prediction']
                                            direction_emoji = "🟢" if direction_pred.get('direction') == 'BUY' else "🔴" if direction_pred.get('direction') == 'SELL' else "🟡"
                                            
                                            st.subheader("🎯 O Günkü Tahmin")
                                            st.markdown(f"""
                                            **Yön:** {direction_emoji} {direction_pred.get('direction', 'HOLD')}  
                                            **Güven:** {direction_pred.get('confidence', 0.5):.1%}
                                            """)
                                            
                                            # Gerçek fiyat değişimleri ile karşılaştırma
                                            try:
                                                if time_travel_results.get('future_changes'):
                                                    st.subheader("📈 Gerçek Fiyat Değişimleri")
                                                    
                                                    comparison = compare_predictions_with_reality(
                                                        ticker=ticker,
                                                        target_date=target_date.strftime("%Y-%m-%d"),
                                                        prediction=time_travel_results
                                                    )
                                                    
                                                    if comparison and 'actual_direction' in comparison and comparison['actual_direction']:
                                                        col_comp1, col_comp2, col_comp3 = st.columns(3)
                                                        with col_comp1:
                                                            st.metric("Tahmin", comparison.get('predicted_direction', 'N/A'))
                                                        with col_comp2:
                                                            st.metric("Gerçek", comparison['actual_direction'])
                                                        with col_comp3:
                                                            accuracy_emoji = "✅" if comparison.get('correct', False) else "❌"
                                                            st.metric("Doğruluk", f"{accuracy_emoji} {'Doğru' if comparison.get('correct', False) else 'Yanlış'}")
                                                        
                                                        # 30 gün sonrası değişim
                                                        if '30_day' in time_travel_results.get('future_changes', {}):
                                                            change_30d = time_travel_results['future_changes']['30_day'].get('change_percent', 0)
                                                            st.metric(
                                                                "30 Gün Sonrası Değişim",
                                                                f"{change_30d:+.2f}%"
                                                            )
                                                    else:
                                                        st.info("ℹ️ Gerçek fiyat değişimi karşılaştırması yapılamadı.")
                                            except Exception as comp_error:
                                                logger.warning(f"Karşılaştırma hatası: {comp_error}")
                                                st.warning("⚠️ Gerçek fiyat değişimi karşılaştırması yapılamadı.")
                                            
                                            # O günkü haberler
                                            if time_travel_results.get('news_df'):
                                                st.subheader("📰 O Günkü Haberler")
                                                with st.expander("Haberleri Görüntüle", expanded=False):
                                                    for news in time_travel_results['news_df'][:10]:
                                                        st.markdown(f"**{news.get('title', 'Başlık yok')}**")
                                                        st.caption(f"📅 {news.get('published_at', 'Tarih yok')}")
                                                        if news.get('url'):
                                                            st.caption(f"🔗 [Link]({news.get('url')})")
                                                        st.divider()
                                            
                                        except Exception as e:
                                            st.error(f"❌ Time Travel Analysis hatası: {str(e)}")
                                            import traceback
                                            with st.expander("🔍 Hata Detayları"):
                                                st.code(traceback.format_exc(), language="python")
                                            logger.error(f"Time Travel Analysis hatası: {e}")
                                            logger.error(traceback.format_exc())
                                
                                elif analyze_button and not target_date:
                                    st.warning("⚠️ Lütfen bir tarih seçin!")
                                
                            except ImportError:
                                st.warning("⚠️ Time Travel Analysis modülü bulunamadı. src/time_travel.py dosyasının mevcut olduğundan emin olun.")
                        
                        # PDF Chat Tab
                        with tab_pdf_chat:
                            st.subheader("💬 PDF Chat (RAG ile Sorgulama)")
                            st.info("💡 Faaliyet raporlarına doğal dil ile soru sorun. Sistem PDF içeriğini analiz edip yanıt verir.")
                            
                            try:
                                from src.pdf_chat import get_pdf_chat
                                from src.pdf_parser import PDFParser
                                
                                pdf_chat = get_pdf_chat()
                                
                                if not pdf_chat or not pdf_chat.available:
                                    st.warning("⚠️ PDF Chat kullanılamıyor. Gerekli kütüphaneler yüklü değil veya API key eksik.")
                                    
                                    # Eksik kütüphaneleri kontrol et
                                    missing_libs = []
                                    try:
                                        import google.generativeai as genai
                                    except ImportError:
                                        missing_libs.append("google-generativeai")
                                    
                                    try:
                                        from sentence_transformers import SentenceTransformer
                                    except ImportError:
                                        missing_libs.append("sentence-transformers")
                                    
                                    try:
                                        import chromadb
                                    except ImportError:
                                        missing_libs.append("chromadb")
                                    
                                    if missing_libs:
                                        st.error(f"❌ Eksik kütüphaneler: {', '.join(missing_libs)}")
                                        st.code(f"pip install {' '.join(missing_libs)}", language="bash")
                                    
                                    if not GEMINI_API_KEY:
                                        st.error("❌ GEMINI_API_KEY eksik. .env dosyasına ekleyin.")
                                    
                                    st.info("💡 Gerekli: GEMINI_API_KEY, sentence-transformers, chromadb")
                                    st.stop()
                                else:
                                    # PDF listesi
                                    pdf_list = pdf_chat.get_pdf_list()
                                    
                                    if pdf_list:
                                        st.subheader("📄 Mevcut PDF'ler")
                                        pdf_options = {f"{pdf['pdf_id']} - {pdf['metadata'].get('company_name', 'N/A')}": pdf['pdf_id'] for pdf in pdf_list}
                                        selected_pdf = st.selectbox(
                                            "PDF Seçin",
                                            options=list(pdf_options.keys()),
                                            help="Sorgulamak istediğiniz PDF'i seçin"
                                        )
                                        selected_pdf_id = pdf_options[selected_pdf] if selected_pdf else None
                                    else:
                                        st.info("📝 Henüz PDF eklenmemiş. KAP'tan PDF indirip ekleyebilirsiniz.")
                                        selected_pdf_id = None
                                    
                                    # PDF ekleme (KAP'tan)
                                    with st.expander("➕ PDF Ekle (KAP'tan)", expanded=False):
                                        st.info("💡 KAP bildirimi linkinden PDF'i indirip sisteme ekleyin.")
                                        
                                        kap_url = st.text_input(
                                            "KAP Bildirimi URL'si",
                                            placeholder="https://www.kap.org.tr/tr/Bildirim/...",
                                            help="KAP bildirimi sayfasının URL'si"
                                        )
                                        
                                        report_title = st.text_input(
                                            "Rapor Başlığı",
                                            value="Faaliyet Raporu",
                                            help="Rapor tipi (örn: Faaliyet Raporu, Mali Tablo)"
                                        )
                                        
                                        if st.button("📥 PDF İndir ve Ekle"):
                                            if kap_url:
                                                with st.spinner("PDF indiriliyor ve analiz ediliyor..."):
                                                    try:
                                                        parser = PDFParser()
                                                        pdf_result = parser.parse_kap_pdf(kap_url, report_title)
                                                        
                                                        if 'error' in pdf_result:
                                                            st.error(f"❌ {pdf_result['error']}")
                                                        else:
                                                            # PDF'i chat'e ekle
                                                            pdf_id = f"{ticker}_{report_title.lower().replace(' ', '_')}"
                                                            pdf_text = pdf_result.get('extracted_text', '')
                                                            
                                                            if pdf_chat.add_pdf(
                                                                pdf_id=pdf_id,
                                                                pdf_text=pdf_text,
                                                                metadata={
                                                                    'ticker': ticker,
                                                                    'company_name': company_name,
                                                                    'report_title': report_title,
                                                                    'kap_url': kap_url
                                                                }
                                                            ):
                                                                st.success(f"✅ PDF eklendi: {pdf_id}")
                                                                st.rerun()
                                                            else:
                                                                st.error("❌ PDF eklenemedi!")
                                                    except Exception as e:
                                                        st.error(f"❌ Hata: {str(e)}")
                                                        st.exception(e)
                                            else:
                                                st.warning("⚠️ Lütfen KAP URL'si girin!")
                                    
                                    # Soru sorma
                                    if selected_pdf_id:
                                        st.markdown("---")
                                        st.subheader("💬 PDF'e Soru Sor")
                                        
                                        question = st.text_area(
                                            "Sorunuz",
                                            placeholder="Örnek: Geçen seneki Ar-Ge harcaması ne kadar? Şirketin en büyük riski nedir?",
                                            help="PDF içeriğine dayalı sorular sorun"
                                        )
                                        
                                        if st.button("❓ Sor", type="primary"):
                                            if question:
                                                with st.spinner("🤔 PDF analiz ediliyor..."):
                                                    try:
                                                        answer_result = pdf_chat.ask_question(
                                                            question=question,
                                                            pdf_id=selected_pdf_id,
                                                            context_chunks=5
                                                        )
                                                        
                                                        if answer_result.get('error'):
                                                            st.error(f"❌ {answer_result['answer']}")
                                                        else:
                                                            st.success("✅ Yanıt hazır!")
                                                            
                                                            # Yanıtı göster
                                                            st.markdown("### 💡 Yanıt")
                                                            st.markdown(answer_result['answer'])
                                                            
                                                            # İlgili bölümler
                                                            if answer_result.get('relevant_chunks'):
                                                                with st.expander("📄 İlgili Bölümler", expanded=False):
                                                                    for i, chunk in enumerate(answer_result['relevant_chunks'][:3], 1):
                                                                        st.markdown(f"**Bölüm {i}** (Benzerlik: {chunk['similarity']:.1%})")
                                                                        st.markdown(chunk['text'][:500] + "...")
                                                                        st.divider()
                                                    except Exception as e:
                                                        st.error(f"❌ Hata: {str(e)}")
                                                        st.exception(e)
                                            else:
                                                st.warning("⚠️ Lütfen bir soru girin!")
                                    
                            except ImportError:
                                st.warning("⚠️ PDF Chat modülü bulunamadı. src/pdf_chat.py dosyasının mevcut olduğundan emin olun.")
                        
                        # Haber listesi (ayrı bir bölüm - eski kod, artık tab_news_report içinde)
                        if False and not results['news_df'].empty and 'sentiment_class' in results['news_df'].columns:
                            news_df = results['news_df']
                            
                            with st.expander("📰 Tüm Haberler", expanded=False):
                                # Filtreleme seçenekleri
                                sentiment_filter = st.multiselect(
                                    "Sentiment Filtresi",
                                    options=['positive', 'negative', 'neutral'],
                                    default=['positive', 'negative', 'neutral'],
                                    key='sentiment_filter'
                                )
                                
                                filtered_news = news_df[news_df['sentiment_class'].isin(sentiment_filter)] if sentiment_filter else news_df
                                
                                for idx, row in filtered_news.head(20).iterrows():
                                    # Güvenli kolon erişimi
                                    title = row.get('title', 'Başlık yok')
                                    sentiment_class = row.get('sentiment_class', 'neutral')
                                    sentiment_confidence = row.get('sentiment_confidence', 0.0)
                                    source = row.get('source', 'Unknown')
                                    url = row.get('url', '')
                                    
                                    emoji = "🟢" if sentiment_class == 'positive' else \
                                           "🔴" if sentiment_class == 'negative' else "🟡"
                                    
                                    col_title, col_info = st.columns([3, 1])
                                    with col_title:
                                        st.write(f"{emoji} **{title}**")
                                    with col_info:
                                        st.caption(f"{sentiment_class.upper()}")
                                        st.caption(f"Güven: {sentiment_confidence:.1%}")
                                    
                                    st.caption(f"📅 {row.get('published_at', 'Bilinmiyor')} | 📰 {source}")
                                    if url:
                                        st.caption(f"🔗 [Haber Linki]({url})")
                                    st.divider()
                        
                        # Skor karşılaştırması - Gelişmiş görselleştirme
                        st.subheader("📊 Skor Analizi")
                        
                        col_score1, col_score2 = st.columns(2)
                        
                        with col_score1:
                            # Skor bar grafiği
                            scores = {
                                'Sentiment': results['sentiment_score'],
                                'Finansal': results['financial_score'],
                                'Genel Durum': results['overall_score']
                            }
                            
                            fig_scores = go.Figure(data=[go.Bar(
                                x=list(scores.keys()),
                                y=list(scores.values()),
                                marker=dict(
                                    color=[scores['Sentiment'], scores['Finansal'], scores['Genel Durum']],
                                    colorscale='RdYlGn',
                                    cmin=0,
                                    cmax=100,
                                    showscale=True
                                ),
                                text=[f"{v:.1f}" for v in scores.values()],
                                textposition='auto',
                                hovertemplate='<b>%{x}</b><br>Skor: %{y:.1f}/100<extra></extra>'
                            )])
                            
                            fig_scores.update_layout(
                                title='Skor Karşılaştırması',
                                yaxis_title='Skor (0-100)',
                                yaxis=dict(range=[0, 100]),
                                height=350
                            )
                            
                            st.plotly_chart(fig_scores, width='stretch')
                        
                        with col_score2:
                            # Skor radar grafiği
                            categories = ['Sentiment', 'Finansal', 'Genel Durum']
                            values = [results['sentiment_score'], results['financial_score'], results['overall_score']]
                            
                            fig_radar = go.Figure()
                            
                            fig_radar.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself',
                                name='Skorlar',
                                line=dict(color='blue'),
                                hovertemplate='<b>%{theta}</b><br>Skor: %{r:.1f}/100<extra></extra>'
                            ))
                            
                            fig_radar.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100]
                                    )),
                                showlegend=False,
                                title='Skor Radar Grafiği',
                                height=350
                            )
                            
                            st.plotly_chart(fig_radar, width='stretch')
                        
                    except Exception as e:
                        st.error(f"❌ Hata oluştu: {str(e)}")
                        st.exception(e)

# İzleme Listesi Sayfası
elif page == "📋 İzleme Listesi":
    st.header("📋 İzleme Listesi")
    st.write("Takip etmek istediğiniz hisse senetlerini ekleyin ve yönetin.")
    
    # Local watchlist kullan (Firebase gerekmez)
    try:
        from src.local_watchlist import (
            load_watchlist, save_watchlist, add_to_watchlist, 
            remove_from_watchlist, get_watchlist, clear_watchlist
        )
        USE_LOCAL_WATCHLIST = True
    except ImportError:
        # Fallback: Firebase watchlist (eğer local_watchlist yoksa)
        try:
            from src.firestore_watchlist import get_firestore_client, save_watchlist, get_watchlist
            USE_LOCAL_WATCHLIST = False
        except ImportError:
            st.error("❌ Watchlist modülü bulunamadı.")
            st.info("💡 src/local_watchlist.py dosyasının mevcut olduğundan emin olun.")
            st.stop()
    
    try:
        if USE_LOCAL_WATCHLIST:
            # Local watchlist kullan (JSON dosyası)
            st.info("💡 İzleme listesi yerel olarak kaydediliyor (data/watchlist.json).")
            
            # Mevcut watchlist'i yükle
            current_watchlist = get_watchlist()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 İzleme Listesi")
                if current_watchlist:
                    # DataFrame oluştur
                    watchlist_data = []
                    for item in current_watchlist:
                        watchlist_data.append({
                            'Ticker': item.get('ticker', ''),
                            'Şirket Adı': item.get('company_name', ''),
                            'Eklenme Tarihi': item.get('added_date', '')[:10] if item.get('added_date') else ''
                        })
                    watchlist_df = pd.DataFrame(watchlist_data)
                    st.dataframe(watchlist_df, width='stretch', use_container_width=True)
                else:
                    st.info("📝 Henüz izleme listesi oluşturulmamış. Sağdaki formdan ekleyin.")
            
            with col2:
                st.subheader("➕ Hisse Ekle")
                new_ticker = st.text_input("Borsa Kodu", value="", placeholder="THYAO, AAPL, ...", key="new_ticker_local")
                new_company = st.text_input("Şirket Adı (Opsiyonel)", value="", placeholder="Apple Inc.", key="new_company_local")
                
                if st.button("➕ Ekle", type="primary", key="add_local"):
                    if new_ticker:
                        new_ticker = new_ticker.upper().strip()
                        company_name = new_company.strip() if new_company else new_ticker
                        
                        if add_to_watchlist(new_ticker, company_name):
                            st.success(f"✅ {new_ticker} ({company_name}) eklendi!")
                            st.rerun()
                        else:
                            st.warning(f"⚠️ {new_ticker} zaten listede veya eklenemedi!")
                    else:
                        st.warning("⚠️ Lütfen bir ticker girin!")
                
                # Silme
                if current_watchlist:
                    st.subheader("🗑️ Hisse Sil")
                    ticker_options = [f"{item.get('ticker', '')} - {item.get('company_name', '')}" for item in current_watchlist]
                    selected = st.selectbox("Silinecek Ticker", ticker_options, key="remove_ticker_local")
                    ticker_to_remove = selected.split(' - ')[0] if selected else None
                    
                    if st.button("🗑️ Sil", type="secondary", key="remove_local"):
                        if ticker_to_remove and remove_from_watchlist(ticker_to_remove):
                            st.success(f"✅ {ticker_to_remove} silindi!")
                            st.rerun()
                        else:
                            st.error("❌ Silme hatası!")
                
                # Temizle
                if current_watchlist:
                    if st.button("🗑️ Tümünü Temizle", type="secondary", key="clear_local"):
                        clear_watchlist()
                        st.success("✅ İzleme listesi temizlendi!")
                        st.rerun()
        
        else:
            # Firebase watchlist (fallback)
            st.warning("⚠️ Local watchlist kullanılamıyor. Firebase watchlist kullanılıyor.")
            st.info("💡 Firebase watchlist özelliği için Google Cloud credentials gerekir.")
            st.info("💡 Local watchlist kullanmak için src/local_watchlist.py dosyasının mevcut olduğundan emin olun.")
    
    except Exception as e:
        st.error(f"❌ İzleme listesi hatası: {str(e)}")
        st.exception(e)

# Portföy Optimizasyonu Sayfası
elif page == "💼 Portföy Optimizasyonu":
    st.header("💼 Portföy Optimizasyonu")
    st.write("Birden fazla hisse için optimal portföy ağırlıklarını hesaplayın.")
    
    try:
        from src.portfolio_optimization import calculate_optimal_portfolio_weights
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📝 Portföy Parametreleri")
            
            # Ticker listesi
            tickers_input = st.text_area(
                "Hisse Kodları (virgülle ayırın)",
                value="THYAO, EREGL, TUPRS, GARAN, AKBNK",
                help="Örnek: THYAO, EREGL, TUPRS"
            )
            
            period = st.selectbox(
                "Veri Periyodu",
                ["6mo", "1y", "2y", "3y"],
                index=1
            )
            
            optimization_method = st.selectbox(
                "Optimizasyon Yöntemi",
                ["max_sharpe", "min_volatility"],
                index=0,
                help="Maksimum Sharpe Oranı veya Minimum Volatilite"
            )
            
            risk_free_rate = st.slider(
                "Risksiz Faiz Oranı (%)",
                min_value=0.0,
                max_value=10.0,
                value=2.0,
                step=0.1,
                help="Maksimum Sharpe optimizasyonu için, en az bir hissenin beklenen getirisi bu değerden yüksek olmalıdır. Düşük değerler daha kolay sonuç verir."
            ) / 100.0
            
            optimize_button = st.button("🚀 Portföy Optimize Et", type="primary")
        
        with col2:
            st.subheader("📊 Optimizasyon Sonuçları")
            
            if optimize_button:
                with st.spinner("Portföy optimizasyonu yapılıyor..."):
                    try:
                        # Ticker'ları parse et
                        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
                        
                        if len(tickers) < 2:
                            st.error("❌ En az 2 hisse gerekli!")
                        else:
                            # Fiyat verilerini çek
                            from src.data_collection import get_price_data
                            
                            price_data = {}
                            for ticker in tickers:
                                try:
                                    df = get_price_data(ticker, period=period)
                                    if not df.empty and 'close' in df.columns:
                                        # Index'i datetime'a çevir (eğer 'date' kolonu varsa)
                                        if 'date' in df.columns:
                                            df = df.set_index('date')
                                            df.index = pd.to_datetime(df.index)
                                        elif not isinstance(df.index, pd.DatetimeIndex):
                                            # Index zaten datetime değilse, datetime'a çevir
                                            df.index = pd.to_datetime(df.index)
                                        
                                        price_data[ticker] = df['close']
                                except Exception as e:
                                    st.warning(f"⚠️ {ticker} için veri çekilemedi: {e}")
                            
                            if len(price_data) < 2:
                                st.error("❌ Yeterli fiyat verisi bulunamadı!")
                            else:
                                # DataFrame oluştur
                                price_df = pd.DataFrame(price_data)
                                
                                # Index'i DatetimeIndex'e çevir (eğer değilse)
                                if not isinstance(price_df.index, pd.DatetimeIndex):
                                    # Tüm Series'lerin index'lerini birleştir
                                    all_dates = set()
                                    for series in price_data.values():
                                        all_dates.update(series.index)
                                    
                                    # Yeni index oluştur
                                    new_index = pd.DatetimeIndex(sorted(all_dates))
                                    price_df = price_df.reindex(new_index)
                                
                                # Eksik değerleri forward fill ile doldur (sonra dropna yapılacak)
                                price_df = price_df.ffill().dropna()
                                
                                # Optimizasyon yap
                                result = calculate_optimal_portfolio_weights(
                                    price_df,
                                    method=optimization_method,
                                    risk_free_rate=risk_free_rate
                                )
                                
                                # Eğer method değiştiyse (fallback), kullanıcıya bilgi ver
                                if result.get('method_used') != optimization_method:
                                    st.warning(f"⚠️ **Not:** Maksimum Sharpe optimizasyonu yapılamadı.")
                                    with st.expander("ℹ️ Neden?", expanded=False):
                                        st.markdown("""
                                        **Maksimum Sharpe optimizasyonu** için, en az bir varlığın beklenen getirisi risksiz faiz oranından yüksek olmalıdır.
                                        
                                        **Neden olmadı?**
                                        - Seçilen hisselerin geçmiş performansı risksiz faiz oranından (%2) düşük
                                        - Bu durum, son dönemde düşük getiri veya negatif trend gösterebilir
                                        - Veri periyodu çok kısa olabilir (örn: 6mo)
                                        
                                        **Ne yapıldı?**
                                        - Otomatik olarak **Minimum Volatilite** optimizasyonuna geçildi
                                        - Bu optimizasyon, riski minimize ederek en güvenli portföyü bulur
                                        - Getiri beklentisi düşük olsa bile, risk yönetimi açısından mantıklı
                                        
                                        **Öneriler:**
                                        - Risksiz faiz oranını düşürün (örn: %1 veya %0.5)
                                        - Daha uzun periyot seçin (örn: 2y veya 3y)
                                        - Farklı hisseler deneyin
                                        """)
                                
                                weights = result['weights']
                                
                                # Sonuçları göster
                                st.success("✅ Optimizasyon tamamlandı!")
                                
                                # Performans metriklerini göster
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Beklenen Getiri", f"{result['expected_return']*100:.2f}%")
                                with col2:
                                    st.metric("Yıllık Volatilite", f"{result['annual_volatility']*100:.2f}%")
                                with col3:
                                    st.metric("Sharpe Oranı", f"{result['sharpe_ratio']:.2f}" if result['sharpe_ratio'] else "N/A")
                                
                                # Ağırlıklar grafiği
                                weights_df = pd.DataFrame({
                                    'Hisse': list(weights.keys()),
                                    'Ağırlık (%)': [w * 100 for w in weights.values()]
                                }).sort_values('Ağırlık (%)', ascending=False)
                                
                                fig = go.Figure(data=[go.Bar(
                                    x=weights_df['Hisse'],
                                    y=weights_df['Ağırlık (%)'],
                                    marker_color='lightblue',
                                    text=[f"{w:.1f}%" for w in weights_df['Ağırlık (%)']],
                                    textposition='auto'
                                )])
                                
                                fig.update_layout(
                                    title='Optimal Portföy Ağırlıkları',
                                    xaxis_title='Hisse',
                                    yaxis_title='Ağırlık (%)',
                                    height=400
                                )
                                
                                st.plotly_chart(fig, width='stretch')
                                
                                # Pasta grafiği
                                fig_pie = go.Figure(data=[go.Pie(
                                    labels=weights_df['Hisse'],
                                    values=weights_df['Ağırlık (%)'],
                                    hole=0.3
                                )])
                                
                                fig_pie.update_layout(
                                    title='Portföy Dağılımı',
                                    height=400
                                )
                                
                                st.plotly_chart(fig_pie, width='stretch')
                                
                                # Tablo
                                st.subheader("📋 Detaylı Ağırlıklar")
                                st.dataframe(weights_df, width='stretch')
                    
                    except Exception as e:
                        st.error(f"❌ Optimizasyon hatası: {str(e)}")
                        st.exception(e)
            else:
                st.info("👈 Sol taraftan parametreleri ayarlayıp 'Portföy Optimize Et' butonuna tıklayın.")
    
    except ImportError:
        st.error("❌ PyPortfolioOpt yüklü değil. Portföy optimizasyonu kullanılamıyor.")
        st.info("💡 Yüklemek için: pip install PyPortfolioOpt")
    except Exception as e:
        st.error(f"❌ Portföy optimizasyonu hatası: {str(e)}")
        st.exception(e)

# Sektörel Analiz Sayfası
elif page == "📊 Sektörel Analiz":
    st.header("📊 Sektörel Analiz ve Korelasyon")
    st.write("Hisseler arası korelasyonları ve sektör rotasyonunu analiz edin.")
    
    try:
        from src.sector_analysis import (
            calculate_correlation,
            analyze_sector_correlation,
            calculate_sector_rotation,
            find_arbitrage_opportunities,
            BIST_SECTORS,
            US_SECTORS
        )
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔗 İki Hisse Korelasyonu", "📈 Sektör Korelasyon Matrisi", "🔄 Sektör Rotasyonu (Sankey)", "💰 Arbitraj Fırsatları", "🏛️ Yatırım Kurulu"])
        
        with tab1:
            st.subheader("🔗 İki Hisse Arası Korelasyon")
            
            col1, col2 = st.columns(2)
            with col1:
                ticker1 = st.text_input("İlk Hisse Kodu", value="THYAO", key="corr_ticker1")
            with col2:
                ticker2 = st.text_input("İkinci Hisse Kodu", value="PGSUS", key="corr_ticker2")
            
            period = st.selectbox("Veri Periyodu", ["3mo", "6mo", "1y", "2y"], index=2, key="corr_period")
            method = st.selectbox("Korelasyon Yöntemi", ["pearson", "spearman", "kendall"], index=0, key="corr_method")
            
            if st.button("🔍 Korelasyon Hesapla", type="primary"):
                with st.spinner("Korelasyon hesaplanıyor..."):
                    result = calculate_correlation(ticker1, ticker2, period=period, method=method)
                    
                    if 'error' not in result:
                        st.success("✅ Korelasyon hesaplandı!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Korelasyon", f"{result['correlation']:.3f}", help=result['interpretation'])
                        with col2:
                            st.metric("P-Value", f"{result['p_value']:.4f}" if result['p_value'] else "N/A")
                        with col3:
                            st.metric("Veri Noktası", f"{result['data_points']}")
                        
                        st.info(f"📊 **Yorum:** {result['interpretation']}")
                    else:
                        st.error(f"❌ Hata: {result['error']}")
        
        with tab2:
            st.subheader("📈 Sektör Korelasyon Matrisi")
            
            country = st.selectbox("Ülke", ["TR", "US"], index=0, key="sector_country")
            sectors = BIST_SECTORS if country == "TR" else US_SECTORS
            
            selected_sector = st.selectbox("Sektör Seçin", list(sectors.keys()), key="sector_select")
            
            # Periyot seçeneği ekle
            corr_period = st.selectbox("Veri Periyodu", ["3mo", "6mo", "1y", "2y"], index=1, key="corr_matrix_period")
            
            # Seçilen sektörün hisselerini göster
            st.info(f"📋 **Seçilen Sektör:** {selected_sector}\n\n**Hisseler:** {', '.join(sectors[selected_sector])}")
            
            if st.button("📊 Korelasyon Matrisini Hesapla", type="primary"):
                with st.spinner("Sektör korelasyon matrisi hesaplanıyor..."):
                    corr_matrix = analyze_sector_correlation(sectors[selected_sector], period=corr_period)
                    
                    # Hata mesajını kontrol et
                    if not corr_matrix.empty and 'error' in corr_matrix.columns:
                        error_msg = corr_matrix['error'].iloc[0]
                        st.error(f"❌ {error_msg}")
                        st.info(f"💡 **İpucu:** Seçilen sektör: {selected_sector}, Hisseler: {', '.join(sectors[selected_sector][:5])}")
                        st.info("💡 **Çözüm:** Farklı bir sektör seçin veya periyodu değiştirin (örn: 1y yerine 3mo)")
                    elif corr_matrix.empty:
                        st.error("❌ Korelasyon matrisi hesaplanamadı.")
                        st.warning(f"⚠️ **Olası nedenler:**")
                        st.write(f"   • Seçilen hisseler için veri bulunamadı: {', '.join(sectors[selected_sector][:5])}")
                        st.write(f"   • Yeterli ortak veri noktası yok")
                        st.write(f"   • Türk hisseleri için '.IS' uzantısı gerekebilir")
                        st.info(f"💡 **İpucu:** Seçilen sektör: {selected_sector}, Hisseler: {', '.join(sectors[selected_sector][:5])}")
                        st.info("💡 **Çözüm:** Farklı bir sektör seçin veya periyodu değiştirin (örn: 1y yerine 3mo)")
                    else:
                        st.success("✅ Korelasyon matrisi hesaplandı!")
                        
                        # Heatmap
                        import plotly.graph_objects as go
                        
                        fig = go.Figure(data=go.Heatmap(
                            z=corr_matrix.values,
                            x=corr_matrix.columns,
                            y=corr_matrix.index,
                            colorscale='RdYlGn',
                            zmid=0,
                            text=corr_matrix.values,
                            texttemplate='%{text:.2f}',
                            textfont={"size": 10},
                            colorbar=dict(title="Korelasyon")
                        ))
                        
                        fig.update_layout(
                            title=f'{selected_sector} Sektörü Korelasyon Matrisi',
                            height=500
                        )
                        
                        st.plotly_chart(fig, width='stretch')
                        
                        # Tablo
                        st.subheader("📋 Detaylı Matris")
                        st.dataframe(corr_matrix, width='stretch')
        
        with tab3:
            st.subheader("🔄 Sektör Rotasyonu (Sankey Diagram)")
            st.info("💡 Paranın hangi sektörden çıkıp hangisine girdiğini gösteren dinamik akış şeması.")
            
            try:
                from src.sector_rotation import get_sector_rotation_analysis
                
                # Ticker listesi al (portföy sayfasından veya manuel)
                sector_tickers_input = st.text_input(
                    "Analiz Edilecek Hisseler (virgülle ayırın)",
                    value="THYAO,PGSUS,GARAN,AKBNK,TUPRS,EREGL",
                    key="sector_tickers_input"
                )
                
                period_sector = st.selectbox(
                    "Zaman Periyodu",
                    ["1mo", "3mo", "6mo", "1y"],
                    index=0,
                    key="sector_period"
                )
                
                if st.button("🔄 Sektör Rotasyonu Analizini Çalıştır", key="run_sector_rotation"):
                    with st.spinner("Sektör rotasyonu analizi yapılıyor..."):
                        tickers = [t.strip().upper() for t in sector_tickers_input.split(',') if t.strip()]
                        
                        if len(tickers) < 2:
                            st.error("❌ En az 2 hisse gerekli!")
                        else:
                            analysis = get_sector_rotation_analysis(tickers, period=period_sector)
                            
                            if analysis.get('success'):
                                st.markdown(analysis.get('summary', ''))
                                
                                # Sankey diagram göster
                                if analysis.get('sankey_figure'):
                                    st.plotly_chart(analysis['sankey_figure'], use_container_width=True)
                                
                                # Sektör performans tablosu
                                if analysis.get('sector_performance'):
                                    st.subheader("📊 Sektör Performansları")
                                    perf_df = pd.DataFrame([
                                        {
                                            'Sektör': sector,
                                            'Performans Skoru': perf.get('performance_score', 0),
                                            'Ortalama Fiyat Değişimi': perf.get('avg_price_change', 0),
                                            'Ortalama Hacim Değişimi': perf.get('avg_volume_change', 0),
                                            'Hisse Sayısı': perf.get('ticker_count', 0)
                                        }
                                        for sector, perf in analysis['sector_performance'].items()
                                    ]).sort_values('Performans Skoru', ascending=False)
                                    
                                    st.dataframe(perf_df, use_container_width=True)
                            else:
                                st.error(f"❌ Analiz başarısız: {analysis.get('error', 'Bilinmeyen hata')}")
            except ImportError:
                st.warning("⚠️ Sektör rotasyonu modülü bulunamadı.")
            except Exception as e:
                st.error(f"❌ Sektör rotasyonu hatası: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        with tab5:
            st.subheader("🏛️ Yatırım Kurulu (Agentic AI)")
            st.info("💡 3 yapay zeka ajanı (Boğa, Ayı, Hakem) tartışıyor ve nihai karar veriyor.")
            
            try:
                from src.agents.investment_board import InvestmentBoard
                import google.generativeai as genai
                
                if GEMINI_API_KEY:
                    genai.configure(api_key=GEMINI_API_KEY)
                    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                else:
                    gemini_model = None
                    st.warning("⚠️ Gemini API key gerekli. Rule-based analiz kullanılacak.")
                
                # Analiz sonuçlarını al (eğer varsa)
                if 'results' in locals() and results:
                    if st.button("🏛️ Yatırım Kurulu Toplantısını Başlat", key="start_investment_board"):
                        with st.spinner("Yatırım kurulu toplantısı yapılıyor..."):
                            board = InvestmentBoard(gemini_model)
                            meeting = board.conduct_meeting(results)
                            
                            if meeting.get('success'):
                                st.markdown(meeting.get('meeting_summary', ''))
                                
                                # Detaylı görüşler
                                with st.expander("🐂 Boğa (Bull) Detaylı Görüşü", expanded=False):
                                    bull = meeting.get('bull_opinion', {})
                                    st.write(f"**Öneri:** {bull.get('recommendation', 'AL')}")
                                    st.write(f"**Güven:** {bull.get('confidence', 0.5):.1%}")
                                    st.write(f"**Özet:** {bull.get('summary', '')}")
                                
                                with st.expander("🐻 Ayı (Bear) Detaylı Görüşü", expanded=False):
                                    bear = meeting.get('bear_opinion', {})
                                    st.write(f"**Öneri:** {bear.get('recommendation', 'BEKLE')}")
                                    st.write(f"**Güven:** {bear.get('confidence', 0.5):.1%}")
                                    st.write(f"**Özet:** {bear.get('summary', '')}")
                                
                                with st.expander("⚖️ Hakem (Referee) Detaylı Kararı", expanded=True):
                                    decision = meeting.get('final_decision', {})
                                    st.write(f"**Nihai Öneri:** {decision.get('final_recommendation', 'BEKLE')}")
                                    st.write(f"**Güven:** {decision.get('confidence', 0.5):.1%}")
                                    st.write(f"**Gerekçe:** {decision.get('reasoning', '')}")
                                    st.write(f"**Özet:** {decision.get('summary', '')}")
                else:
                    st.info("ℹ️ Önce bir hisse analizi yapın, sonra yatırım kurulu toplantısını başlatabilirsiniz.")
            except ImportError:
                st.warning("⚠️ Yatırım kurulu modülü bulunamadı.")
            except Exception as e:
                st.error(f"❌ Yatırım kurulu hatası: {e}")
                import traceback
                st.code(traceback.format_exc())
            st.write("Hangi sektörler 'ucuz' veya 'pahalı' kaldı?")
            
            country = st.selectbox("Ülke", ["TR", "US"], index=0, key="rotation_country")
            sectors = BIST_SECTORS if country == "TR" else US_SECTORS
            
            period = st.selectbox("Analiz Periyodu", ["1mo", "3mo", "6mo", "1y"], index=1, key="rotation_period")
            
            if st.button("🔄 Rotasyon Analizi Yap", type="primary"):
                with st.spinner("Sektör rotasyonu analiz ediliyor..."):
                    rotation = calculate_sector_rotation(sectors, period=period, country=country)
                    
                    if rotation:
                        st.success("✅ Sektör rotasyonu analizi tamamlandı!")
                        
                        # DataFrame oluştur
                        rotation_df = pd.DataFrame([
                            {
                                'Sektör': sector,
                                'Ortalama Getiri (%)': data['avg_return'],
                                'Skor (0-100)': data['score'],
                                'Analiz Edilen Hisse': data['tickers_analyzed']
                            }
                            for sector, data in rotation.items()
                        ]).sort_values('Skor (0-100)', ascending=False)
                        
                        # Bar grafiği
                        fig = go.Figure(data=[go.Bar(
                            x=rotation_df['Sektör'],
                            y=rotation_df['Skor (0-100)'],
                            marker=dict(
                                color=rotation_df['Skor (0-100)'],
                                colorscale='RdYlGn',
                                showscale=True
                            ),
                            text=[f"{s:.1f}" for s in rotation_df['Skor (0-100)']],
                            textposition='auto'
                        )])
                        
                        fig.update_layout(
                            title='Sektör Performans Skorları',
                            xaxis_title='Sektör',
                            yaxis_title='Skor (0-100)',
                            height=400
                        )
                        
                        st.plotly_chart(fig, width='stretch')
                        
                        # Tablo
                        st.subheader("📋 Detaylı Sonuçlar")
                        st.dataframe(rotation_df, width='stretch')
                    else:
                        st.error("❌ Sektör rotasyonu analizi yapılamadı.")
        
        with tab4:
            st.subheader("💰 Arbitraj Fırsatları")
            st.write("İki hisse arasında spread analizi yaparak arbitraj fırsatları bulun.")
            
            col1, col2 = st.columns(2)
            with col1:
                arb_ticker1 = st.text_input("İlk Hisse Kodu", value="THYAO", key="arb_ticker1")
            with col2:
                arb_ticker2 = st.text_input("İkinci Hisse Kodu", value="PGSUS", key="arb_ticker2")
            
            arb_period = st.selectbox("Veri Periyodu", ["3mo", "6mo", "1y"], index=1, key="arb_period")
            threshold = st.slider("Eşik Değeri", min_value=0.1, max_value=1.0, value=0.3, step=0.1, key="arb_threshold")
            
            if st.button("🔍 Arbitraj Analizi Yap", type="primary"):
                with st.spinner("Arbitraj fırsatları aranıyor..."):
                    arb_result = find_arbitrage_opportunities(
                        arb_ticker1, arb_ticker2, period=arb_period, threshold=threshold
                    )
                    
                    if 'error' not in arb_result:
                        st.success("✅ Arbitraj analizi tamamlandı!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Mevcut Oran", f"{arb_result['current_ratio']:.3f}")
                        with col2:
                            st.metric("Ortalama Oran", f"{arb_result['mean_ratio']:.3f}")
                        with col3:
                            st.metric("Z-Score", f"{arb_result['z_score']:.2f}")
                        
                        if arb_result['opportunity']:
                            st.warning(f"⚠️ **Fırsat:** {arb_result['opportunity']}")
                        else:
                            st.info("ℹ️ Belirgin bir arbitraj fırsatı bulunamadı.")
                    else:
                        st.error(f"❌ Hata: {arb_result['error']}")
    
    except ImportError as e:
        st.error(f"❌ Modül yüklenemedi: {e}")
        st.info("💡 Gerekli paketlerin yüklü olduğundan emin olun.")
    except Exception as e:
        st.error(f"❌ Sektörel analiz hatası: {str(e)}")
        st.exception(e)

# Trending Hisseler Sayfası
elif page == "🔥 Trending Hisseler":
    st.header("🔥 Trending Hisseler (Hype Metre)")
    st.write("En çok konuşulan ve popüler olan hisseleri keşfedin.")
    
    try:
        from src.alternative_data import find_trending_stocks, calculate_hype_score
        
        # İzleme listesinden veya manuel giriş
        tickers_input = st.text_area(
            "Analiz Edilecek Hisseler (virgülle ayırın)",
            value="THYAO, EREGL, TUPRS, GARAN, AKBNK, PGSUS, DOAS",
            help="Virgülle ayrılmış hisse kodları"
        )
        
        days_back = st.slider("Analiz Periyodu (Gün)", min_value=1, max_value=30, value=7, key="trending_days")
        
        if st.button("🔥 Trending Analizi Yap", type="primary"):
            with st.spinner("Trending hisseler analiz ediliyor..."):
                tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
                
                if len(tickers) < 1:
                    st.error("❌ En az 1 hisse gerekli!")
                else:
                    trending_df = find_trending_stocks(tickers, days_back=days_back)
                    
                    if not trending_df.empty:
                        st.success("✅ Trending analizi tamamlandı!")
                        
                        # Sıralama
                        trending_df = trending_df.sort_values('hype_score', ascending=False)
                        
                        # Bar grafiği
                        fig = go.Figure(data=[go.Bar(
                            x=trending_df['ticker'],
                            y=trending_df['hype_score'],
                            marker=dict(
                                color=trending_df['hype_score'],
                                colorscale='RdYlGn',
                                showscale=True
                            ),
                            text=[f"{s:.1f}" for s in trending_df['hype_score']],
                            textposition='auto'
                        )])
                        
                        fig.update_layout(
                            title='Hype Skorları (Popülerlik Ölçer)',
                            xaxis_title='Hisse',
                            yaxis_title='Hype Skoru (0-100)',
                            height=400
                        )
                        
                        st.plotly_chart(fig, width='stretch')
                        
                        # Tablo
                        st.subheader("📋 Detaylı Sonuçlar")
                        st.dataframe(trending_df, width='stretch')
                    else:
                        st.warning("⚠️ Trending analizi yapılamadı (forum verisi gerekli).")
                        st.info("💡 Gerçek forum verisi için API entegrasyonu gerekli.")
    
    except ImportError as e:
        st.error(f"❌ Modül yüklenemedi: {e}")
    except Exception as e:
        st.error(f"❌ Trending analiz hatası: {str(e)}")
        st.exception(e)

# Model Eğitimi Sayfası
elif page == "🤖 Model Eğitimi":
    st.header("🤖 ML Modeli Eğitimi")
    st.write("Fiyat yönü tahmini için makine öğrenmesi modeli eğitin.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 Eğitim Parametreleri")
        
        train_ticker = st.text_input(
            "Borsa Kodu",
            value="AAPL",
            key="train_ticker"
        )
        
        period = st.selectbox(
            "Veri Periyodu",
            ["1y", "2y", "3y", "5y"],
            index=1
        )
        
        model_type = st.selectbox(
            "Model Tipi",
            ["random_forest", "xgboost", "gradient_boosting", "logistic"],
            index=0,
            help="Random Forest önerilir (hızlı ve iyi performans)"
        )
        
        future_days = st.slider(
            "Tahmin Periyodu (Gün)",
            min_value=3,
            max_value=10,
            value=5,
            help="Kaç gün sonrasını tahmin edeceğiz"
        )
        
        train_button = st.button("🚀 Model Eğit", type="primary", width='stretch')
    
    with col2:
        st.subheader("📊 Eğitim Sonuçları")
        
        if train_button:
            if not train_ticker:
                st.error("❌ Lütfen borsa kodunu girin!")
            else:
                with st.spinner("🔄 Model eğitiliyor... Bu birkaç dakika sürebilir."):
                    try:
                        predictor = train_price_direction_model(
                            ticker=train_ticker,
                            period=period,
                            model_type=model_type,
                            future_days=future_days,
                            save_path=f"models/price_predictor_{train_ticker.lower().replace('.', '_')}.pkl"
                        )
                        
                        st.success("✅ Model başarıyla eğitildi!")
                        
                        # Feature importance
                        importance_df = predictor.get_feature_importance()
                        
                        st.subheader("📈 En Önemli Feature'lar")
                        st.dataframe(importance_df.head(10), width='stretch')
                        
                        # Feature importance grafiği
                        fig_importance = go.Figure(data=[go.Bar(
                            x=importance_df.head(10)['importance'],
                            y=importance_df.head(10)['feature'],
                            orientation='h',
                            marker_color='lightblue'
                        )])
                        
                        fig_importance.update_layout(
                            title='Top 10 Feature Importance',
                            xaxis_title='Importance',
                            height=400
                        )
                        
                        st.plotly_chart(fig_importance, width='stretch')
                        
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
                        st.exception(e)

# Geçmiş Analizler (Basit bir örnek)
elif page == "📈 Geçmiş Analizler":
    st.header("📈 Geçmiş Analizler")
    st.info("Bu özellik geliştirilme aşamasında. Gelecekte eğitilmiş modellerin listesi burada görünecek.")
    
    # Eğitilmiş modelleri listele
    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.pkl"))
        if model_files:
            st.subheader("🤖 Eğitilmiş Modeller")
            for model_file in model_files:
                st.write(f"✅ {model_file.name}")
        else:
            st.write("Henüz eğitilmiş model yok.")

# Hakkında Sayfası
elif page == "ℹ️ Hakkında":
    st.header("ℹ️ Hakkında")
    
    st.markdown("""
    ### 📊 Finansal Analiz ve Haber Sentiment Analizi Sistemi
    
    Bu uygulama, şirketler hakkında kapsamlı finansal analiz ve haber sentiment analizi yapar.
    
    #### 🎯 Özellikler
    
    - **📰 Haber Analizi**: İnternetten şirketle ilgili haberleri toplar ve sentiment analizi yapar
    - **💰 Finansal Analiz**: Fiyat verilerini ve teknik göstergeleri analiz eder
    - **🎯 Skorlama**: Haber ve finansal verileri birleştirerek 0-100 arası skor üretir
    - **🤖 ML Tahmini**: Eğitilmiş modellerle fiyat yönü tahmini yapar
    
    #### 🚀 Kullanım
    
    1. **Ana Sayfa**: Şirket adı ve borsa kodunu girin, analiz yapın
    2. **Model Eğitimi**: Fiyat yönü tahmini için ML modeli eğitin
    3. **Sonuçlar**: Detaylı raporlar ve görselleştirmeleri inceleyin
    
    #### ⚠️ Önemli Uyarı
    
    Bu sistem sadece **eğitim ve araştırma** amaçlıdır. Yatırım tavsiyesi değildir.
    Yatırım kararlarınızı kendi araştırmanız ve uzman görüşü ile alın.
    
    #### 📚 Teknolojiler
    
    - Python
    - Streamlit (Web Arayüzü)
    - Transformers (NLP)
    - Scikit-learn, XGBoost (ML)
    - Plotly (Görselleştirme)
    - yfinance (Finansal Veri)
    
    #### 📖 Dokümantasyon
    
    Detaylı bilgi için proje klasöründeki README.md dosyasına bakın.
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "⚠️ Bu sistem sadece eğitim amaçlıdır. Yatırım tavsiyesi değildir."
    "</div>",
    unsafe_allow_html=True
)

