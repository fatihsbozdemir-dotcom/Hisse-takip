import requests
import json
import os
import hashlib
from datetime import datetime

# --- AYARLAR ---
# Token'ı buraya yapıştırabilirsin ama güvenlik için os.environ tavsiye edilir
TELEGRAM_TOKEN = "8550118582:AAHvXNPU7DW-QlOc4_XFRTfji-gYXCNchMc"
CHAT_ID = "-1003838602845"
THREAD_ID = 18165
SENT_FILE = "kap_sent_ids.json"

# Filtrelemek istediğin anahtar kelimeler (Küçük harf ve Türkçe karaktersiz)
KONULAR = [
    "kamuyu aydinlatma platformu duyurusu",
    "halka arz",
    "sermaye piyasasi araci",
    "finansal duran varlik edinimi",
    "pay alim satim bildirimi",
    "borsada islem goren tipe donusum",
    "toptan alis satis",
    "paylarin geri alinmasi",
    "pazar gecis basvurusu",
    "islem yasagi",
    "ozel durum aciklamasi"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.isyatirim.com.tr",
    "Referer": "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/kap-haberleri.aspx"
}

def normalize(text):
    if not text: return ""
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return text.translate(tr_map).lower().strip()

def load_sent_ids():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_sent_ids(ids):
    with open(SENT_FILE, "w") as f:
        json.dump(list(ids), f)

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "message_thread_id": THREAD_ID,
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Telegram Hatası: {e}")
        return False

def fetch_haberler():
    today = datetime.now().strftime("%d-%m-%Y")
    # İş Yatırım'ın en güncel veri sağlayan endpoint'i
    url = f"https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/KapHaber?tarih={today}"
    
    try:
        print(f"🔄 Veri çekiliyor: {url}")
        r = requests.get(url, headers=HEADERS, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            # İş Yatırım veriyi 'value' anahtarı içinde liste olarak gönderir
            haberler = data.get("value", [])
            print(f"✅ {len(haberler)} adet ham haber bulundu.")
            return haberler
        else:
            print(f"⚠️ Site hatası: {r.status_code}")
    except Exception as e:
        print(f"❌ Veri çekme hatası: {e}")
    return []

def run():
    print(f"🚀 Bot Başlatıldı: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    sent_ids = load_sent_ids()
    haberler = fetch_haberler()
    
    if not haberler:
        print("ℹ️ İşlenecek yeni haber yok.")
        return

    konular_norm = [normalize(k) for k in KONULAR]
    yeni_sayac = 0

    for haber in haberler:
        # Veri alanlarını güvenli alalım
        sirket = (haber.get("title") or "").strip()
        konu = (haber.get("subject") or "").strip()
        tarih = haber.get("publishDate") or ""
        link_id = haber.get("disclosureIndex") or ""

        # Benzersiz ID oluşturma (Aynı haberin tekrar gitmemesi için)
        unique_id = hashlib.md5(f"{sirket}{konu}{link_id}".encode('utf
