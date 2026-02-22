import requests
from datetime import datetime
import pytz

# --- LOGLARDAN GELEN KESİN BİLGİLER ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
TOPIC_ID = "958" 

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mesaj,
        'parse_mode': 'Markdown',
        'message_thread_id': TOPIC_ID
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            print(f"✅ Mesaj konuya iletildi.")
        else:
            print(f"❌ Telegram Hatası: {res.text}")
    except Exception as e:
        print(f"❌ Sistem Hatası: {e}")

def kap_taramasi():
    print("KAP sistemi kontrol ediliyor...")
    url = "https://www.kap.org.tr/tr/api/disclosures"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        bildirimler = response.json()
        
        # Test amaçlı: Son 3 güncel bildirimi gönder
        for haber in bildirimler[:3]: 
            sirket = haber.get('stockCodes', 'GENEL')
            baslik = haber.get('disclosureIndex', {}).get('title', 'KAP Bildirimi')
            h_id = haber.get('disclosureIndex', {}).get('id')
            link = f"https://www.kap.org.tr/tr/Bildirim/{h_id}"

            mesaj = (f"🔔 *ANLIK KAP HABERİ*\n\n"
                     f"🏢 *Şirket:* {sirket}\n"
                     f"📜 *Konu:* {baslik}\n\n"
                     f"🔗 [Bildirimi Görüntüle]({link})")
            
            telegram_gonder(mesaj)
            
    except Exception as e:
        print(f"❌ KAP Veri Hatası: {e}")

if __name__ == "__main__":
    kap_taramasi()
