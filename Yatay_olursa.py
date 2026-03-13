import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
ARALIK_YUZDE = 3.5 

def get_hisse_listesi():
    """Hisse listesini çeker, temizler ve çift uzantı hatalarını giderir."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(SHEET_URL, headers=headers)
        if response.status_code != 200: return []
        
        df = pd.read_csv(io.StringIO(response.text))
        raw_list = df.iloc[:, 0].dropna().tolist()
        
        hisseler = []
        for h in raw_list:
            sembol = str(h).strip().upper().replace(".IS", "")
            if not sembol: continue
            hisseler.append(sembol + ".IS")
        return list(set(hisseler))
    except: return []

def analiz_et():
    hisseler = get_hisse_listesi()
    if not hisseler: return

    for hisse in hisseler:
        try:
            data = yf.download(hisse, period="7d", interval="1d").tail(5)
            if len(data) < 5: continue

            # Sıkışma Marjı Hesaplama
            low = data['Low'].min()
            high = data['High'].max()
            marj = ((high - low) / low) * 100

            if marj <= ARALIK_YUZDE:
                # Grafik Oluşturma
                plt.figure(figsize=(6, 4))
                plt.plot(data['Close'], marker='o', color='teal', linewidth=2)
                plt.title(f"{hisse} - Dar Bant Sıkışması: %{marj:.2f}")
                plt.grid(True, alpha=0.5)
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()
                
                # Bilgi Mesajı
                mesaj = (
                    f"✅ *Sıkışma Tespit Edildi!*\n\n"
                    f"📌 *Hisse:* `{hisse}`\n"
                    f"📉 *5 Günlük Dar Bant Marjı:* %{marj:.2f}\n"
                    f"⚙️ *Tarama Kriteri:* %{ARALIK_YUZDE} Altı\n"
                    f"📅 *Tarih:* {time.strftime('%d.%m.%Y')}"
                )
                
                # Telegram'a Gönderim
                files = {'photo': ('grafik.png', buf, 'image/png')}
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                              data={'chat_id': CHAT_ID, 'caption': mesaj, 'parse_mode': 'Markdown'}, 
                              files=files)
                time.sleep(2)
        except: continue

if __name__ == "__main__":
    analiz_et()
