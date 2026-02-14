import requests
from tradingview_screener import Query, Column
import pandas as pd

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    try:
        # TradingView Tarayıcı Sorgusu
        # BIST hisselerinde EMA 20, EMA 50'yi yukarı kesenleri getir
        rows = (Query().set_markets('turkey')
                .select('name', 'close', 'EMA20', 'EMA50')
                .where(
                    Column('EMA20').above(Column('EMA50')), # Şu an üstünde olanlar
                    Column('EMA20').crosses_above(Column('EMA50')) # Veya yeni kesenler
                )
                .get_scanner_data()[1])

        bulunanlar = []
        for row in rows:
            hisse_adi = row['ticker']
            fiyat = row['close']
            bulunanlar.append(f"🔥 *{hisse_adi}*\n✅ TV Sinyali: EMA 20/50 Kesişti\n💰 Fiyat: {fiyat:.2f}")

        if bulunanlar:
            # Mesaj çok uzunsa ilk 15 hisseyi gönder (Telegram sınırı için)
            t_mesaj("🚀 *TRADINGVIEW CANLI EMA 20/50 TARAMASI*\n\n" + "\n\n".join(bulunanlar[:15]))
        else:
            t_mesaj("🔍 TradingView tarayıcısında şu an anlık EMA 20/50 kesişmesi bulunamadı.")

    except Exception as e:
        t_mesaj(f"❌ TV Tarama Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
