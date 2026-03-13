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
        # Türkiye saati ile başlangıç mesajı
        simdi = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
        baslangic_notu = f"🔍 *{simdi.strftime('%H:%M')}* Günlük %1-%5 Dar Bant Taraması Başladı..."
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': baslangic_notu, 'parse_mode': 'Markdown'})

        # Excel verisini oku
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        bulunan_sayi = 0

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse.lower() == 'nan': continue
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            
            # GÜNLÜK VERİ: Son 3 ayın günlük verilerini çekiyoruz
            ticker = yf.Ticker(t_name)
            hist = ticker.history(period="3mo", interval="1d")
            
            if hist.empty or len(hist) < 5: continue
            
            # --- 5 GÜNLÜK YATAY KONTROLÜ ---
            son_5_gun = hist.tail(5)
            en_yuksek = son_5_gun['High'].max()
            en_dusuk = son_5_gun['Low'].min()
            guncel_fiyat = son_5_gun['Close'].iloc[-1]
            
            # Kanal genişliği (Volatility) hesaplama
            # (En Yüksek - En Düşük) / En Düşük * 100
            kanal_genisligi = ((en_yuksek - en_dusuk) / en_dusuk) * 100
            
            # KRİTER: %1 ile %5 arasında bir sıkışma var mı?
            if 1.0 <= kanal_genisligi <= 5.0:
                bulunan_sayi += 1
                
                # Grafik Ayarları (Mum Grafiği)
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                buf = io.BytesIO()
                # Son 20 günün grafiğini göster (Sıkışmayı net görmek için)
                mpf.plot(hist.tail(20), type='candle', style=s, volume=True, 
                         title=f"\n{hisse} (Gunluk)", 
                         ylabel='Fiyat (TL)',
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                # Telegram Mesajı
                msg = (f"🟦 *SIKIŞMA TESPİT EDİLDİ*\n"
                       f"📊 *Hisse:* {hisse}\n"
                       f"💰 *Fiyat:* {guncel_fiyat:.2f} TL\n"
                       f"📏 *5 Günlük Marj:* %{kanal_genisligi:.2f}\n"
                       f"🔝 *Direnç:* {en_yuksek:.2f}\n"
                       f"⬇️ *Destek:* {en_dusuk:.2f}")
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': ('plot.png', buf, 'image/png')}, 
                              data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

        # Sonuç Bildirimi
        if bulunan_sayi == 0:
             requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': '✅ Tarama bitti. %1-%5 arası daralan hisse bulunamadı.'})
        else:
             requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'✅ Tarama bitti. Toplam {bulunan_sayi} hisse bulundu.'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata oluştu: {str(e)}'})

if __name__ == "__main__":
    analiz_et()
