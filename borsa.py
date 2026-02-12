import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" # ELİ BÖGRÜNDE GRUBU
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def rsi_hesapla(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def yatay_kontrol(df):
    """Günlük periyotta Bollinger Bantları ile daralma (Squeeze) kontrolü"""
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    ust_bant = ma20 + (2 * std20)
    alt_bant = ma20 - (2 * std20)
    
    bant_genisligi = (ust_bant - alt_bant) / ma20
    su_anki_genislik = bant_genisligi.iloc[-1]
    
    # Eşik: Son 100 günün en dar %15'lik zamanındaysak sıkışma var demektir
    esik_deger = bant_genisligi.rolling(window=100).quantile(0.15).iloc[-1]
    return su_anki_genislik <= esik_deger

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('analiz.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def analiz_et_ve_gruba_at():
    try:
        # 1. Google Sheets'ten verileri çek
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        
        bildirilecek_hisseler = []

        # 2. İNCELEME (Sessizce tarama yapar)
        for index, row in df_sheet.iterrows():
            hisse = row['Hisse']
            # Hedef_Fiyat sütunu boşsa 0 al
            try:
                hedef = float(row['Hedef_Fiyat']) if pd.notnull(row['Hedef_Fiyat']) else 0
            except:
                hedef = 0
            
            ticker_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(ticker_name)
            hist = ticker.history(period="6mo", interval="1d") # GÜNLÜK PERİYOT
            
            if hist.empty or len(hist) < 30: continue

            guncel_fiyat = float(hist['Close'].iloc[-1])
            is_squeeze = yatay_kontrol(hist)
            
            # --- FİLTRE MANTIĞI ---
            kriter_uygun = False
            tip = ""
            not_mesaji = ""

            if hedef > 0:
                # Hedef fiyat yazılmışsa direkt listeye al
                kriter_uygun = True
                tip = "🎯 HEDEF TAKİBİ"
                not_mesaji = "✅ Hedefe ulaşıldı!" if guncel_fiyat >= hedef else "⏳ Hedef bekleniyor."
            elif is_squeeze:
                # Hedef yok ama yatayda sıkışma varsa listeye al
                kriter_uygun = True
                tip = "🟨 YATAY SIKIŞMA"
                not_mesaji = "⚠️ Bollinger bantları daraldı, patlama yakın olabilir."

            if kriter_uygun:
                bildirilecek_hisseler.append({
                    'hisse': hisse, 'fiyat': guncel_fiyat, 'hedef': hedef, 
                    'tip': tip, 'not': not_mesaji, 'data': hist
                })

        # 3. BİLDİRME (Sadece uygun olanları gruba atar)
        if not bildirilecek_hisseler:
            print("Grupta paylaşılacak kritik bir durum (hedef veya sıkışma) bulunamadı.")
            return

        for item in bildirilecek_hisseler:
            hist_data = item['data']
            
            # Grafik hazırlığı
            mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
            s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
            buf = io.BytesIO()
            mpf.plot(hist_data.tail(50), type='candle', style=s, volume=True,
                     title=f"\n{item['hisse']} - Gunluk Analiz",
                     savefig=dict(fname=buf, format='png', bbox_inches='tight'))
            buf.seek(0)

            # Telegram mesajı
            mesaj = (f"📢 *{item['tip']}*\n\n"
                     f"📊 *Hisse:* {item['hisse']}\n"
                     f"💰 *Güncel Fiyat:* {item['fiyat']:.2f} TL\n")
            
            if item['hedef'] > 0:
                mesaj += f"🎯 *Hedef Fiyat:* {item['hedef']:.2f} TL\n"
            
            mesaj += f"📝 *Durum:* {item['not']}\n\n"
            mesaj += "📅 _Son 50 günlük periyot grafiği yukarıdadır._"

            fotograf_gonder(buf, mesaj)
            
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz_et_ve_gruba_at()
