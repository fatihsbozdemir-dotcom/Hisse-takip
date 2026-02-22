import requests
from datetime import datetime, timedelta
import pytz

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
TOPIC_ID = "958" 

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mesaj,
        'parse_mode': 'Markdown',
        'message_thread_id': TOPIC_ID,
        'disable_web_page_preview': False
    }
    # Önce konuya, olmazsa ana gruba gönderir
    res = requests.post(url, json=payload)
    if res.status_code != 200:
        payload.pop('message_thread_id')
        requests.post(url, json=payload)

def kap_taramasi():
    url = "https://www.kap.org.tr/tr/api/disclosures"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        bildirimler = response.json()
        
        tr_tz = pytz.timezone('Europe/Istanbul')
        simdi = datetime.now(tr_tz)
        # Günde 3 kez çalışacağı için son 5 saati kontrol eder
        zaman_esigi = simdi - timedelta(hours=5)

        found = False
        for haber in bildirimler[:20]:
            tarih_ms = haber.get('publishDate')
            haber_vakti = datetime.fromtimestamp(tarih_ms / 1000.0, tr_tz)

            if haber_vakti > zaman_esigi:
                found = True
                sirket = haber.get('stockCodes', 'GENEL')
                baslik = haber.get('disclosureIndex', {}).get('title', 'KAP Bildirimi')
                h_id = haber.get('disclosureIndex', {}).get('id')
                link = f"https://www.kap.org.tr/tr/Bildirim/{h_id}"

                mesaj = (f"🔔 *YENİ KAP BİLDİRİMİ*\n\n"
                         f"🏢 *Şirket:* {sirket}\n"
                         f"📜 *Konu:* {baslik}\n\n"
                         f"🔗 [Bildirimi Görüntüle]({link})")
                
                telegram_gonder(mesaj)
        
        if not found:
            print("Son 5 saatte yeni bildirim bulunamadı.")
                
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    kap_taramasi()
