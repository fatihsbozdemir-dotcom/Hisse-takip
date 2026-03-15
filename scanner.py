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


def get_symbols():
    df = pd.read_csv(SHEET_URL)

    # ilk sütunu kullan
    symbols = df.iloc[:, 0].dropna().tolist()

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
            "caption": f"Yatay hisse bulundu: {symbol}"
        },
        files=files
    )


def run():

    symbols = get_symbols()

    print("Tarama başladı...")

    for s in symbols:

        try:

            signal, data = sideways(s)

            if signal:

                print("Bulundu:", s)

                send_chart(s, data)

        except:

            print("Hata:", s)


run()
