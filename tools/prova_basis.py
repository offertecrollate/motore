"""Diagnosi: prezzi Amazon pubblicati sbagliati? Confronta i dati Keepa normali con quelli aggiornati adesso."""
import datetime as dt, os, requests
key = os.environ["KEEPA_KEY"].strip()
asins = "B0DT1KFV52,B0FH123LLC,B0B6B2JDCF,B0FFLXCMJ8,B0FV8MW74F,B09492RD6C,B0DJC9ZXCG,B0FBGR4LRT,B0CZS9JJT6,1472277546"
def t(m):
    return (dt.datetime(2011, 1, 1) + dt.timedelta(minutes=m)).strftime("%d/%m %H:%M") if m and m > 0 else "-"
for extra in ({}, {"update": 0}):
    r = requests.get("https://api.keepa.com/product", timeout=120,
                     params=dict(key=key, domain=8, asin=asins, history=0, stats=1, buybox=1, **extra))
    j = r.json()
    print("PARAMS", extra, "gettoni usati", j.get("tokensConsumed"), "rimasti", j.get("tokensLeft"), j.get("error"))
    for p in j.get("products") or []:
        s = p.get("stats") or {}
        cur = s.get("current") or []
        g = lambda i: cur[i] if i < len(cur) else None
        print(" ", p.get("asin"), "agg", t(p.get("lastUpdate")), "camb", t(p.get("lastPriceChange")),
              "bb", s.get("buyBoxPrice"), "basis", s.get("buyBoxSavingBasis"), s.get("buyBoxSavingBasisType"),
              "amz", g(0), "nuovo", g(1), "bbcur", g(18), "list", g(4),
              "venditore", s.get("buyBoxSellerId"), "amazon?", s.get("buyBoxIsAmazon"),
              "fba?", s.get("buyBoxIsFBA"), "padre", p.get("parentAsin"), "tipo", p.get("productType"))
