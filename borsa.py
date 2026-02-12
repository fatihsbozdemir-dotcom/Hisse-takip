import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "1003838602845"
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
    requests.post(url, files=files, data=data)

def grafik_ciz(hisse, df, rsi_deger, mesaj_tipi):
    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
    
    # RSI Paneli
    add_plot = [mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI', ylim=(0, 100))]
    
    buf = io.BytesIO()
    # Grafik: Mumlar, Hacim, MA20, MA50
    mpf.plot(df, type='candle', style=s, addplot=add_plot, volume=True, mav=(20, 50),
             title=f"\n{hisse} - {mesaj_tipi}",
             ylabel='Fiyat (TL)', panel_ratios=(3,1,1),
             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
    buf.seek(0)
    return buf

def analiz_et():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        
        for index, row in df_sheet.iterrows():
            hisse = row['Hisse']
            hedef = float(row['Hedef_Fiyat'])
            
            ticker = yf.Ticker(hisse)
            # Hem ortalamalar hem de sinyal için 1 yıllık veri alıyoruz
            hist = ticker.history(period="1y", interval="1d")
            
            if hist.empty or len(hist) < 50: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            hist['RSI'] = rsi_hesapla(hist['Close'])
            son_rsi = hist['RSI'].iloc[-1]
            
            # --- 1. SİNYAL AVCI KONTROLLERİ ---
            sinyaller = []
            # Golden Cross (50 günlük 200 günlüğü keserse - veri 1 yıllık olduğu için MA200 bakabiliriz)
            ma50 = hist['Close'].rolling(window=50).mean()
            ma200 = hist['Close'].rolling(window=200).mean()
            if ma50.iloc[-1] > ma200.iloc[-1] and ma50.iloc[-2] <= ma200.iloc[-2]:
                sinyaller.append("🌟 *ALTIN KESİŞME!*")
            
            # Hacim Patlaması
            if hist['Volume'].iloc[-1] > (hist['Volume'].rolling(window=20).mean().iloc[-1] * 1.5):
                sinyaller.append("🚀 *HACİM PATLAMASI!*")
            
            # RSI Ucuzluk
            if son_rsi < 35:
                sinyaller.append("💎 *AŞIRI UCUZ (RSI 35 Altı)*")

            # --- 2. HEDEF FİYAT ALARMI ---
            hedef_durum = "✅ *HEDEF GEÇİLDİ!* 🎯" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor"
            
            # Mesaj İçeriği Hazırlama
            sinyal_notu = "\n".join(sinyaller) if sinyaller else "🔍 Özel bir sinyal yok."
            rsi_durum = "🔴 Pahalı" if son_rsi > 70 else ("🟢 Ucuz" if son_rsi < 30 else "🔵 Normal")

            mesaj = (f"📊 *{hisse} ANALİZ RAPORU*\n\n"
                     f"💰 *Fiyat:* {guncel_fiyat:.2f} TL\n"
                     f"🎯 *Hedefin:* {hedef:.2f} TL\n"
                     f"📝 *Alarm:* {hedef_durum}\n\n"
                     f"📈 *RSI:* {son_rsi:.2f} ({rsi_durum})\n"
                     f"📡 *Teknik Sinyaller:*\n{sinyal_notu}")
            
            # Grafik türüne göre başlık belirle ve gönder
            tip = "Sinyal Yakalandı!" if sinyaller else "Düzenli Takip"
            foto = grafik_ciz(hisse, hist.suffix(30), son_rsi, tip) # Son 30 günü göster ki grafik net olsun
            fotograf_gonder(foto, mesaj)
                
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    analiz_et()
