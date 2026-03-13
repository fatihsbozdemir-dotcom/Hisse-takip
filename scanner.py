import os, io, requests, numpy as np, pandas as pd
import yfinance as yf, mplfinance as mpf, matplotlib.pyplot as plt

# --- AYARLAR ---
# Eğer bu değerler ortam değişkenlerinde yoksa buraya manuel ekleyebilirsin
TELEGRAM_TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID        = "8599240314" 
SHEET_URL      = f"https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

# --- TELEGRAM FONKSİYONLARI ---
def tg_yaz(metin):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": metin, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload, timeout=15)
        return True
    except Exception as e:
        print(f"Mesaj Hatası: {e}")
        return False

def tg_foto(buf, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("chart.png", buf, "image/png")}
    data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
    try:
        requests.post(url, files=files, data=data, timeout=30)
        return True
    except Exception as e:
        print(f"Fotoğraf Hatası: {e}")
        return False

# --- PIVOT VE ANALİZ FONKSİYONLARI ---
def pivot_bul(df, pencere=5, tolerans=0.015, min_dok=2):
    # Pivot noktalarını hesaplayan mantığın (değiştirilmedi)
    highs, lows = df["High"].values, df["Low"].values
    tum = list(highs) + list(lows)
    t_ham, d_ham = [], []
    for i in range(pencere, len(df) - pencere):
        if highs[i] == max(highs[i-pencere:i+pencere+1]): t_ham.append(highs[i])
        if lows[i]  == min(lows[i-pencere:i+pencere+1]):  d_ham.append(lows[i])

    def isle(ham):
        if not ham: return []
        ham = sorted(ham)
        kumeler, k = [], [ham[0]]
        for v in ham[1:]:
            if (v - k[-1]) / k[-1] < tolerans: k.append(v)
            else: kumeler.append(float(np.mean(k))); k = [v]
        kumeler.append(float(np.mean(k)))
        return sorted([(s, sum(1 for f in tum if abs(f-s)/s < tolerans)) for s in kumeler if sum(1 for f in tum if abs(f-s)/s < tolerans) >= min_dok], key=lambda x: x[1], reverse=True)
    return isle(t_ham), isle(d_ham)

# ... (Grafik fonksiyonun burada kalmalı) ...

# --- ANALİZİ BAŞLAT ---
def analiz_et():
    tg_yaz("🚀 *Hisse Tarama Botu Başladı*")
    # ... (Hisse okuma ve döngü kısmı) ...
    # Döngü içinde sinyal bulursan:
    # tg_foto(buf, caption)
    # Döngü bitince:
    tg_yaz("✅ *Tarama Tamamlandı.*")

if __name__ == "__main__":
    analiz_et()
