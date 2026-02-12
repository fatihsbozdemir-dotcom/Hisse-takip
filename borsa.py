import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def yatay_kontrol(df):
    """Bollinger Bantları ile sıkışma kontrolü (Hassasiyet %30'a çıkarıldı)"""
    ma20 = df['Close'].rolling(window=10).mean()
    std20 = df['Close'].rolling(window=10).std()
    ust_bant = ma20 + (2 * std20)
    alt_bant = ma20 - (2 * std20)
    
    bant_genisligi = (ust_bant - alt_bant) / ma20
    su_anki_genislik = bant_genisligi.iloc[-1]
    
    # %30 hassasiyet ile daha kolay yakalar
    esik_deger = bant_genisligi.rolling(window=50).quantile(0.30).iloc[-1]
    return su_anki_genislik <= esik_deger

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('analiz.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def analiz_et_ve_bildir():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        
        # Botun başladığını gruba bildir (Hata ayıklama için)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': '🔍 *Borsa Takip:* Liste taranıyor...'})

        bulunan_hisse_sayisi = 0

        for index, row in df_sheet.iterrows():
            hisse = row['Hisse']
            # Excel'deki Hedef_Fiyat kontrolü
            try:
                raw_hedef = row['Hedef_Fiyat']
                hedef = float(raw_hedef) if pd.notnull(raw_hedef) and str(raw_hedef).strip() != "" else 0
            except:
                hedef = 0
            
            ticker_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(ticker_name)
            hist = ticker.history(period="6mo", interval="1d")
            
            if hist.empty or len(hist) < 30: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            is_squeeze = yatay_kontrol(hist)
            
            bildir = False
            mesaj_tipi = ""
            durum_notu = ""

            # KRİTER 1: Fiyat yazılıysa HER ZAMAN bildir
            if hedef > 0:
                bildir = True
                mesaj_tipi = "🎯 HEDEF TAKİBİ"
                oran = ((guncel_fiyat - hedef) / hedef) * 100
                if guncel_fiyat >= hedef:
                    durum_notu = f"✅ *Hedef Geçildi!* (Fark: %{oran:.2f})"
                else:
                    durum_notu = f"⏳ Hedef Bekleniyor (Kalan: %{abs(oran):.2f})"
            
            # KRİTER 2: Fiyat yazılı değilse SADECE yataydaysa bildir
            elif is_squeeze:
                bildir = True
                mesaj_tipi = "🟨 YATAY SIKIŞMA"
                durum_notu = "⚠️ Bollinger bantları aşırı daraldı, patlama yakın!"

            if bildir:
                bulunan_hisse_sayisi += 1
                # Grafik Hazırla
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                buf = io.BytesIO()
                mpf.plot(hist.tail(50), type='candle', style=s, title=f"\n{hisse}",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)

                # Mesaj
                mesaj = (f"📢 *{mesaj_tipi}*\n\n"
                         f"📊 *Hisse:* {hisse}\n"
                         f"💰 *Fiyat:* {guncel_fiyat:.2f} TL\n")
                
                if hedef > 0:
                    mesaj += f"🎯 *Hedef:* {hedef:.2f} TL\n"
                
                mesaj += f"📝 *Durum:* {durum_notu}"
                
                fotograf_gonder(buf, mesaj)

        if bulunan_hisse_sayisi == 0:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={'chat_id': CHAT_ID, 'text': '✅ Tarama bitti. Kriterlere uyan hisse bulunamadı.'})
                
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz_et_ve_bildir()
