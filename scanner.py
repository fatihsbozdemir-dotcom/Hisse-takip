import pandas as pd
import yfinance as yf
import requests
import matplotlib.pyplot as plt

TELEGRAM_TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"

SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})


def get_symbols():
    df = pd.read_csv(SHEET_URL)
    return df.iloc[:,0].dropna().tolist()


def sideways(symbol):

    data = yf.download(symbol, period="2mo", interval="1d")

    if len(data) < 20:
        return False, data, 0

    last = data.tail(20)

    high = last["High"].max()
    low = last["Low"].min()

    range_percent = (high - low) / low * 100

    first = last["Close"].iloc[0]
    last_price = last["Close"].iloc[-1]

    trend = abs(last_price - first) / first * 100

    if range_percent < 15 and trend < 8:
        return True, data, range_percent

    return False, data, range_percent


def send_chart(symbol, data, range_percent):

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
            "caption": f"📊 Yatay aday: {symbol}\nRange: %{round(range_percent,2)}"
        },
        files=files
    )


def run():

    send_message("🚀 Yatay hisse taraması başladı")

    symbols = get_symbols()

    send_message(f"🔎 {len(symbols)} hisse kontrol ediliyor")

    found = 0

    for s in symbols:

        try:

            signal, data, r = sideways(s)

            if signal:
                found += 1
                send_chart(s, data, r)

        except Exception as e:
            print("Hata:", s, e)

    if found == 0:
        send_message("⚠️ Uygun yatay hisse bulunamadı (filtre dar olabilir)")
    else:
        send_message(f"✅ Tarama bitti. {found} yatay aday bulundu")


run()
