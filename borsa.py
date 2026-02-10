import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# Takip edilecek hisseler
hisseler = ["THYAO.IS", "ASELS.IS", "EREGL.IS", "SISE.IS"]

def fiyat_kaydet():
    veriler = yf.download(hisseler, period="1d", interval="1m")['Close'].iloc[-1]
    df_yeni = pd.DataFrame(veriler).T
    df_yeni.insert(0, 'Zaman', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    dosya_adi = 'fiyat_gecmisi.csv'
    if not os.path.isfile(dosya_adi):
        df_yeni.to_csv(dosya_adi, index=False)
    else:
        df_yeni.to_csv(dosya_adi, mode='a', header=False, index=False)
    print("Veri kaydedildi.")

if __name__ == "__main__":
    fiyat_kaydet()
