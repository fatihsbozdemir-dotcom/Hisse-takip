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
                      json={'chat_id': CHAT_ID, 'text': f'🤖 *{simdi.strftime("%H:%M")}* Analiz Başladı...'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        bulunan_sayi = 0

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse == 'nan': continue
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            hist = yf.Ticker(t_name).history(period="6mo", interval="1wk")
            
            if hist.empty or len(hist) < 5: continue
            
            # --- ANALİZ MANTIĞI ---
            guncel_fiyat = hist['Close'].iloc[-1]
            
            # 1. Arz Bölgesi (Son 6 ayın zirvesi)
            arz_zirve = hist['High'].max()
            mesafe_yuzde = ((arz_zirve - guncel_fiyat) / guncel_fiyat) * 100
            arz_bolgesinde_mi = mesafe_yuzde <= 3.0 # Zirveye %3 yakınsa
            
            # 2. Yatay Sıkışma (Son 5 hafta)
            son_5 = hist.tail(5)
            kanal_genisligi = ((son_5['High'].max() - son_5['Low'].min()) / son_5['Low'].min()) * 100
            is_yatay = 2.0 <= kanal_genisligi <= 10.0
            
            # Karar
            bildir = False
            tip = ""
            
            if arz_bolgesinde_mi and is_yatay:
                tip = "⚠️ KRİTİK: ARZ BÖLGESİNDE SIKIŞMA"
                bildir = True
            elif arz_bolgesinde_mi:
                tip = "🟥 ARZ BÖLGESİ (SATIŞ BASKISI)"
                bildir = True
            elif is_yatay:
                tip = "🟨 YATAY SIKIŞMA"
                bildir = True

            if bildir:
                bulunan_sayi += 1
                
                # Grafik Görselleştirme
                buf = io.BytesIO()
                mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                mpf.plot(hist.tail(20), type='candle', style=s, volume=True, 
                         title=f"\n{hisse}", savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                buf.seek(0)
                
                msg = f"📢 *{tip}*\n📊 *Hisse:* {hisse}\n💰 *Fiyat:* {guncel_fiyat:.2f} TL\n🏔️ *Zirveye Uzaklık:* %{mesafe_yuzde:.2f}"
                
                requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': buf}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})

        if bulunan_sayi == 0:
             requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': '✅ Tarama bitti. Kriterlere uygun hisse bulunamadı.'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f'❌ Hata: {str(e)}'})

if __name__ == "__main__":
    analiz_et()
