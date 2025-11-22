"""
PDF Chat Modülü (RAG ile PDF Sorgulama)

Kullanıcıların faaliyet raporlarına doğal dil ile soru sorabilmesini sağlar.
RAG (Retrieval-Augmented Generation) mimarisi kullanır.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# .env dosyasını yükle
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Gemini API için
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️  google-generativeai yüklü değil. PDF Chat kullanılamayacak.")

# Vector DB için
try:
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    logger.warning("⚠️  Vector DB kütüphaneleri yüklü değil. PDF Chat kullanılamayacak.")


class PDFChat:
    """
    PDF içeriğini RAG ile sorgulama sınıfı.
    """
    
    def __init__(self, collection_name: str = "pdf_documents"):
        """
        PDF Chat'i başlatır.
        
        Parametreler:
        ------------
        collection_name : str
            ChromaDB collection adı
        """
        if not GEMINI_AVAILABLE:
            self.available = False
            logger.warning("Gemini API kullanılamıyor. PDF Chat devre dışı.")
            return
        
        if not VECTOR_DB_AVAILABLE:
            self.available = False
            logger.warning("Vector DB kullanılamıyor. PDF Chat devre dışı.")
            return
        
        self.available = True
        self.collection_name = collection_name
        
        # Gemini API'yi yapılandır
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            logger.warning("GEMINI_API_KEY bulunamadı. PDF Chat devre dışı.")
            self.available = False
            return
        
        try:
            genai.configure(api_key=gemini_api_key)
            # Model fallback mekanizması
            try:
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                try:
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                except:
                    self.gemini_model = genai.GenerativeModel('gemini-pro')
            logger.info("✅ Gemini modeli yüklendi.")
        except Exception as e:
            logger.error(f"Gemini modeli yüklenirken hata: {e}")
            self.available = False
            return
        
        # Embedding modelini yükle
        try:
            self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("✅ Embedding modeli yüklendi.")
        except Exception as e:
            logger.error(f"Embedding modeli yüklenirken hata: {e}")
            self.available = False
            return
        
        # ChromaDB client'ı başlat
        try:
            vector_db_path = project_root / "data" / "vector_db" / "pdfs"
            vector_db_path.mkdir(parents=True, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=str(vector_db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "PDF belgeleri ve içerikleri"}
            )
            
            logger.info(f"✅ PDF Chat hazır: {self.collection.count()} belge")
            
        except Exception as e:
            logger.error(f"ChromaDB başlatılamadı: {e}")
            self.available = False
    
    def add_pdf(
        self,
        pdf_id: str,
        pdf_text: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        PDF içeriğini vector DB'ye ekler.
        
        Parametreler:
        ------------
        pdf_id : str
            PDF benzersiz ID'si
        pdf_text : str
            PDF'den çıkarılan metin
        metadata : dict
            Ek metadata (ticker, company_name, report_date, vb.)
        
        Döndürür:
        --------
        bool
            Başarılı mı?
        """
        if not self.available:
            return False
        
        try:
            # Metni parçalara böl (chunking)
            chunks = self._chunk_text(pdf_text, chunk_size=500, overlap=50)
            
            # Her chunk için embedding oluştur
            embeddings = []
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                embedding = self.embedder.encode(chunk).tolist()
                embeddings.append(embedding)
                documents.append(chunk)
                
                chunk_metadata = {
                    'pdf_id': pdf_id,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
                if metadata:
                    chunk_metadata.update(metadata)
                metadatas.append(chunk_metadata)
                
                ids.append(f"{pdf_id}_chunk_{i}")
            
            # Vector DB'ye ekle
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ PDF eklendi: {pdf_id} ({len(chunks)} chunk)")
            return True
            
        except Exception as e:
            logger.error(f"PDF eklenirken hata: {e}")
            return False
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Metni parçalara böler.
        
        Parametreler:
        ------------
        text : str
            Metin
        chunk_size : int
            Chunk boyutu (kelime sayısı)
        overlap : int
            Chunk'lar arası overlap (kelime sayısı)
        
        Döndürür:
        --------
        list
            Chunk listesi
        """
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            chunk = words[i:i + chunk_size]
            chunks.append(' '.join(chunk))
            i += chunk_size - overlap
        
        return chunks
    
    def search_relevant_chunks(
        self,
        query: str,
        pdf_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Sorguya en uygun PDF chunk'larını bulur.
        
        Parametreler:
        ------------
        query : str
            Kullanıcı sorusu
        pdf_id : str
            Belirli bir PDF'e sınırla (opsiyonel)
        top_k : int
            Kaç chunk döndürülecek
        
        Döndürür:
        --------
        list
            İlgili chunk'lar ve metadata
        """
        if not self.available:
            return []
        
        try:
            # Sorgu için embedding oluştur
            query_embedding = self.embedder.encode(query).tolist()
            
            # Vector DB'de ara
            where_clause = {'pdf_id': pdf_id} if pdf_id else None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=['metadatas', 'distances', 'documents']
            )
            
            # Sonuçları formatla
            relevant_chunks = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    relevant_chunks.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': 1 - results['distances'][0][i]  # Distance'ı similarity'ye çevir
                    })
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"PDF arama hatası: {e}")
            return []
    
    def ask_question(
        self,
        question: str,
        pdf_id: Optional[str] = None,
        context_chunks: int = 5
    ) -> Dict:
        """
        PDF'e soru sorar ve Gemini ile yanıt üretir.
        
        Parametreler:
        ------------
        question : str
            Kullanıcı sorusu
        pdf_id : str
            Belirli bir PDF'e sınırla (opsiyonel)
        context_chunks : int
            Kaç chunk context olarak kullanılacak
        
        Döndürür:
        --------
        dict
            Yanıt ve ilgili bilgiler
        """
        if not self.available:
            return {
                'answer': 'PDF Chat kullanılamıyor. Gerekli kütüphaneler yüklü değil.',
                'relevant_chunks': [],
                'error': True
            }
        
        try:
            # İlgili chunk'ları bul
            relevant_chunks = self.search_relevant_chunks(
                query=question,
                pdf_id=pdf_id,
                top_k=context_chunks
            )
            
            if not relevant_chunks:
                return {
                    'answer': 'Soruya uygun içerik bulunamadı. Lütfen soruyu farklı şekilde ifade edin.',
                    'relevant_chunks': [],
                    'error': False
                }
            
            # Context'i oluştur
            context_text = "\n\n".join([
                f"[Bölüm {i+1}]\n{chunk['text']}"
                for i, chunk in enumerate(relevant_chunks)
            ])
            
            # Gemini'ye sor
            prompt = f"""
Aşağıdaki bir şirketin faaliyet raporundan alınmış bölümler var. Kullanıcının sorusunu bu bölümlere dayanarak yanıtla.

**Kullanıcı Sorusu:** {question}

**Rapor Bölümleri:**
{context_text}

**Talimatlar:**
1. Sadece verilen bölümlerdeki bilgilere dayanarak yanıt ver.
2. Eğer bilgi yoksa, "Raporda bu bilgi bulunmamaktadır" de.
3. Sayısal veriler varsa, bunları belirt.
4. Yanıtı Türkçe, net ve kısa tut (2-3 paragraf).

**Yanıt:**
"""
            
            response = self.gemini_model.generate_content(prompt)
            answer = response.text.strip()
            
            return {
                'answer': answer,
                'relevant_chunks': relevant_chunks,
                'question': question,
                'pdf_id': pdf_id,
                'error': False
            }
            
        except Exception as e:
            logger.error(f"PDF soru sorma hatası: {e}")
            return {
                'answer': f'Hata oluştu: {str(e)}',
                'relevant_chunks': [],
                'error': True
            }
    
    def get_pdf_list(self) -> List[Dict]:
        """
        Vector DB'deki PDF listesini döndürür.
        
        Döndürür:
        --------
        list
            PDF listesi (metadata ile)
        """
        if not self.available:
            return []
        
        try:
            # Tüm PDF'leri al
            all_data = self.collection.get(include=['metadatas'])
            
            # Benzersiz PDF ID'lerini bul
            pdf_ids = set()
            pdf_metadata = {}
            
            for metadata in all_data['metadatas']:
                pdf_id = metadata.get('pdf_id')
                if pdf_id:
                    pdf_ids.add(pdf_id)
                    if pdf_id not in pdf_metadata:
                        pdf_metadata[pdf_id] = metadata
            
            # PDF listesini oluştur
            pdf_list = []
            for pdf_id in pdf_ids:
                pdf_list.append({
                    'pdf_id': pdf_id,
                    'metadata': pdf_metadata[pdf_id]
                })
            
            return pdf_list
            
        except Exception as e:
            logger.error(f"PDF listesi alınırken hata: {e}")
            return []


# Global instance
_pdf_chat = None


def get_pdf_chat() -> PDFChat:
    """
    PDF Chat instance'ını döndürür (singleton pattern).
    
    Döndürür:
    --------
    PDFChat
        PDF Chat instance'ı
    """
    global _pdf_chat
    if _pdf_chat is None:
        _pdf_chat = PDFChat()
    return _pdf_chat


if __name__ == "__main__":
    # Test
    print("=== PDF Chat Test ===\n")
    
    pdf_chat = get_pdf_chat()
    
    if not pdf_chat.available:
        print("⚠️  PDF Chat kullanılamıyor. Gerekli kütüphaneler yüklü değil.")
        exit(0)
    
    # Test: PDF ekle (örnek metin)
    test_pdf_text = """
    Şirketimiz 2023 yılında önemli büyüme kaydetmiştir.
    Toplam gelir 1.5 milyar TL'ye ulaşmıştır.
    Ar-Ge harcamaları geçen yıla göre %25 artmıştır.
    Net kar 200 milyon TL olmuştur.
    """
    
    print("1. Test PDF ekleniyor...")
    pdf_chat.add_pdf(
        pdf_id="test_report_2023",
        pdf_text=test_pdf_text,
        metadata={
            'ticker': 'TEST',
            'company_name': 'Test Şirketi',
            'report_date': '2023-12-31',
            'report_type': 'Faaliyet Raporu'
        }
    )
    
    # Test: Soru sor
    print("2. Test sorusu soruluyor...")
    result = pdf_chat.ask_question(
        question="Geçen seneki Ar-Ge harcaması ne kadar?",
        pdf_id="test_report_2023"
    )
    
    print(f"   Soru: {result['question']}")
    print(f"   Yanıt: {result['answer']}")
    print(f"   İlgili Bölüm Sayısı: {len(result['relevant_chunks'])}")
    
    # PDF listesi
    print("3. PDF listesi:")
    pdf_list = pdf_chat.get_pdf_list()
    for pdf in pdf_list:
        print(f"   • {pdf['pdf_id']}: {pdf['metadata'].get('company_name', 'N/A')}")

