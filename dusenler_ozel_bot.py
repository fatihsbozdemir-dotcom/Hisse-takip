import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import datetime

# ================= CONFIGURATION (AYARLAR) =================
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGcc?oPN-QcYULJ5_UVHw" # Tokenini kontrol et
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# ===========================================================

def mesaj_gonder(metin):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': metin, 'parse_mode': 'Markdown'})

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def analiz_yap():
    try:
        su_an = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        mesaj_gonder(f"📉 *7 GÜNLÜK SERİ DÜŞÜŞ TARAMASI BAŞLADI*\n📅 {su_an}")

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisseler = df_sheet['Hisse'].dropna().tolist()

        found_count = 0

        for hisse in hisseler:
            try:
                ticker = hisse if "." in hisse else f"{hisse}.IS"
                df = yf.download(ticker, period="30d", interval="1d", progress=False, auto_adjust=True)
                
                if df.empty or len(df) < 8: continue
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

                # Düşüş Kontrolü: Son 7 günün her biri bir öncekinden düşük mü?
                son_7_gun = df['Close'].tail(7).tolist()
                is_falling = True
                for i in range(1, len(son_7_gun)):
                    if son_7_gun[i] >= son_7_gun[i-1]: # Eğer bir gün bile yüksekse bozulsun
                        is_falling = False
                        break

                if is_falling:
                    found_count += 1
                    son_fiyat = float(df['Close'].iloc[-1])
                    toplam_kayip = ((son_fiyat / float(df['Close'].iloc[-7])) - 1) * 100
                    
                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    
                    mpf.plot(df.tail(20), type='candle', style=s,
                             title=f"\n{ticker} - 7 Gunluk Seri Dusus",
                             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                    buf.seek(0)

                    aciklama = (f"🔴 *SERİ DÜŞÜŞ TESPİT EDİLDİ*\n\n"
                                f"🏢 *Hisse:* `{ticker}`\n"
                                f"💰 *Son Fiyat:* {son_fiyat:.2f}\n"
                                f"📉 *7 Günlük Kayıp:* %{toplam_kayip:.2f}\n"
                                f"⚠️ *Durum:* Aralıksız 7 iş günü düşüş.")

                    fotograf_gonder(buf, aciklama)

            except Exception as e:
                print(f"Hata [{hisse}]: {e}")
                continue

        mesaj_gonder(f"✅ *Tarama Tamamlandı.*\nUygun bulunan hisse sayısı: **{found_count}**")

    except Exception as e:
        mesaj_gonder(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
