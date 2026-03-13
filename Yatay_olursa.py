import yfinance as yf
import pandas as pd
import requests
import io
import time

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        sonuclar = []
        
        for hisse in hisseler[:30]: # Test için 30'lu devam edelim
            try:
                # Veriyi çek ve sadece 'Close' fiyatlarını al
                df_h = yf.download(hisse, period="1mo", interval="1d")
                if len(df_h) < 20: continue
                
                fiyatlar = df_h['Close'].values # Etiketleri sildik, sadece sayıları aldık
                
                # Bollinger Bant genişliğini ham sayılarla hesapla
                # Pandas Series yerine numpy dizisi (values) kullandığımız için hata vermeyecek
                seri = pd.Series(fiyatlar)
                sma = seri.rolling(window=20).mean()
                std = seri.rolling(window=20).std()
                bant_genisligi = (std / sma).iloc[-1]
                
                sonuclar.append((hisse, bant_genisligi))
            except Exception: continue
        
        # Sırala ve Telegram'a gönder
        sonuclar.sort(key=lambda x: x[1])
        mesaj = "📊 En Yatay 3 Hisse (Düşük Bant Genişliği):\n"
        for h, b in sonuclar[:3]:
            mesaj += f"{h}: {b:.4f}\n"
            
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': mesaj})
                      
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': f"Kritik Hata: {str(e)}"})

if __name__ == "__main__":
    analiz_et()
