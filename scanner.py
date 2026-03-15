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

    data = yf.download(symbol, period="2mo", interval="1d")

    if len(data) < 20:
        return False, data, 0

    last = data.tail(20)

    mean_price = last["Close"].mean()
    std_price = last["Close"].std()

    # yataylık oranı
    ratio = std_price / mean_price

    if ratio < 0.02:   # %2 sapma
        return True, data, ratio

    return False, data, ratio


def send_chart(symbol, data, ratio):

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
            "caption": f"📊 Yatay aday: {symbol}\nSapma: %{round(ratio*100,2)}"
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

            signal, data, ratio = sideways(s)

            if signal:

                found += 1

                send_chart(s, data, ratio)

        except Exception as e:

            print("Hata:", s, e)

    if found == 0:

        send_message("⚠️ Yatay hisse bulunamadı")

    else:

        send_message(f"✅ Tarama tamamlandı. {found} yatay hisse bulundu")


run()
