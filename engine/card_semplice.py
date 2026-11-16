"""Immagine semplice dell'offerta per Telegram e Facebook (1080x1080).

Fondo bianco, prodotto grande, sotto: nome, prezzo intero barrato, prezzo scontato
in grande e percentuale di sconto in rosso. Si capisce lo sconto a colpo d'occhio.
"""
import io
import os

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from .cards import font, _wrap, _product, LOGO

W = H = 1080
M = 60
INK = (20, 20, 24)
GREY = (120, 120, 128)
RED = (226, 18, 38)
LINE = (232, 232, 236)


def _money(v: float, cur: str) -> str:
    if cur == "EUR":
        s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{s[:-3] if s.endswith(',00') else s} €"
    s = f"{v:,.2f}".replace(",", "'")          # Svizzera: 1'299.50
    return f"CHF {s[:-3] if s.endswith('.00') else s}"


FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
PRICE_FONT = "Montserrat.ttf"   # carattere dei prezzi (scelto: Montserrat)


def _pfont(size):
    if PRICE_FONT:
        from PIL import ImageFont
        return ImageFont.truetype(os.path.join(FONT_DIR, PRICE_FONT), size)
    return font(size, 900, 90)


def hd_url(url: str) -> str:
    """Versione più grande della foto, dove il negozio lo permette (Acer: 1200 px; Electrolux: PD)."""
    import re
    if "acer.com" in url and "width=" in url:
        url = re.sub(r"width=\d+", "width=1200", re.sub(r"height=\d+", "height=1200", url))
        url = re.sub(r"canvas=\d+:\d+", "canvas=1200:1200", url)
    if "electrolux.bynder.com/transform/PV/" in url:
        url = url.replace("/transform/PV/", "/transform/PD/")
    return url


S = 2          # disegno a 2160x2160: su Facebook e Telegram resta nitido anche ingrandito


def _s(v):
    return int(round(v * S))


def make(name: str, price: float, old: float, currency: str, shop: str,
         product_img: Image.Image) -> bytes:
    WW = _s(W)
    MM = _s(M)
    card = Image.new("RGB", (WW, WW), "white")
    d = ImageDraw.Draw(card)

    # intestazione piccola: logo + nome del canale, negozio a destra
    if os.path.exists(LOGO):
        ls = _s(64)
        lg = Image.open(LOGO).convert("RGBA").resize((ls, ls), Image.LANCZOS)
        mk = Image.new("L", (ls, ls), 0)
        ImageDraw.Draw(mk).ellipse([0, 0, ls - 1, ls - 1], fill=255)
        card.paste(lg, (MM, _s(40)), mk)
    d.text((MM + _s(80), _s(72)), "Offerte Crollate", font=font(_s(32), 800), fill=INK, anchor="lm")
    d.text((WW - MM, _s(72)), shop, font=font(_s(30), 600), fill=GREY, anchor="rm")

    # prodotto
    box_w, box_h = WW - 2 * MM, _s(560)
    img = ImageOps.exif_transpose(product_img)
    prod = _product(img, box_w, box_h)
    # foto piccole del negozio: ingrandisco fino a riempire lo spazio (max 4 volte)
    k = min(box_w / prod.width, box_h / prod.height, 4.0)
    if k > 1.05:
        prod = prod.resize((int(prod.width * k), int(prod.height * k)), Image.LANCZOS)
        prod = prod.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    px = (WW - prod.width) // 2
    py = _s(130) + (box_h - prod.height) // 2
    if prod.mode == "RGBA":
        card.paste(prod, (px, py), prod)
    else:
        card.paste(prod, (px, py))

    # nome del prodotto
    d.line([(MM, _s(712)), (WW - MM, _s(712))], fill=LINE, width=_s(3))
    nf = font(_s(38), 700)
    y = _s(740)
    for ln in _wrap(d, name, nf, WW - 2 * MM, 2):
        d.text((MM, y), ln, font=nf, fill=INK)
        y += _s(48)

    # sconto: bollino rosso grande in alto a destra, sopra il prodotto
    pct = round((1 - price / old) * 100)
    pct_txt = f"-{pct}%"
    bf = _pfont(_s(110))
    bw = int(d.textlength(pct_txt, font=bf)) + _s(60)
    bx1, by0 = WW - MM, _s(120)
    d.rounded_rectangle([bx1 - bw, by0, bx1, by0 + _s(150)], _s(28), fill=RED)
    d.text((bx1 - bw // 2, by0 + _s(78)), pct_txt, font=bf, fill="white", anchor="mm")

    # prezzi: intero barrato in grigio, scontato GRANDE e ROSSO
    base = _s(1010)
    newt = _money(price, currency)
    size = _s(200)
    nf2 = _pfont(size)
    oldt = _money(old, currency)
    of = font(_s(56), 600)
    ow = d.textlength(oldt, font=of)
    room = WW - 2 * MM - ow - _s(40)
    while d.textlength(newt, font=nf2) > room and size > _s(80):
        size -= _s(4)
        nf2 = _pfont(size)
    d.text((MM - _s(6), base), newt, font=nf2, fill=RED, anchor="ls")
    nw = d.textlength(newt, font=nf2)
    ox, oy = MM + nw + _s(34), base - _s(30)
    d.text((ox, oy), oldt, font=of, fill=GREY, anchor="ls")
    d.line([(ox - _s(4), oy - _s(20)), (ox + ow + _s(4), oy - _s(20))], fill=GREY, width=_s(5))

    # JPEG di alta qualità (2160 px): Facebook ricomprime comunque, così parte da un'immagine nitida
    out = io.BytesIO()
    card.save(out, "JPEG", quality=95, subsampling=0, optimize=True)
    return out.getvalue()
