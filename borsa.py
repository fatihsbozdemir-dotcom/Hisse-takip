import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
from datetime import datetime

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('candle.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama}
    requests.post(url, files=files, data=data)

def mum_grafigi_olustur(hisse, df):
    # TradingView Tarzı: Yeşil (Up) ve Kırmızı (Down) mumlar
    # michele stili veya charles stili mum grafiği için çok uygundur
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True, edgecolor='#444444')
    
    buf = io.BytesIO()
    # Mum grafiğini çiz (type='candle')
    mpf.plot(df, type='candle', style=s, 
             title=f"\n{hisse} - Mum Grafiği (Saatlik)",
             ylabel='Fiyat (TL)', 
             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
    buf.seek(0)
    return buf

def alarm_ve_grafik_sistemi():
    try:
        # Google Sheets'ten verileri al
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        alarm_listesi = dict(zip(df_sheet['Hisse'], df_sheet['Hedef_Fiyat'].astype(float)))
        
        for hisse, hedef in alarm_listesi.items():
            # Mum grafiği için tam veri çekiyoruz
            ticker = yf.Ticker(hisse)
            hist = ticker.history(period="5d", interval="60m")
            
            if hist.empty: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            
            # Profesyonel Mum Grafiği Oluştur
            foto = mum_grafigi_olustur(hisse, hist)
            
            # Durum mesajını hazırla
            durum = "✅ HEDEF GEÇİLDİ! 🎯" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor"
            mesaj = f"📊 {hisse}\n💰 Güncel: {guncel_fiyat:.2f} TL\n🎯 Hedef: {hedef:.2f} TL\n📝 Durum: {durum}"
            
            # Gönder
            fotograf_gonder(foto, mesaj)
            
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": f"⚠️ Hata: {str(e)}"})

if __name__ == "__main__":
    alarm_ve_grafik_sistemi()
