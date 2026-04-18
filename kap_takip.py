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

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9",
}


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
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return text.translate(tr_map).lower().strip()


def fetch_haberler():
    url = "https://uzmanpara.milliyet.com.tr/kap-haberleri/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"[UZMANPARA] Status: {r.status_code}")

        if r.status_code != 200:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        haberler = []

        # Tum linkleri tara
        links = soup.find_all("a", href=True)
        print(f"[LINKLER] {len(links)} adet link bulundu")

        for link in links:
            href = link["href"]
            if "kap-haberi" not in href:
                continue

            baslik = link.get_text(strip=True)
            if not baslik or len(baslik) < 5:
                continue

            # ID al
            haber_id = href.split("/")[-2] if href.endswith("/") else href.split("/")[-1]

            if href.startswith("http"):
                full_url = href
            else:
                full_url = f"https://uzmanpara.milliyet.com.tr{href}"

            # Parent'tan tarih bul
            parent = link.parent
            tarih = ""
            if parent:
                tarih_el = parent.find(class_=lambda c: c and "date" in c.lower()) if parent else None
                if tarih_el:
                    tarih = tarih_el.get_text(strip=True)

            haberler.append({
                "id": haber_id,
                "baslik": baslik,
                "tarih": tarih,
                "link": full_url
            })

        # Tekrarlari temizle
        seen = set()
        unique = []
        for h in haberler:
            if h["id"] not in seen:
                seen.add(h["id"])
                unique.append(h)

        print(f"[HABERLER] {len(unique)} benzersiz haber")
        if unique:
            print(f"[ORNEK] {unique[0]}")
        return unique

    except Exception as e:
        print(f"[HATA] {e}")
        return []


def run():
    print(f"[BASLADI] {datetime.now().strftime('%H:%M:%S')}")
    sent_ids = load_sent_ids()
    haberler = fetch_haberler()

    if not haberler:
        print("[UYARI] Haber alinamadi")
        return

    konular_norm = [normalize(k) for k in KONULAR]
    yeni = 0

    for haber in haberler:
        haber_id = haber["id"]
        baslik   = haber["baslik"]
        tarih    = haber["tarih"]
        link     = haber["link"]

        if haber_id in sent_ids:
            continue

        baslik_norm = normalize(baslik)
        eslesti = any(k in baslik_norm or baslik_norm in k for k in konular_norm)

        if not eslesti:
            continue

        mesaj = (
            f"📢 <b>KAP BİLDİRİM</b>\n\n"
            f"📌 {baslik}\n"
            f"🕐 {tarih}\n"
            f"🔗 <a href='{link}'>Haberi Görüntüle</a>"
        )

        send_message(mesaj)
        sent_ids.add(haber_id)
        yeni += 1
        print(f"[GONDERILDI] {baslik[:60]}")

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
