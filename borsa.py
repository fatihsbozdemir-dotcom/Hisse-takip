import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
# Sadece ID kısmını bıraktık:
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
    requests.post(url, json=payload)

def sheet_verilerini_al():
    # Google Sheets'i direkt CSV olarak çeker
    df_sheet = pd.read_csv(SHEET_URL)
    return dict(zip(df_sheet['Hisse'], df_sheet['Hedef_Fiyat']))

def alarm_sistemi():
    try:
        alarm_listesi = sheet_verilerini_al()
        hisseler = list(alarm_listesi.keys())
        
        # Fiyatları çek
        data = yf.download(hisseler, period="1d", interval="1m")['Close'].iloc[-1]
        
        rapor = f"📱 Google Sheets Raporu ({datetime.now().strftime('%H:%M')})\n\n"
        
        # Eğer tek bir hisse varsa 'data' seri döner, birden fazlaysa dataframe döner. 
        # Bu yüzden veriyi sözlüğe çevirip garantiye alıyoruz:
        guncel_fiyatlar = data.to_dict() if len(hisseler) > 1 else {hisseler[0]: data}

        for hisse, guncel_fiyat in guncel_fiyatlar.items():
            hedef = alarm_listesi[hisse]
            if guncel_fiyat >= hedef:
                rapor += f"✅ {hisse}: {guncel_fiyat:.2f} TL (HEDEF GEÇİLDİ! 🎯)\n"
            else:
                rapor += f"⏳ {hisse}: {guncel_fiyat:.2f} TL (Hedef: {hedef})\n"
        
        mesaj_gonder(rapor)
    except Exception as e:
        mesaj_gonder(f"⚠️ Hata oluştu: {str(e)}")

if __name__ == "__main__":
    alarm_sistemi()
