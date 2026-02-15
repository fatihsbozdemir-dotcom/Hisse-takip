import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def telegram_gonder(mesaj, dosya=None):
    if dosya:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        try:
            with open(dosya, 'rb') as f:
                requests.post(url, data={'chat_id': CHAT_ID, 'caption': mesaj, 'parse_mode': 'Markdown'}, files={'photo': f})
        except: pass
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz_yap():
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {"filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
               "options": {"lang": "tr"}, "columns": ["name"], "range": [0, 500]}
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        hisseler = [item['d'][0] for item in res.get("data", [])]
        
        telegram_gonder("📉 *Hacim Kuruması Taraması* (Görseldeki Gibi Sert Düşüşler)")

        for sembol in hisseler:
            df = yf.download(f"{sembol}.IS", period="4mo", interval="1d", progress=False)
            if df.empty or len(df) < 25: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # 20 GÜNLÜK HACİM ORTALAMASI (Beyaz Çizgi İçin)
            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
            
            su_anki_vol = df['Volume'].iloc[-1]
            ort_vol = df['Vol_MA20'].iloc[-1]

            # KRİTER: Hacim, ortalamanın %50'sinden bile küçükse (Tam istediğin kuruma)
            if su_anki_vol < (ort_vol * 0.5):
                resim_adi = f"{sembol}.png"
                
                # Grafiğe beyaz hacim ortalamasını ekliyoruz (panel=1 hacim bölgesidir)
                ap = mpf.make_addplot(df['Vol_MA20'], panel=1, color='white', width=1.5)
                
                # Grafiği son 40 güne odaklayalım ki çubuklar net görünsün
                mpf.plot(df.tail(40), type='candle', style='charles', volume=True,
                         addplot=ap, title=f"\n{sembol} - HACIM KURUMASI", savefig=resim_adi)
                
                oran = (su_anki_vol / ort_vol) * 100
                bilgi = (f"📉 *{sembol}*\n"
                         f"📊 Hacim Oranı: `% {oran:.1f}` (Ortalamanın çok altında!)\n"
                         f"💰 Fiyat: `{df.iloc[-1]['Close']:.2f}`")
                
                telegram_gonder(bilgi, resim_adi)
                os.remove(resim_adi)

        telegram_gonder("✅ Tarama tamamlandı.")
    except Exception as e:
        telegram_gonder(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
