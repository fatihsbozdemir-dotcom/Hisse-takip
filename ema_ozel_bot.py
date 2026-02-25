import yfinance as yf
import pandas as pd
import requests
import mplfinance as mpf
import io

TELEGRAM_TOKEN = "8550118582:AAHftKsl1xCuHvGccq7oPN-QcYULJ5_UVHw"
CHAT_ID = "8599240314"
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def mesaj_gonder(metin):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': metin, 'parse_mode': 'Markdown'})

def fotograf_gonder(foto_bayt, aciklama):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto_bayt, 'image/png')}
    data = {'chat_id': CHAT_ID, 'caption': aciklama, 'parse_mode': 'Markdown'}
    requests.post(url, files=files, data=data)

def veri_cek(hisse):
    try:
        df = yf.download(hisse, period="60d", interval="1h", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.empty or len(df) < 4:
            raise ValueError("Yetersiz 1H veri")
        df.index = pd.to_datetime(df.index)
        df_4h = df.resample('4h').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        return df_4h
    except Exception:
        df = yf.download(hisse, period="1y", interval="1d", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

def analiz_yap():
    try:
        df_sheet = pd.read_csv(SHEET_URL)
        df_sheet.columns = df_sheet.columns.str.strip()
        hisseler = df_sheet['Hisse'].dropna().tolist()

        found_count = 0
        mesaj_gonder(f"🔍 *4H EMA 89 Taraması Başladı...* ({len(hisseler)} hisse)")

        for hisse in hisseler:
            try:
                df = veri_cek(hisse)

                if df is None or len(df) < 90:
                    continue

                df['EMA55'] = df['Close'].ewm(span=55, adjust=False).mean()
                df['EMA89'] = df['Close'].ewm(span=89, adjust=False).mean()

                son_fiyat = float(df['Close'].iloc[-1])
                e89 = float(df['EMA89'].iloc[-1])
                e55 = float(df['EMA55'].iloc[-1])

                if e89 == 0:
                    continue

                mesafe = abs(son_fiyat - e89) / e89
                limit = 0.03  # %3 tolerans

                # Fiyat EMA89 üzerinde, EMA55 > EMA89 (trend yukarı) ve yakın
                if mesafe <= limit and son_fiyat >= e89 and e55 > e89:
                    found_count += 1

                    apds = [
                        mpf.make_addplot(df['EMA89'].tail(80), color='purple', width=2.0),
                        mpf.make_addplot(df['EMA55'].tail(80), color='orange', width=1.5),
                    ]

                    buf = io.BytesIO()
                    mc = mpf.make_marketcolors(up='#26a69a', down='#ef5350', inherit=True)
                    s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--', y_on_right=True)

                    mpf.plot(df.tail(80), type='candle', style=s, addplot=apds,
                             title=f"\n{hisse} - EMA 89 Desteği",
                             savefig=dict(fname=buf, format='png', bbox_inches='tight'))
                    buf.seek(0)

                    mesaj = (f"🎯 *EMA 89 DESTEK SİNYALİ*\n\n"
                             f"🏢 *Hisse:* {hisse}\n"
                             f"💰 *Fiyat:* {son_fiyat:.2f}\n"
                             f"🟣 *EMA 89:* {e89:.2f}\n"
                             f"🟠 *EMA 55:* {e55:.2f}\n"
                             f"📉 *Mesafe:* %{mesafe*100:.2f}")

                    fotograf_gonder(buf, mesaj)

            except Exception as e:
                print(f"HATA [{hisse}]: {e}")
                continue

        mesaj_gonder(f"✅ Tarama bitti. {found_count} uygun hisse bulundu.")

    except Exception as e:
        mesaj_gonder(f"❌ Sistem Hatası: {str(e)}")

if __name__ == "__main__":
    analiz_yap()
