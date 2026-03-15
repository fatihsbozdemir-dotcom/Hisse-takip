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
    return series.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def analyze(symbol):
    data = yf.download(symbol, period="3mo", interval="1d", progress=False)
    if len(data) < 20:
        return False, data, {}

    last = data.tail(5).copy()
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
        std_ratio < 0.07 and
        atr_ratio < 0.07
    )

    full_close = data["Close"].squeeze()

    # EMA
    ema8  = float(full_close.ewm(span=8,  adjust=False).mean().iloc[-1])
    ema13 = float(full_close.ewm(span=13, adjust=False).mean().iloc[-1])
    ema21 = float(full_close.ewm(span=21, adjust=False).mean().iloc[-1])

    # WMA
    wma9_series  = wma(full_close, 9)
    wma15_series = wma(full_close, 15)
    wma9_val     = float(wma9_series.iloc[-1])
    wma15_val    = float(wma15_series.iloc[-1])
    wma9_prev    = float(wma9_series.iloc[-2])
    wma15_prev   = float(wma15_series.iloc[-2])

    # WMA kesişim tespiti
    # Önceki mumda wma9 < wma15, şimdi wma9 > wma15 → Altın Kesişim (Bullish)
    # Önceki mumda wma9 > wma15, şimdi wma9 < wma15 → Ölüm Kesişimi (Bearish)
    wma_kesisim = None
    if wma9_prev < wma15_prev and wma9_val > wma15_val:
        wma_kesisim = "🟡 WMA Altin Kesisim (WMA9 WMA15 üstüne cikti) — ALIM SİNYALİ"
    elif wma9_prev > wma15_prev and wma9_val < wma15_val:
        wma_kesisim = "💀 WMA Olum Kesisimi (WMA9 WMA15 altina düstü) — SATIM SİNYALİ"

    last_close = float(full_close.iloc[-1])

    # EMA temas
    temas = []
    for val, name in [(ema8, "EMA8"), (ema13, "EMA13"), (ema21, "EMA21")]:
        if abs(last_close - val) / last_close < 0.015:
            temas.append(name)

    formasyon = detect_patterns(data)

    stats = {
        "fiyat":        round(mean_price, 2),
        "destek":       round(float(low.min()), 2),
        "direnc":       round(float(high.max()), 2),
        "std":          round(std_ratio * 100, 2),
        "atr":          round(atr_ratio * 100, 2),
        "ema8":         round(ema8, 2),
        "ema13":        round(ema13, 2),
        "ema21":        round(ema21, 2),
        "wma9":         round(wma9_val, 2),
        "wma15":        round(wma15_val, 2),
        "wma9_series":  wma9_series,
        "wma15_series": wma15_series,
        "wma_kesisim":  wma_kesisim,
        "temas":        temas,
        "last_close":   round(last_close, 2),
        "formasyon":    formasyon,
    }
    return is_sideways, data, stats


def detect_patterns(data):
    df = data.tail(3).copy()
    patterns = []

    o = df["Open"].squeeze().values.astype(float)
    c = df["Close"].squeeze().values.astype(float)
    h = df["High"].squeeze().values.astype(float)
    l = df["Low"].squeeze().values.astype(float)

    body         = abs(c[-1] - o[-1])
    candle_range = h[-1] - l[-1]
    upper_wick   = h[-1] - max(c[-1], o[-1])
    lower_wick   = min(c[-1], o[-1]) - l[-1]

    if candle_range == 0:
        return patterns

    if body / candle_range < 0.1:
        patterns.append("⚪ Doji")

    if lower_wick > body * 2 and upper_wick < body * 0.5 and body / candle_range > 0.1:
        patterns.append("🔨 Hammer")

    if upper_wick > body * 2 and lower_wick < body * 0.5 and body / candle_range > 0.1:
        patterns.append("🌠 Shooting Star")

    if lower_wick > candle_range * 0.6 or upper_wick > candle_range * 0.6:
        patterns.append("📌 Pinbar")

    if (len(o) >= 2 and c[-2] < o[-2] and c[-1] > o[-1] and
            o[-1] < c[-2] and c[-1] > o[-2]):
        patterns.append("🟢 Bullish Engulfing")

    if (len(o) >= 2 and c[-2] > o[-2] and c[-1] < o[-1] and
            o[-1] > c[-2] and c[-1] < o[-2]):
        patterns.append("🔴 Bearish Engulfing")

    if (len(o) >= 3 and c[-3] < o[-3] and
            abs(c[-2] - o[-2]) < (h[-2] - l[-2]) * 0.3 and
            c[-1] > o[-1] and c[-1] > (o[-3] + c[-3]) / 2):
        patterns.append("🌅 Morning Star")

    if (len(o) >= 3 and c[-3] > o[-3] and
            abs(c[-2] - o[-2]) < (h[-2] - l[-2]) * 0.3 and
            c[-1] < o[-1] and c[-1] < (o[-3] + c[-3]) / 2):
        patterns.append("🌆 Evening Star")

    return patterns


def send_chart(symbol, data, stats):
    plot_data = data.tail(30).copy().reset_index()
    dates     = pd.to_datetime(plot_data["Date"])
    x_pos     = np.arange(len(plot_data))

    full_close  = plot_data["Close"].squeeze()
    ema8_line   = full_close.ewm(span=8,  adjust=False).mean()
    ema13_line  = full_close.ewm(span=13, adjust=False).mean()
    ema21_line  = full_close.ewm(span=21, adjust=False).mean()
    wma9_line   = wma(full_close, 9)
    wma15_line  = wma(full_close, 15)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True
    )
    fig.patch.set_facecolor("#0f1117")
    ax1.set_facecolor("#0f1117")
    ax2.set_facecolor("#0f1117")
    fig.subplots_adjust(hspace=0.05)

    # ── Mumlar ──
    for i, row in plot_data.iterrows():
        o = float(row["Open"].squeeze())
        c = float(row["Close"].squeeze())
        h = float(row["High"].squeeze())
        l = float(row["Low"].squeeze())
        color  = "#26a69a" if c >= o else "#ef5350"
        bottom = min(o, c)
        height = abs(c - o) or (h - l) * 0.01
        ax1.bar(i, height, bottom=bottom, color=color, width=0.6, linewidth=0)
        ax1.plot([i, i], [l, h], color=color, linewidth=0.9)

    # ── EMA ──
    ax1.plot(x_pos, ema8_line,  color="#f5c518", linewidth=1.2, label=f"EMA8: {stats['ema8']}")
    ax1.plot(x_pos, ema13_line, color="#00e5ff", linewidth=1.2, label=f"EMA13: {stats['ema13']}")
    ax1.plot(x_pos, ema21_line, color="#ff69b4", linewidth=1.2, label=f"EMA21: {stats['ema21']}")

    # ── WMA ──
    ax1.plot(x_pos, wma9_line,  color="#76ff03", linewidth=1.4,
             linestyle="--", label=f"WMA9: {stats['wma9']}")
    ax1.plot(x_pos, wma15_line, color="#ff6d00", linewidth=1.4,
             linestyle="--", label=f"WMA15: {stats['wma15']}")

    # ── WMA kesişim noktasını işaretle ──
    if stats["wma_kesisim"]:
        ax1.axvline(x=len(plot_data) - 1, color="#ffdd57",
                    linewidth=1.5, linestyle=":", alpha=0.7)
        ax1.annotate(
            "⚡ WMA KESİSİM",
            xy=(len(plot_data) - 1, stats["last_close"]),
            xytext=(-100, 30),
            textcoords="offset points",
            color="#ffdd57",
            fontsize=9,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#ffdd57", lw=1.5)
        )

    # ── Destek / Direnç ──
    ax1.axhline(stats["destek"], color="#ff9800", linewidth=1.2,
                linestyle="--", alpha=0.8, label=f"Destek: {stats['destek']}")
    ax1.axhline(stats["direnc"], color="#42a5f5", linewidth=1.2,
                linestyle="--", alpha=0.8, label=f"Direnc: {stats['direnc']}")

    # ── Formasyon etiketi ──
    if stats["formasyon"]:
        formasyon_str = " | ".join(stats["formasyon"])
        ax1.annotate(
            formasyon_str,
            xy=(len(plot_data) - 1, stats["last_close"]),
            xytext=(-130, -30),
            textcoords="offset points",
            color="#ffdd57",
            fontsize=8,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#ffdd57", lw=1.0)
        )

    ax1.set_title(
        f"{symbol}  |  Yatay + Formasyon + WMA  |  {stats['last_close']}",
        color="white", fontsize=12, pad=10
    )
    ax1.tick_params(colors="#888888")
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#333333")
    ax1.legend(facecolor="#1a1a2e", edgecolor="#333",
               labelcolor="white", fontsize=7, loc="upper left")

    # ── Hacim ──
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
    fname = f"{symbol.replace('.', '_')}_v2.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()

    formasyon_text = " | ".join(stats["formasyon"]) if stats["formasyon"] else "Formasyon yok"
    temas_text     = ", ".join(stats["temas"]) if stats["temas"] else "EMA temasi yok"

    caption = (
        f"<b>{symbol}</b> — Yatay + Formasyon\n"
        f"💰 Fiyat: {stats['last_close']}\n"
        f"🟢 Destek: {stats['destek']}  |  🔴 Direnc: {stats['direnc']}\n"
        f"📈 EMA8: {stats['ema8']} | EMA13: {stats['ema13']} | EMA21: {stats['ema21']}\n"
        f"📊 WMA9: {stats['wma9']} | WMA15: {stats['wma15']}\n"
        f"⚡ EMA Temas: {temas_text}\n"
        f"🕯 {formasyon_text}\n"
        f"📉 Std: %{stats['std']} | ATR: %{stats['atr']}"
    )

    # WMA kesişim varsa ayrıca bildir
    if stats["wma_kesisim"]:
        caption += f"\n\n🚨 <b>{stats['wma_kesisim']}</b>"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(fname, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f}
        )

    # WMA kesişimi ayrı mesaj olarak da gönder
    if stats["wma_kesisim"]:
        send_message(
            f"🚨 <b>WMA KESİSİM ALARMI</b>\n\n"
            f"<b>{symbol}</b>\n"
            f"{stats['wma_kesisim']}\n"
            f"💰 Fiyat: {stats['last_close']}\n"
            f"WMA9: {stats['wma9']} | WMA15: {stats['wma15']}"
        )

    print(f"[GRAFIK]: {symbol}")


def run():
    send_message("🔍 Yatay + Formasyon + WMA taramasi basladi")
    symbols = get_symbols()
    send_message(f"📋 {len(symbols)} hisse kontrol ediliyor...")

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
        send_message("⚠️ Yatay hisse bulunamadi")
    else:
        send_message(f"✅ Tarama tamamlandi — {found} hisse bulundu!")


run()
