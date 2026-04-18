import requests
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
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Referer": "https://www.kap.org.tr/tr/bildirim-sorgu",
    "X-Requested-With": "XMLHttpRequest",
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


def fetch_kap():
    # KAP'in gercek API endpoint leri
    endpoints = [
        "https://www.kap.org.tr/tr/api/disclosuresSummary",
        "https://www.kap.org.tr/tr/api/home/disclosures",
        "https://www.kap.org.tr/tr/api/disclosures/summary",
        "https://www.kap.org.tr/tr/api/bildirimler",
    ]

    for url in endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            print(f"[DENENIYOR] {url} -> {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"[BASARILI] {url} -> {type(data)} len:{len(data) if isinstance(data, list) else 'dict'}")
                print(f"[ORNEK] {str(data)[:300]}")
                return data, url
        except Exception as e:
            print(f"[HATA] {url}: {e}")

    # RSS ile dene
    try:
        rss_url = "https://www.kap.org.tr/rss/rss.aspx"
        r = requests.get(rss_url, headers=HEADERS, timeout=15)
        print(f"[RSS] {rss_url} -> {r.status_code}")
        if r.status_code == 200:
            print(f"[RSS ICERIK] {r.text[:500]}")
    except Exception as e:
        print(f"[RSS HATA] {e}")

    return [], None


def run():
    print(f"[BASLADI] {datetime.now().strftime('%H:%M:%S')}")
    sent_ids = load_sent_ids()

    data, url = fetch_kap()

    if not data:
        print("[UYARI] Haber alinamadi - tum endpointler basarisiz")
        return

    konular_norm = [normalize(k) for k in KONULAR]
    yeni = 0

    # data liste ise direkt isle
    haberler = data if isinstance(data, list) else data.get("data", data.get("items", data.get("result", [])))

    print(f"[HABERLER] {len(haberler)} adet")

    for haber in haberler[:50]:  # son 50 haber
        try:
            # Farkli field isimlerini dene
            haber_id = str(
                haber.get("disclosureIndex") or
                haber.get("id") or
                haber.get("bildiriIndex") or
                haber.get("index") or ""
            )
            konu = (
                haber.get("subject") or
                haber.get("disclosureType") or
                haber.get("konu") or
                haber.get("baslik") or ""
            )
            sirket = (
                haber.get("title") or
                haber.get("companyName") or
                haber.get("sirket") or
                haber.get("member") or ""
            )
            tarih = (
                haber.get("publishDate") or
                haber.get("disclosureDate") or
                haber.get("tarih") or ""
            )

            if not haber_id:
                haber_id = f"{sirket}-{konu}-{tarih}"

            if haber_id in sent_ids:
                continue

            konu_norm = normalize(konu)
            eslesti = any(k in konu_norm or konu_norm in k for k in konular_norm)

            if not eslesti:
                continue

            link_id = haber.get("disclosureIndex") or haber.get("id") or ""
            kap_link = f"https://www.kap.org.tr/tr/Bildirim/{link_id}" if link_id else "https://www.kap.org.tr/tr/bildirim-sorgu"

            mesaj = (
                f"📢 <b>KAP BİLDİRİM</b>\n\n"
                f"🏢 <b>{sirket}</b>\n"
                f"📌 {konu}\n"
                f"🕐 {tarih}\n"
                f"🔗 <a href='{kap_link}'>Bildirimi Görüntüle</a>"
            )

            send_message(mesaj)
            sent_ids.add(haber_id)
            yeni += 1
            print(f"[GONDERILDI] {sirket} - {konu}")

        except Exception as e:
            print(f"[HATA] Haber isleme: {e}")

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
