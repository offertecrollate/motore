"""Fonti dei prezzi. Ogni fonte restituisce una lista di Product."""
from .feed import FeedSource
from .amazon import AmazonListSource
from .shopify import ShopifySource
from .aliexpress import AliExpressSource
from .keepa import KeepaSource

SOURCE_TYPES = {
    "feed": FeedSource,          # feed prodotti Awin / Tradedoubler / CSV generico
    "amazon_list": AmazonListSource,
    "shopify": ShopifySource,
    "keepa": KeepaSource,             # offerte Amazon (.it/.de/.fr) da Keepa, a pagamento
    "aliexpress": AliExpressSource,   # API ufficiale affiliati AliExpress (prezzo, prezzo pieno, link affiliato)       # negozi Shopify: prezzo e prezzo "prima" dal loro elenco pubblico
}


def build_source(cfg: dict):
    kind = cfg["type"]
    if kind not in SOURCE_TYPES:
        raise ValueError(f"Tipo di fonte sconosciuto: {kind}")
    return SOURCE_TYPES[kind](cfg)
