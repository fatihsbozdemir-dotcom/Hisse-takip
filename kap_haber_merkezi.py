import requests
from datetime import datetime
import pytz

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
TOPIC_ID = "958" 

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # 1. Deneme: Belirlenen konuya (Topic) gönder
    payload = {
        'chat_id': CHAT_ID,
        'text': mesaj,
        'parse_mode': 'Markdown',
        'message_thread_id': TOPIC_ID
    }
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            print(f"Konuya gönderilemedi, ana gruba deneniyor... Hata: {res.text}")
            # 2. Deneme: Eğer konu ID hatalıysa direkt ana gruba gönder
            payload.pop('message_thread_id')
            res = requests.post(url, json=payload)
            if res.status_code == 200:
                print("Mesaj ana gruba başarıyla gönderildi. Topic ID'yi kontrol et!")
        else:
            print("Mesaj konuya başarıyla gönderildi.")
    except Exception as e:
        print(f"Sistem Hatası: {e}")

def kap_akisi_taramasi():
    print("KAP verileri çekiliyor...")
    url = "https://www.kap.org.tr/tr/api/disclosures"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=25)
        bildirimler = response.json()
        
        # Test için son 3 bildirimi gönderiyoruz
        for haber in bildirimler[:3]: 
            sirket = haber.get('stockCodes', 'GENEL')
            baslik = haber.get('disclosureIndex', {}).get('title', 'KAP Bildirimi')
            h_id = haber.get('disclosureIndex', {}).get('id')
            link = f"https://www.kap.org.tr/tr/Bildirim/{h_id}"

            mesaj = (f"🔔 *KAP TEST MESAJI*\n\n"
                     f"🏢 *Şirket:* {sirket}\n"
                     f"📜 *Konu:* {baslik}\n"
                     f"🔗 [Bildirimi Aç]({link})")
            
            telegram_gonder(mesaj)
            
    except Exception as e:
        print(f"KAP Veri Hatası: {e}")

if __name__ == "__main__":
    kap_akisi_taramasi()
