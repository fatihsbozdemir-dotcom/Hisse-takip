import yfinance as yf
import pandas as pd
import requests
import time

TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"

def bildirim_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': mesaj})

try:
    print("Tarama başlatılıyor...")
    bildirim_gonder("🚀 Tarama başladı!")
    
    # Veriyi çek
    df = pd.read_csv("https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv")
    hisseler = [str(x) + ".IS" for x in df.iloc[:, 0].dropna()]
    
    # Sadece ilk 5 hisse ile test edelim (Hata varsa çabuk görelim)
    for hisse in hisseler[:5]:
        print(f"{hisse} taranıyor...")
        data = yf.download(hisse, period="1mo", interval="1d").tail(10)
        # Eğer veri boşsa veya hata varsa görelim
        if data.empty:
            print(f"{hisse} verisi boş!")
            continue
            
    bildirim_gonder("✅ Tarama başarıyla bitti.")
    
except Exception as e:
    bildirim_gonder(f"❌ HATA: {str(e)}")
    print(f"HATA: {e}")
