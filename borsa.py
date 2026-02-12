import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "import yfinance as ticker_data
import pandas as pd
import requests
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"  # Yeni grup ID'si (ELİ BÖGRÜNDE)

# Takip edilecek ana hisse listesi
HISSES = [
    "THYAO.IS", "EREGL.IS", "ASELS.IS", "SISE.IS", "KCHOL.IS", 
    "SASA.IS", "BIMAS.IS", "TUPRS.IS", "AKBNK.IS", "GARAN.IS"
]

def send_telegram_msg(message):
    """Telegram grubuna mesaj gönderir"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Mesaj hatası: {e}")

def check_squeeze(df):
    """Bollinger Bantları ve Keltner Kanalları ile yatay sıkışma (Squeeze) kontrolü"""
    # 20 periyotlu hareketli ortalama
    ma20 = df['Close'].rolling(window=20).mean()
    std_dev = df['Close'].rolling(window=20).std()
    
    # Bollinger Bantları
    upper_bb = ma20 + (2 * std_dev)
"
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
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    return requests.post(url, files=files, data=data)

def grafik_analiz_olustur(hisse, df):
    # RSI Hesapla
    df['RSI'] = rsi_hesapla(df['Close'])
    
    # Stil Ayarları (TradingView Tarzı)
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
    
    # RSI Çizgisini Alt Panele Ekle
    add_plot = [
        mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI', ylim=(0, 100))
    ]
    
    buf = io.BytesIO()
    # Grafik Çizimi: Mumlar, Hacim (Volume), 20 ve 50 günlük Hareketli Ortalamalar (mav)
    mpf.plot(df, type='candle', style=s, addplot=add_plot,
             volume=True, # Hacim ekle
             mav=(20, 50), # 20 ve 50 periyotluk hareketli ortalamalar
             title=f"\n{hisse} - Mum, Hacim, MA & RSI",
             ylabel='Fiyat (TL)',
             panel_ratios=(3, 1, 1), # Panellerin boyut oranları (Grafik, Hacim, RSI)
             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
    buf.seek(0)
    
    son_rsi = df['RSI'].iloc[-1]
    return buf, son_rsi

def alarm_ve_grafik_sistemi():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        alarm_listesi = dict(zip(df_sheet['Hisse'], df_sheet['Hedef_Fiyat'].astype(float)))
        
        for hisse, hedef in alarm_listesi.items():
            ticker = yf.Ticker(hisse)
            # Daha sağlıklı ortalamalar için veri setini biraz genişlettik
            hist = ticker.history(period="3mo", interval="1d") 
            
            if hist.empty or len(hist) < 50:
                continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            foto, son_rsi = grafik_analiz_olustur(hisse, hist)
            
            # RSI Yorumlama
            rsi_notu = "🔵 Normal"
            if son_rsi >= 70: rsi_notu = "🔴 *Asiri Alim (Pahali)*"
            elif son_rsi <= 30: rsi_notu = "🟢 *Asiri Satim (Ucuz)*"
            
            durum = "✅ HEDEF GECILDI! 🎯" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor"
            
            mesaj = (f"📊 *{hisse}*\n"
                     f"💰 Güncel: {guncel_fiyat:.2f} TL\n"
                     f"🎯 Hedef: {hedef:.2f} TL\n"
                     f"📈 RSI: {son_rsi:.2f} ({rsi_notu})\n"
                     f"📉 MA20/50 ve Hacim grafikte eklidir.\n"
                     f"📝 Durum: {durum}")
            
            fotograf_gonder(foto, mesaj)
            
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    alarm_ve_grafik_sistemi()
