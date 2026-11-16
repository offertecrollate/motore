"""Strutture dati comuni del motore."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    """Un prodotto letto da un feed, con il prezzo di oggi."""
    source: str            # es. "awin_mediamarkt_ch", "amazon_de"
    product_id: str        # id univoco nel negozio (EAN, ASIN, id feed...)
    name: str
    price: float
    currency: str          # "CHF" o "EUR"
    shop: str              # nome negozio mostrato nei post
    url: str               # link GIÀ con affiliazione
    image: Optional[str] = None
    old_price: Optional[float] = None   # prezzo barrato dichiarato dal negozio
    category: Optional[str] = None
    ean: Optional[str] = None

    @property
    def key(self) -> str:
        return f"{self.source}:{self.product_id}"


@dataclass
class Deal:
    """Un ribasso trovato dal motore."""
    product: Product
    reference_price: float   # mediana degli ultimi giorni
    discount_pct: float      # sconto rispetto al prezzo di riferimento
    level: str               # "errore" oppure "offerta"
    history_days: int
    extra: dict = field(default_factory=dict)
