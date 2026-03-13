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
            # 6 aylık veri, günlük periyot
            df = yf.Ticker(t_name).history(period="6mo", interval="1d")
            if len(df) < 20: continue

            # --- SAF FİYAT ANALİZİ ---
            guncel_fiyat = df['Close'].iloc[-1]
            arz_zirve = df['High'].max()
            
            # 1. Arz Bölgesi (Zirveye %2 yakınlık)
            mesafe = ((arz_zirve - guncel_fiyat) / arz_zirve) * 100
            in_arz = 0 <= mesafe <= 2.0
            
            # 2. Yatay Kanal (Son 20 günlük en yüksek - en düşük farkı)
            son_20 = df.tail(20)
            kanal_genisligi = ((son_20['High'].max() - son_20['Low'].min()) / son_20['Low'].min()) * 100
            is_yatay = 2.0 <= kanal_genisligi <= 8.0 # %8'e kadar olan sıkışmaları al

            # --- SADECE KRİTERLERE UYUYORSA GÖNDER ---
            if in_arz or is_yatay:
                buf = io.BytesIO()
                
                # Grafik: İndikatörsüz, sadece mumlar
                mpf.plot(df.tail(40), type='candle', volume=True, 
                         title=f"\n{hisse} - Arz/Yatay Analizi",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                msg = f"📢 *Teknik Analiz*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {guncel_fiyat:.2f} TL"
                if in_arz: msg += f"\n🟥 *Arz Bölgesi:* Zirveye %{mesafe:.2f} yakın"
                if is_yatay: msg += f"\n🟨 *Yatay Kanal:* Genişlik %{kanal_genisligi:.2f}"
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
        except: continue

if __name__ == "__main__":
    analiz_et()
