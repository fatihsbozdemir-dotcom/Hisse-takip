import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import pandas_ta as ta

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        bulunan = 0
        for hisse in df_sheet.iloc[:, 0].dropna():
            t_name = f"{str(hisse).strip()}.IS"
            hist = yf.Ticker(t_name).history(period="3mo")
            if len(hist) < 20: continue
            
            # WMA Hesaplama
            hist['WMA9'] = ta.wma(hist['Close'], length=9)
            hist['WMA15'] = ta.wma(hist['Close'], length=15)
            
            cur_vol = hist['Volume'].iloc[-1]
            max_vol = hist['Volume'].tail(10).max()
            
            if cur_vol == max_vol:
                bulunan += 1
                buf = io.BytesIO()
                mpf.plot(hist.tail(40), type='candle', volume=True, savefig=dict(fname=buf, format='png'))
                buf.seek(0)
                msg = f"📊 *{hisse}* - 🔥 YÜKSEK HACİM\n💰 Fiyat: {hist['Close'].iloc[-1]:.2f}"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': f"✅ Tarama bitti. {bulunan} sinyal paylaşıldı."})
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': f"❌ Hata: {str(e)}"})

if __name__ == "__main__":
    analiz()
