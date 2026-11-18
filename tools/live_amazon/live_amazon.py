"""Offerte Crollate - ricerca Amazon per le dirette TikTok.

Avvialo sul PC da cui fai la live, prima di aprire offertecrollate.it/live.html.
Al primo avvio chiede la chiave Keepa e la salva solo su questo PC (file keepa_key.txt accanto al programma).
La pagina live lo chiama su http://localhost:8787 quando premi "Cerca".
Solo libreria standard di Python: nessuna installazione extra.
"""
import gzip
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTA = 8787
TAG = {"it": "offertecrolla-21"}
DOMINIO = {"it": (8, "www.amazon.it")}
CARTELLA = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
FILE_CHIAVE = os.path.join(CARTELLA, "keepa_key.txt")


def chiave() -> str:
    if os.path.exists(FILE_CHIAVE):
        k = open(FILE_CHIAVE, encoding="utf-8").read().strip()
        if k:
            return k
    print("Primo avvio: incolla la tua chiave Keepa e premi Invio (resta salvata solo su questo PC).")
    k = input("Chiave Keepa: ").strip()
    with open(FILE_CHIAVE, "w", encoding="utf-8") as f:
        f.write(k)
    return k


KEY = ""


def keepa(path: str, params: dict) -> dict:
    params = dict(params, key=KEY)
    url = f"https://api.keepa.com/{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
    return json.loads(data)


def _v(arr, i):
    try:
        x = arr[i]
        return x if isinstance(x, (int, float)) and x > 0 else None
    except (TypeError, IndexError):
        return None


def prodotto(p: dict, dom: str) -> dict:
    st = p.get("stats") or {}
    cur, avg = st.get("current") or [], st.get("avg90") or []
    prezzo = st.get("buyBoxPrice") if (st.get("buyBoxPrice") or 0) > 0 else None
    prezzo = prezzo or _v(cur, 18) or _v(cur, 0) or _v(cur, 1)
    media = _v(avg, 18) or _v(avg, 0) or _v(avg, 1)
    voto = _v(cur, 16)
    rec = _v(cur, 17)
    rank = _v(cur, 3)
    img = ""
    if p.get("imagesCSV"):
        img = "https://m.media-amazon.com/images/I/" + p["imagesCSV"].split(",")[0]
    elif p.get("images"):
        i0 = p["images"][0] or {}
        img = "https://m.media-amazon.com/images/I/" + (i0.get("l") or i0.get("m") or "")
    feats = [f.strip() for f in (p.get("features") or []) if f and f.strip()][:5]
    return {
        "asin": p.get("asin"), "nome": p.get("title") or "", "marca": p.get("brand") or "",
        "img": img, "prezzo": round(prezzo / 100, 2) if prezzo else None,
        "media90": round(media / 100, 2) if media else None,
        "voto": round(voto / 10, 1) if voto else None, "recensioni": rec, "rank": rank,
        "caratteristiche": feats,
        "url": f"https://{DOMINIO[dom][1]}/dp/{p.get('asin')}?tag={TAG[dom]}",
    }


def punteggio(x: dict) -> float:
    """Più alto = più consigliato: voto, recensioni, vendite, prezzo rispetto alla media."""
    s = 0.0
    if x["voto"]:
        s += (x["voto"] - 3.8) * 3
    s += math.log10((x["recensioni"] or 0) + 1) * 1.2
    if x["rank"]:
        s += max(0.0, 6 - math.log10(x["rank"])) * 0.6
    if x["prezzo"] and x["media90"] and x["media90"] > x["prezzo"]:
        s += min(30, (1 - x["prezzo"] / x["media90"]) * 100) / 10
    return round(s, 2)


def motivi(x: dict, tutti: list) -> list:
    m = []
    if x["voto"]:
        m.append(f"voto {str(x['voto']).replace('.', ',')} su 5")
    if x["recensioni"]:
        m.append(f"{x['recensioni']:,}".replace(",", ".") + " recensioni")
    ranks = sorted(t["rank"] for t in tutti if t["rank"])
    if x["rank"] and ranks and x["rank"] == ranks[0]:
        m.append("il più venduto di questi")
    if x["prezzo"] and x["media90"] and x["media90"] > x["prezzo"] * 1.05:
        m.append(f"oggi costa il {round((1 - x['prezzo'] / x['media90']) * 100)}% in meno della media degli ultimi 3 mesi")
    return m


def cerca(q: str, dom: str = "it") -> dict:
    r = keepa("search", {"domain": DOMINIO[dom][0], "type": "product", "term": q, "page": 0,
                         "stats": 90, "rating": 1})
    prodotti = [prodotto(p, dom) for p in (r.get("products") or [])]
    prodotti = [p for p in prodotti if p["prezzo"] and p["img"]]
    for p in prodotti:
        p["punteggio"] = punteggio(p)
    prodotti.sort(key=lambda p: -p["punteggio"])
    top = prodotti[:4]
    for p in top:
        p["motivi"] = motivi(p, top)
    print(f"  '{q}': {len(prodotti)} prodotti, gettoni Keepa rimasti {r.get('tokensLeft')}")
    return {"q": q, "prodotti": top, "gettoni": r.get("tokensLeft")}


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if u.path == "/stato":
            return self._json(200, {"ok": True})
        if u.path == "/cerca":
            q = (qs.get("q") or [""])[0].strip()
            if not q:
                return self._json(400, {"errore": "manca il prodotto"})
            try:
                return self._json(200, cerca(q))
            except urllib.error.HTTPError as e:
                msg = "gettoni Keepa finiti, riprova tra qualche minuto" if e.code == 429 else f"Keepa errore {e.code}"
                print("  " + msg)
                return self._json(502, {"errore": msg})
            except Exception as e:
                print("  errore:", e)
                return self._json(502, {"errore": str(e)})
        self._json(404, {"errore": "pagina non trovata"})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    KEY = chiave()
    print(f"Ricerca Amazon pronta su http://localhost:{PORTA}")
    print("Ora apri offertecrollate.it/live.html e premi Avvia. Lascia aperta questa finestra durante la live.")
    print("Per chiudere: chiudi questa finestra.\n")
    ThreadingHTTPServer(("127.0.0.1", PORTA), H).serve_forever()
