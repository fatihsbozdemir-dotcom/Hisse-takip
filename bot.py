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

def bollinger_hesapla(df, periyot=20):
    sma = df['Close'].rolling(window=periyot).mean()
    std = df['Close'].rolling(window=periyot).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    bandwidth = ((upper - lower) / sma) * 100
    return upper.iloc[-1], lower.iloc[-1], bandwidth.iloc[-1]

def analiz_et():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            t_name = f"{hisse}.IS"
            hist = yf.Ticker(t_name).history(period="6mo", interval="1d") # Bollinger için günlük daha iyi
            if hist.empty: continue
            
            # --- BOLLINGER VE YATAY ANALİZ ---
            upper, lower, bandwidth = bollinger_hesapla(hist)
            guncel_fiyat = hist['Close'].iloc[-1]
            
            # Bollinger Sıkışma Kriteri: Bandwidth %5 altındaysa ciddi sıkışma vardır
            is_yatay_bollinger = bandwidth < 5.0 
            
            # Arz Bölgesi Kontrolü (Zirveye %2 yakınlık)
            arz_zirve = hist['High'].max()
            mesafe_yuzde = ((arz_zirve - guncel_fiyat) / arz_zirve) * 100
            arz_bolgesinde_mi = 0.0 <= mesafe_yuzde <= 2.0 
            
            if is_yatay_bollinger or arz_bolgesinde_mi:
                # Grafik oluştur
                buf = io.BytesIO()
                # Bollinger bantlarını grafiğe ekle
                apd = [mpf.make_addplot(hist['Close'].rolling(20).mean(), color='blue'),
                       mpf.make_addplot(hist['Close'].rolling(20).mean() + (hist['Close'].rolling(20).std()*2), color='gray'),
                       mpf.make_addplot(hist['Close'].rolling(20).mean() - (hist['Close'].rolling(20).std()*2), color='gray')]
                
                mpf.plot(hist.tail(40), type='candle', addplot=apd, savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                msg = f"📢 *Analiz*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {guncel_fiyat:.2f}\n📏 *Bollinger Genişliği:* %{bandwidth:.2f}"
                if is_yatay_bollinger: msg += "\n🟨 *Durum:* SIKIŞMA"
                if arz_bolgesinde_mi: msg += "\n🟥 *Durum:* ARZ BÖLGESİ"
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz_et()
