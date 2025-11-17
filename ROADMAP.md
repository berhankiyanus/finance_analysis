# Yapay Zeka Destekli Borsa Analiz Platformu Geliştirme Yol Haritası

Mevcut projen, veri toplama, tahmin, duygu analizi ve finansal analizi ayıran modüler (src) bir yapıya sahip. Bu, geliştirmeyi kolaylaştıran harika bir başlangıç noktası. İşte bu temeli daha da güçlendirmek için 4 aşamalı bir yol haritası:

---

## Aşama 1: Veri ve Model Temelini Güçlendirme (Düzeltme ve Sağlamlaştırma)

Her yapay zeka projesinin temeli veridir. Finansta bu, "hatalı" olmaktan çok "eksik" olmakla ilgilidir. Modelinin doğruluğu doğrudan buraya bağlı.

### 1.1. Veri Toplamayı Çeşitlendir (data_collection.py)

**Mevcut Durum (Tahmini):** Muhtemelen yfinance gibi kütüphanelerle hisse senedi fiyatları (OHLCV) ve hacim bilgisi çekiyorsun.

**Geliştirme:**

- **Temel Veriler:** Şirketlerin bilanço, gelir tablosu, nakit akış tablosu gibi finansal raporlarını API'ler aracılığıyla çek. (Örn: Financial Modeling Prep, Alpha Vantage API'leri). F/K, PD/DD gibi oranları da ekle.

- **Makroekonomik Veriler:** Faiz oranları, enflasyon (TÜFE, ÜFE), işsizlik oranları, GSYİH büyümesi gibi piyasayı etkileyen genel verileri ekle. (TCMB, TÜİK veya uluslararası veriler için FRED).

- **Alternatif Veriler:** Mümkünse, sosyal medya (Twitter/X) veya forumlardaki hisse senedi "bahsedilme" (mention) sayıları gibi verileri entegre et.

### 1.2. Özellik Mühendisliğini Derinleştir (financial_analysis.py)

**Mevcut Durum (Tahmini):** RSI, MACD, Hareketli Ortalamalar gibi temel teknik göstergeler.

**Geliştirme:**

- Daha fazla istatistiksel özellik ekle: Volatilite (örn: ATR), momentum, korelasyon matrisleri.

- `sentiment_analysis.py` dosyasından gelen duygu skorunu, `prediction_model.py` için doğrudan bir "özellik" (feature) olarak kullan. Örneğin, son 3 günün ortalama haber duygu skoru.

- Topladığın temel verilerden (Aşama 1.1) özellikler türet. (Örn: Borç/Özkaynak Oranı, F/K Oranının sektör ortalamasına göre durumu).

### 1.3. Geriye Dönük Test (Backtesting) Modülü Oluştur (Kritik Düzeltme)

**Sorun:** Bir modelin test setinde %70 "accuracy" (doğruluk) oranına sahip olması, para kazandıracağı anlamına gelmez.

**Çözüm:** `test_system.py` dosyasını bir backtesting motoruna dönüştür veya `backtesting.py` gibi yeni bir kütüphane kullan.

- Modelinin ürettiği sinyallere (örn: `scoring.py` çıktısı 'AL', 'SAT', 'TUT') göre geçmişe dönük sanal alım-satım işlemleri simüle et.

- **Metrikler:** Sadece doğruluğa bakma. Sharpe Oranı, Sortino Oranı, Maksimum Düşüş (Max Drawdown) ve Toplam Kâr/Zarar gibi finansal metrikleri hesapla.

- **Dikkat:** "Geleceği görme" (look-ahead bias) hatasından kaçın. Test verisinin hiçbir parçasını eğitimde kullanmadığından emin ol (örn: Walk-Forward Validation).

---

## Aşama 2: Yapay Zeka Modellerini Geliştirme

Temel sağlamsa, modelleri daha akıllı hale getirebiliriz.

### 2.1. Tahmin Modelini İyileştir (prediction_model.py)

**Mevcut Durum (Tahmini):** LSTM, GRU veya RandomForest gibi klasik modeller.

**Geliştirme:**

- **Transformer Modelleri:** Zaman serisi tahmini için özel olarak tasarlanmış Transformer modellerini (örn: Time Series Transformer, Informer) araştır.

- **Gradient Boosting:** Özellikle tabular (tablo) verilerle (teknik göstergeler + temel veriler + duygu skoru) çalışırken XGBoost, LightGBM veya CatBoost genellikle harika sonuçlar verir.

- **Hedef:** Sadece "yön" (yukarı/aşağı) tahmini yerine, "getiri yüzdesi" veya "volatilite" tahmini yapmayı dene.

### 2.2. Duygu Analizini Özelleştir (sentiment_analysis.py)

**Mevcut Durum (Tahmini):** Genel amaçlı bir BERT veya benzeri bir model (örn: transformers kütüphanesinden) kullanıyorsun.

**Geliştirme:**

- **FinBERT:** Özellikle finansal metinler (haberler, raporlar) üzerinde eğitilmiş modelleri (örn: FinBERT) kullan. Bu modeller, "faiz artırımı" gibi ifadelerin piyasa için ne anlama geldiğini (negatif/pozitif/nötr) daha iyi anlar.

- **Veri Kaynağı:** Sadece genel haberler yerine, doğrudan KAP (Kamuyu Aydınlatma Platformu) bildirimlerini veya Borsa İstanbul duyurularını analiz etmeyi dene.

### 2.3. Açıklanabilir Yapay Zeka (XAI) Ekle

**Sorun:** Kullanıcılar "Yapay zeka 'AL' diyor" ifadesine neden güvensin?

**Çözüm:** Modelin neden o kararı verdiğini göster.

- SHAP veya LIME kütüphanelerini kullanarak modelinin hangi özelliklere (feature) en çok önem verdiğini görselleştir.

- **Streamlit Arayüzünde Gösterim:** "Model 'AL' sinyali üretti. En önemli etkenler: [1] RSI düşük seviyede (%40 etki), [2] Haber duygu skoru pozitif (%30 etki), [3] F/K oranı düşük (%20 etki)..."

---

## Aşama 3: Uygulama ve Kullanıcı Deneyimi (UX)

Modelin ne kadar iyi olursa olsun, sunumun da o kadar iyi olmalı (`app.py`).

### 3.1. Streamlit UX/UI İyileştirmeleri

- **Hız:** Streamlit'in `@st.cache_data` ve `@st.cache_resource` özelliklerini kullanarak veri çekme ve model yükleme işlemlerini hızlandır. Kullanıcı her tıkladığında modelin yeniden yüklenmesini engelle.

- **Görsellik:** Statik matplotlib grafikleri yerine, interaktif grafikler (plotly, altair) kullan. Kullanıcı grafik üzerinde gezinebilmeli, zoom yapabilmeli.

- **Düzen:** `st.tabs` (Sekmeler) kullanarak analizleri (Temel, Teknik, AI Tahmin, Haberler) ayır. `st.columns` ile daha modern bir sayfa düzeni oluştur.

### 3.2. Kullanıcı Odaklı Özellikler Ekleme

- **Kullanıcı Girişi (Authentication):** Streamlit'in yeni sürüm özelliklerini veya basit bir veritabanı (Firebase/Firestore) kullanarak kullanıcı girişi ekle.

- **İzleme Listesi (Watchlist):** Kullanıcıların kendi takip listelerini oluşturmalarına ve kaydetmelerine izin ver.

- **Alarmlar:** Belirlediğin bir hisse, model skoruna veya belirlediği bir fiyata ulaştığında kullanıcıya e-posta/bildirim gönder.

### 3.3. API'ye Geçiş Planı (Uzun Vade)

**Sorun:** Streamlit, yüksek trafikli, tam özellikli bir "web sitesi" için ideal değildir, daha çok bir "veri uygulaması" aracıdır.

**Plan:** Gelecekte, AI modellerini FastAPI veya Django REST Framework kullanarak bir API servisi haline getir. Frontend (kullanıcı arayüzü) kısmını ise React, Vue veya Angular gibi modern bir framework ile geliştir. Bu, projeni gerçek anlamda ölçeklenebilir bir "web sitesi" yapar.

---

## Aşama 4: Dağıtım ve MLOps (Süreklilik)

Modelini bir kez eğitip bırakamazsın; piyasalar sürekli değişir.

### 4.1. CI/CD (Sürekli Entegrasyon/Dağıtım) Kurulumu

**Mevcut Durum (Tahmini):** Muhtemelen manuel olarak git push yapıp Streamlit Cloud'da güncelliyorsun.

**Geliştirme:** GitHub Actions (veya GitLab CI) kullanarak bir CI/CD pipeline'ı kur.

- `main` branch'ine her kod itildiğinde (push), test script'lerini otomatik çalıştır.

- Testler başarılı olursa, uygulamayı otomatik olarak Streamlit Cloud'a veya kendi sunucuna (VPS) deploy et.

### 4.2. Otomatik Yeniden Eğitim (Retraining) Pipeline'ı

**Sorun:** Modelin 6 ay önce öğrendiği piyasa dinamikleri bugün geçerli olmayabilir (Model "bayatlar").

**Çözüm:** Modelini otomatik olarak yeniden eğitecek bir sistem kur.

- `train_model.py` script'ini haftalık veya aylık olarak çalıştıracak bir zamanlanmış görev (cron job) ayarla.

- MLflow gibi bir araç kullanarak her model eğitiminin sonuçlarını (backtest metrikleri) kaydet.

- **Strateji:** Eğer yeni eğitilen model, mevcut (production'daki) modelden daha iyi backtest sonuçları veriyorsa, otomatik olarak yeni modeli devreye al.

### 4.3. İzleme (Monitoring)

Uygulamanın (Streamlit) ve modelin canlıdaki performansını izle.

- **Data Drift:** Canlıya gelen verinin (örn: son 1 ayın ortalama hacmi), modelin eğitildiği veriden (örn: 2020-2023 verisi) çok farklılaşmasını (data drift) izle.

- **Model Drift:** Modelin canlıdaki tahmin performansının (örn: 1 hafta sonra tahminin tutup tutmadığı) zamanla düşmesini (model drift) izle ve bu olursa yeniden eğitim için alarm oluştur.

---

## Öncelik Sırası

### 🔴 Yüksek Öncelik (Hemen Başlanabilir)
1. **Backtesting Modülü** (1.3) - Model performansını gerçekçi şekilde değerlendirmek için kritik
2. **Streamlit Cache** (3.1) - Kullanıcı deneyimini hızlandırmak için
3. **SHAP/LIME Entegrasyonu** (2.3) - Model güvenilirliğini artırmak için

### 🟡 Orta Öncelik (Kısa Vadede)
1. **Finansal Veri Çeşitlendirme** (1.1) - Daha zengin veri seti
2. **Özellik Mühendisliği** (1.2) - Daha iyi tahminler
3. **Interaktif Grafikler** (3.1) - Daha iyi görselleştirme

### 🟢 Düşük Öncelik (Uzun Vadede)
1. **Transformer Modelleri** (2.1) - Daha gelişmiş modeller
2. **CI/CD Pipeline** (4.1) - Otomasyon
3. **Monitoring** (4.3) - Production izleme

---

## Notlar

- Bu yol haritası, mevcut projenin modüler yapısına uygun olarak tasarlanmıştır.
- Her aşama, bir önceki aşamanın tamamlanmasına bağlı değildir; paralel olarak ilerlenebilir.
- Öncelikler, projenin mevcut durumuna ve ihtiyaçlara göre değiştirilebilir.

