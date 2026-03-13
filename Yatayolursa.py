import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "1003838602845"
SHEET_ID = "BURAYA_GOOGLE_SHEET_ID_YAZ" # Linkteki ID'yi buraya yapıştır
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
ARALIK_YUZDE = 3.5

def get_hisse_listesi():
    try:
        # Google Sheets'ten veriyi çek
        df = pd.read_csv(SHEET_URL)
        
        # D sütunu iloc[:, 3] demektir.
        # Eğer tabloda başlık (header) varsa otomatik atlar.
        ham_liste = df.iloc[:, 3].tolist() 
        
        hisseler = []
        for h in ham_liste:
            sembol = str(h).strip().upper()
            if sembol and sembol != "NAN": # Boş satırları atla
                # .IS eki yoksa otomatik ekle
                if not sembol.endswith(".IS"):
                    sembol += ".IS"
                hisseler.append(sembol)
        
        print(f"✅ D sütunundan {len(hisseler)} hisse başarıyla alındı.")
        return hisseler
    except Exception as e:
        print(f"❌ Liste çekilirken hata: {e}")
        return []

def send_telegram(mesaj, image_data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/"
    try:
        if image_data:
            files = {'photo': ('grafik.png', image_data, 'image/png')}
            requests.post(url + "sendPhoto", data={'chat_id': CHAT_ID, 'caption': mesaj, 'parse_mode': 'Markdown'}, files=files)
        else:
            requests.post(url + "sendMessage", data={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})
    except Exception as e:
        print(f"❌ Telegram hatası: {e}")

def analiz_et():
    hisseler = get_hisse_listesi()
    if not hisseler: return

    for hisse in hisseler:
        try:
            # 5 iş günü verisi
            data = yf.download(hisse, period="7d", interval="1d").tail(5)
            if len(data) < 5: continue

            yuksek = data['High'].max()
            dusuk = data['Low'].min()
            marj = ((yuksek - dusuk) / dusuk) * 100

            if marj <= ARALIK_YUZDE:
                # Grafik çizimi
                plt.figure(figsize=(10, 5))
                plt.plot(data.index.strftime('%d %b'), data['Close'], marker='o', color='teal', linewidth=2)
                plt.title(f"{hisse} - 5 Günlük Sıkışma Marjı: %{marj:.2f}")
                plt.grid(True, linestyle='--', alpha=0.5)
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()

                mesaj = f"🎯 *Hisse:* `{hisse}`\n📊 *Dar Bant Marjı:* %{marj:.2f}\n✅ D sütunundaki listenize göre tespit edildi."
                send_telegram(mesaj, buf)
                time.sleep(1.2)
        except:
            continue

if __name__ == "__main__":
    analiz_et()
