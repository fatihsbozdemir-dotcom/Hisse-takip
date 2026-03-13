import yfinance as yf
import pandas as pd
import requests
import io
import time
import mplfinance as mpf # Mum grafiği için

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
                df_h = yf.download(hisse, period="1mo", interval="1d").tail(20)
                if len(df_h) < 5: continue
                
                low = float(df_h['Low'].min())
                high = float(df_h['High'].max())
                marj = ((high - low) / low) * 100
                
                if marj <= ARALIK_YUZDE:
                    # Mum Grafiği Oluştur
                    buf = io.BytesIO()
                    mpf.plot(df_h, type='candle', style='charles', title=f"{hisse} Sıkışma: %{marj:.2f}", 
                             ylabel='Fiyat', savefig=dict(fname=buf, format='png'))
                    buf.seek(0)
                    
                    # Gönder
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': f"🎯 {hisse} - Mum Grafiği"}, 
                                  files={'photo': ('grafik.png', buf)})
                    time.sleep(1)
            except: continue
    except: pass

if __name__ == "__main__":
    analiz_et()
