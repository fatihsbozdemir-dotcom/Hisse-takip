import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except: pass

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # Dip tespiti için RSI, Bollinger ve EMA 200 kolonlarını ekliyoruz
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}
        ],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "RSI", "BB.lower", "BB.upper", "EMA200", "change", "relative_volume_10d_calc"],
        "sort": {"sortBy": "RSI", "sortOrder": "asc"}, # En düşük RSI'dan (dipten) başla
        "range": [0, 300]
    }

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        res_data = response.json()
        
        if not res_data or "data" not in res_data: return

        dip_adaylari = []

        for item in res_data["data"]:
            d = item.get("d", [])
            hisse, fiyat, rsi, bb_alt, bb_ust, ema200, degisim, hacim = d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]

            if all(v is not None for v in [fiyat, rsi, bb_alt, ema200]):
                
                # KRİTER 1: RSI Aşırı Satım Bölgesinden Dönüyor (30-40 arası)
                # KRİTER 2: Fiyat Bollinger Alt Bandına Değmiş veya Çok Yakın
                # KRİTER 3: Fiyat EMA 200'ün Maksimum %3 Üzerinde (Zemine Yakınlık)
                
                bollinger_temas = fiyat <= bb_alt * 1.01 # Alt bandın %1 içinde
                ema200_destek = (fiyat >= ema200) and (fiyat <= ema200 * 1.03)
                rsi_dip = 25 < rsi < 42
                
                if (rsi_dip and bollinger_temas) or (ema200_destek and rsi_dip):
                    durum = "🛡️ EMA 200 DESTEĞİ" if ema200_destek else "🕳️ BB ALT BANT DİBİ"
                    dip_adaylari.append(f"💎 *{hisse}*\n📢 {durum}\n💰 Fiyat: {fiyat:.2f} | 🕯 RSI: {rsi:.1f}\n📊 Hacim: {hacim:.1f}x")

        if dip_adaylari:
            t_mesaj("⚓ *POTANSİYEL DİP OLUŞUMU YAPANLAR*\n_Bu hisseler teknik destek seviyelerinde bulunuyor._\n\n" + "\n\n".join(dip_adaylari[:15]))
        else:
            t_mesaj("✅ Bugün teknik dip formasyonuna uyan hisse bulunamadı.")

    except Exception as e:
        t_mesaj(f"❌ Dip Tarama Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
