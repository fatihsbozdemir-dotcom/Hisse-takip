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
    prev = float(data_4h["Close"].squeeze().iloc[-2])

    d9  = mtf["d_wma9"]
    d15 = mtf["d_wma15"]
    w9  = mtf["w_wma9"]
    w15 = mtf["w_wma15"]
    m9  = mtf["m_wma9"]
    m15 = mtf["m_wma15"]

    # Gunluk WMA band
    d_alt = min(d9, d15)
    d_ust = max(d9, d15)

    # Haftalik WMA band
    w_alt = min(w9, w15)
    w_ust = max(w9, w15)

    # 1) Fiyat gunluk WMA9'a temas (%1.5 tolerans)
    temas_d9  = abs(last - d9)  / last < 0.015

    # 2) Fiyat gunluk WMA15'e temas (%1.5 tolerans)
    temas_d15 = abs(last - d15) / last < 0.015

    # 3) Fiyat gunluk WMA9 ve WMA15 ARASINDA
    arasinda_gunluk = d_alt <= last <= d_ust

    # 4) Fiyat haftalik WMA9'a temas (%1.5 tolerans)
    temas_w9  = abs(last - w9)  / last < 0.015

    # 5) Fiyat haftalik WMA15'e temas (%1.5 tolerans)
    temas_w15 = abs(last - w15) / last < 0.015

    # 6) Fiyat haftalik WMA9 ve WMA15 ARASINDA
    arasinda_haftalik = w_alt <= last <= w_ust

    # 7) Gunluk WMA9 yukari kirilim
    prev_d9    = float(data_4h["d_wma9"].iloc[-2])
    kirilim_d9 = prev < prev_d9 and last > d9

    # 8) Haftalik WMA9 yukari kirilim
    prev_w9    = float(data_4h["w_wma9"].iloc[-2])
    kirilim_w9 = prev < prev_w9 and last > w9

    gunluk_sinyal   = temas_d9 or temas_d15 or arasinda_gunluk
    haftalik_sinyal = temas_w9 or temas_w15 or arasinda_haftalik
    kirilim         = kirilim_d9 or kirilim_w9

    signal = gunluk_sinyal or haftalik_sinyal or kirilim

    # Sinyal tipi
    if kirilim_d9:
        sinyal_tipi = "KIRILIM - Gunluk WMA9 yukari kirildi"
    elif kirilim_w9:
        sinyal_tipi = "KIRILIM - Haftalik WMA9 yukari kirildi"
    else:
        detay = []
        if arasinda_gunluk:
            detay.append("Gunluk WMA arasinda")
        elif temas_d9:
            detay.append("Gunluk WMA9 temas")
        elif temas_d15:
            detay.append("Gunluk WMA15 temas")
        if arasinda_haftalik:
            detay.append("Haftalik WMA arasinda")
        elif temas_w9:
            detay.append("Haftalik WMA9 temas")
        elif temas_w15:
            detay.append("Haftalik WMA15 temas")
        sinyal_tipi = " | ".join(detay)

    stats = {
        "last":            round(last, 2),
        "mtf":             mtf,
        "sinyal_tipi":     sinyal_tipi,
        "kirilim":         kirilim,
        "kirilim_d9":      kirilim_d9,
        "kirilim_w9":      kirilim_w9,
        "gunluk_sinyal":   gunluk_sinyal,
        "haftalik_sinyal": haftalik_sinyal,
    }
    return signal, data_4h, stats


def send_chart(symbol, data_4h, stats):
    plot = data_4h.tail(60).copy().reset_index()
    date_col = "Datetime" if "Datetime" in plot.columns else "Date"
    dates = pd.to_datetime(plot[date_col])
    x = np.arange(len(plot))

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

    # MTF WMA cizgileri
    wma_cols = [
        ("d_wma9",  "Gunluk WMA9",    "#00e676", "-",  2.0),
        ("d_wma15", "Gunluk WMA15",   "#ff5252", "-",  2.0),
        ("w_wma9",  "Haftalik WMA9",  "#ffd740", "--", 1.6),
        ("w_wma15", "Haftalik WMA15", "#ff9100", "--", 1.6),
        ("m_wma9",  "Aylik WMA9",     "#40c4ff", ":",  1.3),
        ("m_wma15", "Aylik WMA15",    "#ea80fc", ":",  1.3),
    ]

    for col, label, color, style, lw in wma_cols:
        if col in plot.columns:
            vals = plot[col].squeeze()
            val_last = round(float(vals.iloc[-1]), 2)
            ax1.plot(x, vals, color=color, linewidth=lw,
                     linestyle=style, alpha=0.9,
                     label=f"{label}: {val_last}")

    # Sinyal isareti
    if stats["kirilim_d9"]:
        renk = "#00e676"
        etiket = "KIRILIM D-WMA9"
    elif stats["kirilim_w9"]:
        renk = "#ffd740"
        etiket = "KIRILIM W-WMA9"
    elif stats["gunluk_sinyal"]:
        renk = "#00e676"
        etiket = "GUNLUK WMA TEMAS/ARALIK"
    elif stats["haftalik_sinyal"]:
        renk = "#ffd740"
        etiket = "HAFTALIK WMA TEMAS/ARALIK"
    else:
        renk = "#ffffff"
        etiket = ""

    if etiket:
        ax1.axvline(x=len(plot)-1, color=renk,
                    linewidth=1.5, linestyle=":", alpha=0.8)
        ax1.annotate(
            etiket,
            xy=(len(plot)-1, stats["last"]),
            xytext=(-130, 25),
            textcoords="offset points",
            color=renk, fontsize=10, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=renk, lw=1.5)
        )

    ax1.set_title(
        f"{symbol}  |  MTF WMA  |  {stats['last']}  |  {stats['sinyal_tipi']}",
        color="white", fontsize=10, pad=10
    )
    ax1.tick_params(colors="#555")
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#222")
    ax1.legend(facecolor="#0f0f1a", edgecolor="#333",
               labelcolor="white", fontsize=7,
               loc="upper left", ncol=2)

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
    tick_labels = [dates.iloc[i].strftime("%d/%m %H:%M")
                   for i in range(0, len(dates), 8)]
    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_labels, rotation=45,
                        ha="right", color="#555", fontsize=7)

    plt.tight_layout()
    fname = f"{symbol.replace('.','_')}_mtf2.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()

    m = stats["mtf"]
    caption = (
        f"<b>{symbol}</b> - MTF WMA Analizi\n"
        f"Fiyat: {stats['last']}\n\n"
        f"Gunluk  WMA9: {round(m['d_wma9'],2)} | WMA15: {round(m['d_wma15'],2)}\n"
        f"Haftalik WMA9: {round(m['w_wma9'],2)} | WMA15: {round(m['w_wma15'],2)}\n"
        f"Aylik   WMA9: {round(m['m_wma9'],2)} | WMA15: {round(m['m_wma15'],2)}\n\n"
        f"Sinyal: {stats['sinyal_tipi']}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(fname, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f}
        )

    if stats["kirilim"]:
        send_message(
            f"KIRILIM ALARMI\n\n"
            f"<b>{symbol}</b>\n"
            f"{stats['sinyal_tipi']}\n"
            f"Fiyat: {stats['last']}"
        )

    print(f"[SINYAL]: {symbol} - {stats['sinyal_tipi']}")


def run():
    send_message("MTF WMA Taramasi basladi")
    symbols = get_symbols()
    send_message(f"{len(symbols)} hisse kontrol ediliyor...")

    found = 0
    for s in symbols:
        try:
            signal, data_4h, stats = analyze(s)
            if signal:
                found += 1
                send_chart(s, data_4h, stats)
        except Exception as e:
            print(f"[HATA] {s}: {e}")

    if found == 0:
        send_message("Sinyal bulunamadi")
    else:
        send_message(f"Tarama tamamlandi - {found} sinyal!")


run()
