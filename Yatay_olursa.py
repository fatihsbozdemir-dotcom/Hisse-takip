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
        
        for hisse in hisseler[:30]: # Test için ilk 30 hisseyi tara
            try:
                df_h = yf.download(hisse, period="1mo", interval="1d").tail(20)
                if len(df_h) < 20: continue
                
                # Bollinger genişliği (Yataylık göstergesi)
                sma = df_h['Close'].rolling(window=20).mean()
                std = df_h['Close'].rolling(window=20).std()
                bant_genisligi = (std / sma).iloc[-1]
                
                sonuclar.append((hisse, bant_genisligi))
            except: continue
        
        # En düşük bant genişliğine sahip (en yatay) ilk 3 hisseyi bul
        sonuclar.sort(key=lambda x: x[1])
        en_iyiler = sonuclar[:3]
        
        mesaj = "📊 Güncel En İyi 3 Yatay Hisse:\n"
        for h, b in en_iyiler:
            mesaj += f"{h}: Bant Genişliği {b:.4f}\n"
            
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': mesaj})
                      
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': f"Hata: {str(e)}"})

if __name__ == "__main__":
    analiz_et()
