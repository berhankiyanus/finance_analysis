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
from dotenv import load_dotenv

# Proje kök dizinini path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

# API Key'i yükle - önce Streamlit secrets'tan, sonra .env'den
NEWS_API_KEY = None

# 1. Streamlit Cloud secrets'tan dene (web ortamı için)
try:
    if hasattr(st, 'secrets') and 'NEWS_API_KEY' in st.secrets:
        NEWS_API_KEY = st.secrets['NEWS_API_KEY']
        os.environ['NEWS_API_KEY'] = NEWS_API_KEY
        st.sidebar.success("✅ API Key Streamlit secrets'tan yüklendi")
except:
    pass

# 2. .env dosyasından dene (local için)
# env_path'i genel olarak tanımla (hem NEWS_API_KEY hem GEMINI_API_KEY için kullanılacak)
project_root = Path(__file__).parent
env_path = project_root / '.env'

if NEWS_API_KEY is None:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        NEWS_API_KEY = os.getenv('NEWS_API_KEY')
        if NEWS_API_KEY:
            st.sidebar.success("✅ API Key .env dosyasından yüklendi")
        else:
            st.sidebar.warning("⚠️ .env dosyası var ama NEWS_API_KEY bulunamadı")
    else:
        st.sidebar.warning("⚠️ .env dosyası bulunamadı")

# 3. Environment variable'dan dene (genel)
if NEWS_API_KEY is None:
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    if NEWS_API_KEY:
        st.sidebar.info("ℹ️ API Key environment variable'dan yüklendi")

# Son kontrol
if NEWS_API_KEY is None:
    st.sidebar.error("❌ NEWS_API_KEY bulunamadı! Lütfen Streamlit secrets veya .env dosyasına ekleyin.")
else:
    # API key'i environment'a set et
    os.environ['NEWS_API_KEY'] = NEWS_API_KEY

# Gemini API Key'i yükle
GEMINI_API_KEY = None

# 1. Streamlit Cloud secrets'tan dene (web ortamı için)
try:
    if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
        GEMINI_API_KEY = st.secrets['GEMINI_API_KEY']
        os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
        st.sidebar.success("✅ Gemini API Key Streamlit secrets'tan yüklendi")
except:
    pass

# 2. .env dosyasından dene (local için)
if GEMINI_API_KEY is None:
    if env_path.exists():
        # .env dosyasını yükle (eğer daha önce yüklenmediyse)
        load_dotenv(dotenv_path=env_path, override=False)
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        if GEMINI_API_KEY:
            st.sidebar.success("✅ Gemini API Key .env dosyasından yüklendi")
        else:
            st.sidebar.info("ℹ️ Gemini API Key bulunamadı (opsiyonel - FinBERT kullanılacak)")

# 3. Environment variable'dan dene (genel)
if GEMINI_API_KEY is None:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        st.sidebar.info("ℹ️ Gemini API Key environment variable'dan yüklendi")

# Son kontrol
if GEMINI_API_KEY:
    # API key'i environment'a set et
    os.environ['GEMINI_API_KEY'] = GEMINI_API_KEY
else:
    st.sidebar.info("ℹ️ Gemini API Key bulunamadı. Sadece FinBERT modeli kullanılacak.")
    st.sidebar.info("   💡 Daha iyi sentiment analizi için Gemini API key ekleyin: https://makersuite.google.com/app/apikey")

from src.main import analyze_company
from src.prediction_model import train_price_direction_model, PriceDirectionPredictor
from src.data_collection import get_price_data, get_fundamentals

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
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Ana başlık
st.markdown('<h1 class="main-header">📊 Finansal Analiz ve Haber Sentiment Analizi</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Navigasyon
st.sidebar.title("🎯 Menü")
page = st.sidebar.radio(
    "Sayfa Seçin",
    ["🏠 Ana Sayfa - Analiz", "📋 İzleme Listesi", "💼 Portföy Optimizasyonu", "📊 Sektörel Analiz", "🔥 Trending Hisseler", "🤖 Model Eğitimi", "📈 Geçmiş Analizler", "ℹ️ Hakkında"]
)

# Ana Sayfa - Analiz
if page == "🏠 Ana Sayfa - Analiz":
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
                        
                        # API key kontrolü ve uyarı - dummy veri kontrolü
                        news_df = results.get('news_df', pd.DataFrame())
                        news_count = results.get('news_count', 0)
                        is_dummy_data = False
                        
                        # Dummy veri kontrolü: Eğer haberler varsa ve tüm haberlerin kaynağı "Dummy News" ise
                        if not news_df.empty and 'source' in news_df.columns:
                            unique_sources = news_df['source'].unique()
                            if len(unique_sources) == 1 and 'Dummy News' in unique_sources:
                                is_dummy_data = True
                        elif news_df.empty and news_count == 0:
                            # Boş DataFrame ve 0 haber sayısı
                            # Eğer API key yoksa, dummy data kullanılmış olabilir
                            # Eğer API key varsa, API'den haber bulunamadı demektir (dummy data değil)
                            if NEWS_API_KEY is None:
                                is_dummy_data = True
                        
                        # Mesajları göster
                        if is_dummy_data:
                            st.warning("⚠️ **Dikkat:** Dummy (test) verisi kullanılıyor. NEWS_API_KEY bulunamadı veya API isteği başarısız oldu. Gerçek haberler için NewsAPI key ekleyin ve uygulamayı yeniden başlatın.")
                        elif news_count == 0 and NEWS_API_KEY is not None:
                            st.warning("⚠️ **Uyarı:** API key çalışıyor ancak seçilen periyotta haber bulunamadı. "
                                     "**Çözüm önerileri:**\n"
                                     "1. Şirket adını İngilizce olarak deneyin (örn: 'Apple' yerine 'Apple Inc.')\n"
                                     "2. Ticker sembolü kullanın (örn: 'AAPL')\n"
                                     "3. Haber analizi periyodunu artırın (örn: 7 gün yerine 14 gün)\n"
                                     "4. Farklı bir şirket adı deneyin")
                        elif news_count > 0 and news_count <= 3:
                            st.info("ℹ️ **Bilgi:** Çok az haber bulundu. Bu, seçilen periyotta gerçekten az haber olmasından kaynaklanıyor olabilir. Daha fazla haber için periyodu artırabilirsiniz.")
                        
                        # Skorlar
                        col_score1, col_score2, col_score3 = st.columns(3)
                        
                        with col_score1:
                            st.metric(
                                "📰 Sentiment Skoru",
                                f"{results['sentiment_score']:.1f}/100",
                                delta=f"{results['sentiment_score'] - 50:.1f}"
                            )
                        
                        with col_score2:
                            st.metric(
                                "💰 Finansal Skor",
                                f"{results['financial_score']:.1f}/100",
                                delta=f"{results['financial_score'] - 50:.1f}"
                            )
                        
                        with col_score3:
                            score_color = "normal"
                            if results['overall_score'] >= 70:
                                score_color = "normal"
                            elif results['overall_score'] < 30:
                                score_color = "inverse"
                            
                            st.metric(
                                "🎯 Genel Durum Skoru",
                                f"{results['overall_score']:.1f}/100",
                                delta=f"{results['overall_score'] - 50:.1f}",
                                delta_color=score_color
                            )
                        
                        # Yorum
                        interpretation = results['interpretation']
                        st.info(f"**{interpretation['category']}** - {interpretation['risk_level']}")
                        st.write(interpretation['recommendation'])
                        
                        # Yön tahmini
                        if 'direction_prediction' in results:
                            pred = results['direction_prediction']
                            direction_emoji = {"up": "📈", "down": "📉", "neutral": "➡️"}
                            direction_tr = {"up": "YÜKSELİŞ", "down": "DÜŞÜŞ", "neutral": "NÖTR"}
                            
                            st.write(f"**Yön Tahmini:** {direction_emoji.get(pred.get('direction', 'neutral'), '❓')} "
                                   f"{direction_tr.get(pred.get('direction', 'neutral'), 'NÖTR')} "
                                   f"({pred.get('confidence', 0):.1%} güven)")
                            
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
                                        
                                        with st.expander("🔍 Model Açıklaması (SHAP)", expanded=False):
                                            explanation_text = format_explanation_for_display(shap_result, pred)
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
                            
                            # Markdown raporu göster
                            st.markdown(detailed_report['summary'])
                            
                            # En önemli haberler
                            if detailed_report.get('news_analysis'):
                                st.subheader("📰 En Etkili Haberler")
                                for news in detailed_report['news_analysis'][:5]:
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
                            
                            # Gemini AI Analist Raporu (eğer varsa)
                            if detailed_report.get('gemini_analyst_report'):
                                st.subheader("🤖 AI Analist Raporu (Gemini)")
                                st.info("💡 Bu rapor, Gemini AI tarafından otomatik olarak oluşturulmuştur.")
                                st.markdown(detailed_report['gemini_analyst_report'])
                                
                                # Haber özetleri
                                if detailed_report.get('hisse_news_summary'):
                                    with st.expander("📰 Hisse Bazlı Haber Özeti"):
                                        st.markdown(detailed_report['hisse_news_summary'])
                                
                                if detailed_report.get('piyasa_news_summary'):
                                    with st.expander("🌐 Piyasa Geneli Haber Özeti"):
                                        st.markdown(detailed_report['piyasa_news_summary'])
                        else:
                            # Eski rapor formatı (geriye dönük uyumluluk)
                            with st.expander("📄 Detaylı Rapor"):
                                st.text(results.get('summary', 'Rapor mevcut değil.'))
                        
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
                                
                                st.plotly_chart(fig, use_container_width=True, config={
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
                                    
                                    st.plotly_chart(fig_candle, use_container_width=True, config={
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
                                
                                st.plotly_chart(tech_fig, use_container_width=True, config={
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
                                        
                                        st.plotly_chart(fig_sentiment, use_container_width=True)
                                    
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
                                            
                                            st.plotly_chart(fig_timeseries, use_container_width=True)
                                    
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
                                        
                                        st.plotly_chart(fig_confidence, use_container_width=True)
                                else:
                                    st.info("Haber analizi için veri bulunamadı.")
                        
                        # Haber listesi (ayrı bir bölüm)
                        if not results['news_df'].empty and 'sentiment_class' in results['news_df'].columns:
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
                            
                            st.plotly_chart(fig_scores, use_container_width=True)
                        
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
                            
                            st.plotly_chart(fig_radar, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"❌ Hata oluştu: {str(e)}")
                        st.exception(e)

# İzleme Listesi Sayfası
elif page == "📋 İzleme Listesi":
    st.header("📋 İzleme Listesi")
    st.write("Takip etmek istediğiniz hisse senetlerini ekleyin ve yönetin.")
    
    try:
        from src.firestore_watchlist import get_firestore_client, save_watchlist, get_watchlist
        
        # Basit kullanıcı ID (gerçek uygulamada authentication olmalı)
        user_id = st.text_input("Kullanıcı ID", value="default_user", help="Geçici kullanıcı ID (gerçek uygulamada oturum açma olmalı)")
        
        db = get_firestore_client()
        
        if db:
            # Mevcut watchlist'i yükle
            current_watchlist = get_watchlist(user_id) or []
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 İzleme Listesi")
                if current_watchlist:
                    watchlist_df = pd.DataFrame({
                        'Ticker': current_watchlist,
                        'Durum': ['✅ Aktif'] * len(current_watchlist)
                    })
                    st.dataframe(watchlist_df, use_container_width=True)
                else:
                    st.info("📝 Henüz izleme listesi oluşturulmamış. Sağdaki formdan ekleyin.")
            
            with col2:
                st.subheader("➕ Hisse Ekle")
                new_ticker = st.text_input("Borsa Kodu", value="", placeholder="THYAO, AAPL, ...", key="new_ticker")
                
                if st.button("➕ Ekle", type="primary"):
                    if new_ticker:
                        new_ticker = new_ticker.upper().strip()
                        if new_ticker not in current_watchlist:
                            current_watchlist.append(new_ticker)
                            if save_watchlist(user_id, current_watchlist):
                                st.success(f"✅ {new_ticker} eklendi!")
                                st.rerun()
                            else:
                                st.error("❌ Kaydetme hatası!")
                        else:
                            st.warning(f"⚠️ {new_ticker} zaten listede!")
                    else:
                        st.warning("⚠️ Lütfen bir ticker girin!")
                
                # Silme
                if current_watchlist:
                    st.subheader("🗑️ Hisse Sil")
                    ticker_to_remove = st.selectbox("Silinecek Ticker", current_watchlist, key="remove_ticker")
                    if st.button("🗑️ Sil", type="secondary"):
                        current_watchlist.remove(ticker_to_remove)
                        if save_watchlist(user_id, current_watchlist):
                            st.success(f"✅ {ticker_to_remove} silindi!")
                            st.rerun()
                        else:
                            st.error("❌ Silme hatası!")
        else:
            st.warning("⚠️ Firestore bağlantısı kurulamadı. İzleme listesi özelliği kullanılamıyor.")
            st.info("💡 Firestore kullanmak için Google Cloud credentials ayarlayın.")
            
            # Basit local watchlist (Firestore yoksa)
            if 'local_watchlist' not in st.session_state:
                st.session_state.local_watchlist = []
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📊 İzleme Listesi (Local)")
                if st.session_state.local_watchlist:
                    watchlist_df = pd.DataFrame({
                        'Ticker': st.session_state.local_watchlist,
                        'Durum': ['✅ Aktif'] * len(st.session_state.local_watchlist)
                    })
                    st.dataframe(watchlist_df, use_container_width=True)
                else:
                    st.info("📝 Henüz izleme listesi oluşturulmamış.")
            
            with col2:
                st.subheader("➕ Hisse Ekle")
                new_ticker = st.text_input("Borsa Kodu", value="", placeholder="THYAO, AAPL, ...", key="new_ticker_local")
                
                if st.button("➕ Ekle", type="primary", key="add_local"):
                    if new_ticker:
                        new_ticker = new_ticker.upper().strip()
                        if new_ticker not in st.session_state.local_watchlist:
                            st.session_state.local_watchlist.append(new_ticker)
                            st.success(f"✅ {new_ticker} eklendi!")
                            st.rerun()
                        else:
                            st.warning(f"⚠️ {new_ticker} zaten listede!")
                
                if st.session_state.local_watchlist:
                    ticker_to_remove = st.selectbox("Silinecek Ticker", st.session_state.local_watchlist, key="remove_ticker_local")
                    if st.button("🗑️ Sil", type="secondary", key="remove_local"):
                        st.session_state.local_watchlist.remove(ticker_to_remove)
                        st.success(f"✅ {ticker_to_remove} silindi!")
                        st.rerun()
    
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
                step=0.1
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
                                    st.warning(f"⚠️ **Not:** Maksimum Sharpe optimizasyonu yapılamadı (beklenen getiriler risksiz faiz oranından düşük). Minimum volatilite optimizasyonu kullanıldı.")
                                
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
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
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
                                
                                st.plotly_chart(fig_pie, use_container_width=True)
                                
                                # Tablo
                                st.subheader("📋 Detaylı Ağırlıklar")
                                st.dataframe(weights_df, use_container_width=True)
                    
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
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔗 İki Hisse Korelasyonu", "📈 Sektör Korelasyon Matrisi", "🔄 Sektör Rotasyonu", "💰 Arbitraj Fırsatları"])
        
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
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tablo
                        st.subheader("📋 Detaylı Matris")
                        st.dataframe(corr_matrix, use_container_width=True)
        
        with tab3:
            st.subheader("🔄 Sektör Rotasyonu")
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
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tablo
                        st.subheader("📋 Detaylı Sonuçlar")
                        st.dataframe(rotation_df, use_container_width=True)
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
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tablo
                        st.subheader("📋 Detaylı Sonuçlar")
                        st.dataframe(trending_df, use_container_width=True)
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

