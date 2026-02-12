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
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': '📊 *10 Günlük Hacim Analizi Başladı...* (WMA 9/15 Aktif)'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            t_name = f"{hisse}.IS" if not hisse.endswith(".IS") else hisse
            hist = yf.Ticker(t_name).history(period="3mo", interval="1d")
            
            if len(hist) < 20: continue

            # --- HESAPLAMALAR ---
            # Hacim Taraması (Son 10 İş Günü)
            son_10_gun_hacim = hist['Volume'].tail(10)
            guncel_hacim = hist['Volume'].iloc[-1]
            en_yuksek_hacim = son_10_gun_hacim.max()
            en_dusuk_hacim = son_10_gun_hacim.min()

            # WMA Hesaplama (pandas_ta kütüphanesi ile)
            hist['WMA9'] = ta.wma(hist['Close'], length=9)
            hist['WMA15'] = ta.wma(hist['Close'].fillna(method='ffill'), length=15)

            durum = ""
            if guncel_hacim == en_yuksek_hacim:
                durum = "🔥 YÜKSEK HACİM (10 Günün Zirvesi)"
            elif guncel_hacim == en_dusuk_hacim:
                durum = "💤 DÜŞÜK HACİM (10 Günün Dibi)"
            
            # Sadece en düşük veya en yüksekse bildirim at
            if durum != "":
                # Grafik Çizimi
                # WMA'ları grafiğe eklemek için ek çizim (addplot) oluşturuyoruz
                apds = [
                    mpf.make_addplot(hist['WMA9'].tail(40), color='blue', width=1.5),
                    mpf.make_addplot(hist['WMA15'].tail(40), color='orange', width=1.5)
                ]

                buf = io.BytesIO()
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                # Grafiği oluştur
                mpf.plot(hist.tail(40), type='candle', style=s, volume=True, addplot=apds,
                         title=f"\n{hisse} - {durum}",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)

                msg = (f"📊 *HACİM ANALİZİ*\n\n"
                       f"🎫 *Hisse:* {hisse}\n"
                       f"📢 *Durum:* {durum}\n"
                       f"💰 *Fiyat:* {hist['Close'].iloc[-1]:.2f}\n"
                       f"🔵 *Mavi Hat:* WMA 9\n"
                       f"🟠 *Turuncu Hat:* WMA 15\n\n"
                       f"📝 _Not: Son 10 iş günü içindeki hacim ekstrem noktalarıdır._")
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata: {str(e)}'})

if __name__ == "__main__":
    analiz_et()
