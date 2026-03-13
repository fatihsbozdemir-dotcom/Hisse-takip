import os
import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import requests

# --- AYARLAR (GitHub Secrets'tan okunur) ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID        = os.environ["TELEGRAM_CHAT_ID"]
SHEET_URL      = os.environ.get("SHEET_URL",
    "https://docs.google.com/spreadsheets/d/12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA/export?format=csv")

# ---------------------------------------------------------------
# PIVOT DESTEK / DİRENÇ BULMA
# Grafikteki gibi: fiyatın birden fazla kez döndüğü seviyeleri bul
# ---------------------------------------------------------------
def pivot_noktalari_bul(df, pencere=5, min_dokunma=2, tolerans_pct=0.015):
    """
    Gerçek pivot high/low noktalarını bulur.
    - pencere: kaç mumdaki en yüksek/düşük olduğunu kontrol eder
    - min_dokunma: bir seviyenin geçerli sayılması için kaç kez test edilmeli
    - tolerans_pct: iki seviyenin aynı bölge sayılması için yakınlık yüzdesi
    """
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values

    # Pivot tepe ve dipleri bul
    pivot_tepeler = []
    pivot_dipler = []

    for i in range(pencere, len(df) - pencere):
        # Pivot tepe: penceredeki en yüksek nokta
        if highs[i] == max(highs[i - pencere:i + pencere + 1]):
            pivot_tepeler.append(highs[i])
        # Pivot dip: penceredeki en düşük nokta
        if lows[i] == min(lows[i - pencere:i + pencere + 1]):
            pivot_dipler.append(lows[i])

    # Yakın seviyeleri birleştir (kümeleme)
    def kumelere_ayir(levels, tolerans_pct):
        if not levels:
            return []
        levels = sorted(levels)
        kumeler = []
        mevcut_kume = [levels[0]]

        for level in levels[1:]:
            if (level - mevcut_kume[-1]) / mevcut_kume[-1] < tolerans_pct:
                mevcut_kume.append(level)
            else:
                kumeler.append(np.mean(mevcut_kume))
                mevcut_kume = [level]
        kumeler.append(np.mean(mevcut_kume))
        return kumeler

    # Kümeleme ve dokunma sayısı filtresi
    def guclu_seviyeler_bul(pivot_list, tum_fiyatlar, tolerans_pct, min_dokunma):
        kumeler = kumelere_ayir(pivot_list, tolerans_pct)
        guclu = []
        for seviye in kumeler:
            # Bu seviyeye kaç kez dokunulmuş?
            dokunma = sum(1 for f in tum_fiyatlar if abs(f - seviye) / seviye < tolerans_pct)
            if dokunma >= min_dokunma:
                guclu.append((seviye, dokunma))
        # Güce göre sırala
        return sorted(guclu, key=lambda x: x[1], reverse=True)

    tum_fiyatlar = list(highs) + list(lows)
    guclu_tepeler = guclu_seviyeler_bul(pivot_tepeler, tum_fiyatlar, tolerans_pct, min_dokunma)
    guclu_dipler = guclu_seviyeler_bul(pivot_dipler, tum_fiyatlar, tolerans_pct, min_dokunma)

    return guclu_tepeler, guclu_dipler


# ---------------------------------------------------------------
# GRAFİKTEKİ GİBİ: "ALIŞ BÖLGESİ" SİNYALİ
# Fiyat önemli bir destek seviyesine yaklaşmış VE dönüş mumları var
# ---------------------------------------------------------------
def alis_bolgesi_var_mi(df, guclu_dipler, tolerans_pct=0.025):
    """
    Son fiyat güçlü bir destek bölgesine yakın mı kontrol eder.
    Grafikteki 'Alış Bölgesi' etiketi gibi.
    """
    guncel_fiyat = df['Close'].iloc[-1]
    guncel_low = df['Low'].iloc[-1]
    son_mumlar = df.tail(3)

    for seviye, dokunma in guclu_dipler:
        uzaklik_pct = (guncel_fiyat - seviye) / seviye

        # Fiyat destek bölgesinin %2.5 içindeyse
        if -0.01 < uzaklik_pct < tolerans_pct:
            # Ek filtre: son mumlarda dönüş işareti (alt fitil uzun mu?)
            alt_fitil = son_mumlar['Low'].min()
            ust_fitil = son_mumlar['High'].max()
            govde = abs(son_mumlar['Close'].iloc[-1] - son_mumlar['Open'].iloc[-1])
            fitil_uzunluk = son_mumlar['Close'].iloc[-1] - alt_fitil

            return True, seviye, dokunma, uzaklik_pct * 100

    return False, None, None, None


def satis_bolgesi_var_mi(df, guclu_tepeler, tolerans_pct=0.025):
    """
    Son fiyat güçlü bir direnç bölgesine yakın mı kontrol eder.
    """
    guncel_fiyat = df['Close'].iloc[-1]

    for seviye, dokunma in guclu_tepeler:
        uzaklik_pct = (seviye - guncel_fiyat) / seviye

        if -0.01 < uzaklik_pct < tolerans_pct:
            return True, seviye, dokunma, uzaklik_pct * 100

    return False, None, None, None


# ---------------------------------------------------------------
# GRAFIK OLUŞTURMA - Grafikteki görünüme yakın
# ---------------------------------------------------------------
def grafik_olustur(df, hisse, guclu_tepeler, guclu_dipler, sinyal_tipi, sinyal_seviye):
    son_100 = df.tail(100).copy()

    # Ek çizgiler
    ek_cizgiler = []

    # Direnç seviyeleri (kırmızı)
    for seviye, dokunma in guclu_tepeler[:3]:
        cizgi = [seviye] * len(son_100)
        ek_cizgiler.append(
            mpf.make_addplot(cizgi, color='#FF4444', linestyle='--',
                             width=1.5, alpha=0.8)
        )

    # Destek seviyeleri (yeşil)
    for seviye, dokunma in guclu_dipler[:3]:
        cizgi = [seviye] * len(son_100)
        ek_cizgiler.append(
            mpf.make_addplot(cizgi, color='#44FF44', linestyle='--',
                             width=1.5, alpha=0.8)
        )

    # Sinyal seviyesi (mavi - kalın)
    sinyal_cizgi = [sinyal_seviye] * len(son_100)
    ek_cizgiler.append(
        mpf.make_addplot(sinyal_cizgi, color='#00BFFF', linestyle='-',
                         width=2.5)
    )

    # Grafik stili (koyu tema)
    mc = mpf.make_marketcolors(
        up='#26A69A', down='#EF5350',
        edge='inherit',
        wick={'up': '#26A69A', 'down': '#EF5350'},
        volume={'up': '#26A69A', 'down': '#EF5350'}
    )
    stil = mpf.make_mpf_style(
        marketcolors=mc,
        facecolor='#131722',
        edgecolor='#2A2E39',
        figcolor='#131722',
        gridcolor='#2A2E39',
        gridstyle='--',
        y_on_right=True,
        rc={'axes.labelcolor': 'white',
            'xtick.color': 'white',
            'ytick.color': 'white',
            'text.color': 'white'}
    )

    guncel_fiyat = df['Close'].iloc[-1]
    baslik = (f"\n{hisse}  |  {guncel_fiyat:.2f} TL  |  "
              f"{'🟢 ALIŞ BÖLGESİ' if sinyal_tipi == 'ALIS' else '🔴 SATIŞ BÖLGESİ'}")

    buf = io.BytesIO()
    fig, axlist = mpf.plot(
        son_100,
        type='candle',
        addplot=ek_cizgiler,
        title=baslik,
        style=stil,
        volume=True,
        figsize=(12, 8),
        returnfig=True
    )

    # Sinyal etiketi ekle (grafikteki gibi)
    ax = axlist[0]
    etiket = '🟢 Alış Bölgesi' if sinyal_tipi == 'ALIS' else '🔴 Satış Bölgesi'
    renk = '#00FF88' if sinyal_tipi == 'ALIS' else '#FF4444'
    ax.axhspan(sinyal_seviye * 0.98, sinyal_seviye * 1.02,
               alpha=0.15, color=renk, zorder=0)
    ax.text(0.02, sinyal_seviye, etiket,
            transform=ax.get_yaxis_transform(),
            color=renk, fontsize=10, fontweight='bold',
            va='center')

    fig.savefig(buf, format='png', bbox_inches='tight',
                facecolor='#131722', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf


# ---------------------------------------------------------------
# ANA FONKSİYON
# ---------------------------------------------------------------
def analiz_et():
    print("📊 Hisse taraması başlıyor...")

    try:
        df_sheet = pd.read_csv(SHEET_URL)
        hisseler = df_sheet['Hisse'].dropna().unique()
        print(f"✅ {len(hisseler)} hisse taranacak: {list(hisseler)}")
    except Exception as e:
        print(f"❌ Google Sheets okunamadı: {e}")
        return

    bulunan = 0

    for hisse in hisseler:
        try:
            t_name = f"{hisse}.IS"
            print(f"  🔍 {hisse} analiz ediliyor...")

            # 1 yıllık günlük veri
            df = yf.Ticker(t_name).history(period="1y", interval="1d")
            if len(df) < 60:
                print(f"    ⚠️  Yeterli veri yok ({len(df)} mum)")
                continue

            # Pivot destek/direnç bul
            guclu_tepeler, guclu_dipler = pivot_noktalari_bul(
                df, pencere=5, min_dokunma=2, tolerans_pct=0.015
            )

            if not guclu_tepeler and not guclu_dipler:
                print(f"    ⚠️  Güçlü seviye bulunamadı")
                continue

            guncel_fiyat = df['Close'].iloc[-1]
            degisim_pct = (df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100

            # Alış bölgesi kontrolü
            alis, alis_seviye, alis_guc, alis_uzaklik = alis_bolgesi_var_mi(
                df, guclu_dipler, tolerans_pct=0.025
            )

            # Satış bölgesi kontrolü
            satis, satis_seviye, satis_guc, satis_uzaklik = satis_bolgesi_var_mi(
                df, guclu_tepeler, tolerans_pct=0.025
            )

            if alis:
                print(f"    ✅ ALIŞ BÖLGESİ! Fiyat: {guncel_fiyat:.2f} | Destek: {alis_seviye:.2f} | Güç: {alis_guc}")
                buf = grafik_olustur(df, hisse, guclu_tepeler, guclu_dipler, 'ALIS', alis_seviye)

                destek_str = " | ".join([f"{s:.2f}({g}x)" for s, g in guclu_dipler[:3]])
                direnc_str = " | ".join([f"{s:.2f}({g}x)" for s, g in guclu_tepeler[:3]])

                msg = (
                    f"🟢 *ALIŞ BÖLGESİ SİNYALİ*\n"
                    f"📊 *Hisse:* `{hisse}`\n"
                    f"💰 *Fiyat:* {guncel_fiyat:.2f} TL  ({degisim_pct:+.2f}%)\n"
                    f"🎯 *Destek Bölgesi:* {alis_seviye:.2f} TL  (Güç: {alis_guc}x)\n"
                    f"📏 *Seviyeye Uzaklık:* %{alis_uzaklik:.1f}\n"
                    f"🟢 *Destek Seviyeleri:* {destek_str}\n"
                    f"🔴 *Direnç Seviyeleri:* {direnc_str}"
                )

                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                    files={'photo': buf},
                    data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'}
                )
                bulunan += 1

            elif satis:
                print(f"    🔴 SATIŞ BÖLGESİ! Fiyat: {guncel_fiyat:.2f} | Direnç: {satis_seviye:.2f} | Güç: {satis_guc}")
                buf = grafik_olustur(df, hisse, guclu_tepeler, guclu_dipler, 'SATIS', satis_seviye)

                destek_str = " | ".join([f"{s:.2f}({g}x)" for s, g in guclu_dipler[:3]])
                direnc_str = " | ".join([f"{s:.2f}({g}x)" for s, g in guclu_tepeler[:3]])

                msg = (
                    f"🔴 *SATIŞ BÖLGESİ SİNYALİ*\n"
                    f"📊 *Hisse:* `{hisse}`\n"
                    f"💰 *Fiyat:* {guncel_fiyat:.2f} TL  ({degisim_pct:+.2f}%)\n"
                    f"🎯 *Direnç Bölgesi:* {satis_seviye:.2f} TL  (Güç: {satis_guc}x)\n"
                    f"📏 *Seviyeye Uzaklık:* %{satis_uzaklik:.1f}\n"
                    f"🟢 *Destek Seviyeleri:* {destek_str}\n"
                    f"🔴 *Direnç Seviyeleri:* {direnc_str}"
                )

                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                    files={'photo': buf},
                    data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'}
                )
                bulunan += 1
            else:
                print(f"    ➖ Sinyal yok. Fiyat: {guncel_fiyat:.2f}")

        except Exception as e:
            print(f"    ❌ {hisse} hatası: {e}")
            continue

    print(f"\n✅ Tarama tamamlandı. {bulunan} sinyal bulundu.")

    if bulunan == 0:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={'chat_id': CHAT_ID,
                  'text': "📊 Tarama tamamlandı. Şu an destek/direnç bölgesinde hisse bulunamadı.",
                  'parse_mode': 'Markdown'}
        )


if __name__ == "__main__":
    analiz_et()
