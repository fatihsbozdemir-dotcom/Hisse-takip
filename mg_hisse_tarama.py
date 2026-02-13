import pandas as pd
import requests
import pandas_ta as ta
from tvdatafeed import TvDatafeed, Interval
import time

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def analiz():
    try:
        tv = TvDatafeed()
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [str(h).strip() for h in df_sheet.iloc[:, 0].dropna()]
        
        bulunan = []
        
        for hisse in hisseler:
            try:
                # 4 Saatlik veriyi çek
                df = tv.get_hist(symbol=hisse, exchange='BIST', interval=Interval.in_4_hour, n_bars=100)
                
                if df is None or df.empty:
                    continue

                # MG-Hisse V1 Ortalamaları (Ağırlıklı Hareketli Ortalama)
                df['wma9'] = ta.wma(df['close'], length=9)
                df['wma15'] = ta.wma(df['close'], length=15)
                df['wma55'] = ta.wma(df['close'], length=55)
                
                # Son 6 mumda temas kontrolü
                son_6 = df.tail(6)
                fiyat_son = df['close'].iloc[-1]
                
                durum = ""
                for i in range(len(son_6)):
                    f = son_6['close'].iloc[i]
                    w9 = son_6['wma9'].iloc[i]
                    w15 = son_6['wma15'].iloc[i]
                    w55 = son_6['wma55'].iloc[i]
                    
                    # %3 Yakınlık marjı
                    if abs(f - w9) / w9 < 0.03 or abs(f - w15) / w15 < 0.03:
                        durum = "🟢 Yeşil Bölge Temas"
                        break
                    elif abs(f - w55) / w55 < 0.03:
                        durum = "🟡 Sarı Bölge Temas"
                        break
                    elif (max(w9, w15) > f > w55):
                        durum = "🌓 Kanal İçi"
                        break

                if durum:
                    bulunan.append(f"📍 *{hisse}*\n💰 Fiyat: {fiyat_son:.2f}\n📢 {durum}")
                
                time.sleep(0.5) # Banlanmamak için kısa bekleme

            except:
                continue

        if bulunan:
            t_mesaj("🚀 *MG-HİSSE V1 (4S) ANALİZ SONUCU*\n\n" + "\n\n".join(bulunan))
        else:
            t_mesaj("✅ Tarama bitti, kriterlere uyan hisse bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
