import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        # Liste boşsa veya yanlışsa hata verir, kontrol edelim
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # Daha fazla veri (1 yıl) çekiyoruz ki EMA50 tam otursun
        data = yf.download(hisseler, period="1y", interval="1d", group_by='ticker', threads=True)
        
        bulunanlar = []

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 60: continue 

                # TradingView ile birebir aynı EMA hesaplama (adjust=False kritik)
                df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()

                # Sadece son 7 satıra (yaklaşık son 5-6 iş günü) bakıyoruz
                son_dilim = df.tail(7) 
                
                for i in range(1, len(son_dilim)):
                    # dun ve bugun
                    idx_bugun = i
                    idx_dun = i - 1
                    
                    ema20_dun = son_dilim['ema20'].iloc[idx_dun]
                    ema50_dun = son_dilim['ema50'].iloc[idx_dun]
                    ema20_bugun = son_dilim['ema20'].iloc[idx_bugun]
                    ema50_bugun = son_dilim['ema50'].iloc[idx_bugun]

                    # KESİŞME ŞARTI: Dün altındaydı, bugün üstünde.
                    if ema20_dun <= ema50_dun and ema20_bugun > ema50_bugun:
                        tarih = son_dilim.index[idx_bugun].strftime('%d.%m')
                        bulunanlar.append(f"🔥 *{ticker.replace('.IS','')}*\n✅ EMA 20/50 Kesişti ({tarih})\n💰 Fiyat: {son_dilim['Close'].iloc[idx_bugun]:.2f}")
                        break
            except:
                continue

        if bulunanlar:
            t_mesaj("📢 *TRADINGVIEW TARZI TARAMA SONUÇLARI*\n\n" + "\n\n".join(bulunanlar))
        else:
            # Eğer hiç bulamazsa listedeki ilk 3 hissenin EMA değerlerini at ki botun çalıştığını görelim
            test_hisseler = hisseler[:3]
            test_msg = "⚠️ Kesişme yok. Örnek değerler:\n"
            for t in test_hisseler:
                try:
                    c = data[t]['Close'].iloc[-1]
                    e20 = data[t]['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
                    e50 = data[t]['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
                    test_msg += f"{t.replace('.IS','')}: Fiyat:{c:.2f} E20:{e20:.2f} E50:{e50:.2f}\n"
                except: pass
            t_mesaj(test_msg)
            
    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
