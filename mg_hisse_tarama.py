import yfinance as yf
import pandas as pd
import requests

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"  # Mesajlar artık direkt sana geliyor
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    # Özel mesaj gönderimi
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def wma(data, period):
    # Ağırlıklı Hareketli Ortalama (MG-Hisse Merdiven Yapısı)
    weights = list(range(1, period + 1))
    return data.rolling(period).apply(lambda x: sum(weights * x) / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # 4 saatlik (4h) veri çekme - MG-Hisse ana periyodu
        data = yf.download(hisseler, period="1mo", interval="4h", group_by='ticker', threads=False)
        
        bulunan = []
        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 55: continue 
                
                fiyat = df['Close'].iloc[-1]

                # 4S MG-Hisse V1 Ortalamaları (WMA)
                wma9 = wma(df['Close'], 9).iloc[-1]
                wma15 = wma(df['Close'], 15).iloc[-1]
                wma55 = wma(df['Close'], 55).iloc[-1]

                durum = ""
                # Kriterler: Yeşil temas, Sarı temas veya Kanal içi
                if abs(fiyat - wma9) / wma9 < 0.05 or abs(fiyat - wma15) / wma15 < 0.05:
                    durum = "🟢 4S Yeşil Bölge Temas"
                elif abs(fiyat - wma55) / wma55 < 0.05:
                    durum = "🟡 4S Sarı Bölge Temas"
                elif (wma15 > fiyat > wma55) or (wma9 > fiyat > wma55):
                    durum = "🌓 4S Kanal İçi (Sıkışma)"

                if durum:
                    bulunan.append(f"📍 *{ticker.replace('.IS','')}*\n💰 Fiyat: {fiyat:.2f}\n📢 {durum}")
            except:
                continue

        if bulunan:
            t_mesaj("🕒 *MG-HİSSE V1: 4 SAATLİK RAPOR*\n\n" + "\n\n".join(bulunan))
        else:
            t_mesaj("✅ MG-Hisse V1: Şartlara uygun hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ MG-Hisse Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
