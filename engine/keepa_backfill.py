"""
Storico prezzi Amazon da Keepa (OPZIONALE, a pagamento: da 49 €/mese).

SPENTO di default. Si attiva mettendo nel config:

    keepa:
      api_key: "LA_TUA_CHIAVE"

Quando il motore vede per la prima volta un prodotto Amazon (meno di
`min_history` giorni di storico), chiede a Keepa lo storico e lo salva nel
database: il grafico e il calcolo degli sconti partono subito con i prezzi vecchi.
Ogni prodotto costa 1 token Keepa, e viene chiesto una volta sola.
"""
import logging
from datetime import datetime, timezone
from typing import Iterable

import requests

from .db import PriceDB
from .models import Product

log = logging.getLogger("errori-prezzo")

KEEPA_DOMAIN = {"amazon_de": 3, "amazon_fr": 4, "amazon_it": 8}
KEEPA_EPOCH_MIN = 21564000          # i tempi Keepa sono minuti dal 2011-01-01


def _keepa_day(keepa_min: int) -> str:
    ts = (keepa_min + KEEPA_EPOCH_MIN) * 60
    return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def backfill(db: PriceDB, products: Iterable[Product], api_key: str, min_history: int,
             max_per_run: int = 50) -> int:
    done = 0
    for p in products:
        if done >= max_per_run:
            break
        domain = KEEPA_DOMAIN.get(p.source)
        if not domain or db.days_known(p.key) >= min_history or db.backfilled(p.key):
            continue
        try:
            r = requests.get("https://api.keepa.com/product", timeout=60, params={
                "key": api_key, "domain": domain, "asin": p.product_id, "history": 1, "days": 120})
            r.raise_for_status()
            prods = r.json().get("products") or []
        except Exception as e:
            log.error("Keepa %s: %s", p.product_id, e)
            continue
        csv = (prods[0].get("csv") if prods else None) or []
        # serie 0 = prezzo venduto da Amazon; se manca, serie 1 = nuovo da terzi
        series = next((s for s in (csv[0] if len(csv) > 0 else None,
                                   csv[1] if len(csv) > 1 else None) if s), [])
        days = {}
        for i in range(0, len(series) - 1, 2):
            t, cents = series[i], series[i + 1]
            if cents and cents > 0:                 # -1 = non disponibile
                d = _keepa_day(t)
                days[d] = min(days.get(d, cents / 100), cents / 100)
        db.import_history(p.key, days)
        db.mark_backfilled(p.key)
        done += 1
        log.info("Keepa: %s, %d giorni importati", p.product_id, len(days))
    return done


def _median90(csv) -> "float | None":
    """Prezzo mediano degli ultimi 90 giorni pesato sul tempo (prezzo Amazon; se manca, nuovo da terzi),
    come il "Prezzo mediano" mostrato da Amazon."""
    import time
    now = int(time.time() / 60) - 21564000          # minuti Keepa
    start = now - 90 * 24 * 60
    for idx in (0, 1):
        s = csv[idx] if len(csv) > idx and csv[idx] else []
        pts = [(s[i], s[i + 1]) for i in range(0, len(s) - 1, 2)]
        if not pts:
            continue
        dur = {}
        for k, (t, c) in enumerate(pts):
            t0 = max(t, start)
            t1 = pts[k + 1][0] if k + 1 < len(pts) else now
            if t1 <= start or c is None or c < 0:
                continue
            dur[c] = dur.get(c, 0) + max(0, t1 - t0)
        tot = sum(dur.values())
        if tot <= 0:
            continue
        acc = 0
        for c in sorted(dur):
            acc += dur[c]
            if acc >= tot / 2:
                return round(c / 100, 2)
    return None


def ratings(products: Iterable[Product], api_key: str) -> dict:
    """Stelle e numero di recensioni Amazon (Keepa, serie 16 e 17) per i pochi prodotti da pubblicare.
    Una sola chiamata per dominio; costa circa 1-2 gettoni a prodotto. Restituisce {asin: (stelle, recensioni, prezzo mediano 90 gg)}."""
    out, by_dom = {}, {}
    for p in products:
        dom = KEEPA_DOMAIN.get(p.source)
        if dom:
            by_dom.setdefault(dom, []).append(p.product_id)
    for dom, asins in by_dom.items():
        try:
            r = requests.get("https://api.keepa.com/product", timeout=60, params={
                "key": api_key, "domain": dom, "asin": ",".join(asins[:20]), "rating": 1, "history": 1, "days": 90})
            r.raise_for_status()
            for pr in r.json().get("products") or []:
                csv = pr.get("csv") or []
                def last(i):
                    s = csv[i] if len(csv) > i and csv[i] else []
                    vals = [v for v in s[1::2] if isinstance(v, int) and v >= 0]
                    return vals[-1] if vals else None
                rt, cnt = last(16), last(17)
                out[pr.get("asin")] = ((rt / 10) if rt else None, cnt or 0, _median90(csv))
        except Exception as e:
            log.error("Keepa stelle: %s", e)
    return out
