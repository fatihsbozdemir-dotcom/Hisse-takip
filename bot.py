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
        baslangic_notu = f"🔭 *{simdi.strftime('%H:%M')}* 50-200 Günlük Geniş Tarama Başladı..."
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': baslangic_notu, 'parse_mode': 'Markdown'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        bulunan_sayi = 0
        # Kontrol edilecek gün aralıkları
        gun_periyotlari = [50, 100, 150, 200]

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse.lower() == 'nan': continue
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            
            # 1 yıllık veri çekelim ki 200 günü analiz edebilelim
            ticker = yf.Ticker(t_name)
            hist = ticker.history(period="1y", interval="1d")
            
            if hist.empty or len(hist) < 200: continue
            
            en_iyi_periyot = None
            en_dar_marj = 100

            # 50, 100, 150 ve 200 günleri tek tek kontrol et
            for gun in gun_periyotlari:
                data = hist.tail(gun)
                en_yuksek = data['High'].max()
                en_dusuk = data['Low'].min()
                kanal_genisligi = ((en_yuksek - en_dusuk) / en_dusuk) * 100
                
                # Bu periyotta %1 - %10 arası bir yataylık var mı? 
                # (Uzun vadede %5 çok zor olduğu için sınırı %10 yaptım, isterseniz değiştirebilirsiniz)
                if 1.0 <= kanal_genisligi <= 10.0:
                    if kanal_genisligi < en_dar_marj:
                        en_dar_marj = kanal_genisligi
                        en_iyi_periyot = gun
                        fiyat_detay = (en_yuksek, en_dusuk, data['Close'].iloc[-1])

            if en_iyi_periyot:
                bulunan_sayi += 1
                zirve, dip, son_fiyat = fiyat_detay
                
                # Grafik
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                buf = io.BytesIO()
                # Grafikte seçilen periyodu göster
                mpf.plot(hist.tail(en_iyi_periyot + 20), type='candle', style=s, 
                         title=f"\n{hisse} ({en_iyi_periyot} Gunluk)", 
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                msg = (f"📈 *UZUN VADE SIKIŞMA*\n"
                       f"📊 *Hisse:* {hisse}\n"
                       f"⏱ *Periyot:* Last {en_iyi_periyot} Days\n"
                       f"💰 *Son Fiyat:* {son_fiyat:.2f} TL\n"
                       f"📏 *Kanal Genişliği:* %{en_dar_marj:.2f}\n"
                       f"📐 *Direnç:* {zirve:.2f} / *Destek:* {dip:.2f}")
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': ('longterm.png', buf, 'image/png')}, 
                              data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'✅ Tarama bitti. {bulunan_sayi} adet uzun vade sıkışma bulundu.'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata: {str(e)}'})

if __name__ == "__main__":
    analiz_et()
