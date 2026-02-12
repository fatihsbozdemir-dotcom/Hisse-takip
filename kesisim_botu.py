import yfinance as yf
import pandas as pd
import requests
import pandas_ta as ta

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz_et():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = df_sheet.iloc[:, 0].dropna()
        bulunan = 0
        
        for hisse in hisseler:
            t_name = f"{str(hisse).strip()}.IS"
            
            # --- GÜNLÜK ANALİZ ---
            d_hist = yf.Ticker(t_name).history(period="6mo", interval="1d")
            if len(d_hist) > 20:
                d_hist['W9'] = ta.wma(d_hist['Close'], length=9)
                d_hist['W15'] = ta.wma(d_hist['Close'], length=15)
                # Yukarı Kesişim Kontrolü
                if d_hist['W9'].iloc[-2] < d_hist['W15'].iloc[-2] and d_hist['W9'].iloc[-1] > d_hist['W15'].iloc[-1]:
                    t_mesaj(f"🚀 *{hisse}* - GÜNLÜKTE WMA 9-15 Kesişimi (AL)!")
                    bulunan += 1

            # --- HAFTALIK ANALİZ ---
            w_hist = yf.Ticker(t_name).history(period="1y", interval="1wk")
            if len(w_hist) > 20:
                w_hist['W9'] = ta.wma(w_hist['Close'], length=9)
                w_hist['W15'] = ta.wma(w_hist['Close'], length=15)
                # Yukarı Kesişim Kontrolü
                if w_hist['W9'].iloc[-2] < w_hist['W15'].iloc[-2] and w_hist['W9'].iloc[-1] > w_hist['W15'].iloc[-1]:
                    t_mesaj(f"🌟 *{hisse}* - HAFTALIKTA WMA 9-15 Kesişimi (GÜÇLÜ AL)!")
                    bulunan += 1

        t_mesaj(f"✅ Kesişim taraması bitti. Toplam {bulunan} sinyal bulundu.")
    except Exception as e:
        t_mesaj(f"❌ Kesişim Botu Hatası: {str(e)}")

if __name__ == "__main__":
    analiz_et()
