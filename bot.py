import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def analiz_et():
    df_sheet = pd.read_csv(SHEET_URL)
    hisseler = df_sheet['Hisse'].dropna().unique()

    for hisse in hisseler:
        try:
            t_name = f"{hisse}.IS"
            df = yf.Ticker(t_name).history(period="6mo", interval="1d")
            if len(df) < 20: continue

            # --- HESAPLAMALAR ---
            # Bollinger (20, 2)
            sma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            upper = sma + (2 * std)
            lower = sma - (2 * std)
            
            # Sıkışma oranı (Bandwidth)
            bandwidth = ((upper - lower) / sma) * 100
            is_sikisma = bandwidth.iloc[-1] < 5.0 # %5 altı sıkışmadır
            
            # Arz Bölgesi (Zirveye %2 yakınlık)
            arz_zirve = df['High'].max()
            fiyat = df['Close'].iloc[-1]
            mesafe = ((arz_zirve - fiyat) / arz_zirve) * 100
            is_arz = 0 <= mesafe <= 2.0

            # --- FİLTRE VE BİLDİRİM ---
            if is_sikisma or is_arz:
                buf = io.BytesIO()
                
                # Grafik çizimi
                apds = [
                    mpf.make_addplot(upper, color='gray', linestyle='--'),
                    mpf.make_addplot(lower, color='gray', linestyle='--'),
                    mpf.make_addplot(sma, color='blue')
                ]
                
                mpf.plot(df.tail(60), type='candle', addplot=apds, volume=True, 
                         title=f"\n{hisse} - Bollinger/Arz Analizi",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                msg = f"📢 *Analiz Sonucu*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {fiyat:.2f} TL"
                if is_sikisma: msg += f"\n🟨 *Sıkışma:* %{bandwidth.iloc[-1]:.2f} (Daralma Var)"
                if is_arz: msg += f"\n🟥 *Arz Bölgesi:* Zirveye %{mesafe:.2f} uzaklıkta"
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
        except: continue

if __name__ == "__main__":
    analiz_et()
