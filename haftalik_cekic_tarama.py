import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except: pass

def analiz():
    # TradingView'dan sadece hisse listesini ve güncel fiyatı çekiyoruz (En stabil kısım)
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        data = res.get("data", [])
        if not data:
            t_mesaj("⚠️ Liste boş döndü, bağlantı kontrol ediliyor...")
            return

        t_mesaj(f"🚀 *{len(data)}* hisse için haftalık mum formasyonları analiz ediliyor...")

        for item in data:
            hisse = item['d'][0]
            fiyat = item['d'][1]
            
            # Detaylı veriyi yfinance üzerinden çekiyoruz (Daha güvenilir)
            df = yf.download(f"{hisse}.IS", period="6mo", interval="1wk", progress=False)
            
            if df.empty or len(df) < 4: continue
            
            # Multi-index temizliği
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Son 3 haftanın verileri (0: en yeni, 1: geçen hafta, 2: önceki hafta)
            m1 = df.iloc[-1] # Bu hafta
            m2 = df.iloc[-2] # Geçen hafta
            m3 = df.iloc[-3] # Önceki hafta
            
            formasyon = None
            
            # Mum Parametreleri
            body1 = abs(m1['Close'] - m1['Open'])
            lower_s1 = min(m1['Open'], m1['Close']) - m1['Low']
            upper_s1 = m1['High'] - max(m1['Open'], m1['Close'])
            
            # 1. ÇEKİÇ (Hammer)
            if (lower_s1 > body1 * 2) and (upper_s1 < body1 * 0.5) and body1 > 0:
                formasyon = "🔨 Çekiç (Hammer)"
            
            # 2. TERS ÇEKİÇ (Inverted Hammer)
            elif (upper_s1 > body1 * 2) and (lower_s1 < body1 * 0.5) and body1 > 0:
                formasyon = "⛏️ Ters Çekiç"

            # 3. YUTAN BOĞA (Bullish Engulfing)
            elif m2['Close'] < m2['Open'] and m1['Close'] > m1['Open'] and \
                 m1['Close'] >= m2['Open'] and m1['Open'] <= m2['Close']:
                formasyon = "🌊 Yutan Boğa (Engulfing)"

            # 4. SABAH YILDIZI (Morning Star)
            elif m3['Close'] < m3['Open'] and abs(m2['Close']-m2['Open']) < abs(m3['Close']-m3['Open'])*0.3 \
                 and m1['Close'] > m1['Open'] and m1['Close'] > (m3['Open'] + m3['Close'])/2:
                formasyon = "⭐ Sabah Yıldızı"

            if formasyon:
                dosya = f"{hisse}_form.png"
                mpf.plot(df, type='candle', style='charles', volume=True,
                         title=f"\n{hisse} - {formasyon}", savefig=dosya)
                
                caption = (f"🔥 *{hisse}* - Formasyon Tespit Edildi!\n"
                           f"📊 Formasyon: `{formasyon}`\n"
                           f"💰 Fiyat: `{m1['Close']:.2f}`\n"
                           f"📈 Yüksek: `{m1['High']:.2f}` | 📉 Düşük: `{m1['Low']:.2f}`")
                
                with open(dosya, 'rb') as photo:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                                  files={'photo': photo})
                os.remove(dosya)

        t_mesaj("✅ Haftalık formasyon taraması tamamlandı.")

    except Exception as e:
        t_mesaj(f"❌ Kritik Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
