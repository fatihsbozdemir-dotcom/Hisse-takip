import yfinance as yf
import pandas as pd
import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # Hisseleri tek tek değil, gruplar halinde (batch) çekiyoruz
        data = yf.download(hisseler, period="3y", group_by='ticker', threads=False)
        
        bulunan = []
        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 144: continue
                
                fiyat = df['Close'].iloc[-1]
                # GÜNLÜK SMA
                for n in [55, 89, 144]:
                    sma = df['Close'].rolling(window=n).mean().iloc[-1]
                    if abs(fiyat - sma) / sma < 0.015:
                        bulunan.append(f"📅 *{ticker.replace('.IS','')}* (G) -> SMA {n}")

                # HAFTALIK SMA
                df_w = df['Close'].resample('W').last()
                if len(df_w) >= 144:
                    w_fiyat = df_w.iloc[-1]
                    for n in [55, 89, 144]:
                        w_sma = df_w.rolling(window=n).mean().iloc[-1]
                        if abs(w_fiyat - w_sma) / w_sma < 0.02:
                            bulunan.append(f"🌟 *{ticker.replace('.IS','')}* (H) -> SMA {n}")
            except:
                continue

        if bulunan:
            t_mesaj("🚀 *FİBONACCİ TEMASLARI*\n\n" + "\n".join(sorted(list(set(bulunan)))))
        else:
            t_mesaj("✅ Bugün temas eden hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
