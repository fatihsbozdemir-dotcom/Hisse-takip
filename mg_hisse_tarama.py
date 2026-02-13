import pandas as pd
import requests
from tvdatafeed import TvDatafeed, Interval

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

def calculate_wma(df, column, length):
    """Saf Python ile Ağırlıklı Hareketli Ortalama (WMA) Hesabı"""
    weights = list(range(1, length + 1))
    return df[column].rolling(window=length).apply(lambda x: (x * weights).sum() / sum(weights), raw=True)

def analiz():
    try:
        tv = TvDatafeed()
        
        # Google Sheet'ten listeyi çek
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [str(h).strip() for h in df_sheet.iloc[:, 0].dropna()]
        
        bulunan = []
        
        for hisse in hisseler:
            try:
                # 4 Saatlik veriyi TradingView'dan çek
                df = tv.get_hist(symbol=hisse, exchange='BIST', interval=Interval.in_4_hour, n_bars=100)
                
                if df is None or df.empty:
                    continue

                # Sütun isimlerini küçük harfe çevirelim (Uyum için)
                df.columns = [c.lower() for c in df.columns]

                # WMA Ortalamalarını Hesapla
                df['wma9'] = calculate_wma(df, 'close', 9)
                df['wma15'] = calculate_wma(df, 'close', 15)
                df['wma55'] = calculate_wma(df, 'close', 55)
                
                # Son 6 mumda (24 saat) temas veya bölge kontrolü
                son_6 = df.tail(6)
                fiyat_son = df['close'].iloc[-1]
                
                durum = ""
                for i in range(len(son_6)):
                    f = son_6['close'].iloc[i]
                    w9 = son_6['wma9'].iloc[i]
                    w15 = son_6['wma15'].iloc[i]
                    w55 = son_6['wma55'].iloc[i]
                    
                    # %3'lük hassasiyet marjı
                    if abs(f - w9) / w9 < 0.03 or abs(f - w15) / w15 < 0.03:
                        durum = "🟢 Yeşil Bölge (WMA 9-15) Temas"
                        break
                    elif abs(f - w55) / w55 < 0.03:
                        durum = "🟡 Sarı Bölge (WMA 55) Temas"
                        break
                    elif (max(w9, w15) > f > w55):
                        durum = "🌓 Yeşil-Sarı Arası Kanalda"
                        break

                if durum:
                    bulunan.append(f"📍 *{hisse}*\n💰 Fiyat: {fiyat_son:.2f}\n📢 {durum}")

            except:
                continue

        if bulunan:
            t_mesaj("🚀 *MG-HİSSE V1 (4S) TARAMA*\n\n" + "\n\n".join(bulunan))
        else:
            t_mesaj("✅ Tarama bitti, uygun hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ Kritik Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
