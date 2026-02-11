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

def yatay_kontrol(df):
    # Bollinger Bantları ile sıkışma (Squeeze) kontrolü
    ma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    ust_bant = ma20 + (2 * std20)
    alt_bant = ma20 - (2 * std20)
    
    # Bant Genişliği
    bant_genisligi = (ust_bant - alt_bant) / ma20
    
    # Son 5 günün ortalama genişliği, son 100 günün en dar %15'lik dilimindeyse
    su_anki_genislik = bant_genisligi.iloc[-1]
    esik_deger = bant_genisligi.rolling(window=100).quantile(0.15).iloc[-1]
    
    return su_anki_genislik <= esik_deger

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('squeeze.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def sadece_yatay_ara():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisse_listesi = df_sheet['Hisse'].tolist()
        
        bulunan_hisseler = []

        for hisse in hisse_listesi:
            ticker = yf.Ticker(hisse)
            hist = ticker.history(period="6mo", interval="1d")
            
            if len(hist) < 30: continue

            if yatay_kontrol(hist):
                # Sıkışma bulunduysa grafik hazırla
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                # Bollinger Bantlarını grafiğe ekle
                ma20 = hist['Close'].rolling(window=20).mean()
                std20 = hist['Close'].rolling(window=20).std()
                ust = ma20 + (2 * std20)
                alt = ma20 - (2 * std20)
                add_plot = [mpf.make_addplot(ust.tail(40), color='gray', alpha=0.3),
                            mpf.make_addplot(alt.tail(40), color='gray', alpha=0.3)]

                buf = io.BytesIO()
                mpf.plot(hist.tail(40), type='candle', style=s, addplot=add_plot,
                         title=f"\n{hisse} - Sıkışma (Yatay)",
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                mesaj = (f"🟨 *Yatay Sıkışma Yakalandı!* 🟨\n\n"
                         f"📊 *Hisse:* {hisse}\n"
                         f"💰 *Fiyat:* {hist['Close'].iloc[-1]:.2f} TL\n\n"
                         f"⚠️ Bollinger bantları aşırı daraldı. Sert bir kırılım (patlama) gelebilir.")
                
                fotograf_gonder(buf, mesaj)
                bulunan_hisseler.append(hisse)

        if not bulunan_hisseler:
            print("Yatayda hisse bulunamadı.")
                
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    sadece_yatay_ara()
