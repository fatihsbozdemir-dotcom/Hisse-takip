import requests
import json

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
    
    # TradingView'ın tam olarak beklediği ham sorgu yapısı
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
        "range": [0, 50]
    }

    try:
        response = requests.post(url, json=payload, timeout=20)
        data = response.json()
        
        if "data" not in data:
            t_mesaj("⚠️ TradingView'dan veri dönmedi.")
            return

        bulunanlar = []
        for item in data["data"]:
            # item['d'] içindeki sıra: 0: name, 1: close, 2: EMA20, 3: EMA50, 4: change
            hisse = item['d'][0]
            fiyat = item['d'][1]
            e20 = item['d'][2]
            e50 = item['d'][3]
            
            # Sadece yeni kesişenleri (fark %0.7'den küçük olanlar) alalım
            fark = (e20 - e50) / e50
            if 0 < fark < 0.007:
                bulunanlar.append(f"🔥 *{hisse}*\n✅ EMA 20/50 Üstünde\n💰 Fiyat: {fiyat:.2f}\n🎯 Fark: %{fark*100:.2f}")

        if bulunanlar:
            t_mesaj("🚀 *TRADINGVIEW HAM VERİ TARAMASI*\n\n" + "\n\n".join(bulunanlar[:20]))
        else:
            t_mesaj("🔍 Şu an TV kriterlerine göre yeni kesişmiş hisse bulunamadı.")

    except Exception as e:
        t_mesaj(f"❌ Kritik Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
