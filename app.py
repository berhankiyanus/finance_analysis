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
if NEWS_API_KEY is None:
    project_root = Path(__file__).parent
    env_path = project_root / '.env'
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
    ["🏠 Ana Sayfa - Analiz", "🤖 Model Eğitimi", "📈 Geçmiş Analizler", "ℹ️ Hakkında"]
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
                        # Analiz yap
                        results = analyze_company(
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
                            st.write(f"**Yön Tahmini:** {direction_emoji.get(pred.get('direction', 'neutral'), '❓')} "
                                   f"{pred.get('direction', 'neutral').upper()} "
                                   f"({pred.get('confidence', 0):.1%} güven)")
                        
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
                        else:
                            # Eski rapor formatı (geriye dönük uyumluluk)
                            with st.expander("📄 Detaylı Rapor"):
                                st.text(results.get('summary', 'Rapor mevcut değil.'))
                        
                        # Grafikler
                        st.subheader("📈 Görselleştirmeler")
                        
                        # Fiyat grafiği
                        if not results['price_df'].empty:
                            price_df = results['price_df']
                            
                            fig = make_subplots(
                                rows=2, cols=1,
                                subplot_titles=('Fiyat Hareketi', 'Hacim'),
                                vertical_spacing=0.1,
                                row_heights=[0.7, 0.3]
                            )
                            
                            # Fiyat çizgisi
                            fig.add_trace(
                                go.Scatter(
                                    x=price_df['date'],
                                    y=price_df['close'],
                                    mode='lines',
                                    name='Kapanış Fiyatı',
                                    line=dict(color='#1f77b4', width=2)
                                ),
                                row=1, col=1
                            )
                            
                            # Hareketli ortalamalar
                            if 'ma_20' in price_df.columns:
                                fig.add_trace(
                                    go.Scatter(
                                        x=price_df['date'],
                                        y=price_df['ma_20'],
                                        mode='lines',
                                        name='MA 20',
                                        line=dict(color='orange', width=1, dash='dash')
                                    ),
                                    row=1, col=1
                                )
                            
                            # Hacim
                            fig.add_trace(
                                go.Bar(
                                    x=price_df['date'],
                                    y=price_df['volume'],
                                    name='Hacim',
                                    marker_color='lightblue'
                                ),
                                row=2, col=1
                            )
                            
                            fig.update_layout(
                                title=f'{company_name} ({ticker}) - Fiyat ve Hacim',
                                height=600,
                                showlegend=True
                            )
                            
                            fig.update_xaxes(title_text="Tarih", row=2, col=1)
                            fig.update_yaxes(title_text="Fiyat ($)", row=1, col=1)
                            fig.update_yaxes(title_text="Hacim", row=2, col=1)
                            
                            st.plotly_chart(fig, width='stretch')
                        
                        # Haber sentiment dağılımı
                        if not results['news_df'].empty and 'sentiment_class' in results['news_df'].columns:
                            news_df = results['news_df']
                            sentiment_counts = news_df['sentiment_class'].value_counts()
                            
                            fig_sentiment = go.Figure(data=[go.Bar(
                                x=sentiment_counts.index,
                                y=sentiment_counts.values,
                                marker_color=['green', 'red', 'gray'],
                                text=sentiment_counts.values,
                                textposition='auto'
                            )])
                            
                            fig_sentiment.update_layout(
                                title='Haber Sentiment Dağılımı',
                                xaxis_title='Sentiment Sınıfı',
                                yaxis_title='Haber Sayısı',
                                height=300
                            )
                            
                            st.plotly_chart(fig_sentiment, width='stretch')
                            
                            # Haber listesi
                            with st.expander("📰 Haberler"):
                                for idx, row in news_df.head(10).iterrows():
                                    # Güvenli kolon erişimi
                                    title = row.get('title', 'Başlık yok')
                                    sentiment_class = row.get('sentiment_class', 'neutral')
                                    sentiment_confidence = row.get('sentiment_confidence', 0.0)
                                    source = row.get('source', 'Unknown')
                                    
                                    emoji = "🟢" if sentiment_class == 'positive' else \
                                           "🔴" if sentiment_class == 'negative' else "🟡"
                                    st.write(f"{emoji} **{title}**")
                                    st.caption(f"Sentiment: {sentiment_class} ({sentiment_confidence:.1%}) | "
                                             f"Kaynak: {source}")
                                    st.write("---")
                        
                        # Skor karşılaştırması
                        scores = {
                            'Sentiment': results['sentiment_score'],
                            'Finansal': results['financial_score'],
                            'Genel Durum': results['overall_score']
                        }
                        
                        fig_scores = go.Figure(data=[go.Bar(
                            x=list(scores.keys()),
                            y=list(scores.values()),
                            marker_color=['lightblue', 'lightgreen', 'gold'],
                            text=[f"{v:.1f}" for v in scores.values()],
                            textposition='auto'
                        )])
                        
                        fig_scores.update_layout(
                            title='Skor Karşılaştırması',
                            yaxis_title='Skor (0-100)',
                            yaxis=dict(range=[0, 100]),
                            height=300
                        )
                        
                        st.plotly_chart(fig_scores, width='stretch')
                        
                    except Exception as e:
                        st.error(f"❌ Hata oluştu: {str(e)}")
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

