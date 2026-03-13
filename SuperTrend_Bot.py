import yfinance as yf
import pandas as pd
import requests
import io
import time
import matplotlib.pyplot as plt
import numpy as np

# BOT AYARLARI
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def get_supertrend(df, period=7, multiplier=3):
    """Modern ve hatasız SuperTrend hesaplama."""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    upperband = ((high + low) / 2) + (multiplier * atr)
    lowerband = ((high + low) / 2) - (multiplier * atr)
    
    st = pd.Series(index=df.index, dtype='float64')
    trend = pd.Series(index=df.index, dtype='int')
    
    for i in range(period, len(df)):
        if close.iloc[i] > upperband.iloc[i-1]:
            trend.iloc[i] = 1
        elif close.iloc[i] < lowerband.iloc[i-1]:
            trend.iloc[i] = -1
        else:
            trend.iloc[i] = trend.iloc[i-1] if not pd.isna(trend.iloc[i-1]) else 1
            
        st.iloc[i] = lowerband.iloc[i] if trend.iloc[i] == 1 else upperband.iloc[i]
            
    return st, trend

def analiz_et():
    # Başlangıç bildirimi
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': "📊 SuperTrend Botu devrede! Trend dönüşleri taranıyor..."})
    
    try:
        r = requests.get(SHEET_URL)
        df_list = pd.read_csv(io.StringIO(r.text))
        hisseler = [str(x).strip().replace(".IS", "") + ".IS" for x in df_list.iloc[:, 0].dropna()]
        
        sinyal_sayisi = 0
        for hisse in hisseler:
            try:
                df = yf.download(hisse, period="3mo", interval="1d")
                if len(df) < 20: continue
                
                st, trend = get_supertrend(df)
                
                # Trend Değişimi: Satıştan ( -1 ) -> Alışa ( 1 ) geçtiği an
                if trend.iloc[-1] == 1 and trend.iloc[-2] == -1:
                    sinyal_sayisi += 1
                    
                    # Grafik Oluştur
                    plt.figure(figsize=(10, 5))
                    plt.plot(df['Close'].tail(30), label='Fiyat', color='black', alpha=0.6)
                    plt.plot(st.tail(30), label='SuperTrend', color='green', linewidth=2)
                    plt.title(f"AL SİNYALİ: {hisse}")
                    plt.legend()
                    plt.grid(True)
                    
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plt.close()
                    
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': f"🚀 {hisse} - Yeni Yükseliş Trendi Başladı!"}, 
                                  files={'photo': ('grafik.png', buf)})
                    time.sleep(2)
            except: continue
        
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': f"✅ Tarama bitti. {sinyal_sayisi} hisse AL sinyali verdi."})
            
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': f"❌ Hata: {str(e)}"})

if __name__ == "__main__":
    analiz_et()
