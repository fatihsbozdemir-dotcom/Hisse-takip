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
    
    # Sadece Haftalık EMA 144 (EMA144|52) verisini çekiyoruz
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA144|52", "open|52", "low|52", "high|52"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        hisseler = res.get("data", [])
        
        t_mesaj(f"📅 *Haftalık Tarama:* {len(hisseler)} hisse sadece *Haftalık EMA 144* desteği için inceleniyor...")

        found_any = False
        for item in hisseler:
            d = item.get('d', [])
            if len(d) < 6: continue
            
            hisse, fiyat = d[0], d[1]
            ema_h = d[2]
            acilis_h, dusuk_h = d[3], d[4]
            
            # --- HAFTALIK EMA 144 TEMAS KONTROLÜ (%1.5 Esneklik) ---
            if ema_h and (0.985 <= fiyat/ema_h <= 1.015):
                found_any = True
                
                # Haftalık Mum Yapısı: Çekiç kontrolü
                body = abs(fiyat - acilis_h)
                lower_shadow = min(acilis_h, fiyat) - dusuk_h
                is_hammer = lower_shadow > (body * 2) and body > 0
                
                # Grafik çizimi (Haftalık veri çekiyoruz)
                df = yf.download(f"{hisse}.IS", period="5y", interval="1wk", progress=False)
                if df.empty: continue
                
                # Veri temizleme
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df = df.dropna()

                # Haftalık EMA 144 hesapla
                df['EMA144_W'] = df['Close'].ewm(span=144, adjust=False).mean()
                
                dosya = f"{hisse}_weekly.png"
                ap = [mpf.make_addplot(df['EMA144_W'], color='orange', width=1.5)]
                
                status = "🔨 HAFTALIK ÇEKİÇ" if is_hammer else "🛡️ HAFTALIK DESTEK"
                
                mpf.plot(df, type='candle', style='charles', addplot=ap, volume=True,
                         title=f"\n{hisse} - WEEKLY EMA 144", savefig=dosya)
                
                caption = f"💎 *{hisse}* (Haftalık)\n📍 Destek: `EMA 144`\n💰 Fiyat: {fiyat:.2f}\n{status}"
                
                with open(dosya, 'rb') as photo:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                                  files={'photo': photo})
                os.remove(dosya)

        if not found_any:
            t_mesaj("✅ Haftalık tarama bitti. Şu an Haftalık EMA 144 bölgesinde hisse yok.")

    except Exception as e:
        t_mesaj(f"❌ Hata oluştu: {str(e)}")

if __name__ == "__main__":
    analiz()
