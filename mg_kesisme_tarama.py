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
    # EMA 20'yi columns listesinden çıkardık
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA50", "EMA100", "EMA200", "EMA144|52", "EMA200|52", "open", "low", "high"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload).json()
        hisseler = res.get("data", [])
        t_mesaj(f"🕵️‍♂️ *{len(hisseler)}* hisse majör ortalamalarda (50, 100, 144, 200) taranıyor...")

        for item in hisseler:
            d = item['d']
            hisse, fiyat = d[0], d[1]
            # EMA 20'yi all_emas sözlüğünden de çıkardık
            all_emas = {"EMA50": d[2], "EMA100": d[3], "EMA200": d[4], "W-EMA144": d[5], "W-EMA200": d[6]}
            acilis, dusuk, yuksek = d[7], d[8], d[9]
            
            # --- ÇEKİÇ KONTROLÜ ---
            body = abs(fiyat - acilis)
            lower_shadow = min(acilis, fiyat) - dusuk
            # Çekiç: Alt fitil gövdenin en az 2 katı ve fiyat açılışın üzerinde (boğa çekici) veya yakınında
            is_hammer = lower_shadow > (body * 2) and body > 0
            
            # --- DESTEK KONTROLÜ ---
            hit_ema = None
            for name, val in all_emas.items():
                if val and (0.99 <= fiyat/val <= 1.01): # %1 yakınlık (Daha hassas yaptık)
                    hit_ema = name
                    break
            
            if hit_ema:
                df = yf.download(f"{hisse}.IS", period="1y", interval="1d", progress=False)
                
                if df.empty or len(df) < 5: continue
                
                # Multi-index temizliği
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df = df.dropna()

                # Grafiğe basılacak EMA'yı hesapla
                # Haftalık EMA ise günlüğe yaklaşık çeviriyoruz (Örn: W144 için yaklaşık değer)
                if "W-" in hit_ema:
                    ema_period = 200 # Haftalık temaslarda görsel referans için EMA 200 gösterilsin
                else:
                    ema_period = int(''.join(filter(str.isdigit, hit_ema)))
                
                df['MA_HIT'] = df['Close'].ewm(span=ema_period, adjust=False).mean()
                
                dosya = f"{hisse}.png"
                ap = [mpf.make_addplot(df['MA_HIT'], color='cyan', width=1.5)]
                
                status = "🔨 ÇEKİÇ + DESTEK" if is_hammer else "🛡️ DESTEK TEMASI"
                
                mpf.plot(df, type='candle', style='charles', addplot=ap, volume=True,
                         title=f"\n{hisse} - {hit_ema}", savefig=dosya)
                
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
