"""Offerte Amazon da Keepa (servizio a pagamento che segue i prezzi Amazon).

Usa l'elenco "deals" di Keepa: prodotti il cui prezzo è sceso rispetto alla media degli ultimi 90 giorni.
Il "prezzo prima" (old_price) è la media a 90 giorni di Keepa, quindi lo sconto è reale e non il prezzo
barrato del venditore. Il link porta ad Amazon con il codice affiliato.

    - name: amazon_it         # il nome deve iniziare con "amazon": niente grafico né prezzo barrato (regole Amazon)
      type: keepa
      api_key: ${KEEPA_KEY}
      domain: it                # it, de, fr
      tag: offertecrolla-21     # codice affiliato di quel Paese
      min_discount: 30          # sconto minimo sulla media a 90 giorni
      min_price: 15             # prezzo minimo in euro (niente accessori da 2 euro)
      pages: 2                  # pagine da 150 offerte (5 gettoni l'una)
"""
import json
import logging
import os
import time
from typing import List

import requests

from ..models import Product

log = logging.getLogger(__name__)
API = "https://api.keepa.com"
DOMAINS = {"de": (3, "amazon.de"), "fr": (4, "amazon.fr"), "it": (8, "amazon.it")}
PRICE_AMAZON, PRICE_NEW = 0, 1
# categorie principali escluse: libri, Kindle, musica, film (prezzi "medi" poco affidabili e poco interesse)
EXCLUDE = {"it": [411663031, 818937031, 412600031, 412606031, 433842031],
           "de": [186606, 530484031, 255882, 284266],
           "fr": [301061, 672108031, 301062, 405322]}          # tipi di prezzo Keepa: venduto da Amazon / nuovo da terzi


def _eur(v):
    return round(v / 100, 2) if isinstance(v, (int, float)) and v > 0 else None


def _media(st: dict, campo: str):
    """Prezzo medio del periodo (30/90/180 giorni) da Keepa: buy box, poi nuovo, poi Amazon."""
    arr = st.get(campo) or []
    for i in (18, 1, 0):
        if i < len(arr) and isinstance(arr[i], (int, float)) and arr[i] > 0:
            return arr[i] / 100
    return None


def _gonfiato(v: dict) -> bool:
    """Prezzo alzato prima dello sconto per farlo sembrare un affare. Dal 20/11/2026 (Giuseppe) il riferimento
    è il prezzo medio degli ultimi 60 giorni:
    - il prezzo di adesso deve essere almeno il 10% sotto la media dei 60 giorni (e dei 90/180 se c'è);
    - nell'ultimo mese il prezzo medio non deve essere salito oltre il 15% rispetto ai 60 giorni (rialzo recente);
    - per gli sconti forti (dal 50%) lo sconto vero rispetto ai 60 giorni deve essere almeno il 60%
      di quello dichiarato: un -70% che rispetto ai 60 giorni è solo -15% è un prezzo barrato gonfiato."""
    bb, a30, basis = v.get("bb"), v.get("a30"), v.get("basis")
    medie = [x for x in (v.get("a60"), v.get("a90"), v.get("a180")) if x]
    if not bb or not medie:
        return False
    rif = min(medie)
    if bb > rif * 0.90:
        return True
    if a30 and v.get("a60") and a30 > v["a60"] * 1.15:
        return True
    if basis and basis > bb:
        dichiarato = 1 - bb / basis
        vero = 1 - bb / rif
        if dichiarato >= 0.50 and vero < dichiarato * 0.60:
            return True
    return False


class KeepaSource:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.key = str(cfg.get("api_key") or "").strip()

    def fetch(self) -> List[Product]:
        if not self.key or self.key.startswith("$"):
            log.info("%s: chiave Keepa non ancora inserita, salto", self.cfg["name"])
            return []
        c = self.cfg
        dom_id, site = DOMAINS[c.get("domain", "it")]
        tag = c.get("tag", "")
        out, seen = [], set()
        # 1) prima le categorie che su Amazon vendono di più (decisione di Giuseppe del 16/11/2026):
        #    elettronica, PS5 e giochi, smartphone, iPad, monitor, TV grandi, carta igienica, merendine…
        #    solo prodotti molto venduti (classifica vendite alta), così niente "cazzate".
        for f in c.get("focus", []):
            sel = {"page": 0, "domainId": dom_id, "priceTypes": [PRICE_AMAZON],
                   "deltaPercentRange": [int(f.get("min_discount", c.get("min_discount", 30))), 100],
                   "currentRange": [int(float(f.get("min_price", 1)) * 100), 1000000],
                   "dateRange": 1, "isRangeEnabled": True, "isFilterEnabled": False, "filterErotic": True,
                   "singleVariation": True, "sortType": 3, "isOutOfStock": False,
                   "includeCategories": f["cats"], "salesRankRange": [1, int(f.get("max_rank", 20000))]}
            if f.get("title"):
                sel["titleSearch"] = f["title"]      # parola nel titolo (es. cioccolatini)
            try:
                r = requests.get(f"{API}/deal", params={"key": self.key, "selection": json.dumps(sel)}, timeout=60)
                if r.status_code == 429:
                    log.warning("%s: gettoni Keepa finiti per ora", c["name"]); break
                items = ((r.json().get("deals") or {}).get("dr") or [])
            except Exception as e:
                log.warning("%s: categoria %s non letta: %s", c["name"], f.get("name"), e); continue
            n0 = len(out)
            prima = len(out)
            self._aggiungi(items, out, seen, site, tag, dom_id, focus=True, gruppo=f.get("name", ""))
            if f.get("post_pct"):          # soglia diversa per Telegram/Facebook
                for p in out[prima:]:
                    p.post_pct = float(f["post_pct"])
            log.info("%s: categoria %s, %d candidati (%d trovati da Keepa)", c["name"], f.get("name"), len(out) - n0, len(items))
        # 2) poi tutte le altre offerte
        for page in range(int(c.get("pages", 2))):
            sel = {"page": page, "domainId": dom_id, "priceTypes": [PRICE_AMAZON],
                   "deltaPercentRange": [int(c.get("min_discount", 30)), 100],
                   "currentRange": [int(float(c.get("min_price", 15)) * 100), 1000000],
                   "dateRange": 0, "isRangeEnabled": True, "isFilterEnabled": False,
                   "filterErotic": True, "singleVariation": True, "sortType": 4,
                   "isOutOfStock": False}
            if c.get("quality", True):        # solo prodotti con recensioni, almeno 4 stelle, ben venduti
                sel.update({"hasReviews": True, "minRating": int(c.get("min_rating", 40)),
                            "salesRankRange": [1, int(c.get("max_sales_rank", 30000))]})
            if c.get("exclude_media", True):  # libri, Kindle, musica, film
                sel["excludeCategories"] = EXCLUDE.get(c.get("domain", "it"), [])
            r = requests.get(f"{API}/deal", params={"key": self.key, "selection": json.dumps(sel)}, timeout=60)
            if r.status_code == 429:
                log.warning("%s: gettoni Keepa finiti per ora", c["name"])
                break
            r.raise_for_status()
            data = r.json()
            items = (data.get("deals") or {}).get("dr") or []
            log.info("%s: pagina %d, %d offerte (gettoni rimasti %s)", c["name"], page, len(items), data.get("tokensLeft"))
            self._aggiungi(items, out, seen, site, tag, dom_id)
            if len(items) < 150:
                break
        if c.get("amazon_prices", True):
            out = self._prezzi_amazon(out, dom_id)
        return out

    def _aggiungi(self, items, out, seen, site, tag, dom_id, focus=False, gruppo=""):
        c = self.cfg
        for d in items:
            asin = d.get("asin")
            cur = d.get("current") or []
            price = _eur(cur[PRICE_AMAZON]) if len(cur) > PRICE_AMAZON else None
            avg = d.get("avg") or []
            avg90 = _eur(avg[3][PRICE_AMAZON]) if len(avg) > 3 and len(avg[3]) > PRICE_AMAZON else None
            if not asin or asin in seen or not price or not avg90 or avg90 <= price:
                continue
            if c.get("exclude_media", True) and d.get("rootCat") in EXCLUDE.get(c.get("domain", "it"), []):
                continue
            if (1 - price / avg90) * 100 > float(c.get("max_discount", 80)):   # oltre: di solito media gonfiata
                continue
            seen.add(asin)
            img = d.get("image")
            if isinstance(img, list):     # Keepa dà il nome dell'immagine come lista di codici carattere
                img = "".join(chr(x) for x in img)
            out.append(Product(
                source=c["name"], product_id=asin, name=(d.get("title") or asin)[:200],
                price=price, currency="EUR", shop=f"Amazon.{c.get('domain', 'it')}",
                url=f"https://www.{site}/dp/{asin}" + (f"?tag={tag}" if tag else ""),
                image=f"https://m.media-amazon.com/images/I/{img}" if img else None,
                old_price=avg90))
            if focus:
                out[-1].focus = True
                out[-1].gruppo = gruppo
            try:      # classifica vendite Amazon (più basso = più venduto)
                out[-1].rank = cur[3] if len(cur) > 3 and cur[3] and cur[3] > 0 else 10 ** 9
            except Exception:
                out[-1].rank = 10 ** 9

    def _prezzi_amazon(self, cands: List[Product], dom_id: int) -> List[Product]:
        """Prezzi come li vede chi apre Amazon (decisione di Giuseppe del 15/11/2026): prezzo in vetrina
        (buy box) e prezzo barrato mostrato da Amazon (saving basis: prezzo tipico/di listino/precedente).
        Keepa serve solo per trovare i candidati e per il grafico. Senza prezzo barrato su Amazon niente offerta.
        Costa 3 gettoni a prodotto: si controllano i più promettenti, con una cache di 1 ora condivisa
        tra Svizzera e Italia nello stesso giro."""
        c = self.cfg
        path = c.get("cache_file", "keepa_prezzi.json")
        try:
            cache = json.load(open(path, encoding="utf-8"))
        except Exception:
            cache = {}
        now = time.time()
        ttl = float(c.get("cache_hours", 1)) * 3600   # 19/11/2026: cache salvata tra i giri, così il sito accumula offerte
        cache = {k: v for k, v in cache.items() if now - v.get("t", 0) < ttl and v.get("v") == 4}
        # prima i più venduti (decisione di Giuseppe del 16/11/2026): classifica vendite Amazon più alta
        cands = sorted(cands, key=lambda p: (not getattr(p, "focus", False), getattr(p, "rank", 10 ** 9)))
        cands_tutti = list(cands)
        cands = cands[: int(c.get("max_check", 300))]
        todo = [p.product_id for p in cands if f"{dom_id}:{p.product_id}" not in cache][: int(c.get("max_new", 300))]
        for i in range(0, len(todo), 100):
            chunk = todo[i:i + 100]
            try:
                r = requests.get(f"{API}/product", timeout=90, params={
                    "key": self.key, "domain": dom_id, "asin": ",".join(chunk),
                    "stats": 60, "buybox": 1, "history": 0})   # stats=60: media degli ultimi 60 giorni in "avg"
                if r.status_code == 429:
                    log.warning("%s: gettoni Keepa finiti, controllo prezzi Amazon interrotto", c["name"])
                    break
                r.raise_for_status()
                j = r.json()
                log.info("%s: prezzi Amazon controllati %d (gettoni rimasti %s)", c["name"], len(chunk), j.get("tokensLeft"))
                for pr in j.get("products") or []:
                    st = pr.get("stats") or {}
                    cache[f"{dom_id}:{pr.get('asin')}"] = {"t": now, "v": 4, "a60": _media(st, "avg"), "root": pr.get("rootCategory"), "bb": _eur(st.get("buyBoxPrice")),
                                                           "a30": _media(st, "avg30"), "a90": _media(st, "avg90"),
                                                           "a180": _media(st, "avg180"),
                                                           "basis": _eur(st.get("buyBoxSavingBasis")),
                                                           "tipo": st.get("buyBoxSavingBasisType")}
            except Exception as e:
                log.error("%s: controllo prezzi Amazon: %s", c["name"], e)
                break
        try:
            json.dump(cache, open(path, "w", encoding="utf-8"))
        except Exception:
            pass
        keep, mind, gonf, moda = [], float(c.get("min_discount", 30)), 0, 0
        escluse = set(c.get("exclude_roots", []))   # Moda lasciata dentro (decisione di Giuseppe 16/11/2026)
        for p in cands:
            v = cache.get(f"{dom_id}:{p.product_id}")
            if not v or not v.get("bb") or not v.get("basis") or v["basis"] <= v["bb"]:
                continue
            if (1 - v["bb"] / v["basis"]) * 100 < mind:
                continue
            if v.get("root") in escluse:      # Moda: prezzo crollato solo su una taglia, nell'app se ne vede un'altra
                moda += 1
                continue
            if _gonfiato(v):
                gonf += 1
                continue
            p.price, p.old_price = v["bb"], v["basis"]
            keep.append(p)
        log.info("%s: %d offerte con prezzo e prezzo barrato uguali ad Amazon (%d scartate: prezzo gonfiato poco prima; %d di moda/taglie)",
                 c["name"], len(keep), gonf, moda)
        # 19/11/2026 (Giuseppe): se i gettoni non bastano, sul sito anche gli altri prodotti trovati da Keepa,
        # con prezzo Keepa e media 90 giorni, senza controllo del prezzo barrato. Mai su Telegram/Facebook.
        if c.get("site_unchecked"):
            n = 0
            for p in cands_tutti:
                if f"{dom_id}:{p.product_id}" in cache or not p.old_price or p.old_price <= p.price:
                    continue
                if (1 - p.price / p.old_price) * 100 < mind:
                    continue
                p.unchecked = True
                keep.append(p); n += 1
            log.info("%s: %d offerte in più sul sito senza controllo del prezzo barrato", c["name"], n)
        return keep
