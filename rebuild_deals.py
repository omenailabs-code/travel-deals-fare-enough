#!/usr/bin/env python3
"""Rebuild deals.json from DB: clean packages + flight deals with proper origin/dest from routes table."""

import sqlite3
import json

DB_PATH = 'deals.db'
DATA_DIR = 'site/data'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# === PACKAGES ===
# Filter by source: only keep redtag.ca and travelpayouts (genuine)
# For luxuryescapes.com: only keep entries with hotel/resort keywords
packages = []
all_pkgs = conn.execute('SELECT * FROM packages').fetchall()
for p in all_pkgs:
    p_dict = dict(p)
    pkg_id = p_dict['id']
    resort = p_dict['resort']
    source = (p_dict.get('source', '') or '').lower()
    resort_lower = resort.lower()
    
    # Discard html_scraper packages (IDs 6-8: "Allegiant Air", "EcoFlow", "JetBlue")
    if source == 'html_scraper':
        continue
    
    # Discard luxuryescapes.com packages that are nav/filter text
    # Keep only those with hotel/resort keywords, but exclude these specific false positives
    if source == 'luxuryescapes.com':
        # Explicitly exclude nav/filter entries even if they match resort keywords
        false_positives = [
            'sun & beach', 'spa break', 'city break', 'double occupancy',
            'valued up to', 'offers ending', 'around the world',
            'set sail', 'ultimate cruise', 'lux exclusives',
            'starts and ends', 'explora journeys', 'exceptional',
            'very good', 'excellent', 'outstanding', 'family friendly',
            'show 69', 'whistler', 'ubud', 'new york', 'dubai',
            'hong kong', 'bali', 'cambodia', 'sri lanka', 'usa',
            'huang hom bay', 'kapau atoll', 'south male', 'nusa dua',
            'hambantota', 'capau atoll', 'south malé',
        ]
        if any(fp in resort_lower for fp in false_positives):
            continue
        
        resort_keywords = ['resort', 'hotel', 'villa', 'spa', 'beach', 'club',
                           'bay', 'cove', 'palace', 'park', 'manor', 'estate',
                           'inn', 'lodge', 'retreat', 'camp', 'guesthouse']
        # Must have at least one resort keyword (but false_positives already filtered above)
        if not any(kw in resort_lower for kw in resort_keywords):
            continue
        # Also discard price-based entries ("Non-member CA$1,039")
        if 'non-member' in resort_lower or 'ca$' in resort_lower:
            continue
    else:
        # For travelpayouts and redtag: keep all (they're genuine)
        pass
    
    # Get the price from the deals table for this package
    pkg_deals = conn.execute('SELECT price FROM deals WHERE package_id = ? AND price IS NOT NULL ORDER BY price ASC LIMIT 1', (pkg_id,)).fetchall()
    price = pkg_deals[0]['price'] if pkg_deals else 0
    
    # Discard luxuryescapes.com packages with price < 100 (parsing errors)
    if source == 'luxuryescapes.com' and price < 100:
        continue
    
    packages.append({
        'resort': p_dict['resort'],
        'destination': p_dict.get('destination', '') or '',
        'stars': p_dict.get('stars'),
        'price': float(price),
        'currency': 'CAD',
        'is_all_inclusive': True,
        'source': p_dict.get('source', '') or 'database',
        'type': 'package'
    })

# === FLIGHTS ===
# JOIN with routes table to get origin/dest from route_key
flights = []
flight_deals = conn.execute('''
    SELECT d.*, r.key as route_key, r.origin, r.dest
    FROM deals d
    JOIN routes r ON d.route_id = r.id
    WHERE d.package_id IS NULL AND d.route_id IS NOT NULL
''').fetchall()

# Deduplicate: keep only the lowest price per route_key
seen_routes = {}
for d in flight_deals:
    d_dict = dict(d)
    route_key = d_dict['route_key']
    price = d_dict['price']
    
    if route_key not in seen_routes or price < seen_routes[route_key]['price']:
        seen_routes[route_key] = {
            'origin': d_dict['origin'],
            'destination': d_dict['dest'],
            'route_key': route_key,
            'price': price,
            'currency': d_dict.get('currency', 'USD'),
            'label': 'anomaly',
            'type': 'flight'
        }

flights = list(seen_routes.values())

# === SORT ===
def pkg_sort_key(d):
    stars = d.get('stars') if d.get('stars') else 0
    return (-stars, d.get('price', 0))

def flight_sort_key(d):
    return d.get('price', 0)

packages.sort(key=pkg_sort_key)
flights.sort(key=flight_sort_key)
sorted_deals = packages + flights

# === WRITE JSON ===
with open(f'{DATA_DIR}/deals.json', 'w') as f:
    json.dump(sorted_deals, f, indent=2)

print(f"Total deals: {len(sorted_deals)}")
print(f"  Packages: {len(packages)}")
print(f"  Flights: {len(flights)}")
print()
print("=== PACKAGES ===")
for p in sorted(packages, key=lambda x: (-(x.get('stars') or 0), x.get('price', 0))):
    stars = f'{p["stars"]}★' if p.get('stars') else 'N/A'
    price = p.get('price', 0)
    print(f'  {p["resort"]} | CAD{price} | {stars} | source: {p.get("source", "")}')
print()
print("=== FLIGHTS ===")
for f in sorted(flights, key=lambda x: x.get('price', 0)):
    route = f.get('origin', '') + ' → ' + f.get('destination', '')
    print(f'  {route} | CAD{f.get("price", 0)} | key: {f.get("route_key", "")}')

conn.close()
