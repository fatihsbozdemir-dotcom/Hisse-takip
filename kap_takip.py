import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc")
CHAT_ID = "-1003838602845"
THREAD_ID = 18165

KONULAR = [
    "kamuyu aydinlatma platformu duyurusu",
    "halka arz islemlerinde sermaye piyasasi aracinin % 5 inden fazlasini satin alanlara iliskin bildirim",
    "finansal duran varlik edinimi",
    "pay alim satim bildirimi",
    "borsada islem goren tipe donusum duyurusu",
    "toptan alis satis islemi",
    "pay satis bilgi formu hakkinda",
    "borsada islem gormeyen tipe donusum duyurusu",
    "paylarin geri alinmasina iliskin bildirim",
    "pazar gecis basvurusu",
    "spk islem yasagi nedeniyle pay duyurusu",
]

SENT_FILE = "kap_sent_ids.json"


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
        "disable_web_page_preview": True
    })


def normalize(text):
    tr_map = str.maketrans(
        "çğıöşüÇĞİÖŞÜ",
        "cgiosuCGIOSU"
    )
    return text.translate(tr_map).lower().strip()


def fetch_kap():
    url = "https://www.kap.org.tr/tr/bildirim-sorgu"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Referer": "https://www.kap.org.tr/tr/",
    }

    try:
        r = requests.get(url, headers=headers, timeout=20)
        print(f"[KAP] Status: {r.status_code}")

        if r.status_code != 200:
            print(f"[HATA] HTTP {r.status_code}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        haberler = []

        # KAP bildirim satirlarini bul
        rows = soup.find_all("div", class_="w-clearfix w-inline-block notification-item")
        if not rows:
            rows = soup.find_all("tr")

        print(f"[KAP] {len(rows)} satir bulundu")

        for row in rows:
            try:
                # Sirket adi
                sirket_el = row.find(class_="notification-company") or row.find("td", class_="company")
                sirket = sirket_el.get_text(strip=True) if sirket_el else ""

                # Konu
                konu_el = row.find(class_="notification-subject") or row.find("td", class_="subject")
                konu = konu_el.get_text(strip=True) if konu_el else ""

                # Tarih
                tarih_el = row.find(class_="notification-date") or row.find("td", class_="date")
                tarih = tarih_el.get_text(strip=True) if tarih_el else ""

                # Link
                link_el = row.find("a", href=True)
                link = ""
                if link_el:
                    href = link_el["href"]
                    if href.startswith("/"):
                        link = f"https://www.kap.org.tr{href}"
                    else:
                        link = href

                # ID olarak link veya konu+sirket+tarih kombinasyonu kullan
                haber_id = link or f"{sirket}-{konu}-{tarih}"

                if sirket or konu:
                    haberler.append({
                        "id": haber_id,
                        "sirket": sirket,
                        "konu": konu,
                        "tarih": tarih,
                        "link": link
                    })

            except Exception as e:
                print(f"[HATA] Satir parse: {e}")
                continue

        return haberler

    except Exception as e:
        print(f"[HATA] KAP fetch: {e}")
        return []


def run():
    print(f"[BASLADI] {datetime.now().strftime('%H:%M:%S')}")
    sent_ids = load_sent_ids()
    haberler = fetch_kap()

    if not haberler:
        print("[UYARI] Haber alinamadi")
        return

    konular_norm = [normalize(k) for k in KONULAR]
    yeni = 0

    for haber in haberler:
        haber_id = haber["id"]
        konu     = haber["konu"]
        sirket   = haber["sirket"]
        tarih    = haber["tarih"]
        link     = haber["link"]

        if haber_id in sent_ids:
            continue

        konu_norm = normalize(konu)
        eslesti = any(k in konu_norm or konu_norm in k for k in konular_norm)

        if not eslesti:
            continue

        if link:
            mesaj = (
                f"📢 <b>KAP BİLDİRİM</b>\n\n"
                f"🏢 <b>{sirket}</b>\n"
                f"📌 {konu}\n"
                f"🕐 {tarih}\n"
                f"🔗 <a href='{link}'>Bildirimi Görüntüle</a>"
            )
        else:
            mesaj = (
                f"📢 <b>KAP BİLDİRİM</b>\n\n"
                f"🏢 <b>{sirket}</b>\n"
                f"📌 {konu}\n"
                f"🕐 {tarih}"
            )

        send_message(mesaj)
        sent_ids.add(haber_id)
        yeni += 1
        print(f"[GONDERILDI] {sirket} - {konu}")

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
