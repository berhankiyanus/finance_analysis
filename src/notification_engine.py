"""
Notification Engine Modülü

Kullanıcı uyarılarını yöneten ve otomatik bildirim gönderen sistem.
Telegram bot entegrasyonu ile çalışır.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from src.logger_config import setup_logger
from src.telegram_bot import (
    send_sentiment_alert,
    send_rsi_alert,
    send_kap_alert,
    send_price_alert,
    send_analysis_summary
)

logger = setup_logger(__name__)

# .env dosyasını yükle
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Kullanıcı uyarı ayarları dosyası
ALERTS_FILE = project_root / "data" / "user_alerts.json"


class NotificationEngine:
    """
    Kullanıcı uyarılarını yöneten ve bildirim gönderen sınıf.
    """
    
    def __init__(self):
        """Notification engine'i başlatır."""
        self.alerts_file = ALERTS_FILE
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        self.alerts = self._load_alerts()
    
    def _load_alerts(self) -> Dict:
        """
        Kullanıcı uyarı ayarlarını yükler.
        
        Döndürür:
        --------
        dict
            Uyarı ayarları
        """
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Uyarı ayarları yüklenirken hata: {e}")
                return {}
        return {}
    
    def _save_alerts(self):
        """Uyarı ayarlarını kaydeder."""
        try:
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Uyarı ayarları kaydedilirken hata: {e}")
    
    def add_alert(
        self,
        chat_id: str,
        ticker: str,
        alert_type: str,
        threshold: Optional[float] = None,
        enabled: bool = True
    ) -> bool:
        """
        Yeni bir uyarı ekler.
        
        Parametreler:
        ------------
        chat_id : str
            Telegram chat ID
        ticker : str
            Hisse kodu
        alert_type : str
            Uyarı tipi ("sentiment", "rsi_oversold", "rsi_overbought", "kap", "price_change")
        threshold : float
            Eşik değeri (opsiyonel)
        enabled : bool
            Uyarı aktif mi?
        
        Döndürür:
        --------
        bool
            Başarılı mı?
        """
        if chat_id not in self.alerts:
            self.alerts[chat_id] = {}
        
        if ticker not in self.alerts[chat_id]:
            self.alerts[chat_id][ticker] = []
        
        alert = {
            'type': alert_type,
            'threshold': threshold,
            'enabled': enabled,
            'created_at': datetime.now().isoformat()
        }
        
        self.alerts[chat_id][ticker].append(alert)
        self._save_alerts()
        
        logger.info(f"Uyarı eklendi: {chat_id} - {ticker} - {alert_type}")
        return True
    
    def remove_alert(self, chat_id: str, ticker: str, alert_index: int) -> bool:
        """
        Bir uyarıyı kaldırır.
        
        Parametreler:
        ------------
        chat_id : str
            Telegram chat ID
        ticker : str
            Hisse kodu
        alert_index : int
            Uyarı indeksi
        
        Döndürür:
        --------
        bool
            Başarılı mı?
        """
        if chat_id in self.alerts and ticker in self.alerts[chat_id]:
            if 0 <= alert_index < len(self.alerts[chat_id][ticker]):
                del self.alerts[chat_id][ticker][alert_index]
                self._save_alerts()
                logger.info(f"Uyarı kaldırıldı: {chat_id} - {ticker} - {alert_index}")
                return True
        return False
    
    def get_alerts(self, chat_id: str, ticker: Optional[str] = None) -> List[Dict]:
        """
        Kullanıcının uyarılarını döndürür.
        
        Parametreler:
        ------------
        chat_id : str
            Telegram chat ID
        ticker : str
            Hisse kodu (opsiyonel, None ise tüm hisseler)
        
        Döndürür:
        --------
        list
            Uyarı listesi
        """
        if chat_id not in self.alerts:
            return []
        
        if ticker is None:
            # Tüm hisseler için uyarıları döndür
            all_alerts = []
            for tick, alerts in self.alerts[chat_id].items():
                all_alerts.extend([{**alert, 'ticker': tick} for alert in alerts])
            return all_alerts
        else:
            return self.alerts[chat_id].get(ticker, [])
    
    def check_and_send_alerts(
        self,
        chat_id: str,
        ticker: str,
        company_name: str,
        analysis_results: Dict
    ) -> int:
        """
        Analiz sonuçlarını kontrol eder ve gerekirse uyarı gönderir.
        
        Parametreler:
        ------------
        chat_id : str
            Telegram chat ID
        ticker : str
            Hisse kodu
        company_name : str
            Şirket adı
        analysis_results : dict
            Analiz sonuçları (sentiment_score, financial_score, rsi, vb.)
        
        Döndürür:
        --------
        int
            Gönderilen uyarı sayısı
        """
        alerts = self.get_alerts(chat_id, ticker)
        if not alerts:
            return 0
        
        sent_count = 0
        
        for alert in alerts:
            if not alert.get('enabled', True):
                continue
            
            alert_type = alert.get('type')
            threshold = alert.get('threshold')
            
            try:
                if alert_type == 'sentiment':
                    sentiment_score = analysis_results.get('sentiment_score', 0)
                    if threshold and sentiment_score >= threshold:
                        if send_sentiment_alert(chat_id, ticker, company_name, sentiment_score, threshold):
                            sent_count += 1
                
                elif alert_type == 'rsi_oversold':
                    rsi = analysis_results.get('rsi', 50)
                    if rsi < 30:
                        if send_rsi_alert(chat_id, ticker, company_name, rsi, "oversold"):
                            sent_count += 1
                
                elif alert_type == 'rsi_overbought':
                    rsi = analysis_results.get('rsi', 50)
                    if rsi > 70:
                        if send_rsi_alert(chat_id, ticker, company_name, rsi, "overbought"):
                            sent_count += 1
                
                elif alert_type == 'price_change':
                    change_percent = analysis_results.get('price_change_30d', 0)
                    if threshold and abs(change_percent) >= abs(threshold):
                        current_price = analysis_results.get('current_price', 0)
                        if send_price_alert(chat_id, ticker, company_name, current_price, change_percent):
                            sent_count += 1
                
                elif alert_type == 'daily_summary':
                    # Günlük özet gönder
                    overall_score = analysis_results.get('overall_score', 50)
                    sentiment_score = analysis_results.get('sentiment_score', 50)
                    financial_score = analysis_results.get('financial_score', 50)
                    direction = analysis_results.get('direction_prediction', {}).get('direction', 'HOLD')
                    confidence = analysis_results.get('direction_prediction', {}).get('confidence', 0.5)
                    
                    if send_analysis_summary(
                        chat_id, ticker, company_name,
                        overall_score, sentiment_score, financial_score,
                        direction, confidence
                    ):
                        sent_count += 1
                
            except Exception as e:
                logger.warning(f"Uyarı gönderilirken hata ({alert_type}): {e}")
                continue
        
        if sent_count > 0:
            logger.info(f"{sent_count} uyarı gönderildi: {chat_id} - {ticker}")
        
        return sent_count


# Global instance
_notification_engine = None


def get_notification_engine() -> NotificationEngine:
    """
    Notification engine instance'ını döndürür (singleton pattern).
    
    Döndürür:
    --------
    NotificationEngine
        Notification engine instance'ı
    """
    global _notification_engine
    if _notification_engine is None:
        _notification_engine = NotificationEngine()
    return _notification_engine


if __name__ == "__main__":
    # Test
    print("=== Notification Engine Test ===\n")
    
    engine = get_notification_engine()
    
    # Test chat ID
    test_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not test_chat_id:
        print("⚠️  TELEGRAM_CHAT_ID bulunamadı. Test atlanıyor.")
        exit(0)
    
    # Test uyarı ekle
    print("1. Test uyarısı ekleniyor...")
    engine.add_alert(
        chat_id=test_chat_id,
        ticker="THYAO",
        alert_type="sentiment",
        threshold=80.0
    )
    
    # Uyarıları listele
    print("2. Uyarılar listeleniyor...")
    alerts = engine.get_alerts(test_chat_id, "THYAO")
    print(f"   Bulunan uyarı sayısı: {len(alerts)}")
    for i, alert in enumerate(alerts):
        print(f"   [{i}] {alert['type']} - Threshold: {alert.get('threshold', 'N/A')}")
    
    # Test analiz sonuçları
    print("3. Test analiz sonuçları ile uyarı kontrol ediliyor...")
    test_results = {
        'sentiment_score': 85.0,  # Eşik değeri aşıyor
        'financial_score': 70.0,
        'overall_score': 77.5,
        'rsi': 25.0,  # Aşırı satım
        'price_change_30d': 5.0,
        'current_price': 100.0,
        'direction_prediction': {
            'direction': 'BUY',
            'confidence': 0.75
        }
    }
    
    sent_count = engine.check_and_send_alerts(
        chat_id=test_chat_id,
        ticker="THYAO",
        company_name="Türk Hava Yolları",
        analysis_results=test_results
    )
    
    print(f"   ✅ {sent_count} uyarı gönderildi")

