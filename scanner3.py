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


def get_mtf_levels(symbol):
    """
    Her zaman diliminde WMA9 ve WMA15 hesapla.
    4H grafiğe tarihe göre eşleştirerek yansıt (dinamik step).
    """
    data_4h = yf.download(symbol, period="3mo",  interval="4h",  progress=False)
    data_1d = yf.download(symbol, period="1y",   interval="1d",  progress=False)
    data_1w = yf.download(symbol, period="3y",   interval="1wk", progress=False)
    data_1m = yf.download(symbol, period="10y",  interval="1mo", progress=False)

    if len(data_4h) < 10 or len(data_1d) < 15 or len(data_1w) < 15 or len(data_1m) < 9:
        return None, None

    # Her zaman diliminde WMA hesapla
    for df in [data_1d, data_1w, data_1m]:
        c = df["Close"].squeeze()
        df["wma9"]  = wma(c, 9)
        df["wma15"] = wma(c, 15)

    # 4H her satırına o anki günlük/haftalık/aylık WMA değerini eşleştir
    def map_to_4h(data_4h, source_df, col):
        """
        Her 4H mumunun tarihine en yakın önceki
        günlük/haftalık/aylık WMA değerini al
        """
        result = pd.Series(index=data_4h.index, dtype=float)
        src = source_df[col].dropna()

        for ts in data_4h.index:
            # O ana kadar olan son WMA değerini al
            ts_date = ts if hasattr(ts, 'date') else pd.Timestamp(ts)
            past = src[src.index <= ts_date]
            if len(past) > 0:
                result[ts] = float(past.iloc[-1])
        return result

    data_4h["d_wma9"]  = map_to_4h(data_4h, data_1d, "wma9")
    data_4h["d_wma15"] = map_to_4h(data_4h, data_1d, "wma15")
    data_4h["w_wma9"]  = map_to_4h(data_4h, data_1w, "wma9")
    data_4h["w_wma15"] = map_to_4h(data_4h, data_1w, "wma15")
    data_4h["m_wma9"]  = map_to_4h(data_4h, data_1m, "wma9")
    data_4h["m_wma15"] = map_to_4h(data_4h, data_1m, "wma15")

    return data_4h, {
        "d_wma9":  float(data_4h["d_wma9"].iloc[-1]),
        "d_wma15": float(data_4h["d_wma15"].iloc[-1]),
        "w_wma9":  float(data_4h["w_wma9"].iloc[-1]),
        "w_wma15": float(data_4h["w_wma15"].iloc[-1]),
        "m_wma9":  float(data_4h["m_wma9"].iloc[-1]),
        "m_wma15": float(data_4h["m_wma15"].iloc[-1]),
    }


def analyze(symbol):
    data_4h, mtf = get_mtf_levels(symbol)
    if data_4h is None:
        return False, None, {}

    last  = float(data_4h["Close"].squeeze().iloc[-1])
    prev  = float(data_4h["Close"].squeeze().iloc[-2])

    d9  = mtf["d_wma9"]
    d15 = mtf["d_wma15"]
    w9  = mtf["w_wma9"]
    w15 = mtf["w_wma15"]
    m9  = mtf["m_wma9"]
    m15 = mtf["m_wma15"]

    # ── DURUM TESPİTİ ──────────────────────────────
    # 1) Fiyat tüm WMA'ların üzerinde → Güçlü yükseliş
    guclu_yukselis = last > d9 and last > d15 and last > w9 and last > w15

    # 2) Fiyat günlük WMA'lara geri test yapıyor
    # (günlük WMA'dan max %3 uzakta ve üzerinden geliyor)
    d_wma_ust = max(d9, d15)
    d_wma_alt = min(d9, d15)
    geri_test_gunluk = (
        d_wma_alt * 0.97 < last < d_wma_ust * 1.03 and
        last > w9  # haftalık WMA üzerinde
    )

    # 3) Fiyat haftalık WMA'lara geri test yapıyor
    w_wma_ust = max(w9, w15)
    w_wma_alt = min(w9, w15)
    geri_test_haftalik = (
        w_wma_alt * 0.97 < last < w_wma_ust * 1.03 and
        last > m9  # aylık WMA üzerinde
    )

    # 4) Fiyat günlük WMA'yı yeni yukarı kırdı mı?
    # (önceki mumda altındaydı, şimdi üstünde)
    prev_d9  = float(data_4h["d_wma9"].iloc[-2])
    kirilim = prev < prev_d9 and last > d9

    # Sinyal var mı?
    signal = guclu_yukselis or geri_test_gunluk or geri_test_haftalik or kirilim

    # Sinyal tipi
    if kirilim:
        sinyal_tipi = "🚀 KIRILIM — Günlük WMA9 yukarı kırıldı"
    elif geri_test_gunluk:
        sinyal_tipi = "🟢 Günlük WMA desteği test ediliyor"
    elif geri_test_haftalik:
        sinyal_tipi = "🟡 Haftalık WMA desteği test ediliyor"
    elif guclu_yukselis:
        sinyal_tipi = "✅ Tüm WMA'ların üzerinde — Güçlü trend"
    else:
        sinyal_tipi = ""

    stats = {
        "last":             round(last, 2),
        "mtf":              mtf,
        "sinyal_tipi":      sinyal_tipi,
        "guclu_yukselis":   guclu_yukselis,
        "geri_test_gunluk": geri_test_gunluk,
        "geri_test_haftalik": geri_test_haftalik,
        "kirilim":          kirilim,
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

    # ── Mumlar ──
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

    # ── MTF WMA çizgileri (dinamik step) ──
    wma_cols = [
        ("d_wma9",  "Günlük WMA9",   "#00e676", "-",  2.0),
        ("d_wma15", "Günlük WMA15",  "#ff5252", "-",  2.0),
        ("w_wma9",  "Haftalık WMA9", "#ffd740", "--", 1.6),
        ("w_wma15", "Haftalık WMA15","#ff9100", "--", 1.6),
        ("m_wma9",  "Aylık WMA9",    "#40c4ff", ":",  1.3),
        ("m_wma15", "Aylık WMA15",   "#ea80fc", ":",  1.3),
    ]

    for col, label, color, style, lw in wma_cols:
        if col in plot.columns:
            vals = plot[col].squeeze()
            val_last = round(float(vals.iloc[-1]), 2)
            ax1.plot(x, vals, color=color, linewidth=lw,
                     linestyle=style, alpha=0.9,
                     label=f"{label}: {val_last}")

    # ── Kırılım işareti ──
    if stats["kirilim"]:
        ax1.axvline(x=len(plot)-1, color="#00e676",
                    linewidth=2, linestyle=":", alpha=0.9)
        ax1.annotate(
            "🚀 KIRILIM",
            xy=(len(plot)-1, stats["last"]),
            xytext=(-100, 25),
            textcoords="offset points",
            color="#00e676", fontsize=11, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#00e676", lw=1.5)
        )

    # ── Geri test işareti ──
    elif stats["geri_test_gunluk"] or stats["geri_test_haftalik"]:
        renk = "#ffd740" if stats["geri_test_haftalik"] else "#00e676"
        ax1.annotate(
            "⚡ DESTEK TESTİ",
            xy=(len(plot)-1, stats["last"]),
            xytext=(-110, 25),
            textcoords="offset points",
            color=renk, fontsize=10, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=renk, lw=1.5)
        )

    m = stats["mtf"]
    ax1.set_title(
        f"{symbol}  |  MTF WMA  |  {stats['last']}  |  {stats['sinyal_tipi']}",
        color="white", fontsize=11, pad=10
    )
    ax1.tick_params(colors="#555")
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#222")
    ax1.legend(facecolor="#0f0f1a", edgecolor="#333",
               labelcolor="white", fontsize=7,
               loc="upper left", ncol=2)

    # ── Hacim ──
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

    caption = (
        f"<b>{symbol}</b> — MTF WMA Analizi\n"
        f"💰 Fiyat: {stats['last']}\n\n"
        f"🟢 Günlük  WMA9: {round(m['d_wma9'],2)} | WMA15: {round(m['d_wma15'],2)}\n"
        f"🟡 Haftalık WMA9: {round(m['w_wma9'],2)} | WMA15: {round(m['w_wma15'],2)}\n"
        f"🔵 Aylık   WMA9: {round(m['m_wma9'],2)} | WMA15: {round(m['m_wma15'],2)}\n\n"
        f"📌 {stats['sinyal_tipi']}"
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
            f"🚨 <b>MTF WMA KIRILIM ALARMI</b>\n\n"
            f"<b>{symbol}</b>\n"
            f"🚀 Günlük WMA9 yukarı kırıldı!\n"
            f"💰 Fiyat: {stats['last']}\n"
            f"D_WMA9: {round(m['d_wma9'],2)} | W_WMA9: {round(m['w_wma9'],2)}"
        )

    print(f"[SINYAL]: {symbol} — {stats['sinyal_tipi']}")


def run():
    send_message("🔍 MTF WMA Debug taramasi basladi")
    symbols = get_symbols()

    for s in symbols[:10]:  # Sadece ilk 10 hisse test
        try:
            data_4h, mtf = get_mtf_levels(s)
            if data_4h is None:
                print(f"[ATLANDI] {s}")
                continue

            last = float(data_4h["Close"].squeeze().iloc[-1])
            d9   = mtf["d_wma9"]
            d15  = mtf["d_wma15"]
            w9   = mtf["w_wma9"]

            print(f"{s} | Fiyat:{round(last,2)} | D9:{round(d9,2)} | D15:{round(d15,2)} | W9:{round(w9,2)}")
            print(f"  Fiyat>D9:{last>d9} | Fiyat>D15:{last>d15} | Fiyat>W9:{last>w9}")

        except Exception as e:
            print(f"[HATA] {s}: {e}")

    send_message("Debug tamamlandi - loglara bak")

run()
