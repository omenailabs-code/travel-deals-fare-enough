"""Populate packages and package_prices tables with live data from Travelpayouts."""
from __future__ import annotations

import json
import os
import httpx
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'deals.db')

# Test cities with active package markets
POPULAR_CITIES = ["Cancun", "Los Cabos", "Punta Cana", "Dominican Republic", "All-inclusive resorts near Orlando"]

def _now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collect_packages(token, conn):
    """Fetch hotel/package data and store in packages/package_prices tables."""
    BASE = "https://api.travelpayouts.com"
    
    with httpx.Client(timeout=30) as client:
        for city in POPULAR_CITIES:
            try:
                params = {
                    "city": city,
                    "checkin": "2026-12-01",
                    "checkout": "2026-12-08",
                    "adults": 2,
                    "currency": "usd",
                    "token": token,
                }
                r = client.get(f"{BASE}/hotels/v1/search", params=params)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"  Failed to fetch {city}: {e}")
                continue
            
            results = data.get("results") or []
            if not results:
                print(f"  No results for {city}")
                continue
            
            for item in results:
                resort = item.get("name", f"Resort-{city.upper()}")
                dest = item.get("city_name", city)
                board_type = "all-inclusive"
                nights = 7
                
                source_url = item.get("url") or item.get("deeplink")
                if not source_url:
                    continue
                
                # Check if package exists
                pkg = conn.execute(
                    "SELECT id FROM packages WHERE source_url = ?", (source_url,)
                ).fetchone()
                
                if pkg:
                    package_id = pkg["id"]
                else:
                    cur = conn.execute(
                        "INSERT INTO packages (resort, destination, board_type, nights, source, source_url) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (resort, dest, board_type, nights, "travelpayouts", source_url)
                    )
                    package_id = cur.lastrowid
                
                price = float(item.get("price") or 0.0)
                observed_at = _now_iso()
                
                # Check if price exists
                exists = conn.execute(
                    "SELECT 1 FROM package_prices WHERE package_id = ? AND price_total = ? AND observed_at = ?",
                    (package_id, price, observed_at)
                ).fetchone()
                
                if not exists:
                    conn.execute(
                        "INSERT INTO package_prices (package_id, price_total, price_per_person, currency, source, source_url, observed_at, raw_json) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (package_id, price, price, "USD", "travelpayouts", source_url, observed_at, json.dumps(item))
                    )
            
            conn.commit()


def main():
    """Main entry point."""
    token = os.getenv("TRAVELPAYOUTS_TOKEN", "f5c1ae433cd63bc27f2e9e6113c91556").strip()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print(f"Populating packages from Travelpayouts ({len(POPULAR_CITIES)} cities)...")
    collect_packages(token, conn)
    
    # Verify
    pkg_count = conn.execute("SELECT count(*) as cnt FROM packages").fetchone()["cnt"]
    price_count = conn.execute("SELECT count(*) as cnt FROM package_prices").fetchone()["cnt"]
    print(f"\nPackages: {pkg_count} rows")
    print(f"Package prices: {price_count} rows")
    
    conn.close()


if __name__ == "__main__":
    main()
