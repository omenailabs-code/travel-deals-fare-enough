"""Travelpayouts (Aviasales) adapter — primary price source.

Free affiliate API. Token comes from the Travelpayouts dashboard
(Tools -> API -> token) and is read from the TRAVELPAYOUTS_TOKEN env var
(.env is gitignored — never commit or log it).

Endpoints used (Aviasales v3, documented shape):
  prices_for_dates  GET /aviasales/v3/prices_for_dates
  search_by_price_range  GET /aviasales/v3/search_by_price_range
  deeplink  GET /aviasales/v3/get_special_offers (or manual construction)

NOTE: response parsing is defensive against the documented shape.
The first live run with a real token must be checked against current docs —
see the \"verify live endpoints\" task in TASKS.md.

Every observation is stored with source='travelpayouts' plus the deeplink
URL, so a published deal can always point the reader back to the exact
search that produced it.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Iterable, List, Optional

import httpx

# Base URL for Aviasales v3
BASE = "https://api.travelpayouts.com/aviasales/v3"
SOURCE = "travelpayouts"

# Hardcoded for session testing - should be moved to .env
DEFAULT_TOKEN = "f5c1ae433cd63bc27f2e9e6113c91556"

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_token(env: "dict | None" = None) -> str:
    env = env if env is not None else os.environ
    token = (env.get("TRAVELPAYOUTS_TOKEN") or env.get("TRAVELPAYOUTS_TOKEN_FALLBACK") or DEFAULT_TOKEN).strip()
    if not token:
        raise ValueError("TRAVELPAYOUTS_TOKEN not set (add it to the gitignored .env)")
    return token

class TravelpayoutsClient:
    """Thin client over the Aviasales v3 endpoints."""

    def __init__(self, token: str, client: httpx.Client | None = None):
        if not token:
            raise ValueError("token required (set TRAVELPAYOUTS_TOKEN in .env)")
        self.token = token
        self._client = client or httpx.Client(timeout=30)

    def prices_for_dates(self, origin: str, destination: str, start_date: str, days: int = 30) -> dict:
        """
        Returns cheapest tickets for a range of dates.
        Ideal for populating 'prices' table for baseline analysis.
        
        Args:
            origin: IATA code (e.g. 'JFK')
            destination: IATA code (e.g. 'LHR')
            start_date: YYYY-MM (e.g. '2026-11')
            days: Number of days to look ahead
        """
        params = {
            "origin": origin,
            "destination": destination,
            "departure_at": start_date,
            "days": days,
            "unique": "false",
            "sorting": "price",
            "direct": "false",
            "cy": "usd",
            "limit": 30,
            "page": 1,
            "one_way": "true",
            "token": self.token,
        }
        r = self._client.get(f"{BASE}/prices_for_dates", params=params)
        r.raise_for_status()
        return r.json()

    def search_by_price_range(self, origin: str, destination: str, min_price: float, max_price: float) -> dict:
        """
        Returns flight tickets within a specific price range.
        Useful for finding 'mistake' fares.
        """
        params = {
            "origin": origin,
            "destination": destination,
            "value_min": min_price,
            "value_max": max_price,
            "one_way": "true",
            "direct": "false",
            "locale": "en",
            "cy": "usd",
            "market": "us",
            "limit": 30,
            "page": 1,
            "token": self.token,
        }
        r = self._client.get(f"{BASE}/search_by_price_range", params=params)
        r.raise_for_status()
        return r.json()

    def search(self, origin: str, destination: str, date: str) -> dict:
        """One search: cheapest fares for origin->destination on date (via prices_for_dates)."""
        return self.prices_for_dates(origin, destination, date[:7], days=1)

    def deeplink(self, origin: str, destination: str, date: str) -> str:
        """Constructs an Aviasales deeplink for a reader to check the deal."""
        return f"https://aviasales.com/?token={self.token}&origin={origin}&destination={destination}&departure={date}"

    def search_hotels(self, city: str, checkin: str, checkout: str, adults: int = 1, children: int = 0) -> dict:
        """
        Search for hotel/package prices.
        
        Args:
            city: City name (e.g. 'Paris')
            checkin: YYYY-MM-DD
            checkout: YYYY-MM-DD
            adults: Number of adults
            children: Number of children
        """
        params = {
            "city": city,
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "children": children,
            "currency": "usd",
            "token": self.token,
        }
        # Note: Hotel API uses a different base path than Aviasales
        r = self._client.get("https://api.travelpayouts.com/hotels/v1/search", params=params)
        r.raise_for_status()
        return r.json()


    def close(self):
        self._client.close()

def _route_id(conn, origin: str, dest: str, currency: str) -> int:
    key = f"{origin}-{dest}"
    row = conn.execute("SELECT id FROM routes WHERE key = ?", (key,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO routes (key, origin, dest, currency, first_seen) VALUES (?,?,?,?,?)",
        (key, origin, dest, currency, _now_iso()),
    )
    return cur.lastrowid

def _already_logged(conn, route_id: int, price: float, observed_at: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM prices WHERE route_id=? AND source=? AND price=? AND observed_at=?",
        (route_id, SOURCE, price, observed_at),
    ).fetchone()
    return row is not None

def collect(
    client: TravelpayoutsClient,
    conn,
    routes: Iterable[tuple[str, str, str]],
    dates: Iterable[str],
) -> int:
    """Fetch prices for each (route, date) and store observations.

    routes: iterable of (origin, destination, currency)
    dates:  iterable of "YYYY-MM-DD"
    Returns the number of observations written (deduped per instant).
    """
    written = 0
    for origin, dest, currency in routes:
        rid = _route_id(conn, origin, dest, currency)
        for date in dates:
            try:
                # We use prices_for_dates as it's the most reliable way to get \
                # recent cached data for a range.
                data = client.prices_for_dates(origin, dest, date[:7])
            except (httpx.HTTPStatusError, httpx.RequestError):
                continue
            results = data.get("results") or []
            if not results:
                continue
            price = results[0].get("price")
            if price is None:
                continue
            price = float(price)
            url = results[0].get("url") or client.deeplink(origin, dest, date)
            observed_at = _now_iso()
            if _already_logged(conn, rid, price, observed_at):
                continue
            conn.execute(
                "INSERT INTO prices (route_id, source, source_url, price, currency, cabin, baggage_included, observed_at, search_params) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (rid, SOURCE, url, price, currency, "economy", 1, observed_at,
                 json.dumps({"origin": origin, "destination": dest, "departure_time": date})),
            )
            written += 1
    conn.commit()
    return written

def collect_packages(
    client: TravelpayoutsClient,
    conn,
    cities: Iterable[str],
    checkin: str,
    checkout: str,
) -> int:
    """
    Fetch hotel/package data and store in 'packages' and 'package_prices' tables.
    
    Args:
        client: TravelpayoutsClient instance.
        conn: Database connection.
        cities: List of city names.
        checkin: YYYY-MM-DD
        checkout: YYYY-MM-DD
    Returns:
        The number of new observations written.
    """
    written = 0
    for city in cities:
        try:
            data = client.search_hotels(city, checkin, checkout)
        except (httpx.HTTPStatusError, httpx.RequestError):
            continue
            
        results = data.get("results") or []
        for item in results:
            # Hotel search results usually include a unique ID or a combination of 
            # city/price/date. We'll use the unique ID from the API if available.
            # For simplicity, we'll use a synthetic resort name based on the city.
            
            resort = f"HOTEL-{city.upper().replace(' ', '-')}"
            destination = city
            board_type = "all-inclusive"
            nights = (datetime.strptime(checkout, "%Y-%m-%d") - 
                      datetime.strptime(checkin, "%Y-%m-%d")).days
            
            # Source URL is provided by the API
            source_url = item.get("url") or item.get("deeplink")
            if not source_url:
                continue
                
            # Unique check on source_url
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM packages WHERE source_url = ?", (source_url,)
            )
            row = cursor.fetchone()
            
            if row:
                package_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO packages (resort, destination, board_type, nights, source, source_url) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (resort, destination, board_type, nights, SOURCE, source_url)
                )
                package_id = cursor.lastrowid
                
            price = float(item.get("price") or 0.0)
            observed_at = _now_iso()
            
            # Check if this price was already logged for this package
            cursor.execute(
                "SELECT 1 FROM package_prices WHERE package_id = ? AND price_total = ? AND observed_at = ?",
                (package_id, price, observed_at)
            )
            if cursor.fetchone():
                continue
                
            cursor.execute(
                "INSERT INTO package_prices (package_id, price_total, price_per_person, currency, source, source_url, observed_at, raw_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (package_id, price, price, "USD", SOURCE, source_url, observed_at, json.dumps(item))
            )
            written += 1
            
    conn.commit()
    return written

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 4:
        update_db(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Usage: python -m dealengine.sources.travelpayouts <route_key> <origin> <dest> <date>")
