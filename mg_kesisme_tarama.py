
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
    caption = f"📊 *{hisse}* - Haftalık Grafik\n💰 Fiyat: {fiyat:.2f}\n🛡️ {ema_tip}: {ema_val:.2f}\n⚠️ Haftalık ana destek bölgesinde!"
    with open(dosya_yolu, 'rb') as photo:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, files={'photo': photo})

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # Range değerini 1000 yaparak BIST'teki TÜM hisseleri kapsama alıyoruz
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA144|52", "EMA200|52"],
        "sort": {"sortBy": "name", "sortOrder": "asc"},
        "range": [0, 1000] 
    }
    
    try:
        res = requests.post(url, json=payload).json()
        hisseler = res.get("data", [])
        
        found_count = 0
        total_scanned = len(hisseler)
        
        # Kullanıcıya kaç hisse tarandığını bildirelim
        t_mesaj(f"🔍 Tarama Başladı: Toplam *{total_scanned}* hisse analiz ediliyor...")
        
        for item in hisseler:
            d = item['d']
            hisse, fiyat, e144, e200 = d[0], d[1], d[2], d[3]
            
            # Veri varlığı kontrolü
            if e144 and e200 and fiyat:
                # KRİTER: Fiyat EMA144 veya EMA200'ün %10 yakınındaysa
                # (Haftalıkta %10, dönüşün başladığı 'ilgi alanını' temsil eder)
                if (0.90 <= fiyat/e144 <= 1.10) or (0.90 <= fiyat/e200 <= 1.10):
                    found_count += 1
                    
                    # Yahoo'dan veri çek (IS uzantısı ile)
                    df = yf.download(f"{hisse}.IS", period="4y", interval="1wk", progress=False)
                    if df.empty or len(df) < 144: continue # Yeterli geçmişi yoksa atla
                    
                    # Grafik için indikatörleri hesapla
                    df['EMA144'] = df['Close'].ewm(span=144, adjust=False).mean()
                    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
                    
                    dosya = f"{hisse}.png"
                    ek_izimler = [
                        mpf.make_addplot(df['EMA144'], color='orange', width=1.5),
                        mpf.make_addplot(df['EMA200'], color='red', width=1.5)
                    ]
                    
                    mpf.plot(df, type='candle', style='charles', 
                             addplot=ek_izimler, volume=True, 
                             title=f"\n{hisse} - Weekly Support Zone",
                             savefig=dosya, tight_layout=True)
                    
                    tip = "EMA 144" if abs(fiyat-e144) < abs(fiyat-e200) else "EMA 200"
                    val = e144 if tip == "EMA 144" else e200
                    
                    t_grafik_gonder(dosya, hisse, fiyat, tip, val)
                    os.remove(dosya)

        if found_count == 0:
            t_mesaj(f"✅ Tarama bitti. {total_scanned} hissenin hiçbirinde haftalık EMA 144/200'e yakınlık (±%10) tespit edilemedi.")
        else:
            t_mesaj(f"✅ İşlem tamam! Kriterlere uyan {found_count} hissenin grafiği yukarıda.")

    except Exception as e:
        t_mesaj(f"❌ Kritik Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
