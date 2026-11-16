"""Negozi su Shopify: l'elenco pubblico /products.json ha per ogni variante il prezzo e il prezzo "prima"
(compare_at_price). Serve per riempire il sito con offerte vere anche da negozi senza affiliazione.

Configurazione:
    - name: shopify_onestreet_it
      type: shopify
      url: https://onestreet.it
      shop: Onestreet
      currency: EUR
      max_pages: 20          # 250 prodotti per pagina
      site_only: true        # sul sito sì, su Telegram/Facebook no (link non affiliato)
      awin_mid: 128805       # se il negozio ci ha approvato su Awin: link affiliato Awin
"""
import logging
import time
from urllib.parse import quote
from typing import List

import requests

from ..models import Product

log = logging.getLogger(__name__)
UA = {"User-Agent": "Mozilla/5.0 (compatible; OfferteCrollate/1.0; +https://offertecrollate.it)"}


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


class ShopifySource:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.base = cfg["url"].rstrip("/")

    def fetch(self) -> List[Product]:
        out: List[Product] = []
        for page in range(1, int(self.cfg.get("max_pages", 20)) + 1):
            r = requests.get(f"{self.base}/products.json", params={"limit": 250, "page": page},
                             headers=UA, timeout=30)
            if r.status_code == 429:          # troppe richieste: pausa e riprova una volta
                time.sleep(5)
                r = requests.get(f"{self.base}/products.json", params={"limit": 250, "page": page},
                                 headers=UA, timeout=30)
            r.raise_for_status()
            items = r.json().get("products", [])
            if not items:
                break
            for p in items:
                out.extend(self._product(p))
            time.sleep(0.5)
        return out

    def _link(self, url: str) -> str:
        mid = self.cfg.get("awin_mid")
        if not mid:
            return url
        return (f"https://www.awin1.com/cread.php?awinmid={mid}&awinaffid={self.cfg.get('awin_affid', 3152592)}"
                f"&clickref=sito&ued={quote(url, safe='')}")

    def _product(self, p: dict) -> List[Product]:
        variants = [v for v in p.get("variants", []) if v.get("available", True)]
        if not variants:
            return []
        # la variante con lo sconto più forte (se nessuna è scontata, la prima)
        def pct(v):
            pr, old = _num(v.get("price")), _num(v.get("compare_at_price"))
            return (1 - pr / old) if pr and old and old > pr else 0
        v = max(variants, key=pct)
        price, old = _num(v.get("price")), _num(v.get("compare_at_price"))
        if not price:
            return []
        img = (v.get("featured_image") or {}).get("src") or ((p.get("images") or [{}])[0].get("src"))
        name = p.get("title", "").strip()
        vt = (v.get("title") or "").strip()
        if vt and vt.lower() not in ("default title", "default") and len(variants) > 1:
            name = f"{name} ({vt})"
        return [Product(
            source=self.cfg["name"], product_id=str(v.get("id") or p.get("id")), name=name,
            price=price, currency=self.cfg.get("currency", "EUR"), shop=self.cfg.get("shop", self.base),
            url=self._link(f"{self.base}/products/{p.get('handle')}?variant={v.get('id')}"),
            image=img, old_price=old if old and old > price else None,
            category=p.get("product_type") or "",
        )]
