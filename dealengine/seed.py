"""Seed a DB with clearly-labeled SYNTHETIC data to exercise the pipeline.

Every observation is source='synthetic-seed' so it must be excluded from
real baselines and can never become a published deal. Demo only.

Usage: python -m dealengine.seed --db PATH [--days 21]
"""
import argparse
import random
from datetime import datetime, timedelta, timezone

from . import db

ROUTES = [
    ("JFK-LHR", 520),
    ("SFO-LAX", 180),
    ("ORD-MIA", 240),
    ("BOS-SEA", 310),
    ("LAX-DFW", 210),
]

# last-observation price as a fraction of the route base:
#   0.55 -> ~45% below median  -> flash
#   0.28 -> ~72% below median  -> mistake
#   0.52 -> ~48% below median  -> flash
INJECTIONS = {"JFK-LHR": 0.55, "SFO-LAX": 0.28, "ORD-MIA": 0.52}


def seed(path, days=21, now=None):
    now = now or datetime.now(timezone.utc)
    rng = random.Random(42)
    conn = db.connect(path)
    db.init(conn)
    conn.execute("DELETE FROM baseline_cache")
    conn.execute("DELETE FROM deals")
    conn.execute("DELETE FROM prices")
    conn.execute("DELETE FROM routes")
    for key, base in ROUTES:
        origin, dest = key.split("-")
        cur = conn.execute(
            "INSERT INTO routes (key, origin, dest, currency, first_seen) VALUES (?,?,?,?,?)",
            (key, origin, dest, "USD", now.isoformat(timespec="seconds").replace("+00:00", "Z")),
        ).lastrowid
        for d in range(days):
            ts = (now - timedelta(days=days - 1 - d, minutes=9 * 60)).isoformat(
                timespec="seconds"
            ).replace("+00:00", "Z")
            price = round(base * (1 + rng.uniform(-0.08, 0.12)), 2)
            conn.execute(
                "INSERT INTO prices (route_id, source, source_url, price, currency, observed_at) "
                "VALUES (?,?,?,?,?,?)",
                (cur, "synthetic-seed", "synthetic://seed", price, "USD", ts),
            )
        if key in INJECTIONS:
            ts = now.isoformat(timespec="seconds").replace("+00:00", "Z")
            price = round(base * INJECTIONS[key], 2)
            conn.execute(
                "INSERT INTO prices (route_id, source, source_url, price, currency, observed_at) "
                "VALUES (?,?,?,?,?,?)",
                (cur, "synthetic-seed", "synthetic://seed", price, "USD", ts),
            )
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
    conn.close()
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", required=True)
    ap.add_argument("--days", type=int, default=21)
    args = ap.parse_args()
    n = seed(args.db, args.days)
    print(f"seeded {n} synthetic observations (source=synthetic-seed) into {args.db}")


if __name__ == "__main__":
    main()
