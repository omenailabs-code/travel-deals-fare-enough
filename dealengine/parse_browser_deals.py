#!/usr/bin/env python3
"""Parse browser-extracted raw text files and push to SQLite DB + deals.json"""

import sqlite3
import json
import re
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'deals.db')
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site', 'data')

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

# ── 1. Parse RedTag deals ──────────────────────────────────────────
def parse_redtag(text):
    deals = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        rating_match = re.search(r'Hotel rating (\d+\.\d) out of 5 stars', line)
        if rating_match:
            stars = float(rating_match.group(1))
            hotel_name = lines[i-1].strip() if i > 0 else "Unknown Resort"
            dest_line = lines[i+1].strip() if i+1 < len(lines) else ""
            dest_match = re.search(r'To (.+?), (.+)', dest_line)
            destination = dest_match.group(2) if dest_match else dest_line
            price = None
            for j in range(i+2, min(i+10, len(lines))):
                price_match = re.search(r'\$(\d+)', lines[j])
                if price_match:
                    price = float(price_match.group(1))
                    break
            if price and destination:
                deals.append({
                    'resort': hotel_name,
                    'destination': destination,
                    'stars': int(round(stars)),
                    'price': price,
                    'currency': 'CAD',
                    'source': 'redtag.ca'
                })
            print(f"  RedTag: {hotel_name} -> {destination} ${price} ({stars}★)")
        i += 1
    return deals

# ── 2. Parse Luxury Escapes deals ─────────────────────────────────
def parse_luxury_escapes(text, source='luxuryescapes.com'):
    deals = []
    # The text format per deal block:
    # Save\n
    # [Location line like "South Malé Atoll, Maldives"]
    # [RESORT NAME in caps or Title Case like "RAH GILI MALDIVES"]
    # [Rating number like "8.4"]
    # [Rating label like "Very Good"]
    # [Description]
    # ...
    # CA$[price]
    # Split on "Save\n" to get individual deal blocks
    blocks = text.split('\nSave\n')
    
    # Exclusion list for navigation/pattern text
    skip_keywords = [
        'view', 'save', 'valued', 'show', 'offers', 'around',
        'city', 'spa break', 'double', 'exotic', 'europe', 'back to',
        'top trending', 'book early', 'very good', 'exceptional',
        'excellent', 'outstanding', 'good', 'amazing', 'fantastic',
        'set sail', 'ultimate cruise', 'explora journeys', 'starts and ends',
        'barcelona', 'portugal', 'spain', 'italy', 'france', 'greece',
        'turkey', 'egypt', 'morocco', 'india', 'thailand', 'vietnam',
        'japan', 'korea', 'china', 'singapore', 'malaysia', 'indonesia',
        'philippines', 'australia', 'new zealand', 'kenya', 'tanzania',
        'zanzibar', 'mauritius', 'seychelles', 'comoros',
        'address beach', 'nh collection', 'raffles', 'so/', 'aman',
        'four seasons', 'st. regis', 'belmond', 'andrew', 'hilton',
        'marriott', 'hyatt', 'ihg', 'accor', 'intercontinental',
        'sofitel', 'kayumanis', 'burasari', 'anantara', 'sana',
        'kayumanis ubud', 'kayumanis nusa dua', 'sinae', 'mai khao',
        'anana', 'harbor grand', 'anana ecological', 'nh dubai',
        'raffles dubai', 'sa ii', 'so maldives'
    ]
    
    for block in blocks:
        # Find price
        price_match = re.search(r'CA\$(\d+)', block)
        if not price_match:
            continue
        price = float(price_match.group(1))
        
        # Filter: only keep if price is reasonable (>= $500) - CA$1-9 are false positives
        if price < 500:
            continue
        
        # Extract resort name and rating from block
        resort_name = None
        rating = None
        block_lines = block.strip().split('\n')
        
        for raw_line in block_lines:
            line = raw_line.strip()
            # Skip empty lines
            if not line:
                continue
            
            # Rating: standalone number like "8.4", "9.3"
            if re.match(r'^(\d+\.\d)$', line):
                rating = float(line)
            # Skip rating labels like "Very Good", "Exceptional"
            elif re.match(r'^(Very Good|Exceptional|Excellent|Outstanding|Good|Amazing|Fantastic|Superb|Amazingly)$', line):
                continue
            # Skip lines starting with lowercase or containing common words
            elif line[0] in 'abcdefghijklmnopqrstuvwxyz':
                continue
            # Skip lines that are just a single short word
            elif len(line.split()) == 1 and len(line) < 10:
                continue
            # Skip lines with numbers at the end (like "5 nights from")
            elif re.search(r'\d+\s+night', line, re.IGNORECASE):
                continue
            # Skip lines with special chars
            elif '⁦' in line or '⁩' in line or 'Chat' in line:
                continue
            # Skip lines that contain '$' (like "Non-member CA$989")
            elif '$' in line:
                continue
            # Skip lines that look like locations (contain comma followed by country/city)
            # Pattern: "City, Country" or "Location, Country"
            elif re.match(r'^[A-Za-z\s,]+,\s+[A-Za-z\s]+$', line) and len(line.split(',')) == 2:
                continue
            # Resort name: multi-word, starts with uppercase, 2-6 words, 8-60 chars
            words = line.split()
            if (len(words) >= 2 and len(words) <= 6 and 
                all(w[0].isalpha() and w[0].isupper() for w in words) and
                8 <= len(line) <= 60 and
                not any(kw in line.lower() for kw in skip_keywords)):
                # Double check: must have at least one common letter
                if 'a' in line.lower() or 'e' in line.lower() or 'i' in line.lower():
                    resort_name = line
                    break
        
        if resort_name and price >= 500:
            stars = int(round(rating)) if rating else None
            deals.append({
                'resort': resort_name,
                'stars': stars,
                'price': price,
                'currency': 'CAD',
                'source': source
            })
    return deals

# ── 3. Insert into DB ─────────────────────────────────────────────
def insert_deals(conn, all_deals):
    cursor = conn.cursor()
    now = '2026-11-02T00:00:00Z'
    
    # Collect unique resort names for dedup
    seen_resorts = set()
    new_deals = []
    for d in all_deals:
        resort_key = d['resort'].lower()
        if resort_key in seen_resorts:
            print(f"  SKIP dup: {d['resort']}")
            continue
        seen_resorts.add(resort_key)
        new_deals.append(d)
    
    # Insert packages
    for d in new_deals:
        # Check if resort already exists
        cursor.execute('SELECT id FROM packages WHERE LOWER(resort) = ?', (d['resort'].lower(),))
        existing = cursor.fetchone()
        
        if existing:
            pkg_id = existing[0]  # id is first column
            # Update stars if missing
            if d.get('stars'):
                cursor.execute('UPDATE packages SET stars = ? WHERE id = ? AND stars IS NULL',
                              (d['stars'], pkg_id))
        else:
            cursor.execute('''
                INSERT INTO packages (resort, destination, board_type, nights, departure_origin, 
                                     source, source_url, stars)
                VALUES (?, ?, 'package', 7, NULL, ?, NULL, ?)
            ''', (d['resort'], d.get('destination', ''), d['source'], d['stars']))
            pkg_id = cursor.lastrowid
        
        # Insert deal
        cursor.execute('''
            INSERT INTO deals (package_id, price, currency, label, confidence, 
                              source_url, verified_at, verified_by, travel_window, 
                              terms, status, created_at)
            VALUES (?, ?, ?, 'anomaly', 2, ?, ?, 'browser_scrape', 
                    ?, '', 'active', ?)
        ''', (pkg_id, d['price'], d['currency'], f"https://{d['source']}",
              now, f"{d.get('nights', '7')} nights at {d['resort']}, {d['source']}",
              now))
    
    conn.commit()
    
    # Count new inserts
    count = len(new_deals)
    print(f"\nDB updated: {count} new packages/deals inserted")
    return count

# ── 4. Generate deals.json for frontend ───────────────────────────
def generate_deals_json(deals):
    """Create the frontend-facing deals.json with full deal objects"""
    # Load existing deals.json
    deals_json_path = os.path.join(DATA_DIR, 'deals.json')
    existing = []
    if os.path.exists(deals_json_path):
        with open(deals_json_path, 'r') as f:
            existing = json.load(f)
    
    # Dedup by resort name
    seen = set()
    unique = []
    for d in existing:
        key = d.get('resort') or d.get('label') or d.get('origin')
        if key and key.lower() not in seen:
            seen.add(key.lower())
            unique.append(d)
    
    # Add new browser-extracted deals
    for d in deals:
        key = d['resort'].lower()
        if key not in seen:
            seen.add(key)
            deal_obj = {
                'resort': d['resort'],
                'destination': d.get('destination', ''),
                'stars': d.get('stars'),
                'price': d['price'],
                'currency': d.get('currency', 'CAD'),
                'is_all_inclusive': True,
                'source': d['source'],
                'type': 'package'
            }
            unique.append(deal_obj)
    
    # Sort: packages by stars desc (None -> 0), then price asc; flights by price asc
    packages = [d for d in unique if d.get('type') == 'package']
    flights = [d for d in unique if d.get('type') != 'package']
    
    def pkg_sort_key(d):
        stars = d.get('stars') if d.get('stars') else 0
        return (-stars, d.get('price', 0))
    
    def flight_sort_key(d):
        return d.get('price', 0)
    
    packages.sort(key=pkg_sort_key)
    flights.sort(key=flight_sort_key)
    sorted_deals = packages + flights
    
    with open(deals_json_path, 'w') as f:
        json.dump(sorted_deals, f, indent=2)
    
    print(f"\ndeals.json updated: {len(sorted_deals)} total deals")
    return len(sorted_deals)

# ── Main ──────────────────────────────────────────────────────────
def main():
    print("=== Parsing browser-extracted deal data ===\n")
    
    # Read raw files
    redtag_text = read_file(os.path.join(DATA_DIR, 'redtag_raw.txt'))
    luxury_deals_text = read_file(os.path.join(DATA_DIR, 'luxuryescapes_deals_raw.txt'))
    luxury_home_text = read_file(os.path.join(DATA_DIR, 'luxuryescapes_home_raw.txt'))
    
    # Parse
    print("RedTag:")
    redtag_deals = parse_redtag(redtag_text)
    
    print("\nLuxury Escapes Deals:")
    luxury_deals = parse_luxury_escapes(luxury_deals_text)
    
    print("\nLuxury Escapes Home:")
    luxury_home_deals = parse_luxury_escapes(luxury_home_text)
    
    all_deals = redtag_deals + luxury_deals + luxury_home_deals
    print(f"\nTotal raw deals found: {len(all_deals)}")
    
    # Connect to DB
    conn = sqlite3.connect(DB_PATH)
    
    # Insert into DB
    insert_deals(conn, all_deals)
    
    # Generate frontend JSON
    total = generate_deals_json(all_deals)
    
    conn.close()
    print("\n=== DONE ===")

if __name__ == '__main__':
    main()
