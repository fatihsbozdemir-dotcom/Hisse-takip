import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import mplfinance as mpf
import io
import os

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
# Mesajların doğrudan sana gelmesi için kullanıcı ID'n:
CHAT_ID = "8599240314" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {
        'chat_id': CHAT_ID, 
        'caption': aciklama, 
        'parse_mode': 'Markdown'
    }
    # Özel mesajda TOPIC_ID kullanılmaz, o yüzden kaldırıldı.
    requests.post(url, files=files, data=data)

def analiz_yap():
    try:
        # Google Sheets'ten listeyi oku
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisseler = df_sheet['Hisse'].dropna().tolist()
        
        print(f"{len(hisseler)} hisse kontrol ediliyor...")

        for hisse in hisseler:
            # 4 Saatlik veriyi çek
            df = yf.download(hisse, period="2mo", interval="4h", progress=False)
            if df.empty or len(df) < 90: continue

            # EMA 55 ve 89 Hesaplama
            df['EMA55'] = ta.ema(df['Close'], length=55)
            df['EMA89'] = ta.ema(df['Close'], length=89)
            
            son_fiyat = float(df['Close'].iloc[-1])
            e55 = float(df['EMA55'].iloc[-1])
            e89 = float(df['EMA89'].iloc[-1])
            
            # Strateji: Fiyat EMA 55 veya 89'a %1.5 yakın mı?
            limit = 0.015
            yakin_55 = abs(son_fiyat - e55) / e55 <= limit
            yakin_89 = abs(son_fiyat - e89) / e89 <= limit

            if yakin_55 or yakin_89:
                # Grafik Çizimi
                apds = [
                    mpf.make_addplot(df['EMA55'].tail(60), color='blue', width=1.5),
                    mpf.make_addplot(df['EMA89'].tail(60), color='red', width=1.5)
                ]
                
                buf = io.BytesIO()
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                mpf.plot(df.tail(60), type='candle', style=s, addplot=apds,
                         title=f"\n{hisse} - 4H EMA Stratejisi",
                         ylabel='Fiyat (TL)',
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)

                # Mesaj
                bolge = "🔵 EMA 55" if yakin_55 else "🔴 EMA 89"
                mesaj = (
                    f"🕵️‍♂️ *ÖZEL SİNYAL: {hisse}*\n\n"
                    f"💰 *Fiyat:* {son_fiyat:.2f} TL\n"
                    f"📍 *Bölge:* {bolge} Yakınında (4H)\n"
                    f"──────────────────\n"
                    f"🔹 EMA 55: {e55:.2f}\n"
                    f"🔸 EMA 89: {e89:.2f}\n"
                )
                
                fotograf_gonder(buf, mesaj)
                print(f"✅ {hisse} sana özel olarak gönderildi.")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz_yap()
