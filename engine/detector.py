"""Trova errori di prezzo e offerte forti confrontando il prezzo di oggi con lo storico."""
from datetime import date
from statistics import median
from typing import Iterable, List

from .db import PriceDB
from .models import Deal, Product


def find_deals(db: PriceDB, products: Iterable[Product], rules: dict,
               today: date = None) -> List[Deal]:
    """
    rules (dal config):
      history_days:   giorni di storico da guardare (es. 30)
      min_history:    giorni minimi di storico per giudicare (es. 7)
      offer_pct:      sconto minimo per "offerta" (es. 30)
      error_pct:      sconto minimo per "errore di prezzo" (es. 60)
      min_price:      prezzo di riferimento minimo, evita accessori da 2 franchi (es. 20)
      trust_old_price: se True usa anche il prezzo barrato del negozio quando manca lo storico
    """
    today = today or date.today()
    deals = []
    for p in products:
        hist = db.history(p.key, before=today, days=rules["history_days"])
        ref = None
        if len(hist) >= rules["min_history"]:
            ref = median(hist)
        elif (rules.get("trust_old_price") or p.source in rules.get("trust_sources", ())) and p.old_price and p.old_price > p.price:
            ref = p.old_price
        if not ref or ref < rules["min_price"] or p.price <= 0:
            continue
        pct = (1 - p.price / ref) * 100
        if pct >= rules["error_pct"]:
            level = "errore"
        elif pct >= rules["offer_pct"]:
            level = "offerta"
        else:
            continue
        deals.append(Deal(p, round(ref, 2), round(pct, 1), level, len(hist)))
    # prima gli errori più forti
    deals.sort(key=lambda d: (d.level != "errore", -d.discount_pct))
    return deals
