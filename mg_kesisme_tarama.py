import requests
from tradingview_screener import Query
import pandas as pd

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        pass

def analiz():
    try:
        # Sorguyu kütüphanenin en stabil versiyonuna göre kuruyoruz
        # turkey marketinde EMA20'nin EMA50'den büyük olduğu hisseleri getir
        q = Query().set_markets('turkey') \
            .select('name', 'close', 'EMA20', 'EMA50') \
            .where(
                # 'above' hatasını gidermek için doğrudan string karşılaştırma 
                # veya kütüphanenin güncel filter yapısını kullanıyoruz
                ('EMA20', 'above', 'EMA50')
            ) \
            .get_scanner_data()

        # get_scanner_data() [0] metadata, [1] verileri döndürür
        rows = q[1]

        bulunanlar = []
        for row in rows:
            # TradingView bazen 'BIST:HİSSE' formatında döner, temizleyelim
            hisse_adi = row['ticker'].split(':')[-1] if ':' in row['ticker'] else row['ticker']
            fiyat = row['close']
            ema20 = row['EMA20']
            ema50 = row['EMA50']
            
            # Son kontrol: Kesişme çok taze mi? (Fark %0.5'ten küçükse yeni kesişmiştir)
            fark = (ema20 - ema50) / ema50
            if 0 < fark < 0.005:
                bulunanlar.append(f"🔥 *{hisse_adi}*\n✅ TV Sinyali: EMA 20/50 Yeni Kesişti\n💰 Fiyat: {fiyat:.2f}\n🎯 Fark: %{fark*100:.2f}")

        if bulunanlar:
            t_mesaj("🚀 *TRADINGVIEW CANLI EMA 20/50 TARAMASI*\n\n" + "\n\n".join(bulunanlar[:20]))
        else:
            t_mesaj("🔍 TradingView'da şu an *yeni kesişmiş* (fark %0.5 altı) hisse bulunamadı.")

    except Exception as e:
        # Hatayı daha detaylı görmek için
        t_mesaj(f"❌ TV Tarama Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
