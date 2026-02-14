import yfinance as yf
import pandas as pd
import requests

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        pass

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        # ".IS" eklemesini yaparak Yahoo formatına getiriyoruz
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # EMA50'nin oturması için çekebileceğimiz maksimum veriyi çekiyoruz
        data = yf.download(hisseler, period="max", interval="1d", group_by='ticker', threads=True)
        
        bulunanlar = []

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 60: continue 

                # TradingView uyumlu EMA hesaplama
                df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()

                # Son 5 günün verilerini alalım
                son_5 = df.tail(5)
                
                # Kesişme veya Yakınlaşma Kontrolü
                for i in range(1, len(son_5)):
                    e20_bugun = son_5['ema20'].iloc[i]
                    e50_bugun = son_5['ema50'].iloc[i]
                    e20_dun = son_5['ema20'].iloc[i-1]
                    e50_dun = son_5['ema50'].iloc[i-1]
                    
                    # 1. ŞART: Tam Kesişme (Dün altındaydı bugün üstünde)
                    kesisme = e20_dun <= e50_dun and e20_bugun > e50_bugun
                    
                    # 2. ŞART: Çok Yakın (%0.3 marj) - TV'de "kesişti" görünenler buraya düşer
                    fark = (e20_bugun - e50_bugun) / e50_bugun
                    yakinlasma = abs(fark) < 0.
