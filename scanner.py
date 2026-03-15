import pandas as pd
import yfinance as yf
import requests
import matplotlib.pyplot as plt

TELEGRAM_TOKEN = "TOKEN"
CHAT_ID = "CHAT_ID"

SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


def get_symbols():

    df = pd.read_csv(SHEET_URL)

    return df["symbol"].dropna().tolist()


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

    plt.figure()
    plt.plot(data["Close"])
    plt.title(symbol)

    file = f"{symbol}.png"

    plt.savefig(file)
    plt.close()

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    files = {"photo": open(file, "rb")}

    requests.post(
        url,
        data={"chat_id": CHAT_ID, "caption": f"Yatay hisse bulundu: {symbol}"},
        files=files,
    )


symbols = get_symbols()

for s in symbols:

    signal, data = sideways(s)

    if signal:
        send_chart(s, data)
