import yfinance as yf
import pandas as pd
import requests
import io
import time
import mplfinance as mpf
import numpy as np

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

# YATAYLIK KRİTERİ: 
# Volatiliteyi (fiyatın sapmasını) ölçüyoruz. Düşük olması "yatay" olduğu anlamına gelir.
MAX_VOLATILITE = 0.02 

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        for hisse in hisseler:
            try:
                df_h = yf.download(hisse, period="1mo", interval="1d").tail(10)
                if len(df_h) < 10: continue
                
                # YATAYLIK HESABI: Fiyatların standart sapmasının ortalamaya oranı
                fiyatlar = df_h['Close']
                volatilite = fiyatlar.std() / fiyatlar.mean()
                
                # Fiyatın son 10 günde hareket etme aralığı
                degisim = (fiyatlar.max() - fiyatlar.min()) / fiyatlar.min()
                
                # Hem volatilite düşük olmalı (yataylık) hem de değişim aralığı küçük olmalı
                if volatilite < MAX_VOLATILITE and degisim < 0.05:
                    
                    buf = io.BytesIO()
                    mpf.plot(df_h, type='candle', style='charles', title=f"{hisse} - YATAY", 
                             ylabel='Fiyat', savefig=dict(fname=buf, format='png'))
                    buf.seek(0)
                    
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': f"🎯 {hisse} - Yatay Sıkışma Yakalandı!"}, 
                                  files={'photo': ('grafik.png', buf)})
                    time.sleep(1)
            except: continue
    except: pass

if __name__ == "__main__":
    analiz_et()
