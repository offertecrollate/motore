"""Elenca i cataloghi (feed) Awin disponibili: inserzionista, Feed ID, lingua, numero prodotti, stato.
Non stampa gli indirizzi di download (contengono la chiave)."""
import csv, io, sys, requests, yaml
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
lst = next(s["awin_list"] for c in cfg["countries"].values() for s in c["sources"] if s.get("awin_list"))
r = requests.get(lst, timeout=60); r.raise_for_status()
want = set(sys.argv[1:])
rows = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
print("colonne:", list(rows[0].keys()) if rows else [], "righe:", len(rows))
for row in rows:
    vals = " ".join(str(v) for k, v in row.items() if k != "URL")
    if not want or any(w in vals.split() or w.lower() in vals.lower() for w in want):
        print({k: v for k, v in row.items() if k != "URL"})
