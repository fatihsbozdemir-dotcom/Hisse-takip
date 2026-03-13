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
    # 1. Bilgilendirme mesajı
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': "🔍 Tarama başladı, yataylık hesaplanıyor..."})
    
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        bulunanlar = 0
        for hisse in hisseler:
            try:
                # Son 10 iş günü verisi
                df_h = yf.download(hisse, period="1mo", interval="1d").tail(10)
                if len(df_h) < 10: continue
                
                fiyatlar = df_h['Close'].values
                seri = pd.Series(fiyatlar)
                
                # Sıkışma skoru (5 günlük hareketli ortalama üzerinde)
                sma = seri.rolling(window=5).mean()
                std = seri.rolling(window=5).std()
                bant_genisligi = (std / sma).iloc[-1]
                
                # Eğer sıkışma skoru 0.08'in altındaysa yataydır
                if bant_genisligi < 0.15:
                    bulunanlar += 1
                    plt.figure(figsize=(8, 4))
                    plt.plot(df_h['Close'].values, color='purple', marker='o', linewidth=2)
                    plt.title(f"{hisse} - Yatay Skoru: {bant_genisligi:.4f}")
                    plt.grid(True)
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plt.close()
                    
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': f"🎯 {hisse} - Yatay Sıkışma!"}, 
                                  files={'photo': ('grafik.png', buf)})
                    time.sleep(1)
            except: continue
        
        if bulunanlar == 0:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={'chat_id': CHAT_ID, 'text': "✅ Tarama bitti, bu hafta yatay hisse bulunamadı."})
        else:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={'chat_id': CHAT_ID, 'text': f"✅ Tarama bitti, {bulunanlar} adet yatay hisse bulundu."})
            
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': f"❌ Hata: {str(e)}"})

if __name__ == "__main__":
    analiz_et()
