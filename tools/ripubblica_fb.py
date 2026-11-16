"""Ripubblica sulla pagina Facebook le offerte ancora attive pubblicate PRIMA di un certo momento
(es. quando l'app Facebook era ancora "in sviluppo" e i post li vedeva solo l'amministratore).

    python -m tools.ripubblica_fb 2026-11-15T18:15 [max]

Solo Facebook: niente Telegram, niente avvisi privati. Il vecchio post resta (lo vede solo l'amministratore);
nel registro viene chiuso e sostituito da quello nuovo, così la chiusura "offerta terminata" tocca il post giusto.
Pausa tra un post e l'altro per non sembrare spam."""
import json
import sys
import time

import yaml

from engine.cards import make_card
from engine.db import PriceDB
from engine.models import Deal, Product
from engine.publishers import build_publisher
from engine.texts import flags_for

cutoff = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 40
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
db = PriceDB(cfg.get("database", "prezzi.db"))
AFF = ("awin", "amazon", "tradedoubler")
deals = {"it": {x["key"]: x for x in json.load(open("site_it/deals.json", encoding="utf-8"))},
         "ch": {x["key"]: x for x in json.load(open("site_ch/deals.json", encoding="utf-8"))}}
fbconf = {k: next(p for p in c["publishers"] if p["type"] == "facebook_page") for k, c in cfg["countries"].items()}

done, fatti = set(), 0
for country in ("it", "ch"):
    msgs = [m for m in db.open_messages(country, days=14) if m["channel"].lower().startswith("facebook")]
    rows = db.conn.execute("SELECT rowid, posted_at FROM messages").fetchall()
    when = dict(rows)
    msgs = [m for m in msgs if when.get(m["id"], "") < cutoff]
    msgs.sort(key=lambda m: when.get(m["id"], ""), reverse=True)        # prima le più recenti
    for m in msgs:
        if fatti >= limit:
            break
        x = deals[country].get(m["key"])
        if not x or m["key"] in done:
            continue                                     # offerta non più attiva o già rifatta
        src, pid = m["key"].split(":", 1)
        if x.get("category") == "adulti" or src.startswith("awin_sedusia"):
            continue                                     # mai contenuti per adulti su Facebook
        p = Product(source=src, product_id=pid, name=x["name"], price=x["price"], currency=x["currency"],
                    shop=x["shop"], url=x["url"], image=x.get("image"), old_price=x.get("ref"))
        d = Deal(p, x["ref"], x["pct"], x.get("level", "offerta"), 0, extra={"flags": flags_for(country, src)})
        d.extra["card"] = make_card(d, "it")
        site = "https://offertecrollate.it" if country == "it" else "https://offertecrollate.ch"
        pc = dict(fbconf[country], post_tag=fbconf[country].get("post_tag", "") if src.startswith(AFF) else "", site_url=site)
        pub = build_publisher(pc)
        try:
            ref = pub.send(d)
        except Exception as e:
            print("ERRORE", m["key"], e)
            continue
        if ref:
            db.end_message(m["id"])
            db.save_message(m["key"], country, pub.label, ref[0], ref[1], pub.last_text, x["price"],
                            ref[2] if len(ref) > 2 else "")
        done.add(m["key"])
        fatti += 1
        print("ripubblicata", country, m["key"])
        time.sleep(20)
print("totale ripubblicate:", fatti)
