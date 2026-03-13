import yfinance as yf
import pandas as pd
import requests
import io
import time
import matplotlib.pyplot as plt

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        for hisse in hisseler:
            try:
                df_h = yf.download(hisse, period="1mo", interval="1d").tail(20)
                if len(df_h) < 20: continue
                
                # Bollinger Bantları ile Yataylık Kontrolü (Standart Sapma)
                sma = df_h['Close'].rolling(window=20).mean()
                std = df_h['Close'].rolling(window=20).std()
                bollinger_width = (std / sma)
                
                # Eğer son gün bant genişliği %5'in altındaysa yataydır
                if bollinger_width.iloc[-1] < 0.05:
                    
                    # Basit Mum Grafiği (mplfinance kullanmadan)
                    plt.figure(figsize=(8, 5))
                    up = df_h[df_h.Close >= df_h.Open]
                    down = df_h[df_h.Close < df_h.Open]
                    
                    plt.bar(up.index, up.Close-up.Open, bottom=up.Open, color='green')
                    plt.bar(up.index, up.High-up.Close, bottom=up.Close, color='green')
                    plt.bar(up.index, up.Low-up.Open, bottom=up.Open, color='green')
                    
                    plt.bar(down.index, down.Close-down.Open, bottom=down.Open, color='red')
                    plt.bar(down.index, down.High-down.Close, bottom=down.Close, color='red')
                    plt.bar(down.index, down.Low-down.Open, bottom=down.Open, color='red')
                    
                    plt.title(f"{hisse} - Yatay Sıkışma Yakalandı")
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': f"🎯 {hisse} yatay seyrediyor!"}, 
                                  files={'photo': ('grafik.png', buf)})
                    plt.close()
                    time.sleep(1)
            except: continue
    except: pass

if __name__ == "__main__":
    analiz_et()
