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

def analiz_et():
    try:
        # Google Sheets'ten veriyi çek
        response = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(response.text))
        
        # A sütunundaki hisseleri al
        hisseler = [str(x).strip().upper() + ".IS" for x in df.iloc[:, 0].dropna() if str(x).strip()]
        hisseler = list(set(hisseler)) # Tekrar edenleri temizle
        
        print(f"✅ {len(hisseler)} hisse bulundu, tarama başlıyor...")

        for hisse in hisseler:
            try:
                # 5 iş günü için son 7 günlük veri
                data = yf.download(hisse, period="7d", interval="1d").tail(5)
                if len(data) < 5: continue
                
                # Marj hesabı
                marj = ((data['High'].max() - data['Low'].min()) / data['Low'].min()) * 100
                
                if marj <= ARALIK_YUZDE:
                    # Grafik oluştur
                    plt.figure(figsize=(6, 4))
                    plt.plot(data.index.strftime('%d-%m'), data['Close'], marker='o', color='teal', linewidth=2)
                    plt.title(f"{hisse} - Sıkışma: %{marj:.2f}")
                    plt.grid(True)
                    
                    # Grafiği hafızaya kaydet
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png')
                    buf.seek(0)
                    plt.close()
                    
                    # Telegram'a gönder
                    mesaj = f"🎯 *Hisse:* `{hisse}`\n📊 *Dar Bant Marjı:* %{marj:.2f}\n✅ Sıkışma tespit edildi!"
                    files = {'photo': ('grafik.png', buf, 'image/png')}
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  data={'chat_id': CHAT_ID, 'caption': mesaj, 'parse_mode': 'Markdown'}, 
                                  files=files)
                    
                    time.sleep(2) # Telegram sınırına takılmamak için
            except Exception as e:
                print(f"⚠️ {hisse} analiz edilemedi: {e}")
                
    except Exception as e:
        print(f"❌ Google Sheets hatası: {e}")

if __name__ == "__main__":
    analiz_et()
