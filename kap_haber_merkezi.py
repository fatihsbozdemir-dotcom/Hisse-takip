import requests
from datetime import datetime
import pytz

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
TOPIC_ID = "958"  # KAP Haberleri Konusu (Topic)

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mesaj,
        'parse_mode': 'Markdown',
        'message_thread_id': TOPIC_ID,
        'disable_web_page_preview': False
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            print(f"Telegram Hatası: {res.text}")
    except Exception as e:
        print(f"Gönderim hatası: {e}")

def kap_akisi_taramasi():
    print("KAP verileri çekiliyor...")
    url = "https://www.kap.org.tr/tr/api/disclosures"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        bildirimler = response.json()
        
        tr_tz = pytz.timezone('Europe/Istanbul')
        
        # TEST MODU: Zaman filtresini şimdilik kaldırdım. 
        # Son gelen 5 haberi saati ne olursa olsun gruba atar.
        for haber in bildirimler[:5]: 
            tarih_ms = haber.get('publishDate')
            haber_vakti = datetime.fromtimestamp(tarih_ms / 1000.0, tr_tz).strftime('%H:%M')
            
            sirket = haber.get('stockCodes', 'GENEL')
            baslik = haber.get('disclosureIndex', {}).get('title', 'KAP Bildirimi')
            ozet = haber.get('summary', 'Özet bulunmuyor.')
            h_id = haber.get('disclosureIndex', {}).get('id')
            link = f"https://www.kap.org.tr/tr/Bildirim/{h_id}"

            mesaj = (f"🔔 *YENİ KAP BİLDİRİMİ* [{haber_vakti}]\n\n"
                     f"🏢 *Şirket:* {sirket}\n"
                     f"📜 *Konu:* {baslik}\n"
                     f"📝 *Özet:* {ozet[:300]}...\n\n" # Özet çok uzunsa keser
                     f"🔗 [Bildirimi Aç]({link})")
            
            telegram_gonder(mesaj)
            print(f"Gönderildi: {sirket}")

    except Exception as e:
        print(f"KAP Veri Hatası: {e}")

if __name__ == "__main__":
    kap_akisi_taramasi()
