import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    # Günlük ve Haftalık tüm önemli ortalamaları çekiyoruz
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA20", "EMA50", "EMA100", "EMA200", "EMA144|52", "EMA200|52", "open", "low", "high"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload).json()
        hisseler = res.get("data", [])
        t_mesaj(f"🕵️‍♂️ *{len(hisseler)}* hisse tüm ortalamalarda (20, 50, 100, 144, 200) taranıyor...")

        for item in hisseler:
            d = item['d']
            hisse, fiyat = d[0], d[1]
            # Günlük EMA'lar
            emas = {"EMA20": d[2], "EMA50": d[3], "EMA100": d[4], "EMA200": d[5]}
            # Haftalık EMA'lar
            emas_w = {"W-EMA144": d[6], "W-EMA200": d[7]}
            
            # Mum Verileri (Çekiç Kontrolü İçin)
            acilis, dusuk, yuksek = d[8], d[9], d[10]
            
            # 1. ÇEKİÇ MUM KONTROLÜ (Basit Mantık)
            # Gövde küçük, alt fitil gövdenin en az 2 katı
            body = abs(fiyat - acilis)
            lower_shadow = min(acilis, fiyat) - dusuk
            is_hammer = lower_shadow > (body * 2) and body > 0
            
            # 2. ORTALAMA TEMAS KONTROLÜ
            hit_ema = None
            # Tüm günlük ve haftalık ortalamaları kontrol et
            all_emas = {**emas, **emas_w}
            for name, val in all_emas.items():
                if val and (0.985 <= fiyat/val <= 1.015): # %1.5 yakınlık (Tam temas veya hafif üstü)
                    hit_ema = name
                    break
            
            if hit_ema:
                # Grafik çiz ve gönder
                status = "🔨 ÇEKİÇ + DESTEK" if is_hammer else "🛡️ DESTEK TEMASI"
                
                df = yf.download(f"{hisse}.IS", period="1y", interval="1d", progress=False)
                if df.empty: continue
                
                # Grafikte hangisi temas ettiyse onu ve EMA200'ü gösterelim
                df['MA_HIT'] = df['Close'].ewm(span=int(''.join(filter(str.isdigit, hit_ema))), adjust=False).mean()
                
                dosya = f"{hisse}.png"
                ap = [mpf.make_addplot(df['MA_HIT'], color='cyan', width=1.5)]
                
                mpf.plot(df, type='candle', style='charles', addplot=ap, volume=True,
                         title=f"\n{hisse} - {hit_ema} {status}", savefig=dosya)
                
                caption = f"✅ *{hisse}*\n📍 Temas: `{hit_ema}`\n💰 Fiyat: {fiyat:.2f}\n{status}"
                
                with open(dosya, 'rb') as photo:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                                  files={'photo': photo})
                os.remove(dosya)

    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
