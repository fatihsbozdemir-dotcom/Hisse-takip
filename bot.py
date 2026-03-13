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

# TARAMA KİMLİĞİ
TARAMA_ISMI = "GENİŞ BANT SIKIŞMA ANALİZİ"
STRATEJI_NOTU = "Max %35 Marj / 50-200 Günlük Kontrol"

def analiz_et():
    try:
        simdi = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
        tarih_str = simdi.strftime('%d/%m/%Y %H:%M')
        
        # Giriş Mesajı
        baslangic_msg = (f"🔍 *TARAMA BAŞLATILDI*\n"
                         f"📋 *İsim:* {TARAMA_ISMI}\n"
                         f"⚙️ *Kriter:* {STRATEJI_NOTU}\n"
                         f"⏰ *Zaman:* {tarih_str}")
        
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': baslangic_msg, 'parse_mode': 'Markdown'})

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = [c.strip() for c in df_sheet.columns]
        
        bulunan_sayi = 0
        gun_periyotlari = [50, 100, 150, 200] # Kontrol edilen gün aralıkları

        for index, row in df_sheet.iterrows():
            hisse = str(row.get('Hisse', '')).strip()
            if not hisse or hisse.lower() == 'nan': continue
            
            t_name = hisse if hisse.endswith(".IS") else f"{hisse}.IS"
            ticker = yf.Ticker(t_name)
            hist = ticker.history(period="1y", interval="1d") # 1 yıllık veri çek
            
            if hist.empty or len(hist) < 50: continue
            
            for gun in gun_periyotlari:
                if len(hist) < gun: continue
                
                data = hist.tail(gun)
                en_yuksek = data['High'].max()
                en_dusuk = data['Low'].min()
                kanal_genisligi = ((en_yuksek - en_dusuk) / en_dusuk) * 100
                
                # --- YENİ KRİTER: MAKSİMUM %35 ---
                if 1.0 <= kanal_genisligi <= 35.0:
                    bulunan_sayi += 1
                    guncel_fiyat = data['Close'].iloc[-1]
                    
                    # Grafik Hazırlığı
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    buf = io.BytesIO()
                    mpf.plot(data, type='candle', style=s, title=f"\n{hisse} - {gun} Gunluk", 
                             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                    buf.seek(0)
                    
                    # BİLGİ MESAJI (Kim, Hangi Gün, Ne Taraması)
                    msg = (f"✅ *ADAY HİSSE BULUNDU*\n"
                           f"━━━━━━━━━━━━━━━\n"
                           f"📊 *Tarama:* {TARAMA_ISMI}\n"
                           f"🏢 *Hisse:* #{hisse}\n"
                           f"⏱ *Periyot:* {gun} GÜNLÜK Hareket\n"
                           f"📏 *Tespit Edilen Marj:* %{kanal_genisligi:.2f}\n"
                           f"💰 *Son Fiyat:* {guncel_fiyat:.2f} TL\n"
                           f"📈 *Direnç:* {en_yuksek:.2f} | 📉 *Destek:* {en_dusuk:.2f}\n"
                           f"━━━━━━━━━━━━━━━\n"
                           f"👤 *Analiz Tipi:* Teknik Sıkışma Taraması")
                    
                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", 
                              files={'photo': (f'{hisse}.png', buf, 'image/png')}, 
                              data={'chat_id': CH_ID, 'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
                    
                    break # Bir hisseyi bir periyotta bulduysak diğer günlere bakmaya gerek yok

        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f"🏁 *Tarama Bitti.*\nToplam {bulunan_sayi} hisse kriterlere uygun.", 'parse_mode': 'Markdown'})

    except Exception as e:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={'chat_id': CHAT_ID, 'text': f"❌ Hata: {str(e)}"})

if __name__ == "__main__":
    analiz_et()
