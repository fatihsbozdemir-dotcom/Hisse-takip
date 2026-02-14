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

def t_grafik_gonder(dosya_yolu, hisse):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(dosya_yolu, 'rb') as photo:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': f"📊 {hisse} Haftalık Grafik (EMA 144/200)"}, files={'photo': photo})

def analiz():
    # TradingView API'den tüm BIST hisselerini çek (Haftalık veri)
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA144|52", "EMA200|52"],
        "range": [0, 400]
    }
    
    try:
        res = requests.post(url, json=payload).json()
        hisseler = res.get("data", [])
        
        for item in hisseler:
            d = item['d']
            hisse, fiyat, e144, e200 = d[0], d[1], d[2], d[3]
            
            if e144 and e200:
                # %3 yakınlık kontrolü
                if (0.97 <= fiyat/e144 <= 1.03) or (0.97 <= fiyat/e200 <= 1.03):
                    # Grafik çizimi için Yahoo'dan veri çek
                    df = yf.download(f"{hisse}.IS", period="2y", interval="1wk", progress=False)
                    if df.empty: continue
                    
                    # EMA'ları hesapla
                    df['EMA144'] = df['Close'].ewm(span=144, adjust=False).mean()
                    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
                    
                    # Grafik ayarları
                    dosya = f"{hisse}.png"
                    ek_izimler = [
                        mpf.make_addplot(df['EMA144'], color='orange', width=1.5),
                        mpf.make_addplot(df['EMA200'], color='red', width=1.5)
                    ]
                    
                    mpf.plot(df, type='candle', style='charles', 
                             addplot=ek_izimler, volume=True, 
                             title=f"\n{hisse} - WEEKLY",
                             savefig=dosya, tight_layout=True)
                    
                    # Telegram'a gönder
                    t_grafik_gonder(dosya, hisse)
                    os.remove(dosya) # Sunucuda yer kaplamasın

    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
