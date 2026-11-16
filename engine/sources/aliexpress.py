"""AliExpress tramite l'API ufficiale per affiliati (AliExpress Portals / Open Platform).

Legge i prodotti in promozione con prezzo di oggi, prezzo pieno e link affiliato già pronto
(promotion_link). Niente lettura del sito: solo l'API permessa dal programma affiliati.

Configurazione (i codici arrivano dai segreti di GitHub):
    - name: aliexpress_it
      type: aliexpress
      app_key: ${ALI_APP_KEY}
      app_secret: ${ALI_APP_SECRET}
      tracking_id: ${ALI_TRACKING_ID}
      country: IT              # paese di spedizione (IT o CH)
      currency: EUR            # EUR o CHF
      language: IT             # IT, DE, FR
      keywords: [smartphone, cuffie, smartwatch, aspirapolvere, ...]   # ricerche fatte a ogni giro
      pages: 2                 # pagine da 50 prodotti per ricerca
      min_discount: 40         # sotto questo sconto dichiarato il prodotto non interessa
"""
import hashlib
import hmac
import logging
import re
import time
from typing import List

import requests

from ..models import Product

log = logging.getLogger(__name__)
API = "https://api-sg.aliexpress.com/sync"
FIELDS = ("product_id,product_title,target_sale_price,target_original_price,discount,"
          "product_main_image_url,promotion_link,first_level_category_name,evaluate_rate,lastest_volume")


def _num(v):
    try:
        return float(str(v).replace(",", "")) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


class AliExpressSource:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.key = str(cfg.get("app_key") or "").strip()
        self.secret = str(cfg.get("app_secret") or "").strip()
        self.tracking = str(cfg.get("tracking_id") or "").strip()

    def _call(self, method: str, **params) -> dict:
        p = {"app_key": self.key, "method": method, "sign_method": "sha256",
             "timestamp": str(int(time.time() * 1000)), **{k: str(v) for k, v in params.items() if v not in (None, "")}}
        base = "".join(f"{k}{p[k]}" for k in sorted(p))
        p["sign"] = hmac.new(self.secret.encode(), base.encode(), hashlib.sha256).hexdigest().upper()
        r = requests.post(API, data=p, timeout=40)
        r.raise_for_status()
        data = r.json()
        if "error_response" in data:
            raise RuntimeError(f"AliExpress: {data['error_response'].get('msg') or data['error_response']}")
        return data

    def fetch(self) -> List[Product]:
        if not (self.key and self.secret and self.tracking) or self.key.startswith("$"):
            log.info("%s: codici AliExpress non ancora inseriti, salto", self.cfg["name"])
            return []
        c = self.cfg
        min_pct = float(c.get("min_discount", 40))
        seen, out = set(), []
        for kw in c.get("keywords", [""]):
            for page in range(1, int(c.get("pages", 2)) + 1):
                try:
                    data = self._call("aliexpress.affiliate.product.query",
                                      keywords=kw, page_no=page, page_size=50, fields=FIELDS,
                                      target_currency=c.get("currency", "EUR"),
                                      target_language=c.get("language", "IT"),
                                      ship_to_country=c.get("country", "IT"),
                                      tracking_id=self.tracking, sort="LAST_VOLUME_DESC")
                except Exception as e:
                    log.warning("%s: ricerca '%s' non riuscita: %s", c["name"], kw, e)
                    break
                res = (data.get("aliexpress_affiliate_product_query_response", {})
                       .get("resp_result", {}).get("result", {}))
                items = (res.get("products") or {}).get("product") or []
                if not items:
                    break
                for it in items:
                    pid = str(it.get("product_id") or "")
                    price, old = _num(it.get("target_sale_price")), _num(it.get("target_original_price"))
                    link = it.get("promotion_link")
                    if not pid or pid in seen or not price or not link:
                        continue
                    if not old or old <= price or (1 - price / old) * 100 < min_pct:
                        continue
                    seen.add(pid)
                    out.append(Product(
                        source=c["name"], product_id=pid,
                        name=re.sub(r"\s+", " ", it.get("product_title") or "").strip()[:200],
                        price=price, currency=c.get("currency", "EUR"), shop="AliExpress",
                        url=link, image=it.get("product_main_image_url"), old_price=old,
                        category=it.get("first_level_category_name")))
                time.sleep(0.3)
        return out
