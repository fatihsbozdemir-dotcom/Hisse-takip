import requests
import json
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc")
CHAT_ID = "-1003838602845"
THREAD_ID = 18165

# Takip edilecek konu basiklari
KONULAR = [
    "Kamuyu Aydinlatma Platformu Duyurusu",
    "Halka Arz Islemlerinde Sermaye Piyasasi Aracinin % 5 inden Fazlasini Satin Alanlara Iliskin Bildirim",
    "Finansal Duran Varlik Edinimi",
    "Pay Alim Satim Bildirimi",
    "Borsada Islem Goren Tipe Donusum Duyurusu",
    "Toptan Alis Satis Islemi",
    "PAY SATIS BILGI FORMU HAKKINDA",
    "Borsada Islem Gormeyen Tipe Donusum Duyurusu",
    "Paylarin Geri Alinmasina Iliskin Bildirim",
    "Pazar Gecis Basvurusu",
    "SPK Islem Yasagi Nedeniyle Pay Duyurusu",
]

# Daha once gonderilen haberlerin ID lerini tut
SENT_FILE = "sent_ids.json"


def load_sent_ids():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_sent_ids(ids):
    with open(SENT_FILE, "w") as f:
        json.dump(list(ids), f)


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "message_thread_id": THREAD_ID,
        "disable_web_page_preview": False
    })


def normalize(text):
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosуCGIOSU")
    return text.translate(tr_map).lower().strip()


def fetch_kap():
    url = "https://www.kap.org.tr/tr/api/disclosures"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[HATA] KAP API: {e}")
    return []


def run():
    print("[BASLADI] KAP haber taramasi...")
    sent_ids = load_sent_ids()
    haberler = fetch_kap()

    if not haberler:
        print("[UYARI] Haber alinamadi")
        return

    yeni = 0
    konular_norm = [normalize(k) for k in KONULAR]

    for haber in haberler:
        try:
            haber_id   = str(haber.get("disclosureIndex", ""))
            baslik     = haber.get("subject", "") or haber.get("disclosureType", "")
            sirket     = haber.get("title", "") or haber.get("companyName", "")
            tarih      = haber.get("publishDate", "") or haber.get("disclosureDate", "")
            link_id    = haber.get("disclosureIndex", "")

            if haber_id in sent_ids:
                continue

            # Konu filtresi
            baslik_norm = normalize(baslik)
            eslesti = any(k in baslik_norm or baslik_norm in k for k in konular_norm)

            if not eslesti:
                continue

            # KAP linki
            kap_link = f"https://www.kap.org.tr/tr/Bildirim/{link_id}"

            mesaj = (
                f"📢 <b>KAP BİLDİRİM</b>\n\n"
                f"🏢 <b>{sirket}</b>\n"
                f"📌 {baslik}\n"
                f"🕐 {tarih}\n"
                f"🔗 <a href='{kap_link}'>Bildirimi Görüntüle</a>"
            )

            send_message(mesaj)
            sent_ids.add(haber_id)
            yeni += 1
            print(f"[GONDERILDI] {sirket} - {baslik}")

        except Exception as e:
            print(f"[HATA] Haber isleme: {e}")

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
