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
    
    # En stabil filtre yapısı
    payload = {
        "filter": [
            {"left": "EMA20", "operation": "above", "right": "EMA50"},
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}
        ],
        "options": {"lang": "tr"},
        "markets": ["turkey"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": ["name", "close", "EMA20", "EMA50", "change"],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 100]
    }

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            t_mesaj(f"⚠️ TV Sunucusu hata döndürdü: {response.status_code}")
            return

        res_data = response.json()
        
        # 'NoneType' hatasını engelleyen kritik kontrol
        if not res_data or "data" not in res_data or res_data["data"] is None:
            t_mesaj("🔍 Şu an TV kriterlerine uyan aktif hisse verisi bulunamadı (Borsa kapalı veya filtreye uygun hisse yok).")
            return

        bulunanlar = []
        for item in res_data["data"]:
            # Veri içeriği kontrolü
            if "d" in item and len(item["d"]) >= 4:
                hisse = item['d'][0]
                fiyat = item['d'][1]
                e20 = item['d'][2]
                e50 = item['d'][3]
                
                # Sadece yeni kesişenleri (fark %1'den küçük olanlar) alalım
                if e20 and e50: # Verilerin None olmadığını kontrol et
                    fark = (e20 - e50) / e50
                    if 0 < fark < 0.01: # %1 esneklik payı
                        bulunanlar.append(f"🔥 *{hisse}*\n✅ EMA 20/50 Üstünde\n💰 Fiyat: {fiyat:.2f}\n🎯 Fark: %{fark*100:.2f}")

        if bulunanlar:
            t_mesaj("🚀 *TRADINGVIEW CANLI TARAMA*\n\n" + "\n\n".join(bulunanlar[:15]))
        else:
            t_mesaj("✅ Tarama yapıldı, kriterlerinize uygun yeni kesişmiş hisse şu an yok.")

    except Exception as e:
        t_mesaj(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
