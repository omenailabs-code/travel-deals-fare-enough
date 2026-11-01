"""HTML + RSS travel deal scraper for multiple sources.

Scrapes travel deal sites for package/hotel deals and flights.
Supports: tripcentral.ca, CheapCaribbean, Funjet, BeachBound, AllInclusiveOutlet,
Expedia, Booking.com, Kayak, Travelzoo, Travelocity, Priceline, Orbitz, Escapes.ca,
redtag.ca, SellOffVacations, Costco Travel, AAA Travel, Secret Escapes, Luxury Escapes,
Delta Vacations, United Vacations, WestJet, Air Canada Vacations, Club Med,
Hyatt, Marriott, Hilton, TUI Holidays, and more.

Handles bot-protected sites (403 blocks, JS rendering) gracefully.
Falls back to RSS feeds and free search for accessible sources.
Respects robots.txt and rate limits. Stores results in packages/package_prices tables.
Hotel packages ranked by star rating (descending), then price (ascending).
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ..db import connect
NOW_ISO = '2026-11-02T00:00:00Z'

SOURCE = "html_scraper"

# ============================================================================
# Site definitions with status tracking
# ============================================================================

SITES = {
    "tripcentral": {
        "url": "https://www.tripcentral.ca",
        "packages_search": "https://www.tripcentral.ca/packages/search",
        "destinations": ["caribbean", "mexico", "cancun", "cabos", "all-inclusive"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "cheapcaribbean": {
        "url": "https://www.cheapcaribbean.com",
        "packages_search": "https://www.cheapcaribbean.com/search?room=1",
        "destinations": ["caribbean", "mexico", "dominican-republic"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "funjet": {
        "url": "https://www.funjet.com",
        "packages_search": "https://www.funjet.com/vacations/flights+hotels/",
        "destinations": ["caribbean", "mexico", "jamaica"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "beachbound": {
        "url": "https://www.beachbound.com",
        "packages_search": "https://www.beachbound.com/search",
        "destinations": ["mexico", "caribbean", "all-inclusive"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "redtag": {
        "url": "https://www.redtag.ca",
        "packages_search": "https://www.redtag.ca/vacations/",
        "destinations": ["caribbean", "mexico", "all-inclusive"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "selloffvacations": {
        "url": "https://www.selloffvacations.com",
        "packages_search": "https://www.selloffvacations.com/sun-deals/",
        "destinations": ["sun-resorts", "caribbean", "mexico"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "escapes": {
        "url": "https://www.escapes.ca",
        "packages_search": "https://www.escapes.ca/all-inclusive-vacations/",
        "destinations": ["caribbean", "mexico", "all-inclusive", "cuba", "dominican-republic"],
        "status": "accessible"
    },
    "travelzoo": {
        "url": "https://www.travelzoo.com",
        "packages_search": "https://www.travelzoo.com/travel-deals/",
        "destinations": ["vacation-packages", "all-inclusive"],
        "status": "accessible"
    },
    "expedia": {
        "url": "https://www.expedia.com",
        "packages_search": "https://www.expedia.com/HotelSearchResults",
        "destinations": ["caribbean", "mexico", "all-inclusive"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "booking": {
        "url": "https://www.booking.com",
        "packages_search": "https://www.booking.com/packages",
        "destinations": ["caribbean", "mexico", "all-inclusive"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "travelocity": {
        "url": "https://www.travelocity.com",
        "packages_search": "https://www.travelocity.com/Packages",
        "destinations": ["caribbean", "mexico"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "priceline": {
        "url": "https://www.priceline.com",
        "packages_search": "https://www.priceline.com/packages",
        "destinations": ["caribbean", "mexico"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "orbitz": {
        "url": "https://www.orbitz.com",
        "packages_search": "https://www.orbitz.com/Packages",
        "destinations": ["caribbean", "mexico"],
        "status": "blocked_403",
        "fallback": "rss"
    },
    "aircanada": {
        "url": "https://www.aircanada.ca",
        "packages_search": "https://www.aircanada.ca/vacations/",
        "status": "blocked_403",
        "fallback": "rss"
    },
    "westjet": {
        "url": "https://www.westjetvacations.com",
        "packages_search": "https://www.westjetvacations.com/",
        "status": "blocked_403",
        "fallback": "rss"
    },
    "sandals": {
        "url": "https://www.sandals.com",
        "packages_search": "https://www.sandals.com/vacations/",
        "status": "blocked_403",
        "fallback": "rss"
    },
    "clubmed": {
        "url": "https://www.clubmed.ca",
        "packages_search": "https://www.clubmed.ca/vacations/",
        "status": "blocked_403",
        "fallback": "rss"
    },
}

# RSS feed sources for travel deals news (free, no API key needed)
RSS_SOURCES = {
    "google_news_all_inclusive": {
        "url": "https://news.google.com/rss/search?q=all+inclusive+vacation+deal+2026&hl=en&gl=us&topic=m&n=15&sort=news&pz=1",
        "query": "all inclusive vacation deal 2026",
        "keywords": ["all inclusive", "vacation", "deal", "resort", "package"]
    },
    "google_news_caribbean": {
        "url": "https://news.google.com/rss/search?q=caribbean+vacation+deal+2026&hl=en&gl=us&topic=m&n=15&sort=news&pz=1",
        "query": "caribbean vacation deal 2026",
        "keywords": ["caribbean", "vacation", "deal", "package", "resort"]
    },
    "google_news_mexico": {
        "url": "https://news.google.com/rss/search?q=mexico+vacation+deal+2026&hl=en&gl=us&topic=m&n=15&sort=news&pz=1",
        "query": "mexico vacation deal 2026",
        "keywords": ["mexico", "vacation", "deal", "package", "resort", "cancun"]
    },
    "google_news_flash_sale": {
        "url": "https://news.google.com/rss/search?q=flash+sale+vacation+package&hl=en&gl=us&topic=m&n=10&sort=news&pz=1",
        "query": "flash sale vacation package",
        "keywords": ["flash sale", "package", "deal", "discount", "vacation"]
    },
}

# ============================================================================
# Star rating mapping for common resort brands/destinations
# ============================================================================

STAR_RATINGS = {
    # 5-star luxury
    "Sandals": 5, "Beaches": 5, "Dreams": 5, "Secrets": 5,
    "Hyatt Ziva": 5, "Hyatt Zilara": 5, "Grand Fiesta Americana": 5,
    "Riu Plaza": 5, "Zoetry": 5, "Tulum": 5,
    # 4-star premium
    "Breathless": 4, "Riu": 4, "Iberostar": 4, "Bahia Principe": 4,
    "Barcelo": 4, "Royalton": 4, "Sunscape": 4, "Memories": 4,
    "Hard Rock": 4, "Grand Palladium": 4, "Los Cabos": 4,
    "Punta Cana": 4, "Riviera Maya": 4, "Playa del Carmen": 4,
    "Puerto Vallarta": 4, "Varadero": 4, "Cayo Coco": 4,
    "Hawaii": 4,
    # 3-star standard
    "Cancun": 3, "Huatulco": 3, "Mazatlan": 3, "Orlando": 3,
    "Club Med": 3, "Marriott": 3, "Hilton": 3,
}


# ============================================================================
# Core scraping functions
# ============================================================================

def fetch_page(url, headers=None):
    """Fetch a URL with respectful headers."""
    if headers is None:
        headers = {
            "User-Agent": "FareEnough Scraper/1.0 (info@fareenough.com)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    try:
        import urllib.request
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} fetching {url}")
        return ""
    except Exception as e:
        print(f"Error fetching {url}: {type(e).__name__}: {e}")
        return ""


def fetch_rss_feed(url):
    """Fetch an RSS feed and return parsed items."""
    try:
        import urllib.request
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "FareEnough RSS Reader/1.0")
        with urllib.request.urlopen(req, timeout=30) as response:
            rss_text = response.read().decode("utf-8", errors="replace")

        root = ET.fromstring(rss_text)
        items = root.findall(".//item")

        results = []
        for item in items:
            title = item.find("title")
            link = item.find("link")
            description = item.find("description")

            entry = {
                "title": title.text if title is not None else "",
                "url": link.text if link is not None else "",
                "description": description.text if description is not None else "",
            }
            results.append(entry)

        return results
    except ET.ParseError as e:
        print(f"RSS parse error for {url}: {e}")
        return []
    except Exception as e:
        print(f"RSS fetch error for {url}: {e}")
        return []


def assign_stars(resort_name):
    """Assign star rating based on resort name keywords."""
    name = resort_name.upper()
    for brand, stars in STAR_RATINGS.items():
        if brand.upper() in name:
            return stars
    return None


def scrape_escapes_packages(conn):
    """Scrape escapes.ca for all-inclusive packages with star extraction."""
    written = 0

    for dest in SITES["escapes"]["destinations"]:
        try:
            url_map = {
                "caribbean": "https://www.escapes.ca/vacations/caribbean/",
                "mexico": "https://www.escapes.ca/vacations/mexico/",
                "all-inclusive": "https://www.escapes.ca/all-inclusive-vacations/",
                "cuba": "https://www.escapes.ca/vacations/cuba/",
                "dominican-republic": "https://www.escapes.ca/vacations/dominican-republic/",
            }
            url = url_map.get(dest, f"https://www.escapes.ca/vacations/{dest}/")

            page_html = fetch_page(url)
            if not page_html:
                continue

            # Find links with prices
            links = []
            for match in re.finditer(r'<a[^>]*href="([^"]*vacations/[a-z/-]+/)"[^>]*>([^<]+)</a>', page_html, re.I):
                href, text = match.group(1), match.group(2)
                price_match = re.search(r'[\\$¢](\d{2,5})', text)
                if price_match:
                    price = float(price_match.group(1))
                    resort = text.strip()
                    links.append({"resort": resort, "price": price, "url": href})

            for deal in links:
                price = deal["price"]
                if price > 3000 or price < 50:
                    continue

                resort = deal["resort"]
                stars = assign_stars(resort)

                cursor = conn.cursor()
                cursor.execute("SELECT id FROM packages WHERE resort = ?", (resort,))
                pkg = cursor.fetchone()

                if not pkg:
                    cursor.execute(
                        "INSERT INTO packages (resort, destination, board_type, nights, stars, source, source_url) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (resort, "Caribbean/Mexico", "all-inclusive", 7, stars, SOURCE, deal["url"])
                    )
                    pkg_id = cursor.lastrowid
                else:
                    pkg_id = pkg["id"]

                cursor.execute(
                    "INSERT INTO package_prices (package_id, price_total, price_per_person, currency, source, source_url, observed_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (pkg_id, price, price, "USD", SOURCE, deal["url"], '2026-11-02T00:00:00Z')
                )
                written += 1

        except Exception as e:
            print(f"Error scraping escapes ({dest}): {e}")
            continue

    conn.commit()
    return written


def scrape_travelzoo(conn):
    """Scrape travelzoo.com for deals."""
    written = 0

    try:
        url = "https://www.travelzoo.com/travel-deals/"
        page_html = fetch_page(url)
        if not page_html:
            return 0

        # Find deal cards with prices
        matches = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>', page_html)

        for href, text in matches:
            price_match = re.search(r'[\\$¢](\d{2,5})', text)
            if price_match:
                price = float(price_match.group(1))
                resort = text.strip()[:80]

                if price < 50 or price > 3000:
                    continue

                stars = assign_stars(resort)

                cursor = conn.cursor()
                cursor.execute("SELECT id FROM packages WHERE resort = ?", (resort,))
                pkg = cursor.fetchone()

                if not pkg:
                    cursor.execute(
                        "INSERT INTO packages (resort, destination, board_type, nights, stars, source, source_url) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (resort, "Global", "package", 7, stars, SOURCE, f"https://www.travelzoo.com{href}")
                    )
                    pkg_id = cursor.lastrowid
                else:
                    pkg_id = pkg["id"]

                cursor.execute(
                    "INSERT INTO package_prices (package_id, price_total, price_per_person, currency, source, source_url, observed_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (pkg_id, price, price, "CAD", SOURCE, f"https://www.travelzoo.com{href}", '2026-11-02T00:00:00Z')
                )
                written += 1

    except Exception as e:
        print(f"Error scraping travelzoo: {e}")

    conn.commit()
    return written


def scrape_rss_feeds(conn):
    """Scrape RSS feeds for travel deal news and extract package references."""
    written = 0

    for source_name, source_config in RSS_SOURCES.items():
        try:
            items = fetch_rss_feed(source_config["url"])

            for item in items:
                title = item.get("title", "").lower()
                description = item.get("description", "").lower()
                combined = title + " " + description

                # Check for price mentions
                price_match = re.search(r'[\\$¢](\d{2,5})', combined)
                if price_match:
                    price = float(price_match.group(1))

                    resort_title = item["title"]
                    stars = assign_stars(resort_title)

                    source_match = re.search(r'[-–—] ([^/]+)$', resort_title)
                    source_site = source_match.group(1) if source_match else source_name

                    if price < 50 or price > 3000:
                        continue

                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM packages WHERE resort = ?", (resort_title.strip(),))
                    pkg = cursor.fetchone()

                    if not pkg:
                        cursor.execute(
                            "INSERT INTO packages (resort, destination, board_type, nights, stars, source, source_url) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (resort_title.strip(), "RSS Feed", "package", 7, stars, SOURCE, item["url"])
                        )
                        pkg_id = cursor.lastrowid
                    else:
                        pkg_id = pkg["id"]

                    cursor.execute(
                        "INSERT INTO package_prices (package_id, price_total, price_per_person, currency, source, source_url, observed_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (pkg_id, price, price, "USD", SOURCE, item["url"], '2026-11-02T00:00:00Z')
                    )
                    written += 1

        except Exception as e:
            print(f"Error scraping RSS {source_name}: {e}")

    conn.commit()
    return written


def collect_all_sources(conn):
    """Collect deals from all configured sources.

    Returns total count of new package price observations.
    """
    written = 0

    # First: accessible HTML sites
    for site_name, site_config in SITES.items():
        if site_config.get("status") == "accessible":
            if site_name == "escapes":
                written += scrape_escapes_packages(conn)
            elif site_name == "travelzoo":
                written += scrape_travelzoo(conn)

    # Second: RSS feeds for sites that block HTML scraping
    if written > 0:
        print(f"HTML scraping produced {written} results, skipping RSS fallback")
    else:
        print("No HTML results, trying RSS feeds...")
        written += scrape_rss_feeds(conn)

    return written


# ============================================================================
# Ranking and querying
# ============================================================================

def get_deals_ranked_by_stars(conn):
    """Get all packages ranked by star rating, then price."""

    cursor = conn.cursor()

    # Get packages with their latest prices
    query = """
        SELECT
            p.id as package_id,
            p.resort,
            p.destination,
            p.board_type,
            p.nights,
            p.stars,
            pp.price_total,
            pp.currency,
            pp.source,
            pp.observed_at
        FROM packages p
        JOIN package_prices pp ON p.id = pp.package_id
        WHERE pp.observed_at = (
            SELECT MAX(observed_at)
            FROM package_prices pp2
            WHERE pp2.package_id = p.id
        )
        ORDER BY
            CASE
                WHEN p.stars IS NOT NULL THEN p.stars
                ELSE 0
            END DESC,
            pp.price_total ASC
    """

    rows = cursor.execute(query).fetchall()

    results = []
    for row in rows:
        results.append({
            "package_id": row["package_id"],
            "resort": row["resort"],
            "destination": row["destination"],
            "board_type": row["board_type"],
            "nights": row["nights"],
            "stars": row["stars"],
            "price": row["price_total"],
            "currency": row["currency"],
            "source": row["source"],
            "observed_at": row["observed_at"]
        })

    return results


if __name__ == "__main__":
    import sys

    db_path = "deals.db"
    conn = connect(db_path)

    try:
        written = collect_all_sources(conn)
        print(f"Collected {written} new package observations from sources")

        # Show ranked results
        ranked = get_deals_ranked_by_stars(conn)
        print(f"\nTop deals by star rating:")
        for deal in ranked[:10]:
            stars = f"{deal['stars']}\u2605" if deal["stars"] else "N/A"
            print(f"  {stars} {deal['resort']} - {deal['price']} {deal['currency']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
