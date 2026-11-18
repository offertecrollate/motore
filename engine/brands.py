"""Marchi famosi: le loro offerte vanno prima sui canali e nel post compare ⭐ MARCA (decisione di Giuseppe 18/11/2026)."""
import re

BRANDS = ["Apple", "Samsung", "Sony", "PlayStation", "Nintendo", "Xbox", "Microsoft", "Dyson", "De'Longhi", "Philips",
          "Xiaomi", "Bose", "JBL", "Logitech", "Oral-B", "Braun", "iRobot", "Roomba", "LG", "Lenovo", "HP", "Asus",
          "Acer", "Garmin", "GoPro", "DJI", "Nespresso", "Lavazza", "KitchenAid", "Kenwood", "Ninja", "Rowenta",
          "Moulinex", "Bosch", "Nike", "Adidas", "The North Face", "Lego", "LEGO", "Amazon Echo", "Kindle", "Fire TV",
          "Meta", "Ray-Ban", "Canon", "Nikon", "Huawei", "Google", "Pixel", "Beats", "Sennheiser", "Marshall",
          "Tefal", "Smeg", "Polti", "Vileda", "Gillette", "L'Oréal", "Kérastase", "Burton", "Under Armour", "Asics"]
_ALIAS = {"PlayStation": "Sony", "Roomba": "iRobot", "LEGO": "Lego", "Pixel": "Google", "Kindle": "Amazon",
          "Fire TV": "Amazon", "Amazon Echo": "Amazon", "Xbox": "Microsoft", "AirPods": "Apple", "iPhone": "Apple",
          "iPad": "Apple", "MacBook": "Apple", "Galaxy": "Samsung"}
_RX = [(b, re.compile(r"(?<![\w])" + re.escape(b) + r"(?![\w])", re.I if len(b) > 3 else 0))
       for b in sorted(set(BRANDS) | set(_ALIAS), key=len, reverse=True)]


_ACCESSORI = {"per", "for", "compatibile", "compatible", "custodia", "cover", "pellicola", "vetro", "supporto",
              "cavo", "adattatore", "caricatore", "ricambio", "ricambi", "testine", "sacchetti", "filtro", "filtri"}


def brand_of(name: str) -> str:
    """Restituisce il marchio famoso contenuto nelle prime parole del nome (o "")."""
    parole = str(name or "").split()[:3]           # il marchio è quasi sempre all'inizio
    if any(w.lower().strip(",.") in _ACCESSORI for w in parole):
        return ""                                  # "Custodia per iPhone" non è un prodotto Apple
    testa = " ".join(parole)
    for b, rx in _RX:
        if rx.search(testa):
            return _ALIAS.get(b, b)
    return ""
