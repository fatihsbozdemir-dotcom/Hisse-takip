import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

# --- AYARLAR ---
# Token sabit kalıyor, CHAT_ID yeni grup ID'si yapıldı
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def mesaj_gonder(mesaj):
    """Gruba düz metin mesajı gönderir"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}
    requests.post(url, data=data)

def rapor_hazirla_ve_gonder():
    try:
        # Google Sheets'ten listeyi çek
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisse_listesi = df_sheet['Hisse'].tolist()
        
        rapor_metni = "📈 *ELİ BÖGRÜNDE - GÜNLÜK RAPOR* 📉\n\n"
        
        for hisse in hisse_listesi:
            # .IS uzantısı yoksa ekle
            ticker_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(ticker_name)
            hist = ticker.history(period="2d") # Son 2 günün verisi
            
            if len(hist) < 2: continue

            # Fiyat ve Değişim Hesapla
            su_anki_fiyat = hist['Close'].iloc[-1]
            onceki_kapanis = hist['Close'].iloc[-2]
            degisim = ((su_anki_fiyat - onceki_kapanis) / onceki_kapanis) * 100
            
            emoji = "🟢" if degisim >= 0 else "🔴"
            arti = "+" if degisim > 0 else ""
            
            rapor_metni += f"{emoji} *{hisse}*: {su_anki_fiyat:.2f} TL (%{arti}{degisim:.2f})\n"

        # Hazırlanan raporu gruba gönder
        mesaj_gonder(rapor_metni)
        print("Rapor başarıyla ELİ BÖGRÜNDE grubuna gönderildi.")
                
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    # Bot çalıştığında raporu gönderir
    rapor_hazirla_ve_gonder()
