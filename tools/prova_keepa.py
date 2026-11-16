"""Mostra le offerte Amazon che Keepa darebbe al motore, senza pubblicare nulla."""
import yaml
from engine.sources import build_source
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
for c in cfg["countries"].values():
    for s in c["sources"]:
        if s.get("type") == "keepa":
            ps = build_source(s).fetch()
            print(s["name"], len(ps), "prodotti")
            for p in sorted(ps, key=lambda p: p.price / p.old_price)[:25]:
                print(f"  -{(1 - p.price / p.old_price) * 100:.0f}%  {p.price:>8.2f} (media {p.old_price:.2f})  {p.name[:70]}")
