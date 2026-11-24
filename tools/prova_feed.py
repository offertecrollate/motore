"""Diagnostica catalogo Awin: tipi di prodotto e prezzi (Mondadori)."""
import csv, gzip, io, os, sys, collections, requests
sys.path.insert(0, ".")
from engine.sources.feed import awin_feed_url
adv = os.environ.get("ADV", "9423")
lista = f"https://ui.awin.com/productdata-darwin-download/publisher/3152592/{os.environ['AWIN_FEED_KEY'].strip()}/1/feedList"
r = requests.get(awin_feed_url(lista, None, adv), stream=True, timeout=600)
f = io.TextIOWrapper(gzip.GzipFile(fileobj=r.raw), encoding="utf-8", errors="replace")
tipi, sopra15, n = collections.Counter(), collections.Counter(), 0
esempi = collections.defaultdict(list)
for row in csv.DictReader(f):
    n += 1
    t = (row.get("product_type") or "").strip()
    tipi[t] += 1
    try:
        if float(row.get("search_price") or 0) >= 15:
            sopra15[t] += 1
    except ValueError:
        pass
    if len(esempi[t]) < 2:
        esempi[t].append((row.get("product_name") or "")[:50] + " | " + (row.get("search_price") or ""))
print("righe:", n)
for t, c in tipi.most_common(40):
    print(f"{c:>8} (>=15€ {sopra15[t]:>7})  {t[:70]}  ->  {esempi[t]}")
