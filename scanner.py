import os, io, requests, numpy as np, pandas as pd
import yfinance as yf, mplfinance as mpf, matplotlib.pyplot as plt

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc")
CHAT_ID        = os.environ.get("TELEGRAM_CHAT_ID", "8599240314")
SHEET_ID       = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL      = os.environ.get("SHEET_URL",
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv")

def tg_yaz(metin):
    print(f"[TG] {metin[:120]}")
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": metin},
            timeout=15
        )
        print(f"     {r.status_code} | {r.text[:300]}")
        return r.ok
    except Exception as e:
        print(f"     HATA: {e}")
        return False

def tg_foto(buf, caption):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            files={"photo": ("chart.png", buf, "image/png")},
            data={"chat_id": CHAT_ID, "caption": caption},
            timeout=30
        )
        print(f"[FOTO] {r.status_code} | {r.text[:200]}")
        return r.ok
    except Exception as e:
        print(f"[FOTO] HATA: {e}")
        return False

def pivot_bul(df, pencere=5, tolerans=0.015, min_dok=2):
    highs, lows = df["High"].values, df["Low"].values
    tum = list(highs) + list(lows)
    t_ham, d_ham = [], []
    for i in range(pencere, len(df) - pencere):
        if highs[i] == max(highs[i-pencere:i+pencere+1]): t_ham.append(highs[i])
        if lows[i]  == min(lows[i-pencere:i+pencere+1]):  d_ham.append(lows[i])

    def isle(ham):
        if not ham: return []
        ham = sorted(ham)
        kumeler, k = [], [ham[0]]
        for v in ham[1:]:
            if (v - k[-1]) / k[-1] < tolerans: k.append(v)
            else: kumeler.append(float(np.mean(k))); k = [v]
        kumeler.append(float(np.mean(k)))
        return sorted(
            [(s, sum(1 for f in tum if abs(f-s)/s < tolerans))
             for s in kumeler
             if sum(1 for f in tum if abs(f-s)/s < tolerans) >= min_dok],
            key=lambda x: x[1], reverse=True
        )
    return isle(t_ham), isle(d_ham)

def sinyal(df, tepeler, dipler, tol=0.03):
    fiyat = float(df["Close"].iloc[-1])
    for sev, guc in dipler:
        uzak = (fiyat - sev) / sev
        if -0.01 < uzak < tol: return "ALIS", sev, guc, uzak * 100
    for sev, guc in tepeler:
        uzak = (sev - fiyat) / sev
        if -0.01 < uzak < tol: return "SATIS", sev, guc, uzak * 100
    return None, None, None, None

def grafik(df, hisse, tepeler, dipler, tip, sev):
    son = df.tail(100).copy()
    ekler = (
        [mpf.make_addplot([s]*len(son), color="#FF4444", linestyle="--", width=1.2) for s,_ in tepeler[:3]] +
        [mpf.make_addplot([s]*len(son), color="#44FF88", linestyle="--", width=1.2) for s,_ in dipler[:3]] +
        [mpf.make_addplot([sev]*len(son), color="#00BFFF", linestyle="-", width=2.5)]
    )
    mc = mpf.make_marketcolors(up="#26A69A", down="#EF5350", edge="inherit",
                                wick={"up":"#26A69A","down":"#EF5350"},
                                volume={"up":"#26A69A","down":"#EF5350"})
    stil = mpf.make_mpf_style(
        marketcolors=mc, facecolor="#131722", figcolor="#131722",
        edgecolor="#2A2E39", gridcolor="#2A2E39", gridstyle="--", y_on_right=True,
        rc={"axes.labelcolor":"white","xtick.color":"white",
            "ytick.color":"white","text.color":"white"}
    )
    fiyat = float(df["Close"].iloc[-1])
    etiket = "ALIS BOLGESI" if tip == "ALIS" else "SATIS BOLGESI"
    buf = io.BytesIO()
    fig, _ = mpf.plot(son, type="candle", addplot=ekler,
                      title=f"\n{hisse}  {fiyat:.2f} TL  {etiket}",
                      style=stil, volume=True, figsize=(12,7), returnfig=True)
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#131722", dpi=130)
    buf.seek(0); plt.close(fig)
    return buf

def analiz_et():
    print("="*60)
    print(f"Token: {TELEGRAM_TOKEN[:20]}...")
    print(f"Chat ID: {CHAT_ID}")

    # Telegram testi
    if not tg_yaz("Hisse Tarama Botu basladi. Hisseler taraniyor..."):
        print("TELEGRAM CALISMIYOR"); return

    # Hisse listesi
    try:
        df_s = pd.read_csv(SHEET_URL)
        print(f"Sutunlar: {list(df_s.columns)}")
        sutun = "Hisse" if "Hisse" in df_s.columns else df_s.columns[0]
        hisseler = [str(h).replace(".IS","").strip().upper()
                    for h in df_s[sutun].dropna().unique()]
        print(f"{len(hisseler)} hisse: {hisseler[:10]}")
        tg_yaz(f"{len(hisseler)} hisse taraniyor...")
    except Exception as e:
        print(f"Sheets hatasi: {e}")
        tg_yaz(f"Sheets okunamadi: {e}"); return

    # Tarama
    bulunan = 0
    for i, hisse in enumerate(hisseler):
        try:
            df = yf.Ticker(f"{hisse}.IS").history(period="1y", interval="1d")
            if len(df) < 60:
                print(f"[{i+1}/{len(hisseler)}] {hisse}: veri yok ({len(df)})")
                continue

            tepeler, dipler = pivot_bul(df)
            tip, sev, guc, uzak = sinyal(df, tepeler, dipler, tol=0.03)
            fiyat = float(df["Close"].iloc[-1])
            degis = (df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100

            if tip:
                emoji = "ALIS" if tip == "ALIS" else "SATIS"
                print(f"[{i+1}] {hisse}: {emoji}! Fiyat={fiyat:.2f} Seviye={sev:.2f} Guc={guc}x")
                buf = grafik(df, hisse, tepeler, dipler, tip, sev)
                d_str = " | ".join([f"{s:.2f}({g}x)" for s,g in dipler[:3]])
                t_str = " | ".join([f"{s:.2f}({g}x)" for s,g in tepeler[:3]])
                caption = (
                    f"{'ALIS' if tip=='ALIS' else 'SATIS'} BOLGESI\n"
                    f"Hisse: {hisse}\n"
                    f"Fiyat: {fiyat:.2f} TL ({degis:+.2f}%)\n"
                    f"Seviye: {sev:.2f} TL | Guc: {guc}x | Uzaklik: %{uzak:.1f}\n"
                    f"Destek: {d_str}\n"
                    f"Direnc: {t_str}"
                )
                tg_foto(buf, caption)
                bulunan += 1
            else:
                print(f"[{i+1}/{len(hisseler)}] {hisse}: sinyal yok ({fiyat:.2f})")

        except Exception as e:
            print(f"[{i+1}] {hisse}: HATA - {e}")
            continue

    print(f"Tamamlandi: {bulunan} sinyal")
    if bulunan == 0:
        tg_yaz("Tarama tamamlandi. Su an sinyal yok.")
    else:
        tg_yaz(f"Tarama tamamlandi. {bulunan} sinyal gonderildi.")

if __name__ == "__main__":
    analiz_et()
