"""
Sektör Rotasyonu Analizi Modülü

Paranın hangi sektörden çıkıp hangisine girdiğini gösteren dinamik bir akış şeması (Sankey Diagram).
"""

import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from src.logger_config import setup_logger

logger = setup_logger(__name__)


# BIST Sektör Eşleştirmeleri
BIST_SECTORS = {
    'THYAO': 'Havacılık',
    'PGSUS': 'Havacılık',
    'TAVHL': 'Havacılık',
    'GARAN': 'Bankacılık',
    'AKBNK': 'Bankacılık',
    'ISCTR': 'Bankacılık',
    'YKBNK': 'Bankacılık',
    'TUPRS': 'Petrol',
    'PETKM': 'Petrol',
    'EREGL': 'Demir-Çelik',
    'KRDMD': 'Demir-Çelik',
    'CEMTS': 'Demir-Çelik',
    'SASA': 'Tekstil',
    'KLKIM': 'Tekstil',
    'YUNSA': 'Tekstil',
    'BIMAS': 'Perakende',
    'MIGRS': 'Perakende',
    'SOKM': 'Perakende',
    'KCHOL': 'Otomotiv',
    'TOASO': 'Otomotiv',
    'FROTO': 'Otomotiv',
    'ARCLK': 'Beyaz Eşya',
    'VESTEL': 'Beyaz Eşya',
    'BFREN': 'Beyaz Eşya',
    'THYAO': 'Havacılık',
    'PGSUS': 'Havacılık',
    'TAVHL': 'Havacılık',
}


def get_sector_for_ticker(ticker: str) -> Optional[str]:
    """
    Bir hisse için sektör bilgisini döndürür.
    
    Parametreler:
    ------------
    ticker : str
        Hisse kodu
    
    Döndürür:
    --------
    str veya None
        Sektör adı
    """
    ticker_clean = ticker.replace('.IS', '').upper()
    return BIST_SECTORS.get(ticker_clean)


def calculate_sector_flows(
    tickers: List[str],
    period: str = "1mo"
) -> Dict:
    """
    Sektörler arası para akışını hesaplar.
    
    Parametreler:
    ------------
    tickers : list
        Analiz edilecek hisse kodları listesi
    period : str
        Zaman periyodu (örn: "1mo", "3mo", "6mo")
    
    Döndürür:
    --------
    dict
        Sektör akış verileri (Sankey diagram için)
    """
    try:
        from src.data_collection import get_price_data
        
        sector_data = {}
        
        for ticker in tickers:
            sector = get_sector_for_ticker(ticker)
            if not sector:
                continue
            
            try:
                price_df = get_price_data(ticker, period=period)
                if price_df.empty:
                    continue
                
                # Fiyat değişimi hesapla
                if len(price_df) >= 2:
                    start_price = price_df.iloc[0]['close']
                    end_price = price_df.iloc[-1]['close']
                    price_change = ((end_price - start_price) / start_price) * 100
                    
                    # Hacim değişimi
                    avg_volume_start = price_df.iloc[:len(price_df)//2]['volume'].mean()
                    avg_volume_end = price_df.iloc[len(price_df)//2:]['volume'].mean()
                    volume_change = ((avg_volume_end - avg_volume_start) / avg_volume_start) * 100 if avg_volume_start > 0 else 0
                    
                    if sector not in sector_data:
                        sector_data[sector] = {
                            'tickers': [],
                            'price_changes': [],
                            'volume_changes': [],
                            'total_market_cap_change': 0.0
                        }
                    
                    sector_data[sector]['tickers'].append(ticker)
                    sector_data[sector]['price_changes'].append(price_change)
                    sector_data[sector]['volume_changes'].append(volume_change)
                    
            except Exception as e:
                logger.warning(f"{ticker} için veri çekilemedi: {e}")
                continue
        
        # Sektör performansını hesapla
        sector_performance = {}
        for sector, data in sector_data.items():
            avg_price_change = sum(data['price_changes']) / len(data['price_changes']) if data['price_changes'] else 0
            avg_volume_change = sum(data['volume_changes']) / len(data['volume_changes']) if data['volume_changes'] else 0
            
            # Performans skoru (fiyat + hacim değişimi)
            performance_score = (avg_price_change * 0.7) + (avg_volume_change * 0.3)
            
            sector_performance[sector] = {
                'performance_score': performance_score,
                'avg_price_change': avg_price_change,
                'avg_volume_change': avg_volume_change,
                'ticker_count': len(data['tickers'])
            }
        
        return {
            'sector_data': sector_data,
            'sector_performance': sector_performance,
            'period': period
        }
        
    except Exception as e:
        logger.error(f"Sektör akışı hesaplanırken hata: {e}")
        return {
            'sector_data': {},
            'sector_performance': {},
            'period': period,
            'error': str(e)
        }


def create_sankey_diagram(
    sector_performance: Dict,
    top_n: int = 5
) -> go.Figure:
    """
    Sektör rotasyonu için Sankey diagram oluşturur.
    
    Parametreler:
    ------------
    sector_performance : dict
        Sektör performans verileri
    top_n : int
        En iyi ve en kötü N sektörü göster
    
    Döndürür:
    --------
    plotly.graph_objects.Figure
        Sankey diagram
    """
    if not sector_performance:
        # Boş diagram
        fig = go.Figure()
        fig.add_annotation(
            text="Veri bulunamadı",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Sektörleri performansa göre sırala
    sorted_sectors = sorted(
        sector_performance.items(),
        key=lambda x: x[1].get('performance_score', 0),
        reverse=True
    )
    
    # En iyi ve en kötü sektörleri al
    top_sectors = sorted_sectors[:top_n]
    bottom_sectors = sorted_sectors[-top_n:] if len(sorted_sectors) > top_n else []
    
    # Kaynak ve hedef sektörleri belirle
    # Negatif performanslı sektörlerden pozitif performanslı sektörlere akış
    source_sectors = [s[0] for s in bottom_sectors if s[1].get('performance_score', 0) < 0]
    target_sectors = [s[0] for s in top_sectors if s[1].get('performance_score', 0) > 0]
    
    if not source_sectors or not target_sectors:
        # Basit bar chart göster
        fig = go.Figure()
        sectors = [s[0] for s in sorted_sectors]
        scores = [s[1].get('performance_score', 0) for s in sorted_sectors]
        
        colors = ['red' if s < 0 else 'green' for s in scores]
        
        fig.add_trace(go.Bar(
            x=sectors,
            y=scores,
            marker_color=colors,
            text=[f"{s:.1f}%" for s in scores],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Sektör Performansı",
            xaxis_title="Sektör",
            yaxis_title="Performans Skoru (%)",
            height=500
        )
        
        return fig
    
    # Sankey diagram için label'lar
    labels = source_sectors + target_sectors + ['Para Çıkışı', 'Para Girişi']
    
    # Source ve target indeksleri
    source_indices = [labels.index(s) for s in source_sectors]
    target_indices = [labels.index(t) for t in target_sectors]
    
    # Değerler (akış miktarları)
    values = []
    for source in source_sectors:
        source_perf = abs(sector_performance[source].get('performance_score', 0))
        for target in target_sectors:
            target_perf = sector_performance[target].get('performance_score', 0)
            # Akış miktarı = kaynak sektörün negatif performansı * hedef sektörün pozitif performansı
            flow_value = source_perf * target_perf / 100
            values.append(flow_value)
    
    # Sankey diagram oluştur
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=["red"] * len(source_sectors) + ["green"] * len(target_sectors) + ["gray", "gray"]
        ),
        link=dict(
            source=source_indices * len(target_sectors),
            target=[labels.index(t) for t in target_sectors] * len(source_sectors),
            value=values,
            color=["rgba(255,0,0,0.3)"] * len(values)
        )
    )])
    
    fig.update_layout(
        title="Sektör Rotasyonu - Para Akışı",
        font_size=12,
        height=600
    )
    
    return fig


def get_sector_rotation_analysis(tickers: List[str], period: str = "1mo") -> Dict:
    """
    Sektör rotasyonu analizi yapar ve görselleştirme hazırlar.
    
    Parametreler:
    ------------
    tickers : list
        Analiz edilecek hisse kodları listesi
    period : str
        Zaman periyodu
    
    Döndürür:
    --------
    dict
        Analiz sonuçları ve görselleştirme
    """
    flows = calculate_sector_flows(tickers, period)
    
    if flows.get('error'):
        return {
            'success': False,
            'error': flows['error']
        }
    
    sector_performance = flows.get('sector_performance', {})
    
    # Sankey diagram oluştur
    sankey_fig = create_sankey_diagram(sector_performance)
    
    # Özet mesaj
    if sector_performance:
        best_sector = max(sector_performance.items(), key=lambda x: x[1].get('performance_score', 0))
        worst_sector = min(sector_performance.items(), key=lambda x: x[1].get('performance_score', 0))
        
        summary = f"""
**Sektör Rotasyonu Analizi ({period})**

🏆 **En İyi Performans:** {best_sector[0]} ({best_sector[1].get('performance_score', 0):.2f}%)
📉 **En Kötü Performans:** {worst_sector[0]} ({worst_sector[1].get('performance_score', 0):.2f}%)

**Trend:** Para {worst_sector[0]} sektöründen çıkıp {best_sector[0]} sektörüne akıyor.
"""
    else:
        summary = "Sektör rotasyonu analizi yapılamadı."
    
    return {
        'success': True,
        'flows': flows,
        'sankey_figure': sankey_fig,
        'summary': summary,
        'sector_performance': sector_performance
    }


if __name__ == "__main__":
    # Test
    print("=== Sektör Rotasyonu Test ===\n")
    
    test_tickers = ['THYAO', 'PGSUS', 'GARAN', 'AKBNK', 'TUPRS', 'EREGL']
    
    analysis = get_sector_rotation_analysis(test_tickers, period="1mo")
    
    if analysis.get('success'):
        print(analysis['summary'])
        print("\nSektör Performansları:")
        for sector, perf in analysis['sector_performance'].items():
            print(f"  {sector}: {perf.get('performance_score', 0):.2f}%")
    else:
        print(f"Hata: {analysis.get('error')}")

