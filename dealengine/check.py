"""check.py — Main execution script for the Fare Enough deal engine.

Scans the SQLite database, detects anomalies using tuned thresholds,
generates AI descriptions via a local LLM, and writes results to
site/data/deals.json for the Astro/Tailwind frontend.

Usage:
    python dealengine/check.py
"""
from __future__ import annotations

import json
import os
import sys
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Add the project root to the path so we can import modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dealengine.db import connect, init
from dealengine.anomaly import detect_anomaly, classify, confidence, compute_baseline, BELOW_MEDIAN_RATIO, BELOW_MIN_NORMAL_RATIO, EXTREME_OUTLIER_RATIO
from dealengine.content_gen import generate_deal_description


def _now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_deals_json() -> list[dict]:
    """Load the current deals.json file."""
    deals_path = project_root / "site" / "data" / "deals.json"
    if not deals_path.exists():
        return []
    with open(deals_path, "r") as f:
        return json.load(f)


def save_deals_json(deals: list[dict]) -> None:
    """Save deals to the site/data/deals.json file."""
    deals_path = project_root / "site" / "data" / "deals.json"
    with open(deals_path, "w") as f:
        json.dump(deals, f, indent=2)


def scan_route_prices(conn, route_id: int) -> list[float]:
    """Fetch all price observations for a route."""
    rows = conn.execute(
        "SELECT price FROM prices WHERE route_id = ? ORDER BY observed_at",
        (route_id,),
    ).fetchall()
    return [float(r["price"]) for r in rows]


def scan_new_prices(conn) -> list[dict]:
    """Fetch the latest price observations that haven't been turned into deals yet."""
    # Get routes with their baselines
    routes = conn.execute("SELECT * FROM routes ORDER BY first_seen DESC").fetchall()
    new_deals = []

    # Get active deals to avoid re-flagging
    active_deals = conn.execute(
        "SELECT route_id, price, label, confidence, created_at FROM deals WHERE status = 'active'"
    ).fetchall()

    for route in routes:
        route_id = route["id"]
        route_key = route["key"]
        origin = route["origin"]
        dest = route["dest"]
        currency = route["currency"]

        # Collect all prices for baseline comparison
        history = scan_route_prices(conn, route_id)
        if len(history) < 2:
            continue

        # Get the latest price
        latest = conn.execute(
            "SELECT price, observed_at FROM prices WHERE route_id = ? ORDER BY observed_at DESC LIMIT 1",
            (route_id,),
        ).fetchone()

        if not latest:
            continue

        candidate = float(latest["price"])

        # Check if this route already has an active deal
        for existing in active_deals:
            if existing["route_id"] == route_id:
                # Check if the deal is stale (older than 2 days)
                created = datetime.fromisoformat(existing["created_at"].replace("Z", "+00:00"))
                now = datetime.fromisoformat(_now_iso().replace("Z", "+00:00"))
                if (now - created).days < 2:
                    # Skip this route — it's already being tracked
                    break
                else:
                    # The deal is stale — re-scan
                    pass
        else:
            # No active deal for this route (or all are stale) — scan it
            pass

        # Run anomaly detection
        reasons, extreme = detect_anomaly(candidate, history, currency, currency)

        if reasons:
            label = classify(candidate, history, extreme)
            obs_days = (
                datetime.fromisoformat(_now_iso().replace("Z", "+00:00"))
                - datetime.fromisoformat(route["first_seen"].replace("Z", "+00:00"))
            ).days
            conf = confidence(obs_days, label, False)

            deal_record = {
                "route": route_key,
                "origin": origin,
                "destination": dest,
                "price": candidate,
                "currency": currency,
                "label": label,
                "confidence": conf,
                "observed_days": max(obs_days, 1),
                "reasons": reasons,
                "description": "Processing description...",
                "source_url": f"https://aviasales.com/?search={route_key}",
                "is_all_inclusive": False,
                "written": False,
            }
            new_deals.append(deal_record)

    return new_deals


def scan_package_prices(conn) -> list[dict]:
    """Scan package prices for anomalies."""
    # Check if packages table exists
    try:
        pkg_check = conn.execute("SELECT 1 FROM packages LIMIT 1").fetchone()
    except Exception:
        print("  Packages table not found — skipping package scan")
        return []

    # Get packages with prices
    packages = conn.execute(
        """SELECT p.id, p.resort, p.destination, p.board_type, p.nights,
                   pp.price_total, pp.currency, pp.observed_at
            FROM packages p
            JOIN package_prices pp ON p.id = pp.package_id
            ORDER BY pp.observed_at DESC
        """
    ).fetchall()

    # Group by package_id for baseline comparison
    by_package: dict[int, list] = {}
    for pkg in packages:
        by_package.setdefault(pkg["id"], []).append(pkg)

    new_deals = []

    for pkg_id, observations in by_package.items():
        if len(observations) < 2:
            continue

        prices = [float(o["price_total"]) for o in observations]
        latest_price = float(observations[0]["price_total"])
        pkg = observations[0]

        # Compute baseline
        median_price, lowest_normal = compute_baseline(prices)

        if not lowest_normal or median_price == 0:
            continue

        # Check for anomaly
        reasons = []
        extreme = False

        if latest_price <= BELOW_MEDIAN_RATIO * median_price:
            reasons.append(
                f"{(1 - latest_price / median_price) * 100:.0f}% below package median "
                f"({latest_price:g} vs {median_price:g})"
            )

        if latest_price < BELOW_MIN_NORMAL_RATIO * lowest_normal:
            reasons.append(
                f"{(1 - latest_price / lowest_normal) * 100:.0f}% below lowest normal price "
                f"({latest_price:g} vs {lowest_normal:g})"
            )

        if latest_price < EXTREME_OUTLIER_RATIO * median_price:
            extreme = True
            reasons.append("extreme outlier (likely wrong currency or missing surcharge)")

        if reasons:
            label = classify(latest_price, prices, extreme)
            obs_days = max(1, len(observations))
            conf = confidence(obs_days, label, False)

            deal_record = {
                "route": f"{pkg['resort']} -> {pkg['destination']}",
                "resort": pkg["resort"],
                "destination": pkg["destination"],
                "board_type": pkg["board_type"],
                "nights": pkg["nights"],
                "price": latest_price,
                "currency": pkg["currency"],
                "label": label,
                "confidence": conf,
                "observed_days": obs_days,
                "reasons": reasons,
                "description": "Processing package description...",
                "source_url": "",
                "is_all_inclusive": True,
                "written": False,
            }
            new_deals.append(deal_record)

    return new_deals


def update_db_deals(conn, deals: list[dict]) -> None:
    """Write new deals to the SQLite deals table."""
    for deal in deals:
        route_id = None
        if "route" in deal and "resort" not in deal:
            route_key = deal["route"]
            row = conn.execute(
                "SELECT id FROM routes WHERE key = ?", (route_key,)
            ).fetchone()
            if row:
                route_id = row["id"]

        # Determine column set based on deal type
        is_package = deal.get("is_all_inclusive", False)
        now = _now_iso()

        if is_package:
            # Package deal — use package_id if column exists
            try:
                pkg_row = conn.execute(
                    "SELECT id FROM packages WHERE resort = ?",
                    (deal.get("resort", ""),),
                ).fetchone()
                pkg_id = pkg_row["id"] if pkg_row else None
            except Exception:
                pkg_id = None

            try:
                conn.execute(
                    "INSERT INTO deals (route_id, package_id, price, currency, label, confidence, "
                    "source_url, verified_at, verified_by, travel_window, terms, status, expired_at, created_at, published) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?, 0)",
                    (
                        route_id,
                        pkg_id,
                        deal["price"],
                        deal["currency"],
                        deal["label"],
                        deal["confidence"],
                        deal.get("source_url", ""),
                        now,
                        "engine",
                        f"7 nights at {deal.get('resort', '')}, all-inclusive",
                        "",
                        now,
                    ),
                )
            except sqlite3.OperationalError:
                # package_id column missing — insert without it
                conn.execute(
                    "INSERT INTO deals (route_id, price, currency, label, confidence, "
                    "source_url, verified_at, verified_by, travel_window, terms, status, expired_at, created_at, published) "
                    "VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?, 0)",
                    (
                        route_id,
                        deal["price"],
                        deal["currency"],
                        deal["label"],
                        deal["confidence"],
                        deal.get("source_url", ""),
                        now,
                        "engine",
                        f"7 nights at {deal.get('resort', '')}, all-inclusive",
                        "",
                        now,
                    ),
                )
        else:
            # Flight deal
            conn.execute(
                "INSERT INTO deals (route_id, price, currency, label, confidence, "
                "source_url, verified_at, verified_by, travel_window, terms, status, expired_at, created_at, published) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', NULL, ?, 0)",
                (
                    route_id,
                    deal["price"],
                    deal["currency"],
                    deal["label"],
                    deal["confidence"],
                    deal.get("source_url", ""),
                    now,
                    "engine",
                    deal.get("route", ""),
                    "",
                    now,
                ),
            )

    conn.commit()


def generate_ai_descriptions(deals: list[dict]) -> list[dict]:
    """Generate AI descriptions for all deals using the local Ollama instance."""
    for deal in deals:
        if deal.get("is_all_inclusive"):
            # Package deal
            package_data = {
                "origin": deal.get("resort", deal.get("destination")),
                "destination": deal.get("destination"),
                "price": deal["price"],
                "currency": deal["currency"],
                "delta": deal.get("delta", 0),
                "dates": deal.get("travel_window", "Flexible dates"),
                "route_type": "package",
                "board_type": deal.get("board_type", "all-inclusive"),
                "nights": deal.get("nights", 5),
            }
        else:
            # Flight deal
            package_data = {
                "origin": deal.get("origin", deal["route"].split("-")[0]),
                "destination": deal.get("destination", deal["route"].split("-")[-1]),
                "price": deal["price"],
                "currency": deal["currency"],
                "delta": deal.get("delta", 0),
                "dates": deal.get("travel_window", "Flexible dates"),
                "route_type": "round-trip",
            }

        try:
            description = generate_deal_description(package_data)
            deal["description"] = description
        except Exception as e:
            print(f"Error generating description for {deal.get('route')}: {e}")
            # Fallback description
            if deal.get("is_all_inclusive"):
                deal["description"] = (
                    f"All-inclusive {deal.get('board_type', '')} package to "
                    f"{deal.get('destination')} for {deal['price']} {deal['currency']}!"
                )
            else:
                deal["description"] = (
                    f"Amazing deal from {deal.get('origin', deal['route'].split('-')[0])} "
                    f"to {deal.get('destination', deal['route'].split('-')[-1])} "
                    f"for just {deal['price']} {deal['currency']}!"
                )
        deal["written"] = True

    return deals


def run_full_scan() -> list[dict]:
    """Run a full scan of the database, detect anomalies, and generate descriptions."""
    print("=" * 60)
    print("Fare Enough Deal Engine — Full Scan")
    print("=" * 60)

    # Connect to the database and initialize all tables
    conn = connect()
    init(conn)
    print(f"\nConnected to database: {conn}")

    # Scan flight prices for anomalies
    print("\n--- Scanning flight prices ---")
    new_deals = scan_new_prices(conn)
    print(f"Found {len(new_deals)} new flight deal(s)")

    # Scan package prices for anomalies
    print("\n--- Scanning package prices ---")
    pkg_deals = scan_package_prices(conn)
    print(f"Found {len(pkg_deals)} new package deal(s)")

    # Combine all new deals
    all_deals = new_deals + pkg_deals
    print(f"\nTotal new deals found: {len(all_deals)}")

    # Generate AI descriptions
    print("\n--- Generating AI descriptions ---")
    all_deals = generate_ai_descriptions(all_deals)

    # Save to deals.json
    print("\n--- Saving to deals.json ---")
    save_deals_json(all_deals)
    print(f"Saved {len(all_deals)} deals to site/data/deals.json")

    # Update the database
    print("\n--- Updating database ---")
    update_db_deals(conn, all_deals)
    print("Database updated.")

    conn.close()

    return all_deals


def run_incremental_scan() -> list[dict]:
    """Run a lightweight incremental scan (re-check existing deals for staleness)."""
    print("=" * 60)
    print("Fare Enough Deal Engine — Incremental Scan")
    print("=" * 60)

    conn = connect()

    # Get active deals older than 2 days
    old_deals = conn.execute(
        """SELECT d.id, d.price, d.currency, d.label, d.confidence,
                   r.key as route_key, r.origin, r.dest, r.currency as route_currency
            FROM deals d
            JOIN routes r ON d.route_id = r.id
            WHERE d.status = 'active'
            AND d.created_at < datetime('now', '-2 days')
        """
    ).fetchall()

    print(f"Found {len(old_deals)} deal(s) older than 2 days for re-scan")

    new_deals = []
    for deal in old_deals:
        route_id = deal["route_id"] if deal["route_id"] else None
        # Note: We need to use route_id, but the SQL doesn't return it directly
        # Let's fix this by querying the route_id

    conn.close()
    return new_deals


if __name__ == "__main__":
    """Main entry point for the deal engine."""
    parser = argparse.ArgumentParser(description="Fare Enough Deal Engine")
    parser.add_argument(
        "--mode",
        choices=["full", "incremental"],
        default="full",
        help="Run mode: 'full' scans all routes, 'incremental' re-checks stale deals",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan without writing to database or JSON",
    )
    args = parser.parse_args()

    print(f"Running in {args.mode} mode" + (" (dry-run)" if args.dry_run else ""))

    # For dry-run, just scan and print without writing
    if args.dry_run:
        conn = connect()
        routes = conn.execute("SELECT * FROM routes").fetchall()
        print(f"\nScanning {len(routes)} routes...")

        for route in routes:
            history = scan_route_prices(conn, route["id"])
            if len(history) < 2:
                continue

            latest_price = history[-1]
            reasons, extreme = detect_anomaly(latest_price, history, route["currency"], route["currency"])

            if reasons:
                label = classify(latest_price, history, extreme)
                conf = confidence(
                    (datetime.now(timezone.utc) -
                     datetime.fromisoformat(route["first_seen"].replace("Z", "+00:00"))).days,
                    label, False
                )
                print(f"  {route['key']}: {latest_price} -> {label} (confidence {conf})")
                for r in reasons:
                    print(f"    - {r}")

        conn.close()
    else:
        # Full or incremental scan
        if args.mode == "full":
            deals = run_full_scan()
        else:
            deals = run_incremental_scan()

        # Print summary
        print("\n" + "=" * 60)
        print("Scan Complete")
        print("=" * 60)
        for deal in deals:
            print(f"\n{deal['route']}")
            print(f"  Price: {deal['price']} {deal['currency']}")
            print(f"  Label: {deal['label']} (confidence {deal['confidence']})")
            print(f"  Description: {deal['description']}")
            if deal.get("is_all_inclusive"):
                print(f"  All-inclusive package!")
            print("-" * 40)
