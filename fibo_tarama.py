import time # En üste ekle

# ... (diğer kodlar aynı)

        for hisse in hisseler:
            t_name = f"{str(hisse).strip()}.IS"
            time.sleep(1.5) # Her hisse arasında 1.5 saniye bekle
            df = yf.Ticker(t_name).history(period="3y")
# ...


# --- AYARLAR ---
TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

def t_mesaj(mesaj):
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={'chat_id': CHAT_ID, 'text': mesaj, 'parse_mode': 'Markdown'})

def analiz():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = df_sheet.iloc[:, 0].dropna()
        bulunan = []
        
        for hisse in hisseler:
            t_name = f"{str(hisse).strip()}.IS"
            # Hem Günlük hem Haftalık veri için geniş bir aralık çekiyoruz
            hist = yf.Ticker(t_name).history(period="2y")
            if len(hist) < 144: continue
            
            # GÜNLÜK TEMAS KONTROLÜ
            fiyat = hist['Close'].iloc[-1]
            for n in [55, 89, 144]:
                sma = hist['Close'].rolling(window=n).mean().iloc[-1]
                if abs(fiyat - sma) / sma < 0.015: # %1.5 yakınlık
                    bulunan.append(f"📅 *{hisse}* (Günlük) -> EMA {n} Teması")

            # HAFTALIK TEMAS KONTROLÜ
            w_hist = hist['Close'].resample('W').last()
            if len(w_hist) > 144:
                w_fiyat = w_hist.iloc[-1]
                for n in [55, 89, 144]:
                    w_sma = w_hist.rolling(window=n).mean().iloc[-1]
                    if abs(w_fiyat - w_sma) / w_sma < 0.02: # %2 yakınlık
                        bulunan.append(f"🌟 *{hisse}* (Haftalık) -> EMA {n} Teması")

        if bulunan:
            t_mesaj("🚀 *FİBONACCİ ORTALAMA TEMASLARI*\n\n" + "\n".join(set(bulunan)))
        else:
            t_mesaj("✅ Bugün Fibonacci ortalamalarına temas eden hisse yok.")
            
    except Exception as e:
        t_mesaj(f"❌ Tarama Hatası: {str(e)}")

if __name__ == "__main__":
    analiz()
