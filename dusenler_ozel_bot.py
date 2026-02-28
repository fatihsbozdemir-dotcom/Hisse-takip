import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import datetime

# ================= CONFIGURATION (AYARLAR) =================
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# KRİTER: Kaç gün üst üste düşüş arıyoruz? (Test için 3 idealdir)
DUSUS_GUN_SAYISI = 3 
# ===========================================================

def mesaj_gonder(metin):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': metin, 'parse_mode': 'Markdown'})
    except: pass

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, files=files, data=data)
    except: pass

def analiz_yap():
    try:
        # Google Sheet'ten listeyi çek
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisseler = df_sheet['Hisse'].dropna().tolist()
        
        found_count = 0
        su_an = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        mesaj_gonder(f"🚀 *Tarama Başladı ({su_an})*\n🔍 {len(hisseler)} hisse kontrol ediliyor...")

        for hisse in hisseler:
            try:
                # Hisse formatını düzelt (THYAO -> THYAO.IS)
                ticker = hisse.strip()
                if not ticker.endswith(".IS"):
                    ticker += ".IS"
                
                # Veriyi çek
                df = yf.download(ticker, period="1mo", interval="1d", progress=False, auto_adjust=True)
                if df.empty or len(df) < DUSUS_GUN_SAYISI + 1:
                    continue

                # Sütun isimlerini temizle
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # Düşüş Kontrolü (Son X günün her biri bir öncekinden düşük mü?)
                son_gunler = df['Close'].tail(DUSUS_GUN_SAYISI).tolist()
                bir_onceki_gun = df['Close'].iloc[-(DUSUS_GUN_SAYISI + 1)]
                
                # Karşılaştırma listesi oluştur (Örn: [G-3, G-2, G-1, G-0])
                tum_liste = [bir_onceki_gun] + son_gunler
                
                is_falling = True
                for i in range(1, len(tum_liste)):
                    if tum_liste[i] >= tum_liste[i-1]:
                        is_falling = False
                        break

                if is_falling:
                    found_count += 1
                    son_fiyat = float(df['Close'].iloc[-1])
                    ilk_fiyat = float(df['Close'].iloc[-(DUSUS_GUN_SAYISI)])
                    kayip = ((son_fiyat / ilk_fiyat) - 1) * 100

                    # Grafik Çizimi
                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    
                    mpf.plot(df.tail(20), type='candle', style=s,
                             title=f"\n{ticker} - {DUSUS_GUN_SAYISI} Gunluk Seri Dusus",
                             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                    buf.seek(0)

                    aciklama = (f"🔴 *SERİ DÜŞÜŞ TESPİT EDİLDİ*\n\n"
                                f"🏢 *Hisse:* `{ticker}`\n"
                                f"💰 *Fiyat:* {son_fiyat:.2f}\n"
                                f"📉 *Seri Kayıp:* %{kayip:.2f}\n"
                                f"⚠️ *Durum:* Aralıksız {DUSUS_GUN_SAYISI} iş günü kırmızı kapanış.")

                    fotograf_gonder(buf, aciklama)

            except Exception as e:
                print(f"Hata [{hisse}]: {e}")
                continue

        mesaj_gonder(f"✅ *Tarama Tamamlandı.*\nUygun bulunan hisse sayısı: **{found_count}**")

    except Exception as e:
        mesaj_gonder(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
