from datetime import date, timedelta

from engine.db import PriceDB
from engine.detector import find_deals
from engine.models import Product

RULES = {"history_days": 30, "min_history": 7, "offer_pct": 30, "error_pct": 60,
         "min_price": 20, "trust_old_price": False}


def prod(price, pid="1", old=None):
    return Product("test", pid, "Prodotto", price, "CHF", "Shop", "https://x", old_price=old)


def db_with_history(price, days=10, pid="1"):
    db = PriceDB(":memory:")
    for i in range(days):
        db.save([prod(price, pid)], day=date.today() - timedelta(days=days - i))
    return db


def test_errore():
    d = find_deals(db_with_history(100), [prod(30)], RULES)
    assert d and d[0].level == "errore" and d[0].discount_pct == 70


def test_offerta():
    d = find_deals(db_with_history(100), [prod(65)], RULES)
    assert d and d[0].level == "offerta"


def test_niente_se_ribasso_piccolo():
    assert find_deals(db_with_history(100), [prod(85)], RULES) == []


def test_storico_insufficiente():
    assert find_deals(db_with_history(100, days=3), [prod(10)], RULES) == []


def test_prodotti_economici_ignorati():
    assert find_deals(db_with_history(10), [prod(1)], RULES) == []


def test_prezzo_barrato_solo_se_attivo():
    db = PriceDB(":memory:")
    assert find_deals(db, [prod(30, old=100)], RULES) == []
    d = find_deals(db, [prod(30, old=100)], {**RULES, "trust_old_price": True})
    assert d and d[0].level == "errore"


def test_niente_doppioni():
    db = PriceDB(":memory:")
    db.mark_posted("test:1", "ch", 30)
    assert db.already_posted("test:1", "ch", 30, 7)
    assert not db.already_posted("test:1", "ch", 25, 7)   # prezzo sceso ancora: si ripubblica
    assert not db.already_posted("test:1", "it", 30, 7)   # altro paese


def test_import_storico_non_sovrascrive():
    db = PriceDB(":memory:")
    db.save([prod(50)], day=date(2026, 1, 2))
    db.import_history("test:1", {"2026-01-01": 100.0, "2026-01-02": 999.0})
    assert db.series("test:1", days=10000) == [["2026-01-01", 100.0], ["2026-01-02", 50.0]]


def test_keepa_conversione_data():
    from engine.keepa_backfill import _keepa_day
    assert _keepa_day(0) == "2011-01-01"
