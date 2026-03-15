import pandas as pd
import yfinance as yf
import requests
import matplotlib.pyplot as plt

# TELEGRAM
TELEGRAM_TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "1003838602845"

# GOOGLE SHEET
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


def send_message(text):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text
            }
        )
    except:
        print("Telegram mesaj hatası")


def get_symbols():

    df = pd.read_csv(SHEET_URL)

    symbols = df.iloc[:,0].dropna().tolist()

    return symbols


def sideways(symbol):

    data = yf.download(symbol, period="3mo", interval="1d")

    if len(data) < 30:
        return False, data

    mean = data["Close"].rolling(20).mean()
    std = data["Close"].rolling(20).std()

    upper = mean + 2 * std
    lower = mean - 2 * std

    width = (upper - lower) / mean * 100

    if width.iloc[-1] < 6:
        return True, data

    return False, data


def send_chart(symbol, data):

    try:

        plt.figure(figsize=(8,4))
        plt.plot(data["Close"])
        plt.title(symbol)

        file = f"{symbol}.png"

        plt.savefig(file)
        plt.close()

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

        files = {"photo": open(file, "rb")}

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": f"📊 Yatay hisse bulundu: {symbol}"
            },
            files=files
        )

    except:
        print("Grafik gönderme hatası")


def run():

    send_message("🚀 Hisse taraması başladı")

    try:

        symbols = get_symbols()

        send_message(f"🔎 Toplam {len(symbols)} hisse taranacak")

        found = 0

        for s in symbols:

            try:

                signal, data = sideways(s)

                if signal:

                    found += 1

                    send_chart(s, data)

            except:

                print("Hata:", s)

        if found == 0:

            send_message("❗ Yatay hisse bulunamadı")

        else:

            send_message(f"✅ Tarama tamamlandı. {found} yatay hisse bulundu")

    except:

        send_message("❌ Tarama sırasında hata oluştu")


run()
