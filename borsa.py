import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import datetime

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def yatay_kontrol_haftalik(df):
    """5 haftalık periyotta daralma kontrolü"""
    if len(df) < 20: return False
    # 5 haftalık (1 ay) pencere
    ma5 = df['Close'].rolling(window=5).mean()
    std5 = df['Close'].rolling(window=5).std()
    ust_bant = ma5 + (2 * std5)
    alt_bant = ma5 - (2 * std5)
    
    bant_genisligi = (ust_bant - alt_bant) / ma5
    su_anki_genislik = bant_genisligi.iloc[-1]
    
    # Son 100 haftanın en dar %30'u
    esik_deger = bant_genisligi.rolling(window=100).quantile(0.30).iloc[-1]
    return su_anki_genislik <= esik_deger

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('analiz.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def analiz_et_ve_bildir():
    try:
        # Türkiye saati ayarı (UTC+3)
        simdi = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        saat_dk = simdi.strftime("%H:%M")

        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'🤖 *{saat_dk} Taraması Başladı...*\n(5 Haftalık Sıkışma & Hedef Kontrolü)'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        
        bulunan_sayi = 0

        for index, row in df_sheet.iterrows():
            hisse = str(row['Hisse']).strip()
            try:
                hedef = float(row['Hedef_Fiyat']) if pd.notnull(row['Hedef_Fiyat']) else 0
            except:
                hedef = 0
            
            ticker_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(ticker_name)
            
            # HAFTALIK VERİ
            hist = ticker.history(period="2y", interval="1wk")
            
            if hist.empty or len(hist) < 10: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            is_squeeze = yatay_kontrol_haftalik(hist)
            
            bildir = False
            mesaj_tipi = ""
            durum_notu = ""

            if hedef > 0:
                bildir = True
                mesaj_tipi = "🎯 HEDEF TAKİBİ"
                durum_notu = "✅ Hedef Geçildi!" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor."
            elif is_squeeze:
                bildir = True
                mesaj_tipi = "🟨 5 HAFTALIK SIKIŞMA"
                durum_notu = "⚠️ Son 5 haftadır yatay seyirde, patlama yapabilir."

            if bildir:
                bulunan_sayi += 1
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                buf = io.BytesIO()
                mpf.plot(hist.tail(30), type='candle', style=s, title=f"\n{hisse} (Haftalik)",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)

                mesaj = (f"📢 *{mesaj_tipi}*\n\n"
                         f"📊 *Hisse:* {hisse}\n"
                         f"💰 *Fiyat:* {guncel_fiyat:.2f} TL\n")
                if hedef > 0: mesaj += f"🎯 *Hedef:* {hedef:.2f} TL\n"
                mesaj += f"📝 *Durum:* {durum_notu}"
                
                fotograf_gonder(buf, mesaj)

        if bulunan_sayi == 0:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={'chat_id': CHAT_ID, 'text': f'✅ {saat_dk} taraması bitti. Kriterlere uyan hisse bulunamadı.'})
                
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata: {str(e)}'})

if __name__ == "__main__":
    analiz_et_ve_bildir()
