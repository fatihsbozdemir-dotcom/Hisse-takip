import yfinance as yf
import pandas as pd
import requests
import matplotlib.pyplot as plt
import io
from datetime import datetime

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama}
    requests.post(url, files=files, data=data)

def grafik_olustur(hisse, data):
    plt.figure(figsize=(10, 5))
    # Verinin temiz olduğundan emin oluyoruz
    plt.plot(data.index, data.values, marker='o', linestyle='-', color='blue')
    plt.title(f"{hisse} - Son 5 Gunluk Hareket")
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def alarm_ve_grafik_sistemi():
    try:
        # Google Sheets'ten verileri al
        df_sheet = pd.read_csv(SHEET_URL)
        # Sütun isimlerindeki olası boşlukları temizle
        df_sheet.columns = df_sheet.columns.str.strip()
        alarm_listesi = dict(zip(df_sheet['Hisse'], df_sheet['Hedef_Fiyat'].astype(float)))
        
        for hisse, hedef in alarm_listesi.items():
            # Veriyi çek (Son 5 gün)
            ticker = yf.Ticker(hisse)
            hist = ticker.history(period="5d", interval="60m")['Close']
            
            if hist.empty:
                continue

            # Güncel fiyatı alırken hata oluşmaması için .iloc[-1] ve float zorlaması
            guncel_fiyat = float(hist.iloc[-1])
            
            # Grafiği çiz
            foto = grafik_olustur(hisse, hist)
            
            # Mesajı hazırla
            durum = "✅ HEDEF GECILDI! 🎯" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor"
            mesaj = f"📊 {hisse}\n💰 Guncel: {guncel_fiyat:.2f} TL\n🎯 Hedef: {hedef:.2f} TL\n📝 Durum: {durum}"
            
            # Telegram'a gönder
            fotograf_gonder(foto, mesaj)
            
    except Exception as e:
        error_msg = f"⚠️ Hata Detayi: {str(e)}"
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": error_msg})

if __name__ == "__main__":
    alarm_ve_grafik_sistemi()
