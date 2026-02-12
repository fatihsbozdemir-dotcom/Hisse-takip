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

def analiz_et_ve_bildir():
    try:
        # Başlangıç mesajı
        simdi = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'🤖 *{simdi.strftime("%H:%M")}* Taraması Başlatıldı...'})

        # Veriyi çek
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns] # Boşlukları temizle

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            hedef = row.get('Hedef_Fiyat', 0)
            try: hedef = float(hedef)
            except: hedef = 0
            
            ticker = yf.Ticker(f"{hisse}.IS" if not hisse.endswith(".IS") else hisse)
            hist = ticker.history(period="1y", interval="1wk")
            
            if hist.empty: continue
            
            # 5 Haftalık Sıkışma Kontrolü
            ma5 = hist['Close'].rolling(window=5).mean()
            std5 = hist['Close'].rolling(window=5).std()
            genislik = ( (ma5 + 2*std5) - (ma5 - 2*std5) ) / ma5
            is_squeeze = genislik.iloc[-1] <= genislik.rolling(window=100).quantile(0.30).iloc[-1]

            bildir = False
            tip = ""
            if hedef > 0:
                bildir = True
                tip = "🎯 HEDEF TAKİBİ"
            elif is_squeeze:
                bildir = True
                tip = "🟨 5 HAFTALIK SIKIŞMA"

            if bildir:
                buf = io.BytesIO()
                mpf.plot(hist.tail(30), type='candle', style='charles', savefig=dict(fname=buf, format='png'))
                buf.seek(0)
                msg = f"📢 *{tip}*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {hist['Close'].iloc[-1]:.2f}"
                if hedef > 0: msg += f"\n🎯 *Hedef:* {hedef:.2f}"
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata oluştu: {str(e)}'})

if __name__ == "__main__":
    analiz_et_ve_bildir()
