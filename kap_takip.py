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
    today = datetime.now().strftime("%d-%m-%Y")

    endpoints = [
        # Isyatirim KAP haberleri
        f"https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/KapHaber?tarih={today}.json",
        f"https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/SirketHaberleri?tarih={today}.json",
        "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/KapHaberler.json",
        # Bigpara
        "https://bigpara.hurriyet.com.tr/api/kaphaberler/",
        "https://bigpara.hurriyet.com.tr/api/v1/kaphaberler/",
        # Doviz.com
        "https://www.doviz.com/api/v1/stock/news",
    ]

    for url in endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            print(f"[TEST] {url[:60]} -> {r.status_code}")
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"[BASARILI] len:{len(data) if isinstance(data, list) else 'dict'}")
                    print(f"[ORNEK] {str(data)[:200]}")
                    return data, url
                except Exception:
                    print(f"[JSON HATASI] {r.text[:100]}")
        except Exception as e:
            print(f"[HATA] {url[:60]}: {str(e)[:50]}")

    return [], None


def normalize(text):
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return text.translate(tr_map).lower().strip()


def run():
    print(f"[BASLADI] {datetime.now().strftime('%H:%M:%S')}")
    sent_ids = load_sent_ids()

    data, url = fetch_haberler()

    if not data:
        print("[UYARI] Hic endpoint calismadi")
        send_message("⚠️ KAP haber kaynagina erisilemedl, kontrol gerekiyor.")
        return

    konular_norm = [normalize(k) for k in KONULAR]
    haberler = data if isinstance(data, list) else []

    # dict ise icindeki listeyi bul
    if isinstance(data, dict):
        for key in ["value", "data", "items", "result", "haberler"]:
            if key in data and isinstance(data[key], list):
                haberler = data[key]
                break

    print(f"[HABERLER] {len(haberler)} adet")
    yeni = 0

    for haber in haberler[:100]:
        try:
            haber_id = str(
                haber.get("id") or haber.get("ID") or
                haber.get("disclosureIndex") or
                haber.get("index") or ""
            )
            konu = (
                haber.get("subject") or haber.get("SUBJECT") or
                haber.get("konu") or haber.get("KONU") or
                haber.get("baslik") or haber.get("BASLIK") or
                haber.get("title") or haber.get("TITLE") or ""
            )
            sirket = (
                haber.get("title") or haber.get("TITLE") or
                haber.get("companyName") or
                haber.get("sirket") or haber.get("SIRKET") or
                haber.get("member") or ""
            )
            tarih = (
                haber.get("publishDate") or haber.get("PUBLISHDATE") or
                haber.get("tarih") or haber.get("TARIH") or
                haber.get("date") or ""
            )

            if not haber_id:
                haber_id = f"{sirket}-{konu}-{tarih}"

            if haber_id in sent_ids:
                continue

            konu_norm = normalize(konu)
            eslesti = any(k in konu_norm or konu_norm in k for k in konular_norm)

            if not eslesti:
                continue

            link_id = haber.get("disclosureIndex") or haber.get("id") or haber.get("ID") or ""
            kap_link = f"https://www.kap.org.tr/tr/Bildirim/{link_id}" if link_id else "https://www.kap.org.tr"

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
            print(f"[HATA] {e}")

    save_sent_ids(sent_ids)
    print(f"[BITTI] {yeni} yeni haber gonderildi")


run()
