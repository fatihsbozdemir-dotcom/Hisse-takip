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


def url_to_baslik(href):
    """URL'den okunabilir baslik cikar
    ornek: katilim-finansi-ilkeleri-bilgi-formu -> Katilim Finansi Ilkeleri Bilgi Formu
    """
    # Son ID kismini at, baslik kismini al
    parts = href.strip("/").split("/")
    # kap-haberi/BASLIK/ID formatinda
    if len(parts) >= 2:
        baslik_slug = parts[-2]  # ID'den once gelen kisim
        baslik = baslik_slug.replace("-", " ").title()
        return baslik
    return ""


def fetch_haberler():
    url = "https://uzmanpara.milliyet.com.tr/kap-haberleri/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"[UZMANPARA] Status: {r.status_code}")

        if r.status_code != 200:
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        haberler = []
        seen_ids = set()

        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"]
            if "kap-haberi" not in href:
                continue

            # ID - URL'nin son parcasi
            clean = href.strip("/")
            parts = clean.split("/")
            haber_id = parts[-1] if parts else ""

            if not haber_id or haber_id in seen_ids:
                continue
            seen_ids.add(haber_id)

            # Hisse kodu - link metni
            hisse = link.get_text(strip=True)

            # Baslik - URL'den
            baslik = url_to_baslik(href)

            # Tarih - parent elementten
            tarih = ""
            parent = link.find_parent()
            if parent:
                siblings = parent.find_all(string=True)
                for s in siblings:
                    s = s.strip()
                    if len(s) == 19 and "." in s and ":" in s:
                        tarih = s
                        break

            # Tam URL
            if href.startswith("http"):
                full_url = href
            else:
                full_url = f"https://uzmanpara.milliyet.com.tr{href}"

            haberler.append({
                "id": haber_id,
                "hisse": hisse,
                "baslik": baslik,
                "baslik_slug": url_to_baslik(href).lower(),
                "tarih": tarih,
                "link": full_url
            })

        print(f"[HABERLER] {len(haberler)} haber bulundu")
        if haberler:
            print(f"[ORNEK] hisse:{haberler[0]['hisse']} baslik:{haberler[0]['baslik']}")
        return haberler

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
        hisse    = haber["hisse"]
        tarih    = haber["tarih"]
        link     = haber["link"]

        if haber_id in sent_ids:
            continue

        baslik_norm = normalize(baslik)
        eslesti = any(k in baslik_norm or baslik_norm in k for k in konular_norm)

        if eslesti:
            mesaj = (
                f"📢 <b>KAP BİLDİRİM</b>\n\n"
                f"🏷 <b>{hisse}</b>\n"
                f"📌 {baslik}\n"
                f"🕐 {tarih}\n"
                f"🔗 <a href='{link}'>Haberi Görüntüle</a>"
            )
            send_message(mesaj)
            yeni += 1
            print(f"[GONDERILDI] {hisse} - {baslik}")

        # Goruldugu isaretlenmis olsun (eslesmese de)
        sent_ids.add(haber_id)

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
