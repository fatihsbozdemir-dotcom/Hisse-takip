import yfinance as yf
import pandas as pd
import requests
import time

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # Veriyi toplu çekiyoruz
        data = yf.download(hisseler, period="3y", group_by='ticker', threads=False)
        
        bulunan = []
        # Fibonacci sayılarını genişlettik: 21, 34, 55, 89, 144
        fibo_numbers = [21, 34, 55, 89, 144]
        
        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 144: continue
                
                fiyat = df['Close'].iloc[-1]
                
                # --- GÜNLÜK TARAMA (%3 Hass
