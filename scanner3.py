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


def get_mtf_wma(symbol):
    """
    Çoklu zaman diliminde WMA hesapla:
    - Günlük WMA9, WMA15
    - Haftalık WMA9, WMA15
    - Aylık WMA9, WMA15
    - 3 Aylık WMA9
    """
    # 4H ana veri
    data_4h = yf.download(symbol, period="3mo", interval="4h", progress=False)

    # Günlük veri
    data_1d = yf.download(symbol, period="6mo", interval="1d", progress=False)

    # Haftalık veri
    data_1w = yf.download(symbol, period="2y", interval="1wk", progress=False)

    # Aylık veri
    data_1mo = yf.download(symbol, period="5y", interval="1mo", progress=False)

    if len(data_4h) < 10 or len(data_1d) < 15 or len(data_1w) < 15 or len(data_1mo) < 9:
        return None, None

    # Her zaman diliminde WMA hesapla (son değer)
    def last_wma(data, period):
        close = data["Close"].squeeze()
        result = wma(close, period)
        return float(result.iloc[-1]) if not pd.isna(result.iloc[-1]) else None

    mtf = {
        # Günlük
        "d_wma9":  last_wma(data_1d, 9),
        "d_wma15": last_wma(data_1d, 15),
        # Haftalık
        "w_wma9":  last_wma(data_1w, 9),
        "w_wma15": last_wma(data_1w, 15),
        # Aylık
        "m_wma9":  last_wma(data_1mo, 9),
        "m_wma15": last_wma(data_1mo, 15),
        # 3 Aylık
        "q_wma9":  last_wma(data_1mo, 3),
    }

    return data_4h, mtf


def analyze(symbol):
    data_4h, mtf = get_mtf_wma(symbol)

    if data_4h is None:
        return False, None, {}

    close      = data_4h["Close"].squeeze()
    last_close = float(close.iloc[-1])

    # ── Sinyaller ──
    sinyaller = []

    # 1) Fiyat tüm günlük WMA'ların üzerinde mi?
    uzerinde = []
    altinda  = []
    for key, label in [
        ("d_wma9",  "Günlük WMA9"),
        ("d_wma15", "Günlük WMA15"),
        ("w_wma9",  "Haftalık WMA9"),
        ("w_wma15", "Haftalık WMA15"),
        ("m_wma9",  "Aylık WMA9"),
        ("m_wma15", "Aylık WMA15"),
    ]:
        val = mtf.get(key)
        if val is None:
            continue
        if last_close > val:
            uzerinde.append(label)
        else:
            altinda.append(label)

    # 2) Temas tespiti — fiyat WMA'nın %2 yakınında mı?
    temas = []
    for key, label, renk in [
        ("d_wma9",  "Günlük WMA9",  "🟢"),
        ("d_wma15", "Günlük WMA15", "🔴"),
        ("w_wma9",  "Haftalık WMA9",  "🟡"),
        ("w_wma15", "Haftalık WMA15", "🟠"),
        ("m_wma9",  "Aylık WMA9",  "🔵"),
        ("m_wma15", "Aylık WMA15", "🟣"),
    ]:
        val = mtf.get(key)
        if val is None:
            continue
        mesafe = abs(last_close - val) / last_close
        if mesafe < 0.02:
            yon = "üstten" if last_close > val else "alttan"
            temas.append(f"{renk} {label} {yon} temas (%{round(mesafe*100,1)})")

    # 3) WMA dizilimi sağlıklı mı? (günlük > haftalık > aylık)
    dizi_saglikli = False
    if all(mtf.get(k) for k in ["d_wma9", "w_wma9", "m_wma9"]):
        dizi_saglikli = (
            mtf["d_wma9"] > mtf["w_wma9"] > mtf["m_wma9"]
        )

    # 4) Günlük WMA kesişimi (son 2 mum)
    close_1d   = data_4h["Close"].squeeze()
    wma9_4h    = wma(close_1d, 9)
    wma15_4h   = wma(close_1d, 15)
    kesisim_4h = None
    if (float(wma9_4h.iloc[-2]) < float(wma15_4h.iloc[-2]) and
            float(wma9_4h.iloc[-1]) > float(wma15_4h.iloc[-1])):
        kesisim_4h = "alim"
    elif (float(wma9_4h.iloc[-2]) > float(wma15_4h.iloc[-2]) and
          float(wma9_4h.iloc[-1]) < float(wma15_4h.iloc[-1])):
        kesisim_4h = "satim"

    # ── Sinyal kriteri ──
    # En az 1 temas VEYA kesişim olmalı
    signal = len(temas) > 0 or kesisim_4h is not None

    stats = {
        "last_close":    round(last_close, 2),
        "mtf":           mtf,
        "uzerinde":      uzerinde,
        "altinda":       altinda,
        "temas":         temas,
        "dizi_saglikli": dizi_saglikli,
        "kesisim_4h":    kesisim_4h,
    }
    return signal, data_4h, stats


def send_chart(symbol, data_4h, stats):
    plot_data = data_4h.tail(60).copy().reset_index()
    date_col  = "Datetime" if "Datetime" in plot_data.columns else "Date"
    dates     = pd.to_datetime(plot_data[date_col])
    x_pos     = np.arange(len(plot_data))
    n         = len(plot_data)

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

    # ── MTF WMA yatay çizgileri ──
    mtf = stats["mtf"]
    wma_levels = [
        ("d_wma9",  "Günlük WMA9",   "#00e676", "-",  1.8),
        ("d_wma15", "Günlük WMA15",  "#ff1744", "-",  1.8),
        ("w_wma9",  "Haftalık WMA9", "#ffea00", "--", 1.5),
        ("w_wma15", "Haftalık WMA15","#ff9100", "--", 1.5),
        ("m_wma9",  "Aylık WMA9",    "#40c4ff", ":",  1.3),
        ("m_wma15", "Aylık WMA15",   "#ea80fc", ":",  1.3),
        ("q_wma9",  "3Aylık WMA9",   "#b0bec5", "-.", 1.2),
    ]

    for key, label, color, style, lw in wma_levels:
        val = mtf.get(key)
        if val:
            ax1.axhline(val, color=color, linewidth=lw,
                        linestyle=style, alpha=0.85,
                        label=f"{label}: {round(val, 2)}")

    # ── Kesişim işareti ──
    if stats["kesisim_4h"]:
        renk   = "#00e676" if stats["kesisim_4h"] == "alim" else "#ff1744"
        etiket = "🟢 4H ALIM KESİSİMİ" if stats["kesisim_4h"] == "alim" else "🔴 4H SATIM KESİSİMİ"
        ax1.axvline(x=n - 1, color=renk, linewidth=2, linestyle=":", alpha=0.9)
        ax1.annotate(etiket,
                     xy=(n - 1, stats["last_close"]),
                     xytext=(-120, 30),
                     textcoords="offset points",
                     color=renk, fontsize=10, fontweight="bold",
                     arrowprops=dict(arrowstyle="->", color=renk, lw=1.5))

    # ── Başlık ──
    dizi = "✅ Trend Sağlıklı" if stats["dizi_saglikli"] else "⚠️ Trend Karışık"
    ax1.set_title(
        f"{symbol}  |  MTF WMA Tarayici  |  {stats['last_close']}  |  {dizi}",
        color="white", fontsize=12, pad=10
    )
    ax1.tick_params(colors="#666666")
    ax1.yaxis.tick_right()
    ax1.yaxis.set_label_position("right")
    for spine in ax1.spines.values():
        spine.set_edgecolor("#222222")
    ax1.legend(facecolor="#0f0f1a", edgecolor="#333",
               labelcolor="white", fontsize=7, loc="upper left",
               ncol=2)

    # ── Hacim ──
    for i, row in plot_data.iterrows():
        c   = float(row["Close"].squeeze())
        o   = float(row["Open"].squeeze())
        vol = float(row["Volume"].squeeze())
        color = "#26a69a" if c >= o else "#ef5350"
        ax2.bar(i, vol, color=color, width=0.6, alpha=0.7, linewidth=0)

    ax2.set_ylabel("Hacim", color="#666666", fontsize=8)
    ax2.tick_params(colors="#666666", labelsize=7)
    ax2.yaxis.tick_right()
    ax2.yaxis.set_label_position("right")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#222222")

    tick_pos    = x_pos[::8]
    tick_labels = [dates.iloc[i].strftime("%d/%m %H:%M")
                   for i in range(0, len(dates), 8)]
    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_labels, rotation=45,
                        ha="right", color="#666666", fontsize=7)

    plt.tight_layout()
    fname = f"{symbol.replace('.', '_')}_mtf.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()

    # ── Caption ──
    uzerinde_str = ", ".join(stats["uzerinde"]) if stats["uzerinde"] else "Yok"
    altinda_str  = ", ".join(stats["altinda"])  if stats["altinda"]  else "Yok"
    temas_str    = "\n".join(stats["temas"])    if stats["temas"]    else "Temas yok"
    dizi_str     = "✅ Sağlıklı (Günlük > Haftalık > Aylık)" if stats["dizi_saglikli"] else "⚠️ Karışık"

    kesisim_str = ""
    if stats["kesisim_4h"] == "alim":
        kesisim_str = "\n🟢 <b>4H ALIM KESİSİMİ</b>"
    elif stats["kesisim_4h"] == "satim":
        kesisim_str = "\n🔴 <b>4H SATIM KESİSİMİ</b>"

    caption = (
        f"<b>{symbol}</b> — MTF WMA Analizi\n"
        f"💰 Fiyat: {stats['last_close']}\n\n"
        f"📊 <b>WMA Seviyeleri:</b>\n"
        f"🟢 Günlük  → WMA9: {round(mtf.get('d_wma9',0),2)} | WMA15: {round(mtf.get('d_wma15',0),2)}\n"
        f"🟡 Haftalık → WMA9: {round(mtf.get('w_wma9',0),2)} | WMA15: {round(mtf.get('w_wma15',0),2)}\n"
        f"🔵 Aylık   → WMA9: {round(mtf.get('m_wma9',0),2)} | WMA15: {round(mtf.get('m_wma15',0),2)}\n"
        f"⚪ 3Aylık  → WMA9: {round(mtf.get('q_wma9',0),2)}\n\n"
        f"📈 Trend: {dizi_str}\n"
        f"✅ Üzerinde: {uzerinde_str}\n"
        f"❌ Altında: {altinda_str}\n\n"
        f"⚡ <b>Temas:</b>\n{temas_str}"
        f"{kesisim_str}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(fname, "rb") as f:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": f}
        )

    if stats["kesisim_4h"]:
        send_message(
            f"🚨 <b>MTF WMA KESİSİM ALARMI</b>\n\n"
            f"<b>{symbol}</b>{kesisim_str}\n"
            f"💰 Fiyat: {stats['last_close']}\n"
            f"Trend: {dizi_str}"
        )

    print(f"[SINYAL]: {symbol}")


def run():
    send_message("🔍 MTF WMA Taramasi basladi\n(Günlük + Haftalık + Aylık + 3Aylık)")
    symbols = get_symbols()
    send_message(f"📋 {len(symbols)} hisse kontrol ediliyor...")

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
        send_message("⚠️ Sinyal bulunamadi")
    else:
        send_message(f"✅ Tarama tamamlandi — {found} hisse sinyal verdi!")


run()
