import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "1003838602845" # Eksi işareti kaldırıldı, özel mesaja dönüştü
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
ARALIK_YUZDE = 3.5 # Kriteri test etmek için önce 20 yapabilirsin

def get_hisse_listesi():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(SHEET_URL, headers=headers)
        if response.status_code != 200:
            print(f"❌ Sheets bağlantı hatası: {response.status_code}")
            return []
            
        df = pd.read_csv(io.StringIO(response.text))
        
        # A Sütununu alıyoruz
        ham_liste = df.iloc[:, 0].tolist() 
        
        hisseler = []
        for h in ham_liste:
            sembol = str(h).strip().upper()
            if sembol and sembol != "NAN":
                if not sembol.endswith(".IS"):
                    sembol += ".IS"
                hisseler.append(sembol)
        return list(set(hisseler))
    except Exception as e:
        print(f"❌ Liste çekme hatası: {e}")
        return []

def send_telegram(mesaj, image_data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/"
    try:
        if image_data:
            files = {'photo': ('grafik.png', image
