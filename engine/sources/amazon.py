"""
Amazon.it / Amazon.de / Amazon.fr (tutti e tre spediscono in Svizzera).

Amazon non dà un feed come Awin. Per ora questa fonte legge un CSV
(asin, name, price, old_price, image) che si può riempire da un servizio di
storico prezzi o dall'API prodotti di Amazon quando l'account affiliato è attivo.
Il link viene costruito qui con il TUO tag affiliato (diverso per .it, .de e .fr).
"""
import csv
from typing import List

from ..models import Product
from .feed import _num

DOMAINS = {"amazon_it": ("amazon.it", "EUR", "Amazon.it"),
           "amazon_de": ("amazon.de", "EUR", "Amazon.de"),
           "amazon_fr": ("amazon.fr", "EUR", "Amazon.fr")}


class AmazonListSource:
    def __init__(self, cfg: dict):
        self.name = cfg["name"]               # "amazon_it" o "amazon_de"
        self.domain, self.currency, self.shop = DOMAINS[cfg["name"]]
        self.tag = cfg["tag"]                 # es. "tuonome-21"
        self.file = cfg["file"]

    def link(self, asin: str) -> str:
        return f"https://www.{self.domain}/dp/{asin}?tag={self.tag}"

    def fetch(self) -> List[Product]:
        out = []
        with open(self.file, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                asin, price = row.get("asin", "").strip(), _num(row.get("price"))
                if not asin or not price:
                    continue
                out.append(Product(
                    source=self.name, product_id=asin, name=row.get("name", "").strip(),
                    price=price, currency=self.currency, shop=self.shop,
                    url=self.link(asin), image=row.get("image") or None,
                    old_price=_num(row.get("old_price")),
                ))
        return out
