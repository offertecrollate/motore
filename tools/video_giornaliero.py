"""Ogni giorno: video verticale "Offerte crollate di oggi" (TikTok / Reel) con le offerte più forti del sito,
mandato in privato a Giuseppe sul bot Telegram. Senza musica: la musica di tendenza si aggiunge nell'app.
Uso: python tools/video_giornaliero.py site_it/deals.json   (segreti: TELEGRAM_TOKEN, ALERT_CHAT_ID)"""
import datetime as dt, io, json, os, subprocess, sys
import numpy as np, requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
A = os.path.join(os.path.dirname(__file__), "..", "assets") + "/"
MB, AN = A + "fonts/Montserrat.ttf", A + "fonts/Anton.ttf"
RED, YEL, FBB = (227, 6, 19), (255, 212, 0), (24, 119, 242)
N, DUR_I, DUR_D, DUR_O = 6, 2.2, 2.4, 3.0
OUT = "/tmp/video"


def F(p, s): return ImageFont.truetype(p, s)
def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def back(t):
    t = max(0, min(1, t)); c1 = 1.7; c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def fmt(v, cur): return (("%.2f" % v).replace(".", ",") + " €") if cur == "EUR" else ("CHF %.2f" % v)


def scegli(path):
    d = [x for x in json.load(open(path, encoding="utf-8")) if x.get("image") and x.get("category") != "Adulti 18+"
         and x.get("ref") and x["ref"] > x["price"] > 0 and 30 <= x.get("pct", 0) <= 95]
    ieri = (dt.datetime.now() - dt.timedelta(hours=30)).isoformat()
    recenti = [x for x in d if x.get("at", "") >= ieri] or d
    recenti.sort(key=lambda x: -x["pct"])
    per, out = {}, []
    for x in recenti:                      # al massimo 2 per negozio, così il video è vario
        if per.get(x["shop"], 0) < 2:
            per[x["shop"]] = per.get(x["shop"], 0) + 1; out.append(x)
        if len(out) == N:
            break
    imgs = []
    for x in out:
        try:
            r = requests.get(x["image"], timeout=20, headers={"User-Agent": "Mozilla/5.0"}); r.raise_for_status()
            imgs.append((x, Image.open(io.BytesIO(r.content)).convert("RGBA")))
        except Exception as e:
            print("immagine non scaricata:", x["name"][:40], e)
    return imgs


def bg():
    im = Image.new("RGB", (W, H), (8, 6, 10)); g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse([-300, 300, W + 300, 1700], fill=200); g = g.filter(ImageFilter.GaussianBlur(220))
    im.paste(Image.new("RGB", (W, H), (120, 0, 8)), (0, 0), g); return im


BG = bg()
LOGO = Image.open(A + "logo_dark.png").convert("RGBA")


def logo_at(im, x, y, w):
    l = LOGO.resize((w, int(LOGO.height * w / LOGO.width)), Image.LANCZOS); im.paste(l, (int(x), int(y)), l)


def ctext(d, y, txt, font, fill):
    d.text(((W - d.textlength(txt, font=font)) / 2, y), txt, font=font, fill=fill)


def wrap(d, txt, font, maxw, n=2):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur); lines = [l for l in lines if l]
    if len(lines) > n:
        lines = lines[:n]; lines[-1] = lines[-1].rstrip(",.;") + "…"
    return lines


def intro(maxp, oggi):
    def fr(t):
        im = BG.copy(); d = ImageDraw.Draw(im)
        s = back(t / 0.5); w = max(10, int(720 * s)); logo_at(im, (W - w) / 2, 360, w)
        for k, (txt, col) in enumerate((("LE OFFERTE", (255, 255, 255)), ("PIÙ CROLLATE", YEL), ("DI OGGI", (255, 255, 255)))):
            a = ease((t - 0.3 - 0.15 * k) / 0.35)
            if a > 0:
                f = F(AN, 130); tw = d.textlength(txt, font=f)
                lay = Image.new("RGBA", (W, 200), (0, 0, 0, 0)); ImageDraw.Draw(lay).text(((W - tw) / 2, 0), txt, font=f, fill=col + (int(255 * a),))
                im.paste(lay, (int((1 - a) * -200), 820 + k * 150), lay)
        b = back((t - 1.0) / 0.4)
        if b > 0:
            f = F(AN, 150); txt = "FINO AL -%d%%" % maxp; tw = d.textlength(txt, font=f)
            lay = Image.new("RGBA", (int(tw) + 80, 210), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([0, 5, tw + 79, 205], radius=26, fill=RED + (255,)); ld.text((40, 0), txt, font=f, fill=(255, 255, 255))
            lay = lay.resize((max(1, int(lay.width * b)), max(1, int(lay.height * b))), Image.LANCZOS).rotate(-4, expand=True, resample=Image.BICUBIC)
            im.paste(lay, ((W - lay.width) // 2, 1320), lay)
        ctext(d, 1700, oggi, F(MB, 44), (220, 220, 220))
        return im
    return fr


def deal(x, prod, i, n):
    def fr(t):
        im = BG.copy(); d = ImageDraw.Draw(im)
        logo_at(im, 60, 70, 280)
        d.rounded_rectangle([60, 215, W - 60, 225], radius=5, fill=(70, 40, 40))
        d.rounded_rectangle([60, 215, 60 + (W - 120) * (i + min(1, t / DUR_D)) / n, 225], radius=5, fill=YEL)
        f = F(MB, 40); txt = "%d/%d" % (i + 1, n); d.text((W - 60 - d.textlength(txt, font=f), 105), txt, font=f, fill=(210, 210, 210))
        a = ease(t / 0.25); cy = 300 + int((1 - a) * 160)
        card = Image.new("RGBA", (900, 860), (255, 255, 255, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, 899, 859], radius=48, fill=(255, 255, 255, 255))
        m = 720 * (1.0 + 0.05 * (t / DUR_D)); r = min(m / prod.width, m / prod.height)
        pr = prod.resize((max(1, int(prod.width * r)), max(1, int(prod.height * r))), Image.LANCZOS)
        card.paste(pr, ((900 - pr.width) // 2, (860 - pr.height) // 2), pr)
        mask = Image.new("L", (900, 860), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, 899, 859], radius=48, fill=255)
        card.putalpha(Image.fromarray(np.minimum(np.array(card.split()[3]), np.array(mask))))
        im.paste(card, (90, cy), card)
        s = back((t - 0.15) / 0.3)
        if s > 0:
            f = F(AN, 170); txt = "-%d%%" % round(x["pct"]); tw = int(d.textlength(txt, font=f))
            b = Image.new("RGBA", (tw + 80, 230), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
            bd.rounded_rectangle([0, 0, tw + 79, 229], radius=30, fill=RED + (255,)); bd.text((40, -10), txt, font=f, fill=(255, 255, 255))
            b = b.resize((max(1, int(b.width * s)), max(1, int(b.height * s))), Image.LANCZOS).rotate(8, expand=True, resample=Image.BICUBIC)
            im.paste(b, (W - 40 - b.width, 250), b)
        c = ease((t - 0.3) / 0.3)
        if c > 0:
            y = 1200; x0 = int(-300 * (1 - c)); cur = x.get("currency", "EUR")
            f2 = F(MB, 64); old = fmt(x["ref"], cur); d.text((90 + x0, y), old, font=f2, fill=(200, 200, 200))
            ow = d.textlength(old, font=f2); d.line([(85 + x0, y + 46), (95 + x0 + ow, y + 38)], fill=RED, width=8)
            f3 = F(AN, 190); new = fmt(x["price"], cur); nw = d.textlength(new, font=f3)
            d.rounded_rectangle([70 + x0, y + 95, 130 + x0 + nw, y + 335], radius=30, fill=YEL); d.text((100 + x0, y + 95), new, font=f3, fill=(15, 10, 10))
        e = ease((t - 0.45) / 0.3)
        if e > 0:
            f4 = F(MB, 50); lines = wrap(d, x["name"], f4, 900)
            for k, ln in enumerate(lines):
                d.text((90, 1580 + k * 62), ln, font=f4, fill=(255, 255, 255))
            d.text((90, 1580 + len(lines) * 62 + 12), "su " + x["shop"] + "  ·  #ADV", font=F(MB, 38), fill=YEL)
        return im
    return fr


def outro(oggi):
    def fr(t):
        im = BG.copy(); d = ImageDraw.Draw(im)
        a = ease(t / 0.4); logo_at(im, (W - 700) / 2, 230, 700)
        if a > 0:
            for k, (txt, col) in enumerate((("ERRORI DI PREZZO", (255, 255, 255)), ("E OFFERTE FORTI", (255, 255, 255)), ("OGNI ORA", YEL))):
                ctext(d, 760 + k * 120 + int((1 - a) * 50), txt, F(AN, 112), col)
        b = back((t - 0.5) / 0.45)
        if b > 0:
            box = Image.new("RGBA", (860, 180), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            bd.rounded_rectangle([0, 0, 859, 179], radius=90, fill=RED + (255,))
            f = F(MB, 66); txt = "Link sul canale Telegram"; bd.text(((860 - bd.textlength(txt, font=f)) / 2, 48), txt, font=f, fill=(255, 255, 255))
            box = box.resize((max(1, int(860 * b)), max(1, int(180 * b))), Image.LANCZOS); im.paste(box, ((W - box.width) // 2, 1180 + (180 - box.height) // 2), box)
        c = ease((t - 0.9) / 0.4)
        if c > 0:
            ctext(d, 1410, "Offerte Crollate", F(MB, 64), (255, 255, 255))
            ctext(d, 1500, "offertecrollate.it  ·  offertecrollate.ch", F(MB, 44), (220, 220, 220))
            ctext(d, 1770, "Prezzi del %s: possono cambiare. Link affiliati #ADV." % oggi, F(MB, 26), (160, 160, 160))
        return im
    return fr


def render(fn, dur, out):
    n = int(round(dur * FPS)); tmp = out + ".tmp.mp4"
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(n):
        pr.stdin.write(fn(k / FPS).convert("RGB").tobytes())
    pr.stdin.close(); assert pr.wait() == 0; os.replace(tmp, out)


def main():
    os.makedirs(OUT, exist_ok=True)
    scelte = scegli(sys.argv[1] if len(sys.argv) > 1 else "site_it/deals.json")
    if not scelte:
        print("nessuna offerta con immagine"); return
    oggi = dt.date.today().strftime("%d/%m/%Y")
    scenes = [(f"{OUT}/s00.mp4", intro(round(max(x['pct'] for x, _ in scelte)), oggi), DUR_I)]
    scenes += [(f"{OUT}/s%02d.mp4" % (i + 1), deal(x, p, i, len(scelte)), DUR_D) for i, (x, p) in enumerate(scelte)]
    scenes += [(f"{OUT}/s99.mp4", outro(oggi), DUR_O)]
    for out, fn, dur in scenes:
        render(fn, dur, out)
    open(f"{OUT}/list.txt", "w").write("".join("file '%s'\n" % s[0] for s in scenes))
    video = f"{OUT}/offerte_crollate_{dt.date.today():%Y%m%d}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{OUT}/list.txt", "-c", "copy",
                    "-movflags", "+faststart", video], check=True)
    righe = "\n".join("• -%d%% %s (%s)" % (round(x["pct"]), x["name"][:60], x["shop"]) for x, _ in scelte)
    didascalia = ("🎬 Video di oggi per TikTok / Reel\n\nTesto da copiare:\n"
                  "🔥 Le offerte più crollate di oggi! Fino al -%d%% 😱 Link sul canale Telegram Offerte Crollate 👉 profilo #ADV "
                  "#offerte #erroridiprezzo #amazon #blackfriday #risparmio #tech\n\nProdotti:\n%s") % (
                      round(max(x['pct'] for x, _ in scelte)), righe)
    tok, chat = os.environ.get("TELEGRAM_TOKEN", "").strip(), os.environ.get("ALERT_CHAT_ID", "").strip()
    if tok and chat:
        with open(video, "rb") as f:
            r = requests.post(f"https://api.telegram.org/bot{tok}/sendVideo", timeout=300,
                              data={"chat_id": chat, "caption": didascalia[:1024], "supports_streaming": "true", "width": W, "height": H},
                              files={"video": f})
        print(r.status_code, r.text[:200]); r.raise_for_status()
    else:
        print("video pronto:", video)


if __name__ == "__main__":
    main()
