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


def analyze(symbol):
    # 4 saatlik veri çek
    data = yf.download(symbol, period="1mo", interval="4h", progress=False)
    if len(data) < 20:
        return False, data, {}

    close = data["Close"].squeeze()

    wma9_series  = wma(close, 9)
    wma15_series = wma(close, 15)

    wma9_now  = float(wma9_series.iloc[-1])
    wma15_now = float(wma15_series.iloc[-1])
    wma9_prev  = float(wma9_series.iloc[-2])
    wma15_prev = float(wma15_series.iloc[-2])
    last_close = float(close.iloc[-1])

    # ── KESİŞİM TESPİTİ ──
    kesisim = None
    if wma9_prev < wma15_prev and wma9_now > wma15_now:
        kesisim = "alim"
    elif wma9_prev > wma15_prev and wma9_now < wma15_now:
        kesisim = "satim"

    # ── TEMAS TESPİTİ ──
    # Fiyat WMA'nın %1.5 yakınına geldiyse temas var
    temas = []
    if abs(last_close - wma9_now) / last_close < 0.015:
        # Hangi yönden temas?
        yon = "alttan" if last_close < wma9_now else "üstten"
        temas.append(f"WMA9 {yon} temas")
    if abs(last_close - wma15_now) / last_close < 0.015:
        yon = "alttan" if last_close < wma15_now else "üstten"
        temas.append(f"WMA15 {yon} temas")

    # Sinyal var mı? Kesişim veya temas olmalı
    signal = kesisim is not None or len(temas) > 0

    stats = {
        "last_close": round(last_close, 2),
        "wma9":       round(wma9_now, 2),
        "wma15":      round(wma15_now, 2),
        "wma9_s":     wma9_series,
        "wma15_s":    wma15_series,
        "kesisim":    kesisim,
        "temas":      temas,
    }
    return signal, data, stats


def send_chart(symbol, data, stats):
    plot_data  = data.tail(60).copy().reset_index()

    # 4h veride index adı Datetime olabilir
    date_col = "Datetime" if "Datetime" in plot_data.columns else "Date"
    dates    = pd.to_datetime(plot_data[date_col])
    x_pos    = np.arange(len(plot_data))

    full_close  = plot_data["Close"].squeeze()
    wma9_line   = wma(full_close, 9)
    wma15_line  = wma(full_close, 15)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(16, 9),
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
        ax1.plot([i, i], [l, h], color=color, linewidth=0.8)

    # ── WMA çizgileri ──
    ax1.plot(x_pos, wma9_line,  color="#76ff03", linewidth=1.8,
             label=f"WMA9: {stats['wma9']}")
    ax1.plot(x_pos, wma15_line, color="#ff6d00", linewidth=1.8,
             label=f"WMA15: {stats['wma15']}")

    # ── Kesişim noktasını işaretle ──
    if stats["kesisim"]:
        renk  = "#00e676" if stats["kesisim"] == "alim" else "#ff1744"
        etiket = "🟢 ALIM KESİSİMİ" if stats["kesisim"] == "alim" else "🔴 SATIM KESİSİMİ"
        ax1.axvline(x=len(plot_data) - 1, color=renk,
                    linewidth=2, linestyle=":", alpha=0.9)
        ax1.annotate(
            etiket,
            xy=(len(plot_data) - 1, stats["last_close"]),
            xytext=(-110, 25),
            textcoords="offset points",
            color=renk,
            fontsize=10,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=renk, lw=1.5)
        )

    # ── Temas noktalarını işaretle ──
    for i, t in enumerate(stats["temas"]):
        renk = "#76ff03" if "WMA9" in t else "#ff6d00"
        ax1.annotate(
            f"⚡ {t}",
            xy=(len(plot_data) - 1, stats["last_close"]),
            xytext=(-110, -25 - (i * 20)),
            textcoords="offset points",
            color=renk,
            fontsize=9,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=renk, lw=1.2)
        )

    # Başlık
    sinyal_str = ""
    if stats["kesisim"] == "alim":
        sinyal_str = "🟢 ALIM"
    elif stats["kesisim"] == "satim":
        sinyal_str = "🔴 SATIM"
    elif stats["temas"]:
        sinyal_str = "⚡ TEMAS"

    ax1.set_title(
        f"{symbol}  |  4H WMA Tarayici  |  {stats['last_close']}  |  {sinyal_str}",
        color="white", fontsize=13, pad=10
    )
    ax1.tick_params(colors="#888888")
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#333333")
    ax1.legend(facecolor="#1a1a2e", edgecolor="#333",
               labelcolor="white", fontsize=9, loc="upper left")

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

    # Her 6 mumda bir tarih göster (kalabalık olmasın)
    tick_positions = x_pos[::6]
    tick_labels    = [dates.iloc[i].strftime("%d/%m %H:%M")
                      for i in range(0, len(dates), 6)]
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels, rotation=45,
                        ha="right", color="#888888", fontsize=7)

    plt.tight_layout()
    fname = f"{symbol.replace('.', '_')}_4h.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()

    # ── Caption ──
    kesisim_text = ""
    if stats["kesisim"] == "alim":
        kesisim_text = "🟢 WMA ALIM KESİSİMİ (WMA9 WMA15 üstüne çıktı)"
    elif stats["kesisim"] == "satim":
        kesisim_text = "🔴 WMA SATIM KESİSİMİ (WMA9 WMA15 altına düştü)"

    temas_text = "\n".join([f"⚡ {t}" for t in stats["temas"]]) if stats["temas"] else ""

    caption = (
        f"<b>{symbol}</b> — 4H WMA Sinyali\n"
        f"💰 Fiyat: {stats['last_close']}\n"
        f"📊 WMA9: {stats['wma9']}  |  WMA15: {stats['wma15']}\n"
    )
    if kesisim_text:
        caption += f"\n{kesisim_text}\n"
    if temas_text:
        caption += f"\n{temas_text}\n"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(fname, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f}
        )

    # Kesişimse ayrıca acil mesaj at
    if stats["kesisim"]:
        acil = (
            f"🚨 <b>4H WMA KESİSİM ALARMI</b>\n\n"
            f"<b>{symbol}</b>\n"
            f"{kesisim_text}\n"
            f"💰 Fiyat: {stats['last_close']}\n"
            f"WMA9: {stats['wma9']}  |  WMA15: {stats['wma15']}"
        )
        send_message(acil)

    print(f"[SINYAL]: {symbol} — {stats['kesisim'] or 'temas'}")


def run():
    send_message("🔍 4H WMA Kesisim + Temas taramasi basladi")
    symbols = get_symbols()
    send_message(f"📋 {len(symbols)} hisse kontrol ediliyor...")

    kesisim_count = 0
    temas_count   = 0

    for s in symbols:
        try:
            signal, data, stats = analyze(s)
            if signal:
                send_chart(s, data, stats)
                if stats["kesisim"]:
                    kesisim_count += 1
                if stats["temas"]:
                    temas_count += 1
        except Exception as e:
            print(f"[HATA] {s}: {e}")

    send_message(
        f"✅ Tarama tamamlandi\n"
        f"🔀 Kesisim: {kesisim_count} hisse\n"
        f"⚡ Temas: {temas_count} hisse"
    )


run()
