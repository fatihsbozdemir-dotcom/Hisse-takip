import yfinance as yf
import pandas as pd
import requests

# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def wma(data, period):
    weights = list(range(1, period + 1))
    return data.rolling(period).apply(lambda x: sum(weights * x) / sum(weights), raw=True)

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = [f"{str(h).strip()}.IS" for h in df_sheet.iloc[:, 0].dropna()]
        
        # 4 saatlik veri çekme
        data = yf.download(hisseler, period="1mo", interval="4h", group_by='ticker', threads=False)
        
        bulunan = []
        for ticker in hisseler:
            try:
                df = data[ticker].dropna()
                if len(df) < 60: continue 
                
                # Ortalamaları hesapla
                df['wma9'] = wma(df['Close'], 9)
                df['wma15'] = wma(df['Close'], 15)
                df['wma55'] = wma(df['Close'], 55)
                
                # --- SON 6 MUMU KONTROL ET ---
                # Son 6 periyodu (24 saat) alıyoruz
                son_6_mum = df.tail(6)
                fiyat_simdi = df['Close'].iloc[-1]
                
                temas_yesil = False
                temas_sari = False
                kanal_ici = False
                
                for i in range(len(son_6_mum)):
                    fiyat = son_6_mum['Close'].iloc[i]
                    w9 = son_6_mum['wma9'].iloc[i]
                    w15 = son_6_mum['wma15'].iloc[i]
                    w55 = son_6_mum['wma55'].iloc[i]
                    
                    # Yeşil Bölge Temas Kontrolü (%3 Hassasiyet)
                    if abs(fiyat - w9) / w9 < 0.03 or abs(fiyat - w15) / w15 < 0.03:
                        temas_yesil = True
                    
                    # Sarı Bölge Temas Kontrolü
                    if abs(fiyat - w55) / w55 < 0.03:
                        temas_sari = True
                        
                    # Kanal İçi Kontrolü
                    if (max(w9, w15) > fiyat > w55):
                        kanal_ici = True

                # Durum Belirleme (Öncelik sırasına göre)
                durum = ""
                if temas_yesil:
                    durum = "🟢 4S Yeşil Bölge (Son 6 Mumda Temas Var)"
                elif temas_sari:
                    durum = "🟡 4S Sarı Bölge (Son 6 Mumda Temas Var)"
                elif kanal_ici:
                    durum = "🌓 4S Kanal İçi (Son 6 Mumda Sıkışma)"

                if durum:
                    bulunan.append(f"📍 *{ticker.replace('.IS','')}*\n💰 Fiyat: {fiyat_simdi:.2f}\n📢 {durum}")
            except:
                continue

        if bulunan:
            t_mesaj("🕒 *MG-HİSSE V1: 6 MUMLUK (24S) ANALİZ*\n\n" + "\n\n".join(bulunan))
        else:
            t_mesaj("✅ Son 6 mumda kriterlere uygun bir temas bulunamadı.")
            
    except Exception as e:
        t_mesaj(f"❌ MG-Hisse Hata: {str(e)}")

if __name__ == "__main__":
    analiz()
