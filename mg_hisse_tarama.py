import yfinance as yf
import pandas as pd
import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def wma(series, period):
    weights = list(range(1, period + 1))
    return series.rolling(period).apply(lambda x: (weights * x).sum() / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # 1 saatlik veriyi 1 aylık çekiyoruz (4 saatlik yapı kurmak için en sağlıklısı)
        data = yf.download(hisseler, period="1mo", interval="1h", group_by='ticker', threads=True)
        
        bulunan = []

        for ticker in hisseler:
            try:
                df_1h = data[ticker].dropna()
                if df_1h.empty: continue
                
                # --- TRADINGVIEW UYUMLU 4 SAATLİK MUM YAPISI ---
                # Borsa İstanbul 10:00'da açılır. 10-14, 14-18 mumlarını doğru birleştirelim.
                df = df_1h.resample('4H', offset='2H').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                }).dropna()
                
                # MG-Hisse Ortalamaları (WMA)
                df['wma9'] = wma(df['Close'], 9)
                df['wma15'] = wma(df['Close'], 15)
                df['wma55'] = wma(df['Close'], 55)
                
                # Son 6 mumda (24 saat) temas var mı?
                son_6 = df.tail(6)
                fiyat_simdi = df['Close'].iloc[-1]
                
                for i in range(len(son_6)):
                    f = son_6['Close'].iloc[i]
                    w9 = son_6['wma9'].iloc[i]
                    w15 = son_6['wma15'].iloc[i]
                    w55 = son_6['wma55'].iloc[i]
                    
                    # Hassasiyeti %4 yapalım ki hiçbir şeyi kaçırmasın
                    if abs(f-w9)/w9 < 0.04 or abs(f-w15)/w15 < 0.04:
                        bulunan.append(f"📍 *{ticker.replace('.IS','')}* 🟢 Yeşil Temas\n💰 Fiyat: {fiyat_simdi:.2f}")
                        break # Bir kez bulması yeterli
                    elif abs(f-w55)/w55 < 0.04:
                        bulunan.append(f"📍 *{ticker.replace('.IS','')}* 🟡 Sarı Temas\n💰 Fiyat: {fiyat_simdi:.2f}")
                        break

            except: continue

        if bulunan:
            t_mesaj("🕒 *MG-HİSSE V1 (4S) TARAMA SONUCU*\n\n" + "\n\n".join(set(bulunan)))
        else:
            t_mesaj("✅ Tarama yapıldı, kriterlere uyan hisse şu an yok.")
            
    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
