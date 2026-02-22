import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"

def id_bul():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    try:
        res = requests.get(url).json()
        if res["result"]:
            for update in res["result"]:
                # Mesaj veya Kanal postu fark etmeksizin ID'leri yakala
                msg = update.get("message") or update.get("channel_post")
                if msg:
                    chat_id = msg["chat"]["id"]
                    thread_id = msg.get("message_thread_id", "Konu ID bulunamadı")
                    print(f"\n✅ BULUNAN BİLGİLER:")
                    print(f"Grup (Chat) ID: {chat_id}")
                    print(f"Konu (Topic) ID: {thread_id}")
                    print(f"Mesaj Metni: {msg.get('text')}\n")
        else:
            print("❌ Yeni mesaj bulunamadı. Lütfen gruptaki KAP konusuna bir şey yazıp tekrar çalıştırın!")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    id_bul()
