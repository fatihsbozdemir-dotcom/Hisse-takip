import yfinance as yf
import pandas as pd
import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # EMA hesaplamasının oturması için 'max' periyot çekiyoruz
        data = yf.download(hisseler, period="2y", interval="1d", group_by='ticker', threads=True)
        
        bulunanlar = []

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 100: continue 

                # TradingView uyumlu EMA (Hassas hesaplama)
                df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()

                # SON 5 GÜNÜN HERHANGİ BİRİNDE KESİŞME VAR MI?
                # Veya EMA20, EMA50'yi yeni mi yukarı kırmış?
                
                for i in range(1, 6): # Son 5 gün
                    idx_bugun = -i
                    idx_dun = -(i + 1)
                    
                    e20_b = df['ema20'].iloc[idx_bugun]
                    e50_b = df['ema50'].iloc[idx_bugun]
                    e20_d = df['ema20'].iloc[idx_dun]
                    e50_d = df['ema50'].iloc[idx_dun]

                    # 1. ŞART: Tam Kesişme (Dün altında, bugün üstünde)
                    # 2. ŞART: Kesişmiş ve fark yeni açılıyor (%0.5 dahilinde yakınlık)
                    if (e20_d <= e50_d and e20_b > e50_b):
                        tarih = df.index[idx_bugun].strftime('%d.%m')
                        bulunanlar.append(f"🔥 *{ticker.replace('.IS','')}*\n✅ EMA 20/50 KESİŞTİ ({tarih})\n💰 Fiyat: {df['Close'].iloc[idx_bugun]:.2f}")
                        break 
                    
                    # 3. ŞART: Zaten kesişmiş ama hala çok taze (Son 3 günde %1'den az farkla üstteyse)
                    elif i <= 3 and (e20_b > e50_b) and (e20_d > e50_d) and ((e20_b - e50_b) / e50_b < 0.01):
                        bulunanlar.append(f"🚀 *{ticker.replace('.IS','')}*\n✅ EMA 20/50 ÜSTÜNDE (Taze Trend)\n💰 Fiyat: {df['Close'].iloc[idx_bugun]:.2f}")
                        break

            except: continue

        if bulunanlar:
            t_mesaj("📢 *GÜNCEL EMA 20/50 TARAMA SONUÇLARI*\n\n" + "\n\n".join(set(bulunanlar)))
        else:
            t_mesaj("✅ Tarama yapıldı. Şu an kriterlere uyan (yeni kesişmiş veya taze trendde olan) hisse yok.")
            
    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
