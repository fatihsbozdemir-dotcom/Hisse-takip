import yfinance as yf
import pandas as pd
import requests
import io
import time
import matplotlib.pyplot as plt

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"
ARALIK_YUZDE = 5.0 

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        for hisse in hisseler:
            try:
                df_hisse = yf.download(hisse, period="7d", interval="1d").tail(5)
                if len(df_hisse) < 5: continue
                
                low = float(df_hisse['Low'].min())
                high = float(df_hisse['High'].max())
                marj = ((high - low) / low) * 100
                
                if marj <= ARALIK_YUZDE:
                    # Grafik Çiz
                    plt.figure(figsize=(6, 4))
                    plt.plot(df_hisse['Close'], marker='o', color='red')
                    plt.title(f"{hisse} - Sıkışma Marjı: %{marj:.2f}")
                    plt.grid(True)
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plt.close()
                    
                    # Grafiği gönder
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': f"🎯 {hisse} bulundu! Marj: %{marj:.2f}"}, 
                                  files={'photo': ('grafik.png', buf)})
                    time.sleep(1)
            except: continue
    except: pass

if __name__ == "__main__":
    analiz_et()
