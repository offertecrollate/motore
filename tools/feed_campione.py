"""Mostra le colonne di un catalogo Awin e quante righe hanno un prezzo "prima" più alto di quello di oggi.
    python -m tools.feed_campione <advertiser_id>"""
import csv, gzip, io, sys, requests, yaml
from engine.sources.feed import awin_feed_url
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
lst = next(s["awin_list"] for c in cfg["countries"].values() for s in c["sources"] if s.get("awin_list"))
url = awin_feed_url(lst, advertiser_id=sys.argv[1])
import re as _re
print("forma indirizzo:", _re.sub(r"apikey/[^/]+", "apikey/***", url))
extra = "rrp_price,product_price_old,store_price,base_price,saving,savings_percent,price_old"
if "/columns/" in url:
    url = _re.sub(r"(/columns/)([^/]+)", lambda m: m.group(1) + m.group(2) + "," + extra, url)
raw = requests.get(url, timeout=180).content
if raw[:2] == b"\x1f\x8b":
    raw = gzip.decompress(raw)
rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace"))))
print("colonne:", list(rows[0].keys()))
def n(v):
    try: return float(str(v).replace(",", "."))
    except Exception: return None
for col in rows[0].keys():
    if any(k in col.lower() for k in ("price", "rrp", "old", "saving", "discount")):
        vals = [n(r.get(col)) for r in rows]
        filled = sum(1 for v in vals if v)
        higher = sum(1 for r, v in zip(rows, vals) if v and n(r.get("search_price")) and v > n(r.get("search_price")) * 1.05)
        print(f"{col}: piene {filled}, più alte del prezzo di oggi {higher}")
for r in rows[:2]:
    print({k: (v[:60] if isinstance(v, str) else v) for k, v in r.items() if "link" not in k.lower() and "url" not in k.lower()})
