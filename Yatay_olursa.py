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
    """Google Sheet üzerinden hisse listesini alır ve temizler."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(SHEET_URL, headers=headers)
        if response.status_code != 200:
            return []
            
        df = pd.read_csv(io.StringIO(response.text))
        # A sütununu temizle (ilk sütun)
        raw_list = df.iloc[:, 0].dropna().tolist()
        
        hisseler = []
        for h in raw_list:
            sembol = str(h).strip().upper()
            if not sembol: continue
            # Zaten .IS varsa ekleme, yoksa ekle
            if not sembol.endswith(".IS"):
                sembol += ".IS"
            hisseler.append(sembol)
        return list(set(hisseler))
    except Exception as e:
        print(f"Liste çekme hatası: {e}")
        return []

def analiz_et():
    hisseler = get_hisse_listesi()
    print(f"🚀 Toplam {len(hisseler)} hisse taranıyor...")
    
    for hisse in hisseler:
        try:
            # 5 iş günü verisi
            data = yf.download(hisse, period="7d", interval="1d").tail(5)
            if len(data) < 5: continue

            # Marj hesaplama
            low = data['Low'].min()
            high = data['High'].max()
            marj = ((high - low) / low) * 100

            if marj <= ARALIK_YUZDE:
                # Grafik oluştur
                plt.figure(figsize=(6, 4))
                plt.plot(data['Close'], marker='o', linestyle='-', color='teal')
                plt.title(f"{hisse} - Sıkışma: %{marj:.2f}")
                plt.grid(True, alpha=0.3)
                
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                plt.close()
                
                # Telegram Bildirimi
                mesaj = f"🎯 *Hisse:* `{hisse}`\n📊 *Dar Bant Marjı:* %{marj:.2f}\n✅ Sıkışma tespit edildi!"
                
                # Resimli gönderim
                files = {'photo': ('grafik.png', buf, 'image/png')}
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                              data={'chat_id': CHAT_ID, 'caption': mesaj, 'parse_mode': 'Markdown'}, 
                              files=files)
                
                time.sleep(2) # Hız sınırı
        except Exception as e:
            print(f"⚠️ {hisse} analizi sırasında hata: {e}")
            continue

if __name__ == "__main__":
    analiz_et()
