import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import os

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except: pass

def analiz():
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # Haftalık (1W) verileri çekiyoruz
    payload = {
        "filter": [{"left": "type", "operation": "in_range", "right": ["stock", "dr", "fund"]}],
        "options": {"lang": "tr"},
        "columns": ["name", "close", "open|52", "low|52", "high|52", "change|52"],
        "range": [0, 1000]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20).json()
        hisseler = res.get("data", [])
        
        t_mesaj("🔨 *Haftalık Çekiç Formasyonu Taraması Başladı...*")

        found_count = 0
        for item in hisseler:
            d = item.get('d', [])
            hisse, fiyat, acilis_h, dusuk_h, yuksek_h, degisim = d[0], d[1], d[2], d[3], d[4], d[5]
            
            if not all([fiyat, acilis_h, dusuk_h, yuksek_h]): continue

            # --- ÇEKİÇ MATEMATİĞİ ---
            body = abs(fiyat - acilis_h)
            lower_shadow = min(acilis_h, fiyat) - dusuk_h
            upper_shadow = yuksek_h - max(acilis_h, fiyat)
            
            # Kriter: Alt fitil gövdenin en az 2 katı, üst fitil çok küçük (gövdeden küçük)
            is_hammer = (lower_shadow > body * 2) and (upper_shadow < body) and (body > 0)
            
            if is_hammer:
                found_count += 1
                df = yf.download(f"{hisse}.IS", period="1y", interval="1wk", progress=False)
                if df.empty: continue
                
                # Veri temizleme
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                
                dosya = f"{hisse}_cekic.png"
                mpf.plot(df, type='candle', style='charles', volume=True,
                         title=f"\n{hisse} - HAFTALIK CEKIC", savefig=dosya)
                
                caption = (f"🔨 *{hisse}* - Haftalık Çekiç\n"
                           f"💰 Fiyat: `{fiyat:.2f}` (%{degisim:.2f})\n"
                           f"⬆️ Haftalık En Yüksek: `{yuksek_h:.2f}`\n"
                           f"⬇️ Haftalık En Düşük: `{dusuk_h:.2f}`\n"
                           f"⚠️ Alıcılar dipten güçlü topladı!")
                
                with open(dosya, 'rb') as photo:
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'Markdown'}, 
                                  files={'photo': photo})
                os.remove(dosya)

        if found_count == 0:
            t_mesaj("✅ Tarama tamamlandı. Bu hafta Çekiç formasyonu yapan hisse bulunamadı.")
        else:
            t_mesaj(f"✅ Toplam {found_count} hissede haftalık çekiç tespit edildi.")

    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
