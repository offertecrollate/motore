"""
Feed prodotti delle piattaforme di affiliazione (CSV, anche compresso .gz).

Awin e Tradedoubler danno a ogni affiliato approvato un URL di download del feed:
dentro ci sono prezzo, nome, immagine e il link GIÀ con il tuo codice affiliato.
È il modo legale e gratuito di avere i prezzi ogni giorno, senza scraping.
"""
import csv
import gzip
import io
from typing import List, Optional

import requests

from ..models import Product

# Nomi delle colonne per le piattaforme più comuni. Si possono sovrascrivere nel config.
PRESETS = {
    "awin": {
        "id": "aw_product_id", "name": "product_name", "price": "search_price",
        "old_price": "rrp_price", "url": "aw_deep_link", "image": "merchant_image_url",
        "currency": "currency", "category": "merchant_category", "ean": "ean",
        "shop": "merchant_name",
    },
    "tradedoubler": {
        "id": "id", "name": "name", "price": "price", "old_price": "previousPrice",
        "url": "productUrl", "image": "imageUrl", "currency": "currency",
        "category": "categories", "ean": "ean", "shop": "programName",
    },
    # formato "Google Shopping" che alcuni negozi usano su Awin
    "google": {
        "id": "id", "name": "title", "price": "price", "sale_price": "sale_price",
        "url": "link", "image": "image_link", "currency": "currency",
        "category": "product_type", "ean": "gtin", "shop": "merchant_name",
    },
    "generic": {
        "id": "id", "name": "name", "price": "price", "old_price": "old_price",
        "url": "url", "image": "image", "currency": "currency",
        "category": "category", "ean": "ean", "shop": "shop",
    },
}


def _num(v: Optional[str]) -> Optional[float]:
    if v is None:
        return None
    v = str(v).strip().replace("CHF", "").replace("EUR", "").replace("'", "").strip()
    if not v:
        return None
    if "," in v and "." not in v:
        v = v.replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


_AWIN_LISTS = {}


_AWIN_ROWS = {}


def _awin_rows(list_url: str) -> list:
    if list_url not in _AWIN_ROWS:
        r = requests.get(list_url, timeout=60)
        r.raise_for_status()
        _AWIN_ROWS[list_url] = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
    return _AWIN_ROWS[list_url]


def awin_feed_url(list_url: str, feed_id: str = None, advertiser_id: str = None) -> str:
    """Trova nella lista feed di Awin l'indirizzo di download: per Feed ID, oppure per ID inserzionista
    (sceglie il catalogo con più prodotti; utile appena iscritti, quando il Feed ID non si conosce ancora)."""
    rows = _awin_rows(list_url)
    if feed_id:
        url = next((r["URL"] for r in rows if r.get("Feed ID") == str(feed_id)), None)
    else:
        mine = [r for r in rows if r.get("Advertiser ID") == str(advertiser_id)]
        mine.sort(key=lambda r: int(r.get("No of products") or 0), reverse=True)
        url = mine[0]["URL"] if mine else None
    if not url:
        raise ValueError(f"Catalogo Awin {feed_id or 'inserzionista ' + str(advertiser_id)} non ancora disponibile")
    return url


class FeedSource:
    def __init__(self, cfg: dict):
        self.name = cfg["name"]
        self.url = cfg.get("url")          # URL del feed (dalla piattaforma)
        self.awin_list = cfg.get("awin_list")   # oppure: lista feed Awin + Feed ID
        self.awin_fid = cfg.get("awin_feed_id")
        self.awin_adv = cfg.get("awin_advertiser_id")
        self.file = cfg.get("file")        # oppure file locale (per test)
        self.cols = {**PRESETS[cfg.get("preset", "generic")], **cfg.get("columns", {})}
        self.shop = cfg.get("shop")        # nome negozio fisso, se il feed non lo dà
        self.currency = cfg.get("currency", "CHF")
        self.delimiter = cfg.get("delimiter", ",")

    def _read_text(self) -> str:
        if self.file:
            raw = open(self.file, "rb").read()
        else:
            if not self.url and self.awin_list and (self.awin_fid or self.awin_adv):
                self.url = awin_feed_url(self.awin_list, self.awin_fid, self.awin_adv)
            r = requests.get(self.url, timeout=120)
            r.raise_for_status()
            raw = r.content
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return raw.decode("utf-8-sig", errors="replace")

    def fetch(self) -> List[Product]:
        c = self.cols
        out = []
        reader = csv.DictReader(io.StringIO(self._read_text()), delimiter=self.delimiter)
        for row in reader:
            price = _num(row.get(c["price"]))
            old = _num(row.get(c["old_price"])) if c.get("old_price") else None
            if c.get("sale_price"):              # Google: price = listino, sale_price = scontato
                sale = _num(row.get(c["sale_price"]))
                if sale and price and sale < price:
                    price, old = sale, price
            pid = (row.get(c["id"]) or "").strip()
            url = (row.get(c["url"]) or "").strip()
            if not price or not pid or not url:
                continue
            out.append(Product(
                source=self.name,
                product_id=pid,
                name=(row.get(c["name"]) or "").strip(),
                price=price,
                currency=(row.get(c["currency"]) or self.currency).strip() or self.currency,
                shop=self.shop or (row.get(c["shop"]) or "").strip(),
                url=url,
                image=(row.get(c["image"]) or "").strip() or None,
                old_price=old,
                category=(row.get(c["category"]) or "").strip() or None,
                ean=(row.get(c["ean"]) or "").strip() or None,
            ))
        return out
