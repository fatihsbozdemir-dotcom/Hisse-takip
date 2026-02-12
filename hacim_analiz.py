import requests
import sys

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"

def test_mesaji():
    try:
        msg = "🚀 *Bot Bağlantı Testi:* GitHub dosyayı buldu ve Python çalıştı! Şimdi hisse analizine geçiyorum..."
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        res = requests.post(url, json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        print(f"Telegram Yanıtı: {res.text}")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    test_mesaji()
    # Eğer buraya kadar çalışırsa, bir sonraki adımda tam kodu buraya ekleyeceğiz.
