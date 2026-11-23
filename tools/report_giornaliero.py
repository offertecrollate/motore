"""Ogni sera: clic, vendite e commissioni Awin del giorno, in privato a Giuseppe sul bot Telegram.
Segreti: AWIN_API_TOKEN (token API di Awin), TELEGRAM_TOKEN, ALERT_CHAT_ID.
Testo extra opzionale (es. vendite Amazon) dalla variabile EXTRA."""
import datetime as dt, os, requests

PUB = 3152592
tok = os.environ.get("AWIN_API_TOKEN", "").strip()
oggi = dt.date.today()
inizio_mese = oggi.replace(day=1)


def awin(da, a):
    righe = []
    for reg in ("IT", "CH"):
        for tentativo in range(4):   # 24/11/2026: l'API Awin a volte non risponde, riprova fino a 4 volte
            try:
                r = requests.get(f"https://api.awin.com/publishers/{PUB}/reports/advertiser", timeout=150,
                                 headers={"Authorization": f"Bearer {tok}"},
                                 params={"startDate": da.isoformat(), "endDate": a.isoformat(), "region": reg, "timezone": "UTC"})
                r.raise_for_status()
                break
            except requests.RequestException:
                if tentativo == 3:
                    raise
                import time
                time.sleep(30 * (tentativo + 1))
        righe += r.json()
    return righe


def blocco(titolo, righe):
    clic = sum(x.get("clicks", 0) for x in righe)
    vend = sum(x.get("totalNo", 0) for x in righe)
    comm = {}
    for x in righe:
        comm[x.get("currency", "EUR")] = comm.get(x.get("currency", "EUR"), 0) + x.get("totalComm", 0)
    soldi = " + ".join(f"{v:.2f} {k}" for k, v in comm.items() if v) or "0"
    out = [f"<b>{titolo}</b>: {clic} clic, {vend} vendite, commissioni {soldi}"]
    for x in sorted(righe, key=lambda x: -x.get("clicks", 0)):
        if x.get("clicks") or x.get("totalNo"):
            v = f", {x['totalNo']} vendite ({x['totalComm']:.2f} {x['currency']})" if x.get("totalNo") else ""
            out.append(f"• {x['advertiserName']}: {x['clicks']} clic{v}")
    return "\n".join(out)


testo = [f"📊 <b>Resoconto Offerte Crollate – {oggi.strftime('%d/%m/%Y')}</b>", ""]
if tok:
    try:
        testo += [blocco("Awin oggi", awin(oggi, oggi)), "", blocco("Awin dal 1° del mese", awin(inizio_mese, oggi))]
    except Exception as e:
        testo.append(f"Awin: dati non letti ({e})")
else:
    testo.append("Awin: manca il segreto AWIN_API_TOKEN")
extra = os.environ.get("EXTRA", "").strip()
if extra:
    testo += ["", extra]
r = requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN'].strip()}/sendMessage", timeout=30,
                  data={"chat_id": os.environ["ALERT_CHAT_ID"].strip(), "text": "\n".join(testo), "parse_mode": "HTML",
                        "disable_web_page_preview": "true"})
print(r.status_code, r.text[:200])
r.raise_for_status()
