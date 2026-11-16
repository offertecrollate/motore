"""Storico prezzi su SQLite (un file, nessun server, gratis)."""
import sqlite3
from datetime import date, datetime, timedelta
from typing import Iterable, List, Optional

from .models import Product

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    key TEXT PRIMARY KEY,
    source TEXT, product_id TEXT, name TEXT, shop TEXT,
    url TEXT, image TEXT, currency TEXT, category TEXT, ean TEXT,
    last_seen TEXT
);
CREATE TABLE IF NOT EXISTS prices (
    key TEXT, day TEXT, price REAL,
    PRIMARY KEY (key, day)
);
CREATE TABLE IF NOT EXISTS posted (
    key TEXT, country TEXT, price REAL, posted_at TEXT
);
CREATE TABLE IF NOT EXISTS backfilled (key TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS messages (
    key TEXT, country TEXT, channel TEXT, kind TEXT, ref TEXT, extra TEXT,
    text TEXT, price REAL, posted_at TEXT, ended_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_prices_key ON prices(key);
CREATE INDEX IF NOT EXISTS idx_posted ON posted(key, country);
"""


class PriceDB:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.executescript(SCHEMA)

    def save(self, products: Iterable[Product], day: Optional[date] = None) -> int:
        d = (day or date.today()).isoformat()
        n = 0
        cur = self.conn.cursor()
        for p in products:
            cur.execute(
                """INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(key) DO UPDATE SET name=excluded.name, url=excluded.url,
                   image=excluded.image, shop=excluded.shop, last_seen=excluded.last_seen""",
                (p.key, p.source, p.product_id, p.name, p.shop, p.url, p.image,
                 p.currency, p.category, p.ean, d),
            )
            # se nello stesso giorno arrivano più letture, si tiene la più bassa
            cur.execute(
                """INSERT INTO prices VALUES (?,?,?)
                   ON CONFLICT(key, day) DO UPDATE SET price=MIN(price, excluded.price)""",
                (p.key, d, p.price),
            )
            n += 1
        self.conn.commit()
        return n

    def prune(self, keep_days: int = 100) -> None:
        """Toglie i prezzi più vecchi di keep_days giorni (il file resta piccolo)."""
        start = (date.today() - timedelta(days=keep_days)).isoformat()
        self.conn.execute("DELETE FROM prices WHERE day<?", (start,))
        self.conn.commit()

    def history(self, key: str, before: date, days: int) -> List[float]:
        """Prezzi dei giorni precedenti a `before` (escluso), al massimo `days` giorni."""
        start = (before - timedelta(days=days)).isoformat()
        rows = self.conn.execute(
            "SELECT price FROM prices WHERE key=? AND day>=? AND day<? ORDER BY day",
            (key, start, before.isoformat()),
        ).fetchall()
        return [r[0] for r in rows]

    def series(self, key: str, days: int = 90) -> List[list]:
        """[[giorno, prezzo], ...] degli ultimi `days` giorni, oggi compreso (per il grafico)."""
        start = (date.today() - timedelta(days=days)).isoformat()
        rows = self.conn.execute(
            "SELECT day, price FROM prices WHERE key=? AND day>=? ORDER BY day",
            (key, start),
        ).fetchall()
        return [[d, p] for d, p in rows]

    def days_known(self, key: str) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM prices WHERE key=?", (key,)).fetchone()[0]

    def import_history(self, key: str, days: dict) -> None:
        """Storico arrivato da fuori (es. Keepa): {giorno: prezzo}; non sovrascrive i prezzi già raccolti."""
        self.conn.executemany("INSERT OR IGNORE INTO prices VALUES (?,?,?)",
                              [(key, d, p) for d, p in days.items()])
        self.conn.commit()

    def backfilled(self, key: str) -> bool:
        return self.conn.execute("SELECT 1 FROM backfilled WHERE key=?", (key,)).fetchone() is not None

    def mark_backfilled(self, key: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO backfilled VALUES (?)", (key,))
        self.conn.commit()

    def already_posted(self, key: str, country: str, price: float, within_days: int) -> bool:
        """True se il prodotto è già stato pubblicato di recente a un prezzo uguale o più basso."""
        since = (datetime.now() - timedelta(days=within_days)).isoformat()
        row = self.conn.execute(
            "SELECT MIN(price) FROM posted WHERE key=? AND country=? AND posted_at>=?",
            (key, country, since),
        ).fetchone()
        return row[0] is not None and price >= row[0] - 0.01

    def mark_posted(self, key: str, country: str, price: float) -> None:
        self.conn.execute(
            "INSERT INTO posted VALUES (?,?,?,?)",
            (key, country, price, datetime.now().isoformat()),
        )
        self.conn.commit()

    # ---- messaggi pubblicati, per poterli segnare come terminati
    def save_message(self, key, country, channel, kind, ref, text, price, extra=""):
        self.conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                          (key, country, channel, kind, str(ref), extra or "", text, price,
                           datetime.now().isoformat(timespec="minutes")))
        self.conn.commit()

    def open_messages(self, country, days=14):
        since = (datetime.now() - timedelta(days=days)).isoformat(timespec="minutes")
        cur = self.conn.execute("SELECT rowid, key, channel, kind, ref, extra, text, price FROM messages "
                                "WHERE country=? AND ended_at IS NULL AND posted_at>=?", (country, since))
        return [dict(zip(["id", "key", "channel", "kind", "ref", "extra", "text", "price"], r)) for r in cur]

    def end_message(self, rowid):
        self.conn.execute("UPDATE messages SET ended_at=? WHERE rowid=?",
                          (datetime.now().isoformat(timespec="minutes"), rowid))
        self.conn.commit()
