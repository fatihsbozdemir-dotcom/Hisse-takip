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
    # BIST Hisse Listesini Çek
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {"filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
               "options": {"lang": "tr"}, "columns": ["name"], "range": [0, 1000]}
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        hisseler = [item['d'][0] for item in res.get("data", [])]
        
        telegram_gonder("📉 *Günlük Hacim Kuruması Taraması Başladı...*\n(Günlük Mum + 20 Günlük Hacim Ortalaması Altı)")

        for sembol in hisseler:
            # Günlük veri çek (Hem analiz hem grafik için GÜNLÜK)
            df = yf.download(f"{sembol}.IS", period="3mo", interval="1d", progress=False)
            
            if df.empty or len(df) < 21: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # --- HACİM KONTROLÜ (GÜNLÜK) ---
            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
            su_anki_vol = df['Volume'].iloc[-1]
            ort_vol = df['Vol_MA20'].iloc[-1]

            # KRİTER: Bugünün hacmi, son 20 günün ortalamasının ALTINDAYSA
            if su_anki_vol < ort_vol:
                resim_adi = f"{sembol}_gunluk_kuruma.png"
                
                # Sade Grafik: Sadece Günlük Mumlar, Hacim ve Fiyat
                mpf.plot(df, type='candle', style='charles', volume=True,
                         title=f"\n{sembol} - GUNLUK HACIM KURUMASI", savefig=resim_adi)
                
                son_mum = df.iloc[-1]
                oran = (su_anki_vol / ort_vol) * 100
                bilgi = (f"📉 *{sembol}* (Günlük)\n"
                         f"📊 Hacim: Ortalamanın `% {oran:.1f}` kadarı.\n"
                         f"💰 Fiyat: `{son_mum['Close']:.2f}`\n"
                         f"↕️ H: `{son_mum['High']:.2f}` | L: `{son_mum['Low']:.2f}`")
                
                telegram_gonder(bilgi, resim_adi)
                os.remove(resim_adi)

        telegram_gonder("✅ Günlük hacim kuruması raporu bitti.")

    except Exception as e:
        telegram_gonder(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
