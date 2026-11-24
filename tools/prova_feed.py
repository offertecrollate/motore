"""Diagnostica: quali colonne del catalogo Awin di un negozio sono piene (prime 3000 righe)."""
import csv, gzip, io, os, sys, requests
sys.path.insert(0, ".")
from engine.sources.feed import awin_feed_url
adv = os.environ.get("ADV", "9423")
lista = f"https://ui.awin.com/productdata-darwin-download/publisher/3152592/{os.environ['AWIN_FEED_KEY'].strip()}/1/feedList"
url = awin_feed_url(lista, None, adv)
print("colonne richieste:", url.split("/columns/")[1].split("/")[0] if "/columns/" in url else "?")
r = requests.get(url, stream=True, timeout=300)
f = io.TextIOWrapper(gzip.GzipFile(fileobj=r.raw), encoding="utf-8", errors="replace")
rd = csv.DictReader(f)
piene, n, esempi = {}, 0, []
for row in rd:
    n += 1
    for k, v in row.items():
        if v and str(v).strip():
            piene[k] = piene.get(k, 0) + 1
    if n <= 3:
        esempi.append({k: (v or "")[:60] for k, v in row.items() if v})
    try:
        pz, ol = float(row.get("search_price") or 0), float(row.get("product_price_old") or 0)
        if ol > pz > 0:
            sc = (1 - pz / ol) * 100
            piene["_sconto>=30"] = piene.get("_sconto>=30", 0) + (sc >= 30)
            piene["_sconto>0"] = piene.get("_sconto>0", 0) + 1
    except ValueError:
        pass
    if n >= 50000:
        break
print("righe lette:", n)
for k in sorted(piene, key=lambda k: -piene[k]):
    print(f"{k}: {piene[k]}")
for e in esempi:
    print(e)
