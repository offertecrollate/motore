import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import live_amazon as L
L.KEY = os.environ["KEEPA_KEY"].strip()
r = L.cerca(sys.argv[1] if len(sys.argv) > 1 else "cuffie bluetooth")
print(json.dumps(r, ensure_ascii=False, indent=1)[:6000])
json.dump(r, open("risultato.json", "w"), ensure_ascii=False)
