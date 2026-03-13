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
        
        sonuclar = []
        for hisse in hisseler:
            try:
                df_h = yf.download(hisse, period="1mo", interval="1d")
                if len(df_h) < 20: continue
                
                fiyatlar = df_h['Close'].values
                seri = pd.Series(fiyatlar)
                sma = seri.rolling(window=20).mean()
                std = seri.rolling(window=20).std()
                bant_genisligi = (std / sma).iloc[-1]
                
                sonuclar.append((hisse, bant_genisligi, df_h.tail(20)))
            except: continue
        
        # En düşük bant genişliğine sahip ilk 10'u seç
        sonuclar.sort(key=lambda x: x[1])
        
        for h, b, data in sonuclar[:10]:
            plt.figure(figsize=(8, 4))
            plt.plot(data['Close'].values, color='blue', linewidth=2)
            plt.title(f"{h} - Sıkışma Skoru: {b:.4f}")
            plt.grid(True, linestyle='--', alpha=0.6)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                          data={'chat_id': CHAT_ID, 'caption': f"🎯 {h} - En iyi yatay hisselerden!"}, 
                          files={'photo': ('grafik.png', buf)})
            time.sleep(1.5) # Telegram spam engeli için
            
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': f"Sistem Hatası: {str(e)}"})

if __name__ == "__main__":
    analiz_et()
