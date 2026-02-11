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

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama}
    requests.post(url, files=files, data=data)

def grafik_ve_rsi_olustur(hisse, df):
    # RSI Hesapla
    df['RSI'] = rsi_hesapla(df['Close'])
    
    # Stil Ayarları
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
    
    # RSI Panelini Hazırla
    add_plot = [
        mpf.make_addplot(df['RSI'], panel=1, color='purple', ylabel='RSI', 
                         secondary_y=False, ylim=(0, 100))
    ]
    
    buf = io.BytesIO()
    # Grafik Çiz (Üstte Mumlar, Altta RSI)
    mpf.plot(df, type='candle', style=s, addplot=add_plot,
             title=f"\n{hisse} - Mum Grafik & RSI",
             ylabel='Fiyat (TL)',
             panel_ratios=(2, 1), # Mumlar 2 birim, RSI 1 birim yer kaplasın
             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
    buf.seek(0)
    return buf, df['RSI'].iloc[-1]

def alarm_ve_grafik_sistemi():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        alarm_listesi = dict(zip(df_sheet['Hisse'], df_sheet['Hedef_Fiyat'].astype(float)))
        
        for hisse, hedef in alarm_listesi.items():
            ticker = yf.Ticker(hisse)
            hist = ticker.history(period="1mo", interval="4h") # 4 Saatlik & 1 Aylık Veri
            
            if hist.empty: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            
            # Grafik ve RSI Değerini Al
            foto, son_rsi = grafik_ve_rsi_olustur(hisse, hist)
            
            # RSI Durum Mesajı
            rsi_notu = "🔵 Normal"
            if son_rsi >= 70: rsi_notu = "🔴 Aşırı Alım (Pahalı)"
            elif son_rsi <= 30: rsi_notu = "🟢 Aşırı Satım (Ucuz)"
            
            durum = "✅ HEDEF GEÇİLDİ! 🎯" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor"
            
            mesaj = (f"📊 {hisse}\n"
                     f"💰 Güncel: {guncel_fiyat:.2f} TL\n"
                     f"🎯 Hedef: {hedef:.2f} TL\n"
                     f"📈 RSI: {son_rsi:.2f} ({rsi_notu})\n"
                     f"📝 Durum: {durum}")
            
            fotograf_gonder(foto, mesaj)
            
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": f"⚠️ Hata: {str(e)}"})

if __name__ == "__main__":
    alarm_ve_grafik_sistemi()
