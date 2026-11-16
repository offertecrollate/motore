"""
Demo senza account: simula 30 giorni di feed (un negozio svizzero in stile Awin
e Amazon.de), poi al giorno 31 inserisce un errore di prezzo e un'offerta.
Stampa i post (Svizzera -> WhatsApp, Italia -> Telegram) e genera il sito in demo_out/site (pagina iniziale con le bandiere).

    python demo.py
"""
import csv
import os
import random
import shutil
from datetime import date, timedelta

from engine.run import run_country

OUT = "demo_out"
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)

SHOP = [  # id, nome, prezzo normale
    ("1001", "Apple AirPods Pro (2. Gen.)", 229.0),
    ("1002", "Samsung Galaxy Tab S9 128GB", 699.0),
    ("1003", "Dyson V15 Detect Absolute", 749.0),
    ("1004", "Sony WH-1000XM5", 329.0),
    ("1005", "Cavo USB-C 1m", 9.9),
]
AMAZON = [("B0TEST0001", "LEGO Technic Ferrari Daytona SP3", 349.0),
          ("B0TEST0002", "Kindle Paperwhite 16GB", 159.0)]
AMAZON_IT = [("B0TEST0003", "De'Longhi Magnifica S", 399.0),
             ("B0TEST0004", "Nintendo Switch OLED", 319.0)]

# prezzi di oggi (giorno 31): errore su Dyson, offerta su Sony, errore su LEGO,
# errore finto sul cavo (escluso perché costa meno di 20)
TODAY_SHOP = {"1003": 199.0, "1004": 199.0, "1005": 1.0}
TODAY_AMZ = {"B0TEST0001": 119.0}
TODAY_AMZ_IT = {"B0TEST0003": 129.0}   # errore su Amazon.it: va su WhatsApp CH e Telegram IT


def write_shop(path, prices):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["aw_product_id", "product_name", "search_price", "rrp_price", "aw_deep_link",
                    "merchant_image_url", "currency", "merchant_category", "ean", "merchant_name"])
        for pid, name, price in prices:
            w.writerow([pid, name, f"{price:.2f}", "", f"https://www.awin1.com/cread.php?p={pid}&demo=1",
                        IMGS.get(pid, ""), "CHF", "Elektronik", "", "MediaMarkt CH"])


def write_amz(path, prices):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["asin", "name", "price", "old_price", "image"])
        for asin, name, price in prices:
            w.writerow([asin, name, f"{price:.2f}", "", IMGS.get(asin, "")])


shop_file, amz_file = f"{OUT}/feed_shop.csv", f"{OUT}/amazon_de.csv"
amz_it_file = f"{OUT}/amazon_it.csv"
RULES = {"history_days": 30, "min_history": 7, "offer_pct": 30, "error_pct": 60,
         "min_price": 20, "trust_old_price": False, "repost_after_days": 7,
         "max_posts_per_run": 5}
cfg = {
    "database": f"{OUT}/prezzi.db",
    "site": {"out_dir": f"{OUT}/site", "countries": {
        "it": {"langs": ["it"], "sections": [
            {"id": "amazon", "name": {"it": "Amazon"}, "sources": ["amazon_it"]}]},
        "ch": {"langs": ["it", "de", "fr"], "sections": [
            {"id": "amazon", "name": {"it": "Amazon", "de": "Amazon", "fr": "Amazon"},
             "sources": ["amazon_it", "amazon_de", "amazon_fr"]},
            {"id": "elettronica", "name": {"it": "Elettronica e informatica",
             "de": "Elektronik und Informatik", "fr": "Électronique et informatique"},
             "sources": ["awin_mediamarkt_ch"]}]},
    }},
    "countries": {
        "ch": {"rules": RULES, "sources": [
            {"name": "awin_mediamarkt_ch", "type": "feed", "preset": "awin", "file": shop_file},
            {"name": "amazon_de", "type": "amazon_list", "tag": "demo-de-21", "file": amz_file},
            {"name": "amazon_it", "type": "amazon_list", "tag": "demo-it-21", "file": amz_it_file},
        ], "publishers": [{"type": "console", "lang": "it", "label": "WhatsApp Svizzera"}]},
        "it": {"rules": RULES, "sources": [
            {"name": "amazon_it", "type": "amazon_list", "tag": "demo-it-21", "file": amz_it_file},
        ], "publishers": [{"type": "console", "lang": "it", "label": "Telegram Italia"}]},
    },
}

# immagini segnaposto per la demo (nel sito vero le foto arrivano dai feed dei negozi)
from PIL import Image, ImageDraw, ImageFont
IMG_DIR = f"{OUT}/site/demo-img"
os.makedirs(IMG_DIR, exist_ok=True)
def placeholder(pid, name):
    im = Image.new("RGB", (600, 450), "#ffffff"); dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((150, 90, 450, 300), 28, fill="#f3e6e4", outline="#e2cbc8", width=4)
    dr.ellipse((265, 160, 335, 230), outline="#c9a9a5", width=6)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except OSError: f = ImageFont.load_default()
    w = dr.textlength(name, font=f); dr.text(((600 - w) / 2, 340), name, fill="#7b5f5c", font=f)
    dr.text((205, 385), "foto di esempio", fill="#b49894", font=f)
    im.save(f"{IMG_DIR}/{pid}.png")
    return f"../demo-img/{pid}.png"
IMGS = {}
for pid, name, _ in SHOP + AMAZON + AMAZON_IT:
    IMGS[pid] = placeholder(pid, name[:30])

# dati del gestore per la pagina Info e privacy, se presenti nel config privato
try:
    import yaml
    cfg["site"]["owner"] = yaml.safe_load(open("config.yaml"))["site"]["owner"]
except Exception:
    pass

random.seed(1)
start = date.today() - timedelta(days=30)
for i in range(30):  # 30 giorni di prezzi normali con piccole oscillazioni
    day = start + timedelta(days=i)
    write_shop(shop_file, [(p, n, v * random.uniform(0.95, 1.03)) for p, n, v in SHOP])
    write_amz(amz_file, [(a, n, v * random.uniform(0.93, 1.02)) for a, n, v in AMAZON])
    write_amz(amz_it_file, [(a, n, v * random.uniform(0.95, 1.02)) for a, n, v in AMAZON_IT])
    run_country(cfg, "ch", dry_run=True, today=day)
    run_country(cfg, "it", dry_run=True, today=day)

print("\n================ GIORNO 31: OGGI ================")
write_shop(shop_file, [(p, n, TODAY_SHOP.get(p, v)) for p, n, v in SHOP])
write_amz(amz_file, [(a, n, TODAY_AMZ.get(a, v)) for a, n, v in AMAZON])
write_amz(amz_it_file, [(a, n, TODAY_AMZ_IT.get(a, v)) for a, n, v in AMAZON_IT])
ch = run_country(cfg, "ch", dry_run=True, today=date.today())
it = run_country(cfg, "it", dry_run=True, today=date.today())
print(f"\nWhatsApp Svizzera: {len(ch)} post, Telegram Italia: {len(it)} post.")
print(f"Sito di prova: {OUT}/site/index.html")
