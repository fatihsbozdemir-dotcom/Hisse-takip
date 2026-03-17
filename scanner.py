import pandas as pd
import numpy as np
import yfinance as yf
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc")
CHAT_ID = "-1003838602845"
THREAD_ID = 1770

SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


def send_message(text):
    print(f"[MESAJ]: {text}")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "message_thread_id": THREAD_ID
    })
    print(f"[YANIT]: {r.status_code} - {r.text}")


def get_symbols():
    df = pd.read_csv(SHEET_URL)
    symbols = df.iloc[:, 0].dropna().tolist()
    print(f"[SEMBOLLER]: {symbols}")
    return symbols


def analyze(symbol):
    data = yf.download(symbol, period="1mo", interval="1d", progress=False)
    if len(data) < 10:
        return False, data, {}

    last = data.tail(10).copy()
    close = last["Close"].squeeze()
    high  = last["High"].squeeze()
    low   = last["Low"].squeeze()

    mean_price = float(close.mean())
    std_ratio  = float(close.std()) / mean_price

    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs()
    ], axis=1).max(axis=1)
    atr_ratio = float(tr.mean()) / mean_price

    is_sideways = (
        std_ratio < 0.05 and
        atr_ratio < 0.05
    )

    full_close = data["Close"].squeeze()
    ma5  = float(full_close.rolling(5).mean().iloc[-1])
    ma10 = float(full_close.rolling(10).mean().iloc[-1])
    ma20 = float(full_close.rolling(20).mean().iloc[-1]) if len(full_close) >= 20 else None
    last_close = float(full_close.iloc[-1])

    temas = []
    for ma_val, ma_name in [(ma5, "MA5"), (ma10, "MA10"), (ma20, "MA20")]:
        if ma_val is not None and abs(last_close - ma_val) / last_close < 0.01:
            temas.append(ma_name)

    stats = {
        "fiyat":      round(mean_price, 2),
        "destek":     round(float(low.min()), 2),
        "direnc":     round(float(high.max()), 2),
        "std":        round(std_ratio * 100, 2),
        "atr":        round(atr_ratio * 100, 2),
        "ma5":        round(ma5, 2),
        "ma10":       round(ma10, 2),
        "ma20":       round(ma20, 2) if ma20 else None,
        "temas":      temas,
        "last_close": round(last_close, 2),
    }
    return is_sideways, data, stats


def send_chart(symbol, data, stats):
    plot_data = data.tail(40).copy().reset_index()
    dates     = pd.to_datetime(plot_data["Date"])
    x_pos     = np.arange(len(plot_data))

    full_close = plot_data["Close"].squeeze()
    ma5_line   = full_close.rolling(5).mean()
    ma10_line  = full_close.rolling(10).mean()
    ma20_line  = full_close.rolling(20).mean()

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True
    )
    fig.patch.set_facecolor("#0f1117")
    ax1.set_facecolor("#0f1117")
    ax2.set_facecolor("#0f1117")
    fig.subplots_adjust(hspace=0.05)

    for i, row in plot_data.iterrows():
        o = float(row["Open"].squeeze())
        c = float(row["Close"].squeeze())
        h = float(row["High"].squeeze())
        l = float(row["Low"].squeeze())
        color  = "#26a69a" if c >= o else "#ef5350"
        bottom = min(o, c)
        height = abs(c - o) or (h - l) * 0.01
        ax1.bar(i, height, bottom=bottom, color=color, width=0.7, linewidth=0)
        ax1.plot([i, i], [l, h], color=color, linewidth=0.8)

    ax1.plot(x_pos, ma5_line,  color="#f5c518", linewidth=1.2, label=f"MA5: {stats['ma5']}")
    ax1.plot(x_pos, ma10_line, color="#1e90ff", linewidth=1.2, label=f"MA10: {stats['ma10']}")
    if stats["ma20"]:
        ax1.plot(x_pos, ma20_line, color="#ff69b4", linewidth=1.2, label=f"MA20: {stats['ma20']}")

    ax1.axhline(stats["destek"], color="#ff9800", linewidth=1.2,
                linestyle="--", alpha=0.8, label=f"Destek: {stats['destek']}")
    ax1.axhline(stats["direnc"], color="#42a5f5", linewidth=1.2,
                linestyle="--", alpha=0.8, label=f"Direnc: {stats['direnc']}")

    if stats["temas"]:
        temas_str = " & ".join(stats["temas"])
        ax1.annotate(
            f"{temas_str} temasinda",
            xy=(len(plot_data)-1, stats["last_close"]),
            xytext=(-100, 15),
            textcoords="offset points",
            color="#ffdd57", fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#ffdd57", lw=1.2)
        )

    ax1.set_title(
        f"{symbol}  |  Yatay Konsolidasyon  |  {stats['last_close']}",
        color="white", fontsize=13, pad=10
    )
    ax1.tick_params(colors="#888888")
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#333333")
    ax1.legend(facecolor="#1e1e2e", edgecolor="#333",
               labelcolor="white", fontsize=9, loc="upper left")

    for i, row in plot_data.iterrows():
        c   = float(row["Close"].squeeze())
        o   = float(row["Open"].squeeze())
        vol = float(row["Volume"].squeeze())
        color = "#26a69a" if c >= o else "#ef5350"
        ax2.bar(i, vol, color=color, width=0.6, alpha=0.8, linewidth=0)

    ax2.set_ylabel("Hacim", color="#888888", fontsize=8)
    ax2.tick_params(colors="#888888", labelsize=7)
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#333333")

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(
        [d.strftime("%d/%m") for d in dates],
        rotation=45, ha="right", color="#888888", fontsize=7
    )

    plt.tight_layout()
    fname = f"{symbol.replace('.', '_')}.png"
    plt.savefig(fname, dpi=130, bbox_inches="tight")
    plt.close()

    temas_text = ", ".join(stats["temas"]) if stats["temas"] else "Temas yok"

    caption = (
        f"<b>{symbol}</b> - Yatay Aday\n"
        f"Fiyat: {stats['last_close']}\n"
        f"Destek: {stats['destek']} | Direnc: {stats['direnc']}\n"
        f"MA5: {stats['ma5']} | MA10: {stats['ma10']} | MA20: {stats['ma20']}\n"
        f"MA Temas: {temas_text}\n"
        f"Std: %{stats['std']} | ATR: %{stats['atr']}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(fname, "rb") as f:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML",
                "message_thread_id": THREAD_ID
            },
            files={"photo": f}
        )
    print(f"[GRAFIK]: {symbol}")


def run():
    print(f"[TOKEN]: {TELEGRAM_TOKEN[:15]}...")
    print(f"[CHAT_ID]: {CHAT_ID}")

    send_message("Yatay Tarama basladi")
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
