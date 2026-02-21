import requests
from datetime import datetime, timedelta
import pytz
import os

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
TOPIC_ID = "958"  # KAP/Haber Akışı Konusu

# Takip etmek istediğin X kullanıcıları (RSS tabanlı bir servis üzerinden çekilebilir)
# Ücretsiz ve stabil olması için şimdilik sadece KAP odaklı, 
# ancak X haberleri için "nitter" linkleri eklenebilir.
X_KAYNAKLARI = ["kap_haber", "borsagundem", "bloomberght"]

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': mesaj,
        'parse_mode': 'Markdown',
        'message_thread_id': TOPIC_ID,
        'disable_web_page_preview': False
    }
    requests.post(url, json=payload)

def kap_akisi():
    print("KAP Bildirimleri taranıyor...")
    url = "https://www.kap.org.tr/tr/api/disclosures"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        bildirimler = response.json()
        tr_tz = pytz.timezone('Europe/Istanbul')
        simdi = datetime.now(tr_tz)
        # GitHub Actions 30 dakikada bir çalışacağı için son 35 dakikayı tarıyoruz
        zaman_esigi = simdi - timedelta(minutes=35)

        for haber in bildirimler[:20]:
            tarih_ms = haber.get('publishDate')
            haber_vakti = datetime.fromtimestamp(tarih_ms / 1000.0, tr_tz)

            if haber_vakti > zaman_esigi:
                sirket = haber.get('stockCodes', 'GENEL')
                baslik = haber.get('disclosureIndex', {}).get('title', 'KAP Bildirimi')
                ozet = haber.get('summary', 'Özet yok.')
                h_id = haber.get('disclosureIndex', {}).get('id')
                link = f"https://www.kap.org.tr/tr/Bildirim/{h_id}"

                mesaj = (f"📢 *KAP HABER AKIŞI*\n\n"
                         f"🏢 *Şirket:* {sirket}\n"
                         f"📌 *Konu:* {baslik}\n"
                         f"📝 *Özet:* {ozet}\n\n"
                         f"🔗 [KAP Bildirimi İçin Tıklayın]({link})")
                
                telegram_gonder(mesaj)
    except Exception as e:
        print(f"KAP Hatası: {e}")

def x_haber_akisi_simulasyon():
    """
    X (Twitter) için ücretsiz API kalmadığından, 
    buraya önemli haber sitelerinin RSS linkleri veya 
    Twitter linklerini otomatik arayan bir yapı eklenebilir.
    """
    # Şimdilik ana haber başlıklarını X linki olarak ekliyoruz
    # İleride profesyonel bir haber API'si (NewsAPI vb.) ekleyebiliriz.
    pass

if __name__ == "__main__":
    kap_akisi()
    x_haber_akisi_simulasyon()
