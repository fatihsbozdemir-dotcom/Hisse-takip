import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except: pass

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    # Formasyonlar için son 2 haftanın verisi gerekiyor (Açılış, Yüksek, Düşük, Kapanış)
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "open|52", "low|52", "high|52", "prev_close|52", "open_prev|52"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        hisseler = res.get("data", [])
        t_mesaj("🚀 *Büyük Yükseliş Formasyonları Taraması Başladı...*")

        for item in hisseler:
            d = item.get('d', [])
            hisse = d[0]
            c1, o1, l1, h1 = d[1], d[2], d[3], d[4] # Bu haftanın verileri
            c2, o2 = d[5], d[6]                     # Geçen haftanın verileri (Yutan Boğa vb. için)
            
            if not all([c1, o1, l1, h1, c2, o2]): continue

            formasyon = None
            body1 = abs(c1 - o1)
            lower_s1 = min(o1, c1) - l1
            upper_s1 = h1 - max(o1, c1)
            
            # 1. ÇEKİÇ (Hammer)
            if (lower_s1 > body1 * 2) and (upper_s1 < body1 * 0.5) and body1 > 0:
                formasyon = "🔨 Çekiç (Hammer)"
            
            # 2. TERS ÇEKİÇ (Inverted Hammer)
            elif (upper_s1 > body1 * 2) and (lower_s1 < body1 * 0.5) and body1 > 0:
                formasyon = "inverted_hammer" # Genelde dipte anlamlıdır
                formasyon = "⛏️ Ters Çekiç"

            # 3. YUTAN BOĞA (Bullish Engulfing)
            # Geçen hafta kırmızı, bu hafta yeşil ve bu haftanın gövdesi geçen haftayı yutuyor
            elif c2 < o2 and c1 > o1 and c1 > o2 and o1 < c2:
                formasyon = "🌊 Yutan Boğa (Engulfing)"

            # 4. DELEN ÇİZGİ (Piercing Line)
            # Geçen hafta kırmızı, bu hafta geçen haftanın orta noktasının üzerinde kapatıyor
            elif c2 < o2 and c1 > o1 and o1 < l1*1.05 and c1 > (o2 + c2)/2 and c1 < o2:
                formasyon = "🌅 Delen Çizgi (Piercing)"

            if formasyon:
                df = yf.download(f"{hisse}.IS", period="1y", interval="1wk", progress=False)
                if df.empty: continue
                
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                
                dosya = f"{hisse}_form.png"
                mpf.plot(df, type='candle', style='charles', volume=True,
                         title=f"\n{hisse} - {formasyon}", savefig=dosya)
                
                caption = (f"🔥 *{hisse}* - Formasyon Tespit Edildi!\n"
                           f"📊 Formasyon: `{formasyon}`\n"
                           f"💰 Güncel Fiyat: `{c1:.2f}`\n"
                           f"📈 Haftalık Yüksek: `{h1:.2f}`\n"
                           f"📉 Haftalık Düşük: `{l1:.2f}`")
                
                with open(dosya, 'rb') as photo:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                                  files={'photo': photo})
                os.remove(dosya)

    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
