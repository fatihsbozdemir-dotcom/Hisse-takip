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
        df_sheet = pd.read_csv(SHEET_URL)
        alarm_listesi = dict(zip(df_sheet['Hisse'], df_sheet['Hedef_Fiyat']))
        
        for hisse, hedef in alarm_listesi.items():
            # Veriyi çek (Son 5 gün, saatlik)
            df = yf.download(hisse, period="5d", interval="60m")['Close']
            guncel_fiyat = df.iloc[-1]
            
            # Grafiği çiz
            foto = grafik_olustur(hisse, df)
            
            # Mesajı hazırla
            durum = "✅ HEDEF GECILDI! 🎯" if guncel_fiyat >= hedef else "⏳ Hedef Bekleniyor"
            mesaj = f"📊 {hisse}\n💰 Guncel: {guncel_fiyat:.2f} TL\n🎯 Hedef: {hedef:.2f} TL\n📝 Durum: {durum}"
            
            # Telegram'a gönder
            fotograf_gonder(foto, mesaj)
            
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": f"⚠️ Hata: {str(e)}"})

if __name__ == "__main__":
    alarm_ve_grafik_sistemi()
