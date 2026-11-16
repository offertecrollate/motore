"""Pubblica su Telegram e Facebook le offerte scelte a mano (selezione/selezione.json),
con le immagini già pronte (selezione/card_N.jpg), e le registra nello storico così il motore
le chiude da solo quando il prezzo torna normale.

    python -m tools.pubblica_selezione            # pubblica
    python -m tools.pubblica_selezione --prova    # stampa soltanto
"""
import json
import sys
import time

import yaml

from engine.db import PriceDB
from engine.models import Deal, Product
from engine.publishers import build_publisher
from engine.texts import flags_for

prova = "--prova" in sys.argv
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
db = PriceDB(cfg.get("database", "prezzi.db"))
sel = json.load(open("selezione/selezione.json", encoding="utf-8"))


def publishers_for(country):
    pubs = [dict(p) for p in cfg["countries"][country]["publishers"]]
    if not any(p["type"] == "telegram" for p in pubs):     # un solo canale Telegram per IT e CH
        tg = next(dict(p) for p in cfg["countries"]["it"]["publishers"] if p["type"] == "telegram")
        fb = next((p for p in pubs if p["type"] == "facebook_page"), {})
        tg["label"] = "Telegram " + {"ch": "Svizzera"}.get(country, country)
        tg["site_url"] = fb.get("site_url", tg.get("site_url"))
        pubs.append(tg)
    if prova:
        pubs = [{"type": "console", "lang": p.get("lang", "it"), "label": p.get("label", p["type"]), "post_tag": p.get("post_tag", "")} for p in pubs]
    return [build_publisher(p) for p in pubs]


def cancella_vecchi():
    """--rifai: cancella da Telegram e Facebook i post già usciti per queste stesse offerte."""
    import requests
    tg = next(p for p in cfg["countries"]["it"]["publishers"] if p["type"] == "telegram")
    fb = next(p for c in cfg["countries"].values() for p in c["publishers"] if p["type"] == "facebook_page")
    keys = [f'{x["source"]}:{x["id"]}' for x in sel]
    rows = db.conn.execute(
        f"SELECT rowid, channel, ref FROM messages WHERE ended_at IS NULL AND key IN ({','.join('?' * len(keys))})",
        keys).fetchall()
    for rowid, channel, ref in rows:
        try:
            if prova:
                print("cancellerei", channel, ref)
                continue
            if channel.startswith("Telegram"):
                r = requests.post(f"https://api.telegram.org/bot{tg['bot_token']}/deleteMessage", timeout=30,
                                  data={"chat_id": tg["chat_id"], "message_id": ref})
            else:
                r = requests.delete(f"https://graph.facebook.com/{fb.get('api_version', 'v27.0')}/{ref}",
                                    timeout=30, params={"access_token": fb["page_token"]})
            print("CANCELLATO" if r.ok else f"NON CANCELLATO ({r.status_code} {r.text[:120]})", channel, ref)
            if r.ok:
                db.conn.execute("DELETE FROM messages WHERE rowid=?", (rowid,))
                db.conn.commit()
        except Exception as e:
            print("ERRORE cancellando", channel, ref, e)
        time.sleep(1)


if "--rifai" in sys.argv:
    cancella_vecchi()

ok = err = 0
for s in sel:
    prod = Product(source=s["source"], product_id=s["id"], name=s["name"], price=s["price"],
                   currency=s["currency"], shop=s["shop"], url=s["url"], image=s.get("image"))
    pct = round((1 - s["price"] / s["old"]) * 100, 1)
    deal = Deal(prod, s["old"], pct, s.get("level", "offerta"), 0,
                extra={"card": open("selezione/" + s["card"], "rb").read(),
                       "flags": flags_for(s["country"], s["source"])})
    if s.get("hook"):
        deal.extra["hook"] = s["hook"]
    for pub in publishers_for(s["country"]):
        try:
            ref = pub.send(deal)
            if ref and not prova:
                db.save_message(prod.key, s["country"], pub.label, ref[0], ref[1], pub.last_text,
                                prod.price, ref[2])
            ok += 1
            print(f"OK  {pub.label:22} {s['name'][:60]}")
        except Exception as e:
            err += 1
            print(f"ERR {pub.label:22} {s['name'][:60]}: {e}")
        time.sleep(3)
    if not prova:
        db.save([prod])
        db.mark_posted(prod.key, s["country"], prod.price)
print(f"\nPubblicati: {ok}  Errori: {err}")
sys.exit(1 if err else 0)
