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

def analiz_et():
    try:
        # BOT ÇALIŞTI MESAJI
        simdi = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'🤖 *{simdi.strftime("%H:%M")}* Taraması Başlatıldı...'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            hedef = row.get('Hedef_Fiyat', 0)
            try: hedef = float(hedef)
            except: hedef = 0
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            # Haftalık Veri
            hist = yf.Ticker(t_name).history(period="1y", interval="1wk")
            
            if hist.empty: continue
            
            # Sıkışma Hesabı (5 Haftalık)
            ma5 = hist['Close'].rolling(window=5).mean()
            std5 = hist['Close'].rolling(window=5).std()
            genislik = ( (ma5 + 2*std5) - (ma5 - 2*std5) ) / ma5
            is_squeeze = genislik.iloc[-1] <= genislik.rolling(window=100).quantile(0.30).iloc[-1]

            if hedef > 0 or is_squeeze:
                # --- GRAFİK AYARLARINI GERİ GETİRİYORUZ ---
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                buf = io.BytesIO()
                # volume=True: Hacmi geri getirir, type='candle': Mum grafik yapar
                mpf.plot(hist.tail(40), type='candle', style=s, volume=True, 
                         title=f"\n{hisse} (Haftalik)", ylabel='Fiyat (TL)',
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                tip = "🎯 HEDEF" if hedef > 0 else "🟨 SIKIŞMA"
                msg = f"📢 *{tip}*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {hist['Close'].iloc[-1]:.2f}"
                if hedef > 0: msg += f"\n🎯 *Hedef:* {hedef:.2f}"
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata: {str(e)}'})

if __name__ == "__main__":
    analiz_et()
