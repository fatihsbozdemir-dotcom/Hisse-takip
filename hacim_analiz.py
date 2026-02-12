import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import pandas_ta as ta

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def analiz_et():
    try:
        # Google Sheet'ten listeyi çek
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        bulunan = 0
        
        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            # Veriyi çek
            t_name = f"{hisse}.IS" if not hisse.endswith(".IS") else hisse
            hist = yf.Ticker(t_name).history(period="3mo", interval="1d")
            
            if len(hist) < 20: continue

            # Hacim Kontrolü (Son 10 İş Günü)
            son_10_hacim = hist['Volume'].tail(10)
            guncel_hacim = hist['Volume'].iloc[-1]
            
            # WMA 9 ve WMA 15 Hesaplama
            hist['WMA9'] = ta.wma(hist['Close'], length=9)
            hist['WMA15'] = ta.wma(hist['Close'], length=15)

            durum = ""
            if guncel_hacim == son_10_hacim.max():
                durum = "🔥 YÜKSEK HACİM (10 Günün Zirvesi)"
            elif guncel_hacim == son_10_hacim.min():
                durum = "💤 DÜŞÜK HACİM (10 Günün Dibi)"
            
            # Sadece ekstrem durumlarda grafik at
            if durum != "":
                bulunan += 1
                # Grafik Hazırlığı (WMA'lar ile)
                apds = [
                    mpf.make_addplot(hist['WMA9'].tail(40), color='cyan', width=1.2), # Mavi Hat
                    mpf.make_addplot(hist['WMA15'].tail(40), color='orange', width=1.2) # Turuncu Hat
                ]

                buf = io.BytesIO()
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                mpf.plot(hist.tail(40), type='candle', style=s, volume=True, addplot=apds,
                         title=f"\n{hisse} - {durum}", savefig=dict(fname=buf, format='png'))
                buf.seek(0)

                msg = (f"📊 *HACİM VE TREND ANALİZİ*\n\n"
                       f"🎫 *Hisse:* {hisse}\n"
                       f"📢 *Durum:* {durum}\n"
                       f"🔵 *Mavi Çizgi:* WMA 9\n"
                       f"🟠 *Turuncu Çizgi:* WMA 15\n"
                       f"💰 *Fiyat:* {hist['Close'].iloc[-1]:.2f}")
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

        # Özet Mesaj
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'✅ Tarama bitti. {bulunan} hisse için sinyal gönderildi.'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata oluştu: {str(e)}'})

if __name__ == "__main__":
    analiz_et()
