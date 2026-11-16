"""Prova dell'avviso privato: prende un'offerta già pubblicata sulla pagina Facebook
e manda a Giuseppe nel bot il messaggio da inoltrare nel gruppo. Non pubblica nulla.

    python -m tools.prova_avviso [chiave_prodotto]
"""
import json
import sys

import requests
import yaml

from engine import run
from engine.cards import make_card
from engine.db import PriceDB
from engine.models import Deal, Product
from engine.texts import flags_for

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
db = PriceDB(cfg.get("database", "prezzi.db"))
key = sys.argv[1] if len(sys.argv) > 1 else "awin_acer_it:acer-nitro-gaming-mouse-ii-nero-gp-mce11-40"
country, ref = db.conn.execute(
    "SELECT country, ref FROM messages WHERE key=? AND channel LIKE 'Facebook%' ORDER BY rowid DESC LIMIT 1",
    (key,)).fetchone()
source, pid = key.split(":", 1)
x = next(x for x in json.load(open(f"site_{country}/deals.json", encoding="utf-8")) if x["key"].endswith(key))
p = Product(source=source, product_id=pid, name=x["name"], price=x["price"], currency=x["currency"],
            shop=x["shop"], url=x["url"], image=x.get("image"))
d = Deal(p, x["ref"], x["pct"], x.get("level", "offerta"), 0, extra={"flags": flags_for(country, source)})
d.extra["card"] = make_card(d, "it")
fb = next(q for c in cfg["countries"].values() for q in c["publishers"] if q["type"] == "facebook_page")
r = requests.get(f"https://graph.facebook.com/{fb.get('api_version', 'v27.0')}/{ref}", timeout=30,
                 params={"fields": "permalink_url", "access_token": fb["page_token"]}).json()
d.extra["fb_post"] = ref
d.extra["fb_link"] = r.get("permalink_url", "")
print("post:", d.extra["fb_link"] or r)
run._avviso_privato(cfg, d, country)
print("avviso mandato")
