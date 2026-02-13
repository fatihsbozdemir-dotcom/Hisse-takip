import yfinance as yf
import pandas as pd
import requests

TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def wma(series, period):
    # TradingView uyumlu WMA hesaplaması
    weights = list(range(1, period + 1))
    return series.rolling(period).apply(lambda x: (weights * x).sum() / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # Daha fazla veri çekiyoruz ki WMA sağlıklı hesaplansın
        data = yf.download(hisseler, period="3mo", interval="4h", group_by='ticker', threads=False)
        
        bulunan = []
        yakindakiler = [] # Temas olmasa da çok yaklaşanlar için

        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 60: continue 
                
                # Ortalamalar
                df['wma9'] = wma(df['Close'], 9)
                df['wma15'] = wma(df['Close'], 15)
                df['wma55'] = wma(df['Close'], 55)
                
                son_6 = df.tail(6)
                fiyat_simdi = df['Close'].iloc[-1]
                
                en_dusuk_fark = 100
                durum = ""

                for i in range(len(son_6)):
                    f = son_6['Close'].iloc[i]
                    w9 = son_6['wma9'].iloc[i]
                    w15 = son_6['wma15'].iloc[i]
                    w55 = son_6['wma55'].iloc[i]
                    
                    # Farkları hesapla
                    fark_w9 = abs(f - w9) / w9
                    fark_w15 = abs(f - w15) / w15
                    fark_w55 = abs(f - w55) / w55
                    
                    min_fark = min(fark_w9, fark_w15, fark_w55)
                    if min_fark < en_dusuk_fark: en_dusuk_fark = min_fark

                    # KRİTERLERİ ESNETİYORUZ (%5 Hassasiyet)
                    if fark_w9 < 0.05 or fark_w15 < 0.05:
                        durum = "🟢 Yeşil Bölge (WMA 9/15)"
                    elif fark_w55 < 0.05:
                        durum = "🟡 Sarı Bölge (WMA 55)"
                    elif (max(w9, w15) > f > w55):
                        durum = "🌓 Kanal İçi"

                if durum:
                    bulunan.append(f"📍 *{ticker.replace('.IS','')}*\n💰 Fiyat: {fiyat_simdi:.2f}\n📢 {durum}\n🎯 Fark: %{en_dusuk_fark*100:.1f}")
                else:
                    # Hiçbir şey bulamazsa en azından %10 yakındaki en iyi adayı listeye ekle
                    if en_dusuk_fark < 0.10:
                        yakindakiler.append(f"{ticker.replace('.IS','')}(%{en_dusuk_fark*100:.1f})")

            except:
                continue

        if bulunan:
            t_mesaj("🕒 *MG-HİSSE V1: SON 6 MUM ANALİZİ*\n\n" + "\n\n".join(bulunan))
        elif yakindakiler:
            t_mesaj(f"ℹ️ Tam temas yok ama yaklaşanlar:\n{', '.join(yakindakiler)}")
        else:
            t_mesaj("❌ Veri çekildi ama kriterlere veya yakınına uygun hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ MG-Hisse Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
