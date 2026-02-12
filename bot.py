import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import datetime

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def analiz():
    try:
        # BOT BAŞLADI TESTİ
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': '🤖 Tarama denemesi yapılıyor...'})

        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]

        for _, row in df.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            hedef = row.get('Hedef_Fiyat', 0)
            try: hedef = float(hedef)
            except: hedef = 0
            
            t_name = f"{hisse}.IS" if not hisse.endswith(".IS") else hisse
            hist = yf.Ticker(t_name).history(period="1y", interval="1wk")
            
            if hist.empty: continue
            
            # SADECE TEST İÇİN: Hedef fiyat olan her şeyi bildir
            if hedef > 0:
                buf = io.BytesIO()
                mpf.plot(hist.tail(20), type='candle', style='charles', savefig=dict(fname=buf, format='png'))
                buf.seek(0)
                msg = f"📢 *ANALİZ*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {hist['Close'].iloc[-1]:.2f}\n🎯 *Hedef:* {hedef:.2f}"
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata: {str(e)}'})

if __name__ == "__main__":
    analiz()
