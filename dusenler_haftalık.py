import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io
import schedule
import time
import datetime

# --- Ayarlar (Senin Bilgilerin) ---
TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def mesaj_gonder(metin):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': metin, 'parse_mode': 'Markdown'})
    except Exception as e:
        print(f"Mesaj hatası: {e}")

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, files=files, data=data)
    except Exception as e:
        print(f"Fotoğraf hatası: {e}")

def veri_cek(hisse):
    try:
        # 7 günlük periyodu kontrol etmek için günlük (1d) veri şarttır
        df = yf.download(hisse, period="60d", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

def yedi_gun_seri_dususte_mi(df):
    """Son 7 kapanışın her birinin bir önceki günden düşük olduğunu doğrular."""
    if len(df) < 8:
        return False
    
    son_donem = df['Close'].tail(8).tolist()
    
    # Döngü ile her günün bir önceki günden küçük olup olmadığını kontrol et
    for i in range(1, 8):
        if son_donem[i] >= son_donem[i-1]:
            return False
    return True

def analiz_yap():
    try:
        # Başlangıç bildirimi
        simdi = datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
        mesaj_gonder(f"🔍 *HAFTALIK TARAMA BAŞLADI*\n\n"
                     f"📅 *Tarih:* {simdi}\n"
                     f"📋 *Kriter:* 7 İş Günü Aralıksız Düşüş")

        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisseler = df_sheet['Hisse'].dropna().tolist()

        found_count = 0

        for hisse in hisseler:
            try:
                df = veri_cek(hisse)
                if df is None or df.empty:
                    continue

                if yedi_gun_seri_dususte_mi(df):
                    found_count += 1
                    son_fiyat = float(df['Close'].iloc[-1])
                    ilk_fiyat = float(df['Close'].iloc[-7])
                    degisim = ((son_fiyat / ilk_fiyat) - 1) * 100

                    # Grafik oluşturma (Sadece mumlar)
                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s  = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)
                    
                    mpf.plot(df.tail(25), type='candle', style=s,
                             title=f"\n{hisse} - 7 Gunluk Seri Dusus",
                             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                    buf.seek(0)

                    aciklama = (f"⚠️ *SERİ DÜŞÜŞ SİNYALİ
