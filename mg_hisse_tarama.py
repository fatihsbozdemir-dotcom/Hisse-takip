import yfinance as yf
import pandas as pd
import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def wma(series, period):
    weights = list(range(1, period + 1))
    return series.rolling(period).apply(lambda x: (weights * x).sum() / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # 1 SAATLİK veri çekiyoruz (4 saatlik Yahoo'da yok)
        data = yf.download(hisseler, period="2mo", interval="1h", group_by='ticker', threads=False)
        
        bulunan = []

        for ticker in hisseler:
            try:
                df_1h = data[ticker].dropna()
                if df_1h.empty: continue
                
                # --- 1 SAATLİĞİ 4 SAATLİĞE ÇEVİRME ---
                logic = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
                df = df_1h.resample('4H').apply(logic).dropna()
                
                if len(df) < 60: continue 

                # Ortalamalar
                df['wma9'] = wma(df['Close'], 9)
                df['wma15'] = wma(df['Close'], 15)
                df['wma55'] = wma(df['Close'], 55)
                
                son_6 = df.tail(6)
                fiyat_simdi = df['Close'].iloc[-1]
                
                durum = ""
                min_fark = 100

                for i in range(len(son_6)):
                    f = son_6['Close'].iloc[i]
                    w9 = son_6['wma9'].iloc[i]
                    w15 = son_6['wma15'].iloc[i]
                    w55 = son_6['wma55'].iloc[i]
                    
                    fark = min(abs(f-w9)/w9, abs(f-w15)/w15, abs(f-w55)/w55)
                    if fark < min_fark: min_fark = fark

                    if abs(f-w9)/w9 < 0.04 or abs(f-w15)/w15 < 0.04:
                        durum = "🟢 Yeşil Bölge (WMA 9/15)"
                    elif abs(f-w55)/w55 < 0.04:
                        durum = "🟡 Sarı Bölge (WMA 55)"
                    elif (max(w9, w15) > f > w55):
                        durum = "🌓 Kanal İçi"

                if durum:
                    bulunan.append(f"📍 *{ticker.replace('.IS','')}*\n💰 Fiyat: {fiyat_simdi:.2f}\n📢 {durum}\n🎯 Fark: %{min_fark*100:.1f}")

            except Exception as e:
                continue

        if bulunan:
            t_mesaj("🕒 *MG-HİSSE V1: 4 SAATLİK ANALİZ (1H'den Çevrildi)*\n\n" + "\n\n".join(bulunan))
        else:
            t_mesaj("✅ 4 Saatlik periyotta kriterlere uygun hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ MG-Hisse Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
