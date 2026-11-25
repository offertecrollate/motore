"""Immagine dell'offerta nello stile scelto da Giuseppe (esempio delle cuffie, novembre 2026):
fondo bianco con cornice rossa arrotondata, logo "Offerte Crollate" a pennellata in alto a sinistra,
sconto grande su pennellata rossa, prezzo intero barrato, prezzo scontato in un riquadro rosso,
foto del prodotto grande a destra. Niente nome del prodotto: lo dice già il testo del post."""
import io
import math
import os
import re
import random
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .card_semplice import FONT_DIR, _money

W = H = 1350
RED = (226, 10, 24)
RED_D = (150, 0, 10)
INK = (14, 14, 16)
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(FONT_DIR, "Montserrat.ttf"), size)   # Montserrat Black


def _money_card(v: float, cur: str) -> str:
    """"€ 49,99" come nell'esempio; Svizzera "CHF 152.15"."""
    s = _money(v, cur)
    if cur == "EUR":
        return "€ " + s.replace(" €", "")
    return s


def _brush(w: int, h: int, seed: int) -> Image.Image:
    """Pennellata rossa obliqua con bordi sfrangiati e qualche striscia, come un colpo di pennello."""
    rnd = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad_y = h * 0.14
    top, bot = [], []
    n = 40
    for i in range(n + 1):
        x = w * 0.04 + (w * 0.92) * i / n
        slope = (i / n) * h * 0.10          # leggermente in salita verso destra
        top.append((x, pad_y - slope + rnd.uniform(-h * 0.035, h * 0.035)))
        bot.append((x, h - pad_y - slope + rnd.uniform(-h * 0.035, h * 0.035)))
    left = [(rnd.uniform(0, w * 0.06), pad_y + (h - 2 * pad_y) * k / 6) for k in range(7)]
    right = [(w - rnd.uniform(0, w * 0.07), h - pad_y - h * 0.10 - (h - 2 * pad_y) * k / 6) for k in range(7)]
    d.polygon(top + right + bot[::-1] + left[::-1], fill=RED + (255,))
    for _ in range(8):                      # venature scure dentro la pennellata
        y = rnd.uniform(pad_y + h * 0.08, h - pad_y - h * 0.12)
        x0 = rnd.uniform(w * 0.10, w * 0.55)
        ln = rnd.uniform(w * 0.12, w * 0.30)
        d.line([(x0, y), (x0 + ln, y - ln * 0.10)], fill=RED_D + (70,), width=max(2, int(h * 0.012)))
    return im


def _euro_font(size: int) -> ImageFont.FreeTypeFont:
    """Il "€" di Montserrat Black sembra una C con due barre: per il solo simbolo si usa Archivo nerissimo."""
    f = ImageFont.truetype(os.path.join(FONT_DIR, "Archivo.ttf"), size)
    try:
        f.set_variation_by_axes([900, 100])
    except Exception:
        pass
    return f


def _runs(text: str, size: int):
    """Divide il testo in pezzi con il carattere giusto: € in Archivo, il resto in Montserrat."""
    out, cur, cur_e = [], "", None
    for ch in text:
        e = ch == "€"
        if cur and e != cur_e:
            out.append((cur, _euro_font(int(size * 0.96)) if cur_e else _font(size)))
            cur = ""
        cur += ch
        cur_e = e
    if cur:
        out.append((cur, _euro_font(int(size * 0.96)) if cur_e else _font(size)))
    return out


def _text_width(text: str, size: int) -> int:
    return int(sum(f.getlength(t) for t, f in _runs(text, size)))


def _shear_text(text: str, size: int, fill, shadow=True, shear: float = 0.18) -> Image.Image:
    """Testo in corsivo finto (inclinato) con ombra scura, come nell'esempio."""
    runs = _runs(text, size)
    tw = _text_width(text, size)
    asc = max(f.getmetrics()[0] for _, f in runs)
    desc = max(f.getmetrics()[1] for _, f in runs)
    padx, pady = int(size * 0.30), int(size * 0.10)
    h = asc + desc + 2 * pady
    im = Image.new("RGBA", (tw + 2 * padx + int(h * shear), h), (0, 0, 0, 0))
    sw = max(2, size // 40) if shadow else 0

    def draw(d, dx, dy, color):
        x = padx + dx
        for t, f in runs:
            d.text((x, pady + asc + dy), t, font=f, fill=color, anchor="ls", stroke_width=sw, stroke_fill=color)
            x += f.getlength(t)

    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw(ImageDraw.Draw(sh), size * 0.035, size * 0.045, (60, 0, 0, 200))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * 0.03)))
    draw(ImageDraw.Draw(im), 0, 0, fill)
    # taglia lo spazio vuoto sopra e sotto, poi inclina verso destra
    bb = im.getbbox()
    if bb:
        im = im.crop((0, max(0, bb[1] - int(size * 0.06)), im.width, min(im.height, bb[3] + int(size * 0.06))))
    w, h = im.size
    return im.transform((w + int(h * shear), h), Image.AFFINE, (1, shear, -h * shear, 0, 1, 0), Image.BICUBIC)


def _fit(text: str, max_w: int, start: int, min_size: int = 60) -> int:
    s = start
    while s > min_size:
        if _text_width(text, s) * 1.1 <= max_w:
            return s
        s -= 4
    return min_size


def _product(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    im = img.convert("RGBA")
    # taglia il bordo bianco o trasparente intorno al prodotto, così la foto riempie il riquadro
    from PIL import ImageChops
    rgb = Image.new("RGB", im.size, (255, 255, 255))
    rgb.paste(im, mask=im.split()[3])
    diff = ImageChops.difference(rgb, Image.new("RGB", im.size, (255, 255, 255))).convert("L").point(lambda v: 255 if v > 18 else 0)
    bb = diff.getbbox()
    if bb:
        pad = 6
        im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
    k = min(box_w / im.width, box_h / im.height)
    k = min(k, 4.0)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
    if k > 1.2:
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    return im


def _wrap(text: str, font, max_w: int) -> list:
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _descrizione(can: Image.Image, name: str, shop: str) -> None:
    """Nome del prodotto su massimo 4 righe nello spazio libero accanto al logo, sotto il negozio."""
    x0, y0, max_w, max_h = 815, 52, W - 815 - 52, 236
    name = re.sub(r"\s+", " ", name or "").strip()
    d = ImageDraw.Draw(can)
    for size in (48, 44, 40, 36, 33):
        f = _font(size)
        lines = _wrap(name, f, max_w)
        lh = int(size * 1.18)
        fs = _font(int(size * 0.62))
        need = len(lines) * lh + int(size * 0.9)
        if len(lines) <= 4 and need <= max_h:
            break
    if len(lines) > 4 or need > max_h:                       # nome lunghissimo: taglio con i puntini
        keep = max(1, min(4, (max_h - int(size * 0.9)) // lh))
        lines = lines[:keep]
        while f.getlength(lines[-1] + "…") > max_w and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] += "…"
    y = y0 + (max_h - (len(lines) * lh + int(size * 0.9))) // 2
    for ln in lines:
        d.text((x0, y), ln, font=f, fill=INK)
        y += lh
    if shop:
        d.text((x0, y + int(size * 0.18)), f"su {shop}", font=fs, fill=RED)


def _star(cx: float, cy: float, r: float):
    import math
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _stelle(can: Image.Image, x: int, y: int, rating: float, reviews: int) -> None:
    """Cinque stelle dorate (anche mezze) con il voto e le recensioni: solo da 4 stelle in su."""
    r, gap = 28, 64
    lay = Image.new("RGBA", can.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    gold, grey = (255, 184, 0, 255), (215, 215, 215, 255)
    for i in range(5):
        cx = x + r + i * gap
        ld.polygon(_star(cx, y + r, r), fill=grey)
        fill = max(0.0, min(1.0, rating - i))
        if fill > 0:
            m = Image.new("L", can.size, 0)
            ImageDraw.Draw(m).polygon(_star(cx, y + r, r), fill=255)
            cut = Image.new("L", can.size, 0)
            ImageDraw.Draw(cut).rectangle((cx - r, y, cx - r + 2 * r * fill, y + 2 * r), fill=255)
            from PIL import ImageChops
            g = Image.new("RGBA", can.size, gold)
            lay.paste(g, (0, 0), ImageChops.multiply(m, cut))
    can.alpha_composite(lay)
    d = ImageDraw.Draw(can)
    txt = f"{rating:.1f}".replace(".", ",") + (f"  ({reviews:,})".replace(",", ".") if reviews else "")
    d.text((x + 4, y + 2 * r + 12), txt, font=_font(38), fill=INK)


def make(name: str, price: float, old: float, currency: str, shop: str,
         product_img: Optional[Image.Image] = None, seed: Optional[int] = None,
         rating: Optional[float] = None, reviews: Optional[int] = None) -> bytes:
    seed = seed if seed is not None else abs(hash(name)) % 10000
    pct = round((1 - price / old) * 100) if old and old > price else 0
    can = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(can)

    # foto del prodotto, grande, a destra
    prod_left = W - 60                       # bordo sinistro del prodotto: lo sconto non deve superarlo
    if product_img is not None:
        bx0, by0, bw0, bh0 = 600, 300, 700, 720      # riquadro della foto: lontano da logo e sconto
        p = _product(product_img, bw0, bh0)
        px = bx0 + (bw0 - p.width) // 2
        py = by0 + (bh0 - p.height) // 2
        prod_left = px
        # ombra morbida sotto il prodotto
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((px + p.width * 0.15, py + p.height - 30, px + p.width * 0.9, py + p.height + 25), fill=(0, 0, 0, 55))
        can.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
        if p.mode == "RGBA" and p.getextrema()[3][0] < 255:
            can.alpha_composite(p, (px, py))
        else:
            can.paste(p.convert("RGB"), (px, py))

    # logo a pennellata
    logo_path = os.path.join(ASSETS, "logo_card_v3.png")    # 25/11/2026: nuovo logo di Giuseppe (carrello, cartellino %)
    if os.path.exists(logo_path):
        lg = Image.open(logo_path).convert("RGBA")
        k = min(740 / lg.width, 315 / lg.height)              # non deve coprire il riquadro dello sconto
        lg = lg.resize((int(lg.width * k), int(lg.height * k)), Image.LANCZOS)
        can.paste(lg, (28, 30), lg)
    elif os.path.exists(os.path.join(ASSETS, "logo_brush.png")):
        lg = Image.open(os.path.join(ASSETS, "logo_brush.png")).convert("RGB")
        lg = lg.resize((760, int(lg.height * 760 / lg.width)), Image.LANCZOS)
        can.paste(lg, (28, 34))

    # descrizione: nome del prodotto (e negozio) in alto a destra, accanto al logo
    _descrizione(can, name, shop)

    # sconto su pennellata
    if pct:
        # grandezza dello sconto in base allo spazio libero a sinistra del prodotto
        bx_, by_ = 34, 360
        avail = prod_left - bx_ - 24
        size = 230
        while True:
            t = _shear_text(f"-{pct}%", size, (255, 255, 255))
            if t.width + 50 <= avail or size <= 90:
                break
            size -= 6
        bw_ = min(max(t.width + 50, 300), max(avail, t.width + 20))
        bh_ = int(size * 1.55)
        br = _brush(bw_, bh_, seed)
        can.alpha_composite(br, (bx_, by_))
        can.alpha_composite(t, (bx_ + (bw_ - t.width) // 2, by_ + (bh_ - t.height) // 2 - int(size * 0.07)))

    # stelle Amazon (da 4 in su), tra lo sconto e il prezzo barrato
    if rating and rating >= 4.0:
        _stelle(can, 70, 650, rating, int(reviews or 0))

    # prezzo intero barrato
    if old and old > price:
        ot = _money_card(old, currency)
        os_ = _fit(ot, 620, 92)
        o = _shear_text(ot, os_, INK, shadow=False, shear=0.14)
        ox, oy = 70, 880
        can.alpha_composite(o, (ox, oy))
        d.line([(ox + o.width * 0.10, oy + o.height * 0.80), (ox + o.width * 0.95, oy + o.height * 0.22)],
               fill=RED, width=12)

    # prezzo scontato nel riquadro rosso
    pt = _money_card(price, currency)
    ps = _fit(pt, W - 260, 190)
    pim = _shear_text(pt, ps, (255, 255, 255), shear=0.12)
    bw, bh = max(640, pim.width + 50), 250
    bx, by = 55, H - 55 - bh
    box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(box)
    bd.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=44, fill=(255, 196, 0, 255))         # bordo dorato
    grad = Image.new("RGBA", (bw - 14, bh - 14))
    for y in range(bh - 14):                                                                 # sfumatura rossa
        k = y / (bh - 14)
        c = tuple(int(a + (b - a) * k) for a, b in zip((240, 30, 36), (175, 0, 12)))
        ImageDraw.Draw(grad).line([(0, y), (bw, y)], fill=c + (255,))
    m = Image.new("L", grad.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, grad.width - 1, grad.height - 1), radius=38, fill=255)
    box.paste(grad, (7, 7), m)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((bx + 8, by + 14, bx + bw + 8, by + bh + 14), radius=44, fill=(0, 0, 0, 90))
    can.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    can.alpha_composite(box, (bx, by))
    can.alpha_composite(pim, (bx + (bw - pim.width) // 2, by + (bh - pim.height) // 2))

    # cornice rossa arrotondata
    d = ImageDraw.Draw(can)
    d.rounded_rectangle((16, 16, W - 17, H - 17), radius=48, outline=RED, width=10)

    out = io.BytesIO()
    can.convert("RGB").save(out, "JPEG", quality=93, optimize=True)
    return out.getvalue()


def neutral_adult_img(size: int = 900) -> Image.Image:
    """Al posto della foto del prodotto per adulti: riquadro sobrio con "18+" (nessuna foto del negozio)."""
    im = Image.new("RGB", (size, size), (255, 255, 255))
    d = ImageDraw.Draw(im)
    r = int(size * 0.36)
    cx = cy = size // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(227, 6, 19), width=int(size * 0.045))
    f = _font(int(size * 0.26))
    d.text((cx, cy), "18+", font=f, fill=(20, 20, 20), anchor="mm")
    return im
