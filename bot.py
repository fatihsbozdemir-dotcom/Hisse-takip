import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import datetime

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845" 
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def analiz_et():
    try:
        simdi = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f"🔍 *Tarama Başladı:* {simdi.strftime('%H:%M')}\nKriter: 50-200 Gün / Max %35 Marj", 'parse_mode': 'Markdown'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        bulunan_sayi = 0
        # MERCN gibi hisseleri kaçırmamak için periyotları sıklaştırdık
        gun_periyotlari = [50, 75, 100, 125, 150, 175, 200] 

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse.lower() == 'nan': continue
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(t_name)
            
            # auto_adjust=True: Bölünme ve temettüleri hesaba katar (Grafikteki fiyatla eşleşir)
            hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
            
            if hist.empty or len(hist) < 50: continue
            
            # Hisse için uygun bir periyot bulalım
            bulundu = False
            for gun in gun_periyotlari:
                if len(hist) < gun: continue
                
                data = hist.tail(gun)
                en_yuksek = data['High'].max()
                en_dusuk = data['Low'].min()
                
                # Kanal marjı hesapla
                marj = ((en_yuksek - en_dusuk) / en_dusuk) * 100
                
                # ŞART: %1 ile %35 arası
                if 1.0 <= marj <= 35.0:
                    bulunan_sayi += 1
                    guncel_fiyat = data['Close'].iloc[-1]
                    
                    # Grafik Oluştur
                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    mpf.plot(data, type='candle', style=s, title=f"\n{hisse} ({gun} Gun)", savefig=dict(fname=buf, format='png'))
                    buf.seek(0)
                    
                    # Detaylı Bilgi Mesajı
                    msg = (f"✅ *HİSSE BULUNDU: {hisse}*\n"
                           f"━━━━━━━━━━━━━━━\n"
                           f"📅 *Analiz Periyodu:* {gun} GÜN\n"
                           f"📐 *Kanal Marjı:* %{marj:.2f}\n"
                           f"💰 *Son Fiyat:* {guncel_fiyat:.2f} TL\n"
                           f"🔝 *Zirve:* {en_yuksek:.2f}\n"
                           f"⬇️ *Dip:* {en_dusuk:.2f}\n"
                           f"━━━━━━━━━━━━━━━\n"
                           f"🤖 *Sistem:* %35 Geniş Bant Taraması")
                    
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                                  files={'photo': (f'{hisse}.png', buf, 'image/png')}, 
                                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
                    
                    bulundu = True
                    break # Bir periyotta bulduysak diğer günlere bakma
            
    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f"❌ Hata: {str(e)}"})

if __name__ == "__main__":
    analiz_et()
