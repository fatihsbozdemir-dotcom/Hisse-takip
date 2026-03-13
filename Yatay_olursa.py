import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
ARALIK_YUZDE = 20.0 # Test için 20 yaptık

def analiz_et():
    # Botun çalıştığını anlamak için başlangıç mesajı
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                  data={'chat_id': CHAT_ID, 'text': "🚀 Tarama başladı!"})
    
    hisseler = get_hisse_listesi()
    print(f"🚀 {len(hisseler)} hisse taranıyor...")
    
    for hisse in hisseler:
        try:
            data = yf.download(hisse, period="7d", interval="1d").tail(5)
            if len(data) < 5: continue
            marj = ((data['High'].max() - data['Low'].min()) / data['Low'].min()) * 100
            
            # Kriteri sağlıyorsa gönder
            if marj <= ARALIK_YUZDE:
                mesaj = f"✅ {hisse} bulundu! Marj: %{marj:.2f}"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                              data={'chat_id': CHAT_ID, 'text': mesaj})
        except Exception as e:
            print(f"Hata: {e}")

# ... (get_hisse_listesi fonksiyonu aynı kalacak)
