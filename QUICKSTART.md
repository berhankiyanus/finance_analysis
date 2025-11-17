# Hızlı Başlangıç Kılavuzu

Bu kılavuz, projeyi hızlıca çalıştırmanız için temel adımları içerir.

## 1. Kurulum (5 dakika)

```bash
# Virtual environment oluştur ve aktifleştir
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Paketleri yükle
pip install -r requirements.txt
```

## 2. İlk Test (API Key Olmadan)

API key olmadan da test edebilirsiniz (dummy veri kullanılır):

```bash
# Basit test
python -m src.data_collection

# Tam analiz örneği
python example_usage.py

# Komut satırından
python -m src.main "Apple" "AAPL" 30
```

## 3. API Key ile Kullanım (Önerilen)

1. `.env` dosyası oluşturun:
```bash
cp .env.example .env
```

2. NewsAPI key alın: https://newsapi.org/ (ücretsiz)

3. `.env` dosyasına ekleyin:
```
NEWS_API_KEY=your_key_here
```

4. Tekrar çalıştırın:
```bash
python -m src.main "Apple" "AAPL" 30
```

## 4. Jupyter Notebook ile Kullanım

```bash
# Jupyter'ı başlat
jupyter notebook

# notebooks/analysis_notebook.ipynb dosyasını açın
```

## Örnek Kullanımlar

### Apple Analizi
```bash
python -m src.main "Apple" "AAPL" 30
```

### Microsoft Analizi (Finansal Ağırlıklı)
```python
from src.main import analyze_company

results = analyze_company(
    company_name="Microsoft",
    ticker="MSFT",
    days_back=30,
    sentiment_weight=0.3,  # Haberlere daha az ağırlık
    financial_weight=0.7    # Finansal verilere daha fazla ağırlık
)

print(results['summary'])
```

### Türk Şirketi Analizi
```bash
python -m src.main "Türk Hava Yolları" "THYAO.IS" 30
```

## Sorun Giderme

**Import hatası alıyorsanız:**
```bash
# Proje kök dizininden çalıştırdığınızdan emin olun
cd /path/to/finance
python -m src.main "Apple" "AAPL"
```

**Model indirme hatası:**
- İnternet bağlantınızı kontrol edin
- İlk çalıştırmada model otomatik indirilir (birkaç yüz MB)

**API limit hatası:**
- NewsAPI ücretsiz tier: 100 istek/gün
- Dummy veri modunda limit yok

## Sonraki Adımlar

1. `README.md` dosyasını okuyarak detaylı bilgi edinin
2. `src/` klasöründeki kodları inceleyerek özelleştirin
3. Kendi şirketlerinizi analiz edin!

