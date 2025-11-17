# Kurulum Kılavuzu

Bu kılavuz, projeyi bilgisayarınıza kurmanız için gerekli adımları açıklar.

## Gereksinimler

- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- Git (opsiyonel)

## Adım 1: Projeyi İndirin

Eğer Git kullanıyorsanız:
```bash
git clone <repository-url>
cd finance
```

Veya proje dosyalarını doğrudan indirip açın.

## Adım 2: Virtual Environment Oluşturun (Önerilen)

```bash
# Virtual environment oluştur
python -m venv venv

# Aktifleştir (Windows)
venv\Scripts\activate

# Aktifleştir (macOS/Linux)
source venv/bin/activate
```

## Adım 3: Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

**Not**: PyTorch kurulumu sisteminize göre değişebilir. Eğer GPU desteği istiyorsanız:
- [PyTorch kurulum sayfasından](https://pytorch.org/get-started/locally/) uygun komutu alın.

## Adım 4: API Key'leri Yapılandırın

1. `.env.example` dosyasını `.env` olarak kopyalayın:
```bash
cp .env.example .env
```

2. `.env` dosyasını düzenleyin ve API key'lerinizi ekleyin:

```env
NEWS_API_KEY=your_news_api_key_here
```

### API Key'leri Nereden Alabilirsiniz?

- **NewsAPI**: https://newsapi.org/ adresinden ücretsiz hesap oluşturun (100 istek/gün)
- **Alpha Vantage** (Opsiyonel): https://www.alphavantage.co/support/#api-key
- **Financial Modeling Prep** (Opsiyonel): https://financialmodelingprep.com/developer/docs/

## Adım 5: Test Edin

```bash
# Basit test
python -m src.data_collection

# Tam analiz örneği
python example_usage.py

# Komut satırından kullanım
python -m src.main "Apple" "AAPL" 30
```

## Sorun Giderme

### PyTorch Kurulum Hatası

Eğer PyTorch kurulumunda sorun yaşıyorsanız:
```bash
# CPU versiyonu için
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Transformers Model İndirme Hatası

Model ilk kullanımda otomatik indirilir. İnternet bağlantınızı kontrol edin.

### API Key Hatası

API key yoksa sistem dummy veri kullanacaktır. Test için yeterlidir, ancak gerçek analiz için API key gerekir.

## Sonraki Adımlar

1. `example_usage.py` dosyasını çalıştırarak örnekleri inceleyin
2. `notebooks/analysis_notebook.ipynb` dosyasını Jupyter'da açarak interaktif analiz yapın
3. `src/main.py` dosyasını inceleyerek kodu özelleştirin

## Yardım

Sorun yaşıyorsanız:
1. Hata mesajını kontrol edin
2. Python ve paket versiyonlarınızı kontrol edin
3. Virtual environment'ın aktif olduğundan emin olun

