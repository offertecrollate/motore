"""Cancella da Telegram e Facebook i post DOPPI: per ogni offerta e canale tiene il più recente
e cancella quelli più vecchi. Stampa l'esito di ogni cancellazione.

    python -m tools.pulisci_doppioni           # cancella
    python -m tools.pulisci_doppioni --prova   # mostra soltanto
"""
import sys
import time

import requests
import yaml

from engine.db import PriceDB

prova = "--prova" in sys.argv
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
db = PriceDB(cfg.get("database", "prezzi.db"))
tg = next(p for p in cfg["countries"]["it"]["publishers"] if p["type"] == "telegram")
fb = next(p for c in cfg["countries"].values() for p in c["publishers"] if p["type"] == "facebook_page")
api = fb.get("api_version", "v27.0")

rows = db.conn.execute("""SELECT rowid, key, channel, ref FROM messages m WHERE ended_at IS NULL AND EXISTS (
    SELECT 1 FROM messages n WHERE n.key=m.key AND substr(n.channel,1,8)=substr(m.channel,1,8)
    AND n.ended_at IS NULL AND n.posted_at>m.posted_at)""").fetchall()
print(f"Doppioni vecchi da cancellare: {len(rows)}")
ok = ko = 0
for rowid, key, channel, ref in rows:
    if prova:
        print("cancellerei", channel, ref, key)
        continue
    if channel.startswith("Telegram"):
        r = requests.post(f"https://api.telegram.org/bot{tg['bot_token']}/deleteMessage", timeout=30,
                          data={"chat_id": tg["chat_id"], "message_id": ref})
        gone = r.ok or "message to delete not found" in r.text
    else:
        r = requests.delete(f"https://graph.facebook.com/{api}/{ref}", timeout=30,
                            params={"access_token": fb["page_token"]})
        gone = r.ok or "does not exist" in r.text
    print("CANCELLATO" if gone else f"ERRORE {r.status_code} {r.text[:160]}", channel, ref)
    if gone:
        ok += 1
        db.conn.execute("DELETE FROM messages WHERE rowid=?", (rowid,))
        db.conn.commit()
    else:
        ko += 1
    time.sleep(1)
print(f"Cancellati: {ok}  Non riusciti: {ko}")
sys.exit(1 if ko else 0)
