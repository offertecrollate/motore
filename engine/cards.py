"""
Immagine promozionale per ogni offerta (1080x1350, formato verticale per Facebook e Telegram).

Stile Offerte Crollate: fondo vino scuro preso dall'immagine principale, foto del prodotto su
pannello chiaro, bollino oro con lo sconto, prezzo grande in rosso con bordo oro.

Per le offerte Amazon NON si genera la scheda: le regole Amazon vietano di modificare le foto
dei prodotti e di mostrare prezzi in immagini che non si aggiornano. Lì si usa la foto originale.
"""
import io
import math
import os
from typing import Optional

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from .models import Deal
from .texts import money

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "assets", "fonts", "Archivo.ttf")
BG = os.path.join(ROOT, "assets", "card_bg.jpg")
LOGO = os.path.join(ROOT, "assets", "logo_round.png")

W, H = 1080, 1350
WINE, WINE2 = (74, 15, 21), (122, 18, 32)
RED, RED2 = (214, 24, 38), (150, 8, 22)
GOLD, GOLD2, GOLD3 = (255, 228, 138), (244, 176, 18), (190, 120, 0)
CREAM = (255, 246, 236)
INK = (40, 6, 10)

LABEL = {
    "it": {"offerta": "OFFERTA", "errore": "ERRORE DI PREZZO", "invece": "invece di", "su": "su"},
    "de": {"offerta": "DEAL", "errore": "PREISFEHLER", "invece": "statt", "su": "bei"},
    "fr": {"offerta": "BON PLAN", "errore": "ERREUR DE PRIX", "invece": "au lieu de", "su": "chez"},
}


def font(size: int, weight: int = 900, width: int = 100) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([weight, width])
    return f


def _fit(draw, text, max_w, size, weight=900, width=100, min_size=20):
    while size > min_size:
        f = font(size, weight, width)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(min_size, weight, width)


def _wrap(draw, text, f, max_w, max_lines=2):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    used = " ".join(lines)
    if len(used) < len(text.strip()):
        last = lines[-1]
        while last and draw.textlength(last + "…", font=f) > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip(" ,-–") + "…"
    return lines


def _gradient(size, top, bottom):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h))


def _rounded(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


def _italic_text(img, xy, text, f, fill, shear=0.18, stroke=0, stroke_fill=None, anchor="la", shadow=None):
    """Testo inclinato (stile del titolo dell'immagine principale)."""
    d0 = ImageDraw.Draw(img)
    bbox = d0.textbbox((0, 0), text, font=f, stroke_width=stroke, anchor="la")
    tw, th = bbox[2] - bbox[0] + int(abs(shear) * (bbox[3]) ) + 20, bbox[3] + 20
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((10 - bbox[0], 10), text, font=f, fill=fill,
                               stroke_width=stroke, stroke_fill=stroke_fill)
    layer = layer.transform(layer.size, Image.AFFINE, (1, shear, -shear * th, 0, 1, 0), Image.BICUBIC)
    x, y = xy
    if anchor[0] == "m":
        x -= tw // 2
    elif anchor[0] == "r":
        x -= tw
    if anchor[1] == "m":
        y -= th // 2
    if shadow:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        sh.putalpha(layer.getchannel("A").filter(ImageFilter.GaussianBlur(shadow[2])))
        sh = Image.composite(Image.new("RGBA", layer.size, shadow[3]), sh, sh.getchannel("A"))
        img.alpha_composite(sh, (x + shadow[0], y + shadow[1]))
    img.alpha_composite(layer, (x, y))
    return tw, th


def _gold_text(img, xy, text, f, anchor="la", shear=0.18):
    """Scritta oro con sfumatura e bordo scuro."""
    d0 = ImageDraw.Draw(img)
    bb = d0.textbbox((0, 0), text, font=f, stroke_width=6)
    w, h = bb[2] - bb[0] + 30, bb[3] - bb[1] + 30
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((15 - bb[0], 15 - bb[1]), text, font=f, fill=255)
    stroke = Image.new("L", (w, h), 0)
    ImageDraw.Draw(stroke).text((15 - bb[0], 15 - bb[1]), text, font=f, fill=255, stroke_width=6, stroke_fill=255)
    grad = _gradient((w, h), (255, 240, 170), GOLD2).convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    layer.paste(Image.new("RGBA", (w, h), INK + (255,)), (0, 0), stroke)
    layer.paste(grad, (0, 0), mask)
    layer = layer.transform(layer.size, Image.AFFINE, (1, shear, -shear * h * 0.5, 0, 1, 0), Image.BICUBIC)
    x, y = xy
    if anchor[0] == "m":
        x -= w // 2
    elif anchor[0] == "r":
        x -= w
    if anchor[1] == "m":
        y -= h // 2
    img.alpha_composite(layer, (x, y))
    return w, h


def _burst(r_out, r_in, points=18, rot=0.0):
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points + rot
        r = r_out if i % 2 == 0 else r_in
        pts.append((r_out + r * math.cos(a), r_out + r * math.sin(a)))
    return pts


# ------------------------------------------------------------------ stile "cattivo"
import random


def _cracks(size, seed=7, n=14, color=(70, 30, 0, 255), width=(2, 4)):
    """Crepe frastagliate come nelle lettere del titolo dell'immagine principale."""
    rnd = random.Random(seed)
    w, h = size
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        ang = rnd.uniform(0, math.pi)
        pts = [(x, y)]
        for _ in range(rnd.randint(4, 9)):
            ang += rnd.uniform(-0.9, 0.9)
            step = rnd.uniform(h * .08, h * .25)
            x, y = x + step * math.cos(ang), y + step * math.sin(ang)
            pts.append((x, y))
        d.line(pts, fill=color, width=rnd.randint(*width), joint="curve")
        hl = [(px + 1.5, py + 1.5) for px, py in pts]
        d.line(hl, fill=(255, 250, 210, 140), width=1)
    return lay


def _metal_fill(size, top, mid, bottom, band=(255, 255, 235)):
    """Metallo lucido: sfumatura verticale con riflesso orizzontale."""
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        if t < .45:
            c = [top[i] + (mid[i] - top[i]) * (t / .45) for i in range(3)]
        else:
            c = [mid[i] + (bottom[i] - mid[i]) * ((t - .45) / .55) for i in range(3)]
        if .40 < t < .50:   # riflesso
            k = 1 - abs(t - .45) / .05
            c = [c[i] + (band[i] - c[i]) * .55 * k for i in range(3)]
        g.putpixel((0, y), tuple(int(v) for v in c))
    return g.resize((w, h)).convert("RGBA")


def metal_text(text, f, palette="gold", depth=14, shear=0.16, glow=(255, 60, 20), cracks=True, seed=3,
               stroke=7, outer=None):
    """Scritta 3D in metallo con estrusione scura, bordo nero, crepe e bagliore."""
    pal = {
        "gold": ((255, 246, 190), (247, 190, 40), (176, 96, 0), (110, 40, 0), (40, 10, 0)),
        "red": ((255, 120, 100), (255, 28, 36), (170, 0, 14), (100, 0, 8), (40, 0, 4)),
        "silver": ((255, 255, 255), (205, 205, 210), (120, 120, 128), (60, 60, 66), (15, 15, 18)),
    }[palette]
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d0.textbbox((0, 0), text, font=f, stroke_width=stroke)
    pad = depth + stroke + 40
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    org = (pad - bb[0], pad - bb[1])
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text(org, text, font=f, fill=255)
    ms = Image.new("L", (w, h), 0)
    ImageDraw.Draw(ms).text(org, text, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mo = None
    if outer:   # contorno esterno chiaro tipo adesivo, per staccare dal fondo
        mo = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mo).text(org, text, font=f, fill=255, stroke_width=stroke + outer[1], stroke_fill=255)
    # bagliore
    if glow:
        gl = Image.new("RGBA", (w, h), glow + (0,))
        gl.putalpha((mo or ms).filter(ImageFilter.GaussianBlur(22)).point(lambda v: min(255, int(v * 1.1))))
        out.alpha_composite(gl)
    if mo:
        for i in range(depth + 4, -1, -2):
            out.paste(Image.new("RGBA", (w, h), outer[0] + (255,)), (int(i * .55), i), mo)
    # estrusione 3D (verso il basso a destra)
    for i in range(depth, 0, -1):
        t = i / depth
        col = tuple(int(pal[3][k] * (1 - t) + pal[4][k] * t) for k in range(3)) + (255,)
        sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sh.paste(Image.new("RGBA", (w, h), col), (0, 0), ms)
        out.alpha_composite(sh, (int(i * .55), i))
    # bordo nero
    out.paste(Image.new("RGBA", (w, h), (12, 2, 2, 255)), (0, 0), ms)
    # riempimento metallico con crepe
    fill = _metal_fill((w, h), pal[0], pal[1], pal[2])
    if cracks:
        fill.alpha_composite(_cracks((w, h), seed=seed, n=max(6, len(text) * 2),
                                     color=pal[4] + (230,), width=(2, 5)))
    top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    top.paste(fill, (0, 0), m)
    # luce sul bordo superiore delle lettere
    edge = ImageChops_sub(m, m.transform(m.size, Image.AFFINE, (1, 0, 0, 0, 1, -3)))
    top.paste(Image.new("RGBA", (w, h), (255, 255, 230, 200)), (0, 0), edge)
    out.alpha_composite(top)
    if shear:
        out = out.transform(out.size, Image.AFFINE, (1, shear, -shear * h * .5, 0, 1, 0), Image.BICUBIC)
    return out.crop(out.getbbox())


def ImageChops_sub(a, b):
    from PIL import ImageChops
    return ImageChops.subtract(a, b)


def _paste_center(img, layer, cx, cy):
    img.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def _badge(pct: float) -> Image.Image:
    """Esplosione rossa al neon con lo sconto in metallo rosso: deve colpire subito."""
    R = 205
    size = 2 * R + 120
    c = size // 2
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    burst = [(x - R + c, y - R + c) for x, y in _burst(R, R * .74, points=16, rot=.12)]
    # alone rosso
    g = Image.new("L", (size, size), 0)
    ImageDraw.Draw(g).polygon(burst, fill=255)
    halo = Image.new("RGBA", (size, size), (255, 30, 20, 0))
    halo.putalpha(g.filter(ImageFilter.GaussianBlur(26)))
    im.alpha_composite(halo)
    # corpo: metallo nero con crepe, bordo rosso neon
    body = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    body.paste(Image.new("RGBA", (size, size), (255, 70, 50, 255)), (0, 0), g)
    inner = Image.new("L", (size, size), 0)
    ImageDraw.Draw(inner).polygon([(c + (x - c) * .93, c + (y - c) * .93) for x, y in burst], fill=255)
    core = Image.radial_gradient("L").resize((size, size))
    dark = Image.composite(Image.new("RGBA", (size, size), (20, 4, 6, 255)),
                           Image.new("RGBA", (size, size), (95, 8, 14, 255)), core)
    body.paste(dark, (0, 0), inner)
    im.alpha_composite(body)
    txt = f"-{pct:.0f}%"
    f = font(170 if len(txt) <= 4 else 146, 900, 70)
    t = metal_text(txt, f, palette="red", depth=12, shear=.14, glow=(255, 40, 20), seed=5, stroke=6,
                   outer=((255, 255, 255), 8), cracks=False)
    t.thumbnail((int(R * 1.95), int(R * 1.3)), Image.LANCZOS)
    _paste_center(im, t, c + 6, c + 4)
    return im.rotate(-8, resample=Image.BICUBIC)


def _product(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Ritaglia il prodotto se la foto ha lo sfondo bianco (anche i buchi interni, es. dentro l'archetto
    delle cuffie). Se lo sfondo non è bianco o il ritaglio non convince, restituisce la foto intera
    con img.info["cutout"] = False, così chi disegna la mette su una tessera."""
    import numpy as np
    img = ImageOps.exif_transpose(img).convert("RGBA")
    img.thumbnail((1400, 1400), Image.LANCZOS)
    rgb = np.asarray(img.convert("RGB")).astype(np.int16)
    h, w = rgb.shape[:2]
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    white_border = (border.min(axis=1) > 238).mean()
    ok = False
    if white_border > 0.55:
        try:
            import cv2
            near = (rgb.min(axis=2) >= 236) & ((rgb.max(axis=2) - rgb.min(axis=2)) <= 12)
            n, lab, stats, _ = cv2.connectedComponentsWithStats(near.astype(np.uint8), connectivity=4)
            bg = np.zeros((h, w), bool)
            edge_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
            min_hole = 0.002 * h * w
            for i in range(1, n):
                if i in edge_labels:
                    bg |= lab == i
                elif stats[i, cv2.CC_STAT_AREA] >= min_hole:
                    region = rgb[lab == i]
                    if region.mean() >= 248 and region.std() < 4:   # bianco piatto = sfondo, non prodotto
                        bg |= lab == i
            fg = ~bg
            cover = fg.mean()
            if 0.04 < cover < 0.995:
                alpha = Image.fromarray((fg * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)) \
                    .filter(ImageFilter.GaussianBlur(1.1))
                img.putalpha(alpha)
                bb = alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
                if bb:
                    img = img.crop(bb)
                ok = True
        except ImportError:
            pass
    img.thumbnail((box_w, box_h), Image.LANCZOS)
    img.info["cutout"] = ok
    return img


def _shadow(img, box, r, blur=28, alpha=150, dy=18):
    m = Image.new("L", img.size, 0)
    x0, y0, x1, y1 = box
    ImageDraw.Draw(m).rounded_rectangle([x0, y0 + dy, x1, y1 + dy], r, fill=alpha)
    img.alpha_composite(Image.composite(Image.new("RGBA", img.size, (0, 0, 0, 255)),
                                        Image.new("RGBA", img.size, (0, 0, 0, 0)), m.filter(ImageFilter.GaussianBlur(blur))))


def _text_w(d, t, f):
    return d.textlength(t, font=f)


def make_card_moderna(deal: Deal, lang: str = "it", product_img: Optional[Image.Image] = None) -> Optional[bytes]:
    """Scheda moderna: fondo vino scuro, prodotto su tessera bianca, sconto in blocco rosso,
    prezzo grande e pulito. Il marchio (crepa oro, logo) resta come dettaglio."""
    p = deal.product
    if p.source.startswith("amazon"):
        return None
    if product_img is None:
        if not p.image:
            return None
        r = requests.get(p.image, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        product_img = Image.open(io.BytesIO(r.content))
    L = LABEL.get(lang, LABEL["it"])
    err = deal.level == "errore"
    RED_F = (229, 22, 43)
    WHITE = (255, 255, 255)
    MUTED = (196, 160, 158)

    # fondo: vino quasi nero con un'ombra dell'immagine principale
    card = _gradient((W, H), (44, 6, 10), (16, 2, 4)).convert("RGBA")
    if os.path.exists(BG):
        tex = ImageOps.fit(Image.open(BG).convert("RGB"), (W, H)).convert("RGBA")
        tex.putalpha(70)
        card.alpha_composite(tex)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-200, 300, W + 200, 1100], fill=110)
    card.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (150, 14, 28, 255)),
                                         Image.new("RGBA", (W, H), (0, 0, 0, 0)), glow.filter(ImageFilter.GaussianBlur(160))))
    d = ImageDraw.Draw(card)
    M = 56

    # intestazione: logo piccolo + nome, a destra l'etichetta
    if os.path.exists(LOGO):
        lg = Image.open(LOGO).convert("RGBA").resize((76, 76), Image.LANCZOS)
        mk = Image.new("L", (76, 76), 0)
        ImageDraw.Draw(mk).ellipse([0, 0, 75, 75], fill=255)
        card.paste(lg, (M, 44), mk)
    d.text((M + 96, 82), "Offerte Crollate", font=font(34, 800, 100), fill=WHITE, anchor="lm")
    lab = L["errore"] if err else L["offerta"]
    lf = font(28, 900, 100)
    lw = _text_w(d, lab, lf) + (100 if err else 48)
    x1, x0 = W - M, W - M - lw
    if err:
        d.rounded_rectangle([x0, 56, x1, 108], 26, fill=(255, 196, 0))
        tri = [(x0 + 26, 96), (x0 + 42, 68), (x0 + 58, 96)]
        d.polygon(tri, fill=INK)
        d.text((x0 + 42, 89), "!", font=font(20, 900, 100), fill=(255, 196, 0), anchor="ms")
        d.text((x0 + 70, 82), lab, font=lf, fill=INK, anchor="lm")
    else:
        d.rounded_rectangle([x0, 56, x1, 108], 26, outline=(255, 255, 255, 170), width=3)
        d.text((x0 + 24, 82), lab, font=lf, fill=WHITE, anchor="lm")

    # tessera bianca con il prodotto
    tx0, ty0, tx1, ty1 = M, 150, W - M, 860
    _shadow(card, (tx0, ty0, tx1, ty1), 44)
    tile = Image.new("RGBA", (tx1 - tx0, ty1 - ty0), (0, 0, 0, 0))
    tile.paste(Image.new("RGBA", tile.size, (255, 255, 255, 255)), (0, 0), _rounded(tile.size, 44))
    prod = _product(product_img, tile.width - 140, tile.height - 120)
    ox, oy = (tile.width - prod.width) // 2, (tile.height - prod.height) // 2 + 30
    if prod.mode == "RGBA":
        sh = Image.new("L", tile.size, 0)
        sh.paste(prod.getchannel("A"), (ox, oy + 18))
        tile.alpha_composite(Image.composite(Image.new("RGBA", tile.size, (0, 0, 0, 255)),
                                             Image.new("RGBA", tile.size, (0, 0, 0, 0)),
                                             sh.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * .18))))
        tile.alpha_composite(prod, (ox, oy))
    else:
        tile.paste(prod, (ox, oy))
    card.alpha_composite(tile, (tx0, ty0))

    # sconto: blocco rosso pieno sull'angolo in alto a sinistra della tessera
    pct = f"-{deal.discount_pct:.0f}%"
    pf = font(150, 900, 66)
    pw = _text_w(d, pct, pf)
    bw, bh = int(pw + 70), 190
    blk = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blk)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], 30, fill=RED_F)
    bd.text((bw // 2, bh // 2 + 4), pct, font=pf, fill=WHITE, anchor="mm")
    bx, by = tx0 - 14, ty0 - 26
    _shadow(card, (bx, by, bx + bw, by + bh), 30, blur=20, alpha=170, dy=12)
    card.alpha_composite(blk, (bx, by))

    # nome del prodotto
    nf = font(40, 700, 100)
    lines = _wrap(d, p.name, nf, W - 2 * M, 2)
    y = 900
    for ln in lines:
        d.text((M, y), ln, font=nf, fill=(246, 230, 226))
        y += 52

    # prezzo: grande e pulito; vecchio prezzo barrato accanto
    new = money(p.price, p.currency)
    old = money(deal.reference_price, p.currency)
    nfp = _fit(d, new, 640, 170, 900, 70)
    base = 1190
    d.text((M - 4, base), new, font=nfp, fill=WHITE, anchor="ls")
    nw = _text_w(d, new, nfp)
    of = font(46, 700, 90)
    ox = M + nw + 34
    if ox + _text_w(d, old, of) > W - M:     # se non ci sta, va sopra il prezzo
        ox, oy = M, base - 190
    else:
        oy = base - 14
    d.text((ox, oy - 62), L["invece"], font=font(26, 600, 100), fill=MUTED, anchor="ls")
    d.text((ox, oy), old, font=of, fill=MUTED, anchor="ls")
    ow = _text_w(d, old, of)
    d.line([(ox - 4, oy - 13), (ox + ow + 4, oy - 13)], fill=RED_F, width=5)

    # riga finale: negozio e sito, con la crepa oro del marchio come separatore
    d.line([(M, 1236), (W - M, 1236)], fill=(255, 255, 255, 40), width=2)
    sf = font(30, 700, 100)
    d.text((M, 1290), f'{L["su"]} {p.shop}', font=sf, fill=(246, 230, 226), anchor="lm")
    d.text((W - M, 1290), "offertecrollate.ch", font=font(30, 800, 100), fill=GOLD2, anchor="rm")

    out = io.BytesIO()
    card.convert("RGB").save(out, "JPEG", quality=90, optimize=True)
    return out.getvalue()


def make_card(deal: Deal, lang: str = "it", product_img: Optional[Image.Image] = None,
              style: str = "crollata") -> Optional[bytes]:
    """Immagine dell'offerta. Predefinito: "crollata" (stile dell'esempio delle cuffie scelto da Giuseppe:
    logo a pennellata, sconto su pennellata rossa, prezzo nel riquadro rosso). Restano "semplice", "crollo", "moderna"."""
    p = deal.product
    # Amazon: card come tutte le altre solo se c'è il prezzo medio vero (Keepa), su richiesta di Giuseppe
    if p.source.startswith("amazon") and not (deal.reference_price and deal.reference_price > p.price):
        return None
    if style in ("semplice", "crollata"):
        from .card_semplice import make as make_semplice, hd_url
        from .card_crollata import make as make_crollata
        if product_img is None:
            if not p.image:
                return None
            r = requests.get(hd_url(p.image), timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code >= 400:
                r = requests.get(p.image, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            product_img = Image.open(io.BytesIO(r.content))
        fn = make_crollata if style == "crollata" else make_semplice
        if fn is make_crollata:
            return fn(p.name, p.price, deal.reference_price, p.currency, p.shop, product_img,
                      rating=deal.extra.get("rating"), reviews=deal.extra.get("reviews"))
        return fn(p.name, p.price, deal.reference_price, p.currency, p.shop, product_img)
    if style == "moderna":
        return make_card_moderna(deal, lang, product_img)
    if product_img is None:
        if not p.image:
            return None
        r = requests.get(p.image, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        product_img = Image.open(io.BytesIO(r.content))
    from . import card_crollo
    out = io.BytesIO()
    card_crollo.make(deal, lang, product_img).convert("RGB").save(out, "JPEG", quality=90, optimize=True)
    return out.getvalue()
