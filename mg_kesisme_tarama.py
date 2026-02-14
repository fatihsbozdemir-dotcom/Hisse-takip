import yfinance as yf
import pandas as pd
import requests

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=10)
    except:
        pass

def calculate_wma(df, length):
    weights = list(range(1, length + 1))
    return df['Close'].rolling(window=length).apply(lambda x: (x * weights).sum() / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        data = yf.download(hisseler, period="3mo", interval="1d", group_by='ticker', threads=True)
        
        kesisenler = []

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 20: continue 

                df['wma9'] = calculate_wma(df, 9)
                df['wma15'] = calculate_wma(df, 15)

                # Son 3 günü kontrol et (Bugün, Dün, Önceki Gün)
                # i=1 (Bugün), i=2 (Dün), i=3 (Önceki Gün) kesişmiş mi?
                for i in range(1, 4):
                    idx_bugun = -i
                    idx_dun = -(i + 1)
                    
                    bugun_w9 = df['wma9'].iloc[idx_bugun]
                    bugun_w15 = df['wma15'].iloc[idx_bugun]
                    dun_w9 = df['wma9'].iloc[idx_dun]
                    dun_w15 = df['wma15'].iloc[idx_dun]

                    # Golden Cross kontrolü
                    if dun_w9 <= dun_w15 and bugun_w9 > bugun_w15:
                        fiyat = df['Close'].iloc[idx_bugun]
                        gun_bilgisi = "Bugün" if i == 1 else f"{i-1} Gün Önce"
                        kesisenler.append(f"🚀 *{ticker.replace('.IS','')}*\n✅ WMA 9/15 Kesişimi: *{gun_bilgisi}*\n💰 O Günkü Fiyat: {fiyat:.2f}")
                        break # Bir kez bulması yeterli, döngüden çık
            except:
                continue

        if kesisenler:
            t_mesaj("🔔 *MG-HİSSE GÜNLÜK KESİŞME RAPORU (SON 3 GÜN)*\n\n" + "\n\n".join(kesisenler))
        else:
            t_mesaj("✅ Son 3 gün içerisinde WMA 9/15 kesişmesi yapan yeni hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ Kesişme Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
