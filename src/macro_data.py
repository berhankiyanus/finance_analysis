"""
Makroekonomik Veri Toplama Modülü

Bu modül, piyasayı etkileyen makroekonomik verileri toplar.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance yüklü değil. Makroekonomik veriler çekilemeyecek.")


def get_macroeconomic_data(country: str = "US") -> Dict:
    """
    Makroekonomik verileri çeker (faiz oranları, enflasyon, vb.).
    
    Parametreler:
    ------------
    country : str
        Ülke kodu (varsayılan: "US")
    
    Döndürür:
    --------
    dict
        Makroekonomik göstergeler
    """
    
    if not YFINANCE_AVAILABLE:
        return {}
    
    macro_data = {}
    
    try:
        # ABD için makroekonomik veriler (yfinance ile)
        if country == "US":
            # 10 Yıllık Hazine Tahvili Getirisi (risk-free rate)
            try:
                tnx = yf.Ticker("^TNX")
                tnx_hist = tnx.history(period="1mo")
                if not tnx_hist.empty:
                    macro_data['treasury_10y'] = float(tnx_hist['Close'].iloc[-1])
                    macro_data['treasury_10y_change'] = float((tnx_hist['Close'].iloc[-1] - tnx_hist['Close'].iloc[0]) / tnx_hist['Close'].iloc[0] * 100)
            except:
                pass
            
            # DXY (Dolar Endeksi)
            try:
                dxy = yf.Ticker("DX-Y.NYB")
                dxy_hist = dxy.history(period="1mo")
                if not dxy_hist.empty:
                    macro_data['dollar_index'] = float(dxy_hist['Close'].iloc[-1])
                    macro_data['dollar_index_change'] = float((dxy_hist['Close'].iloc[-1] - dxy_hist['Close'].iloc[0]) / dxy_hist['Close'].iloc[0] * 100)
            except:
                pass
            
            # VIX (Volatilite Endeksi)
            try:
                vix = yf.Ticker("^VIX")
                vix_hist = vix.history(period="1mo")
                if not vix_hist.empty:
                    macro_data['vix'] = float(vix_hist['Close'].iloc[-1])
                    macro_data['vix_change'] = float((vix_hist['Close'].iloc[-1] - vix_hist['Close'].iloc[0]) / vix_hist['Close'].iloc[0] * 100)
            except:
                pass
        
        # Türkiye için (BIST 100, USD/TRY)
        elif country == "TR":
            # BIST 100
            try:
                bist = yf.Ticker("XU100.IS")
                bist_hist = bist.history(period="1mo")
                if not bist_hist.empty:
                    macro_data['bist100'] = float(bist_hist['Close'].iloc[-1])
                    macro_data['bist100_change'] = float((bist_hist['Close'].iloc[-1] - bist_hist['Close'].iloc[0]) / bist_hist['Close'].iloc[0] * 100)
            except:
                pass
            
            # USD/TRY
            try:
                usdtry = yf.Ticker("USDTRY=X")
                usdtry_hist = usdtry.history(period="1mo")
                if not usdtry_hist.empty:
                    macro_data['usd_try'] = float(usdtry_hist['Close'].iloc[-1])
                    macro_data['usd_try_change'] = float((usdtry_hist['Close'].iloc[-1] - usdtry_hist['Close'].iloc[0]) / usdtry_hist['Close'].iloc[0] * 100)
            except:
                pass
        
        if macro_data:
            print(f"✅ {len(macro_data)} makroekonomik gösterge bulundu.")
        else:
            print("⚠️  Makroekonomik veri bulunamadı.")
        
        return macro_data
        
    except Exception as e:
        print(f"⚠️  Makroekonomik veri çekilirken hata: {e}")
        return {}


def get_sector_performance() -> Dict:
    """
    Sektör performans verilerini çeker.
    
    Döndürür:
    --------
    dict
        Sektör performans göstergeleri
    """
    
    if not YFINANCE_AVAILABLE:
        return {}
    
    sector_data = {}
    
    try:
        # Sektör ETF'leri (örnek)
        sector_etfs = {
            'technology': 'XLK',
            'financials': 'XLF',
            'healthcare': 'XLV',
            'consumer_discretionary': 'XLY',
            'communication': 'XLC',
            'industrials': 'XLI',
            'consumer_staples': 'XLP',
            'energy': 'XLE',
            'utilities': 'XLU',
            'real_estate': 'XLRE',
            'materials': 'XLB'
        }
        
        for sector, ticker in sector_etfs.items():
            try:
                etf = yf.Ticker(ticker)
                hist = etf.history(period="1mo")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[0])
                    change = (current_price - prev_price) / prev_price * 100
                    
                    sector_data[sector] = {
                        'price': current_price,
                        'change_1m': change
                    }
            except:
                continue
        
        if sector_data:
            print(f"✅ {len(sector_data)} sektör performans verisi bulundu.")
        
        return sector_data
        
    except Exception as e:
        print(f"⚠️  Sektör performans verisi çekilirken hata: {e}")
        return {}


if __name__ == "__main__":
    print("=== Makroekonomik Veri Modülü Test ===\n")
    
    # ABD makro verileri
    print("1. ABD Makroekonomik Veriler:")
    us_macro = get_macroeconomic_data("US")
    print(us_macro)
    print()
    
    # Türkiye makro verileri
    print("2. Türkiye Makroekonomik Veriler:")
    tr_macro = get_macroeconomic_data("TR")
    print(tr_macro)
    print()
    
    # Sektör performansı
    print("3. Sektör Performansı:")
    sectors = get_sector_performance()
    print(sectors)

