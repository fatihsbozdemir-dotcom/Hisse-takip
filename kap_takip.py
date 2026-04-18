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

STATE_FILE = "kap_state.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Referer": "https://www.kap.org.tr/tr/bildirim-sorgu",
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    # Baslangic ID - bugun civarindaki bir ID
    return {"last_id": 1500000}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


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


def get_latest_id():
    """KAP ana sayfasından en son bildirim ID'sini bul"""
    try:
        url = "https://www.kap.org.tr/tr/api/disclosuresSummary/gunluk"
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"[LATEST ID API] {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                ids = [d.get("disclosureIndex", 0) for d in data if d.get("disclosureIndex")]
                if ids:
                    return max(ids)
    except Exception as e:
        print(f"[LATEST ID HATA] {e}")

    return None


def fetch_bildirim(bildirim_id):
    """Tek bir bildirimi cek ve parse et"""
    url = f"https://www.kap.org.tr/tr/Bildirim/{bildirim_id}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Baslik
        baslik = ""
        baslik_el = soup.find("h1") or soup.find(class_="disclosure-title") or soup.find(class_="title")
        if baslik_el:
            baslik = baslik_el.get_text(strip=True)

        # Sirket adi
        sirket = ""
        sirket_el = soup.find(class_="company-name") or soup.find(class_="member-name")
        if sirket_el:
            sirket = sirket_el.get_text(strip=True)

        # Konu/tip
        konu = ""
        konu_el = soup.find(class_="disclosure-type") or soup.find(class_="subject")
        if konu_el:
            konu = konu_el.get_text(strip=True)

        # Tarih
        tarih = ""
        tarih_el = soup.find(class_="publish-date") or soup.find(class_="date")
        if tarih_el:
            tarih = tarih_el.get_text(strip=True)

        # Eger baslik yoksa title tag'inden al
        if not baslik:
            title_tag = soup.find("title")
            if title_tag:
                baslik = title_tag.get_text(strip=True)

        return {
            "id": bildirim_id,
            "baslik": baslik,
            "sirket": sirket,
            "konu": konu,
            "tarih": tarih,
            "link": url
        }

    except Exception as e:
        print(f"[BILDIRIM HATA] {bildirim_id}: {e}")
        return None


def find_current_max_id():
    """Binary search ile gecerli max ID'yi bul"""
    # Bilinen bir aralik ile baslayalim
    test_ids = [1500000, 1510000, 1520000, 1530000, 1540000, 1550000]
    last_valid = 1500000

    for tid in test_ids:
        url = f"https://www.kap.org.tr/tr/Bildirim/{tid}"
        try:
            r = requests.head(url, headers=HEADERS, timeout=5)
            if r.status_code == 200:
                last_valid = tid
            else:
                break
        except:
            break

    return last_valid


def run():
    print(f"[BASLADI] {datetime.now().strftime('%H:%M:%S')}")
    state = load_state()
    last_id = state.get("last_id", 1500000)

    print(f"[SON ID] {last_id}")

    konular_norm = [normalize(k) for k in KONULAR]
    yeni = 0
    kontrol_edilen = 0
    max_kontrol = 50  # Her calishmada max 50 bildirim kontrol et

    current_id = last_id + 1
    bos_sayac = 0

    while kontrol_edilen < max_kontrol:
        bildirim = fetch_bildirim(current_id)

        if bildirim is None:
            bos_sayac += 1
            if bos_sayac > 10:
                print(f"[BITTI] 10 bos bildirim, duruyorum. Son ID: {current_id}")
                break
        else:
            bos_sayac = 0
            last_id = current_id

            # Konu filtresi
            baslik_norm = normalize(bildirim["baslik"])
            konu_norm   = normalize(bildirim["konu"])
            eslesti = any(
                k in baslik_norm or baslik_norm in k or
                k in konu_norm   or konu_norm in k
                for k in konular_norm
            )

            if eslesti:
                mesaj = (
                    f"📢 <b>KAP BİLDİRİM</b>\n\n"
                    f"🏢 <b>{bildirim['sirket']}</b>\n"
                    f"📌 {bildirim['baslik']}\n"
                    f"🕐 {bildirim['tarih']}\n"
                    f"🔗 <a href='{bildirim['link']}'>Bildirimi Görüntüle</a>"
                )
                send_message(mesaj)
                yeni += 1
                print(f"[GONDERILDI] {bildirim['sirket']} - {bildirim['baslik'][:50]}")

            kontrol_edilen += 1

        current_id += 1

    state["last_id"] = last_id
    save_state(state)
    print(f"[BITTI] {kontrol_edilen} bildirim kontrol edildi, {yeni} gonderildi, son ID: {last_id}")


run()
