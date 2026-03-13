import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import io
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "1003838602845"
SHEET_ID = "BURAYA_SHEET_ID_YAZ" # ÖRNEK: 1A2B3C4D5E6F...
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
ARALIK_YUZDE = 3.5 # Tarama kriteri (%3.5)

def get_hisse_listesi():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(SHEET_URL, headers=headers)
        if response.status_code != 200:
            print(f"❌ Sheets bağlantı hatası: {response.status_code}")
            return []
            
        df = pd.read_csv(io.StringIO(response.text))
        
        # A Sütununu alıyoruz (ilk sütun)
        ham_liste = df.iloc[:, 0].tolist() 
        
        hisseler = []
        for h in ham_liste:
            sembol = str(h).strip().upper()
            if sembol and sembol != "NAN":
                if not sembol.endswith(".IS"):
                    sembol += ".IS"
                hisseler.append(sembol)
        return list(set(hisseler)) # Tekrar edenleri temizle
    except Exception as e:
        print(f"❌ Liste çekme hatası: {e}")
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
        print(f"❌ Telegram gönderim hatası: {e}")

def analiz_et():
    hisseler = get_hisse_listesi()
    print(f"🚀 {len(hisseler)} hisse taranıyor...")
    
    for hisse in hisseler:
        try:
            data = yf.download(hisse, period="7d", interval="1d").tail(5)
            if len(data) < 5: continue

            yuksek = data['High'].max()
            dusuk = data['Low'].min()
            marj = ((yuksek - dusuk) / dusuk) * 100

            if marj <= ARALIK_YUZDE:
                plt.figure(figsize=(10, 5))
                plt.plot(data.index.strftime('%d-%m'), data['Close'], marker='o', color='teal', linewidth=2)
                plt.title(f"{hisse} - Son 5 Günlük Sıkışma (%{marj:.2f})")
                plt.grid(True, linestyle='--', alpha=0.5)
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()

                mesaj = f"🎯 *Hisse:* `{hisse}`\n📊 *Dar Bant Marjı:* %{marj:.2f}\n✅ Sıkışma tespit edildi."
                send_telegram(mesaj, buf)
                time.sleep(2) # Hız sınırı için
        except Exception as e:
            print(f"⚠️ {hisse} analizi yapılamadı: {e}")

if __name__ == "__main__":
    analiz_et()
