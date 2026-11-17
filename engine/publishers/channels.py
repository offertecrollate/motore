"""
Canali di pubblicazione.

- telegram:      API ufficiale dei bot Telegram (gratis).
- whatsapp_waha: canale WhatsApp tramite WAHA, installato sul tuo server.
                 Strumento NON ufficiale: usa un numero dedicato, non il tuo personale.
- facebook_page: API ufficiale Meta (Graph API) per pubblicare sulla pagina.
- console:       stampa a schermo, per le prove.
"""
import json
import requests

from ..models import Deal
from ..texts import post_text, fb_text


def _img(card: bytes):
    """Nome e tipo del file immagine (PNG o JPEG) per l'invio."""
    return ("offerta.png", card, "image/png") if card[:4] == b"\x89PNG" else ("offerta.jpg", card, "image/jpeg")


class _Base:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.lang = cfg.get("lang", "it")
        self.label = cfg.get("label", cfg["type"])

    last_text = ""

    def send(self, deal: Deal):
        """Pubblica e restituisce (kind, ref, extra) per poter poi chiudere il post, oppure None."""
        raise NotImplementedError

    def end(self, msg: dict, lang: str = "it") -> None:
        """Segna come terminato un post già pubblicato (se il canale lo permette)."""
        return None


class ConsolePublisher(_Base):
    def send(self, deal: Deal) -> None:
        print(f"\n----- [{self.label} / {self.lang}] -----\n{post_text(deal, self.lang, self.cfg.get('post_tag', ''))}")


class TelegramPublisher(_Base):
    def send(self, deal: Deal) -> None:
        api = f"https://api.telegram.org/bot{self.cfg['bot_token']}"
        text = post_text(deal, self.lang, self.cfg.get('post_tag', ''))
        if self.cfg.get("site_url"):   # riga fissa che porta a tutte le offerte sul sito
            text += f"\n\n🌐 Tutte le offerte: {self.cfg['site_url']}"
        # link nascosto dietro "Vai all'offerta" (niente indirizzi lunghissimi, decisione di Giuseppe 16/11/2026)
        import html as _h
        plain = text
        url = deal.product.url
        lbl = {"it": "VAI ALL'OFFERTA", "de": "ZUM ANGEBOT", "fr": "VOIR L'OFFRE"}.get(self.lang, "VAI ALL'OFFERTA")
        text = _h.escape(plain).replace(_h.escape(f"👉 {url}"), f'👉 <a href="{_h.escape(url)}"><b>{lbl}</b></a>')
        card = deal.extra.get("card")
        if card:
            r = requests.post(f"{api}/sendPhoto", timeout=60, data={
                "chat_id": self.cfg["chat_id"], "caption": text[:1024], "parse_mode": "HTML"},
                files={"photo": _img(card)})
        elif deal.product.image and not deal.extra.get("adult"):   # adulti: mai la foto del negozio
            r = requests.post(f"{api}/sendPhoto", timeout=30, data={
                "chat_id": self.cfg["chat_id"], "photo": deal.product.image,
                "caption": text[:1024], "parse_mode": "HTML"})
        else:
            # senza foto (es. Amazon): anteprima grande del link SOPRA il testo, così l'immagine si vede subito
            r = requests.post(f"{api}/sendMessage", timeout=30, data={
                "chat_id": self.cfg["chat_id"], "text": text, "parse_mode": "HTML",
                "link_preview_options": json.dumps({"url": deal.product.url, "prefer_large_media": True,
                                                    "show_above_text": True})})
        r.raise_for_status()
        res = r.json().get("result", {})
        self.last_text = plain
        return ("photo" if res.get("photo") else "text", res.get("message_id"), "")

    def end(self, msg: dict, lang: str = "it") -> None:
        import html as _h
        api = f"https://api.telegram.org/bot{self.cfg['bot_token']}"
        head = {"it": "❌ OFFERTA TERMINATA", "de": "❌ ANGEBOT BEENDET", "fr": "❌ OFFRE TERMINÉE"}.get(lang)
        import re as _re
        testo = _re.sub(r"\n*👉 https?://\S+", "", msg["text"])
        body = f"<b>{head}</b>\n\n<s>{_h.escape(testo)}</s>"
        method, field = ("editMessageCaption", "caption") if msg["kind"] == "photo" else ("editMessageText", "text")
        r = requests.post(f"{api}/{method}", timeout=30, data={
            "chat_id": self.cfg["chat_id"], "message_id": msg["ref"], field: body[:1024 if field == "caption" else 4096],
            "parse_mode": "HTML", "disable_web_page_preview": "true"})
        if r.status_code >= 400 and "not modified" not in r.text:
            raise RuntimeError(f"Telegram {r.status_code}: {r.text[:200]}")


class WhatsAppWahaPublisher(_Base):
    """cfg: base_url (es. http://localhost:3000), session, channel_id (…@newsletter), api_key"""
    def send(self, deal: Deal) -> None:
        headers = {"X-Api-Key": self.cfg.get("api_key", "")}
        text = post_text(deal, self.lang, self.cfg.get('post_tag', ''))
        base = self.cfg["base_url"].rstrip("/")
        if deal.product.image:
            body = {"session": self.cfg.get("session", "default"), "chatId": self.cfg["channel_id"],
                    "file": {"url": deal.product.image}, "caption": text}
            r = requests.post(f"{base}/api/sendImage", json=body, headers=headers, timeout=60)
        else:
            body = {"session": self.cfg.get("session", "default"),
                    "chatId": self.cfg["channel_id"], "text": text}
            r = requests.post(f"{base}/api/sendText", json=body, headers=headers, timeout=60)
        r.raise_for_status()


def _grassetto(riga: str) -> str:
    """Lettere in grassetto Unicode (Facebook non ha il grassetto). Hashtag e link restano normali."""
    def b(ch):
        o = ord(ch)
        if 65 <= o <= 90: return chr(0x1D5D4 + o - 65)
        if 97 <= o <= 122: return chr(0x1D5EE + o - 97)
        if 48 <= o <= 57: return chr(0x1D7EC + o - 48)
        return ch
    return " ".join(w if w.startswith(("#", "http")) else "".join(b(c) for c in w) for w in riga.split(" "))


class FacebookPagePublisher(_Base):
    """Pagina Facebook tramite Graph API ufficiale.
    cfg: page_id, page_token (token della pagina, senza scadenza), api_version (facoltativo).
    Con immagine pubblica una foto con il testo (si vede meglio nel feed),
    altrimenti un post con anteprima del link."""
    _resolved = {}

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        tok = str(cfg.get("page_token") or "")
        # Se nel segreto c'è il token "utente" a lunga durata, da qui si ricava il token della pagina
        # (più semplice da rinnovare: basta rimettere il token utente su GitHub).
        if tok and not tok.startswith("$") and cfg.get("page_id"):
            if tok not in FacebookPagePublisher._resolved:
                try:
                    r = requests.get(f"https://graph.facebook.com/{cfg.get('api_version', 'v27.0')}/{cfg['page_id']}",
                                     params={"fields": "access_token", "access_token": tok}, timeout=20)
                    FacebookPagePublisher._resolved[tok] = (r.json().get("access_token") if r.ok else None) or tok
                except Exception:
                    FacebookPagePublisher._resolved[tok] = tok
            self.cfg = dict(cfg, page_token=FacebookPagePublisher._resolved[tok])

    def send(self, deal: Deal) -> None:
        base = f"https://graph.facebook.com/{self.cfg.get('api_version', 'v27.0')}/{self.cfg['page_id']}"
        text = fb_text(deal, self.lang, self.cfg.get('post_tag', ''))
        righe = text.split("\n")            # prime 2 righe in grassetto (quelle visibili nell'anteprima)
        text = "\n".join([_grassetto(r) for r in righe[:2]] + righe[2:])
        if not self.cfg.get("link_comment", True):     # senza commento il link va nel testo
            text += f"\n\n👉 {deal.product.url}"
        if self.cfg.get("site_url"):   # riga fissa che porta a tutte le offerte del paese
            text += f"\n\n🌐 Tutte le offerte: {self.cfg['site_url']}"
        card = deal.extra.get("card")
        if card:
            r = requests.post(f"{base}/photos", timeout=60, data={
                "caption": text, "access_token": self.cfg["page_token"]},
                files={"source": _img(card)})
        elif deal.product.image:
            r = requests.post(f"{base}/photos", timeout=60, data={
                "url": deal.product.image, "caption": text,
                "access_token": self.cfg["page_token"]})
        else:
            r = requests.post(f"{base}/feed", timeout=60, data={
                "message": text, "link": deal.product.url,
                "access_token": self.cfg["page_token"]})
        if r.status_code >= 400:
            raise RuntimeError(f"Facebook {r.status_code}: {r.text[:300]}")
        post_id = r.json().get("post_id") or r.json().get("id")
        self.last_text = text
        comment_id = ""
        # primo commento con il link del negozio (cliccabile anche dove il testo viene accorciato)
        if self.cfg.get("link_comment", True):
            c = requests.post(f"https://graph.facebook.com/{self.cfg.get('api_version', 'v27.0')}/{post_id}/comments",
                              timeout=30, data={"message": f"👉 Link all'offerta: {deal.product.url}",
                                                "access_token": self.cfg["page_token"]})
            if c.status_code >= 400:   # il post è uscito: un commento mancato non è un errore grave
                print(f"Commento con il link non pubblicato: {c.text[:200]}")
            else:
                comment_id = c.json().get("id", "")
        # link "ufficiale" del post (formato pfbid): si apre anche nell'app di Facebook
        try:
            pl = requests.get(f"https://graph.facebook.com/{self.cfg.get('api_version', 'v27.0')}/{post_id}",
                              timeout=20, params={"fields": "permalink_url",
                                                  "access_token": self.cfg["page_token"]})
            if pl.ok and pl.json().get("permalink_url"):
                deal.extra["fb_link"] = pl.json()["permalink_url"]
        except Exception:
            pass
        return ("post", post_id, comment_id)

    def end(self, msg: dict, lang: str = "it") -> None:
        """Facebook non permette di chiudere i commenti via API: cambio il testo in TERMINATA,
        nascondo il commento con il link e tolgo il link dal testo."""
        v = self.cfg.get("api_version", "v27.0")
        tok = self.cfg["page_token"]
        head = {"it": "❌ OFFERTA TERMINATA", "de": "❌ ANGEBOT BEENDET", "fr": "❌ OFFRE TERMINÉE"}.get(lang)
        import re as _re
        old = _re.sub(r"https?://\S+", "", msg["text"]).replace("👉", "").strip()
        r = requests.post(f"https://graph.facebook.com/{v}/{msg['ref']}", timeout=30,
                          data={"message": f"{head}\n\nPrezzo tornato normale o prodotto esaurito.\n\n{old}",
                                "access_token": tok})
        if r.status_code >= 400:
            raise RuntimeError(f"Facebook {r.status_code}: {r.text[:200]}")
        if msg.get("extra"):
            requests.post(f"https://graph.facebook.com/{v}/{msg['extra']}", timeout=30,
                          data={"is_hidden": "true", "access_token": tok})
