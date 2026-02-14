
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # Sadece EMA 144 (Günlük) ve EMA 144 (Haftalık) kolonlarını bırakıyoruz
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "EMA144", "EMA144|52", "open", "low"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload).json()
        hisseler = res.get("data", [])
        t_mesaj(f"🎯 *{len(hisseler)}* hisse sadece *EMA 144* (G/H) desteğinde taranıyor...")

        for item in hisseler:
            d = item['d']
            hisse, fiyat = d[0], d[1]
            # EMA 144 Günlük ve Haftalık değerleri
            ema_gunluk = d[2]
            ema_haftalik = d[3]
            acilis, dusuk = d[4], d[5]
            
            # --- ÇEKİÇ KONTROLÜ ---
            body = abs(fiyat - acilis)
            lower_shadow = min(acilis, fiyat) - dusuk
            is_hammer = lower_shadow > (body * 2) and body > 0
            
            # --- EMA 144 TEMAS KONTROLÜ ---
            hit_ema = None
            if ema_gunluk and (0.99 <= fiyat/ema_gunluk <= 1.01):
                hit_ema = "EMA 144 (Günlük)"
            elif ema_haftalik and (0.99 <= fiyat/ema_haftalik <= 1.01):
                hit_ema = "EMA 144 (Haftalık)"
            
            if hit_ema:
                # Veri çekme ve temizleme
                df = yf.download(f"{hisse}.IS", period="2y", interval="1d", progress=False)
                if df.empty: continue
                
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df = df.dropna()

                # Grafiğe sadece EMA 144 çizelim
                df['EMA144'] = df['Close'].ewm(span=144, adjust=False).mean()
                
                dosya = f"{hisse}.png"
                ap = [mpf.make_addplot(df['EMA144'], color='orange', width=1.5)]
                
                status = "🔨 ÇEKİÇ + DESTEK" if is_hammer else "🛡️ DESTEK TEMASI"
                
                mpf
