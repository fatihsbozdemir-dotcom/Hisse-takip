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

def yatay_kontrol_haftalik(df):
    """Haftalık periyotta Bollinger Bantları ile sıkışma kontrolü"""
    # Haftalık kapanışlar üzerinden 20 haftalık Bollinger hesaplama
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    ust_bant = ma20 + (2 * std20)
    alt_bant = ma20 - (2 * std20)
    
    bant_genisligi = (ust_bant - alt_bant) / ma20
    su_anki_genislik = bant_genisligi.iloc[-1]
    
    # Son 100 haftanın en dar %30'u (Esnek ve güçlü bir kriter)
    esik_deger = bant_genisligi.rolling(window=100).quantile(0.30).iloc[-1]
    return su_anki_genislik <= esik_deger

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('haftalik_analiz.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def analiz_et_ve_bildir():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': '🔍 *Haftalık Tarama Başladı:* Büyük sıkışmalar aranıyor...'})

        bulunan_sayi = 0

        for index, row in df_sheet.iterrows():
            hisse = row['Hisse']
            try:
                hedef = float(row['Hedef_Fiyat']) if pd.notnull(row['Hedef_Fiyat']) else 0
            except:
                hedef = 0
            
            ticker_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(ticker_name)
            
            # HAFTALIK VERİ ÇEKİMİ (period=2y, interval=1wk)
            hist = ticker.history(period="2y", interval="1wk")
            
            if hist.empty or len(hist) < 30: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            is_squeeze = yatay_kontrol_haftalik(hist)
            
            bildir = False
            mesaj_tipi = ""
            durum_notu = ""

            # KRİTER 1: Fiyat yazılıysa bildir
            if hedef > 0:
                bildir = True
                mesaj_tipi = "🎯 HEDEF TAKİBİ (Haftalık)"
                durum_notu = "✅ Hedef Geçildi!" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor"
            
            # KRİTER 2: Hedef yoksa HAFTALIK SIKIŞMA kontrolü
            elif is_squeeze:
                bildir = True
                mesaj_tipi = "🟨 HAFTALIK SIKIŞMA"
                durum_notu = "🔥 *BÜYÜK PATLAMA YAKIN!* 20 haftalık bantlar aşırı daraldı."

            if bildir:
                bulunan_sayi += 1
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                buf = io.BytesIO()
                # Haftalık mumu daha net görmek için son 40 haftayı çiziyoruz
                mpf.plot(hist.tail(40), type='candle', style=s, title=f"\n{hisse} (Haftalik)",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)

                mesaj = (f"📢 *{mesaj_tipi}*\n\n"
                         f"📊 *Hisse:* {hisse}\n"
                         f"💰 *Fiyat:* {guncel_fiyat:.2f} TL\n")
                if hedef > 0: mesaj += f"🎯 *Hedef:* {hedef:.2f} TL\n"
                mesaj += f"📝 *Durum:* {durum_notu}\n\n"
                mesaj += "📅 _Grafikte her bir mum 1 haftayı temsil eder._"
                
                fotograf_gonder(buf, mesaj)

        if bulunan_sayi == 0:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                          json={'chat_id': CHAT_ID, 'text': '✅ Haftalık tarama bitti. Kritik bir sıkışma bulunamadı.'})
                
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz_et_ve_bildir()
