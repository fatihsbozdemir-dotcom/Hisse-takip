import yfinance as yf
import pandas as pd
import requests

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def wma(data, period):
    weights = list(range(1, period + 1))
    return data.rolling(period).apply(lambda x: (weights * x).sum() / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # Günlük (1d) veri çekiyoruz
        data = yf.download(hisseler, period="3mo", interval="1d", group_by='ticker', threads=True)
        
        kesisenler = []

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 20: continue 

                # WMA 9 ve 15 Hesaplama
                df['wma9'] = wma(df['Close'], 9)
                df['wma15'] = wma(df['Close'], 15)

                # Kesişme Kontrolü (Crossover)
                # Bugün: WMA9 > WMA15 VE Dün: WMA9 <= WMA15
                bugun_w9 = df['wma9'].iloc[-1]
                bugun_w15 = df['wma15'].iloc[-1]
                dun_w9 = df['wma9'].iloc[-2]
                dun_w15 = df['wma15'].iloc[-2]

                if dun_w9 <= dun_w15 and bugun_w9 > bugun_w15:
                    fiyat = df['Close'].iloc[-1]
                    kesisenler.append(f"🚀 *{ticker.replace('.IS','')}*\n✅ WMA 9, WMA 15'i Yukarı Kesti!\n💰 Fiyat: {fiyat:.2f}")
            except:
                continue

        if kesisenler:
            t_mesaj("🔔 *GÜNLÜK WMA KESİŞME RAPORU*\n\n" + "\n\n".join(kesisenler))
        else:
            t_mesaj("✅ Bugün WMA 9/15 kesişmesi yapan hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ Kesişme Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
