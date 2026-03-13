import os, io, requests, numpy as np, pandas as pd
import yfinance as yf, mplfinance as mpf, matplotlib.pyplot as plt

# --- AYARLAR ---
TELEGRAM_TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID        = "8599240314"
SHEET_URL      = "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv"

# --- TELEGRAM FONKSİYONLARI ---
def tg_yaz(metin):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": metin, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def tg_foto(buf, caption):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                      files={"photo": ("chart.png", buf, "image/png")},
                      data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "Markdown"}, timeout=30)
    except: pass

# --- ANALİZ MANTIĞI ---
def pivot_bul(df, pencere=10, tolerans=0.03, min_dok=2):
    highs, lows = df["High"].values, df["Low"].values
    t_ham, d_ham = [], []
    for i in range(pencere, len(df) - pencere):
        if highs[i] == max(highs[i-pencere:i+pencere+1]): t_ham.append(highs[i])
        if lows[i]  == min(lows[i-pencere:i+pencere+1]):  d_ham.append(lows[i])

    def kumeler(ham):
        if not ham: return []
        ham = sorted(ham)
        res, k = [], [ham[0]]
        for v in ham[1:]:
            if (v - k[-1]) / k[-1] < tolerans: k.append(v)
            else: res.append((np.mean(k), len(k))); k = [v]
        res.append((np.mean(
