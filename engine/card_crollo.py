"""
Scheda "Crollo" (1080x1080), nello stile scelto da Giuseppe: fondo rosso con fulmini e macerie,
cartello ERRORE DI PREZZO, prodotto a sinistra con luce rossa, prezzo nuovo in oro crepato,
prezzo vecchio barrato, esplosione rossa con lo sconto, pulsante PRENDILO AL VOLO.

Il fondo fisso sta in assets/card/plate_errore.jpg; qui si disegnano solo le parti che cambiano.
"""
import math
import os
import re

from PIL import Image, ImageDraw, ImageFilter

from .cards import font, metal_text, _product, _paste_center, _burst
from .texts import money

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "assets", "card")
S = 1080

TXT = {
    "it": {"cta": "PRENDILO SUBITO"},
    "de": {"cta": "SCHNELL ZUGREIFEN"},
    "fr": {"cta": "FONCE VITE"},
}

# genere e numero del prodotto per "PRENDILO / PRENDILA / PRENDILI / PRENDILE SUBITO"
_FEM_PL = {"cuffie", "scarpe", "sneakers", "ciabatte", "calze", "calzature", "lenzuola", "posate", "padelle",
           "pentole", "lampadine", "batterie", "pile", "forbici", "tende", "bottiglie", "capsule", "cialde",
           "carte", "infradito", "mutande", "magliette", "camicie", "giacche", "felpe", "borse", "valigie"}
_MAS_PL = {"auricolari", "occhiali", "pantaloni", "jeans", "stivali", "guanti", "pneumatici", "piatti",
           "bicchieri", "coltelli", "altoparlanti", "giochi", "set", "mattoncini", "pannolini", "sandali",
           "boxer", "shorts", "leggings", "cuscini", "asciugamani", "accappatoi"}
_FEM = {"friggitrice", "lavatrice", "lavastoviglie", "asciugatrice", "macchina", "macchinetta", "stampante",
        "console", "tv", "televisione", "smart tv", "bicicletta", "bici", "e-bike", "monopattino_",
        "borsa", "valigia", "giacca", "felpa", "maglietta", "camicia", "scarpa", "sedia", "scrivania",
        "lampada", "fotocamera", "videocamera", "action cam", "telecamera", "webcam", "tastiera",
        "scheda", "chiavetta", "memoria", "ssd_", "cassa", "soundbar", "radio", "tenda", "padella",
        "pentola", "bilancia", "piastra", "spazzola", "spazzolino_", "caffettiera", "bollitore_",
        "planetaria", "impastatrice", "affettatrice", "centrifuga", "estrattore_", "griglia", "graffettatrice",
        "trapano_", "smerigliatrice", "sega", "pistola", "idropulitrice", "motosega", "batteria",
        "powerbank_", "cover", "custodia", "pellicola", "bambola", "palla", "racchetta", "tenda", "coperta",
        "piumino_", "poltrona", "lampadina", "consolle", "playstation", "xbox", "nintendo switch", "switch",
        "smartwatch_", "bambola", "crema", "colonia", "fragranza", "lozione", "maschera", "tazza", "moka"}


def cta_it(name: str) -> str:
    words = re.findall(r"[a-zàèéìòù\-]+", name.lower())
    for w in words:
        if w in _FEM_PL:
            return "PRENDILE SUBITO"
        if w in _MAS_PL:
            return "PRENDILI SUBITO"
        if w in _FEM:
            return "PRENDILA SUBITO"
    return "PRENDILO SUBITO"


def short_name(name: str, max_chars: int = 16) -> str:
    name = re.sub(r"\(.*?\)|\[.*?\]", " ", name)
    name = re.split(r",|\s[-–|:]\s|\|", name)[0]
    out = ""
    for w in name.split():
        t = (out + " " + w).strip()
        if len(t) > max_chars and out:
            break
        out = t
    return out.upper()


def big_money(v: float, cur: str) -> str:
    """Prezzo per l'immagine: senza ,00 quando è un prezzo tondo, così le cifre vengono più grandi."""
    m = money(v, cur)
    return m.replace(",00 €", " €").replace(".–", ".–")


def _rays(size, center, n=28, color=(255, 170, 40), alpha=170, seed=1):
    import random
    rnd = random.Random(seed)
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = center
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-.08, .08)
        L = rnd.uniform(.35, 1) * max(size) * .45
        w = rnd.uniform(.02, .05)
        d.polygon([(cx, cy), (cx + L * math.cos(a - w), cy + L * math.sin(a - w)),
                   (cx + L * math.cos(a + w), cy + L * math.sin(a + w))], fill=color + (alpha,))
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse([cx - max(size) * .45, cy - max(size) * .45, cx + max(size) * .45, cy + max(size) * .45], fill=255)
    lay.putalpha(Image.composite(lay.getchannel("A"), Image.new("L", size, 0), m.filter(ImageFilter.GaussianBlur(60))))
    return lay.filter(ImageFilter.GaussianBlur(3))


def _red_burst(pct: float) -> Image.Image:
    R = 190
    size = 2 * R + 80
    c = size // 2
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    pts = [(x - R + c, y - R + c) for x, y in _burst(R, R * .72, points=14, rot=.2)]
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    glow = Image.new("RGBA", (size, size), (255, 150, 0, 0))
    glow.putalpha(m.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(glow)
    im.paste(Image.new("RGBA", (size, size), (255, 200, 60, 255)), (0, 0), m)          # bordo giallo-arancio
    inner = Image.new("L", (size, size), 0)
    ImageDraw.Draw(inner).polygon([(c + (x - c) * .9, c + (y - c) * .9) for x, y in pts], fill=255)
    rg = Image.radial_gradient("L").resize((size, size))
    body = Image.composite(Image.new("RGBA", (size, size), (120, 0, 8, 255)),
                           Image.new("RGBA", (size, size), (240, 26, 30, 255)), rg)
    im.paste(body, (0, 0), inner)
    t = metal_text(f"-{pct:.0f}%", font(170, 900, 72), palette="silver", depth=10, shear=.14,
                   glow=(80, 0, 0), cracks=True, seed=4, stroke=6)
    t.thumbnail((int(R * 1.85), int(R * 1.3)), Image.LANCZOS)
    _paste_center(im, t, c + 4, c + 6)
    return im.rotate(-6, resample=Image.BICUBIC)


def _rim(prod: Image.Image, color=(255, 30, 20)) -> Image.Image:
    """Luce rossa dietro e intorno al prodotto."""
    pad = 70
    w, h = prod.width + 2 * pad, prod.height + 2 * pad
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    a = Image.new("L", (w, h), 0)
    a.paste(prod.getchannel("A") if prod.mode == "RGBA" else Image.new("L", prod.size, 255), (pad, pad))
    for blur, k in [(40, 1.0), (14, 1.2)]:
        g = Image.new("RGBA", (w, h), color + (0,))
        g.putalpha(a.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: min(255, int(v * k))))
        out.alpha_composite(g)
    out.alpha_composite(prod.convert("RGBA"), (pad, pad))
    return out


def make(deal, lang, product_img) -> Image.Image:
    p = deal.product
    t = TXT.get(lang, TXT["it"])
    card = Image.open(os.path.join(A, "plate_errore.jpg")).convert("RGBA").resize((S, S))

    # sirena staccata dal prodotto, in alto a sinistra
    if os.path.exists(os.path.join(A, "siren.png")):
        sr = Image.open(os.path.join(A, "siren.png"))
        sr = sr.resize((int(sr.width * .9), int(sr.height * .9)), Image.LANCZOS)
        card.alpha_composite(sr, (300 - sr.width // 2, 6))

    # prodotto a sinistra, appoggiato sulle macerie, sotto la sirena
    prod = _product(product_img, 500, 580)
    if not prod.info.get("cutout"):     # foto con sfondo non bianco: la metto su una tessera chiara
        tile = Image.new("RGBA", (prod.width + 40, prod.height + 40), (0, 0, 0, 0))
        ImageDraw.Draw(tile).rounded_rectangle([0, 0, tile.width - 1, tile.height - 1], 28, fill=(255, 255, 255, 255))
        tile.alpha_composite(prod.convert("RGBA"), (20, 20))
        m = Image.new("L", tile.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, tile.width - 1, tile.height - 1], 28, fill=255)
        tile.putalpha(m)
        prod = tile
    lit = _rim(prod)
    px = 300 - lit.width // 2
    py = max(860 - lit.height + 50, 200 - 70)
    card.alpha_composite(lit, (px, py))

    # colonna di destra
    RX0, RX1 = 560, 1060
    cx = (RX0 + RX1) // 2
    name = deal.extra.get("short") or short_name(p.name)
    nt = metal_text(name, font(120, 900, 72), palette="silver", depth=10, shear=.14, glow=(255, 30, 20),
                    cracks=False, stroke=6)
    nt.thumbnail((RX1 - RX0, 140), Image.LANCZOS)
    _paste_center(card, nt, cx, 300)

    old = money(deal.reference_price, p.currency)
    ot = metal_text(old, font(80, 900, 80), palette="silver", depth=6, shear=.14, glow=None, cracks=False, stroke=4)
    ot.thumbnail((380, 80), Image.LANCZOS)
    _paste_center(card, ot, cx, 400)
    sl = Image.new("RGBA", (ot.width + 40, 60), (0, 0, 0, 0))
    ImageDraw.Draw(sl).line([(4, 44), (sl.width - 4, 14)], fill=(255, 25, 25, 255), width=9)
    slg = Image.new("RGBA", sl.size, (255, 0, 0, 0))
    slg.putalpha(sl.getchannel("A").filter(ImageFilter.GaussianBlur(6)))
    _paste_center(card, slg, cx, 402)
    _paste_center(card, sl, cx, 402)

    new = big_money(p.price, p.currency)
    fire = Image.new("L", (S, S), 0)
    ImageDraw.Draw(fire).ellipse([cx - 260, 430, cx + 260, 660], fill=255)
    fg = Image.new("RGBA", (S, S), (255, 120, 0, 0))
    fg.putalpha(fire.filter(ImageFilter.GaussianBlur(60)).point(lambda v: int(v * .75)))
    card.alpha_composite(fg)
    gt = metal_text(new, font(260, 900, 68), palette="gold", depth=20, shear=.14, glow=(255, 110, 0), seed=8, stroke=9)
    gt.thumbnail((RX1 - RX0 + 30, 270), Image.LANCZOS)
    _paste_center(card, gt, cx, 548)

    b = _red_burst(deal.discount_pct)
    b.thumbnail((420, 420), Image.LANCZOS)
    _paste_center(card, b, cx + 70, 745)

    # pulsante
    cta = cta_it(p.name) if lang == "it" else t["cta"]
    ct = metal_text(cta, font(96, 900, 82), palette="silver", depth=6, shear=.14, glow=None, cracks=False, stroke=4)
    ct.thumbnail((700, 74), Image.LANCZOS)
    _paste_center(card, ct, 540, 928)
    return card
