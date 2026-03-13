import yfinance as yf
import pandas as pd
import requests
import io
import time
import matplotlib.pyplot as plt

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

# YATAYLIK SKORU: Değer küçüldükçe fiyat daha yataydır (0.05 ve altı çok iyidir)
MAX_VOLATILITE = 0.08 

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        for hisse in hisseler:
            try:
                # Son 10 iş gününü net alıyoruz
                df_h = yf.download(hisse, period="1mo", interval="1d").tail(10)
                if len(df_h) < 10: continue
                
                fiyatlar = df_h['Close'].values
                seri = pd.Series(fiyatlar)
                
                # 5 günlük hareketli ortalama ve standart sapma ile yataylık skoru
                sma = seri.rolling(window=5).mean()
                std = seri.rolling(window=5).std()
                bant_genisligi = (std / sma).iloc[-1]
                
                if bant_genisligi < MAX_VOLATILITE:
                    # Grafiği Çiz
                    plt.figure(figsize=(8, 4))
                    plt.plot(df_h['Close'].values, color='purple', marker='o', linewidth=2)
                    plt.title(f"{hisse} - 10 Günlük Yataylık Skoru: {bant_genisligi:.4f}")
                    plt.grid(True, linestyle='--', alpha=0.7)
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plt.close()
                    
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': f"🎯 {hisse} - Yatay Sıkışma Yakalandı!\nSkor: {bant_genisligi:.4f}"}, 
                                  files={'photo': ('grafik.png', buf)})
                    time.sleep(1.5)
            except: continue
    except Exception as e:
        pass

if __name__ == "__main__":
    analiz_et()
