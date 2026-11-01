#!/usr/bin/env python3
"""Clean up deals.json: remove false-positive Luxury Escapes deals, keep only real packages"""

import json

DATA_DIR = 'site/data'

# Load existing deals
with open(f'{DATA_DIR}/deals.json', 'r') as f:
    deals = json.load(f)

# Real resort name patterns (exclude false positives)
bad_patterns = [
    'non-member', 'outstanding', 'exceptional', 'excellent', 'family friendly',
    'very good', 'set sail', 'ultimate cruise', 'lux exclusives',
    'starts and ends', 'explora journeys', 'new york', 'whistler',
    'dubai', 'hong kong', 'bali', 'cambodia', 'sri lanka', 'usa',
    'huang hom bay', 'kapau atoll', 'south male', 'nusa dua',
    'ubud', 'cabo san lu', 'breckenridge', 'hambantota',
    'mel', 'meli', 'sa ii', 'raffles', 'nh collection', 'sofitel',
    'anantara', 'anana', 'kayumanis', 'mai khao', 'harbor grand',
    'sinae', 'address beach', 'island escape', 'the aviary',
]

# Filter: keep only deals that pass quality checks
cleaned = []
for d in deals:
    # Must have a resort name
    resort = d.get('resort', '')
    if not resort:
        continue
    
    # Must have a price >= 500
    price = d.get('price', 0)
    if price < 500:
        continue
    
    # Must not contain bad patterns
    resort_lower = resort.lower()
    if any(pat in resort_lower for pat in bad_patterns):
        continue
    
    # Must have a valid source (redtag.ca or luxuryescapes with real resort)
    if d.get('source') == 'luxuryescapes.com':
        # For luxuryescapes, we need more stringent filtering
        # Only keep if it has a proper resort name (2-4 words, all caps or title case)
        words = resort.split()
        if len(words) < 2 or len(words) > 6:
            continue
        # Must have stars
        if not d.get('stars'):
            continue
    
    cleaned.append(d)

# Sort: packages by stars desc (None -> 0), then price asc; flights by price asc
packages = [d for d in cleaned if d.get('type') == 'package']
flights = [d for d in cleaned if d.get('type') != 'package']

def pkg_sort_key(d):
    stars = d.get('stars') if d.get('stars') else 0
    return (-stars, d.get('price', 0))

def flight_sort_key(d):
    return d.get('price', 0)

packages.sort(key=pkg_sort_key)
flights.sort(key=flight_sort_key)
sorted_deals = packages + flights

with open(f'{DATA_DIR}/deals.json', 'w') as f:
    json.dump(sorted_deals, f, indent=2)

print(f"Original: {len(deals)} deals")
print(f"Cleaned: {len(sorted_deals)} deals")
print(f"  Packages: {len(packages)}")
print(f"  Flights: {len(flights)}")
print()
print("=== PACKAGES ===")
for p in sorted(packages, key=lambda x: (-(x.get('stars') or 0), x.get('price', 0))):
    stars = f'{p["stars"]}★' if p.get('stars') else 'N/A'
    print(f'  {p["resort"]} | CAD{p["price"]} | {stars} | source: {p.get("source", "")}')
