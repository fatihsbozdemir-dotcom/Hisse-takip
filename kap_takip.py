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
    clean = href.strip("/")
    parts = clean.split("/")
    if len(parts) >= 2:
        return parts[-2].replace("-", " ").title()
    return ""


def fetch_haberler():
    tum_haberler = []
    seen_ids = set()

    for sayfa in range(1, 4):
        url = "https://uzmanpara.milliyet.com.tr/kap-haberleri/" if sayfa == 1 else f"https://uzmanpara.milliyet.com.tr/kap-haberleri/?page={sayfa}"

        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break

            soup = BeautifulSoup(r.text, "html.parser")
            sayfa_haber = 0

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "kap-haberi" not in href:
                    continue

                parts = href.strip("/").split("/")
                haber_id = parts[-1] if parts else ""
                if not haber_id or haber_id in seen_ids:
                    continue
                seen_ids.add(haber_id)

                hisse  = link.get_text(strip=True)
                baslik = url_to_baslik(href)
                full_url = href if href.startswith("http") else f"https://uzmanpara.milliyet.com.tr{href}"

                tum_haberler.append({
                    "id": haber_id,
                    "hisse": hisse,
                    "baslik": baslik,
                    "link": full_url
                })
                sayfa_haber += 1

            print(f"[SAYFA {sayfa}] {sayfa_haber} haber")
            if sayfa_haber == 0:
                break

        except Exception as e:
            print(f"[HATA] {e}")
            break

    print(f"[TOPLAM] {len(tum_haberler)} haber bulundu")
    return tum_haberler


def run():
    print(f"[BASLADI] {datetime.now().strftime('%H:%M:%S')}")
    sent_ids = load_sent_ids()
    print(f"[ONCEKI] {len(sent_ids)} haber daha once goruldu")
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
        link     = haber["link"]

        if haber_id in sent_ids:
            print(f"[ZATEN GORULDU] {baslik}")
            continue

        baslik_norm = normalize(baslik)
        eslesti = any(k in baslik_norm or baslik_norm in k for k in konular_norm)

        if eslesti:
            mesaj = (
                f"📢 <b>KAP BİLDİRİM</b>\n\n"
                f"🏷 <b>{hisse}</b>\n"
                f"📌 {baslik}\n"
                f"🔗 <a href='{link}'>Haberi Görüntüle</a>"
            )
            send_message(mesaj)
            yeni += 1
            print(f"[GONDERILDI] {hisse} - {baslik}")

        sent_ids.add(haber_id)

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
