"""RSS Feed Scraper — for catching rapid deal updates and "glitches".

Parses public travel deal feeds (e.g., from blogs, forums, or aggregator sites).
Data is saved to both 'packages' and 'package_prices' tables.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Dict, Any
import httpx
import xml.etree.ElementTree as ET
from pathlib import Path

from ..db import connect, _now_iso

SOURCE = "rss_feeds"

def parse_rss_feed(url: str) -> List[Dict[str, Any]]:
    """
    Parses an RSS feed and extracts deal information.
    
    Expects a standard RSS 2.0 or Atom feed.
    Returns a list of dicts with:
        title: Deal description
        link: Source URL
        price: Extracted price (float)
        description: Additional details
    """
    results = []
    try:
        with httpx.Client(timeout=20) as client:
            r = client.get(url)
            r.raise_for_status()
            root = ET.fromstring(r.text)
            
            # Handle different namespace prefixes if present
            ns = {'rss': 'http://www.w3.org/2000/rcd/rss', 'content': 'http://purl.org/rss/1.0/content'}
            
            # RSS 2.0
            items = root.findall('.//item')
            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                
                title = title_elem.text if title_elem is not None and title_elem.text is not None else ""
                link = link_elem.text if link_elem is not None and link_elem.text is not None else ""
                desc = desc_elem.text if desc_elem is not None and desc_elem.text is not None else ""
                
                # Simple heuristic to find price in title or description
                # e.g. "$499" or "£1,200"
                price = None
                prices = re.findall(r'[\$\£\€](\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', f"{title} {desc}")
                if prices:
                    price = float(prices[0].replace(',', ''))
                
                if link and title:
                    results.append({
                        "title": title,
                        "link": link,
                        "price": price,
                        "description": desc
                    })
    except Exception as e:
        print(f"Error parsing RSS feed {url}: {e}")
    return results

def collect(
    urls: List[str],
    conn,
) -> int:
    """
    Fetches deals from RSS feeds and stores them in the database.
    
    Args:
        urls: List of RSS feed URLs.
        conn: Database connection.
    Returns:
        The number of new observations written.
    """
    written = 0
    for url in urls:
        deals = parse_rss_feed(url)
        for deal in deals:
            # Since RSS is unstructured, we treat each as a unique "package" 
            # if it's an all-inclusive deal.
            # We'll use a synthetic resort name/destination based on the title 
            # or just a generic "RSS-Feed" if we can't parse it.
            
            resort = "RSS_FEED_DEAL"
            destination = deal.get("title", "Unknown")[:50] # Truncate for DB key
            board_type = "all-inclusive"
            nights = 7 # Default assumption
            
            # Check if we already have this package identity
            # We'll use a simpler check: does this link already exist in package_prices?
            
            # Because we don't have a clean "package_id" yet for RSS, 
            # we'll create a new entry in 'packages' for every unique link 
            # found in the feed.
            
            cursor = conn.cursor()
            # Check if this specific URL is already known
            cursor.execute(
                "SELECT id FROM packages WHERE source_url = ?", (deal.get("link"),)
            )
            row = cursor.fetchone()
            
            if row:
                package_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO packages (resort, destination, board_type, nights, source, source_url) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (resort, destination, board_type, nights, SOURCE, deal.get("link"))
                )
                package_id = cursor.lastrowid
            
            price = deal.get("price") or 0.0
            observed_at = _now_iso()
            
            # Check if this price was already logged for this package at this exact moment
            cursor.execute(
                "SELECT 1 FROM package_prices WHERE package_id = ? AND price_total = ? AND observed_at = ?",
                (package_id, price, observed_at)
            )
            if cursor.fetchone():
                continue
            
            cursor.execute(
                "INSERT INTO package_prices (package_id, price_total, price_per_person, currency, source, source_url, observed_at, raw_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (package_id, price, price, "USD", SOURCE, deal.get("link"), observed_at, json.dumps(deal))
            )
            written += 1
            
    conn.commit()
    return written
