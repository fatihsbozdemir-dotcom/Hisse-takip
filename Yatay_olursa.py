import yfinance as yf
import pandas as pd
import requests
import io
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"
ARALIK_YUZDE = 10.0 # Test için %10

def bot_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': mesaj})
    except: pass

def analiz_et():
    try:
        r = requests.get(SHEET_URL)
        df = pd.read_csv(io.StringIO(r.text))
        hisseler = list(set([str(x).strip().replace(".IS", "") + ".IS" for x in df.iloc[:, 0].dropna()]))
        
        bot_mesaj_gonder(f"🚀 {len(hisseler)} hisse taranıyor...")

        for hisse in hisseler:
            try:
                data = yf.download(hisse, period="7d", interval="1d").tail(5)
                if len(data) < 5: continue
                
                low = data['Low'].min()
                high = data['High'].max()
                marj = ((high - low) / low) * 100
                
                # HER HİSSEYİ RAPORLA: Bu satır sayesinde sistemin çalıştığını ve marjları göreceksin
                if marj <= ARALIK_YUZDE:
                    bot_mesaj_gonder(f"🎯 {hisse} bulundu! Marj: %{marj:.2f}")
                else:
                    # Sadece kontrol için; çok fazla mesaj gelirse bu satırı silersin
                    print(f"{hisse} marj: %{marj:.2f} (Kriter dışı)")
                
                time.sleep(1)
            except: continue
        
        bot_mesaj_gonder("✅ Tarama tamamlandı.")
        
    except Exception as e:
        bot_mesaj_gonder(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz_et()
