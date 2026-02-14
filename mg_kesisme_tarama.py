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
    
    # Her iki kesişme türünü ve gerekli ek verileri (Hacim, RSI) istiyoruz
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}
        ],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "WMA9", "WMA15", "EMA20", "EMA50", "relative_volume_10d_calc", "RSI"],
        "sort": {"sortBy": "relative_volume_10d_calc", "sortOrder": "desc"},
        "range": [0, 250] # Daha geniş bir havuzda tarıyoruz
    }

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        res_data = response.json()
        
        if not res_data or "data" not in res_data:
            t_mesaj("🔍 Veri çekilemedi.")
            return

        wma_list = []
        ema_list = []

        for item in res_data["data"]:
            d = item.get("d", [])
            hisse = d[0]
            fiyat = d[1]
            w9, w15 = d[2], d[3]
            e20, e50 = d[4], d[5]
            hacim_artisi = d[6] if d[6] else 0 # 10 günlük ortalamaya göre hacim katı
            rsi = d[7] if d[7] else 0

            # --- STRATEJİ 1: WMA 9/15 (Kısa Vade) ---
            if w9 and w15:
                w_fark = (w9 - w15) / w15
                if 0 < w_fark < 0.005: # %0.5 taze kesişme
                    wma_list.append(f"⚡ *{hisse}*\n💰 {fiyat:.2f} | 📊 Hacim: {hacim_artisi:.1f}x | 🕯 RSI: {rsi:.0f}")

            # --- STRATEJİ 2: EMA 20/50 (Orta Vade) ---
            if e20 and e50:
                e_fark = (e20 - e50) / e50
                if 0 < e_fark < 0.007: # %0.7 taze kesişme
                    ema_list.append(f"🔥 *{hisse}*\n💰 {fiyat:.2f} | 📊 Hacim: {hacim_artisi:.1f}x | 🕯 RSI: {rsi:.0f}")

        # Mesajları Birleştir ve Gönder
        if wma_list:
            t_mesaj("🚀 *WMA 9/15 TAZE KESİŞMELER (Kısa Vade)*\n\n" + "\n\n".join(wma_list[:15]))
        
        if ema_list:
            t_mesaj("💹 *EMA 20/50 TAZE KESİŞMELER (Orta Vade)*\n\n" + "\n\n".join(ema_list[:15]))

        if not wma_list and not ema_list:
            t_mesaj("✅ Bugün kriterlere uyan yeni bir kesişme yakalanamadı.")

    except Exception as e:
        t_mesaj(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
