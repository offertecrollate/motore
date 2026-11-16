"""
Avvio del motore.

    python -m engine.run --config config.yaml --country ch
    python -m engine.run --config config.yaml --country it --dry-run

Da lanciare una o più volte al giorno con cron sul server.
"""
import argparse
import logging
import sys
from datetime import date

import yaml

from .db import PriceDB
from .detector import find_deals
from .publishers import build_publisher
from .site import update_site
from .sources import build_source

log = logging.getLogger("errori-prezzo")


def close_ended(db, products, country, publishers, cfg, c, tolerance=0.03):
    """Ricontrolla i post degli ultimi giorni. Un'offerta è terminata se il prezzo di oggi è salito
    oltre il prezzo pubblicato (+3%) oppure se il prodotto non è più nel catalogo di una fonte
    che oggi ha risposto. Telegram: testo barrato. Facebook: TERMINATA + commento nascosto. Sito: tolta."""
    now = {p.key: p.price for p in products}
    shops_ok = {p.shop for p in products}          # negozi che oggi hanno risposto
    by_label = {p.label: p for p in publishers}
    ended = set()
    for m in db.open_messages(country, days=c["rules"].get("watch_days", 14)):
        price = now.get(m["key"])
        row = db.conn.execute("SELECT shop FROM products WHERE key=?", (m["key"],)).fetchone()
        gone = price is None and row is not None and row[0] in shops_ok
        up = price is not None and price > m["price"] * (1 + tolerance)
        if not (gone or up):
            continue
        pub = by_label.get(m["channel"])
        try:
            if pub:
                pub.end(m, pub.lang)
            db.end_message(m["id"])
            ended.add(m["key"])
        except Exception as e:
            log.error("Chiusura su %s fallita: %s", m["channel"], e)
    if ended and cfg.get("site"):
        from .site import remove_from_site
        remove_from_site(ended, country, cfg["site"])
    if ended:
        log.info("%s: %d offerte terminate", country, len(ended))
    return ended


def run_country(cfg: dict, country: str, dry_run: bool = False, today: date = None) -> list:
    c = cfg["countries"][country]
    db = PriceDB(cfg.get("database", "prezzi.db"))

    # 1. raccolta prezzi da tutte le fonti del paese
    products = []
    for s in c["sources"]:
        try:
            got = build_source(s).fetch()
            log.info("%s: %d prodotti", s["name"], len(got))
            products += got
        except Exception as e:  # una fonte rotta non blocca le altre
            log.error("Fonte %s non letta: %s", s["name"], e)

    # 1a. offerte già pubblicate: se il prezzo è tornato su o il prodotto non c'è più, le chiudo
    publishers_all = [build_publisher(p) for p in c["publishers"]]
    if not dry_run:
        close_ended(db, products, country, publishers_all, cfg, c)

    # 1b. (opzionale, spento di default) storico Amazon da Keepa per i prodotti nuovi
    if cfg.get("keepa", {}).get("api_key"):
        from .keepa_backfill import backfill
        backfill(db, products, cfg["keepa"]["api_key"], c["rules"]["min_history"],
                 cfg["keepa"].get("max_per_run", 50))

    # 1c. Amazon: prezzo e prezzo barrato sono quelli che Amazon mostra (vedi sources/keepa.py),
    #     Keepa serve solo per il grafico. Nessuna media o mediana calcolata da noi.

    # 2. ricerca ribassi (prima di salvare il prezzo di oggi nello storico)
    # fonti di cui ci fidiamo del "prezzo prima" anche senza nostro storico (es. Keepa: media a 90 giorni)
    rules = dict(c["rules"], trust_sources={s["name"] for s in c["sources"] if s.get("trust_old_price")})
    deals = find_deals(db, products, rules, today=today)
    db.save(products, day=today)
    db.prune(cfg.get("keep_days", 100))

    # negozi che non ci hanno ancora accettato: si salva lo storico ma non si pubblica
    solo_storico = {s["name"] for s in c["sources"] if s.get("publish", True) is False}
    if solo_storico:
        deals = [d for d in deals if d.product.source not in solo_storico]

    # negozi senza affiliazione ma con prezzo "prima" dichiarato: solo sul sito (non sui canali)
    site_deals = _site_only_deals(c, products)
    # negozi per adulti (es. Sedusia): categoria "Adulti 18+" sul sito, solo Telegram, mai Facebook
    adult = {s["name"] for s in c["sources"] if s.get("adult")}
    for d in deals + site_deals:
        if d.product.source in adult:
            d.extra["adult"] = True
            d.extra["hook"] = ADULT_HOOK
    site_only = {s["name"] for s in c["sources"] if s.get("site_only")}
    if site_only:
        deals = [d for d in deals if d.product.source not in site_only]

    # negozi "solo sito" che ci hanno approvato (link affiliato Awin): anche su Telegram e Facebook
    affiliati = {s["name"] for s in c["sources"] if (s.get("site_only") and s.get("awin_mid")) or s.get("affiliate")}
    deals = deals + [d for d in site_deals if d.product.source in affiliati]
    deals.sort(key=lambda d: -d.discount_pct)     # le più forti prima (decisione 15/11/2026)

    # 3. filtro: niente doppioni (né in questo paese né nell'altro: canale e pagina sono unici),
    #    né due prodotti con lo stesso nome nello stesso giro; solo i migliori N per giro
    #    15-20 per sito a ogni giro, divise tra i negozi a turno (decisione di Giuseppe del 15/11/2026):
    #    a ogni turno la più forte di ciascun negozio, partendo dal negozio con lo sconto più alto
    nuove, nomi = [], set()
    for d in deals:
        nome = (d.product.name or "").strip().lower()
        if nome in nomi:
            continue
        if any(db.already_posted(d.product.key, paese, d.product.price, c["rules"].get("repost_after_days", 7))
               for paese in ("it", "ch")):
            continue
        nomi.add(nome)
        nuove.append(d)
    # Telegram e Facebook: solo le offerte più forti di tutti i negozi affiliati (decisione di Giuseppe 16/11/2026)
    nuove.sort(key=lambda d: (d.level != "errore", -d.discount_pct))
    fresh = nuove[: c["rules"].get("max_posts_per_run", 5)]
    fresh.sort(key=lambda d: -d.discount_pct)
    log.info("%s: %d ribassi trovati, %d da pubblicare", country, len(deals), len(fresh))

    # 4. pubblicazione
    publishers = [build_publisher(p) for p in c["publishers"]]
    is_fb = [str(p.get("type", "")).startswith("facebook") for p in c["publishers"]]
    if dry_run:
        publishers = [build_publisher({"type": "console", "lang": p.lang, "label": p.label})
                      for p in publishers]
    from .texts import flags_for
    amz = [d.product for d in fresh if d.product.source.startswith("amazon")]
    if amz and not dry_run and cfg.get("keepa", {}).get("api_key") and not str(cfg["keepa"]["api_key"]).startswith("$"):
        try:                                   # stelle Amazon nell'immagine del post (da 4 in su)
            from .keepa_backfill import ratings
            stars = ratings(amz, cfg["keepa"]["api_key"])
            for d in fresh:            # solo le stelle: prezzi e prezzo barrato restano quelli mostrati da Amazon
                info = stars.get(d.product.product_id)
                if info:
                    d.extra["rating"], d.extra["reviews"] = info[0], info[1]
        except Exception as e:
            log.warning("Stelle Amazon non lette: %s", e)
    for i, d in enumerate(fresh):
        if i and not dry_run:      # pausa tra un'offerta e l'altra: Telegram e Facebook non le vedono come spam
            import time
            time.sleep(int(c["rules"].get("pause_between_posts", 12)))
        d.extra["flags"] = flags_for(country, d.product.source)
        ad = d.extra.get("adult")
        if ad:
            d.extra["flags"] = ("🔞 " + d.extra["flags"]).strip()
        if cfg.get("cards", True) and not dry_run:   # immagine promozionale (non per Amazon, vedi cards.py)
            try:
                from .cards import make_card
                if ad:   # adulti: niente foto del negozio, al suo posto il riquadro neutro "18+"
                    from .card_crollata import neutral_adult_img
                    d.extra["card"] = make_card(d, c.get("card_lang", "it"), product_img=neutral_adult_img())
                else:
                    d.extra["card"] = make_card(d, c.get("card_lang", "it"))
            except Exception as e:
                log.warning("Immagine non creata per %s: %s", d.product.name, e)
        for pub, fb in zip(publishers, is_fb):
            if ad and fb:      # mai su Facebook
                continue
            try:
                ref = pub.send(d)
                if ref and ref[0] == "post":          # post sulla pagina Facebook: serve per condividerlo nel gruppo
                    d.extra["fb_post"] = ref[1]
                if ref and not dry_run:
                    db.save_message(d.product.key, country, pub.label, ref[0], ref[1],
                                    pub.last_text, d.product.price, ref[2])
            except Exception as e:
                log.error("Pubblicazione su %s fallita: %s", pub.label, e)
        if not dry_run:
            db.mark_posted(d.product.key, country, d.product.price)
            if not ad:   # l'avviso serve per condividere su Facebook: per gli adulti no
                _avviso_privato(cfg, d, country)

    if dry_run:
        _report(country, products, fresh, db)

    # 5. sito (ogni offerta porta con sé lo storico prezzi per il grafico). Il sito si aggiorna anche
    #    in prova: non manda nulla sui canali, mostra solo le offerte.
    #    sul sito vanno TUTTE le offerte valide (anche quelle non pubblicate sui canali in questo giro)
    site_list, visti = [], set()
    minimo_sito = float(c["rules"].get("site_min_pct", 30))   # sul sito tutte le offerte dal 30% in su
    for d in fresh + deals + site_deals:
        if d.discount_pct < minimo_sito:
            continue
        if d.product.key not in visti:
            visti.add(d.product.key)
            site_list.append(d)
    for d in site_list:
        d.extra["history"] = db.series(d.product.key, days=cfg.get("site", {}).get("chart_days", 90))
    if (site_list or site_only or site_deals) and cfg.get("site") and (not dry_run or cfg["site"].get("update_in_test", True)):
        letti = {p.source for p in products}          # se un negozio non risponde, le sue offerte restano
        da_rifare = {s["name"] for s in c["sources"] if s.get("site_only") or s.get("site_old_price")}
        update_site(site_list, country, cfg["site"], replace_sources=da_rifare & letti)
    return fresh


ADULT_HOOK = "Offerta riservata ai maggiorenni 🔞"


def _site_only_deals(c: dict, products: list) -> list:
    """Offerte dai negozi "solo sito": sconto dichiarato dal negozio (prezzo prima > prezzo oggi)."""
    from .models import Deal
    rules = {s["name"]: s for s in c["sources"] if s.get("site_only") or s.get("site_old_price")}
    out = []
    for p in products:
        s = rules.get(p.source)
        if not s or not p.old_price or p.old_price <= p.price:
            continue
        pct = (1 - p.price / p.old_price) * 100
        if pct < s.get("min_discount", 20) or pct > 95:      # oltre il 95% di solito è un dato sbagliato
            continue
        out.append(Deal(p, p.old_price, round(pct, 1), "offerta", 0, extra={}))
    out.sort(key=lambda d: -d.discount_pct)
    per, keep = {}, []                    # tetto per negozio (max_site), così uno solo non riempie tutto
    for d in out:
        cap = rules[d.product.source].get("max_site")
        per[d.product.source] = per.get(d.product.source, 0) + 1
        if not cap or per[d.product.source] <= cap:
            keep.append(d)
    return keep[: c.get("rules", {}).get("max_site_only", 150)]


def _avviso_privato(cfg, d, country):
    """Super offerta (sconto >= soglia o errore di prezzo): il bot la manda in privato a Giuseppe,
    con immagine e testo pronti da inoltrare nel gruppo Facebook."""
    a = cfg.get("avvisi_privati") or {}
    # solo i possibili errori di prezzo: sconto arrotondato >= soglia (80%), scelta di Giuseppe
    if not a.get("chat_id") or round(d.discount_pct or 0) < a.get("soglia", 80):
        return
    import requests
    from .texts import fb_text
    tok = a.get("bot_token")
    if not tok:
        return
    import html as _h
    fb = d.extra.get("fb_post")
    # formato provato da Giuseppe: si apre anche nell'app Facebook dal link di Telegram
    link = (f"https://www.facebook.com/permalink.php?story_fbid={fb.split('_')[-1]}&id={fb.split('_')[0]}"
            if fb and "_" in fb else d.extra.get("fb_link", ""))
    sito = "https://offertecrollate.it" if country == "it" else "https://offertecrollate.ch"
    commento = f"👉 Link all'offerta: {d.product.url}"
    if fb:
        testo = ("⭐ <b>SUPER OFFERTA da mettere nel gruppo</b>\n\n"
                 "1️⃣ Tocca il testo grigio qui sotto: si copia da solo\n"
                 f"<code>{_h.escape(commento)}</code>\n\n"
                 f"2️⃣ Apri il post: {_h.escape(link)}\n\n"
                 "3️⃣ Sotto l'immagine tocca la freccia ↪ → Condividi in un gruppo → "
                 "Community Offerte Crollate → incolla nel testo → Pubblica\n\n"
                 "— Testo del post —\n" + _h.escape(fb_text(d, "it", "#ADV")) + f"\n\n🌐 {sito}")
    else:
        testo = ("⭐ <b>SUPER OFFERTA da mettere nel gruppo</b>\n\n" + _h.escape(fb_text(d, "it", "#ADV"))
                 + f"\n\n<code>{_h.escape(commento)}</code>\n🌐 {sito}")
    try:
        card = d.extra.get("card")
        if card and len(testo) <= 1024:
            requests.post(f"https://api.telegram.org/bot{tok}/sendPhoto", timeout=60,
                          data={"chat_id": a["chat_id"], "caption": testo, "parse_mode": "HTML"},
                          files={"photo": ("offerta.jpg", card, "image/jpeg")})
        else:
            if card:   # testo troppo lungo per una didascalia: prima la foto, poi il testo
                requests.post(f"https://api.telegram.org/bot{tok}/sendPhoto", timeout=60,
                              data={"chat_id": a["chat_id"]},
                              files={"photo": ("offerta.jpg", card, "image/jpeg")})
            requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", timeout=30,
                          data={"chat_id": a["chat_id"], "text": testo, "parse_mode": "HTML"})
    except Exception as e:
        log.warning("Avviso privato non inviato: %s", e)


def _report(country, products, fresh, db):
    """In prova: riepilogo leggibile nella pagina di GitHub Actions (nessuna pubblicazione)."""
    import os
    from collections import Counter
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    per_fonte = Counter(p.source for p in products)
    righe = [f"## {country.upper()} (prova, niente pubblicato)", "",
             "| Fonte | Prodotti letti | Giorni di storico (max) |", "|---|---|---|"]
    for src, n in sorted(per_fonte.items()):
        giorni = db.conn.execute(
            "SELECT MAX(c) FROM (SELECT COUNT(*) c FROM prices WHERE key LIKE ? GROUP BY key)",
            (src + ":%",)).fetchone()[0] or 0
        righe.append(f"| {src} | {n} | {giorni} |")
    righe += ["", f"**Post che sarebbero usciti: {len(fresh)}**", ""]
    for d in fresh:
        p = d.product
        righe.append(f"- {d.level.upper()} -{d.discount_pct:.0f}% · {p.name[:80]} · "
                     f"{p.price:.2f} {p.currency} (di solito {d.reference_price:.2f}) · {p.shop}")
    txt = "\n".join(righe) + "\n"
    print(txt)
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(txt)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--country", required=True, help="es. ch o it")
    ap.add_argument("--dry-run", action="store_true", help="stampa i post invece di pubblicarli")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with open(a.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    run_country(cfg, a.country, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
