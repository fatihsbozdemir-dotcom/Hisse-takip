import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
import io
import requests

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def pivot_noktalari_bul(df, fiyat_adimi=0.5):
    # En yüksek ve en düşüklerin kümelendiği yerleri bul
    levels = []
    # Fiyatları yuvarlayıp en çok tekrar edenleri al
    highs = np.round(df['High'] / fiyat_adimi) * fiyat_adimi
    lows = np.round(df['Low'] / fiyat_adimi) * fiyat_adimi
    
    # En sık tekrar eden 3 tepe ve 3 dip seviyesi
    top_tepeler = highs.value_counts().nlargest(3).index.tolist()
    top_dipler = lows.value_counts().nlargest(3).index.tolist()
    
    return top_tepeler, top_dipler

def analiz_et():
    df_sheet = pd.read_csv(SHEET_URL)
    hisseler = df_sheet['Hisse'].dropna().unique()

    for hisse in hisseler:
        try:
            t_name = f"{hisse}.IS"
            df = yf.Ticker(t_name).history(period="1y", interval="1d") # 1 yıllık veri daha iyi sonuç verir
            if len(df) < 50: continue

            tepeler, dipler = pivot_noktalari_bul(df)
            guncel_fiyat = df['Close'].iloc[-1]

            # Eğer güncel fiyat herhangi bir tepe veya dibin %1 yakınındaysa sinyal üret
            yakinimda_mi = any(abs(guncel_fiyat - t) / t < 0.01 for t in tepeler + dipler)

            if yakinimda_mi:
                buf = io.BytesIO()
                
                # Çizgileri ekle
                al_levels = [mpf.make_addplot([t]*len(df), color='red', linestyle='-.') for t in tepeler] + \
                            [mpf.make_addplot([d]*len(df), color='green', linestyle='-.') for d in dipler]
                
                mpf.plot(df.tail(100), type='candle', addplot=al_levels, 
                         title=f"\n{hisse} - Dönüş Seviyeleri",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                msg = f"📢 *Dönüş Bölgesi Analizi*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {guncel_fiyat:.2f} TL\n🔴 *Tepe (Direnç):* {tepeler}\n🟢 *Dip (Destek):* {dipler}"
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
        except Exception as e:
            continue

if __name__ == "__main__":
    analiz_et()
