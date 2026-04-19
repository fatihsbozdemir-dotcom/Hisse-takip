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
    "genel kurul",
    "ozel durum",
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
        baslik_slug = parts[-2]
        baslik = baslik_slug.replace("-", " ").title()
        return baslik
    return ""


def fetch_haberler():
    # Birden fazla sayfa dene
    tum_haberler = []
    seen_ids = set()

    for sayfa in range(1, 4):  # 3 sayfa
        if sayfa == 1:
            url = "https://uzmanpara.milliyet.com.tr/kap-haberleri/"
        else:
            url = f"https://uzmanpara.milliyet.com.tr/kap-haberleri/?page={sayfa}"

        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            print(f"[SAYFA {sayfa}] Status: {r.status_code}")

            if r.status_code != 200:
                break

            soup = BeautifulSoup(r.text, "html.parser")
            links = soup.find_all("a", href=True)
            sayfa_haber = 0

            for link in links:
                href = link["href"]
                if "kap-haberi" not in href:
                    continue

                clean = href.strip("/")
                parts = clean.split("/")
                haber_id = parts[-1] if parts else ""

                if not haber_id or haber_id in seen_ids:
                    continue
                seen_ids.add(haber_id)

                hisse  = link.get_text(strip=True)
                baslik = url_to_baslik(href)

                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = f"https://uzmanpara.milliyet.com.tr{href}"

                # Tarih - parent'tan bul
                tarih = ""
                row = link.find_parent("tr") or link.find_parent("li") or link.find_parent("div")
                if row:
                    text_nodes = row.find_all(string=True)
                    for t in text_nodes:
                        t = t.strip()
                        if len(t) >= 8 and "." in t:
                            tarih = t
                            break

                tum_haberler.append({
                    "id": haber_id,
                    "hisse": hisse,
                    "baslik": baslik,
                    "tarih": tarih,
                    "link": full_url
                })
                sayfa_haber += 1

            print(f"[SAYFA {sayfa}] {sayfa_haber} haber")
            if sayfa_haber == 0:
                break

        except Exception as e:
            print(f"[HATA] Sayfa {sayfa}: {e}")
            break

    print(f"[TOPLAM] {len(tum_haberler)} haber")
    return tum_haberler


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
            sent_ids.add(haber_id)
            yeni += 1
            print(f"[GONDERILDI] {hisse} - {baslik}")
        else:
            # Eslesmeyeni de kaydet - bir daha bakma
            sent_ids.add(haber_id)
            print(f"[ATLANDI] {baslik}")

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
