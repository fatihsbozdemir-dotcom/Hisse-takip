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
        simdi = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'🤖 *{simdi.strftime("%H:%M")}* %2-%10 Arası Yatay Tarama Başladı...'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        bulunan_sayi = 0

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            hedef = row.get('Hedef_Fiyat', 0)
            try: hedef = float(hedef)
            except: hedef = 0
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            # Son 10 haftalık veri çekelim ki grafikte biraz öncesini görelim
            hist = yf.Ticker(t_name).history(period="6mo", interval="1wk")
            
            if hist.empty or len(hist) < 5: continue
            
            # --- 5 HAFTALIK YATAY KONTROLÜ ---
            son_5_hafta = hist.tail(5)
            en_yuksek = son_5_hafta['High'].max()
            en_dusuk = son_5_hafta['Low'].min()
            guncel_fiyat = son_5_hafta['Close'].iloc[-1]
            
            # Kanal genişliği yüzdesi
            kanal_genisligi = ((en_yuksek - en_dusuk) / en_dusuk) * 100
            
            # KRİTER: %2 ile %10 arasında mı?
            is_yatay = 2.0 <= kanal_genisligi <= 10.0
            
            bildir = False
            tip = ""
            if hedef > 0:
                bildir = True
                tip = "🎯 HEDEF TAKİBİ"
            elif is_yatay:
                bildir = True
                tip = "🟨 %2-%10 YATAY SIKIŞMA"

            if bildir:
                bulunan_sayi += 1
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                
                buf = io.BytesIO()
                mpf.plot(hist.tail(30), type='candle', style=s, volume=True, 
                         title=f"\n{hisse} (Haftalik)", 
                         ylabel='Fiyat (TL)',
                         savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                msg = f"📢 *{tip}*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {guncel_fiyat:.2f} TL"
                if hedef > 0: 
                    msg += f"\n🎯 *Hedef:* {hedef:.2f} TL"
                else:
                    msg += f"\n📏 *5 Haftalık Bant:* %{kanal_genisligi:.2f}"
                    msg += f"\n🔝 *Zirve:* {en_yuksek:.2f} / ⬇️ *Dip:* {en_dusuk:.2f}"
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

        if bulunan_sayi == 0:
             requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': '✅ Tarama bitti. Bu bant aralığında hisse bulunamadı.'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata: {str(e)}'})

if __name__ == "__main__":
    analiz_et()
