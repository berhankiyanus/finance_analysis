"""
Telegram Bot Modülü

Kullanıcı uyarıları için Telegram bot entegrasyonu.
Kritik olaylardan (sentiment değişimi, RSI aşırı alım/satım, KAP bildirimi) anında haberdar olma.
"""

import os
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from src.logger_config import setup_logger

logger = setup_logger(__name__)

# .env dosyasını yükle
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

# Telegram import (opsiyonel)
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("⚠️  python-telegram-bot yüklü değil. Telegram bildirimleri kullanılamayacak.")
    logger.info("   💡 Yüklemek için: pip install python-telegram-bot")

# Bot instance (singleton)
_telegram_bot = None


def get_telegram_bot() -> Optional[Bot]:
    """
    Telegram bot instance'ını döndürür (singleton pattern).
    
    Döndürür:
    --------
    Bot veya None
        Telegram bot instance'ı veya None (bot yoksa)
    """
    global _telegram_bot
    
    if not TELEGRAM_AVAILABLE:
        return None
    
    if _telegram_bot is None:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.warning("⚠️  TELEGRAM_BOT_TOKEN bulunamadı. Telegram bildirimleri devre dışı.")
            return None
        
        try:
            _telegram_bot = Bot(token=bot_token)
            # Bot bilgilerini al (bağlantıyı test et)
            bot_info = _telegram_bot.get_me()
            logger.info(f"✅ Telegram bot bağlantısı kuruldu: @{bot_info.username}")
        except Exception as e:
            logger.error(f"❌ Telegram bot bağlantısı kurulamadı: {e}")
            _telegram_bot = None
    
    return _telegram_bot


def send_notification(
    chat_id: str,
    message: str,
    parse_mode: str = "Markdown",
    disable_notification: bool = False
) -> bool:
    """
    Telegram'a bildirim gönderir.
    
    Parametreler:
    ------------
    chat_id : str
        Telegram chat ID (kullanıcı veya grup)
    message : str
        Gönderilecek mesaj
    parse_mode : str
        Mesaj formatı (Markdown veya HTML)
    disable_notification : bool
        Bildirim sesi çalmasın mı?
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    bot = get_telegram_bot()
    if bot is None:
        return False
    
    try:
        bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode,
            disable_notification=disable_notification
        )
        return True
    except TelegramError as e:
        logger.error(f"Telegram bildirim hatası: {e}")
        return False
    except Exception as e:
        logger.error(f"Beklenmeyen Telegram hatası: {e}")
        return False


def send_sentiment_alert(
    chat_id: str,
    ticker: str,
    company_name: str,
    sentiment_score: float,
    threshold: float = 80.0
) -> bool:
    """
    Sentiment skoru eşik değerini aştığında uyarı gönderir.
    
    Parametreler:
    ------------
    chat_id : str
        Telegram chat ID
    ticker : str
        Hisse kodu
    company_name : str
        Şirket adı
    sentiment_score : float
        Sentiment skoru (0-100)
    threshold : float
        Eşik değeri (varsayılan: 80.0)
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    if sentiment_score < threshold:
        return False
    
    emoji = "📈" if sentiment_score >= 80 else "📉"
    message = f"""
{emoji} **Sentiment Uyarısı**

**Şirket:** {company_name} ({ticker})
**Sentiment Skoru:** {sentiment_score:.1f}/100
**Eşik Değer:** {threshold:.1f}

⚠️ Sentiment skoru eşik değerini aştı!
"""
    
    return send_notification(chat_id, message)


def send_rsi_alert(
    chat_id: str,
    ticker: str,
    company_name: str,
    rsi: float,
    alert_type: str = "oversold"  # "oversold" veya "overbought"
) -> bool:
    """
    RSI aşırı alım/satım uyarısı gönderir.
    
    Parametreler:
    ------------
    chat_id : str
        Telegram chat ID
    ticker : str
        Hisse kodu
    company_name : str
        Şirket adı
    rsi : float
        RSI değeri (0-100)
    alert_type : str
        Uyarı tipi ("oversold" veya "overbought")
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    if alert_type == "oversold" and rsi >= 30:
        return False
    if alert_type == "overbought" and rsi <= 70:
        return False
    
    if alert_type == "oversold":
        emoji = "🟢"
        action = "Aşırı Satım"
        suggestion = "Potansiyel alım fırsatı olabilir"
    else:
        emoji = "🔴"
        action = "Aşırı Alım"
        suggestion = "Dikkatli olun, düşüş riski var"
    
    message = f"""
{emoji} **RSI Uyarısı**

**Şirket:** {company_name} ({ticker})
**RSI Değeri:** {rsi:.1f}
**Durum:** {action}

💡 {suggestion}
"""
    
    return send_notification(chat_id, message)


def send_kap_alert(
    chat_id: str,
    ticker: str,
    company_name: str,
    kap_title: str,
    kap_link: str,
    alert_type: str = "important"
) -> bool:
    """
    KAP bildirimi uyarısı gönderir.
    
    Parametreler:
    ------------
    chat_id : str
        Telegram chat ID
    ticker : str
        Hisse kodu
    company_name : str
        Şirket adı
    kap_title : str
        KAP bildirimi başlığı
    kap_link : str
        KAP bildirimi linki
    alert_type : str
        Uyarı tipi ("important", "financial", "general")
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    emoji_map = {
        "important": "🔔",
        "financial": "💰",
        "general": "📄"
    }
    emoji = emoji_map.get(alert_type, "📄")
    
    message = f"""
{emoji} **KAP Bildirimi**

**Şirket:** {company_name} ({ticker})
**Başlık:** {kap_title}

🔗 [Bildirimi Görüntüle]({kap_link})
"""
    
    return send_notification(chat_id, message)


def send_price_alert(
    chat_id: str,
    ticker: str,
    company_name: str,
    current_price: float,
    change_percent: float,
    alert_type: str = "significant_change"
) -> bool:
    """
    Önemli fiyat değişimi uyarısı gönderir.
    
    Parametreler:
    ------------
    chat_id : str
        Telegram chat ID
    ticker : str
        Hisse kodu
    company_name : str
        Şirket adı
    current_price : float
        Güncel fiyat
    change_percent : float
        Yüzde değişim
    alert_type : str
        Uyarı tipi ("significant_change", "new_high", "new_low")
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    emoji_map = {
        "significant_change": "📊",
        "new_high": "🚀",
        "new_low": "📉"
    }
    emoji = emoji_map.get(alert_type, "📊")
    
    change_emoji = "📈" if change_percent > 0 else "📉"
    
    message = f"""
{emoji} **Fiyat Uyarısı**

**Şirket:** {company_name} ({ticker})
**Güncel Fiyat:** {current_price:.2f} TL
**Değişim:** {change_emoji} {abs(change_percent):.2f}%
"""
    
    return send_notification(chat_id, message)


def send_analysis_summary(
    chat_id: str,
    ticker: str,
    company_name: str,
    overall_score: float,
    sentiment_score: float,
    financial_score: float,
    direction: str,
    confidence: float
) -> bool:
    """
    Günlük analiz özeti gönderir.
    
    Parametreler:
    ------------
    chat_id : str
        Telegram chat ID
    ticker : str
        Hisse kodu
    company_name : str
        Şirket adı
    overall_score : float
        Genel skor
    sentiment_score : float
        Sentiment skoru
    financial_score : float
        Finansal skor
    direction : str
        Tahmin yönü ("BUY", "SELL", "HOLD")
    confidence : float
        Güven seviyesi (0-1)
    
    Döndürür:
    --------
    bool
        Başarılı mı?
    """
    direction_emoji = {
        "BUY": "🟢",
        "SELL": "🔴",
        "HOLD": "🟡"
    }.get(direction, "⚪")
    
    message = f"""
📊 **Günlük Analiz Özeti**

**Şirket:** {company_name} ({ticker})

**Skorlar:**
• Genel: {overall_score:.1f}/100
• Sentiment: {sentiment_score:.1f}/100
• Finansal: {financial_score:.1f}/100

**Tahmin:** {direction_emoji} {direction}
**Güven:** {confidence:.1%}

📅 {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
    
    return send_notification(chat_id, message)


if __name__ == "__main__":
    # Test
    print("=== Telegram Bot Test ===\n")
    
    bot = get_telegram_bot()
    if bot:
        print("✅ Telegram bot bağlantısı başarılı")
        
        # Chat ID'yi test et (kullanıcı kendi chat ID'sini .env'ye eklemeli)
        test_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if test_chat_id:
            print(f"📱 Test bildirimi gönderiliyor (Chat ID: {test_chat_id})...")
            
            success = send_notification(
                test_chat_id,
                "🧪 **Test Bildirimi**\n\nBu bir test mesajıdır. Telegram bot çalışıyor! ✅"
            )
            
            if success:
                print("✅ Test bildirimi gönderildi!")
            else:
                print("❌ Test bildirimi gönderilemedi")
        else:
            print("⚠️  TELEGRAM_CHAT_ID bulunamadı.")
            print("   💡 .env dosyasına TELEGRAM_CHAT_ID=your_chat_id ekleyin")
            print("   💡 Chat ID'yi öğrenmek için @userinfobot'a mesaj gönderin")
    else:
        print("⚠️  Telegram bot kullanılamıyor (opsiyonel)")

