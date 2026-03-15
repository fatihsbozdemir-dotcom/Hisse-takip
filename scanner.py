import pandas as pd
import yfinance as yf
import requests
import matplotlib.pyplot as plt

# TELEGRAM
TELEGRAM_TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "8599240314"

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

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
        data={"chat_id": CHAT_ID, "caption": f"📊 Yatay aday: {symbol}\nSapma: %{round(ratio*100,2)}"},
        files=files
    )

def get_bist_symbols():
    url = "https://www.kap.org.tr/tr/api/company/companies"
    data = pd.read_json(url)

    symbols = data["stockCode"].dropna().unique().tolist()
    symbols = [s + ".IS" for s in symbols]  # yfinance formatı
    symbols = list(set(symbols))            # tekrarları sil

    return symbols

def sideways(symbol):
    data = yf.download(symbol, period="2mo", interval="1d")

    if len(data) < 20:
        return False, data, 0

    last = data.tail(20)

    mean_price = last["Close"].mean()
    std_price = last["Close"].std()

    ratio = std_price / mean_price

    if ratio < 0.025:   # %2.5 sapma → yatay kabul
        return True, data, ratio

    return False, data, ratio

def run():
    send_message("🚀 BIST taraması başladı")

    symbols = get_bist_symbols()

    send_message(f"📊 {len(symbols)} hisse taranacak")

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
        send_message("⚠️ Uygun yatay hisse bulunamadı")
    else:
        send_message(f"✅ Tarama tamamlandı. {found} yatay hisse bulundu")

run()
