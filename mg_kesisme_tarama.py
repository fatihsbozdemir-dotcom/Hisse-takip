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

def t_grafik_gonder(dosya_yolu, hisse, fiyat, ema_tip, ema_val):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    caption = f"📊 *{hisse}* - Haftalık Grafik\n💰 Fiyat: {fiyat:.2f}\n🛡️ {ema_tip}: {ema_val:.2f}"
    with open(dosya_yolu, 'rb') as photo:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': photo})

def analiz():
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
        
        found_count = 0
        total_scanned = len(hisseler)
        
        for item in hisseler:
            d = item['d']
            hisse, fiyat, e144, e200 = d[0], d[1], d[2], d[3]
            
            if e144 and e200:
                # KRİTER: Test için %10 yakınlığa çekiyoruz (Sonra istersen daraltırız)
                yakınlık = 0.10 
                
                if (1 - yakınlık <= fiyat/e144 <= 1 + yakınlık) or (1 - yakınlık <= fiyat/e200 <= 1 + yakınlık):
                    found_count += 1
                    # Grafik verisini çek
                    df = yf.download(f"{hisse}.IS", period="3y", interval="1wk", progress=False)
                    if df.empty: continue
                    
                    # EMA'ları tekrar hesapla (Grafikte düzgün görünmesi için)
                    df['EMA144'] = df['Close'].ewm(span=144, adjust=False).mean()
                    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
                    
                    dosya = f"{hisse}.png"
                    ek_izimler = [
                        mpf.make_addplot(df['EMA144'], color='orange', width=1.2),
                        mpf.make_addplot(df['EMA200'], color='red', width=1.2)
                    ]
                    
                    mpf.plot(df, type='candle', style='charles', 
                             addplot=ek_izimler, volume=True, 
                             title=f"\n{hisse} (Weekly Support Search)",
                             savefig=dosya, tight_layout=True)
                    
                    # Hangi EMA'ya yakınsa onu belirt
                    tip = "EMA 144" if abs(fiyat-e144) < abs(fiyat-e200) else "EMA 200"
                    val = e144 if tip == "EMA 144" else e200
                    
                    t_grafik_gonder(dosya, hisse, fiyat, tip, val)
                    os.remove(dosya)

        if found_count == 0:
            t_mesaj(f"✅ Tarama bitti. {total_scanned} hisse kontrol edildi, ancak haftalık EMA 144/200'e %10 yakınlıkta hisse bulunamadı.")
        else:
            t_mesaj(f"✅ Tarama tamamlandı. {found_count} adet potansiyel destek hissesi grafiği gönderildi.")

    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
