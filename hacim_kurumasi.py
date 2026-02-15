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
        
        telegram_gonder("📊 *Çift Onaylı Tarama:* Hacim Dipte & Fiyat Dipte")

        for sembol in hisseler:
            df = yf.download(f"{sembol}.IS", period="1y", interval="1d", progress=False)
            if df.empty or len(df) < 60: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # 1. HACİM ŞARTI: 20 Günlük Ortalamanın %50 altı
            df['Vol_MA20'] = df['Volume'].rolling(window=20).mean()
            su_anki_vol = df['Volume'].iloc[-1]
            ort_vol = df['Vol_MA20'].iloc[-1]
            hacim_kurudu_mu = su_anki_vol < (ort_vol * 0.5)

            # 2. FİYAT DİPTE ŞARTI: Son 6 ayın en düşüğüne %10 mesafe
            # Son 125 işlem günü yaklaşık 6 aya denk gelir
            son_6_ay = df.tail(125)
            en_dusuk = son_6_ay['Low'].min()
            su_anki_fiyat = df['Close'].iloc[-1]
            
            # Fiyat en düşüğün en fazla %10 üzerindeyse "Dipte" kabul ediyoruz
            fiyat_dipte_mi = su_anki_fiyat <= (en_dusuk * 1.10)

            # İKİ ŞART DA SAĞLANIYORSA
            if hacim_kurudu_mu and fiyat_dipte_mi:
                df_plot = df.tail(40).copy()
                resim_adi = f"{sembol}.png"
                
                # Beyaz hacim ortalamasını ekle
                ap = [mpf.make_addplot(df_plot['Vol_MA20'], panel=1, color='white', width=1.2)]
                
                mpf.plot(df_plot, type='candle', style='charles', volume=True,
                         addplot=ap, title=f"\n{sembol} - HEM HACIM HEM FIYAT DIPTE", savefig=resim_adi)
                
                oran = (su_anki_vol / ort_vol) * 100
                dip_mesafe = ((su_anki_fiyat / en_dusuk) - 1) * 100
                
                bilgi = (f"🎯 *{sembol}*\n"
                         f"📉 Hacim Oranı: `% {oran:.1f}`\n"
                         f"📏 Dibe Uzaklık: `% {dip_mesafe:.1f}`\n"
                         f"💰 Fiyat: `{su_anki_fiyat:.2f}`\n"
                         f"📍 6 Ayın En Düşüğü: `{en_dusuk:.2f}`")
                
                telegram_gonder(bilgi, resim_adi)
                os.remove(resim_adi)

        telegram_gonder("✅ Çift onaylı rapor tamamlandı.")
    except Exception as e:
        telegram_gonder(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
