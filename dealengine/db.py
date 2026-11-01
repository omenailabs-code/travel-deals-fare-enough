"""SQLite storage for the Fare Enough deal engine.

Tables:
  routes          one row per route (e.g. JFK-LHR) with modal currency
  prices          raw price observations (source URL, timestamp, params)
  deals           flagged/verified deal records (label + confidence 1-5)
  baseline_cache  derived per-route stats (median, lowest normal)

All timestamps are ISO-8601 UTC strings ("...Z"), stored without
microseconds so lexicographic comparison is chronological.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "deals.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS routes (
  id          INTEGER PRIMARY KEY,
  key         TEXT UNIQUE NOT NULL,
  origin      TEXT NOT NULL,
  dest        TEXT NOT NULL,
  currency    TEXT NOT NULL,
  first_seen  TEXT NOT NULL,
  notes       TEXT
);

CREATE TABLE IF NOT EXISTS prices (
  id             INTEGER PRIMARY KEY,
  route_id       INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  source         TEXT NOT NULL,
  source_url     TEXT,
  price          REAL NOT NULL,
  currency       TEXT NOT NULL,
  cabin          TEXT,
  baggage_included INTEGER,
  observed_at    TEXT NOT NULL,
  search_params  TEXT
);
CREATE INDEX IF NOT EXISTS idx_prices_route_time ON prices(route_id, observed_at);

CREATE TABLE IF NOT EXISTS deals (
  id             INTEGER PRIMARY KEY,
  route_id       INTEGER REFERENCES routes(id) ON DELETE CASCADE,
  package_id     INTEGER REFERENCES packages(id) ON DELETE CASCADE,
  price          REAL NOT NULL,
  currency       TEXT NOT NULL,
  label          TEXT NOT NULL CHECK (label IN ('verified','flash','mistake')),\
  confidence     INTEGER NOT NULL CHECK (confidence BETWEEN 1 AND 5),\
  source_url     TEXT NOT NULL,\
  verified_at    TEXT NOT NULL,\
  verified_by    TEXT,\
  travel_window  TEXT,\
  terms          TEXT,\
  status         TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired','archived')),\
  expired_at     TEXT,\
  created_at     TEXT NOT NULL,\
  published      INTEGER NOT NULL DEFAULT 0\
);
CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status);

CREATE TABLE IF NOT EXISTS baseline_cache (
  route_id     INTEGER PRIMARY KEY REFERENCES routes(id) ON DELETE CASCADE,
  median_price REAL,
  lowest_normal REAL,
  n_obs        INTEGER,
  window_start TEXT,
  window_end   TEXT,
  computed_at  TEXT
);

CREATE TABLE IF NOT EXISTS packages (
  id              INTEGER PRIMARY KEY,
  resort          TEXT NOT NULL,
  destination     TEXT NOT NULL,
  board_type      TEXT, -- e.g., 'all-inclusive'
  nights          INTEGER,
  departure_origin TEXT,
  departure_date  TEXT,
  source          TEXT,
  source_url      TEXT,
  UNIQUE(resort, destination, board_type, nights, departure_origin, departure_date)
);

CREATE TABLE IF NOT EXISTS package_prices (
  id               INTEGER PRIMARY KEY,
  package_id       INTEGER NOT NULL REFERENCES packages(id) ON DELETE CASCADE,
  price_total      REAL NOT NULL,
  price_per_person REAL,
  currency         TEXT NOT NULL,
  source           TEXT NOT NULL,
  source_url       TEXT,
  observed_at      TEXT NOT NULL,
  raw_json         TEXT
);

CREATE INDEX IF NOT EXISTS idx_package_prices_time ON package_prices(package_id, observed_at);

CREATE TABLE IF NOT EXISTS package_baseline_cache (
  package_id     INTEGER PRIMARY KEY REFERENCES packages(id) ON DELETE CASCADE,
  median_price   REAL,
  lowest_normal  REAL,
  n_obs           INTEGER,
  window_start   TEXT,
  window_end     TEXT,
  computed_at    TEXT
);
"""


def connect(path: "Path | str" = DB_PATH):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(conn):
    conn.executescript(SCHEMA)
    conn.commit()
