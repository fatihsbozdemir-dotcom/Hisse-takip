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
    print(f"[MESAJ]: {text}")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    })
    print(f"[YANIT]: {r.status_code} - {r.text}")


def get_symbols():
    df = pd.read_csv(SHEET_URL)
    symbols = df.iloc[:, 0].dropna().tolist()
    print(f"[SEMBOLLER]: {symbols}")
    return symbols


def analyze(symbol):
    data = yf.download(symbol, period="3mo", interval="1d", progress=False)
    if len(data) < 20:
        return False, data, {}

    last = data.tail(20).copy()
    close = last["Close"].squeeze()
    high = last["High"].squeeze()
    low = last["Low"].squeeze()

    mean_price = float(close.mean())
    std_price = float(close.std())
    std_ratio = std_price / mean_price

    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = float(tr.mean())
    atr_ratio = atr / mean_price

    bb_std = float(close.rolling(20).std().iloc[-1])
    bb_width = (bb_std * 2) / mean_price

    y = close.values.astype(float)
    x = np.arange(len(y))
    slope = float(np.polyfit(x, y, 1)[0])
    slope_pct = abs(slope) / mean_price

    is_sideways = (
        std_ratio < 0.025 and
        atr_ratio < 0.025 and
        bb_width < 0.06 and
        slope_pct < 0.002
    )

    stats = {
        "fiyat": round(mean_price, 2),
        "destek": round(float(low.min()), 2),
        "direnc": round(float(high.max()), 2),
        "std": round(std_ratio * 100, 2),
        "atr": round(atr_ratio * 100, 2),
        "bb_width": round(bb_width * 100, 2),
    }
    return is_sideways, data, stats


def send_chart(symbol, data, stats):
    last = data.tail(40).copy().reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    for i, row in last.iterrows():
        o = float(row["Open"].squeeze())
        c = float(row["Close"].squeeze())
        h = float(row["High"].squeeze())
        l = float(row["Low"].squeeze())
        color = "#26a69a" if c >= o else "#ef5350"
        bottom = min(o, c)
        height = abs(c - o) or (h - l) * 0.01
        ax.bar(i, height, bottom=bottom, color=color, width=0.7, linewidth=0)
        ax.plot([i, i], [l, h], color=color, linewidth=0.8)

    ax.axhline(stats["destek"], color="#ff9800", linewidth=1.2,
               linestyle="--", alpha=0.8, label=f"Destek: {stats['destek']}")
    ax.axhline(stats["direnc"], color="#42a5f5", linewidth=1.2,
               linestyle="--", alpha=0.8, label=f"Direnc: {stats['direnc']}")

    ax.set_title(f"{symbol} - Yatay Konsolidasyon", color="white", fontsize=13)
    ax.tick_params(colors="#888888")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")
    ax.legend(facecolor="#1e1e2e", edgecolor="#333", labelcolor="white", fontsize=9)
    plt.tight_layout()

    fname = f"{symbol.replace('.', '_')}.png"
    plt.savefig(fname, dpi=130, bbox_inches="tight")
    plt.close()

    caption = (
        f"<b>{symbol}</b> - Yatay Aday\n"
        f"Fiyat: {stats['fiyat']}\n"
        f"Destek: {stats['destek']} | Direnc: {stats['direnc']}\n"
        f"Std: %{stats['std']} | ATR: %{stats['atr']}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(fname, "rb") as f:
        r = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f}
        )
    print(f"[GRAFIK]: {symbol} - {r.status_code}")


def run():
    print(f"[TOKEN]: {TELEGRAM_TOKEN[:15]}...")
    print(f"[CHAT_ID]: {CHAT_ID}")

    send_message("Tarama basladi")

    symbols = get_symbols()

    if not symbols:
        send_message("HATA: Hisse listesi bos!")
        return

    send_message(f"{len(symbols)} hisse kontrol ediliyor...")

    found = 0
    for s in symbols:
        try:
            print(f"[ANALIZ]: {s}")
            signal, data, stats = analyze(s)
            if signal:
                found += 1
                send_chart(s, data, stats)
        except Exception as e:
            print(f"[HATA] {s}: {e}")

    if found == 0:
        send_message("Tarama tamamlandi - yatay hisse bulunamadi")
    else:
        send_message(f"Tarama tamamlandi - {found} yatay hisse bulundu!")


run()
