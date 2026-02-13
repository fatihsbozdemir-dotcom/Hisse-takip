import pandas as pd
import requests
import pandas_ta as ta
from tvdatafeed import TvDatafeed, Interval

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Mesaj gönderme hatası: {e}")

def analiz():
    try:
        # TradingView Bağlantısı (Misafir)
        tv = TvDatafeed()
        
        # Listeyi Çek
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [str(h).strip() for h in df_sheet.iloc[:, 0].dropna()]
        
        bulunan = []
        
        for hisse in hisseler:
            try:
                # 4 Saatlik Veri (BIST Borsasından)
                df = tv.get_hist(symbol=hisse, exchange='BIST', interval=Interval.in_4_hour, n_bars=100)
                
                if df is None or df.empty:
                    continue

                # MG-Hisse V1 Ortalamaları (WMA)
                df['wma9'] = ta.wma(df['close'], length=9)
                df['wma15'] = ta.wma(df['close'], length=15)
                df['wma55'] = ta.wma(df['close'], length=55)
                
                # Son 6 mum (24 saatlik dilim)
                son_6 = df.tail(6).copy()
                fiyat_simdi = df['close'].iloc[-1]
                
                tes
