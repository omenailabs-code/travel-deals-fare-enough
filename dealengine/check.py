"""Scan the database for anomalies: latest price per route vs its history.

Usage:
  python -m dealengine.check [--db PATH] [--window-days N] [--write]

  --db           SQLite path (default: <project>/deals.db)
  --window-days  baseline window, max 90 (default 90)
  --write        insert flagged anomalies into the deals table (deduped:
                 no new row when an active deal with same route+price exists)

Also refreshes baseline_cache for every route that has observations.
"""
import argparse
import json
from datetime import datetime, timedelta, timezone

from . import db
from .anomaly import MIN_OBS, classify, compute_baseline, confidence, detect_anomaly


def _utcnow():
    return datetime.now(timezone.utc)


def _ts(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def scan(path=None, window_days=90, write=False):
    path = path or db.DB_PATH
    conn = db.connect(path)
    db.init(conn)
    now = _utcnow()
    cutoff = _ts(now - timedelta(days=window_days))

    results = []
    rows = []
    for r in conn.execute("SELECT * FROM routes ORDER BY key").fetchall():
        obs = [
            p["price"]
            for p in conn.execute(
                "SELECT price FROM prices WHERE route_id=? AND observed_at>? ORDER BY observed_at",
                (r["id"], cutoff),
            ).fetchall()
        ]
        if not obs:
            continue
        history, candidate = obs[:-1], obs[-1]
        span = conn.execute(
            "SELECT MIN(observed_at), MAX(observed_at) FROM prices WHERE route_id=?",
            (r["id"],),
        ).fetchone()
        observed_days = max(1, (now - datetime.fromisoformat(span[0].replace("Z", "+00:00"))).days)
        m, ln = compute_baseline(history) if len(history) >= MIN_OBS else (None, None)
        reasons, extreme = detect_anomaly(
            candidate, history, currency_modal=r["currency"]
        )
        conn.execute(
            """INSERT INTO baseline_cache
               (route_id, median_price, lowest_normal, n_obs, window_start, window_end, computed_at)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(route_id) DO UPDATE SET
                 median_price=excluded.median_price,
                 lowest_normal=excluded.lowest_normal,
                 n_obs=excluded.n_obs,
                 window_start=excluded.window_start,
                 window_end=excluded.window_end,
                 computed_at=excluded.computed_at""",
            (r["id"], m, ln, len(history), span[0], span[1], _ts(now)),
        )
        if reasons:
            label = classify(candidate, history, extreme)
            conf = confidence(observed_days, label, reverified=False)
            entry = {
                "route": r["key"],
                "price": candidate,
                "currency": r["currency"],
                "label": label,
                "confidence": conf,
                "observed_days": observed_days,
                "reasons": reasons,
            }
            if write:
                dup = conn.execute(
                    "SELECT id FROM deals WHERE route_id=? AND price=? AND status='active'",
                    (r["id"], candidate),
                ).fetchone()
                if dup is None:
                    conn.execute(
                        """INSERT INTO deals
                           (route_id, price, currency, label, confidence, source_url,
                            verified_at, verified_by, terms, created_at)
                           VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (
                            r["id"], candidate, r["currency"], label, conf,
                            "pending-live-verification", _ts(now), "engine",
                            "bootstrap: not yet re-verified live", _ts(now),
                        ),
                    )
                    entry["written"] = True
                else:
                    entry["written"] = False
            results.append(entry)
            status = "FLAG"
        else:
            status = "ok" if len(history) >= MIN_OBS else "baseline-building"
        rows.append(
            f"{r['key']:>10}  cand={candidate:>9.2f} {r['currency']}  "
            f"median={('n/a' if m is None else f'{m:.2f}'):>9}  "
            f"low_norm={('n/a' if ln is None else f'{ln:.2f}'):>9}  "
            f"n={len(history):>3}  {status}"
            + (f"  -> {' / '.join(reasons)}" if reasons else "")
        )
    conn.commit()
    conn.close()
    return rows, results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=None)
    ap.add_argument("--window-days", type=int, default=90)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    rows, results = scan(args.db, args.window_days, args.write)
    print("\n".join(rows) if rows else "(no routes with observations)")
    print(f"\nflagged: {len(results)}")
    if results:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
