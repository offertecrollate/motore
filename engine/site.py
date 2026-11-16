"""
Sito statico di Offerte Crollate.

  Un dominio per paese, con le pagine alla radice:
  offertecrollate.it   index.html (italiano)                  -> cartella countries.it.out_dir
  offertecrollate.ch   index.html (italiano), de.html, fr.html -> cartella countries.ch.out_dir
  In ogni dominio: privacy.html, assets/, deals.json, CNAME e un pulsante per passare all'altro paese.

Le pagine dei paesi hanno ricerca, filtro per categoria di prodotto, filtro per
sconto rispetto al prezzo abituale e ordinamento (tutto nel browser, senza server).
Regole Amazon: per i prodotti Amazon niente grafico, niente prezzo barrato, niente %.
"""
import html
import re
import json
import os
import shutil
from datetime import datetime
from typing import List

from . import categories as cats
from .models import Deal
from .texts import T, money

# ---------------------------------------------------------------- testi
UI = {
    "it": {"title": "Offerte Crollate", "tagline": "Errori di prezzo e offerte, prezzi controllati in meno di un'ora",
           "choose": "Dove fai acquisti?", "enter": "Vedi le offerte", "top": "Torna su",
           "pitch": "Raccogliamo i migliori sconti e gli errori di prezzo dei negozi più affidabili.",
           "pitch2": "Prezzi controllati in meno di un'ora, in Italia e in Svizzera: ti segnaliamo i ribassi più forti, prima che spariscano.",
           "perk1": "Errori di prezzo veri", "perk2": "Italia e Svizzera", "perk3": "Prezzi controllati in meno di un'ora", "active1": "offerta attiva", "activeN": "offerte attive",
           "home": "Cambia paese", "search": "Cerca un prodotto", "allcat": "Tutte le categorie", "cats": "Categorie", "allcats": "tutte", "catsel": "Mostra tutte", "shops": "Negozi", "allshops": "tutti", "shopsel": "Mostra tutti",
           "alldisc": "Tutti gli sconti", "from": "da", "sort": "Ordina",
           "s_new": "Più recenti", "s_disc": "Sconto più alto", "s_low": "Prezzo più basso",
           "found1": "offerta", "foundN": "offerte",
           "amznote": "Le offerte Amazon non mostrano lo sconto e compaiono solo con «Tutti gli sconti».",
           "soon_t": "Le prime offerte stanno arrivando", "soon_p": "Stiamo collegando i negozi. Da qui in poi i prezzi sono controllati in meno di un'ora e pubblichiamo solo i ribassi forti e gli errori di prezzo veri.", "soon_c": "Cosa troverai", "soon_tg": "Ricevile subito su Telegram", "soon_fb": "Seguici su Facebook", "follow": "Seguici", "group": "Community", "empty": "Nessuna offerta con questi filtri.", "reset": "Togli i filtri",
           "go": "Vai all'offerta", "chart": "Andamento del prezzo", "avg": "prezzo abituale",
           "asof": "Prezzo del", "change": "può cambiare in qualsiasi momento", "usual": "di solito",
           "privacy": "Info e privacy", "aff_short": "Link affiliati: se acquisti riceviamo una commissione, senza costi per te.",
           "amz": "In qualità di Affiliato Amazon io ricevo un guadagno dagli acquisti idonei.",
           "sub_it": "Le offerte più forti in Italia.", "sub_ch": "Le offerte più forti per chi vive in Svizzera."},
    "de": {"title": "Offerte Crollate", "tagline": "Preisfehler und Deals, Preise mindestens einmal pro Stunde geprüft",
           "choose": "Wo kaufst du ein?", "active1": "aktives Angebot", "activeN": "aktive Angebote",
           "home": "Land wechseln", "top": "Nach oben", "search": "Produkt suchen", "allcat": "Alle Kategorien", "cats": "Kategorien", "allcats": "alle", "catsel": "Alle anzeigen", "shops": "Shops", "allshops": "alle", "shopsel": "Alle anzeigen",
           "alldisc": "Alle Rabatte", "from": "ab", "sort": "Sortieren",
           "s_new": "Neueste", "s_disc": "Höchster Rabatt", "s_low": "Tiefster Preis",
           "found1": "Angebot", "foundN": "Angebote",
           "amznote": "Amazon-Angebote zeigen keinen Rabatt und erscheinen nur bei «Alle Rabatte».",
           "soon_t": "Die ersten Angebote sind unterwegs", "soon_p": "Wir verbinden gerade die Shops. Ab jetzt prüfen wir die Preise mindestens einmal pro Stunde und zeigen nur starke Preissenkungen und echte Preisfehler.", "soon_c": "Das findest du hier", "soon_tg": "Jetzt auf Telegram folgen", "soon_fb": "Folge uns auf Facebook", "follow": "Folge uns", "group": "Community", "empty": "Keine Angebote mit diesen Filtern.", "reset": "Filter entfernen",
           "go": "Zum Angebot", "chart": "Preisverlauf", "avg": "üblicher Preis",
           "asof": "Preis vom", "change": "kann sich jederzeit ändern", "usual": "üblich",
           "privacy": "Info und Datenschutz", "aff_short": "Affiliate-Links: Bei einem Kauf erhalten wir eine Provision, ohne Mehrkosten für dich.",
           "amz": "Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.",
           "sub_it": "Die stärksten Angebote in Italien.", "sub_ch": "Die stärksten Angebote für die Schweiz."},
    "fr": {"title": "Offerte Crollate", "tagline": "Erreurs de prix et bons plans, prix vérifiés au moins une fois par heure",
           "choose": "Où fais-tu tes achats ?", "active1": "offre active", "activeN": "offres actives",
           "home": "Changer de pays", "top": "Haut de page", "search": "Chercher un produit", "allcat": "Toutes les catégories", "cats": "Catégories", "allcats": "toutes", "catsel": "Tout afficher", "shops": "Boutiques", "allshops": "toutes", "shopsel": "Tout afficher",
           "alldisc": "Toutes les réductions", "from": "dès", "sort": "Trier",
           "s_new": "Plus récentes", "s_disc": "Plus forte réduction", "s_low": "Prix le plus bas",
           "found1": "offre", "foundN": "offres",
           "amznote": "Les offres Amazon n'affichent pas de réduction et n'apparaissent qu'avec «Toutes les réductions».",
           "soon_t": "Les premières offres arrivent", "soon_p": "Nous connectons les boutiques. Désormais, nous vérifions les prix au moins une fois par heure et ne publions que les fortes baisses et les vraies erreurs de prix.", "soon_c": "Ce que tu trouveras", "soon_tg": "Suivre sur Telegram", "soon_fb": "Suis-nous sur Facebook", "follow": "Suis-nous", "group": "Communauté", "empty": "Aucune offre avec ces filtres.", "reset": "Retirer les filtres",
           "go": "Voir l'offre", "chart": "Évolution du prix", "avg": "prix habituel",
           "asof": "Prix du", "change": "peut changer à tout moment", "usual": "d'habitude",
           "privacy": "Infos et confidentialité", "aff_short": "Liens affiliés : en cas d'achat nous touchons une commission, sans frais pour toi.",
           "amz": "En tant que Partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.",
           "sub_it": "Les meilleures offres en Italie.", "sub_ch": "Les meilleures offres pour la Suisse."},
}
# bandiere disegnate in SVG (le emoji delle bandiere su Windows diventano lettere "IT"/"CH")
FLAG_SVG = {
    "it": ('<svg class="flagsvg" viewBox="0 0 3 2" aria-hidden="true"><rect width="1" height="2" fill="#009246"/>'
           '<rect x="1" width="1" height="2" fill="#fff"/><rect x="2" width="1" height="2" fill="#ce2b37"/></svg>'),
    "ch": ('<svg class="flagsvg sq" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" fill="#da291c"/>'
           '<path d="M13 6h6v7h7v6h-7v7h-6v-7H6v-6h7z" fill="#fff"/></svg>'),
}
BIG_FLAG = {
    "it": ('<svg viewBox="0 0 120 84" aria-hidden="true"><defs>'
           '<clipPath id="wvit"><path d="M2 12 C30 0 58 22 118 6 L118 70 C60 86 30 64 2 78 Z"/></clipPath>'
           '<linearGradient id="glit" x1="0" y1="0" x2="1" y2="0">'
           '<stop offset="0" stop-color="#fff" stop-opacity=".0"/><stop offset=".28" stop-color="#fff" stop-opacity=".35"/>'
           '<stop offset=".42" stop-color="#000" stop-opacity=".18"/><stop offset=".7" stop-color="#fff" stop-opacity=".28"/>'
           '<stop offset="1" stop-color="#000" stop-opacity=".2"/></linearGradient></defs>'
           '<g clip-path="url(#wvit)"><rect width="40" height="84" fill="#009246"/><rect x="40" width="40" height="84" fill="#f4f5f0"/>'
           '<rect x="80" width="40" height="84" fill="#ce2b37"/><rect width="120" height="84" fill="url(#glit)"/></g></svg>'),
    "ch": ('<svg viewBox="0 0 120 84" aria-hidden="true"><defs>'
           '<clipPath id="wvch"><path d="M2 12 C30 0 58 22 118 6 L118 70 C60 86 30 64 2 78 Z"/></clipPath>'
           '<linearGradient id="glch" x1="0" y1="0" x2="1" y2="0">'
           '<stop offset="0" stop-color="#fff" stop-opacity=".0"/><stop offset=".28" stop-color="#fff" stop-opacity=".35"/>'
           '<stop offset=".42" stop-color="#000" stop-opacity=".2"/><stop offset=".7" stop-color="#fff" stop-opacity=".28"/>'
           '<stop offset="1" stop-color="#000" stop-opacity=".22"/></linearGradient></defs>'
           '<g clip-path="url(#wvch)"><rect width="120" height="84" fill="#da291c"/>'
           '<path d="M51 18h18v15h15v18H69v15H51V51H36V33h15z" fill="#fff"/><rect width="120" height="84" fill="url(#glch)"/></g></svg>'),
}
SWITCH = {"it": "Passa alle offerte in {}", "de": "Zu den Angeboten in {}", "fr": "Voir les offres en {}"}
COUNTRY = {"it": (FLAG_SVG["it"], {"it": "Italia", "de": "Italien", "fr": "Italie"}),
           "ch": (FLAG_SVG["ch"], {"it": "Svizzera", "de": "Schweiz", "fr": "Suisse"})}
DISCOUNTS = [30, 50, 70]

# ---------------------------------------------------------------- stile
FONT = ("<link rel=\"preload\" href=\"{root}assets/fonts/archivo.woff2\" as=\"font\" type=\"font/woff2\" crossorigin>"
        "<style>@font-face{{font-family:Archivo;src:url({root}assets/fonts/archivo.woff2) format(\"woff2\");"
        "font-weight:400 900;font-stretch:62% 125%;font-display:swap}}</style>")

CSS = """
:root{--bg:#f8f1f0;--ink:#2b1315;--muted:#7b5f5c;--card:#fff;--line:#ecdcda;--wine:#4a0f15;--wine2:#7a1420;
--crimson:#d90f26;--crimson2:#f02a40;--go:#0e8f4a;--go2:#0aa456;--gold:#f4b012;--gold2:#ffd56b;--cream:#fff4e6;--radius:16px}
*{box-sizing:border-box}
@view-transition{navigation:auto}
::view-transition-old(root),::view-transition-new(root){animation-duration:.22s;animation-timing-function:ease-out}
html.swiping,html.swiping body{overflow-x:hidden;background:#4a0f15}
.swipewrap{will-change:transform}
.swipehint{position:fixed;left:0;top:50%;z-index:30;width:44px;height:44px;margin-top:-22px;border-radius:50%;background:var(--wine);color:var(--gold2);
display:flex;align-items:center;justify-content:center;box-shadow:0 8px 20px -6px rgba(0,0,0,.6);opacity:0;transform:translateX(-50px);pointer-events:none}
.swipehint svg{width:22px;height:22px}
@media (prefers-reduced-motion:reduce){::view-transition-old(root),::view-transition-new(root){animation:none}}
html{background:var(--bg)}
body{margin:0;background:radial-gradient(1100px 520px at 50% -160px,#f9d9d7 0%,var(--bg) 70%);color:var(--ink);
font-family:Archivo,system-ui,sans-serif;font-size:16px;line-height:1.45;min-height:100vh;-webkit-text-size-adjust:100%}
a{color:var(--crimson)}
:focus-visible{outline:3px solid var(--gold);outline-offset:2px;border-radius:6px}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
.display{font-stretch:125%;font-weight:900;letter-spacing:-.01em;line-height:.95}
footer{border-top:1px solid var(--line);margin-top:40px;padding:14px 0 26px;color:var(--muted)}footer .wrap{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 20px}footer .fine{margin:0}.social{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;font-size:14px;font-weight:700}.social a{display:inline-flex;align-items:center;gap:6px;text-decoration:none;color:inherit}.social a:hover{text-decoration:underline}.social svg{width:18px;height:18px;flex:none}
footer p{margin:0;max-width:90ch}footer a{color:inherit}.fine{font-size:11px;opacity:.85}

/* ---------- pagina iniziale */
.hero{position:relative;margin:18px auto 0;max-width:min(1180px,calc((100vh - 300px) * 16 / 9));border-radius:22px;overflow:hidden;
box-shadow:0 26px 60px -28px rgba(122,20,32,.55);aspect-ratio:16/9;background:#2a0b0d}
.hero img{width:100%;height:100%;object-fit:cover;display:block}
.home{min-height:calc(100vh + 60px);padding-bottom:60px}.band{background:linear-gradient(180deg,#2a070b 0%,var(--wine) 100%);padding:22px 0 28px}.band-in{max-width:1520px;margin:0 auto;padding:0 18px;text-align:center}.band .hero{margin:0 auto;width:min(100%,calc(80vh * 16 / 9));max-width:none;aspect-ratio:16/9;box-shadow:0 30px 70px -25px rgba(0,0,0,.75)}.pitch{color:var(--cream);max-width:860px;margin:22px auto 0}.pitch h1{font-size:clamp(26px,3.3vw,50px);margin:0 0 12px;line-height:1.02;background:linear-gradient(180deg,#fff6d8 0%,#ffd56b 45%,#f4b012 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 3px 0 rgba(0,0,0,.35))}.pitch p{margin:0 auto;font-size:17px;color:#f6dcd7;max-width:58ch}.perks{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin:18px 0 0;padding:0}.perks li{display:flex;align-items:center;gap:8px;background:rgba(255,244,230,.1);border:1px solid rgba(255,213,107,.45);color:var(--cream);border-radius:999px;padding:8px 16px 8px 10px;font-weight:700;font-size:15px}.perks .dot{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:var(--gold);color:var(--wine);font-weight:900;font-size:14px}.perks .flags{display:inline-flex;align-items:center;gap:4px}.perks .flagsvg{width:24px;height:16px;border-radius:3px}.perks .flagsvg.sq{width:16px;height:16px}@media (max-width:900px){.band{padding:12px 0 20px}.band-in{padding:0 12px}.band .hero{width:100%}.pitch{margin-top:14px}.pitch h1{font-size:25px}.pitch p{font-size:14.5px}.perks{gap:6px}.perks li{font-size:13px;padding:6px 12px 6px 8px}}.home .tags{margin-top:24px}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}.choose{text-align:center;margin:40px 0 8px;font-size:clamp(28px,4.5vw,46px);color:var(--wine)}
.choose-sub{text-align:center;color:var(--muted);margin:0 0 30px}
.tags{display:grid;grid-template-columns:1fr 1fr;gap:26px;max-width:980px;margin:30px auto 0}
.flagsvg{width:84px;height:56px;border-radius:6px;display:block}.flagsvg.sq{width:58px;height:58px}
.tag{position:relative;display:flex;align-items:stretch;gap:22px;padding:26px 26px 26px 22px;border-radius:20px;text-decoration:none;color:var(--cream);overflow:hidden;
background:radial-gradient(120% 90% at 0% 0%,rgba(240,42,64,.38) 0%,transparent 55%),radial-gradient(90% 80% at 100% 100%,rgba(244,176,18,.18) 0%,transparent 60%),linear-gradient(160deg,#1c0508 0%,#0c0204 100%);
border:2px solid rgba(255,213,107,.6);box-shadow:0 0 0 1px rgba(240,42,64,.35),0 0 30px -4px rgba(240,42,64,.55),0 26px 50px -24px rgba(0,0,0,.9),inset 0 1px 0 rgba(255,244,230,.12);
transition:transform .18s ease,box-shadow .18s ease}
.tag::after{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(115deg,transparent 35%,rgba(255,213,107,.16) 48%,transparent 60%);opacity:.9}
.tag:hover,.tag:focus-visible{transform:translateY(-4px);box-shadow:0 0 0 1px rgba(255,213,107,.6),0 0 44px 0 rgba(240,42,64,.7),0 30px 56px -24px rgba(0,0,0,.95),inset 0 1px 0 rgba(255,244,230,.16);outline:none}
.tag .tflag{flex:none;align-self:center;width:118px;filter:drop-shadow(0 6px 10px rgba(0,0,0,.6)) drop-shadow(0 0 10px rgba(255,90,90,.25))}
.tag .tflag svg{display:block;width:100%;height:auto}
.tag .tbody{flex:1;min-width:0;display:flex;flex-direction:column;align-items:flex-start;gap:6px}.tag .tbody small:last-of-type{margin-bottom:8px}
.tag b{display:block;max-width:100%;font-size:clamp(26px,2.8vw,40px);line-height:.95;font-weight:900;font-stretch:125%;font-style:italic;text-transform:uppercase;letter-spacing:-.01em;
background:linear-gradient(180deg,#fff6d8 0%,#ffd56b 45%,#f4b012 70%,#c77d00 100%);-webkit-background-clip:text;background-clip:text;color:transparent;
filter:drop-shadow(0 3px 0 #3a0a0f) drop-shadow(0 0 12px rgba(244,176,18,.35))}
.tag small{display:block;font-weight:600;font-size:14px;color:#f6dcd7}
.tag .langs{font-weight:500;color:#e7b9b3}
.tag .go2{margin-top:auto;display:inline-block;transform:skewX(-14deg);background:linear-gradient(180deg,#ffe48a 0%,#f4b012 55%,#d99400 100%);color:#3a0a0f;
padding:9px 20px;border-radius:6px;font-weight:900;font-size:15px;font-stretch:110%;text-transform:uppercase;letter-spacing:.02em;white-space:nowrap;
box-shadow:0 0 0 2px #3a0a0f,0 0 18px rgba(244,176,18,.55)}
.tag .go2 span{display:inline-block;transform:skewX(14deg)}
@media (max-width:720px){.tags{gap:12px}.tag{flex-direction:column;align-items:stretch;gap:10px;padding:14px 12px 16px;border-radius:14px}.tag .tflag{align-self:flex-start}
.tag .tflag{width:72px}.tag b{font-size:clamp(17px,5.2vw,22px)}.tag small{font-size:12px}.tag .go2{font-size:11.5px;padding:7px 10px;margin:auto 6px 0 4px;align-self:stretch;text-align:center}
.flagsvg{width:64px;height:43px}.flagsvg.sq{width:46px;height:46px}.hero{border-radius:14px;margin-top:12px}}

.totop{position:fixed;right:16px;bottom:18px;z-index:20;width:48px;height:48px;border-radius:50%;border:0;cursor:pointer;
background:var(--wine);color:var(--gold2);box-shadow:0 10px 24px -8px rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;
opacity:0;transform:translateY(12px);pointer-events:none;transition:opacity .2s ease,transform .2s ease}
.totop.show{opacity:1;transform:none;pointer-events:auto}
.totop:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.totop svg{width:22px;height:22px}
@media (prefers-reduced-motion:reduce){.totop{transition:none}}
.soon{margin:28px auto 10px;max-width:760px;text-align:center;border-radius:20px;padding:34px 26px 30px;color:var(--cream);
background:radial-gradient(120% 90% at 0% 0%,rgba(240,42,64,.35) 0%,transparent 55%),radial-gradient(90% 80% at 100% 100%,rgba(244,176,18,.16) 0%,transparent 60%),linear-gradient(160deg,#2a070b 0%,#120305 100%);
border:2px solid rgba(255,213,107,.55);box-shadow:0 0 28px -6px rgba(240,42,64,.45),0 24px 50px -26px rgba(0,0,0,.7)}
.soon h2{margin:0 0 12px;font-size:clamp(24px,3.4vw,36px);line-height:1.05;font-style:italic;font-weight:900;font-stretch:120%;text-transform:uppercase;
background:linear-gradient(180deg,#fff6d8 0%,#ffd56b 45%,#f4b012 75%,#c77d00 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 3px 0 #3a0a0f)}
.soon p{margin:0 auto;max-width:56ch;color:#f6dcd7;font-size:16px}
.soon h3{margin:24px 0 10px;font-size:13px;letter-spacing:.06em;color:var(--gold2);font-weight:800}
.soon ul{list-style:none;display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin:0;padding:0}
.soon li{border:1px solid rgba(255,213,107,.4);background:rgba(255,244,230,.08);border-radius:999px;padding:7px 14px;font-weight:700;font-size:14px}
.soon .tg{display:inline-flex;align-items:center;gap:10px;margin-top:24px;text-decoration:none;transform:skewX(-12deg);
background:linear-gradient(180deg,#ffe48a 0%,#f4b012 55%,#d99400 100%);color:#3a0a0f;padding:11px 22px;border-radius:6px;font-weight:900;text-transform:uppercase;font-size:15px;
box-shadow:0 0 0 2px #3a0a0f,0 0 18px rgba(244,176,18,.5)}
.soon .tg span{display:inline-block;transform:skewX(12deg)}
.soon .ctas{display:flex;flex-wrap:wrap;justify-content:center;gap:14px;margin-top:24px}.soon .ctas .tg{margin-top:0}.soon .tg svg{width:18px;height:18px;transform:skewX(12deg);flex:none}.soon .tg{white-space:nowrap}.soon .tg.fb{background:#fff4e6;color:#3a0a0f;box-shadow:0 0 0 2px #3a0a0f,0 0 18px rgba(255,244,230,.35)}
@media (max-width:720px){.soon .ctas{flex-direction:column;align-items:center}.soon .tg{font-size:14px;padding:11px 18px}.soon{margin-top:18px;padding:24px 16px 22px;border-radius:16px}.soon p{font-size:14.5px}.soon li{font-size:13px;padding:6px 11px}}
/* ---------- pagine paese */
.mast{background:linear-gradient(135deg,var(--wine) 0%,var(--wine2) 100%);color:var(--cream)}
.top{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 0}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:var(--cream)}
.brand .logo{font-size:22px}
.brand .logo span{color:var(--gold)}
.langsw a{margin-left:12px;font-weight:700;text-decoration:none;color:#e4c3bf;padding:6px 2px}
.langsw a[aria-current]{color:var(--gold)}
.head{padding:4px 0 26px}
.head h1{font-size:clamp(34px,6vw,64px);margin:6px 0 0}
.head h1 .flagsvg{display:inline-block;width:.95em;height:.63em;vertical-align:baseline;margin-right:.15em}
.head h1 .flagsvg.sq{width:.7em;height:.7em}
.head p{margin:10px 0 0;color:#ecc9c4}
.back{font-size:14px;color:#ecc9c4}
.tools{position:sticky;top:0;z-index:5;background:rgba(255,255,255,.94);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line);padding:12px 0;box-shadow:0 6px 18px -14px rgba(74,15,21,.4)}
.row{display:flex;gap:10px;align-items:center}
.row+.row{margin-top:10px}
.search{flex:1 1 auto;position:relative;min-width:0}
.search input{width:100%;padding:12px 14px 12px 42px;border-radius:12px;border:1px solid var(--line);
background:#fff;color:var(--ink);font:inherit;font-size:16px}
.search svg{position:absolute;left:14px;top:50%;margin-top:-9px;color:var(--muted)}
select{padding:11px 12px;border-radius:12px;border:1px solid var(--line);background:#fff;color:var(--ink);font:inherit;font-size:16px}
.chips{display:flex;gap:8px;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;margin:0 -18px;padding:0 18px 2px}
.chips::-webkit-scrollbar{display:none}
.shops{position:relative;flex:0 0 auto}
.shops summary{list-style:none;cursor:pointer;white-space:nowrap}
.shops summary::-webkit-details-marker{display:none}
.shops[open] summary{background:var(--wine);color:var(--cream);border-color:var(--wine)}
.shoplist{position:absolute;right:0;top:calc(100% + 6px);z-index:9;background:#fff;border:1px solid var(--line);border-radius:14px;
 box-shadow:0 10px 30px rgba(74,15,21,.18);padding:10px;min-width:220px;max-height:60vh;overflow:auto;display:flex;flex-direction:column;gap:2px}
.shoplist label{display:flex;align-items:center;gap:8px;padding:7px 6px;border-radius:8px;font-size:14px;cursor:pointer}
.shoplist label:hover{background:var(--bg)}
.shoplist input{width:18px;height:18px;accent-color:var(--wine)}
.shoplist .n{margin-left:auto;color:var(--muted);font-size:12px}
.shoplist .chip{margin-top:6px;align-self:flex-start}
.shops.left .shoplist{left:0;right:auto}
.ddrow{flex-wrap:wrap}
.chip{flex:0 0 auto;border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:999px;
padding:8px 14px;font:inherit;font-size:14px;cursor:pointer;white-space:nowrap}
.chip .n{color:var(--muted);margin-left:6px;font-size:12px}
.chip[aria-pressed="true"]{background:var(--wine);color:var(--cream);border-color:var(--wine)}
.chip[aria-pressed="true"] .n{color:#e4c3bf}
.disc .chip[aria-pressed="true"]{background:var(--gold);color:var(--wine);border-color:var(--gold)}
.count{margin:20px 0 12px;color:var(--muted)}
.note{font-size:13px;color:var(--muted);margin:0 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(225px,1fr));gap:14px}
.deal{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
padding:12px;display:flex;flex-direction:column;gap:6px;position:relative;box-shadow:0 10px 24px -20px rgba(74,15,21,.45)}
.deal .imgbox{height:135px;border-radius:12px;background:#fff;display:flex;align-items:center;justify-content:center;
overflow:hidden;border:1px solid #f3e8e7;padding:10px}
.deal .imgbox img{max-width:100%;max-height:100%;object-fit:contain}
a.imgbox{cursor:pointer}
.pct{position:absolute;top:10px;right:-6px;z-index:1;background:var(--gold);color:var(--wine);font-stretch:110%;font-weight:900;
font-size:19px;padding:4px 14px 4px 20px;clip-path:polygon(10px 0,100% 0,100% 100%,10px 100%,0 50%);
filter:drop-shadow(0 4px 6px rgba(74,15,21,.25))}
.pct.hot{background:#e0142a;color:#fff;filter:drop-shadow(0 4px 8px rgba(224,20,42,.45))}
.level{font-weight:800;font-size:13px;color:var(--crimson)}
.level.offerta{color:#b77800}
.level.super{color:#d2141f;font-weight:900}
.level.crollo{color:#e0142a;font-stretch:125%;font-weight:900;font-style:normal;font-size:15px;letter-spacing:.01em;text-shadow:0 1px 0 rgba(224,20,42,.15)}
.gorow{margin-top:auto;display:flex;flex-direction:column;gap:6px}
.gorow .btn{margin-top:0}
.hurry{margin:0;font-size:11.5px;line-height:1.3;color:#b0101f;font-weight:700}
.name{font-size:14.5px;font-weight:600;line-height:1.28;margin:0;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.price{font-size:21px;font-weight:900;font-stretch:110%;color:var(--wine)}
.old{color:var(--muted);font-size:13px;margin-left:6px;display:inline-block;white-space:nowrap}
.old s{text-decoration-thickness:2px}
.meta{font-size:11.5px;line-height:1.35;color:var(--muted)}
.btn{display:block;text-align:center;background:var(--go);color:#fff;text-decoration:none;font-weight:800;
border-radius:10px;padding:9px;font-size:14.5px;margin-top:auto}
.btn:hover{background:var(--go2)}
.empty{text-align:center;padding:50px 10px;color:var(--muted)}
.empty button{margin-top:12px}
.hidden{display:none!important}
.cbox summary{font-size:12.5px;color:var(--muted);cursor:pointer;padding:2px 0}.cbox[open] summary{margin-bottom:2px}.chart{margin:4px 0 0;position:relative}
.chart figcaption{font-size:12px;color:var(--muted);margin-bottom:2px;display:flex;justify-content:flex-end}
.leg i{display:inline-block;width:16px;border-top:1px dashed #a88d89;margin-right:6px;vertical-align:middle}
.chart svg{width:100%;height:auto;display:block}
.chart .grid{stroke:#efe4e3;stroke-width:1}.chart .ref{stroke:#a88d89;stroke-width:1;stroke-dasharray:4 3}
.chart .ax{font-size:10px;fill:#7b5f5c}.chart .hx{stroke:#c8b3b0;stroke-width:1}
.tip{position:absolute;top:18px;background:var(--wine);color:var(--cream);font-size:12px;padding:4px 7px;
border-radius:5px;pointer-events:none;white-space:nowrap;transform:translateX(-50%)}
.legal{max-width:760px;margin:0 auto;padding:24px 18px;line-height:1.6}
.legal .imp{margin-top:36px;font-size:11px;line-height:1.4;color:var(--muted)}.legal h1{font-size:clamp(30px,5vw,48px);color:var(--wine)}
@media (max-width:640px){
 .grid{grid-template-columns:1fr;gap:8px}
 .tools{padding:10px 0}
 .row:first-child{flex-wrap:nowrap}
 select{max-width:36%;padding:11px 6px;font-size:15px}
 .search input{padding-left:38px}
 .head{padding-bottom:18px}
 .brand .logo{font-size:19px}
 .count{margin:14px 0 8px}
 /* scheda in stile Amazon: foto a sinistra, testo a destra */
 .deal{display:grid;grid-template-columns:84px 1fr;column-gap:10px;row-gap:2px;padding:8px;border-radius:12px;align-items:start}
 .deal>*{grid-column:2}
 .deal .imgbox{grid-column:1;grid-row:1/span 6;width:84px;height:84px;padding:4px;border-radius:8px}
 .deal>.pct{grid-column:1;grid-row:1}
 .pct{top:4px;left:4px;right:auto;font-size:12.5px;padding:2px 6px 2px 11px;clip-path:polygon(7px 0,100% 0,100% 100%,7px 100%,0 50%)}
 .level{font-size:11px}
 .name{font-size:13.5px;line-height:1.25;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
 .price{font-size:17px}
 .old{font-size:12.5px;margin-left:0;display:block;white-space:nowrap}
 .meta{font-size:11px;line-height:1.3}
 .cbox{grid-column:1/-1}
 .btn{grid-column:1/-1;padding:9px;font-size:14px;border-radius:10px;margin-top:6px}
 .gorow{grid-column:1/-1}
 .level.crollo{font-size:12.5px}
}
@media (max-width:640px){
 /* pagina iniziale: tutto centrato e in proporzione */
 .band{padding:10px 0 18px}
 .band-in{padding:0 10px}
 .band .hero{border-radius:12px}
 .pitch{margin-top:14px;padding:0 6px}
 .pitch h1{font-size:21px;line-height:1.12;margin-bottom:8px}
 .pitch p{font-size:13.5px;line-height:1.4}
 .perks{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:14px}
 .perks li{flex-direction:column;justify-content:flex-start;text-align:center;gap:5px;border-radius:12px;
  padding:9px 4px;font-size:11.5px;line-height:1.2;font-weight:700}
 .perks .dot{width:22px;height:22px;font-size:12px}
 .perks .flagsvg{width:22px;height:15px}.perks .flagsvg.sq{width:15px;height:15px;margin-left:0}
 .perks li:nth-child(2){flex-direction:column}
 .home .tags{grid-template-columns:1fr 1fr;gap:10px;margin-top:18px;padding:0 2px}
 /* pagine paese: intestazione più bassa, pulsante piccolo come su Amazon */
 .head h1{font-size:34px}
 .head p{font-size:14px;margin-top:6px}
 .btn{grid-column:2!important;justify-self:start;display:inline-block;padding:7px 14px!important;font-size:13px!important;
  border-radius:8px!important;margin-top:6px!important}
 .cbox{grid-column:2!important}
 .cbox summary{font-size:11.5px}
}
html:has(body.homepage){background:#4a0f15}body.homepage{background:linear-gradient(180deg,#2a070b 0px,var(--wine) 380px,var(--wine) 100%)}.homepage .band{background:none}.homepage footer{border-top-color:rgba(255,255,255,.12);color:#d9b3ae}.homepage footer a{color:var(--gold2)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

CHART_JS = """
if(window.matchMedia('(max-width:640px)').matches){document.querySelectorAll('details.cbox').forEach(function(d){d.open=false})}
document.querySelectorAll('.chart').forEach(function(f){
 var svg=f.querySelector('svg'),hit=f.querySelector('.hit'),tip=f.querySelector('.tip');
 var pts=JSON.parse(svg.dataset.pts),hx=f.querySelector('.hx'),hd=f.querySelector('.hd');
 var poly=svg.querySelector('polyline').getAttribute('points').split(' ').map(function(p){return p.split(',').map(Number)});
 function show(ev){var r=svg.getBoundingClientRect(),vb=svg.viewBox.baseVal;
  var e=ev.touches?ev.touches[0]:ev,sx=(e.clientX-r.left)*vb.width/r.width;
  var i=0,best=1e9;poly.forEach(function(p,k){var d=Math.abs(p[0]-sx);if(d<best){best=d;i=k}});
  var p=poly[i];hx.setAttribute('x1',p[0]);hx.setAttribute('x2',p[0]);hd.setAttribute('cx',p[0]);hd.setAttribute('cy',p[1]);
  hx.setAttribute('visibility','visible');hd.setAttribute('visibility','visible');
  tip.hidden=false;tip.textContent=pts[i][0]+'  '+pts[i][1];tip.style.left=(p[0]*r.width/vb.width)+'px'}
 function hide(){tip.hidden=true;hx.setAttribute('visibility','hidden');hd.setAttribute('visibility','hidden')}
 hit.addEventListener('mousemove',show);hit.addEventListener('touchstart',show,{passive:true});
 hit.addEventListener('touchmove',show,{passive:true});hit.addEventListener('mouseleave',hide);
});"""

FILTER_JS = """
(function(){
 if(!document.getElementById('grid')) return;
 var st={q:'',cat:null,shop:null,min:0,sort:'new'};
 var grid=document.getElementById('grid'),cards=[].slice.call(grid.children);
 var cnt=document.getElementById('count'),empty=document.getElementById('empty'),note=document.getElementById('amznote');
 var L=JSON.parse(document.getElementById('L').textContent);
 function apply(){
  var n=0;
  cards.forEach(function(c){
   var pct=+c.dataset.pct, ok=(!st.cat||st.cat.indexOf(c.dataset.cat)>=0)&&(!st.shop||st.shop.indexOf(c.dataset.shop)>=0)
     &&(st.min===0||pct>=st.min)&&(!st.q||c.dataset.q.indexOf(st.q)>=0);
   c.classList.toggle('hidden',!ok); if(ok)n++;});
  var key={new:function(c){return -c.dataset.ts},disc:function(c){return -(+c.dataset.pct)},low:function(c){return +c.dataset.price}}[st.sort];
  cards.slice().sort(function(a,b){return key(a)-key(b)}).forEach(function(c){grid.appendChild(c)});
  cnt.textContent=n+' '+(n===1?L.found1:L.foundN);
  empty.classList.toggle('hidden',n>0); note.classList.toggle('hidden',st.min===0||!grid.querySelector('[data-pct="-1"]'));
 }
 var dds=[].slice.call(document.querySelectorAll('details[data-k]'));
 dds.forEach(function(d){
  var k=d.dataset.k, bs=[].slice.call(d.querySelectorAll('input')), lbl=d.querySelector('.ddn');
  function read(){var on=bs.filter(function(b){return b.checked}).map(function(b){return b.value});
   st[k]=(on.length===bs.length)?null:on; lbl.textContent=st[k]?on.length+'/'+bs.length:L['all_'+k];
   try{localStorage.setItem(L.key+k,JSON.stringify(st[k]))}catch(e){}}
  try{var sv=JSON.parse(localStorage.getItem(L.key+k)||'null'); if(sv&&sv.length)bs.forEach(function(b){b.checked=sv.indexOf(b.value)>=0})}catch(e){}
  read();
  bs.forEach(function(b){b.addEventListener('change',function(){read();apply()})});
  d.querySelector('.ddall').addEventListener('click',function(){bs.forEach(function(b){b.checked=true});read();apply()});
  d.read=read; d.boxes=bs;
 });
 document.addEventListener('click',function(e){dds.forEach(function(d){if(d.open&&!d.contains(e.target))d.open=false})});
 dds.forEach(function(d){d.addEventListener('toggle',function(){if(d.open)dds.forEach(function(o){if(o!==d)o.open=false})})});
 var bs=document.querySelectorAll('.disc .chip');
 bs.forEach(function(b){b.addEventListener('click',function(){
  bs.forEach(function(x){x.setAttribute('aria-pressed','false')});b.setAttribute('aria-pressed','true');
  st.min=+b.dataset.v;apply();});});
 document.getElementById('q').addEventListener('input',function(e){st.q=e.target.value.trim().toLowerCase();apply()});
 document.getElementById('sort').addEventListener('change',function(e){st.sort=e.target.value;apply()});
 document.getElementById('reset').addEventListener('click',function(){
  st.q='';st.min=0;document.getElementById('q').value='';
  dds.forEach(function(d){d.boxes.forEach(function(b){b.checked=true});d.read()});
  bs.forEach(function(b,i){b.setAttribute('aria-pressed',i===0?'true':'false')});
  apply();});
 apply();
})();"""



TOTOP_JS = """
(function(){var b=document.getElementById('totop');if(!b)return;
 function f(){b.classList.toggle('show',window.scrollY>400)}
 window.addEventListener('scroll',f,{passive:true});f();
 b.addEventListener('click',function(){var r=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  window.scrollTo({top:0,behavior:r?'auto':'smooth'});document.getElementById('q')&&document.getElementById('q').focus({preventScroll:true});});
})();"""
TOTOP_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>'

SWIPE_JS = r"""
(function(){
 var home='../index.html', ref=document.referrer||'', fromHome=/\/(index\.html)?$/.test(ref.split('?')[0])&&ref.indexOf(location.host)>=0;
 function goHome(){ if(fromHome&&history.length>1){history.back();} else {location.href=home;} }
 var back=document.querySelector('.back'); if(back) back.addEventListener('click',function(e){ if(fromHome&&history.length>1){e.preventDefault();history.back();}});
 var wrap=document.querySelector('.swipewrap'), hint=document.getElementById('swipehint'); if(!wrap) return;
 var x0=0,y0=0,dx=0,mode=null,W=window.innerWidth;
 var skip='.chips,.shoplist,details[open],input,select,textarea,.chart,.cbox,button';
 document.addEventListener('touchstart',function(e){ if(e.touches.length!==1){mode='no';return;} var t=e.touches[0];
  if(e.target.closest&&e.target.closest(skip)){mode='no';return;} x0=t.clientX;y0=t.clientY;dx=0;mode=null;W=window.innerWidth;},{passive:true});
 document.addEventListener('touchmove',function(e){ if(mode==='no')return; var t=e.touches[0], mx=t.clientX-x0, my=t.clientY-y0;
  if(mode===null){ if(Math.abs(mx)<10&&Math.abs(my)<10)return; mode=(mx>0&&Math.abs(mx)>Math.abs(my)*1.4)?'swipe':'no'; if(mode==='swipe'){document.documentElement.classList.add('swiping');wrap.style.transition='none';} }
  if(mode!=='swipe')return; dx=Math.max(0,mx); wrap.style.transform='translateX('+dx+'px)'; wrap.style.opacity=String(1-Math.min(dx/W,1)*0.35);
  if(hint){var k=Math.min(dx/(W*0.3),1); hint.style.opacity=k; hint.style.transform='translateX('+(-50+k*66)+'px)';} },{passive:true});
 function end(){ if(mode!=='swipe'){mode=null;return;} mode=null; var go=dx>W*0.28;
  wrap.style.transition='transform .18s ease-out,opacity .18s ease-out';
  if(go){ wrap.style.transform='translateX('+W+'px)'; wrap.style.opacity='0'; setTimeout(goHome,150); }
  else { wrap.style.transform=''; wrap.style.opacity=''; if(hint){hint.style.opacity=0;hint.style.transform='';} setTimeout(function(){document.documentElement.classList.remove('swiping')},200); } }
 document.addEventListener('touchend',end,{passive:true}); document.addEventListener('touchcancel',end,{passive:true});
 window.addEventListener('pageshow',function(){ wrap.style.transition='none'; wrap.style.transform=''; wrap.style.opacity=''; if(hint){hint.style.opacity=0;hint.style.transform='';} document.documentElement.classList.remove('swiping'); });
})();"""
BACK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>'


OG_DESC = {"it": "Errori di prezzo e offerte forti in Italia e Svizzera, prezzi controllati in meno di un'ora.",
           "de": "Preisfehler und starke Angebote in der Schweiz und Italien, Preise mindestens einmal pro Stunde geprüft.",
           "fr": "Erreurs de prix et grosses offres en Suisse et en Italie, prix vérifiés au moins une fois par heure."}
SITE_URL = "https://offertecrollate.ch"
DOMAINS = {"it": "offertecrollate.it", "ch": "offertecrollate.ch"}


def base_url(country: str) -> str:
    return f"https://{DOMAINS.get(country, 'offertecrollate.ch')}"


# codici di verifica di Google Search Console (uno per dominio)
GSC_VERIFY = {"offertecrollate.it": "OZ3wBHjv3uBoXwLiADLMJJR8vDE0ucPfGnofFKjhhZs",
              "offertecrollate.ch": "6peHQw8txdbMZDLeVGiCjzepB1ZAS89WnxfvUNbZk5Y"}


def _og(lang: str, title: str, path: str, base: str = SITE_URL, desc: str = None, img: str = None,
        locale: str = None, robots: str = "index,follow,max-image-preview:large") -> str:
    """Anteprima per WhatsApp, Telegram, Facebook ecc. quando si condivide il link,
    più descrizione e canonical per Google."""
    own_img = bool(img)
    img = html.escape(img) if img else f"{base}/assets/og.jpg?v=3"
    d = html.escape(desc or OG_DESC.get(lang, OG_DESC["it"]))
    t = html.escape(title)
    gsc = GSC_VERIFY.get(base.split("//")[-1].strip("/"), "")
    loc = locale or {"it": "it_IT", "de": "de_CH", "fr": "fr_CH"}.get(lang, "it_IT")
    return ((f'<meta name="google-site-verification" content="{gsc}">' if gsc else '') +
            f'<meta name="description" content="{d}"><meta name="robots" content="{robots}">'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="Offerte Crollate">'
            f'<meta property="og:title" content="{t}"><meta property="og:description" content="{d}">'
            f'<meta property="og:url" content="{base}/{path}"><link rel="canonical" href="{base}/{path}">'
            f'<meta property="og:image" content="{img}"><meta property="og:image:secure_url" content="{img}">'
            + ('' if own_img else
               f'<meta property="og:image:type" content="image/jpeg">'
               f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">')
            + f'<meta property="og:image:alt" content="{t if own_img else "Offerte Crollate"}">'
            f'<meta property="og:locale" content="{loc}">'
            f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{img}">')


def _page(lang: str, title: str, body: str, scripts: str = "", cls: str = "", root: str = "", prerender=(),
          path: str = "", base: str = SITE_URL) -> str:
    spec = ('<script type="speculationrules">' + json.dumps({"prerender": [{"source": "list", "urls": list(prerender), "eagerness": "eager"}]}) + "</script>") if prerender else ""
    return (f'<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="theme-color" content="#4a0f15">'
            f'<title>{html.escape(title)}</title>{_og(lang, title, path, base)}{FONT.format(root=root)}<style>{CSS}</style>{spec}</head>'
            f'<body class="{cls}">{body}{scripts}</body></html>')


FB_URL = "https://www.facebook.com/offertecrollate"
TG_URL = "https://t.me/offertecrollate"
GROUP_URL = "https://www.facebook.com/groups/offertecrollate"
FB_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7.1V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.4l-.5 3.5h-2.9v8.4A12 12 0 0 0 24 12z"/></svg>'
TG_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24zm5.9 8.2-2 9.4c-.1.7-.5.8-1.1.5l-3-2.2-1.5 1.4c-.2.2-.3.3-.6.3l.2-3.1 5.6-5c.2-.2 0-.3-.4-.1l-6.9 4.3-3-.9c-.6-.2-.7-.6.1-1l11.6-4.5c.6-.2 1.1.1.9.9z"/></svg>'


def _footer(lang: str, prefix: str, disclosure: bool = True) -> str:
    """Riga piccola in fondo: avviso affiliazione solo nelle pagine con link ai negozi."""
    ui = UI[lang]
    note = f'{ui["aff_short"]} {ui["amz"]} ' if disclosure else ""
    social = (f'<nav class="social" aria-label="{ui["follow"]}"><span>{ui["follow"]}:</span>'
              f'<a href="{FB_URL}" target="_blank" rel="noopener">{FB_SVG}Facebook</a>'
              f'<a href="{GROUP_URL}" target="_blank" rel="noopener">{FB_SVG}{ui.get("group", "Community")} Facebook</a>'
              f'<a href="{TG_URL}" target="_blank" rel="noopener">{TG_SVG}Telegram</a></nav>')
    return (f'<footer><div class="wrap"><p class="fine">{note}'
            f'<a href="{prefix}privacy.html">{ui["privacy"]}</a></p>{social}</div></footer>')


# ---------------------------------------------------------------- dati
def _load(path: str) -> list:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def country_dir(site: dict, country: str) -> str:
    """Cartella del dominio del paese (es. site_it/ per offertecrollate.it)."""
    ccfg = site["countries"][country]
    return ccfg.get("out_dir") or os.path.join(site.get("out_dir", "site"), country)


def update_site(deals: List[Deal], country: str, site: dict, keep: int = 400, replace_sources=()) -> None:
    ccfg = site["countries"][country]
    out_dir = country_dir(site, country)
    os.makedirs(out_dir, exist_ok=True)
    data_path = os.path.join(out_dir, "deals.json")

    now = datetime.now().isoformat(timespec="minutes")
    new = [{
        "key": d.product.key, "source": d.product.source,
        "category": cats.ADULT[0] if d.extra.get("adult") else cats.categorize(d.product.name, d.product.category or ""),
        "name": d.product.name, "price": d.product.price, "ref": d.reference_price,
        "pct": d.discount_pct, "level": d.level, "shop": d.product.shop,
        "url": d.product.url, "image": d.product.image,
        "currency": d.product.currency, "at": now,
        "history": d.extra.get("history", []),
    } for d in deals]
    seen, items = set(), []          # la versione più recente sostituisce quella vecchia
    old = _load(data_path)
    if replace_sources:              # negozi "solo sito": resta solo ciò che è in offerta adesso
        old = [it for it in old if it.get("source") not in set(replace_sources)]
    for it in new + old:
        if it["key"] not in seen:
            seen.add(it["key"])
            items.append(it)
    items = items[:keep]
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)

    render_country(items, country, ccfg, out_dir)
    render_extras(site, country)


def remove_from_site(keys, country: str, site: dict) -> int:
    """Toglie dal sito le offerte terminate e rigenera le pagine."""
    ccfg = site["countries"][country]
    out_dir = country_dir(site, country)
    data_path = os.path.join(out_dir, "deals.json")
    items = _load(data_path)
    keep = [it for it in items if it["key"] not in set(keys)]
    if len(keep) != len(items):
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(keep, f, ensure_ascii=False, indent=1)
        render_country(keep, country, ccfg, out_dir)
        render_extras(site, country)
    return len(items) - len(keep)


# ---------------------------------------------------------------- grafico
LINE = "#d90f26"      # una sola serie: un solo colore (rosso del marchio)
W, H, PL, PR, PT, PB = 320, 110, 58, 10, 10, 20


def _short_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}."


def _axis_money(v: float, cur: str) -> str:
    return f"CHF {v:,.0f}".replace(",", "'") if cur == "CHF" else f"{v:,.0f} €".replace(",", ".")


def _chart(it: dict, lang: str) -> str:
    """Grafico SVG dell'andamento del prezzo (solo negozi non Amazon)."""
    hist = it.get("history") or []
    # grafico solo se racconta qualcosa: almeno 5 giorni e prezzo che si è mosso
    # (con 2 giorni allo stesso prezzo veniva una riga piatta lontana dal prezzo "prima")
    if len(hist) < 5 or len({p for _, p in hist}) < 2:
        return ""
    ui, cur = UI[lang], it["currency"]
    prices = [p for _, p in hist]
    lo, hi = min(prices + [it["ref"]]), max(prices + [it["ref"]])
    pad = (hi - lo) * 0.08 or 1
    lo, hi = max(0, lo - pad), hi + pad
    n = len(hist)

    def x(i): return PL + (W - PL - PR) * i / (n - 1)
    def y(v): return PT + (H - PT - PB) * (1 - (v - lo) / (hi - lo))

    pts = " ".join(f"{x(i):.1f},{y(p):.1f}" for i, (_, p) in enumerate(hist))
    data = json.dumps([[_short_date(d), money(p, cur)] for d, p in hist], ensure_ascii=False)
    yr = y(it["ref"])
    top, bot = max(prices), min(prices)
    return (
        f'<details class="cbox" open><summary>{ui["chart"]}</summary>'
        f'<figure class="chart"><figcaption><span class="leg"><i></i>{ui["avg"]}</span></figcaption>'
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{ui["chart"]}" data-pts="{html.escape(data)}">'
        f'<line x1="{PL}" x2="{W-PR}" y1="{y(top):.1f}" y2="{y(top):.1f}" class="grid"/>'
        f'<line x1="{PL}" x2="{W-PR}" y1="{y(bot):.1f}" y2="{y(bot):.1f}" class="grid"/>'
        f'<text x="{PL-6}" y="{y(top)+4:.1f}" class="ax" text-anchor="end">{_axis_money(top, cur)}</text>'
        f'<text x="{PL-6}" y="{y(bot)+4:.1f}" class="ax" text-anchor="end">{_axis_money(bot, cur)}</text>'
        f'<line x1="{PL}" x2="{W-PR}" y1="{yr:.1f}" y2="{yr:.1f}" class="ref"/>'
        f'<polyline points="{pts}" fill="none" stroke="{LINE}" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{x(n-1):.1f}" cy="{y(prices[-1]):.1f}" r="4.5" fill="{LINE}" stroke="#fff" stroke-width="2"/>'
        f'<text x="{PL}" y="{H-4}" class="ax">{_short_date(hist[0][0])}</text>'
        f'<text x="{W-PR}" y="{H-4}" class="ax" text-anchor="end">{_short_date(hist[-1][0])}</text>'
        f'<line class="hx" y1="{PT}" y2="{H-PB}" x1="0" x2="0" visibility="hidden"/>'
        f'<circle class="hd" r="4.5" fill="{LINE}" stroke="#fff" stroke-width="2" visibility="hidden"/>'
        f'<rect x="{PL}" y="0" width="{W-PL-PR}" height="{H}" fill="transparent" class="hit"/>'
        f'</svg><div class="tip" hidden></div></figure></details>'
    )


# ---------------------------------------------------------------- schede
def is_amazon(it: dict) -> bool:
    """Amazon vieta storico/confronto prezzi sul sito: per i suoi prodotti niente grafico, prezzo barrato e %."""
    # con Keepa abbiamo la media vera a 90 giorni: allora sconto e prezzo di riferimento si mostrano
    if str(it.get("source", "")).startswith("amazon"):
        return not (it.get("ref") and it.get("price") and it["ref"] > it["price"])
    return False


def _stamp(iso: str, lang: str) -> str:
    d, _, t = iso.partition("T")
    y, m, dd = d.split("-")
    return f'{UI[lang]["asof"]} {dd}.{m}.{y} {t[:5]}'


def _ts(iso: str) -> int:
    try:
        return int(datetime.fromisoformat(iso).timestamp())
    except ValueError:
        return 0


def _shop_id(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', (name or '').lower()).strip('-') or 'altro'


LBL = {
    "it": {"super": "SUPER OFFERTA", "crollo": "OFFERTA CROLLATA",
           "hurry": "Prezzo fuori dal normale: forse un errore, può sparire da un momento all'altro"},
    "de": {"super": "SUPER-DEAL", "crollo": "PREIS EINGESTÜRZT",
           "hurry": "Ungewöhnlich tiefer Preis: vielleicht ein Fehler, kann jederzeit verschwinden"},
    "fr": {"super": "SUPER BON PLAN", "crollo": "PRIX EFFONDRÉ",
           "hurry": "Prix anormalement bas : peut-être une erreur, peut disparaître à tout moment"},
}


def _label(it: dict, lang: str, t: dict) -> str:
    """Etichetta sopra il nome: più forte lo sconto, più forte la scritta."""
    if it.get("level") == "errore":
        return f'<div class="level errore">{t["errore"]}</div>'
    pct, L = it.get("pct", 0), LBL.get(lang, LBL["it"])
    if not is_amazon(it) and pct > 75:
        return f'<div class="level crollo">💥 {L["crollo"]}</div>'
    if not is_amazon(it) and pct > 50:
        return f'<div class="level super">🔥 {L["super"]}</div>'
    return f'<div class="level offerta">{t["offerta"]}</div>'


def _hurry(it: dict, lang: str, amz: bool) -> str:
    if amz or it.get("pct", 0) <= 80:
        return ""
    return f'<p class="hurry">⚠️ {LBL.get(lang, LBL["it"])["hurry"]}</p>'


def _card(it: dict, lang: str) -> str:
    t, ui = T[lang], UI[lang]
    amz = is_amazon(it)
    cat = it.get("category") or cats.categorize(it["name"])
    href = html.escape(it["url"])
    img = (f'<a class="imgbox" href="{href}" rel="sponsored nofollow noopener" target="_blank" tabindex="-1">'
           f'<img src="{html.escape(it["image"])}" alt="{html.escape(it["name"])}" loading="lazy"></a>'
           if it.get("image") else '<div class="imgbox"></div>')
    hot = " hot" if it["pct"] > 50 else ""
    pct = "" if amz else f'<div class="pct{hot}" aria-label="sconto">-{it["pct"]:.0f}%</div>'
    old = "" if amz else (f'<span class="old">{ui["usual"]} <s>{money(it["ref"], it["currency"])}</s></span>')
    q = html.escape(f'{it["name"]} {it["shop"]}'.lower())
    return (
        f'<article class="deal" data-cat="{cat}" data-pct="{-1 if amz else round(it["pct"])}" '
        f'data-price="{it["price"]}" data-ts="{_ts(it["at"])}" data-shop="{_shop_id(it["shop"])}" data-q="{q}">'
        f'{pct}{img}'
        f'{_label(it, lang, t)}'
        f'<h3 class="name">{html.escape(it["name"])}</h3>'
        f'<div><span class="price">{money(it["price"], it["currency"])}</span>{old}</div>'
        f'<div class="meta">{html.escape(it["shop"])} · {_stamp(it["at"], lang)}, {ui["change"]}</div>'
        f'{"" if amz else _chart(it, lang)}'
        f'<div class="gorow"><a class="btn" rel="sponsored nofollow noopener" target="_blank" '
        f'href="{html.escape(it["url"])}">{ui["go"]}</a>{_hurry(it, lang, amz)}</div>'
        f'</article>'
    )


SEARCH_ICON = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
               'aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>')


def render_country(items: list, country: str, ccfg: dict, out_dir: str) -> None:
    """Pagine del paese: nuovo look (site_v2), approvato il 14/11/2026."""
    from .site_v2 import render_country as nuovo
    return nuovo(items, country, ccfg, out_dir)


def render_country_vecchio(items: list, country: str, ccfg: dict, out_dir: str) -> None:
    langs = ccfg["langs"]
    flag, names = COUNTRY[country]
    for it in items:
        it.setdefault("category", cats.categorize(it["name"]))
    counts = {}
    for it in items:
        counts[it["category"]] = counts.get(it["category"], 0) + 1
    for lang in langs:
        ui = UI[lang]
        fname = lambda l: "index.html" if l == langs[0] else f"{l}.html"
        langsw = "".join(
            f'<a href="{fname(l)}"{" aria-current=page" if l == lang else ""}>{l.upper()}</a>' for l in langs
        ) if len(langs) > 1 else ""
        other = "ch" if country == "it" else "it"
        oflag, onames = COUNTRY[other]
        switch = (f'<a class="back switch" href="{base_url(other)}/">{oflag} '
                  f'{SWITCH[lang].format(onames[lang])}</a>')
        cat_list = "".join(
            f'<label><input type="checkbox" value="{c}" checked> {cats.label(c, lang)}<span class="n">{counts[c]}</span></label>'
            for c in cats.ORDER if counts.get(c))
        cat_box = (f'<details class="shops left" data-k="cat"><summary class="chip">{ui["cats"]}: <b class="ddn">{ui["allcats"]}</b></summary>'
                   f'<div class="shoplist">{cat_list}'
                   f'<button class="chip ddall" type="button">{ui["catsel"]}</button></div></details>') if counts else ""
        disc_chips = (f'<button class="chip" data-v="0" aria-pressed="true">{ui["alldisc"]}</button>' +
                      "".join(f'<button class="chip" data-v="{d}" aria-pressed="false">{ui["from"]} -{d}%</button>'
                              for d in DISCOUNTS))
        shops = {}
        for it in items:
            sid = _shop_id(it["shop"])
            name, n = shops.get(sid, (it["shop"], 0))
            shops[sid] = (name, n + 1)
        shop_list = "".join(
            f'<label><input type="checkbox" value="{sid}" checked> {html.escape(nm)}<span class="n">{n}</span></label>'
            for sid, (nm, n) in sorted(shops.items(), key=lambda x: x[1][0].lower()))
        shop_box = (f'<details class="shops" data-k="shop"><summary class="chip">{ui["shops"]}: <b class="ddn">{ui["allshops"]}</b></summary>'
                    f'<div class="shoplist">{shop_list}'
                    f'<button class="chip ddall" type="button">{ui["shopsel"]}</button></div></details>') if shops else ""
        cards = "".join(_card(it, lang) for it in items)
        if not items:
            cat_pills = "".join(f'<li>{cats.label(c, lang)}</li>' for c in cats.ORDER if c != cats.OTHER[0])
            cta = (f'<div class="ctas"><a class="tg fb" href="{FB_URL}" target="_blank" rel="noopener">{FB_SVG}<span>{ui["soon_fb"]}</span></a>'
                   + (f'<a class="tg" href="{TG_URL}" target="_blank" rel="noopener">{TG_SVG}<span>{ui["soon_tg"]}</span></a>' if country == "it" else "")
                   + '</div>')
            soon = (f'<section class="soon"><h2>{ui["soon_t"]}</h2><p>{ui["soon_p"]}</p>'
                    f'<h3>{ui["soon_c"]}</h3><ul>{cat_pills}</ul>{cta}</section>')
        labels = json.dumps({"found1": ui["found1"], "foundN": ui["foundN"], "all_shop": ui["allshops"], "all_cat": ui["allcats"], "key": "oc_" + country + "_"}, ensure_ascii=False)
        body = (
            f'<div class="swipewrap"><div class="mast"><div class="wrap"><nav class="top"><a class="brand" href="index.html" aria-label="Offerte Crollate">'
            f'<span class="logo display">Offerte <span>Crollate</span></span></a>'
            f'<div class="langsw">{langsw}</div></nav>'
            f'<header class="head">{switch}'
            f'<h1 class="display">{flag} {names[lang]}</h1><p>{ui["sub_" + country]}</p></header></div></div>'
            + (f'<main class="wrap">{soon}</main>' if not items else (
            f'<div class="tools"><div class="wrap">'
            f'<div class="row"><label class="search">{SEARCH_ICON}'
            f'<input id="q" type="search" placeholder="{ui["search"]}" aria-label="{ui["search"]}"></label>'
            f'<select id="sort" aria-label="{ui["sort"]}"><option value="new">{ui["s_new"]}</option>'
            f'<option value="disc">{ui["s_disc"]}</option><option value="low">{ui["s_low"]}</option></select></div>'
            f'<div class="row ddrow">{cat_box}{shop_box}</div>'
            f'<div class="row chips disc" role="group">{disc_chips}</div>'
            f'</div></div>'
            f'<main class="wrap"><p class="count" id="count" aria-live="polite"></p>'
            f'<p class="note hidden" id="amznote">{ui["amznote"]}</p>'
            f'<div class="grid" id="grid">{cards}</div>'
            f'<div class="empty hidden" id="empty"><p>{ui["empty"]}</p>'
            f'<button class="chip" id="reset" type="button">{ui["reset"]}</button></div></main>'))
            + 
            f'{_footer(lang, "")}</div>'
            f'<button class="totop" id="totop" type="button" aria-label="{ui["top"]}" title="{ui["top"]}">{TOTOP_SVG}</button>'
            f'<script type="application/json" id="L">{labels}</script>'
        )
        page = _page(lang, f'{ui["title"]} – {names[lang]}', body,
                     f"<script>{FILTER_JS}{CHART_JS}{TOTOP_JS}</script>", root="",
                     path="" if lang == langs[0] else f"{lang}.html", base=base_url(country))
        with open(os.path.join(out_dir, fname(lang)), "w", encoding="utf-8") as f:
            f.write(page)


# ---------------------------------------------------------------- privacy
def render_privacy(site: dict, country: str = "ch") -> None:
    """Pagina privacy/cookie/affiliazione. BOZZA: i dati del titolare vanno confermati in config (site.owner)."""
    o = site.get("owner", {})
    name = html.escape(o.get("name", "[NOME E COGNOME DA CONFERMARE]"))
    addr = html.escape(o.get("address", "[INDIRIZZO DA CONFERMARE]"))
    mail = html.escape(o.get("email", "[EMAIL DA CONFERMARE]"))
    body = f"""<main class="legal"><a href="index.html">Offerte Crollate</a>
<h1 class="display">Info e privacy</h1>
<h2>Quali dati raccogliamo</h2><p>Questo sito non richiede registrazione, non ha moduli e non usa cookie propri
né strumenti di statistica. Il servizio che ospita il sito (GitHub Pages) può registrare per motivi di sicurezza
dati tecnici come l'indirizzo IP del visitatore.</p>
<h2>Link di affiliazione</h2><p>Molti link portano a negozi online con cui abbiamo un accordo di affiliazione:
se acquisti dopo aver cliccato, riceviamo una commissione, senza costi aggiuntivi per te.
In qualità di Affiliato Amazon io ricevo un guadagno dagli acquisti idonei.
Quando apri un negozio, valgono la privacy e i cookie di quel negozio.</p>
<h2>Prezzi</h2><p>I prezzi sono quelli rilevati alla data e ora indicate accanto a ogni offerta e possono cambiare
in qualsiasi momento. Fa fede il prezzo mostrato dal negozio al momento dell'acquisto.</p>
<h2>I tuoi diritti</h2><p>Per qualsiasi richiesta sui tuoi dati scrivi a {mail}.</p>
<p class="imp">Gestore del sito: {name}, {addr}, {mail}</p></main>"""
    with open(os.path.join(country_dir(site, country), "privacy.html"), "w", encoding="utf-8") as f:
        f.write(_page("it", "Privacy – Offerte Crollate", body, path="privacy.html", base=base_url(country)))


# ---------------------------------------------------------------- file di contorno del dominio
def _redirect(to: str) -> str:
    return (f'<!DOCTYPE html><meta charset="utf-8"><title>Offerte Crollate</title><meta name="robots" content="noindex,follow">'
            f'<link rel="canonical" href="{to}"><meta http-equiv="refresh" content="0; url={to}">'
            f'<script>location.replace({json.dumps(to)}+location.hash)</script><a href="{to}">Offerte Crollate</a>')


def render_extras(site: dict, country: str) -> None:
    """Immagini, privacy, CNAME e i vecchi indirizzi (che rimandano alla pagina giusta)."""
    out = country_dir(site, country)
    os.makedirs(out, exist_ok=True)
    assets = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    if os.path.isdir(assets):
        shutil.copytree(assets, os.path.join(out, "assets"), dirs_exist_ok=True)
        if os.path.exists(os.path.join(assets, "favicon.ico")):   # icona nella scheda del browser
            shutil.copy(os.path.join(assets, "favicon.ico"), os.path.join(out, "favicon.ico"))
    render_privacy(site, country)
    with open(os.path.join(out, "CNAME"), "w") as f:
        f.write(DOMAINS[country] + "\n")
    open(os.path.join(out, ".nojekyll"), "w").close()
    # per Google: robots.txt e mappa delle pagine
    base = base_url(country)
    with open(os.path.join(out, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")
    with open(os.path.join(out, "404.html"), "w", encoding="utf-8") as f:   # offerte scadute e indirizzi sbagliati
        f.write('<!DOCTYPE html><meta charset="utf-8"><title>Offerte Crollate</title>'
                '<meta name="robots" content="noindex,follow"><meta http-equiv="refresh" content="0; url=/">'
                '<a href="/">Offerte Crollate</a>')
    if country == "ch":   # vecchi indirizzi del sito unico
        langs = site["countries"]["ch"]["langs"]
        old = {"ch/index.html": "/", "it/index.html": base_url("it") + "/", "it/it.html": base_url("it") + "/"}
        old.update({f"ch/{l}.html": ("/" if l == langs[0] else f"/{l}.html") for l in langs})
        for path, to in old.items():
            os.makedirs(os.path.join(out, os.path.dirname(path)), exist_ok=True)
            with open(os.path.join(out, path), "w", encoding="utf-8") as f:
                f.write(_redirect(to))
