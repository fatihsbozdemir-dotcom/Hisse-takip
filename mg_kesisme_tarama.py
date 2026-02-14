import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

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
    
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA144", "EMA144|52", "open", "low"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        hisseler = res.get("data", [])
        
        t_mesaj(f"🎯 *{len(hisseler)}* hisse sadece *EMA 144* desteği için taranıyor...")

        found_any = False
        for item in hisseler:
            d = item.get('d', [])
            if len(d) < 6: continue
            
            hisse, fiyat = d[0], d[1]
            ema_g, ema_h = d[2], d[3]
            acilis, dusuk = d[4], d[5]
            
            # --- EMA 144 TEMAS KONTROLÜ (%1.5 Esneklik) ---
            hit_ema = None
            if ema_g and (0.985 <= fiyat/ema_g <= 1.015):
                hit_ema = "Günlük EMA 144"
            elif ema_h and (0.985 <= fiyat/ema_h <= 1.015):
                hit_ema = "Haftalık EMA 144"
            
            if hit_ema:
                found_any = True
                # Mum yapısı: Çekiç kontrolü
                body = abs(fiyat - acilis)
                lower_shadow = min(acilis, fiyat) - dusuk
                is_hammer = lower_shadow > (body * 2) and body > 0
                
                # Grafik çizimi
                df = yf.download(f"{hisse}.IS", period="2y", interval="1d", progress=False)
                if df.empty: continue
                
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df = df.dropna()

                df['EMA144'] = df['Close'].ewm(span=144, adjust=False).mean()
                
                dosya = f"{hisse}.png"
                ap = [mpf.make_addplot(df['EMA144'], color='orange', width=1.5)]
                
                status = "🔨 ÇEKİÇ + DESTEK" if is_hammer else "🛡️ DESTEK TEMASI"
                
                mpf.plot(df, type='candle', style='charles', addplot=ap, volume=True,
                         title=f"\n{hisse} - {hit_ema}", savefig=dosya)
                
                caption = f"💎 *{hisse}*\n📍 Temas: `{hit_ema}`\n💰 Fiyat: {fiyat:.2f}\n{status}"
                
                with open(dosya, 'rb') as photo:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                                  files={'photo': photo})
                os.remove(dosya)

        if not found_any:
            t_mesaj("✅ Tarama bitti, şu an EMA 144 bölgesinde hisse yok.")

    except Exception as e:
        t_mesaj(f"❌ Hata oluştu: {str(e)}")

if __name__ == "__main__":
    analiz()
