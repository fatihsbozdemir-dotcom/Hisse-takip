import yfinance as yf
import pandas as pd
import requests
import io
import time

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def bot_mesaj_gonder(mesaj):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': mesaj})
    except: pass

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        bot_mesaj_gonder(f"🚀 {len(hisseler)} hisse için hata giderilmiş tarama başlıyor...")

        for hisse in hisseler[:5]:
            try:
                # Veriyi çek
                df_hisse = yf.download(hisse, period="7d", interval="1d").tail(5)
                if len(df_hisse) < 5: continue
                
                # Sütunları temizle ve float yap
                low = float(df_hisse['Low'].min())
                high = float(df_hisse['High'].max())
                
                # Marjı hesapla
                marj = ((high - low) / low) * 100
                
                bot_mesaj_gonder(f"🔍 {hisse} durumu:\n📉 5 Günlük Marj: %{marj:.2f}")
                time.sleep(1)
            except Exception as e:
                bot_mesaj_gonder(f"❌ {hisse} analiz edilemedi: {str(e)}")
        
        bot_mesaj_gonder("✅ Test raporu tamamlandı.")
        
    except Exception as e:
        bot_mesaj_gonder(f"❌ Ana Hata: {str(e)}")

if __name__ == "__main__":
    analiz_et()
