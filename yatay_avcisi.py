import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import requests

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "-1003838602845"
SHEET_URL = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

# ---------------------------------------------------------------
# PIVOT DESTEK / D\u0130REN\u00c7 BULMA
# Grafikteki gibi: fiyat\u0131n birden fazla kez d\u00f6nd\u00fc\u011f\u00fc seviyeleri bul
# ---------------------------------------------------------------
def pivot_noktalari_bul(df, pencere=5, min_dokunma=2, tolerans_pct=0.015):
    """
    Ger\u00e7ek pivot high/low noktalar\u0131n\u0131 bulur.
    - pencere: ka\u00e7 mumdaki en y\u00fcksek/d\u00fc\u015f\u00fck oldu\u011funu kontrol eder
    - min_dokunma: bir seviyenin ge\u00e7erli say\u0131lmas\u0131 i\u00e7in ka\u00e7 kez test edilmeli
    - tolerans_pct: iki seviyenin ayn\u0131 b\u00f6lge say\u0131lmas\u0131 i\u00e7in yak\u0131nl\u0131k y\u00fczdesi
    """
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values

    # Pivot tepe ve dipleri bul
    pivot_tepeler = []
    pivot_dipler = []

    for i in range(pencere, len(df) - pencere):
        # Pivot tepe: penceredeki en y\u00fcksek nokta
        if highs[i] == max(highs[i - pencere:i + pencere + 1]):
            pivot_tepeler.append(highs[i])
        # Pivot dip: penceredeki en d\u00fc\u015f\u00fck nokta
        if lows[i] == min(lows[i - pencere:i + pencere + 1]):
            pivot_dipler.append(lows[i])

    # Yak\u0131n seviyeleri birle\u015ftir (k\u00fcmeleme)
    def kumelere_ayir(levels, tolerans_pct):
        if not levels:
            return []
        levels = sorted(levels)
        kumeler = []
        mevcut_kume = [levels[0]]

        for level in levels[1:]:
            if (level - mevcut_kume[-1]) / mevcut_kume[-1] < tolerans_pct:
                mevcut_kume.append(level)
            else:
                kumeler.append(np.mean(mevcut_kume))
                mevcut_kume = [level]
        kumeler.append(np.mean(mevcut_kume))
        return kumeler

    # K\u00fcmeleme ve dokunma say\u0131s\u0131 filtresi
    def guclu_seviyeler_bul(pivot_list, tum_fiyatlar, tolerans_pct, min_dokunma):
        kumeler = kumelere_ayir(pivot_list, tolerans_pct)
        guclu = []
        for seviye in kumeler:
            # Bu seviyeye ka\u00e7 kez dokunulmu\u015f?
            dokunma = sum(1 for f in tum_fiyatlar if abs(f - seviye) / seviye < tolerans_pct)
            if dokunma >= min_dokunma:
                guclu.append((seviye, dokunma))
        # G\u00fcce g\u00f6re s\u0131rala
        return sorted(guclu, key=lambda x: x[1], reverse=True)

    tum_fiyatlar = list(highs) + list(lows)
