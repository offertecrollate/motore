"""Pubblica a mano alcune offerte già sul sito: su Telegram e sulla pagina Facebook, con la card,
più l'avviso privato a Giuseppe (link al post e link da copiare) per condividerle nel gruppo.

    python -m tools.pubblica_scelte <chiave> [<chiave> ...]

Le offerte senza link affiliato escono senza #ADV (non sono pubblicità)."""
import json
import sys

import yaml

from engine import run
from engine.cards import make_card
from engine.models import Deal, Product
from engine.publishers import build_publisher
from engine.texts import flags_for

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
AFF = ("awin", "amazon", "tradedoubler")
deals = {"it": json.load(open("site_it/deals.json", encoding="utf-8")),
         "ch": json.load(open("site_ch/deals.json", encoding="utf-8"))}
# canali: la pagina Facebook e il canale Telegram sono gli stessi per Italia e Svizzera
pubs = {p["type"]: p for c in cfg["countries"].values() for p in c["publishers"]}
for key in sys.argv[1:]:
    country, x = next((c, x) for c, lst in deals.items() for x in lst if x["key"] == key)
    src, pid = key.split(":", 1)
    p = Product(source=src, product_id=pid, name=x["name"], price=x["price"], currency=x["currency"],
                shop=x["shop"], url=x["url"], image=x.get("image"), old_price=x.get("ref"))
    d = Deal(p, x["ref"], x["pct"], x.get("level", "offerta"), 0, extra={"flags": flags_for(country, src)})
    d.extra["card"] = make_card(d, "it")
    aff = src.startswith(AFF)
    site = "https://offertecrollate.it" if country == "it" else "https://offertecrollate.ch"
    for typ in ("facebook_page", "telegram"):
        pc = dict(pubs[typ], post_tag=pubs[typ].get("post_tag", "") if aff else "", site_url=site)
        pub = build_publisher(pc)
        ref = pub.send(d)
        if ref and ref[0] == "post":
            d.extra["fb_post"] = ref[1]
        print(typ, "ok", key)
    run._avviso_privato(cfg, d, country)
    print("avviso privato ok", key)
