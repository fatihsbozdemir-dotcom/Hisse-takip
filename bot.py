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
                      json={'chat_id': CHAT_ID, 'text': f"🚀 *{simdi.strftime('%H:%M')}* Geniş Bant (%35) Taraması Başlatıldı...", 'parse_mode': 'Markdown'})

        # Tabloyu çek
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        bulunan_sayi = 0
        # 50'den 200'e kadar 10'ar gün arayla her ihtimali tara
        gun_araliklari = range(50, 210, 10)

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse.lower() == 'nan': continue
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(t_name)
            
            # auto_adjust=True grafikle birebir eşleşme sağlar
            hist = ticker.history(period="1y", interval="1d", auto_adjust=True)
            
            if hist.empty or len(hist) < 50: continue
            
            for gun in gun_araliklari:
                if len(hist) < gun: continue
                
                temp_df = hist.tail(gun)
                
                # KRİTER: En Yüksek ve En Düşük arasındaki % farkı
                en_yuksek = temp_df['High'].max()
                en_dusuk = temp_df['Low'].min()
                kanal_genisligi = ((en_yuksek - en_dusuk) / en_dusuk) * 100
                
                # SENİN KRİTERİN: MAKSİMUM %35
                if 1.0 <= kanal_genisligi <= 35.0:
                    bulunan_sayi += 1
                    son_fiyat = temp_df['Close'].iloc[-1]
                    
                    # Grafiği hazırla
                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    mpf.plot(temp_df, type='candle', style=s, title=f"\n{hisse} - {gun} Gunluk SIKISMA", savefig=dict(fname=buf, format='png'))
                    buf.seek(0)
                    
                    # Bilgi Mesajı
                    msg = (f"🎯 *UYGUN HİSSE:* #{hisse}\n"
                           f"📊 *Tarama:* %35 Dar Bant\n"
                           f"⏳ *Zaman Dilimi:* Son {gun} Gün\n"
                           f"📏 *Toplam Hareket:* %{kanal_genisligi:.2f}\n"
                           f"💰 *Fiyat:* {son_fiyat:.2f} TL\n"
                           f"🔝 *Zirve:* {en_yuksek:.2f} / ⬇️ *Dip:* {en_dusuk:.2f}")
                    
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                                  files={'photo': (f'{hisse}.png', buf, 'image/png')}, 
                                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
                    
                    break # Bu hisse için bir periyot bulduysak diğerlerine bakma

        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f"✅ Tarama bitti. Toplam {bulunan_sayi} hisse bulundu."})

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    analiz_et()
