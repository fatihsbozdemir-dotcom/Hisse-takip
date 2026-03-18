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
THREAD_ID = 2643

SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "message_thread_id": THREAD_ID
    })


def get_symbols():
    df = pd.read_csv(SHEET_URL)
    return df.iloc[:, 0].dropna().tolist()


def analyze(symbol):
    data = yf.download(symbol, period="3mo", interval="1d", progress=False)
    if len(data) < 15:
        return False, data, {}

    close = data["Close"].squeeze()

    ema5  = close.ewm(span=5,  adjust=False).mean()
    ema8  = close.ewm(span=8,  adjust=False).mean()
    ema13 = close.ewm(span=13, adjust=False).mean()

    e5_now   = float(ema5.iloc[-1])
    e8_now   = float(ema8.iloc[-1])
    e13_now  = float(ema13.iloc[-1])
    e5_prev  = float(ema5.iloc[-2])
    e8_prev  = float(ema8.iloc[-2])
    e13_prev = float(ema13.iloc[-2])

    last_close = float(close.iloc[-1])

    # EMA5 EMA8'i yukari kesti
    ema5_kesti_ema8 = e5_prev < e8_prev and e5_now > e8_now

    # EMA5 EMA13'u yukari kesti
    ema5_kesti_ema13 = e5_prev < e13_prev and e5_now > e13_now

    # EMA8 EMA13'u yukari kesti
    ema8_kesti_ema13 = e8_prev < e13_prev and e8_now > e13_now

    # EMA5 > EMA8 > EMA13 tam sirali dizilim
    sirali_dizilim = e5_now > e8_now > e13_now

    # Sadece tam sirali dizilim: EMA5 > EMA8 > EMA13
    signal = sirali_dizilim

    if not signal:
        return False, data, {}

    sinyal_tipi = "EMA5 > EMA8 > EMA13 SIRALI DIZILIM"

    stats = {
        "last_close":       round(last_close, 2),
        "ema5":             round(e5_now, 2),
        "ema8":             round(e8_now, 2),
        "ema13":            round(e13_now, 2),
        "sinyal_tipi":      sinyal_tipi,
        "sirali_dizilim":   sirali_dizilim,
        "ema5_kesti_ema8":  ema5_kesti_ema8,
        "ema8_kesti_ema13": ema8_kesti_ema13,
    }
    return True, data, stats


def send_chart(symbol, data, stats):
    plot = data.tail(60).copy().reset_index()
    date_col = "Datetime" if "Datetime" in plot.columns else "Date"
    dates = pd.to_datetime(plot[date_col])
    x = np.arange(len(plot))

    close_s    = plot["Close"].squeeze()
    ema5_line  = close_s.ewm(span=5,  adjust=False).mean()
    ema8_line  = close_s.ewm(span=8,  adjust=False).mean()
    ema13_line = close_s.ewm(span=13, adjust=False).mean()

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(16, 9),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True
    )
    fig.patch.set_facecolor("#0a0a0f")
    ax1.set_facecolor("#0a0a0f")
    ax2.set_facecolor("#0a0a0f")
    fig.subplots_adjust(hspace=0.05)

    # Mumlar
    for i, row in plot.iterrows():
        o = float(row["Open"].squeeze())
        c = float(row["Close"].squeeze())
        h = float(row["High"].squeeze())
        l = float(row["Low"].squeeze())
        color  = "#26a69a" if c >= o else "#ef5350"
        bottom = min(o, c)
        height = abs(c - o) or (h - l) * 0.01
        ax1.bar(i, height, bottom=bottom, color=color, width=0.6, linewidth=0)
        ax1.plot([i, i], [l, h], color=color, linewidth=0.8)

    # EMA cizgileri
    ax1.plot(x, ema5_line,  color="#00e676", linewidth=1.8, label=f"EMA5: {stats['ema5']}")
    ax1.plot(x, ema8_line,  color="#ffd740", linewidth=1.8, label=f"EMA8: {stats['ema8']}")
    ax1.plot(x, ema13_line, color="#ff5252", linewidth=1.8, label=f"EMA13: {stats['ema13']}")

    # Kesisim isareti
    renk   = "#00e676" if stats["sirali_dizilim"] else "#ffd740"
    etiket = "EMA5>EMA8>EMA13" if stats["sirali_dizilim"] else "EMA KESISIM"

    ax1.axvline(x=len(plot)-1, color=renk, linewidth=1.5, linestyle=":", alpha=0.8)
    ax1.annotate(
        etiket,
        xy=(len(plot)-1, stats["last_close"]),
        xytext=(-130, 25),
        textcoords="offset points",
        color=renk, fontsize=11, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=renk, lw=1.5)
    )

    ax1.set_title(
        f"{symbol}  |  Gunluk EMA  |  {stats['last_close']}  |  {stats['sinyal_tipi']}",
        color="white", fontsize=10, pad=10
    )
    ax1.tick_params(colors="#555")
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#222")
    ax1.legend(facecolor="#0f0f1a", edgecolor="#333",
               labelcolor="white", fontsize=8, loc="upper left")

    # Hacim
    for i, row in plot.iterrows():
        c   = float(row["Close"].squeeze())
        o   = float(row["Open"].squeeze())
        vol = float(row["Volume"].squeeze())
        color = "#26a69a" if c >= o else "#ef5350"
        ax2.bar(i, vol, color=color, width=0.6, alpha=0.7, linewidth=0)

    ax2.set_ylabel("Hacim", color="#555", fontsize=8)
    ax2.tick_params(colors="#555", labelsize=7)
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#222")

    tick_pos    = x[::8]
    tick_labels = [dates.iloc[i].strftime("%d/%m")
                   for i in range(0, len(dates), 8)]
    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_labels, rotation=45,
                        ha="right", color="#555", fontsize=7)

    plt.tight_layout()
    fname = f"{symbol.replace('.','_')}_ema_gunluk.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()

    caption = (
        f"<b>{symbol}</b> - Gunluk EMA Kesisim\n"
        f"Fiyat: {stats['last_close']}\n"
        f"EMA5: {stats['ema5']} | EMA8: {stats['ema8']} | EMA13: {stats['ema13']}\n\n"
        f"{stats['sinyal_tipi']}"
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

    print(f"[SINYAL]: {symbol} - {stats['sinyal_tipi']}")


def run():
    send_message("Gunluk EMA 5-8-13 Kesisim taramasi basladi")
    symbols = get_symbols()
    send_message(f"{len(symbols)} hisse kontrol ediliyor...")

    found = 0
    for s in symbols:
        try:
            signal, data, stats = analyze(s)
            if signal:
                found += 1
                send_chart(s, data, stats)
        except Exception as e:
            print(f"[HATA] {s}: {e}")

    if found == 0:
        send_message("Kesisim bulunamadi")
    else:
        send_message(f"Tarama tamamlandi - {found} kesisim bulundu!")


run()
