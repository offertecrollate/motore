import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import live_amazon as L
L.KEY = os.environ["KEEPA_KEY"].strip()
q = sys.argv[1] if len(sys.argv) > 1 else "cuffie bluetooth"
r = L.keepa("search", {"domain": 8, "type": "product", "term": q, "page": 0, "stats": 90, "rating": 1})
for raw in r.get("products") or []:
    x = L.prodotto(raw, "it")
    cats = L._norm(" ".join(c.get("name", "") for c in (raw.get("categoryTree") or [])))
    print(x["prezzo"], round(L.pertinenza(x, q, cats), 2), x["nome"][:80], "|", cats[-60:])
r = L.cerca(q)
print(json.dumps(r, ensure_ascii=False, indent=1)[:3000])
json.dump(r, open("risultato.json", "w"), ensure_ascii=False)
