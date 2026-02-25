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
        mesaj_gonder(f"🔍 *4H EMA 89 Taraması Başladı...* ({len(hisseler)} hisse)")

        for hisse in hisseler:
            try:
                # Veriyi çek (Hata payını azaltmak için periyodu uzattık)
                df = yf.download(hisse, period="6mo", interval="4h", progress=False)
                if df.empty or len(df) < 90: continue

                # EMA Hesaplamaları
                df['EMA55'] = df['Close'].ewm(span=55, adjust=False).mean()
                df['EMA89'] = df['Close'].ewm(span=89, adjust=False).mean()
                
                # Değerleri seriden sayıya (float) güvenli dönüştürme
                son_fiyat = float(df['Close'].iloc[-1])
                e89 = float(df['EMA89'].iloc[-1])
                
                # KRİTER: Fiyat EMA 89'a %1.5 yakın mı? 
                # (Eğer yine bulamazsa bu 0.015 değerini 0.03 yaparak alanı genişletebilirsin)
                limit = 0.015 
                mesafe = abs(son_fiyat - e89) / e89

                if mesafe <= limit:
                    found_count += 1
                    
                    # GRAFİK AYARI: EMA 89'u tam istediğin gibi MOR yapıyoruz
                    apds = [
                        mpf.make_addplot(df['EMA89'].tail(80), color='purple', width=2.0)
                    ]
                    
                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    
                    mpf.plot(df.tail(80), type='candle', style=s, addplot=apds,
                             title=f"\n{hisse} - EMA 89 (Mor Çizgi) Desteği",
                             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                    buf.seek(0)

                    mesaj = (f"🎯 *EMA 89 DESTEK SİNYALİ*\n\n"
                             f"🏢 *Hisse:* {hisse}\n"
                             f"💰 *Fiyat:* {son_fiyat:.2f}\n"
                             f"🟣 *EMA 89:* {e89:.2f}\n"
                             f"📉 *Mesafe:* %{mesafe*100:.2f}")
                    
                    fotograf_gonder(buf, mesaj)

            except Exception:
                continue 

        mesaj_gonder(f"✅ Tarama bitti. {found_count} uygun hisse bulundu.")

    except Exception as e:
        mesaj_gonder(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
