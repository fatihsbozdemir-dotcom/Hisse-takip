
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
        requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        pass

def calculate_wma(df, length):
    weights = list(range(1, length + 1))
    return df['Close'].rolling(window=length).apply(lambda x: (x * weights).sum() / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # EMA 50 için en az 6-8 aylık veri çekmek daha sağlıklıdır
        data = yf.download(hisseler, period="8mo", interval="1d", group_by='ticker', threads=True)
        
        sinyaller = []

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 60: continue 

                # Ortalamaları Hesapla
                df['wma9'] = calculate_wma(df, 9)
                df['wma15'] = calculate_wma(df, 15)
                df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()

                name = ticker.replace('.IS', '')
                
                # Son 5 iş gününü kontrol et
                for i in range(1, 6):
                    idx_bugun = -i
                    idx_dun = -(i + 1)
                    
                    zaman = "Bugün" if i == 1 else f"{i-1} Gün Önce"

                    # --- STRATEJİ 1: WMA 9 / 15 KESİŞİMİ ---
                    if df['wma9'].iloc[idx_dun] <= df['wma15'].iloc[idx_dun] and \
                       df['wma9'].iloc[idx_bugun] > df['wma15'].iloc[idx_bugun]:
                        sinyaller.append(f"🚀 *{name}* - WMA 9/15\n✅ Kısa Vadeli Kesişme ({zaman})\n💰 Fiyat: {df['Close'].iloc[idx_bugun]:.2f}")

                    # --- STRATEJİ 2: EMA 20 / 50 KESİŞİMİ ---
                    if df['ema20'].iloc[idx_dun] <= df['ema50'].iloc[idx_dun] and \
                       df['ema20'].iloc[idx_bugun] > df['ema50'].iloc[idx_bugun]:
                        sinyaller.append(f"🔥 *{name}* - EMA 20/50\n✅ GÜÇLÜ TREND BAŞLANGICI ({zaman})\n💰 Fiyat: {df['Close'].iloc[idx_bugun]:.2f}")

            except:
                continue

        # Telegram Mesaj Gönderme
        if sinyaller:
            # Aynı hisse için birden fazla sinyal varsa (nadir) ayırmak için
            mesaj_metni = "🔔 *MG-HİSSE GÜNLÜK KESİŞME RAPORU*\n\n" + "\n\n".join(sinyaller)
            # Mesaj çok uzunsa böl (Telegram sınırı 4096 karakter)
            if len(mesaj_metni) > 4000:
                t_mesaj(mesaj_metni[:4000])
                t_mesaj(mesaj_metni[4000:])
            else:
                t_mesaj(mesaj_metni)
        else:
            t_mesaj("✅ Tarama bitti. Son 5 günde WMA 9/15 veya EMA 20/50 kesişmesi yapan hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
