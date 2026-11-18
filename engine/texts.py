"""Testi dei post in italiano, tedesco e francese."""
from datetime import datetime
from .models import Deal
from .hooks import hook as _hook

T = {
    "it": {"ora": "Prezzo delle", "errore": "🚨 ERRORE DI PREZZO", "offerta": "🔥 OFFERTA",
           "invece_di": "invece di", "sconto": "sconto", "su": "su", "media90": "sul prezzo mediano degli ultimi 90 giorni",
           "nota": "Prezzo verificato al momento della pubblicazione, può cambiare in qualsiasi momento.",
           "aff": "Link affiliato: se acquisti riceviamo una piccola commissione, a te non costa nulla."},
    "de": {"ora": "Preis von", "errore": "🚨 PREISFEHLER", "offerta": "🔥 DEAL",
           "invece_di": "statt", "sconto": "Rabatt", "su": "bei", "media90": "gegenüber dem Medianpreis der letzten 90 Tage",
           "nota": "Preis zum Zeitpunkt der Veröffentlichung geprüft, kann sich jederzeit ändern.",
           "aff": "Affiliate-Link: Bei einem Kauf erhalten wir eine kleine Provision, für dich ohne Mehrkosten."},
    "fr": {"ora": "Prix à", "errore": "🚨 ERREUR DE PRIX", "offerta": "🔥 BON PLAN",
           "invece_di": "au lieu de", "sconto": "de réduction", "su": "chez", "media90": "par rapport au prix médian sur 90 jours",
           "nota": "Prix vérifié au moment de la publication, il peut changer à tout moment.",
           "aff": "Lien affilié : en cas d'achat nous touchons une petite commission, sans frais pour toi."},
}


def money(v: float, cur: str) -> str:
    if cur == "CHF":
        return f"CHF {v:,.2f}".replace(",", "'").replace(".00", ".–")
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


FLAGS = {"it": "🇮🇹", "ch": "🇨🇭"}


def flags_for(country: str, source: str = "") -> str:
    """Bandiera del paese dove si compra. Amazon.it spedisce anche in Svizzera: tutte e due."""
    if source == "amazon_it" and country == "ch":
        return "🇮🇹🇨🇭"
    return FLAGS.get(country, "")


FRETTA = {"it": "⚠️ Possibile errore di prezzo: affrettati, potrebbe sparire da un momento all'altro!",
          "de": "⚠️ Möglicher Preisfehler: Beeil dich, er kann jeden Moment verschwinden!",
          "fr": "⚠️ Possible erreur de prix : dépêche-toi, elle peut disparaître à tout moment !"}


def _stella(nome: str) -> str:
    """⭐ APPLE · davanti ai marchi famosi (18/11/2026)."""
    from .brands import brand_of
    b = brand_of(nome)
    return f"⭐ {b.upper()} · " if b else ""


def fretta(deal: Deal, lang: str) -> str:
    """Riga di avviso per gli sconti sopra l'80% (non su Amazon, dove non c'è il confronto)."""
    if deal.product.source.startswith("amazon") or round(deal.discount_pct or 0) <= 80:
        return ""
    return FRETTA.get(lang, FRETTA["it"])


def post_text(deal: Deal, lang: str, tag: str = "") -> str:
    """Le prime righe sono quelle che si vedono nell'anteprima (Facebook ne mostra poche):
    1) #ADV + sconto + nome  2) frase simpatica  3) prezzo  4) negozio. Niente righe vuote in mezzo."""
    from .hooks import hook
    t, p = T[lang], deal.product
    amz = p.source.startswith("amazon")   # Amazon: niente prezzo barrato del venditore
    # Amazon: prezzo e prezzo barrato come li mostra Amazon (scelta di Giuseppe del 15/11/2026)
    keepa = amz and bool(deal.reference_price) and deal.reference_price > p.price
    head = f"{t[deal.level]}" if amz else f"{t[deal.level]} -{deal.discount_pct:.0f}%"
    # obbligo di legge (AGCOM/AGCM): dicitura pubblicitaria chiara e visibile SUBITO, in apertura
    fl = deal.extra.get("flags", "")
    if fl:
        head = f"{fl} {head}"
    if tag:
        head = f"{tag} · {head}"
    if keepa:
        cala = deal.reference_price - p.price
        # prezzo barrato = quello mostrato da Amazon (prezzo tipico/di listino), non medie Keepa
        price = (f"💰 {money(p.price, p.currency)} {t['invece_di']} {money(deal.reference_price, p.currency)}\n"
                 f"📉 -{deal.discount_pct:.0f}% (-{money(cala, p.currency)})")
    else:
      price = (f"💰 {money(p.price, p.currency)}" if amz else
               f"💰 {money(p.price, p.currency)} {t['invece_di']} {money(deal.reference_price, p.currency)}")
    frase = deal.extra.get("hook") or hook(p.name, p.key, lang)
    # prima riga: #ADV + bandiera + frase simpatica; seconda: tipo, sconto e prodotto
    off = f"{t[deal.level]}" if (amz and not keepa) else f"{t[deal.level]} -{deal.discount_pct:.0f}%"
    if frase:
        apertura = " ".join(x for x in (tag, deal.extra.get("flags", ""), frase) if x)
        righe = [apertura, f"{_stella(p.name)}{off} | {p.name}"]
    else:
        righe = [f"{_stella(p.name)}{head} | {p.name}"]
    if fretta(deal, lang):
        righe.append(fretta(deal, lang))
    righe += [price, f"🏬 {t['su']} {p.shop}"]
    return "\n".join(righe) + f"\n\n👉 {p.url}"


def fb_text(deal: Deal, lang: str, tag: str = "") -> str:
    """Testo per Facebook: corto e senza righe vuote in alto, così nell'anteprima si leggono
    subito prodotto, frase, prezzo e negozio. Il link va nel primo commento. Niente orario."""
    t, p = T[lang], deal.product
    h = deal.extra.get("hook") or _hook(p.name, p.key, lang)
    fl = deal.extra.get("flags", "")
    pre = (f"{tag} " if tag else "") + (f"{fl} " if fl else "")
    if deal.level == "errore":
        first = f"{pre}{t['errore']}: {p.name} a -{deal.discount_pct:.0f}%!"
    else:
        first = f"{pre}{_stella(p.name) or '🔥 '}{p.name} a -{deal.discount_pct:.0f}%!"
    if h:      # frase simpatica subito accanto a #ADV e bandiera, poi prodotto e sconto
        lines = [f"{pre}{h}", first[len(pre):]]
    else:
        lines = [first]
    if fretta(deal, lang):
        lines.append(fretta(deal, lang))
    lines.append(f"💰 {money(p.price, p.currency)} {t['invece_di']} {money(deal.reference_price, p.currency)}")
    lines.append(f"🏬 {p.shop} · " + {"it": "link nel primo commento 👇", "de": "Link im ersten Kommentar 👇",
                                      "fr": "lien dans le premier commentaire 👇"}[lang])
    return "\n".join(lines)
