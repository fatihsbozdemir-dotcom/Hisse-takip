import requests

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        pass

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # "above" yerine "greater" kullanarak API hatasını gideriyoruz
    payload = {
        "filter": [
            {"left": "EMA20", "operation": "greater", "right": "EMA50"},
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}
        ],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA20", "EMA50"],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 150]
    }

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            t_mesaj(f"⚠️ TV Hatası Devam Ediyor ({response.status_code}):\n{response.text[:100]}")
            return

        res_data = response.json()
        if not res_data or "data" not in res_data:
            t_mesaj("🔍 Eşleşen hisse bulunamadı.")
            return

        bulunanlar = []
        for item in res_data["data"]:
            d = item.get("d", [])
            hisse = d[0]
            fiyat = d[1]
            e20 = d[2]
            e50 = d[3]
            
            if e20 and e50:
                fark = (e20 - e50) / e50
                # Yeni kesişmiş veya taze trend (%1 marj)
                if 0 < fark < 0.01:
                    bulunanlar.append(f"🔥 *{hisse}*\n✅ EMA 20/50 Üstünde\n💰 Fiyat: {fiyat:.2f}\n🎯 Fark: %{fark*100:.2f}")

        if bulunanlar:
            t_mesaj("🚀 *TRADINGVIEW GÜNLÜK TARAMA (EMA 20/50)*\n\n" + "\n\n".join(bulunanlar[:20]))
        else:
            t_mesaj("✅ Şu an EMA 20/50 yeni kesişmiş hisse bulunamadı.")

    except Exception as e:
        t_mesaj(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
