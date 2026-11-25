"""Nuovo look del sito (approvato da Giuseppe il 14/11/2026, grafica "Offerte Crollate – nuovo look dei siti").

Fondo nero, logo a pennellata, menu Home / Offerte / Errori di prezzo / Preferiti, banner con il monumento del
paese, pulsanti Community / Pagina Facebook / Telegram / altro paese, ricerca, sconto minimo ≥30/50/70,
negozi, categorie a icone, schede bianche con "Vai all'offerta". Una pagina per lingua (it, de, fr).
"""
import hashlib
import html
import json
import os
import re
import shutil
from datetime import datetime

from . import categories as cats
from .texts import money
from .site import (_axis_money, _short_date, COUNTRY, FB_URL, FLAG_SVG, GROUP_URL, TG_URL, UI, _og, _shop_id, _ts,
                   base_url, is_amazon)


def _svg(path: str, size: int = 22, sw: float = 2) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg>')


I = {  # icone a tratto
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18a14 14 0 0 1 0-18z"/>',
    "home": '<path d="M3 11 12 3.5 21 11"/><path d="M5.5 9.5V20h13V9.5"/>',
    "offers": '<path d="M3 12V4.5A1.5 1.5 0 0 1 4.5 3H12l9 9-9 9z"/><circle cx="7.5" cy="7.5" r="1.3"/>',
    "errors": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "favs": '<path d="M12 20.5s-8-4.7-8-10.6A4.4 4.4 0 0 1 12 7.3a4.4 4.4 0 0 1 8 2.6c0 5.9-8 10.6-8 10.6z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    "filter": '<path d="M3 4h18l-7 8.5V19l-4 2v-8.5z"/>',
    "shop": '<path d="M3 9.5 4.5 4h15L21 9.5"/><path d="M3 9.5h18v1a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z"/><path d="M5 13v7.5h14V13"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "arrow": '<path d="M7 17 17 7M9 7h8v8"/>',
    "group": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.8"/><path d="M16.5 14.2a5.5 5.5 0 0 1 5 5.8"/>',
    "shield": '<path d="M12 2.5 4 6v6c0 4.6 3.4 8.5 8 9.5 4.6-1 8-4.9 8-9.5V6z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "truck": '<path d="M1.5 6.5h12v10h-12zM13.5 10h4.5l3 3.5v3h-7.5"/><circle cx="6" cy="17.5" r="2"/><circle cx="17" cy="17.5" r="2"/>',
    "chshield": '<path d="M12 2.5 4 6v6c0 4.6 3.4 8.5 8 9.5 4.6-1 8-4.9 8-9.5V6z"/><path d="M12 8v8M8 12h8"/>',
    "chart": '<path d="M3 20h18"/><path d="m4 15 5-5 4 3 7-7"/>',
}
CAT_ICON = {
    "adulti": '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
    "smartphone": '<rect x="7" y="2.5" width="10" height="19" rx="2"/><path d="M11 18.5h2"/>',
    "informatica": '<rect x="3" y="4.5" width="18" height="12" rx="1.5"/><path d="M1.5 19.5h21"/>',
    "tv_audio": '<path d="M3.5 17v-4a8.5 8.5 0 0 1 17 0v4"/><rect x="3" y="14" width="4" height="7" rx="1.5"/><rect x="17" y="14" width="4" height="7" rx="1.5"/>',
    "elettrodomestici": '<rect x="4" y="2.5" width="16" height="19" rx="2"/><circle cx="12" cy="13" r="4.5"/><path d="M7 5.5h2"/>',
    "giochi": '<path d="M7 8.5h10a4.5 4.5 0 0 1 4.3 5.8l-.9 3a2.3 2.3 0 0 1-3.9.9L14.8 16H9.2l-1.7 2.2a2.3 2.3 0 0 1-3.9-.9l-.9-3A4.5 4.5 0 0 1 7 8.5z"/><path d="M8 11v3M6.5 12.5h3"/>',
    "casa": '<path d="M3 11 12 3.5 21 11"/><path d="M5.5 9.5V20h13V9.5"/><path d="M10 20v-6h4v6"/>',
    "sport": '<path d="M6.5 6.5v11M17.5 6.5v11M3.5 9v6M20.5 9v6M6.5 12h11"/>',
    "bellezza": '<path d="M9 2.5h6v4H9z"/><path d="M8 6.5h8l1 15H7z"/><path d="M10 11h4"/>',
    "moda": '<path d="M8 7V5.5a4 4 0 0 1 8 0V7"/><path d="M4.5 7h15l-1 14h-13z"/>',
    "altro": '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
}
FB = '<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7.1V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.4l-.5 3.5h-2.9v8.4A12 12 0 0 0 24 12z"/></svg>'
TG = '<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24zm5.9 8.2-2 9.4c-.1.7-.5.8-1.1.5l-3-2.2-1.5 1.4c-.2.2-.3.3-.6.3l.2-3.1 5.6-5c.2-.2 0-.3-.4-.1l-6.9 4.3-3-.9c-.6-.2-.7-.6.1-1l11.6-4.5c.6-.2 1.1.1.9.9z"/></svg>'

T = {
 "it": {"topdeal": "L'offerta più crollata di oggi", "tg_b": "Gli errori di prezzo? Ricevili sul telefono.", "tg_s": "Iscriviti gratis al canale Telegram ›", "fb_s": "Condividi e commenta le offerte con gli altri ›", "search_go": "Cerca", "home": "Home", "offers": "Offerte", "errors": "Errori di prezzo", "errors_s": "Errori", "maybe": "Possibile errore", "favs": "Preferiti",
        "best": "Le migliori offerte", "in_it": "in Italia", "in_ch": "in Svizzera",
        "h1a": "I prezzi crollano.", "h1b": "Le occasioni volano.",
        "sub_it": "Le migliori offerte, sconti reali ed errori di prezzo dei negozi online in Italia, con prezzi controllati in meno di un'ora.",
        "sub_ch": "Le migliori offerte, sconti reali ed errori di prezzo dei negozi online in Svizzera, con prezzi controllati in meno di un'ora.",
        "group": "Community Facebook", "page": "Pagina Facebook", "goto": "Passa al sito",
        "search": "Cerca offerte, prodotti, negozi…", "filter": "Filtra le offerte", "min": "Sconto minimo",
        "allshops": "Tutti i negozi", "cats": "Categorie prodotti", "allcats": "Tutte le categorie", "cshow": "Mostra offerte", "cclr": "Azzera", "go": "Vai all'offerta",
        "instead": "invece di", "none": "Nessuna offerta con questi filtri.", "reset": "Mostra tutte",
        "nofav": "Tocca il cuore su un'offerta per salvarla qui: resta salvata su questo telefono o computer.",
        "fav_add": "Salva nei preferiti", "fav_del": "Togli dai preferiti", "chart": "Andamento del prezzo",
        "one": "offerta", "many": "offerte",
        "t1": "Prezzi controllati", "d1": "Ricontrolliamo i prezzi in meno di un'ora",
        "t2": "Sconti reali", "d2": "Confrontati con il prezzo degli ultimi mesi",
        "t3": "Community attiva", "d3": "Unisciti ai nostri canali Facebook e Telegram",
        "t4_it": "Negozi italiani", "d4_it": "Le migliori promozioni dei negozi online in Italia",
        "t4_ch": "Per la Svizzera", "d4_ch": "Negozi e spedizioni pensati per la Svizzera",
        "soon": "Stiamo collegando i negozi: le prime offerte arrivano a breve. Intanto seguici per non perderle.",
        "top": "Torna su", "privacy": "Info e privacy", "other_it": "Italia", "other_ch": "Svizzera"},
 "de": {"topdeal": "Der grösste Preissturz heute", "tg_b": "Preisfehler? Direkt aufs Handy.", "tg_s": "Kostenlos dem Telegram-Kanal beitreten ›", "fb_s": "Angebote teilen und kommentieren ›", "search_go": "Suchen", "home": "Home", "offers": "Angebote", "errors": "Preisfehler", "errors_s": "Fehler", "maybe": "Möglicher Fehler", "favs": "Favoriten",
        "best": "Die besten Angebote", "in_ch": "in der Schweiz", "in_it": "in Italien",
        "h1a": "Die Preise fallen.", "h1b": "Die Schnäppchen fliegen.",
        "sub_ch": "Die besten Angebote, echte Rabatte und Preisfehler der Online-Shops in der Schweiz, Preise mindestens einmal pro Stunde geprüft.",
        "group": "Facebook-Community", "page": "Facebook-Seite", "goto": "Zur Seite",
        "search": "Angebote, Produkte, Shops suchen…", "filter": "Angebote filtern", "min": "Mindestrabatt",
        "allshops": "Alle Shops", "cats": "Produktkategorien", "allcats": "Alle Kategorien", "cshow": "Angebote anzeigen", "cclr": "Zurücksetzen", "go": "Zum Angebot",
        "instead": "statt", "none": "Keine Angebote mit diesen Filtern.", "reset": "Alle anzeigen",
        "nofav": "Tippe auf das Herz eines Angebots, um es hier zu speichern: Es bleibt auf diesem Gerät gespeichert.",
        "fav_add": "Zu den Favoriten", "fav_del": "Aus den Favoriten entfernen", "chart": "Preisverlauf",
        "one": "Angebot", "many": "Angebote",
        "t1": "Geprüfte Preise", "d1": "Wir prüfen die Preise mindestens einmal pro Stunde",
        "t2": "Echte Rabatte", "d2": "Verglichen mit dem Preis der letzten Monate",
        "t3": "Aktive Community", "d3": "Folge unseren Kanälen auf Facebook und Telegram",
        "t4_ch": "Für die Schweiz", "d4_ch": "Shops und Lieferungen für die Schweiz",
        "soon": "Wir verbinden gerade die Shops: Die ersten Angebote kommen bald. Folge uns, um keine zu verpassen.",
        "top": "Nach oben", "privacy": "Info und Datenschutz", "other_it": "Italien", "other_ch": "Schweiz"},
 "fr": {"topdeal": "La plus forte baisse du jour", "tg_b": "Les erreurs de prix ? Reçois-les sur ton téléphone.", "tg_s": "Rejoins gratuitement la chaîne Telegram ›", "fb_s": "Partage et commente les offres ›", "search_go": "Chercher", "home": "Accueil", "offers": "Offres", "errors": "Erreurs de prix", "errors_s": "Erreurs", "maybe": "Erreur possible", "favs": "Favoris",
        "best": "Les meilleures offres", "in_ch": "en Suisse", "in_it": "en Italie",
        "h1a": "Les prix s'effondrent.", "h1b": "Les bonnes affaires s'envolent.",
        "sub_ch": "Les meilleures offres, vraies réductions et erreurs de prix des boutiques en ligne en Suisse, prix vérifiés au moins une fois par heure.",
        "group": "Communauté Facebook", "page": "Page Facebook", "goto": "Aller au site",
        "search": "Chercher offres, produits, boutiques…", "filter": "Filtrer les offres", "min": "Réduction minimum",
        "allshops": "Toutes les boutiques", "cats": "Catégories de produits", "allcats": "Toutes les catégories", "cshow": "Voir les offres", "cclr": "Réinitialiser", "go": "Voir l'offre",
        "instead": "au lieu de", "none": "Aucune offre avec ces filtres.", "reset": "Tout afficher",
        "nofav": "Touche le cœur d'une offre pour l'enregistrer ici : elle reste sur cet appareil.",
        "fav_add": "Ajouter aux favoris", "fav_del": "Retirer des favoris", "chart": "Évolution du prix",
        "one": "offre", "many": "offres",
        "t1": "Prix vérifiés", "d1": "Nous vérifions les prix au moins une fois par heure",
        "t2": "Vraies réductions", "d2": "Comparées au prix des derniers mois",
        "t3": "Communauté active", "d3": "Rejoins nos canaux Facebook et Telegram",
        "t4_ch": "Pour la Suisse", "d4_ch": "Boutiques et livraisons pensées pour la Suisse",
        "soon": "Nous connectons les boutiques : les premières offres arrivent bientôt. Suis-nous pour ne rien manquer.",
        "top": "Haut de page", "privacy": "Infos et confidentialité", "other_it": "Italie", "other_ch": "Suisse"},
}
LANG_NAME = {"it": "Italiano", "de": "Deutsch", "fr": "Français"}

# ---------------------------------------------------------------- grafico dell'andamento del prezzo (v2)
CHART_T = {
    "it": {"min": "Minimo", "max": "Massimo", "now": "Oggi", "avg90": "Prezzo barrato Amazon", "ref": "Prezzo prima",
           "days": "gg"},
    "de": {"min": "Tiefstpreis", "max": "Höchstpreis", "now": "Heute", "avg90": "Streichpreis Amazon", "ref": "Vorher",
           "days": "Tage"},
    "fr": {"min": "Plus bas", "max": "Plus haut", "now": "Aujourd'hui", "avg90": "Prix barré Amazon", "ref": "Avant",
           "days": "j"},
}
SHIP_CH = {"it": "Controlla nel carrello la spedizione in Svizzera",
           "de": "Versand in die Schweiz im Warenkorb prüfen",
           "fr": "Vérifie la livraison en Suisse dans le panier"}
CW, CH_, CL, CR, CT, CB = 300, 150, 40, 10, 12, 22     # misure del disegno (viewBox)


def _nice_ticks(lo: float, hi: float) -> list:
    import math
    span = max(hi - lo, 0.01)
    step = 10 ** math.floor(math.log10(span / 2))
    for m in (1, 2, 2.5, 5, 10):
        if span / (step * m) <= 3:
            step *= m
            break
    first = math.floor(lo / step) * step
    ticks, v = [], first
    while v <= hi + step * 0.01:
        ticks.append(round(v, 2))
        v += step
    return ticks


def _chart(it: dict, lang: str) -> str:
    """Andamento del prezzo: gradini (il prezzo resta uguale finché non cambia), asse del tempo con le date vere,
    area sotto la linea, linea tratteggiata del prezzo di riferimento, minimo e prezzo di oggi evidenziati,
    riepilogo sotto (minimo, massimo, oggi). Solo se racconta qualcosa: almeno 5 giorni e prezzo che si muove."""
    from datetime import date as _d
    hist = [(d, float(p)) for d, p in (it.get("history") or []) if p]
    if len(hist) < 5 or len({p for _, p in hist}) < 2:
        return ""
    ct, cur = CHART_T.get(lang, CHART_T["it"]), it["currency"]
    keepa = str(it.get("source", "")).startswith("amazon")
    days = [_d.fromisoformat(d) for d, _ in hist]
    today = max(days[-1], _d.today())
    prices = [p for _, p in hist] + [it["price"]]
    ref = it.get("ref") or None
    lo, hi = min(prices), max(prices + ([ref] if ref else []))
    ticks = _nice_ticks(lo * 0.95, hi * 1.02)
    ylo, yhi = min(ticks[0], lo), max(ticks[-1], hi)
    t0, t1 = days[0], today
    span = max((t1 - t0).days, 1)
    X = lambda d: CL + (CW - CL - CR) * (d - t0).days / span
    Y = lambda v: CT + (CH_ - CT - CB) * (1 - (v - ylo) / ((yhi - ylo) or 1))
    # punti a gradino
    pts = []
    for i, (d, p) in enumerate(zip(days, (p for _, p in hist))):
        if i:
            pts.append((X(d), Y(pts[-1][2]), pts[-1][2]))
        pts.append((X(d), Y(p), p))
    pts.append((X(t1), Y(it["price"]), it["price"]))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)
    area = f"M{pts[0][0]:.1f},{CH_ - CB} L" + " L".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts) + f" L{pts[-1][0]:.1f},{CH_ - CB} Z"
    grid = "".join(
        f'<line x1="{CL}" x2="{CW - CR}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="cg"/>'
        f'<text x="{CL - 6}" y="{Y(v) + 3.5:.1f}" class="cax" text-anchor="end">{html.escape(_axis_money(v, cur))}</text>'
        for v in ticks)
    mid = t0 + (t1 - t0) / 2
    xax = "".join(f'<text x="{X(d):.1f}" y="{CH_ - 6}" class="cax" text-anchor="{a}">{_short_date(d.isoformat())}</text>'
                  for d, a in ((t0, "start"), (mid, "middle"), (t1, "end")))
    ref_svg = ""
    if ref:
        ref_svg = (f'<line x1="{CL}" x2="{CW - CR}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" class="cref"/>')
    pmin = min(p for _, p in hist)
    dmin = next(d for d, (_, p) in zip(days, hist) if p == pmin)
    mark = (f'<circle cx="{X(dmin):.1f}" cy="{Y(pmin):.1f}" r="3.5" class="cmin"/>'
            f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="5" class="cnow"/>')
    data = json.dumps([[round(x, 1), _short_date(days[min(i // 2, len(days) - 1)].isoformat()) if i < len(pts) - 1
                        else _short_date(t1.isoformat()), money(p, cur)] for i, (x, _, p) in enumerate(pts)][::1],
                      ensure_ascii=False)
    leg = (f'<span><i class="l1"></i>{ct["avg90"] if keepa else ct["ref"]}'
           f'{": " + html.escape(money(ref, cur)) if ref else ""}</span>' if ref else "")
    return (
        f'<figure class="pchart"><figcaption>{leg}<span class="cdays">{(t1 - t0).days + 1} {ct["days"]}</span></figcaption>'
        f'<div class="cwrap"><svg viewBox="0 0 {CW} {CH_}" role="img" aria-label="{html.escape(it["name"][:60])}" '
        f'data-pts="{html.escape(data)}">'
        f'<defs><linearGradient id="ga" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#e30613" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="#e30613" stop-opacity="0"/></linearGradient></defs>'
        f'{grid}{ref_svg}<path d="{area}" fill="url(#ga)"/>'
        f'<polyline points="{line}" class="cl"/>{mark}{xax}'
        f'<line class="chx" y1="{CT}" y2="{CH_ - CB}" x1="0" x2="0" visibility="hidden"/>'
        f'<circle class="chd" r="4.5" visibility="hidden"/>'
        f'<rect x="{CL}" y="0" width="{CW - CL - CR}" height="{CH_}" fill="transparent" class="chit"/></svg>'
        f'<div class="ctip" hidden></div></div>'
        f'<dl class="csum"><div><dt>{ct["min"]}</dt><dd class="g">{money(pmin, cur)}</dd></div>'
        f'<div><dt>{ct["max"]}</dt><dd>{money(max(p for _, p in hist), cur)}</dd></div>'
        f'<div><dt>{ct["now"]}</dt><dd class="r">{money(it["price"], cur)}</dd></div></dl></figure>')


CHART_JS = r"""
function ocCharts(R){(R||document).querySelectorAll('.pchart').forEach(function(f){
 var svg=f.querySelector('svg'),hit=f.querySelector('.chit'),tip=f.querySelector('.ctip');
 var pts=JSON.parse(svg.dataset.pts),hx=f.querySelector('.chx'),hd=f.querySelector('.chd');
 var poly=svg.querySelector('.cl').getAttribute('points').split(' ').map(function(p){return p.split(',').map(Number)});
 function show(ev){var r=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal;
  var e=ev.touches?ev.touches[0]:ev,sx=(e.clientX-r.left)*vb.width/r.width;
  var i=0;for(var k=0;k<poly.length;k++){if(poly[k][0]<=sx+0.5)i=k}
  var p=poly[i];hx.setAttribute('x1',sx);hx.setAttribute('x2',sx);hd.setAttribute('cx',sx);hd.setAttribute('cy',p[1]);
  hx.setAttribute('visibility','visible');hd.setAttribute('visibility','visible');
  tip.hidden=false;tip.textContent=pts[i][2];
  var lx=sx*r.width/vb.width;tip.style.left=Math.min(Math.max(lx,40),r.width-40)+'px'}
 function hide(){tip.hidden=true;hx.setAttribute('visibility','hidden');hd.setAttribute('visibility','hidden')}
 hit.addEventListener('mousemove',show);hit.addEventListener('touchstart',show,{passive:true});
 hit.addEventListener('touchmove',show,{passive:true});hit.addEventListener('mouseleave',hide);
});}
ocCharts();"""


CSS = """
@font-face{font-family:Montserrat;font-weight:100 900;font-display:swap;src:url(/assets/fonts/montserrat-var.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:Montserrat;font-weight:100 900;font-display:swap;src:url(/assets/fonts/montserrat-var-ext.woff2) format("woff2");unicode-range:U+0100-024F,U+1E00-1EFF,U+2020,U+20A0-20AB,U+20AD-20CF,U+2113,U+2C60-2C7F,U+A720-A7FF}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:#070707;color:#fff;font-family:Montserrat,Arial,sans-serif;-webkit-font-smoothing:antialiased}
a{color:#fff}
button,input,select{font-family:inherit}
button{cursor:pointer}
:focus-visible{outline:3px solid #ffcc00;outline-offset:2px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.wrap{max-width:2200px;margin:0 auto;padding:16px clamp(12px,1.6vw,32px) 40px;display:flex;flex-direction:column;gap:18px}
header.top{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
.brandrow{display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.brand img{height:74px;width:auto;display:block}
.vline{width:2px;height:46px;background:#3a3a3a}
.claim{display:flex;align-items:center;gap:14px}
.claim p{margin:0;font-size:18px;font-weight:600;line-height:1.15;white-space:nowrap}
.claim b{display:block;font-size:26px;font-weight:800}
.claim svg{display:block;width:44px;height:30px;border-radius:5px;flex:none}.claim svg.sq{width:32px;height:32px}
.langs{display:flex;gap:8px;flex-wrap:wrap}
.langs a{display:flex;align-items:center;min-height:44px;padding:0 18px;border-radius:22px;font-weight:700;font-size:15px;border:2px solid #444;background:#0b0b0b;text-decoration:none}
.langs a[aria-current]{background:#e30613;border-color:#e30613}
.hero{position:relative;overflow:hidden;border-radius:20px;background:#0d0d0d;border:1px solid #222;min-height:400px;display:flex;align-items:center}
.hero picture,.hero img.bg{position:absolute;inset:0;width:100%;height:100%}
.hero img.bg{object-fit:cover;object-position:70% center}
.hero .fade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(8,8,8,.96) 0%,rgba(8,8,8,.88) 34%,rgba(8,8,8,.35) 55%,rgba(8,8,8,0) 70%)}
.hero .txt{position:relative;z-index:2;max-width:640px;padding:34px 32px 30px;display:flex;flex-direction:column;gap:14px}
.hero h1{margin:0;font-size:50px;line-height:1.02;font-weight:900;letter-spacing:-.02em}
.hero h1 span{color:#ff1a2b}
.hero p{margin:0;font-size:17px;line-height:1.45;color:#e6e6e6;max-width:34em}
.hero .bar{width:190px;height:5px;border-radius:4px;background:#e30613}
.soc{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px}
.soc a{display:flex;align-items:center;gap:10px;padding:0 18px;min-height:52px;border-radius:12px;color:#fff;text-decoration:none;font-weight:700;font-size:16px}
.soc a:hover{filter:brightness(1.12)}
.soc .g{background:#1a5cff}.soc .p{background:#1877f2}.soc .t{background:#229ed9}
.soc .sw{background:#0b0b0b;border:2px solid #22c55e;gap:12px;white-space:nowrap}.soc .sw svg{width:34px;height:24px;border-radius:4px;flex:none}.soc .sw svg.sq{width:26px;height:26px}
.soc .sw span.lg{display:flex;flex-direction:column;line-height:1.1}
.soc .sh{display:none}
.soc .sw small{font-size:13px;font-weight:600}.soc .sw b{font-size:17px;font-weight:800}
label.search{display:flex;align-items:center;gap:12px;padding:0 20px;min-height:58px;border:2px solid #4a4a4a;border-radius:30px;background:#0b0b0b}
label.search input{flex:1;min-width:0;background:transparent;border:0;outline:none;color:#fff;font:500 18px Montserrat,Arial,sans-serif}
label.search:focus-within{border-color:#e30613}
.filters{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px 14px;flex-wrap:wrap;background:#121212;border:1px solid #262626;border-radius:16px;padding:10px 14px;box-shadow:0 10px 18px -6px rgba(0,0,0,.75)}
.filters::before{content:'';position:absolute;z-index:-1;left:-1px;right:-1px;top:-1px;bottom:50%;background:#070707}
.filters .lbl{display:flex;align-items:center;gap:8px;font-weight:800;font-size:16px}
.filters .sep{width:1px;height:32px;background:#333}
.chips{display:flex;gap:8px;flex-wrap:wrap;align-items:center;flex:1 1 auto}
.chips .short{display:none}
.chips .fv{margin-left:auto}
.chips button{min-height:44px;padding:0 14px;border-radius:10px;font-weight:800;font-size:15px;border:2px solid #e30613;background:#e30613;color:#fff;display:flex;align-items:center;gap:6px}
.chips button[aria-pressed=true]{background:#fff;color:#e30613;border-color:#fff}
.chips .err{background:#ffd400;border-color:#ffd400;color:#111}
.chips .err[aria-pressed=true]{background:#fff;border-color:#fff;color:#111}
.chips .fv{background:#0b0b0b;border-color:#e30613;color:#fff}
.chips .fv[aria-pressed=true]{background:#e30613;color:#fff}
.chips .fv[aria-pressed=true] path{fill:currentColor}
.filters .right{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.shopsel{display:flex;align-items:center;gap:10px}
.shopsel select{min-height:44px;min-width:190px;padding:0 12px;border-radius:10px;border:1px solid #555;background:#0b0b0b;color:#fff;font:600 15px Montserrat,Arial,sans-serif}
.cathead{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.cathead h2{margin:0;display:flex;align-items:center;gap:10px;font-size:24px;font-weight:800}
.cathead h2 svg{color:#ff1a2b}
.cathead button{background:none;border:0;color:#ff3b47;font-weight:700;font-size:15px;min-height:44px;padding:0}
.cats{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px}
.cats button{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;min-height:84px;padding:8px 6px;border-radius:12px;border:1px solid #2c2c2c;background:#121212;color:#e6e6e6}
.cats button span{font-size:12px;font-weight:600;line-height:1.2;text-align:center}
.cats button:hover{border-color:#e30613;color:#fff}
.cats button[aria-pressed=true]{border-color:#e30613;background:#2a0306;color:#fff}
.count{margin:6px 0 0;font-size:15px;color:#bdbdbd;font-weight:600}
.layout{display:grid;grid-template-columns:250px minmax(0,1fr);gap:20px;align-items:start}
.side{position:sticky;top:78px;max-height:calc(100vh - 90px);overflow:auto;background:#121212;border:1px solid #262626;border-radius:16px;padding:6px 12px 12px}
.side summary{list-style:none;display:flex;align-items:center;gap:8px;font-weight:800;font-size:18px;min-height:46px;cursor:pointer}
.side summary::-webkit-details-marker{display:none}.side summary svg{color:#ff1a2b}
.side summary .chev{margin-left:auto;transition:transform .2s}.side details[open] summary .chev{transform:rotate(180deg)}
.catform{display:flex;flex-direction:column;gap:2px}
.ck{display:flex;align-items:center;gap:10px;min-height:44px;padding:4px 6px;border-radius:10px;cursor:pointer;color:#e6e6e6;font-size:14px;font-weight:600}
.ck:hover{background:#1c1c1c}.ck input{width:20px;height:20px;accent-color:#e30613;flex:none;margin:0}
.ck svg{flex:none;color:#bdbdbd}.ck span{flex:1;line-height:1.2}.ck em{font-style:normal;color:#8a8a8a;font-size:13px}
.ck:has(input:checked){background:#2a0306;color:#fff}.ck:has(input:checked) svg{color:#ff3b47}
.cbtn{display:flex;gap:8px;margin-top:10px}
.cbtn button{flex:1;min-height:44px;border-radius:10px;font-weight:800;font-size:14px;border:1px solid #333;background:none;color:#ddd}
.cbtn button[type=submit]{background:#e30613;border-color:#e30613;color:#fff;flex:1.6}
.results{display:flex;flex-direction:column;gap:14px;min-width:0}
.ck.ad{border-top:1px solid #2a2a2a;margin-top:6px;padding-top:8px;border-radius:0 0 10px 10px}
.agegate{position:fixed;inset:0;z-index:50;background:rgba(7,7,7,.94);display:flex;align-items:center;justify-content:center;padding:20px}
.agegate>div{max-width:440px;background:#121212;border:1px solid #333;border-radius:18px;padding:26px;text-align:center;display:flex;flex-direction:column;gap:14px}
.agegate h2{margin:0;font-size:24px}.agegate p{margin:0;color:#ddd;line-height:1.5}.agegate .big{font-size:44px}
.agegate button{min-height:52px;border:0;border-radius:12px;background:#e30613;color:#fff;font-weight:800;font-size:17px}
.agegate a{color:#bbb;font-weight:700;min-height:44px;display:flex;align-items:center;justify-content:center}
.locked{filter:blur(22px);pointer-events:none;user-select:none}
@media (max-width:860px){.layout{grid-template-columns:1fr;gap:12px}.side{top:calc(var(--fh,96px) + 6px);z-index:15;max-height:calc(100vh - var(--fh,96px) - 16px);padding:0 12px;box-shadow:0 0 0 10px #070707,0 14px 18px -6px rgba(0,0,0,.75)}.side summary{min-height:48px;font-size:16px}.side details[open]{padding-bottom:12px}}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:16px}
@media (min-width:1500px){.layout{grid-template-columns:280px minmax(0,1fr);gap:26px}.grid{grid-template-columns:repeat(auto-fill,minmax(236px,1fr));gap:18px}}
.deal{position:relative;background:#fff;color:#111;border-radius:14px;padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px}
.deal .pct{position:absolute;top:12px;left:12px;background:#e30613;color:#fff;font-weight:900;font-size:18px;padding:4px 9px;border-radius:8px;z-index:1}
.deal .err{position:absolute;top:46px;left:12px;background:#ffd400;color:#111;font-weight:800;font-size:12px;padding:3px 7px;border-radius:6px;z-index:1}
.deal .fav{position:absolute;top:6px;right:6px;width:44px;height:44px;display:flex;align-items:center;justify-content:center;background:none;border:0;color:#111;z-index:1}
.deal .fav[aria-pressed=true]{color:#e30613}
.deal .fav[aria-pressed=true] path{fill:currentColor}
.deal .ph{height:168px;display:flex;align-items:center;justify-content:center;margin-top:26px}
.deal .ph img{max-width:100%;max-height:168px;object-fit:contain}
.deal h3{margin:0;font-size:16px;font-weight:800;line-height:1.25;min-height:40px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.deal .pr{margin:0;display:flex;flex-direction:column}
.deal .pr b{font-size:27px;font-weight:900;color:#e30613;line-height:1.1}
.deal .pr s{font-size:15px;font-weight:700;color:#5f5f5f}
.deal .shop{margin:0;display:flex;align-items:center;gap:8px;font-size:15px;font-weight:700}
.deal details{font-size:13px;color:#444}
.deal summary{cursor:pointer;display:flex;align-items:center;gap:6px;font-weight:700;min-height:32px}
.deal .go{margin-top:auto;display:flex;align-items:center;justify-content:center;gap:8px;min-height:46px;border-radius:10px;background:#e30613;color:#fff;font-weight:800;font-size:17px;text-decoration:none}
.deal .go:hover{background:#c4000d}
.empty{padding:30px;text-align:center;border:1px dashed #444;border-radius:14px;display:flex;flex-direction:column;align-items:center;gap:12px}
.empty p{margin:0;font-size:17px;color:#ddd}
.empty button{min-height:44px;padding:0 18px;border-radius:10px;border:0;background:#e30613;color:#fff;font-weight:800;font-size:15px}
.trust{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));border-top:1px solid #262626;padding-top:22px;margin-top:10px}
.trust div{display:flex;gap:14px;align-items:flex-start;padding:6px 16px;border-left:1px solid #262626}
.trust svg{color:#ff1a2b;flex:none}
.trust b{display:block;margin:0 0 4px;font-weight:800;font-size:17px}
.trust span{font-size:14px;line-height:1.4;color:#cfcfcf}
footer{font-size:13px;line-height:1.5;color:#a8a8a8}
.deal h3 a.dl{color:inherit;text-decoration:none}.deal h3 a.dl:hover{text-decoration:underline}
.crumbs{font-size:14px;color:#bdbdbd;display:flex;flex-wrap:wrap;gap:6px;align-items:center}.crumbs a{color:#fff;font-weight:700}
.pagehead h1{margin:0 0 6px;font-size:32px;font-weight:900;line-height:1.1}.pagehead p{margin:0;color:#d6d6d6;line-height:1.5;max-width:60em}
.offer{max-width:1280px;width:100%;margin:0 auto;box-sizing:border-box;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:22px;background:#fff;color:#111;border-radius:18px;padding:22px}
.offer .oimg{display:flex;align-items:center;justify-content:center;min-height:280px}.offer .oimg img{max-width:100%;max-height:420px;object-fit:contain}
.offer h1{margin:0;font-size:26px;line-height:1.2;font-weight:900}
.offer .oinfo{display:flex;flex-direction:column;gap:12px}
.offer .badges{display:flex;gap:8px;flex-wrap:wrap}.offer .badges span{background:#e30613;color:#fff;font-weight:900;font-size:20px;padding:4px 10px;border-radius:8px}
.offer .badges span.e{background:#ffd400;color:#111;font-size:14px;display:flex;align-items:center}
.offer .pr b{font-size:36px;color:#e30613;font-weight:900}.offer .pr s{display:block;color:#666;font-weight:600;margin-top:2px}
.offer .meta{margin:0;color:#333;font-weight:600;display:flex;gap:8px;align-items:center}
.offer .go{display:flex;align-items:center;justify-content:center;gap:8px;background:#e30613;color:#fff;font-weight:800;font-size:18px;text-decoration:none;border-radius:12px;min-height:54px}
.offer .note{margin:0;font-size:13px;color:#555;line-height:1.45}
.offer details summary{cursor:pointer;font-weight:700}
.catnav h2{font-size:20px;margin:0 0 10px}.catnav ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}
.catnav a{display:inline-block;border:1px solid #333;border-radius:20px;padding:8px 14px;text-decoration:none;font-weight:600;font-size:14px}
.catnav a:hover{border-color:#e30613}
@media (max-width:760px){.offer{grid-template-columns:1fr;padding:16px}.offer .oimg{min-height:200px}.pagehead h1{font-size:26px}}
footer a{color:#ddd}
.hidden{display:none !important}
.totop{position:fixed;right:16px;bottom:16px;width:48px;height:48px;border-radius:50%;border:0;background:#e30613;color:#fff;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .2s}
.totop.on{opacity:1;pointer-events:auto}
.pchart{margin:10px 0 0;color:#333;font-size:12px}
.pchart figcaption{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:2px 8px;margin-bottom:4px;color:#555;font-weight:600;font-size:12px;line-height:1.3}
.pchart figcaption i.l1{display:inline-block;width:16px;border-top:2px dashed #8a8a8a;vertical-align:middle;margin-right:6px}
.pchart .cdays{color:#888;font-weight:500}
.cwrap{position:relative}.pchart svg{width:100%;height:auto;display:block;touch-action:pan-y}
.pchart .cg{stroke:#ececec;stroke-width:1}.pchart .cax{fill:#777;font-size:11px;font-family:inherit}
.pchart .cref{stroke:#8a8a8a;stroke-width:1.5;stroke-dasharray:4 4}
.pchart .cl{fill:none;stroke:#e30613;stroke-width:2.2;stroke-linejoin:round;stroke-linecap:round}
.pchart .cmin{fill:#0a8f3c;stroke:#fff;stroke-width:2}.pchart .cnow{fill:#e30613;stroke:#fff;stroke-width:2.5}
.pchart .chx{stroke:#bbb;stroke-width:1}.pchart .chd{fill:#e30613;stroke:#fff;stroke-width:2}
.pchart .ctip{position:absolute;top:-6px;transform:translate(-50%,-100%);background:#111;color:#fff;font-weight:700;
 font-size:12px;padding:4px 8px;border-radius:6px;white-space:nowrap;pointer-events:none}
.deal .ship{margin:0;font-size:12px;color:#8a5a00;background:#fff4d6;border-radius:8px;padding:5px 8px;line-height:1.35}
.csum{display:flex;flex-direction:column;gap:0;margin:8px 0 0;border-top:1px solid #eee}
.csum div{display:flex;justify-content:space-between;align-items:baseline;gap:8px;padding:5px 2px;border-bottom:1px solid #eee}.csum dt{font-size:12px;color:#666}
.csum dd{margin:0;font-weight:800;font-size:13px;color:#111;white-space:nowrap}.csum dd.g{color:#0a8f3c}.csum dd.r{color:#e30613}
@media (max-width:760px){
 .hero{min-height:0}.hero .fade{background:linear-gradient(180deg,rgba(8,8,8,.55),rgba(8,8,8,.82))}.hero h1{font-size:26px}.hero h1 br{display:none}.hero h1 span{display:block}
 .hero .txt{padding:14px 14px 12px;gap:8px}.hero p{font-size:13px;line-height:1.35}.hero .bar{display:none}
 .brand img{height:56px}.vline{display:none}.claim p{font-size:15px}.claim b{font-size:20px}
 .soc{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:2px}.soc a{flex-direction:column;justify-content:center;gap:3px;padding:6px 2px;font-size:11px;min-height:52px;border-radius:10px;text-align:center}
 .soc .lg{display:none !important}.soc .sh{display:block}.soc .sw{gap:3px;border-width:2px}.soc svg{width:20px;height:20px}.soc .sw svg{width:26px;height:18px}
 .filters{border-radius:0 0 14px 14px;margin:0 -18px;padding:8px 10px;gap:8px}.filters .lbl,.filters .sep{display:none}
 .chips{flex-wrap:nowrap;overflow-x:auto;width:100%;scrollbar-width:none}.chips::-webkit-scrollbar{display:none}
 .chips{gap:5px}.chips button{flex:1 0 auto;justify-content:center;padding:0 7px;font-size:13px;min-height:42px;gap:3px}.chips button svg{width:15px;height:15px}.chips .long{display:none}.chips .short{display:inline}.chips .fv{margin-left:0}
 .filters .right{margin-left:0;width:100%}.shopsel,.shopsel select{width:100%;min-height:40px}
 .grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
 .deal{padding:10px}.deal .ph{height:120px}.deal .ph img{max-height:120px}.deal .pr b{font-size:21px}.deal .go{font-size:15px}
}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.totop{transition:none}}
/* ===== v4: barra fissa in alto, pagina bianca, categorie nere a sinistra, caratteri leggeri ===== */
@font-face{font-family:Inter;font-weight:100 900;font-display:swap;src:url(/assets/fonts/inter-var.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:Inter;font-weight:100 900;font-display:swap;src:url(/assets/fonts/inter-var-ext.woff2) format("woff2");unicode-range:U+0100-024F,U+1E00-1EFF,U+2020,U+20A0-20AB,U+20AD-20CF,U+2113,U+2C60-2C7F,U+A720-A7FF}
body{background:#fff;color:#111;font-family:Inter,system-ui,Arial,sans-serif;letter-spacing:-.005em}
button,input,select{font-family:Inter,system-ui,Arial,sans-serif}
a{color:#111}
.hero h1,.deal .pr b,.deal .pct,.offer .pr b,.offer h1,.pagehead h1,.tdpr{font-family:Montserrat,Arial,sans-serif}
.stick{position:sticky;top:0;z-index:40;box-shadow:0 2px 10px rgba(0,0,0,.18)}
.xbar{display:flex;align-items:center;gap:22px;background:#0b0b0b;padding:8px clamp(12px,1.6vw,28px)}
.xbar .brand img{height:62px;width:auto;display:block}
.xbar .search{flex:1;display:flex;align-items:center;gap:10px;min-height:46px;border:0;border-radius:6px;background:#fff;padding:0 0 0 16px;overflow:hidden;margin:0}
.xbar .search>svg{color:#888;flex:none}
.xbar .search input{flex:1;min-width:0;background:transparent;border:0;outline:none;color:#111;font:400 16px Inter,system-ui,Arial,sans-serif}
.xbar .search:focus-within{box-shadow:0 0 0 3px #e30613}
.xbar .sbtn{display:flex;align-items:center;justify-content:center;align-self:stretch;width:64px;background:#e30613;color:#fff;border:0;padding:0;cursor:pointer}
.hicons{display:flex;gap:6px;align-items:center}
button.hic{background:none;border:0;cursor:pointer;font-family:inherit}
.sbtn.ovb{width:auto;padding:0 14px;gap:6px;background:#111;color:#fff;font:600 14px Inter,system-ui,Arial,sans-serif;border:0;cursor:pointer;display:flex;align-items:center}
label.search .sbtn.ovb{border-radius:20px;min-height:40px}
.ovq{margin:0 0 18px;padding:18px 20px;border:2px solid #e30613;border-radius:14px;background:#fff7f7}
.ovq.hidden{display:none}.ovq p{margin:0 0 12px;font-weight:700;font-size:17px;color:#111}
.ovqb{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:10px}
.ovqb a{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;border-radius:10px;background:#e30613;color:#fff;font-weight:700;text-decoration:none}
.ovq small{color:#666}
/* 17/11/2026: testata mobile più pulita e professionale */
@media(max-width:700px){
 .xbar{padding:10px 12px 12px;gap:10px 6px}
 .xbar .brand img{height:34px}
 .here{font-size:13px}.here .flagsvg{width:30px;height:21px}
 .hicons{gap:2px}.hic{min-width:36px;min-height:36px;padding:0 2px}.hic svg{width:22px;height:22px}
 .hic.sw span,.hic.rf span{display:none!important}
 .hic.sw .flagsvg,.hic.sw svg{width:24px;height:24px;border-radius:5px}
 .xbar .search{order:3;flex:1 1 100%;min-height:46px;border-radius:12px;box-shadow:0 1px 0 rgba(255,255,255,.06);padding-left:14px;flex-wrap:wrap}
 .xbar .search input{font-size:16px}
 .xbar .search .sbtn:not(.ovb){width:46px;min-height:46px;border-radius:0 12px 12px 0}
 .sbtn.ovb{order:4;flex:1 1 100%;margin:0!important;min-height:38px!important;border-radius:0 0 12px 12px!important;background:#f3f3f3!important;color:#111!important;font-size:13px!important;font-weight:600;border-top:1px solid #e6e6e6!important;margin-left:-14px!important;width:calc(100% + 14px)!important}
 .sbtn.ovb svg{width:16px;height:16px;color:#e30613}
 .chips{gap:6px;padding:2px 0}
 .chips button{min-height:32px!important;padding:0 9px!important;border-radius:999px!important;font-size:13px!important;font-weight:600;flex:0 0 auto!important;box-shadow:none!important}
}
@media(max-width:700px){.xbar .search,.xbar form.search,label.search{flex-wrap:wrap;height:auto!important}
.sbtn.ovb{order:3;flex:1 1 100%;width:100%!important;justify-content:center;border-radius:10px!important;min-height:42px;margin-top:6px}}
.hic{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;min-width:64px;min-height:50px;padding:0 6px;border-radius:8px;color:#fff !important;text-decoration:none;font-size:11px;font-weight:400}
.hic:hover{background:#1f1f1f}.hic.tg svg{color:#2aa6e0}.hic.fb svg{color:#3b82f6}.hic svg{width:22px;height:22px;flex:none}
.hic .flagsvg{width:24px;height:24px;border-radius:4px}
.here{display:flex;align-items:center;gap:8px;color:#fff;font-size:16px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;line-height:1.15;white-space:nowrap;margin-left:-4px;padding:5px 12px 5px 6px;border-radius:10px;background:#ffffff14;border:1px solid #ffffff2e}
.here .flagsvg{width:40px;height:28px;border-radius:4px;flex:none;box-shadow:0 0 0 1px #0006}.here .flagsvg.sq{width:30px;height:30px}
.topzone.tz1{grid-template-columns:1fr}.tz1 .rcol{display:flex;flex-direction:row;flex-wrap:wrap;max-width:none;width:100%}.tz1 .topdeal{flex:1 1 100%!important}.tz1 .rcol a{flex:1 1 260px}
.hic.sw span{white-space:nowrap}

.xbar .langs a{min-height:36px;padding:0 12px;font-size:13px;background:#1a1a1a;border-color:#333;color:#fff}
.xbar .langs a[aria-current]{background:#e30613;border-color:#e30613}
.stick .filters{position:static;border-radius:0;border:0;border-bottom:1px solid #e5e5e5;background:#fff;box-shadow:none;padding:8px clamp(12px,1.6vw,28px);color:#111}
.stick .filters::before{display:none}
.stick .filters .sep{background:#ddd}
.filters .lbl{font-weight:500;font-size:15px}
.chips button{font-weight:500;font-size:14px}
.chips .fv{background:#fff;color:#e30613}
.chips button[aria-pressed=true]{background:#111;color:#fff;border-color:#111}
.chips .err[aria-pressed=true]{background:#111;color:#ffd400;border-color:#111}
.chips .fv[aria-pressed=true]{background:#e30613;color:#fff;border-color:#e30613}
.shopsel select{background:#fff;color:#111;border-color:#ccc;font-weight:400}
.wfull{max-width:none;padding:0;gap:0}
.wfull .layout{grid-template-columns:310px minmax(0,1fr);gap:0}
.wfull .side{top:var(--fh,124px);max-height:calc(100vh - var(--fh,124px));min-height:calc(100vh - var(--fh,124px));border-radius:0;border:0}
.wfull .results{padding:16px clamp(12px,1.6vw,28px) 40px;gap:16px}
.wfull .lower{padding:0 clamp(12px,1.6vw,28px) 30px;display:flex;flex-direction:column;gap:18px}
.side{background:#0d0d0d;border-color:#0d0d0d;padding:10px 14px 18px;color:#fff}
.side summary{color:#fff;font-weight:600;font-size:18px}
.ck{color:#fff;font-weight:400;font-size:15px;min-height:50px;border-radius:0;border-bottom:1px solid rgba(255,255,255,.45);padding:6px}
.ck:last-of-type{border-bottom:0}
.ck svg{color:#bdbdbd}.ck input{width:22px;height:22px}
.ck em{color:#fff;background:#262626;font-weight:500;font-size:13px;border-radius:10px;padding:1px 8px}
.ck:hover{background:#1c1c1c}
.ck:has(input:checked){background:#3a0508;color:#fff}.ck:has(input:checked) svg{color:#ff3b47}
.cbtn button{color:#ddd;border-color:#444;font-weight:500}
.cbtn button[type=submit]{color:#fff;border-color:#e30613}
.count{color:#666;font-weight:400}
.deal{border:1px solid #e3e3e3;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.deal:hover{box-shadow:0 6px 18px rgba(0,0,0,.12)}
.deal h3{font-weight:500;font-size:15px;line-height:1.35;color:#1a1a1a}
.deal .pr b{font-weight:700;font-size:25px;letter-spacing:-.02em}
.deal .pr s{font-weight:400;font-size:14px;color:#777}
.deal .shop{font-weight:400;font-size:14px;color:#444}
.deal summary{font-weight:400;color:#555}
.deal .go{font-weight:500;font-size:16px;letter-spacing:.01em}
.deal .pct{font-weight:800;font-size:16px}
.deal .err{font-weight:600}
.topzone{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(300px,1fr);gap:16px;align-items:stretch}
.topzone .hero{min-height:360px;border:0}
.topzone .hero img.bg{object-position:62% 40%}
.hero h1{font-size:40px;font-weight:700}.hero .txt{padding:24px 28px}.hero p{font-weight:400}
.hero h1,.hero p{color:#fff}
.topzone .hero .soc{display:none}
.rcol{display:flex;flex-direction:column;gap:12px}
.rcol a{text-decoration:none;border-radius:16px}
.topdeal{flex:1;display:flex;flex-direction:column;gap:8px;border:2px solid #e30613;background:#fff;padding:12px 14px;color:#111 !important}
.tdh{display:flex;align-items:center;gap:6px;color:#e30613;font-weight:700;font-size:14px}
.tdb{display:flex;gap:14px;align-items:center;flex:1}
.tdb img{width:120px;height:120px;object-fit:contain;flex:none}
.tdt{display:flex;flex-direction:column;gap:6px;min-width:0}
.tdn{font-size:15px;font-weight:500;line-height:1.25;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.tdp{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.tdpct{font-style:normal;background:#e30613;color:#fff;font-weight:800;padding:2px 8px;border-radius:6px;font-size:16px}
.tdpr{color:#e30613;font-size:24px;font-weight:800}.tdold{color:#666;font-weight:400;font-size:13px}
.tgcard{display:flex;align-items:center;gap:14px;background:#ffd400;color:#111 !important;padding:14px 16px}
.tgcard .tgi{width:54px;height:54px;border-radius:50%;background:#229ed9;color:#fff;display:flex;align-items:center;justify-content:center;flex:none}
.tgcard .tgi svg{width:34px;height:34px}
.tgcard b,.fbcard b{display:block;font-size:16px;font-weight:600;line-height:1.2}
.tgcard small,.fbcard small{display:block;font-size:13px;font-weight:400;margin-top:3px}
.fbcard{display:flex;align-items:center;background:#1877f2;color:#fff !important;padding:12px 16px}
.empty{border-color:#ccc}.empty p{color:#333}
.trust{border-color:#e5e5e5}.trust div{border-color:#e5e5e5}.trust span{color:#555}.trust b{font-weight:600}
footer{color:#555}footer a{color:#333}
.catnav a{border-color:#ccc;color:#111;font-weight:400}
.crumbs{color:#666}.crumbs a{color:#111;font-weight:500}
.pagehead p{color:#444}
.offer{border:1px solid #e3e3e3;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.offer h1{font-weight:700}
.offer .meta{font-weight:400}
.langs a{background:#f2f2f2;color:#111;border-color:#ddd}
.langs a[aria-current]{color:#fff}
@media (max-width:1100px){.topzone{grid-template-columns:1fr}.rcol{flex-direction:row;flex-wrap:wrap}.rcol a{flex:1 1 260px}}
@media (max-width:860px){
 .xbar{flex-wrap:wrap;gap:8px 10px;padding:8px 10px}.xbar .brand img{height:48px}
 .xbar .search{order:3;flex:1 1 100%;min-height:42px}
 .hicons{margin-left:auto}.hic{min-width:44px;min-height:40px}.hic span{display:none}.hic.sw span,.hic.rf span{display:block;font-size:10px}.hic.sw,.hic.rf{min-width:0;padding:0 4px}
 .here{margin-left:0;font-size:13px}.here span{display:block}
 .xbar{gap:8px 6px}.xbar .brand img{height:44px}.hicons{gap:0}.hic{min-width:34px;padding:0 3px}.hic svg{width:24px;height:24px}.here{gap:6px;font-size:12px;padding:4px 8px 4px 4px}.here .flagsvg{width:30px;height:21px}.here .flagsvg.sq{width:24px;height:24px}
 .xbar .langs{order:2}
 .wfull .layout{grid-template-columns:1fr;gap:0}
 .wfull .side{position:sticky;top:var(--fh,150px);min-height:0;max-height:calc(100vh - var(--fh,150px));border-bottom:1px solid #333;box-shadow:none;z-index:15}
 .stick .filters{margin:0;border-radius:0}
 .wfull .results{padding:12px 10px 30px}
 .wfull .lower{padding:0 10px 24px}
 .topzone .hero{min-height:220px}.hero h1{font-size:24px}
 .topdeal,.fbcard{display:none}
}
"""

CATJS = r"""
(function(){
 var f=document.querySelector('.catform'); if(!f)return;
 var d=f.closest('details'); if(d&&window.innerWidth>860)d.open=true;
 var fb=document.querySelector('.stick')||document.querySelector('.filters');
 function fh(){document.documentElement.style.setProperty('--fh',(fb?fb.offsetHeight:0)+'px');}
 fh(); window.addEventListener('resize',fh);
 function shut(){if(d&&window.innerWidth<=860)d.open=false;}
 var boxes=[].slice.call(f.querySelectorAll('input[name=c]')), home=f.dataset.home, isCat=f.dataset.page==='cat';
 function sel(){return boxes.filter(function(b){return b.checked;});}
 boxes.forEach(function(b){b.addEventListener('change',function(){ if(!b.checked)return;
  boxes.forEach(function(x){ if(x!==b&&(b.dataset.solo||x.dataset.solo))x.checked=false; }); });});
 var m=location.hash.match(/cat=([a-z0-9_,-]+)/);
 if(isCat){var cur=boxes.filter(function(b){return b.checked;}).map(function(b){return b.value;});
  var sf=document.querySelector('form.search'); if(sf&&cur.length)sf.addEventListener('submit',function(e){e.preventDefault();
   var qi=sf.querySelector('input[name=q]'); location.href=home+'?q='+encodeURIComponent(qi?qi.value:'')+'#cat='+cur.join(',');});}
 if(m&&!isCat){var l=m[1].split(','); boxes.forEach(function(b){b.checked=l.indexOf(b.value)>=0;}); if(window.ocCats)window.ocCats(l);}
 f.addEventListener('submit',function(e){e.preventDefault(); var s=sel();
  if(s.length===1&&s[0].dataset.url&&!window.ocCats){location.href=s[0].dataset.url;return;}
  var l=s.map(function(b){return b.value;});
  if(isCat){location.href=home+(l.length?'#cat='+l.join(','):'');return;}
  if(window.ocCats)window.ocCats(l); shut();
  history.replaceState(null,'',l.length?'#cat='+l.join(','):location.pathname);
  var g=document.getElementById('grid'); if(g)var sk=document.querySelector('.stick'); window.scrollTo({top:g.getBoundingClientRect().top+window.scrollY-(sk?sk.offsetHeight:90)-10});});
 var c=f.querySelector('.clr'); if(c)c.addEventListener('click',function(){boxes.forEach(function(b){b.checked=false;});
  if(isCat){location.href=home;return;} if(window.ocCats)window.ocCats([]); shut(); history.replaceState(null,'',location.pathname);});
})();
"""
JS = r"""
(function(){
 var L=JSON.parse(document.getElementById('L').textContent), KEY='oc_fav_'+L.country;
 var st={tab:'',min:0,shop:'',cats:[],q:''}, favs={};
 try{favs=JSON.parse(localStorage.getItem(KEY)||'{}')||{};}catch(e){favs={};}
 function save(){try{localStorage.setItem(KEY,JSON.stringify(favs));}catch(e){}}
 var cards=[].slice.call(document.querySelectorAll('.deal')), grid=document.getElementById('grid');
 function bind(c){var b=c.querySelector('.fav'); if(!b)return; var k=c.dataset.key;
  function paint(){var on=!!favs[k]; b.setAttribute('aria-pressed',on); b.setAttribute('aria-label',on?L.fav_del:L.fav_add);}
  paint(); b.addEventListener('click',function(){ if(favs[k])delete favs[k]; else favs[k]=1; save(); paint(); if(st.tab==='favs')apply(); });}
 cards.forEach(bind);
 // sito leggero (23/11/2026): le altre offerte arrivano a blocchi; ricerca e filtri usano l'indice di tutte
 var LZ=document.getElementById('lazy'), PID=LZ?LZ.dataset.pid:'', NCH=LZ?+LZ.dataset.ch:0, REST=LZ?+LZ.dataset.n:0;
 var loaded={}, idx=null, busy=false, nloaded=0;
 function getIdx(){return idx?Promise.resolve(idx):fetch('/parti/'+PID+'.json').then(function(r){return r.json();}).then(function(j){idx=j;return j;});}
 function load(i){if(loaded[i])return Promise.resolve();loaded[i]=1;
  return fetch('/parti/'+PID+'-'+i+'.html').then(function(r){return r.text();}).then(function(h){
   var tp=document.createElement('template');tp.innerHTML=h;var nn=[].slice.call(tp.content.querySelectorAll('.deal'));
   nn.forEach(function(c){c.classList.add('hidden');grid.appendChild(c);bind(c);cards.push(c);});nloaded+=nn.length;
   if(window.ocCharts)ocCharts(grid);});}
 function filtering(){return !!(st.q.trim()||st.shop||st.cats.length||st.min||st.tab);}
 function match(e,q){var ok=(e[3]>=st.min)&&(!st.shop||e[6]===st.shop)&&(!st.cats.length||st.cats.indexOf(e[2])>=0)&&(!q||e[1].indexOf(q)>=0);
  if(st.tab==='errors')ok=ok&&e[4]===1; if(st.tab==='favs')ok=ok&&!!favs[e[0]]; return ok;}
 function ensure(){if(!NCH||!filtering())return;var q=st.q.trim().toLowerCase(),my=JSON.stringify(st);
  getIdx().then(function(j){if(JSON.stringify(st)!==my)return;var need={};j.forEach(function(e){if(!loaded[e[7]]&&match(e,q))need[e[7]]=1;});
   var l=Object.keys(need);if(!l.length)return;Promise.all(l.map(function(i){return load(+i);})).then(function(){apply(true);});}).catch(function(){});}
 function more(){if(busy||filtering())return;for(var i=0;i<NCH;i++){if(!loaded[i]){busy=true;load(i).then(function(){busy=false;apply(true);}).catch(function(){busy=false;});return;}}}
 if(LZ&&'IntersectionObserver' in window)new IntersectionObserver(function(en){if(en[0].isIntersecting)more();},{rootMargin:'1500px'}).observe(LZ);
 function apply(noLoad){
  var q=st.q.trim().toLowerCase(), n=0, list=cards.slice();
  if(st.tab==='errors'||st.min) list.sort(function(a,b){return b.dataset.pct-a.dataset.pct;});
  else list.sort(function(a,b){return b.dataset.ts-a.dataset.ts;});
  list.forEach(function(c){ grid.appendChild(c);
   var ok=(+c.dataset.pct>=st.min)&&(!st.shop||c.dataset.shop===st.shop)&&(!st.cats.length||st.cats.indexOf(c.dataset.cat)>=0)&&(!q||c.dataset.q.indexOf(q)>=0);
   if(st.tab==='errors') ok=ok&&c.dataset.err==='1';
   if(st.tab==='favs') ok=ok&&!!favs[c.dataset.key];
   c.classList.toggle('hidden',!ok); if(ok)n++; });
  if(!filtering())n+=Math.max(0,REST-nloaded);
  document.getElementById('count').textContent=n+' '+(n===1?L.one:L.many);
  if(!noLoad)ensure();
  var e=document.getElementById('empty'); e.classList.toggle('hidden',n>0);
  document.getElementById('emptytxt').textContent=(st.tab==='favs'&&!q)?L.nofav:L.none;
  if(window.ocOvq) ocOvq(st.q,n,st.ovq);
 }
 function group(sel,key,toggle){ [].forEach.call(document.querySelectorAll(sel),function(b){ b.addEventListener('click',function(){
   var v=b.dataset.v; if(key==='min')v=+v; st[key]=(toggle&&st[key]===v)?(key==='min'?0:''):v;
   if(key==='tab'&&st.tab==='favs'&&!Object.keys(favs).length){}
   [].forEach.call(document.querySelectorAll(sel),function(x){var xv=key==='min'?+x.dataset.v:x.dataset.v; x.setAttribute('aria-pressed',xv===st[key]);});
   apply(); var g=document.getElementById('grid'); var f=document.querySelector('.stick')||document.querySelector('.filters');
   if(g&&g.getBoundingClientRect().top<(f?f.offsetHeight:0)) window.scrollTo({top:g.getBoundingClientRect().top+window.scrollY-(f?f.offsetHeight:0)-12}); }); }); }
 group('[data-k=min]','min',true); group('[data-k=tab]','tab',true);
 window.ocCats=function(l){st.cats=l;apply();};
 var q=document.getElementById('q'); if(q)q.addEventListener('input',function(){st.q=q.value;st.ovq=false;apply();});
 try{var up=new URLSearchParams(location.search),qp=up.get('q'); if(q&&qp){q.value=qp; st.q=qp; st.ovq=up.get('ovunque')==='1';}}catch(e){}
 var s=document.getElementById('shop'); if(s)s.addEventListener('change',function(){st.shop=s.value;apply();});
 var r=document.getElementById('reset'); if(r)r.addEventListener('click',function(){st={tab:'',min:0,shop:'',cats:[],q:''}; if(q)q.value=''; if(s)s.value=''; [].forEach.call(document.querySelectorAll('.catform input'),function(x){x.checked=false;});
  [].forEach.call(document.querySelectorAll('[aria-pressed]'),function(x){ if(!x.classList.contains('fav')) x.setAttribute('aria-pressed','false');}); apply();});
 var top=document.getElementById('totop'); window.addEventListener('scroll',function(){top.classList.toggle('on',window.scrollY>700);},{passive:true});
 top.addEventListener('click',function(){window.scrollTo({top:0});});
 if(cards.length)apply();
})();
"""


FIRST = 200      # offerte scritte subito nella pagina (sito leggero, 23/11/2026)
CHUNK = 250      # le altre a blocchi da 250, caricati mentre scorri o quando cerchi


def _lazy_grid(lst: list, lang: str, t: dict, page_of, out_dir: str, pid: str) -> str:
    """Prime FIRST offerte nella pagina; le altre in /parti/<pid>-<n>.html + indice /parti/<pid>.json per ricerca e filtri."""
    lst = sorted(lst, key=lambda i: -_ts(i["at"]))
    head, rest = lst[:FIRST], lst[FIRST:]
    html_head = "".join(_card(i, lang, t, page_of(i)) for i in head)
    if not rest:
        return html_head, ""
    d = os.path.join(out_dir, "parti")
    os.makedirs(d, exist_ok=True)
    idx = []
    for n in range(0, len(rest), CHUNK):
        part = rest[n:n + CHUNK]
        with open(os.path.join(d, f"{pid}-{n // CHUNK}.html"), "w", encoding="utf-8") as f:
            f.write("".join(_card(i, lang, t, page_of(i)) for i in part))
        for i in part:
            amz, pct = is_amazon(i), round(i["pct"])
            idx.append([i["key"], f'{i["name"]} {i["shop"]}'.lower(), i.get("category") or cats.categorize(i["name"]),
                        -1 if amz else pct, 1 if pct >= ERR_PCT else 0, _ts(i["at"]), _shop_id(i["shop"]), n // CHUNK])
    with open(os.path.join(d, f"{pid}.json"), "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, separators=(",", ":"))
    nch = (len(rest) + CHUNK - 1) // CHUNK
    return html_head, f'<div id="lazy" data-pid="{pid}" data-ch="{nch}" data-n="{len(rest)}" style="height:1px"></div>'


def _money(v: float, cur: str) -> str:
    return money(v, cur)


def _card(it: dict, lang: str, t: dict, page: str = None) -> str:
    amz = is_amazon(it)
    cat = it.get("category") or cats.categorize(it["name"])
    href = html.escape(it["url"])
    name = html.escape(it["name"])
    pct = round(it["pct"])
    q = html.escape(f'{it["name"]} {it["shop"]}'.lower())
    err = pct >= ERR_PCT      # "Possibile errore" solo da -80% in su (scelta di Giuseppe)
    chart = "" if amz else _chart(it, lang)
    chart_box = (f'<details><summary>{_svg(I["chart"], 16, 2.2)}{t["chart"]}</summary>{chart}</details>') if chart else ""
    return (
        f'<article class="deal" data-key="{html.escape(it["key"])}" data-cat="{cat}" data-pct="{-1 if amz else pct}" '
        f'data-err="{1 if err else 0}" data-ts="{_ts(it["at"])}" data-shop="{_shop_id(it["shop"])}" data-q="{q}">'
        + ("" if amz else f'<span class="pct">-{pct}%</span>')
        + (f'<span class="err">⚡ {t["maybe"]}</span>' if err and not amz else "")
        + f'<button type="button" class="fav" aria-pressed="false" aria-label="{t["fav_add"]}">{_svg(I["favs"], 24, 2)}</button>'
        + (f'<a class="ph" href="{href}" rel="sponsored nofollow noopener" target="_blank" tabindex="-1">'
           f'<img src="{html.escape(it["image"])}" alt="" loading="lazy"></a>' if it.get("image") else '<div class="ph"></div>')
        + (f'<h3><a class="dl" href="{page}">{name}</a></h3>' if page else f'<h3>{name}</h3>')
        + f'<p class="pr"><b>{_money(it["price"], it["currency"])}</b>'
        + ("" if amz else f'<s>{t["instead"]} {_money(it["ref"], it["currency"])}</s>') + '</p>'
        + f'<p class="shop">{_svg(I["shop"], 18, 2)}{html.escape(it["shop"])}</p>'
        + (f'<p class="ship">📦 {SHIP_CH.get(lang, SHIP_CH["it"])}</p>' if it.get("ship_note") else "")
        + chart_box
        + f'<a class="go" href="{href}" rel="sponsored nofollow noopener" target="_blank">{t["go"]} {_svg(I["arrow"], 18, 2.6)}</a>'
        + '</article>'
    )



# ---------------------------------------------------------------- SEO: pagine categoria e offerta
SEO = {
 "it": {"adult_dir": "adulti", "age_h": "Sezione per adulti", "age_p": "Questa pagina contiene prodotti per adulti. Per continuare conferma di avere almeno 18 anni.", "age_y": "Ho almeno 18 anni", "age_n": "Torna alle offerte", "adult_h1": "Offerte per adulti",
        "cat_dir": "categoria", "off_dir": "offerta", "home": "Home", "date": "{d}/{m}/{y}",
        "cat_title": "Offerte {cat} {inx} – sconti ed errori di prezzo | Offerte Crollate",
        "cat_h1": "Offerte {cat} {inx}",
        "cat_desc": "{n} offerte attive nella categoria {cat} {inx}, da {shops}. Sconti reali ed errori di prezzo raccolti da Offerte Crollate.",
        "off_title": "{name} a {price} (-{pct}%) – {shop} | Offerte Crollate",
        "off_desc": "{name} a {price} invece di {ref} da {shop}: sconto del {pct}%. Offerta rilevata il {date}.",
        "detected": "Offerta rilevata il", "more": "Altre offerte in", "all": "Tutte le offerte {inx}",
        "note": "Il prezzo può cambiare in qualsiasi momento: verifica sempre il prezzo finale sul sito del negozio."},
 "de": {"adult_dir": "erwachsene", "age_h": "Bereich für Erwachsene", "age_p": "Diese Seite enthält Produkte für Erwachsene. Bestätige, dass du mindestens 18 Jahre alt bist.", "age_y": "Ich bin mindestens 18", "age_n": "Zurück zu den Angeboten", "adult_h1": "Angebote für Erwachsene",
        "cat_dir": "kategorie", "off_dir": "angebot", "home": "Home", "date": "{d}.{m}.{y}",
        "cat_title": "Angebote {cat} {inx} – Rabatte und Preisfehler | Offerte Crollate",
        "cat_h1": "Angebote {cat} {inx}",
        "cat_desc": "{n} aktive Angebote in der Kategorie {cat} {inx}, von {shops}. Echte Rabatte und Preisfehler, gesammelt von Offerte Crollate.",
        "off_title": "{name} für {price} (-{pct}%) – {shop} | Offerte Crollate",
        "off_desc": "{name} für {price} statt {ref} bei {shop}: {pct}% Rabatt. Angebot erfasst am {date}.",
        "detected": "Angebot erfasst am", "more": "Weitere Angebote in", "all": "Alle Angebote {inx}",
        "note": "Der Preis kann sich jederzeit ändern: Prüfe den Endpreis immer im Shop."},
 "fr": {"adult_dir": "adultes", "age_h": "Espace adultes", "age_p": "Cette page contient des produits pour adultes. Confirme que tu as au moins 18 ans pour continuer.", "age_y": "J'ai au moins 18 ans", "age_n": "Retour aux offres", "adult_h1": "Offres pour adultes",
        "cat_dir": "categorie", "off_dir": "offre", "home": "Accueil", "date": "{d}/{m}/{y}",
        "cat_title": "Offres {cat} {inx} – réductions et erreurs de prix | Offerte Crollate",
        "cat_h1": "Offres {cat} {inx}",
        "cat_desc": "{n} offres actives dans la catégorie {cat} {inx}, chez {shops}. Vraies réductions et erreurs de prix réunies par Offerte Crollate.",
        "off_title": "{name} à {price} (-{pct}%) – {shop} | Offerte Crollate",
        "off_desc": "{name} à {price} au lieu de {ref} chez {shop} : {pct} % de réduction. Offre relevée le {date}.",
        "detected": "Offre relevée le", "more": "Autres offres dans", "all": "Toutes les offres {inx}",
        "note": "Le prix peut changer à tout moment : vérifie toujours le prix final sur le site de la boutique."},
}
ERR_PCT = 80         # da questo sconto in su il sito segna "Possibile errore" ed è nel filtro Errori di prezzo
MIN_CAT = 3          # una categoria ha la sua pagina solo con almeno 3 offerte (niente pagine quasi vuote)
ADULT = cats.ADULT[0]
HREFLANG = {"it": {"it": "it-IT"}, "ch": {"it": "it-CH", "de": "de-CH", "fr": "fr-CH"}}


def _slug(text: str, n: int = 70) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return (t[:n].rstrip("-")) or "offerta"


def _offer_slug(it: dict) -> str:
    """Indirizzo stabile: nome del prodotto + 6 caratteri presi dalla chiave (resta uguale finché l'offerta è attiva)."""
    return f'{_slug(it["name"], 60)}-{hashlib.sha1(it["key"].encode()).hexdigest()[:6]}'


def _pfx(lang: str, langs: list) -> str:
    return "" if lang == langs[0] else f"/{lang}"


def _home_path(lang: str, langs: list) -> str:
    return "/" if lang == langs[0] else f"/{lang}.html"


def _cat_path(c: str, lang: str, langs: list) -> str:
    return f'{_pfx(lang, langs)}/{SEO[lang]["cat_dir"]}/{_slug(cats.label(c, lang))}/'


def _adult_path(lang: str, langs: list) -> str:
    return f'{_pfx(lang, langs)}/{SEO[lang]["adult_dir"]}/'


def _off_path(it: dict, lang: str, langs: list) -> str:
    return f'{_pfx(lang, langs)}/{SEO[lang]["off_dir"]}/{_offer_slug(it)}/'


def _date(iso: str, lang: str) -> str:
    y, m, d = (iso or "")[:10].split("-") if iso and len(iso) >= 10 else ("", "", "")
    return SEO[lang]["date"].format(d=d, m=m, y=y) if y else ""


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n - 1].rsplit(" ", 1)[0] + "…"


def _alternates(country: str, langs: list, path_of) -> str:
    """hreflang reciproci tra le lingue dello stesso sito (+ x-default sulla lingua principale)."""
    base = base_url(country)
    out = "".join(f'<link rel="alternate" hreflang="{HREFLANG[country][l]}" href="{base}{path_of(l)}">' for l in langs)
    return out + f'<link rel="alternate" hreflang="x-default" href="{base}{path_of(langs[0])}">'


def _jsonld(data) -> str:
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def _crumbs(country: str, lang: str, trail: list) -> tuple:
    """Briciole di pane visibili + gli stessi passaggi come BreadcrumbList (solo nomi e indirizzi)."""
    base = base_url(country)
    vis = ' <span aria-hidden="true">›</span> '.join(
        (f'<a href="{u}">{html.escape(n)}</a>' if u else f'<span aria-current="page">{html.escape(n)}</span>') for n, u in trail)
    ld = {"@context": "https://schema.org", "@type": "BreadcrumbList",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, **({"item": base + u} if u else {})}
                              for i, (n, u) in enumerate(trail)]}
    return f'<nav class="crumbs" aria-label="Breadcrumb">{vis}</nav>', _jsonld(ld)


def _catnav(lang: str, langs: list, cat_list: list, t: dict) -> str:
    if not cat_list:
        return ""
    li = "".join(f'<li><a href="{_cat_path(c, lang, langs)}">{cats.label(c, lang)}</a></li>' for c in cat_list)
    return f'<nav class="catnav" aria-label="{t["cats"]}"><h2>{t["cats"]}</h2><ul>{li}</ul></nav>'


def _catside(lang: str, langs: list, counts: dict, page_cats: list, t: dict, checked=(), page: str = "home") -> str:
    """Categorie in verticale a sinistra, con spunta: una sola scelta apre la sua pagina, più scelte filtrano la home."""
    rows = "".join(
        f'<label class="ck"><input type="checkbox" name="c" value="{c}"'
        f'{(" data-url=" + chr(34) + _cat_path(c, lang, langs) + chr(34)) if c in page_cats else ""}'
        f'{" checked" if c in checked else ""}>{_svg(CAT_ICON[c], 22, 1.7)}<span>{cats.label(c, lang)}</span><em>{counts[c]}</em></label>'
        for c in cats.ORDER if counts.get(c))
    if counts.get(ADULT):   # adulti: sempre da sola, apre la pagina con la conferma dei 18 anni
        rows += (f'<label class="ck ad"><input type="checkbox" name="c" value="{ADULT}" data-solo="1" '
                 f'data-url="{_adult_path(lang, langs)}"{" checked" if ADULT in checked else ""}>'
                 f'{_svg(CAT_ICON[ADULT], 22, 1.7)}<span>{cats.label(ADULT, lang)}</span><em>{counts[ADULT]}</em></label>')
    if not rows:
        return ""
    return (f'<aside class="side" aria-label="{t["cats"]}"><details><summary>{_svg(I["grid"], 22, 2.2)}{t["cats"]}'
            f'<svg class="chev" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></summary>'
            f'<form class="catform" data-home="{_home_path(lang, langs)}" data-page="{page}">{rows}'
            f'<div class="cbtn"><button type="submit">{t["cshow"]}</button><button type="button" class="clr">{t["cclr"]}</button></div>'
            f'</form></details></aside>')


def _write(out_dir: str, path: str, page: str) -> None:
    full = os.path.join(out_dir, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(out_dir, path.strip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(page)


def _sitemap(out_dir: str, base: str, urls: list) -> None:
    """Solo pagine valide, canoniche e indicizzabili: home, categorie, offerte attive, privacy."""
    rows = "".join(f'  <url><loc>{html.escape(base + u)}</loc><lastmod>{lm}</lastmod></url>\n' for u, lm in urls)
    with open(os.path.join(out_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n')



TOPJS = r"""
(function(){var best=null;[].forEach.call(document.querySelectorAll('.deal'),function(c){if(!best||+c.dataset.pct>+best.dataset.pct)best=c;});
 var t=document.getElementById('topdeal'); if(!t)return; if(!best){t.style.display='none';return;}
 var a=best.querySelector('h3 a')||best.querySelector('a.go'), im=best.querySelector('.ph img'), pr=best.querySelector('.pr b'), o=best.querySelector('.pr s');
 t.href=a?a.href:'#'; if(a&&a.target)t.target=a.target;
 if(im)t.querySelector('img').src=im.src;
 t.querySelector('.tdn').textContent=(best.querySelector('h3')||{}).textContent||'';
 t.querySelector('.tdpct').textContent='-'+best.dataset.pct+'%';
 t.querySelector('.tdpr').textContent=pr?pr.textContent:''; t.querySelector('.tdold').textContent=o?o.textContent:'';})();
"""


# tasto "Aggiorna" (nella web app sul telefono la pagina non si ricarica da sola) + ricarica automatica
# quando si torna nell'app dopo più di 10 minuti (richiesta di Giuseppe del 16/11/2026)
RF_LBL = {"it": "Aggiorna", "de": "Neu laden", "fr": "Actualiser"}
RF_PATH = '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>'
RFJS = ("var ocT=Date.now();function ocRefresh(){var u=new URL(location.href);u.searchParams.set('r',Date.now());"
        "location.replace(u.toString());}document.addEventListener('visibilitychange',function(){"
        "if(document.visibilityState==='visible'&&Date.now()-ocT>600000)ocRefresh();});")

# "Cerca ovunque": cerca la parola nei negozi affiliati (link affiliato) anche se l'offerta non è sul sito
# (richiesta di Giuseppe del 16/11/2026)
OVQ_LBL = {"it": ("Cerca su Amazon e negozi", 'Cerca «%s» nei negozi partner', "Si apre il sito del negozio · link affiliati #ADV"),
           "de": ("Bei Amazon & Shops suchen", "«%s» bei unseren Partnershops suchen", "Öffnet den Shop · Affiliate-Links #ADV"),
           "fr": ("Chercher sur Amazon & boutiques", "Chercher «%s» chez nos partenaires", "Ouvre le site du magasin · liens affiliés #ADV")}
_AW = "https://www.awin1.com/cread.php?awinmid=%d&awinaffid=3152592&clickref=cerca&ued="
OVQ_SHOPS = {
    "it": [["Amazon.it", "https://www.amazon.it/s?tag=offertecrolla-21&k=", ""],
           ["Onestreet", _AW % 128805, "https://onestreet.it/search?q="],
           ["Celebre Store", _AW % 118201, "https://celebrestore.com/search?q="],
           ["Acer Store", _AW % 15530, "https://store.acer.com/it-it/catalogsearch/result/?q="],
           ["Moulinex", _AW % 9450, "https://www.moulinex.it/search?text="],
           ["Mondadori Store", _AW % 9423, "https://www.mondadoristore.it/search/?tpr=10&g="]],
    "ch": [["Amazon.de", "https://www.amazon.de/s?tag=offertecrol06-21&k=", ""],
           ["Amazon.it", "https://www.amazon.it/s?tag=offertecrolla-21&k=", ""],
           ["MediaMarkt", "https://www.awin1.com/cread.php?awinmid=14040&awinaffid=3152592&clickref=cerca&ued=",
            "https://www.mediamarkt.ch/de/search.html?query="]],
}
OVQJS = ("function ocOvqUrl(s,q){return s[2]?s[1]+encodeURIComponent(s[2]+encodeURIComponent(q)):s[1]+encodeURIComponent(q);}"
         "function ocOvq(q,n,force){var p=document.getElementById('ovq');if(!p)return;q=(q||'').trim();"
         "if(!q||!(force||n===0)){p.classList.add('hidden');return;}"
         "document.getElementById('ovqt').textContent=OCL[1].replace('%s',q);"
         "document.getElementById('ovqb').innerHTML=OCS.map(function(s){return '<a href=\"'+ocOvqUrl(s,q)+'\" target=\"_blank\" rel=\"sponsored noopener\">'+s[0]+' ›</a>';}).join('');"
         "p.classList.remove('hidden');}"
         "function ocOvunque(){var i=document.getElementById('q');var q=(i&&i.value||'').trim();if(!q){if(i)i.focus();return;}"
         "if(!document.getElementById('ovq')){location.href=OCH+'?q='+encodeURIComponent(q)+'&ovunque=1';return;}"
         "ocOvq(q,0,true);document.getElementById('ovq').scrollIntoView({behavior:'smooth',block:'center'});}")

SW_LBL = {"it": {"it": "Passa a Italia", "ch": "Passa a Svizzera"},
          "de": {"it": "Zu Italien", "ch": "Zur Schweiz"},
          "fr": {"it": "Vers l'Italie", "ch": "Vers la Suisse"}}
HERE_LBL = {"it": {"it": "Italia", "ch": "Svizzera"},
            "de": {"it": "Italien", "ch": "Schweiz"},
            "fr": {"it": "Italie", "ch": "Suisse"}}


def _xbar(t: dict, country: str, home_href: str, root: str, search: str, langsw: str = "", lang: str = "it") -> str:
    """Barra nera fissa in alto: logo + paese della pagina, ricerca larga, icone Telegram / Facebook / altro paese."""
    other = "ch" if country == "it" else "it"
    here = FLAG_SVG[country]
    return (f'<div class="xbar"><a class="brand" href="{home_href}" aria-label="Offerte Crollate">'
            f'<picture><source srcset="{root}assets/logo_site.webp" type="image/webp"><img src="{root}assets/logo_site.png" alt="Offerte Crollate" width="107" height="52"></picture></a>'
            f'<span class="here">{here}<span>{HERE_LBL[lang][country]}</span></span>'
            + search
            + (f'<nav class="langs" aria-label="Lingua / Sprache / Langue">{langsw}</nav>' if langsw else "")
            + f'<nav class="hicons" aria-label="Social">'
            f'<a class="hic tg" href="{TG_URL}" target="_blank" rel="noopener" aria-label="Telegram">{TG}<span>Telegram</span></a>'
            f'<a class="hic fb" href="{FB_URL}" target="_blank" rel="noopener" aria-label="Facebook">{FB}<span>Facebook</span></a>'
            f'<a class="hic sw" href="{base_url(other)}/">{FLAG_SVG[other]}<span>{SW_LBL[lang][other]}</span></a>'
            f'<button type="button" class="hic rf" onclick="ocRefresh()" aria-label="{RF_LBL.get(lang, RF_LBL["it"])}">'
            f'{_svg(RF_PATH, 22, 2.2)}<span>{RF_LBL.get(lang, RF_LBL["it"])}</span></button>'
            f'</nav></div><script>{RFJS}var OCS={json.dumps(OVQ_SHOPS.get(country, []))};'
            f'var OCL={json.dumps(OVQ_LBL.get(lang, OVQ_LBL["it"]), ensure_ascii=False)};var OCH={json.dumps(home_href)};{OVQJS}</script>')


def _rcol(t: dict) -> str:
    return (f'<div class="rcol">'
            f'<a class="topdeal" id="topdeal" href="#"><span class="tdh">{_svg(I["errors"], 18, 2.4)}{t["topdeal"]}</span>'
            f'<span class="tdb"><img alt="" width="120" height="120"><span class="tdt"><b class="tdn"></b>'
            f'<span class="tdp"><em class="tdpct"></em><strong class="tdpr"></strong><s class="tdold"></s></span></span></span></a>'
            f'<a class="tgcard" href="{TG_URL}" target="_blank" rel="noopener"><span class="tgi">{TG}</span><span><b>{t["tg_b"]}</b><small>{t["tg_s"]}</small></span></a>'
            f'<a class="fbcard" href="{GROUP_URL}" target="_blank" rel="noopener"><span><b>{t["group"]}</b><small>{t["fb_s"]}</small></span></a>'
            f'</div>')


def _shell(country: str, lang: str, langs: list, t: dict, ui: dict, title: str, desc: str, path_of, main: str,
           extra_head: str = "", og_img: str = None, cat_list=(), js: bool = True,
           robots: str = "index,follow,max-image-preview:large") -> str:
    """Pagina interna (categoria / offerta) con la stessa grafica della home: indirizzi assoluti, canonical,
    hreflang tra le lingue del sito, testo già nell'HTML (visibile anche ai motori di ricerca)."""
    base = base_url(country)
    flag_big = FLAG_SVG[country].replace('class="flagsvg', 'class="flag flagsvg')
    langsw = ("".join(f'<a href="{path_of(l)}" lang="{l}" hreflang="{HREFLANG[country][l]}"'
                      f'{" aria-current=page" if l == lang else ""}>{LANG_NAME[l]}</a>' for l in langs)) if len(langs) > 1 else ""
    labels = json.dumps({k: t[k] for k in ("one", "many", "none", "nofav", "fav_add", "fav_del")} | {"country": country},
                        ensure_ascii=False)
    home_href = _home_path(lang, langs)
    search = (f'<form class="search" action="{home_href}" method="get" role="search"><span class="sr">{t["search"]}</span>{_svg(I["search"], 22, 2.2)}'
              f'<input id="q" name="q" type="search" placeholder="{t["search"]}" autocomplete="off">'
              f'<button class="sbtn" type="submit" aria-label="{t["search_go"]}">{_svg(I["search"], 22, 2.4)}</button>'
              f'<button type="button" class="sbtn ovb" onclick="ocOvunque()" aria-label="{OVQ_LBL.get(lang, OVQ_LBL["it"])[0]}">{_svg(I["globe"], 20, 2.2)}<span>{OVQ_LBL.get(lang, OVQ_LBL["it"])[0]}</span></button>'f'</form>')
    body = (
        f'<div class="stick">{_xbar(t, country, home_href, "/", search, langsw, lang)}</div>'
        f'<div class="wrap">' + main + _catnav(lang, langs, list(cat_list), t)
        + f'<footer>{ui["aff_short"]} {ui["amz"]} <a href="/privacy.html">{t["privacy"]}</a></footer>'
        f'</div>'
        f'<button class="totop" id="totop" type="button" aria-label="{t["top"]}">{_svg("<path d=\"M12 19V5M5 12l7-7 7 7\"/>", 22, 2.6)}</button>'
        f'<script type="application/json" id="L">{labels}</script>'
    )
    loc = HREFLANG[country][lang].replace("-", "_")
    return (f'<!DOCTYPE html><html lang="{HREFLANG[country][lang]}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#070707">'
            f'<title>{html.escape(title)}</title>{_og(lang, title, path_of(lang).lstrip("/"), base, desc=desc, img=og_img, locale=loc, robots=robots)}'
            f'<link rel="preload" href="/assets/fonts/montserrat-var.woff2" as="font" type="font/woff2" crossorigin>'
            + _alternates(country, langs, path_of) + extra_head
            + f'<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><style>{CSS}</style></head>'
            f'<body>{body}<script>{JS if js else ""}{CATJS}{CHART_JS}</script></body></html>')


def render_country(items: list, country: str, ccfg: dict, out_dir: str) -> None:
    shutil.rmtree(os.path.join(out_dir, "parti"), ignore_errors=True)   # blocchi del sito leggero: rifatti ogni giro
    langs = ccfg["langs"]
    other = "ch" if country == "it" else "it"
    base = base_url(country)
    fname = lambda l: "index.html" if l == langs[0] else f"{l}.html"
    for it in items:
        it.setdefault("category", cats.categorize(it["name"]))
    counts = {}
    for it in items:
        counts[it["category"]] = counts.get(it["category"], 0) + 1
    if country == "ch":   # Amazon.it sul sito svizzero: la spedizione in Svizzera va controllata nel carrello
        for it in items:
            if str(it.get("source", "")).startswith("amazon"):
                it["ship_note"] = True
    adult_items = [it for it in items if it["category"] == ADULT]       # solo nella pagina "Adulti 18+"
    items = [it for it in items if it["category"] != ADULT]
    shops = sorted({(_shop_id(it["shop"]), it["shop"]) for it in items}, key=lambda x: x[1].lower())
    banner = f"banner_{country}"
    page_cats = [c for c in cats.ORDER if counts.get(c, 0) >= MIN_CAT]
    with_page = lambda it: not is_amazon(it)
    for lang in langs:
        t, ui = T[lang], UI[lang]
        flag_big = FLAG_SVG[country].replace('class="flagsvg', 'class="flag flagsvg')
        langsw = ("".join(f'<a href="{fname(l)}" lang="{l}"{" aria-current=page" if l == lang else ""}>{LANG_NAME[l]}</a>'
                          for l in langs)) if len(langs) > 1 else ""
        chips = ("".join(f'<button type="button" data-k="min" data-v="{v}" aria-pressed="false">≥{v}%</button>' for v in (30, 50, 70))
                 + f'<button type="button" class="err" data-k="tab" data-v="errors" aria-pressed="false">{_svg(I["errors"], 18, 2.2)}<span class="long">{t["errors"]}</span><span class="short">{t["errors_s"]}</span></button>')
        chips += f'<button type="button" class="fv" data-k="tab" data-v="favs" aria-pressed="false">{_svg(I["favs"], 18, 2.2)}{t["favs"]}</button>'
        shop_opts = "".join(f'<option value="{sid}">{html.escape(nm)}</option>' for sid, nm in shops)
        cards, lazy = _lazy_grid(items, lang, t, lambda it: _off_path(it, lang, langs) if with_page(it) else None,
                                 out_dir, f"{lang}-home")
        trust_icons = [I["shield"], I["errors"], I["group"], I["truck"] if country == "it" else I["chshield"]]
        trust = "".join(f'<div>{_svg(ic, 40, 1.6)}<p style="margin:0"><b>{tt}</b><span>{dd}</span></p></div>'
                        for ic, tt, dd in zip(trust_icons, [t["t1"], t["t2"], t["t3"], t["t4_" + country]],
                                              [t["d1"], t["d2"], t["d3"], t["d4_" + country]]))
        labels = json.dumps({k: t[k] for k in ("one", "many", "none", "nofav", "fav_add", "fav_del")} | {"country": country},
                            ensure_ascii=False)
        title = f'Offerte Crollate – {t["best"]} {t["in_" + country]}'
        search = (f'<label class="search"><span class="sr">{t["search"]}</span>{_svg(I["search"], 22, 2.2)}'
                  f'<input id="q" type="search" placeholder="{t["search"]}" autocomplete="off">'
                  f'<span class="sbtn" aria-hidden="true">{_svg(I["search"], 22, 2.4)}</span>'
                  f'<button type="button" class="sbtn ovb" onclick="ocOvunque()" aria-label="{OVQ_LBL.get(lang, OVQ_LBL["it"])[0]}">{_svg(I["globe"], 20, 2.2)}<span>{OVQ_LBL.get(lang, OVQ_LBL["it"])[0]}</span></button>'f'</label>')
        filters = (
            f'<div class="filters" role="region" aria-label="{t["filter"]}"><span class="lbl">{_svg(I["filter"], 20, 2)}{t["filter"]}</span><span class="sep"></span>'
            f'<div class="chips" role="group" aria-label="{t["min"]}">{chips}</div>'
            f'<div class="right"><label class="shopsel">{_svg(I["shop"], 22, 1.8)}<span class="sr">{t["allshops"]}</span>'
            f'<select id="shop"><option value="">{t["allshops"]}</option>{shop_opts}</select></label></div></div>'
        ) if items else ""
        hero = (
            f'<section class="hero"><picture><source srcset="assets/{banner}.webp" type="image/webp">'
            f'<img class="bg" src="assets/{banner}.jpg" alt=""></picture><div class="fade"></div>'
            f'<div class="txt"><h1>{t["h1a"]}<br><span>{t["h1b"]}</span></h1><p>{t["sub_" + country]}</p><div class="bar"></div>'
            f'<div class="soc"><a class="g" href="{GROUP_URL}" target="_blank" rel="noopener">{_svg(I["group"], 22, 2)}<span class="lg">{t["group"]}</span><span class="sh">Community</span></a>'
            f'<a class="p" href="{FB_URL}" target="_blank" rel="noopener">{FB}<span class="lg">{t["page"]}</span><span class="sh">Facebook</span></a>'
            f'<a class="t" href="{TG_URL}" target="_blank" rel="noopener">{TG}<span>Telegram</span></a>'
            f'<a class="sw" href="{base_url(other)}/">{FLAG_SVG[other]}<span class="lg"><small>{t["goto"]}</small><b>{t["other_" + other]}</b></span><span class="sh">{t["other_" + other]}</span></a></div>'
            f'</div></section>')
        # 25/11/2026 (Giuseppe): tolto il riquadro grande con la foto, pagina più pulita
        topzone = f'<div class="topzone tz1">{_rcol(t)}</div>'
        offers = (
            f'<div class="layout">{_catside(lang, langs, counts, page_cats, t)}<div class="results">{topzone}'
            f'<div class="ovq hidden" id="ovq"><p id="ovqt"></p><div class="ovqb" id="ovqb"></div><small>{OVQ_LBL.get(lang, OVQ_LBL["it"])[2]}</small></div>'
            f'<p class="count" id="count" aria-live="polite"></p><div class="grid" id="grid">{cards}</div>{lazy}'
            f'<div class="empty hidden" id="empty"><p id="emptytxt"></p><button type="button" id="reset">{t["reset"]}</button></div></div></div>'
        ) if items else f'<div class="results">{topzone}<div class="empty"><p>{t["soon"]}</p></div></div>'
        body = (
            f'<div class="stick">{_xbar(t, country, fname(lang), "", search, langsw, lang)}{filters}</div>'
            f'<div class="wrap wfull">' + offers
            + f'<div class="lower">' + _catnav(lang, langs, page_cats, t)
            + f'<div class="trust">{trust}</div>'
            f'<footer>{ui["aff_short"]} {ui["amz"]} <a href="privacy.html">{t["privacy"]}</a></footer></div>'
            f'</div>'
            f'<button class="totop" id="totop" type="button" aria-label="{t["top"]}">{_svg("<path d=\"M12 19V5M5 12l7-7 7 7\"/>", 22, 2.6)}</button>'
            f'<script type="application/json" id="L">{labels}</script>'
        )
        site_ld = _jsonld({"@context": "https://schema.org", "@type": "WebSite", "name": "Offerte Crollate",
                           "url": base + "/", "inLanguage": HREFLANG[country][lang],
                           "publisher": {"@type": "Organization", "name": "Offerte Crollate", "url": base + "/",
                                         "logo": base + "/assets/logo_round.png", "sameAs": [FB_URL, TG_URL]}})
        page = (f'<!DOCTYPE html><html lang="{HREFLANG[country][lang]}"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#070707">'
                f'<title>{html.escape(title)}</title>'
                f'{_og(lang, title, "" if lang == langs[0] else f"{lang}.html", base, desc=t["sub_" + country], locale=HREFLANG[country][lang].replace("-", "_"))}'
                f'<link rel="preload" href="/assets/fonts/montserrat-var.woff2" as="font" type="font/woff2" crossorigin>'
                + _alternates(country, langs, lambda l: _home_path(l, langs)) + site_ld
                + f'<link rel="icon" href="/favicon.ico" sizes="any"><link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><style>{CSS}</style></head>'
                f'<body>{body}<script>{JS}{CATJS}{CHART_JS}{TOPJS}</script></body></html>')
        with open(os.path.join(out_dir, fname(lang)), "w", encoding="utf-8") as f:
            f.write(page)
    # 18/11/2026: pagina per le dirette TikTok (giro automatico delle offerte + voce + ricerca), non indicizzata
    for _lv in ("live.html", "live-voce.html", "link.html"):
        shutil.copy(os.path.join(os.path.dirname(__file__), _lv), os.path.join(out_dir, _lv))

    # ---------- pagine interne indicizzabili: categorie e offerte attive (rifatte da zero a ogni giro,
    # così le offerte scadute spariscono e il loro indirizzo risponde 404)
    for lang in langs:
        root = os.path.join(out_dir, _pfx(lang, langs).strip("/")) if _pfx(lang, langs) else out_dir
        for d in (SEO[lang]["cat_dir"], SEO[lang]["off_dir"]):
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    day = lambda iso: (iso or today)[:10]
    urls = [(_home_path(l, langs), today) for l in langs]
    by_cat = {}
    for it in items:
        by_cat.setdefault(it["category"], []).append(it)
    for c in page_cats:
        lst = by_cat[c]
        urls += [(_cat_path(c, l, langs), max(day(i["at"]) for i in lst)) for l in langs]
    offers = [it for it in items if with_page(it)]
    urls += [(_off_path(it, l, langs), day(it["at"])) for it in offers for l in langs]
    for lang in langs:
        t, ui, sx = T[lang], UI[lang], SEO[lang]
        inx = t["in_" + country]
        home = (sx["home"], _home_path(lang, langs))
        # categorie
        for c in page_cats:
            lst = by_cat[c]
            cl = cats.label(c, lang)
            shops_l = []
            for i in lst:
                if i["shop"] not in shops_l:
                    shops_l.append(i["shop"])
            shops_txt = ", ".join(shops_l[:3]) + (" …" if len(shops_l) > 3 else "")
            title = sx["cat_title"].format(cat=cl, inx=inx)
            desc = sx["cat_desc"].format(n=len(lst), cat=cl, inx=inx, shops=shops_txt)
            cr, ld = _crumbs(country, lang, [home, (cl, None)])
            cg, cz = _lazy_grid(lst, lang, t, lambda i: _off_path(i, lang, langs) if with_page(i) else None,
                                out_dir, f"{lang}-cat-{c}")
            main = (cr + f'<div class="pagehead"><h1>{html.escape(sx["cat_h1"].format(cat=cl, inx=inx))}</h1>'
                    f'<p>{html.escape(desc)}</p></div>'
                    f'<div class="layout">{_catside(lang, langs, counts, page_cats, t, checked={c}, page="cat")}<div class="results">'
                    f'<p class="count" id="count" aria-live="polite"></p>'
                    f'<div class="grid" id="grid">{cg}</div>{cz}'
                    f'<div class="empty hidden" id="empty"><p id="emptytxt"></p></div></div></div>')
            _write(out_dir, _cat_path(c, lang, langs),
                   _shell(country, lang, langs, t, ui, title, desc, lambda l, c=c: _cat_path(c, l, langs), main, ld,
                          cat_list=page_cats))
        # offerte
        for it in offers:
            c = it["category"]
            cl = cats.label(c, lang)
            pct = round(it["pct"])
            price, ref = _money(it["price"], it["currency"]), _money(it["ref"], it["currency"])
            name = it["name"]
            date = _date(it.get("at"), lang)
            title = sx["off_title"].format(name=_cut(name, 60), price=price, pct=pct, shop=it["shop"])
            desc = sx["off_desc"].format(name=_cut(name, 90), price=price, ref=ref, shop=it["shop"], pct=pct, date=date)
            trail = [home] + ([(cl, _cat_path(c, lang, langs))] if c in page_cats else []) + [(_cut(name, 50), None)]
            cr, ld = _crumbs(country, lang, trail)
            href = html.escape(it["url"])
            err = pct >= ERR_PCT
            chart = _chart(it, lang)
            related = [i for i in by_cat.get(c, []) if i is not it][:8]
            main = (
                cr + f'<article class="offer">'
                + (f'<div class="oimg"><img src="{html.escape(it["image"])}" alt="{html.escape(name)}"></div>' if it.get("image") else '<div class="oimg"></div>')
                + f'<div class="oinfo"><h1>{html.escape(name)}</h1>'
                f'<div class="badges"><span>-{pct}%</span>' + (f'<span class="e">⚡ {t["maybe"]}</span>' if err else '') + '</div>'
                f'<p class="pr"><b>{price}</b><s>{t["instead"]} {ref}</s></p>'
                f'<p class="meta">{_svg(I["shop"], 18, 2)}{html.escape(it["shop"])}</p>'
                + (f'<p class="meta">{sx["detected"]} {date}</p>' if date else '')
                + f'<a class="go" href="{href}" rel="sponsored nofollow noopener" target="_blank">{t["go"]} {_svg(I["arrow"], 18, 2.6)}</a>'
                f'<p class="note">{sx["note"]} {ui["aff_short"]}</p>'
                + (f'<details><summary>{_svg(I["chart"], 16, 2.2)}{t["chart"]}</summary>{chart}</details>' if chart else '')
                + '</div></article>'
                + (f'<section><h2>{sx["more"]} {html.escape(cl)}</h2><p class="count hidden" id="count"></p>'
                   f'<div class="grid" id="grid">{"".join(_card(i, lang, t, _off_path(i, lang, langs) if with_page(i) else None) for i in related)}</div>'
                   f'<div class="empty hidden" id="empty"><p id="emptytxt"></p></div></section>' if related else '')
            )
            _write(out_dir, _off_path(it, lang, langs),
                   _shell(country, lang, langs, t, ui, title, desc, lambda l, it=it: _off_path(it, l, langs), main, ld,
                          og_img=it.get("image"), cat_list=page_cats, js=bool(related)))
    # pagina adulti: conferma dei 18 anni, mai su Google (noindex, fuori dalla sitemap, nessun link seguibile)
    for lang in langs:
        root = os.path.join(out_dir, _pfx(lang, langs).strip("/")) if _pfx(lang, langs) else out_dir
        shutil.rmtree(os.path.join(root, SEO[lang]["adult_dir"]), ignore_errors=True)
        if not adult_items:
            continue
        t, ui, sx = T[lang], UI[lang], SEO[lang]
        home = _home_path(lang, langs)
        main = (
            f'<div class="agegate" id="agegate" role="dialog" aria-modal="true" aria-labelledby="ageh"><div>'
            f'<p class="big" aria-hidden="true">🔞</p><h2 id="ageh">{sx["age_h"]}</h2><p>{sx["age_p"]}</p>'
            f'<button type="button" id="ageok">{sx["age_y"]}</button><a href="{home}">{sx["age_n"]}</a></div></div>'
            f'<div class="locked" id="adultzone"><div class="pagehead"><h1>{sx["adult_h1"]} {t["in_" + country]}</h1></div>'
            f'<div class="layout">{_catside(lang, langs, counts, page_cats, t, checked={ADULT}, page="cat")}<div class="results">'
            f'<p class="count" id="count" aria-live="polite"></p>'
            f'<div class="grid" id="grid">{"".join(_card(dict(i, image="/assets/18plus.png"), lang, t) for i in adult_items)}</div>'
            f'<div class="empty hidden" id="empty"><p id="emptytxt"></p></div></div></div></div>'
            '<script>(function(){var g=document.getElementById("agegate"),z=document.getElementById("adultzone");'
            'function ok(){g.remove();z.classList.remove("locked");}'
            'try{if(localStorage.getItem("oc_18")==="1")ok();}catch(e){}'
            'document.getElementById("ageok").addEventListener("click",function(){try{localStorage.setItem("oc_18","1");}catch(e){}ok();});})();</script>'
        )
        _write(out_dir, _adult_path(lang, langs),
               _shell(country, lang, langs, t, ui, f'{sx["adult_h1"]} – Offerte Crollate', sx["age_p"],
                      lambda l: _adult_path(l, langs), main, cat_list=page_cats,
                      robots="noindex,nofollow,noimageindex,noarchive"))
    urls.append(("/privacy.html", today))
    _sitemap(out_dir, base, urls)
