"""Prodotti di elettronica più venduti su Amazon.it in offerta adesso (per il video promozionale).
Prezzo e prezzo barrato come li mostra Amazon (buy box + saving basis)."""
import json, os, requests
key = os.environ["KEEPA_KEY"].strip()
API = "https://api.keepa.com"
cand = []
imgs_d = {}
for cat in (412609031, 425916031):          # Elettronica, Informatica
    for page in range(2):
        sel = {"page": page, "domainId": 8, "priceTypes": [0], "deltaPercentRange": [15, 100],
               "currentRange": [1500, 300000], "includeCategories": [cat], "salesRankRange": [1, 3000],
               "isRangeEnabled": True, "singleVariation": True, "sortType": 3, "isOutOfStock": False,
               "hasReviews": True, "minRating": 40, "filterErotic": True, "dateRange": 1}
        j = requests.get(f"{API}/deal", params={"key": key, "selection": json.dumps(sel)}, timeout=60).json()
        dr = (j.get("deals") or {}).get("dr") or []
        print("cat", cat, "pagina", page, len(dr), "gettoni", j.get("tokensLeft"))
        for d in dr:
            cand.append(d["asin"])
            im = d.get("image")
            if isinstance(im, list):
                im = "".join(chr(x) for x in im)
            imgs_d[d["asin"]] = im
cand = list(dict.fromkeys(cand))[:60]
print("candidati", len(cand))
out = []
for i in range(0, len(cand), 30):
    j = requests.get(f"{API}/product", timeout=120, params={"key": key, "domain": 8, "asin": ",".join(cand[i:i+30]),
                     "stats": 1, "buybox": 1, "history": 0, "rating": 1}).json()
    print("prodotti", len(j.get("products") or []), "gettoni", j.get("tokensLeft"))
    for p in j.get("products") or []:
        s = p.get("stats") or {}
        bb, basis = s.get("buyBoxPrice"), s.get("buyBoxSavingBasis")
        img = imgs_d.get(p["asin"])
        rank = (s.get("current") or [None]*4)[3]
        print("  ", p["asin"], "bb", bb, "basis", basis, "img", bool(img), "rank", rank)
        if bb and basis and basis > bb > 0 and img:
            out.append({"asin": p["asin"], "title": p.get("title"), "price": bb/100, "ref": basis/100,
                        "pct": round((1-bb/basis)*100), "img": "https://m.media-amazon.com/images/I/" + img,
                        "rank": rank, "brand": p.get("brand")})
out.sort(key=lambda x: (x["rank"] or 10**9))
print("RISULTATO_JSON " + json.dumps(out, ensure_ascii=False))
