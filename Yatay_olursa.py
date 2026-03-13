import yfinance as yf
import pandas as pd
import requests
import io
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"
# Kriteri test etmek için %10 yaptık, hisse bulunca düşürürsün
ARALIK_YUZDE = 10.0 

def bot_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': mesaj})
    except: 
        pass

def analiz_et():
    try:
        # 1. Google Sheets'ten hisseleri çek
        r = requests.get(SHEET_URL)
        if r.status_code != 200:
            bot_mesaj_gonder("❌ Sheets bağlantı hatası!")
            return
            
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        bot_mesaj_gonder(f"🚀 {len(hisseler)} hisse taranıyor (Kriter: %{AR
