import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os
import numpy as np

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except: pass

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        data = res.get("data", [])
        if not data: return

        t_mesaj(f"🚀 *{len(data)}* hisse taranıyor, formasyonlar işaretleniyor...")

        for item in data:
            hisse = item['d'][0]
            df = yf.download(f"{hisse}.IS", period="6mo", interval="1wk", progress=False)
            
            if df.empty or len(df) < 5: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # Son mum verileri
            m1 = df.iloc[-1] # Bu hafta
            m2 = df.iloc[-2] # Geçen hafta
            
            formasyon = None
            body1 = abs(m1['Close'] - m1['Open'])
            lower_s1 = min(m1['Open'], m1['Close']) - m1['Low']
            upper_s1 = m1['High'] - max(m1['Open'], m1['Close'])
            
            # --- Formasyon Kontrolleri ---
            if (lower_s1 > body1 * 2) and (upper_s1 < body1 * 0.5) and body1 > 0:
                formasyon = "🔨 Çekiç"
            elif (upper_s1 > body1 * 2) and (lower_s1 < body1 * 0.5) and body1 > 0:
                formasyon = "⛏️ Ters Çekiç"
            elif m2['Close'] < m2['Open'] and m1['Close'] > m1['Open'] and m1['Close'] >= m2['Open'] and m1['Open'] <= m2['Close']:
                formasyon = "🌊 Yutan Boğa"

            if formasyon:
                # İşaretleme için bir liste oluştur (Sadece son muma değer koy, gerisi NaN)
                markers = [np.nan] * len(df)
                # Formasyonun olduğu yerin altına işaret koymak için fiyatın %2 altını seçelim
                markers[-1] = df['Low'].iloc[-1] * 0.98 
                
                # İşaretleyici Ayarı (Mavi bir yukarı ok)
                ap = [mpf.make_addplot(markers, type='scatter', marker='^', markersize=200, color='blue')]
                
                dosya = f"{hisse}_isaretli.png"
                mpf.plot(df, type='candle', style='charles', volume=True,
                         addplot=ap, title=f"\n{hisse} - {formasyon}", savefig=dosya)
                
                caption = f"🔥 *{hisse}*\n📊 Formasyon: `{formasyon}`\n💰 Fiyat: `{m1['Close']:.2f}`\n📍 İşaretli bölgeye dikkat!"
                
                with open(dosya, 'rb') as photo:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                                  files={'photo': photo})
                os.remove(dosya)

        t_mesaj("✅ İşaretli tarama tamamlandı.")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz()
