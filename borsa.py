import yfinance as yf
import requests
from datetime import datetime

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

# Takip listesi ve Alarm fiyatları (Hisse: Hedef Fiyat)
ALARM_LISTESI = {
    "THYAO.IS": 280.50, # Örnek hedef fiyatlar
    "TRILC.IS": 65.00,
    "BINHO.IS": 50.00
}

def mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
    requests.post(url, json=payload)

def alarm_kontrol():
    hisseler = list(ALARM_LISTESI.keys())
    # Güncel fiyatları çek
    data = yf.download(hisseler, period="1d", interval="1m")['Close'].iloc[-1]
    
    rapor_mesaji = f"🕒 Saatlik Kontrol ({datetime.now().strftime('%H:%M')})\n\n"
    alarm_caldi_mi = False

    for hisse, guncel_fiyat in data.items():
        hedef_fiyat = ALARM_LISTESI[hisse]
        
        # Eğer güncel fiyat hedef fiyatı geçtiyse veya çok yaklaştıysa (%0.5 tolerans)
        if guncel_fiyat >= hedef_fiyat:
            rapor_mesaji += f"🚨 ALARM: {hisse} HEDEFİ GEÇTİ!\n💰 Fiyat: {guncel_fiyat:.2f} TL\n🎯 Hedef: {hedef_fiyat:.2f} TL\n\n"
            alarm_caldi_mi = True
        else:
            rapor_mesaji += f"🔹 {hisse}: {guncel_fiyat:.2f} TL (Hedef: {hedef_fiyat})\n"

    # Her durumda raporu gönder (İsterseniz sadece alarm çalınca göndermesi için 'if alarm_caldi_mi' yapabilirsiniz)
    mesaj_gonder(rapor_mesaji)

if __name__ == "__main__":
    alarm_kontrol()
