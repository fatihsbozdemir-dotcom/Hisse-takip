import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
TOPIC_ID = "958"

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # 1. Deneme: KAP Konusuna Gönder
    payload = {
        'chat_id': CHAT_ID,
        'text': mesaj,
        'parse_mode': 'Markdown',
        'message_thread_id': TOPIC_ID
    }
    
    print(f"Deneme 1: Konuya gönderiliyor (ID: {TOPIC_ID})...")
    r1 = requests.post(url, json=payload)
    
    if r1.status_code != 200:
        print(f"❌ Konu başarısız: {r1.text}")
        # 2. Deneme: Ana Gruba Gönder (Thread ID olmadan)
        print("Deneme 2: Ana gruba gönderiliyor...")
        payload.pop('message_thread_id')
        r2 = requests.post(url, json=payload)
        if r2.status_code == 200:
            print("✅ BAŞARILI: Mesaj ana gruba ulaştı!")
        else:
            print(f"❌ Ana grup da başarısız: {r2.text}")
    else:
        print("✅ BAŞARILI: Mesaj KAP konusuna ulaştı!")

if __name__ == "__main__":
    test_mesaji = "🚀 Bot Bağlantı Testi\nSistem: Aktif\nHaber Akışı: Beklemede"
    telegram_gonder(test_mesaji)
