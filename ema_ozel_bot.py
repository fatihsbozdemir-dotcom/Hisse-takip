import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import os

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def mesaj_gonder(metin):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': metin, 'parse_mode': 'Markdown'})

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def analiz_yap():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisseler = df_sheet['Hisse'].dropna().tolist()
        
        found_count = 0
        mesaj_gonder(f"🚀 Tarama başladı... {len(hisseler)} hisse kontrol ediliyor.")

        for hisse in hisseler:
            try:
                # 4 Saatlik veriyi çek
                df = yf.download(hisse, period="3mo", interval="4h", progress=False)
                if df.empty or len(df) < 90: continue

                # EMA Hesaplama (Veriyi temizleyerek)
                df['EMA55'] = df['Close'].ewm(span=55, adjust=False).mean()
                df['EMA89'] = df['Close'].ewm(span=89, adjust=False).mean()
                
                # Değerleri güvenli bir şekilde çek (float zorlaması ile)
                son_fiyat = float(df['Close'].iloc[-1])
                e55 = float(df['EMA55'].iloc[-1])
                e89 = float(df['EMA89'].iloc[-1])
                
                # Limit kontrolü (%1.5 mesafe)
                limit = 0.015 
                yakin_55 = abs(son_fiyat - e55) / e55 <= limit
                yakin_89 = abs(son_fiyat - e89) / e89 <= limit

                if yakin_55 or yakin_89:
                    found_count += 1
                    apds = [
                        mpf.make_addplot(df['EMA55'].tail(60), color='blue', width=1.5),
                        mpf.make_addplot(df['EMA89'].tail(60), color='red', width=1.5)
                    ]
                    
                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    
                    mpf.plot(df.tail(60), type='candle', style=s, addplot=apds,
                             title=f"\n{hisse} - 4H EMA Stratejisi",
                             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                    buf.seek(0)

                    bolge = "🔵 EMA 55" if yakin_55 else "🔴 EMA 89"
                    mesaj = (f"🕵️‍♂️ *SİNYAL: {hisse}*\n💰 Fiyat: {son_fiyat:.2f}\n📍 Bölge: {bolge}\n🔹 EMA55: {e55:.2f}\n🔸 EMA89: {e89:.2f}")
                    fotograf_gonder(buf, mesaj)

            except Exception as e_inner:
                print(f"{hisse} taranırken hata: {e_inner}")
                continue # Bir hisse hatalıysa diğerine geç

        mesaj_gonder(f"✅ Tarama tamamlandı. {found_count} adet uygun hisse bulundu.")

    except Exception as e:
        mesaj_gonder(f"❌ SİSTEM HATASI: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
