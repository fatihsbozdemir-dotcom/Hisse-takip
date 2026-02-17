import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def telegram_gonder(mesaj, dosya=None):
    if dosya:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        try:
            with open(dosya, 'rb') as f:
                requests.post(url, data={'chat_id': CHAT_ID, 'caption': mesaj, 'parse_mode': 'Markdown'}, files={'photo': f})
        except: pass
    else:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz_yap():
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {"filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
               "options": {"lang": "tr"}, "columns": ["name"], "range": [0, 500]}
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        hisseler = [item['d'][0] for item in res.get("data", [])]
        
        telegram_gonder("🚀 *Hacimli Kalkış Taraması Başladı...*\n(Hacmi Ortalamanın Üzerine Çıkan ve Dipten Dönenler)")

        for sembol in hisseler:
            df = yf.download(f"{sembol}.IS", period="1y", interval="1d", progress=False)
            if df.empty or len(df) < 30: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # 20 GÜNLÜK HACİM ORTALAMASI
            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
            su_anki_vol = df['Volume'].iloc[-1]
            ort_vol = df['Vol_MA20'].iloc[-1]

            # 1. HACİM ŞARTI: Hacim ortalamanın en az 1.5 katı (MACKO gibi patlamalar için)
            hacim_guclu_mu = su_anki_vol > (ort_vol * 1.5)

            # 2. FİYAT DİPTE ŞARTI: Son 6 ayın en düşüğüne %20 mesafe (Kalkış payı bıraktık)
            son_6_ay = df.tail(125)
            en_dusuk = son_6_ay['Low'].min()
            su_anki_fiyat = df['Close'].iloc[-1]
            fiyat_dipte_mi = su_anki_fiyat <= (en_dusuk * 1.20)

            # 3. YÜKSELİŞ ŞARTI: Bugünün mumu yeşil mi?
            bugun_pozitif_mi = su_anki_fiyat > df['Open'].iloc[-1]

            if hacim_guclu_mu and fiyat_dipte_mi and bugun_pozitif_mi:
                df_plot = df.tail(40).copy()
                resim_adi = f"{sembol}_patlama.png"
                
                # Beyaz hacim ortalamasını ekle
                ap = [mpf.make_addplot(df_plot['Vol_MA20'], panel=1, color='white', width=1.5)]
                
                mpf.plot(df_plot, type='candle', style='charles', volume=True,
                         addplot=ap, title=f"\n{sembol} - HACIMLI DIPTEN DONUS", savefig=resim_adi)
                
                oran = su_anki_vol / ort_vol
                dip_uzaklik = ((su_anki_fiyat / en_dusuk) - 1) * 100
                
                bilgi = (f"🚀 *{sembol}*\n"
                         f"📊 Hacim Gücü: `{oran:.2f}x` (Ortalama Üstü)\n"
                         f"📏 Dibe Uzaklık: `% {dip_uzaklik:.1f}`\n"
                         f"💰 Fiyat: `{su_anki_fiyat:.2f}`")
                
                telegram_gonder(bilgi, resim_adi)
                os.remove(resim_adi)

        telegram_gonder("✅ Hacimli kalkış raporu tamamlandı.")
    except Exception as e:
        telegram_gonder(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
