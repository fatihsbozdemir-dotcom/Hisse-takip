
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
        
        # En sağlıklı EMA için 'max' periyot çekiyoruz
        data = yf.download(hisseler, period="2y", interval="1d", group_by='ticker', threads=True)
        
        bulunanlar = []

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 50: continue 

                # EMA Hesaplama (TradingView Birebir)
                df['ema20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['ema50'] = df['Close'].ewm(span=50, adjust=False).mean()

                # SON 5 GÜNÜN VERİLERİ
                son_gunler = df.tail(5)
                
                # KRİTER: EMA 20, EMA 50'nin üzerine çıkmış MI veya ÇIKMAK ÜZERE Mİ?
                e20 = son_gunler['ema20'].iloc[-1]
                e50 = son_gunler['ema50'].iloc[-1]
                
                # 1. Senaryo: Zaten üstünde ve fark çok küçük (%0.5) - Yeni Kesişmiş
                # 2. Senaryo: Altında ama fark binde 2 - Kesişmek üzere
                fark = (e20 - e50) / e50
                
                if abs(fark) < 0.005: # %0.5'lik devasa esneklik
                    status = "🔥 KESİŞME BÖLGESİNDE" if fark < 0 else "🚀 YENİ KESİŞTİ"
                    bulunanlar.append(f"📍 *{ticker.replace('.IS','')}*\n📢 Durum: {status}\n💰 Fiyat: {son_gunler['Close'].iloc[-1]:.2f}\n🎯 Fark: %{fark*100:.2f}")

            except: continue

        if bulunanlar:
            t_mesaj("📢 *MG-HİSSE ESNEK TARAMA SONUÇLARI*\n\n" + "\n\n".join(bulunanlar))
        else:
            t_mesaj("🔍 Listenizdeki hisselerde (Son 5 gün) EMA 20/50 yakınlaşması bulunamadı.\n\n*Not:* TradingView'da çıkan hisseler muhtemelen sizin Google Sheet listenizde olmayan hisselerdir.")
            
    except Exception as e:
        t_mesaj(f"❌ Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
