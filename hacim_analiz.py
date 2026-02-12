import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import pandas_ta as ta
import sys

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                  json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz_et():
    try:
        # 1. Veri Okuma Kontrolü
        try:
            df_sheet = pd.read_csv(SHEET_URL)
        except Exception as e:
            t_mesaj(f"❌ Google Sheet okunamadı! Linki veya Sheet ID'yi kontrol et.\nHata: {str(e)}")
            return

        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        bulunan = 0
        
        # 2. Döngü
        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            t_name = f"{hisse}.IS" if not hisse.endswith(".IS") else hisse
            
            try:
                hist = yf.Ticker(t_name).history(period="3mo", interval="1d")
                if len(hist) < 20: continue

                # WMA ve Hacim
                hist['WMA9'] = ta.wma(hist['Close'], length=9)
                hist['WMA15'] = ta.wma(hist['Close'], length=15)
                guncel_hacim = hist['Volume'].iloc[-1]
                son_10_hacim = hist['Volume'].tail(10)

                durum = ""
                if guncel_hacim == son_10_hacim.max(): durum = "🔥 YÜKSEK HACİM"
                elif guncel_hacim == son_10_hacim.min(): durum = "💤 DÜŞÜK HACİM"
                
                if durum != "":
                    bulunan += 1
                    apds = [mpf.make_addplot(hist['WMA9'].tail(40), color='cyan'),
                            mpf.make_addplot(hist['WMA15'].tail(40), color='orange')]
                    buf = io.BytesIO()
                    mpf.plot(hist.tail(40), type='candle', style='charles', volume=True, addplot=apds, savefig=dict(fname=buf, format='png'))
                    buf.seek(0)
                    msg = f"📊 *{hisse}* - {durum}\n🔵 WMA9 | 🟠 WMA15\n💰 Fiyat: {hist['Close'].iloc[-1]:.2f}"
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                                  files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
            except:
                continue

        t_mesaj(f"✅ Tarama bitti. {bulunan} hisse paylaşıldı.")

    except Exception as e:
        t_mesaj(f"❌ Kritik Hata: {str(e)}")

if __name__ == "__main__":
    analiz_et()
