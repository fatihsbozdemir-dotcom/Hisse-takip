import pandas as pd
import yfinance as yf
import requests
import matplotlib.pyplot as plt

# TELEGRAM
TELEGRAM_TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"

# GOOGLE SHEET
SHEET_ID = "12I44srsajllDeCP6QJ9mvn4p2tO6ElPgw002x2F4yoA"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


def send_message(text):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )


def get_symbols():

    df = pd.read_csv(SHEET_URL)

    symbols = df.iloc[:,0].dropna().tolist()

    return symbols


def sideways(symbol):

    data = yf.download(symbol, period="3mo", interval="1d")

    if len(data) < 40:
        return False, data

    last = data.tail(30)

    highest = last["High"].max()
    lowest = last["Low"].min()

    # fiyat aralığı
    range_percent = (highest - lowest) / lowest * 100

    # trend kontrolü
    first_price = last["Close"].iloc[0]
    last_price = last["Close"].iloc[-1]

    trend_percent = abs(last_price - first_price) / first_price * 100

    # gerçek yatay şartı
    if range_percent < 10 and trend_percent < 4:

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
            "caption": f"📊 Yatay konsolidasyon: {symbol}"
        },
        files=files
    )


def run():

    send_message("🚀 Yatay konsolidasyon taraması başladı")

    symbols = get_symbols()

    send_message(f"🔎 Toplam {len(symbols)} hisse taranacak")

    found = 0

    for s in symbols:

        try:

            signal, data = sideways(s)

            if signal:

                found += 1

                send_chart(s, data)

        except Exception as e:

            print("Hata:", s, e)

    if found == 0:

        send_message("❗ Yatay konsolidasyon bulunamadı")

    else:

        send_message(f"✅ Tarama tamamlandı. {found} yatay hisse bulundu")


run()
