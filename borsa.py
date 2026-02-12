import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

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

def yatay_kontrol(df):
    # Bollinger Bantları Hesapla (20 Periyot)
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    ust_bant = ma20 + (2 * std20)
    alt_bant = ma20 - (2 * std20)
    
    # Bant Genişliği (Bandwidth)
    bant_genisligi = (ust_bant - alt_bant) / ma20
    
    # Eğer son 5 günün bant genişliği son 100 günün en düşük seviyelerindeyse: YATAY
    su_anki_genislik = bant_genisligi.iloc[-1]
    tarihsel_min = bant_genisligi.rolling(window=100).min().iloc[-1]
    
    # Eşik değer: Mevcut genişlik, minimuma çok yakınsa (sıkışma var)
    is_squeeze = su_anki_genislik <= (tarihsel_min * 1.2)
    return is_squeeze, su_anki_genislik

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def analiz_et():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        
        for index, row in df_sheet.iterrows():
            hisse = row['Hisse']
            hedef = float(row['Hedef_Fiyat'])
            ticker = yf.Ticker(hisse)
            hist = ticker.history(period="1y", interval="1d")
            
            if hist.empty or len(hist) < 100: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            hist['RSI'] = rsi_hesapla(hist['Close'])
            son_rsi = hist['RSI'].iloc[-1]
            
            # --- YATAY SEYİR VE SİNYAL KONTROLLERİ ---
            sinyaller = []
            is_squeeze, genislik = yatay_kontrol(hist)
            
            if is_squeeze:
                sinyaller.append("🟨 *YATAY SEYİR (Sıkışma Var!)*")
            
            # Diğer sinyaller
            if hist['Volume'].iloc[-1] > (hist['Volume'].rolling(window=20).mean().iloc[-1] * 1.8):
                sinyaller.append("🚀 *HACİM PATLAMASI!*")
            if son_rsi < 35:
                sinyaller.append("💎 *AŞIRI UCUZ*")

            # Mesaj
            hedef_durum = "✅ *HEDEF GEÇİLDİ!*" if guncel_fiyat >= hedef else "⏳ Bekliyor"
            sinyal_notu = "\n".join(sinyaller) if sinyaller else "🔍 Normal seyir."

            mesaj = (f"📊 *{hisse} ANALİZ*\n\n"
                     f"💰 Fiyat: {guncel_fiyat:.2f} TL\n"
                     f"🎯 Hedef: {hedef:.2f} TL\n"
                     f"📈 RSI: {son_rsi:.2f}\n"
                     f"📡 *Durum:*\n{sinyal_notu}\n"
                     f"📝 {hedef_durum}")
            
            # Grafik Çizimi (Son 60 gün)
            mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
            s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
            buf = io.BytesIO()
            mpf.plot(hist.tail(60), type='candle', style=s, volume=True, 
                     title=f"\n{hisse}", ylabel='Fiyat (TL)',
                     savefig=dict(fname=buf, format='png', bbox_inches='tight'))
            buf.seek(0)
            fotograf_gonder(buf, mesaj)
                
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz_et()
