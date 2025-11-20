"""
PDF Parser Modülü

KAP bildirimlerinden indirilen PDF dosyalarını okur ve özetler.
Faaliyet raporları, mali tablolar ve özel durum açıklamalarını analiz eder.
"""

import os
import requests
from typing import Dict, List, Optional
from pathlib import Path
import tempfile
import re

# PDF parsing kütüphaneleri
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("⚠️  pypdf paketi yüklü değil. PDF parsing kullanılamayacak.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("⚠️  pdfplumber paketi yüklü değil. Gelişmiş PDF parsing kullanılamayacak.")

# Gemini API için
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Proje kök dizini
project_root = Path(__file__).parent.parent.parent
pdf_cache_dir = project_root / "data" / "pdf_cache"
pdf_cache_dir.mkdir(parents=True, exist_ok=True)


class PDFParser:
    """
    PDF dosyalarını okuyan ve özetleyen sınıf.
    """
    
    def __init__(self):
        """PDF parser'ı başlatır."""
        self.available = PYPDF_AVAILABLE or PDFPLUMBER_AVAILABLE
        
        if not self.available:
            print("⚠️  PDF parsing kütüphaneleri yüklü değil.")
            print("   💡 Yüklemek için: pip install pypdf pdfplumber")
            return
        
        # Gemini API'yi yükle (eğer varsa)
        self.gemini_model = None
        if GEMINI_AVAILABLE:
            gemini_api_key = os.getenv('GEMINI_API_KEY')
            if gemini_api_key:
                try:
                    genai.configure(api_key=gemini_api_key)
                    # Model isimlerini sırayla dene
                    model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
                    for model_name in model_names:
                        try:
                            self.gemini_model = genai.GenerativeModel(model_name)
                            test_response = self.gemini_model.generate_content("Test")
                            if test_response and test_response.text:
                                print(f"✅ Gemini API yüklendi: {model_name}")
                                break
                        except Exception:
                            continue
                except Exception as e:
                    print(f"⚠️  Gemini API yüklenemedi: {e}")
    
    def download_pdf(self, url: str, filename: Optional[str] = None) -> Optional[Path]:
        """
        PDF dosyasını indirir.
        
        Parametreler:
        ------------
        url : str
            PDF URL'i
        filename : str, optional
            Kaydedilecek dosya adı (None ise URL'den çıkarılır)
        
        Döndürür:
        --------
        Path veya None
            İndirilen PDF dosyasının yolu
        """
        try:
            # Dosya adını belirle
            if filename is None:
                filename = url.split('/')[-1]
                if not filename.endswith('.pdf'):
                    filename = f"{filename}.pdf"
            
            file_path = pdf_cache_dir / filename
            
            # Eğer dosya zaten varsa, tekrar indirme
            if file_path.exists():
                print(f"✅ PDF zaten mevcut: {filename}")
                return file_path
            
            # PDF'i indir
            print(f"📥 PDF indiriliyor: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Dosyaya kaydet
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ PDF indirildi: {filename} ({len(response.content)} bytes)")
            return file_path
            
        except Exception as e:
            print(f"⚠️  PDF indirilemedi: {e}")
            return None
    
    def extract_text_pypdf(self, pdf_path: Path) -> str:
        """pypdf ile PDF'den metin çıkarır."""
        try:
            text = ""
            with open(pdf_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"⚠️  pypdf ile metin çıkarılamadı: {e}")
            return ""
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> str:
        """pdfplumber ile PDF'den metin çıkarır (daha iyi tablo desteği)."""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            print(f"⚠️  pdfplumber ile metin çıkarılamadı: {e}")
            return ""
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        PDF'den metin çıkarır (en iyi yöntemi kullanır).
        
        Parametreler:
        ------------
        pdf_path : Path
            PDF dosyasının yolu
        
        Döndürür:
        --------
        str
            Çıkarılan metin
        """
        if not pdf_path.exists():
            print(f"⚠️  PDF dosyası bulunamadı: {pdf_path}")
            return ""
        
        # Önce pdfplumber dene (daha iyi)
        if PDFPLUMBER_AVAILABLE:
            text = self.extract_text_pdfplumber(pdf_path)
            if text and len(text.strip()) > 100:
                return text
        
        # pdfplumber başarısızsa pypdf dene
        if PYPDF_AVAILABLE:
            text = self.extract_text_pypdf(pdf_path)
            if text and len(text.strip()) > 100:
                return text
        
        print("⚠️  PDF'den metin çıkarılamadı.")
        return ""
    
    def chunk_text(self, text: str, chunk_size: int = 5000, overlap: int = 500) -> List[str]:
        """
        Uzun metni parçalara ayırır (Gemini token limiti için).
        
        Parametreler:
        ------------
        text : str
            Metin
        chunk_size : int
            Her parçanın maksimum karakter sayısı
        overlap : int
            Parçalar arası örtüşme (bağlam kaybını önlemek için)
        
        Döndürür:
        --------
        list
            Metin parçaları
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Eğer son parça değilse, cümle sonuna kadar git
            if end < len(text):
                # Son 500 karakterde nokta, soru işareti veya ünlem ara
                last_period = text.rfind('.', end - overlap, end)
                last_question = text.rfind('?', end - overlap, end)
                last_exclamation = text.rfind('!', end - overlap, end)
                
                last_sentence_end = max(last_period, last_question, last_exclamation)
                
                if last_sentence_end > start:
                    end = last_sentence_end + 1
            
            chunks.append(text[start:end])
            start = end - overlap  # Overlap ile devam et
        
        return chunks
    
    def analyze_with_gemini(self, text: str, report_type: str = "faaliyet_raporu") -> Dict:
        """
        Gemini API ile PDF içeriğini analiz eder.
        
        Parametreler:
        ------------
        text : str
            PDF'den çıkarılan metin
        report_type : str
            Rapor tipi (faaliyet_raporu, mali_tablo, ozel_durum, etc.)
        
        Döndürür:
        --------
        dict
            Analiz sonucu:
            {
                'summary': str,
                'risks': List[str],
                'opportunities': List[str],
                'key_metrics': Dict,
                'management_outlook': str
            }
        """
        if not self.gemini_model:
            return {
                'summary': 'Gemini API kullanılamıyor.',
                'risks': [],
                'opportunities': [],
                'key_metrics': {},
                'management_outlook': ''
            }
        
        try:
            # Metni parçalara ayır (çok uzunsa)
            chunks = self.chunk_text(text, chunk_size=10000)
            
            # İlk parçayı analiz et (genellikle özet ve önemli bilgiler burada)
            first_chunk = chunks[0]
            
            prompt = f"""
Sen bir finansal analiz uzmanısın. Aşağıdaki {report_type} metnini analiz et ve şu bilgileri JSON formatında döndür:

1. **Özet:** Raporun ana mesajı nedir? (2-3 cümle)

2. **Riskler:** Şirketin karşılaştığı en büyük 3 riski madde madde listele.

3. **Fırsatlar:** Şirketin önündeki en büyük 3 fırsatı madde madde listele.

4. **Önemli Metrikler:** Rapor içinde geçen önemli finansal göstergeler (ciro, kar, zarar, büyüme oranı, vb.)

5. **Yönetim Görünümü:** Yönetim kurulunun geleceğe dair görüşleri ve beklentileri nelerdir?

RAPOR METNİ:
{first_chunk[:8000]}

Yanıtını SADECE şu JSON formatında ver:
{{
    "summary": "...",
    "risks": ["Risk 1", "Risk 2", "Risk 3"],
    "opportunities": ["Fırsat 1", "Fırsat 2", "Fırsat 3"],
    "key_metrics": {{
        "ciro": "...",
        "kar": "...",
        "buyume": "..."
    }},
    "management_outlook": "..."
}}
"""
            
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON'u extract et
            import json
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"⚠️  Gemini analiz hatası: {e}")
            return {
                'summary': f'Analiz hatası: {str(e)}',
                'risks': [],
                'opportunities': [],
                'key_metrics': {},
                'management_outlook': ''
            }
    
    def parse_kap_pdf(self, kap_url: str, report_title: str = "") -> Dict:
        """
        KAP bildiriminden PDF'i indirir, okur ve analiz eder.
        
        Parametreler:
        ------------
        kap_url : str
            KAP bildirimi URL'i (PDF linki)
        report_title : str
            Rapor başlığı
        
        Döndürür:
        --------
        dict
            Analiz sonucu:
            {
                'text': str,  # Çıkarılan metin
                'analysis': Dict,  # Gemini analizi
                'success': bool
            }
        """
        if not self.available:
            return {
                'text': '',
                'analysis': {},
                'success': False,
                'error': 'PDF parser kullanılamıyor'
            }
        
        try:
            # PDF'i indir
            pdf_path = self.download_pdf(kap_url)
            if not pdf_path:
                return {
                    'text': '',
                    'analysis': {},
                    'success': False,
                    'error': 'PDF indirilemedi'
                }
            
            # Metni çıkar
            text = self.extract_text(pdf_path)
            if not text:
                return {
                    'text': '',
                    'analysis': {},
                    'success': False,
                    'error': 'PDF\'den metin çıkarılamadı'
                }
            
            print(f"✅ PDF okundu: {len(text)} karakter")
            
            # Rapor tipini belirle
            report_type = "faaliyet_raporu"
            if "mali tablo" in report_title.lower() or "finansal" in report_title.lower():
                report_type = "mali_tablo"
            elif "özel durum" in report_title.lower():
                report_type = "ozel_durum"
            
            # Gemini ile analiz et
            analysis = self.analyze_with_gemini(text, report_type)
            
            return {
                'text': text,
                'analysis': analysis,
                'success': True,
                'pdf_path': str(pdf_path)
            }
            
        except Exception as e:
            print(f"⚠️  KAP PDF parse hatası: {e}")
            return {
                'text': '',
                'analysis': {},
                'success': False,
                'error': str(e)
            }


def parse_kap_report(kap_url: str, report_title: str = "") -> Dict:
    """
    KAP raporunu parse eden yardımcı fonksiyon.
    
    Parametreler:
    ------------
    kap_url : str
        KAP PDF URL'i
    report_title : str
        Rapor başlığı
    
    Döndürür:
    --------
    dict
        Parse sonucu
    """
    parser = PDFParser()
    return parser.parse_kap_pdf(kap_url, report_title)


if __name__ == "__main__":
    print("=== PDF Parser Modülü Test ===\n")
    
    parser = PDFParser()
    
    if not parser.available:
        print("❌ PDF parser kullanılamıyor.")
        exit(1)
    
    # Test: Örnek PDF URL'i (gerçek bir KAP PDF linki ile değiştir)
    test_url = "https://www.kap.org.tr/tr/Bildirim/123456"  # Örnek URL
    
    print(f"\n1. PDF indiriliyor: {test_url}")
    result = parser.parse_kap_pdf(test_url, "Test Raporu")
    
    if result['success']:
        print(f"\n✅ PDF başarıyla parse edildi!")
        print(f"   Metin uzunluğu: {len(result['text'])} karakter")
        print(f"\n📊 Analiz Sonucu:")
        print(f"   Özet: {result['analysis'].get('summary', 'N/A')}")
        print(f"   Riskler: {result['analysis'].get('risks', [])}")
        print(f"   Fırsatlar: {result['analysis'].get('opportunities', [])}")
    else:
        print(f"\n❌ PDF parse edilemedi: {result.get('error', 'Bilinmeyen hata')}")

