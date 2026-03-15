import pandas as pd
import numpy as np
import yfinance as yf
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "8599240314")

SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


def get_symbols():
    df = pd.read_csv(SHEET_URL)
    return df.iloc[:, 0].dropna().tolist()


def wma(series, period):
    weights = np.arange(1, period + 1)
    return series.rolling(period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def clean_index(df):
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


def map_to_4h(data_4h, source_df, col):
    result = pd.Series(index=data_4h.index, dtype=float)
    src = source_df[col].dropna()
    src.index = pd.to_datetime(src.index).tz_localize(None)
    data_4h_index = pd.to_datetime(data_4h.index).tz_localize(None)
    for i, ts in enumerate(data_4h_index):
        past = src[src.index <= ts]
        if len(past) > 0:
            result.iloc[i] = float(past.iloc[-1])
    return result


def get_mtf_levels(symbol):
    data_4h = yf.download(symbol, period="3mo",  interval="4h",  progress=False)
    data_1d = yf.download(symbol, period="1y",   interval="1d",  progress=False)
    data_1w = yf.download(symbol, period="3y",   interval="1wk", progress=False)
    data_1m = yf.download(symbol, period="10y",  interval="1mo", progress=False)

    if len(data_4h) < 10 or len(data_1d) < 15 or len(data_1w) < 15 or len(data_1m) < 9:
        return None, None

    data_4h = clean_index(data_4h)
    data_1d = clean_index(data_1d)
    data_1w = clean_index(data_1w)
    data_1m = clean_index(data_1m)

    for df in [data_1d, data_1w, data_1m]:
        c = df["Close"].squeeze()
        df["wma9"]  = wma(c, 9)
        df["wma15"] = wma(c, 15)

    data_4h["d_wma9"]  = map_to_4h(data_4h, data_1d, "wma9")
    data_4h["d_wma15"] = map_to_4h(data_4h, data_1d, "wma15")
    data_4h["w_wma9"]  = map_to_4h(data_4h, data_1w, "wma9")
    data_4h["w_wma15"] = map_to_4h(data_4h, data_1w, "wma15")
    data_4h["m_wma9"]  = map_to_4h(data_4h, data_1m, "wma9")
    data_4h["m_wma15"] = map_to_4h(data_4h, data_1m, "wma15")

    mtf = {
        "d_wma9":  float(data_4h["d_wma9"].iloc[-1]),
        "d_wma15": float(data_4h["d_wma15"].iloc[-1]),
        "w_wma9":  float(data_4h["w_wma9"].iloc[-1]),
        "w_wma15": float(data_4h["w_wma15"].iloc[-1]),
        "m_wma9":  float(data_4h["m_wma9"].iloc[-1]),
        "m_wma15": float(data_4h["m_wma15"].iloc[-1]),
    }
    return data_4h, mtf


def analyze(symbol):
    data_4h, mtf = get_mtf_levels(symbol)
    if data_4h is None:
        return False, None, {}

    last = float(data_4h["Close"].squeeze().iloc[-1])

    # Haftalik WMA9 (yesil) her zaman WMA15 (sari) den buyuk olmayabilir
    # Hangisi buyuk hangisi kucuk olursa olsun dogru hesapla
    w9  = mtf["w_wma9"]   # Yesil - Haftalik WMA9
    w15 = mtf["w_wma15"]  # Sari  - Haftalik WMA15

    w_ust = max(w9, w15)  # iki haftalik WMA'nin buyugu
    w_alt = min(w9, w15)  # iki haftalik WMA'nin kucugu

    # DURUM 1: Fiyat haftalik WMA9 ve WMA15 ARASINDA
    # Kesinlikle: w_alt <= fiyat <= w_ust
    arasinda = w_alt <= last <= w_ust

    # DURUM 2: Fiyat haftalik WMA9'a temas (ustunden)
    # Fiyat kesinlikle w_ust'un uzerinde olmali
    # Ve w_ust'a %1.5'ten yakin olmali
    temas_w9 = (
        last > w_ust and
        abs(last - w9) / last < 0.015
    )

    # DURUM 3: Fiyat haftalik WMA15'e temas (ustunden)
    # Fiyat kesinlikle w15'in uzerinde olmali
    # Ve w15'e %1.5'ten yakin olmali
    # Ama w9'un da uzerinde olmali
    temas_w15 = (
        last > w_ust and
        abs(last - w15) / last < 0.015
    )

    signal = arasinda or temas_w9 or temas_w15

    if not signal:
        return False, None, {}

    if arasinda:
        sinyal_tipi = "Haftalik WMA9 - WMA15 Arasinda"
    elif temas_w9:
        sinyal_tipi = "Haftalik WMA9 Temas"
