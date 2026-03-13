import yfinance as yf
import pandas as pd
import requests
import io
import time

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"
ARALIK_YUZDE = 10.0 # Kriterin bu, istediğin gibi değiştir

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        rapor = []
        for hisse in hisseler:
            try:
                df_hisse = yf.download(hisse, period="7d", interval="1d").tail(5)
                if len(df_hisse) < 5: continue
                
                low = float(df_hisse['Low'].min())
                high = float(df_hisse['High'].max())
                marj = ((high - low) / low) * 100
                
                if marj <= ARALIK_YUZDE:
                    rapor.append(f"{hisse}: %{marj:.2f}")
                
                time.sleep(0.5) # Hızlandırdık
            except: continue
        
        # Sonuçları tek mesajda gönder
        if rapor:
            mesaj = "🎯 Sıkışan Hisseler:\n" + "\n".join(rapor)
        else:
            mesaj = "✅ Tarama bitti, kriterlere uyan hisse yok."
            
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': mesaj})
    except Exception as e:
        pass

if __name__ == "__main__":
    analiz_et()
