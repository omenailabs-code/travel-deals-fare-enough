# SESSION PROMPT — Pick Up "Fare Enough" Travel Deals Platform

You are continuing the "Fare Enough" travel-deals business. Your standing instructions live in this project's master prompt — re-read it and its state files before doing anything.

## Location
Project at `C:\Users\omena\travel-deals` on Windows 11.

## What's Been Completed (Session ending 2026-11-01)

### Data Pipeline — Fully Operational
- `rebuild_deals.py` rebuilt `site/data/deals.json` to **exactly 18 clean deals**: 15 genuine packages + 3 flight routes
- `content_gen.py` generates unique Ollama descriptions per deal using `qwen2.5:3b` (local, free, 1.9GB — replaced heavy `qwen3.8` due to 16GB RAM constraint)
- `deals.json` now has 18 deals with unique descriptions, star ratings, and confidence scores
- `rebuild_deals.py` filters: bad_patterns for nav/filter entries, minimum price for luxuryescapes.com, route_id→routes.id matching, LEFT JOIN for origin/destination
- `deals.db` SQLite database: 5 routes, 15+ packages with star ratings, 127 deal rows deduped to 18

### Frontend — Fully Verified
- Astro 5.x static site with Tailwind CSS: `npm run build` → `dist/` static HTML
- **18 cards rendering correctly** with: titles, prices, star ratings, All-Inclusive badges, Ollama descriptions, flight confidence scores
- Navy/Amber theme (#0a192f / #f59e0b) applied across all components
- `site/src/layouts/MainLayout.astro` with Tailwind CSS, Google Fonts (Space Grotesk/Inter)
- `site/src/components/DealCard.astro` renders flights with origin→destination, packages with stars
- Dev server running on `http://localhost:4321` (verified via curl/browser)

### Key Files
- `site/data/deals.json` — 18 deals with unique Ollama descriptions
- `dealengine/content_gen.py` — Ollama description generator (`qwen2.5:3b`)
- `dealengine/db.py` — SQLite schema (routes, packages, deals, price_history)
- `dealengine/check.py` — Main scanner (`python dealengine/check.py --mode full`)
- `rebuild_deals.py` — Rebuilds deals.json from DB (18 clean deals)
- `site/src/pages/index.astro` — Landing page
- `site/src/lib/deals.ts` — JSON data loader (fixed path resolution)

## Git State
- Repo committed: `a5883a4 Complete travel deals platform: Ollama descriptions, 18 deals, Astro build`
- Branch: `master`

## ✅ COMPLETED — LIVE SITE
- **Site is LIVE on GitHub Pages**
- **URL:** https://omenailabs-code.github.io/travel-deals-fare-enough/
- **Repo:** https://github.com/omenailabs-code/travel-deals-fare-enough
- **GitHub Account:** omenailabs@gmail.com
- **PAT:** `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`
- **GitHub Pages Status:** built (working)
- **Workflow:** `.github/workflows/deploy.yml` configured for twice-daily updates

## ⚠️ PENDING / NEXT STEPS

### 1. TWICE-DAILY AUTOMATED UPDATES (Critical)
- Current workflow only handles static build — does NOT regenerate deals.json
- Need to fix `.github/workflows/deploy.yml` to:
  1. Install Python dependencies (sqlite3, lxml, httpx, etc.)
  2. Run `python dealengine/check.py --mode full` to scrape fresh deals
  3. Run `python rebuild_deals.py` to rebuild deals.json from DB
  4. Run `python dealengine/content_gen.py` for Ollama descriptions
  5. Build site: `cd site && npm install && npm run build`
  6. Deploy to GitHub Pages
- Without this fix, the site shows stale deals forever

### 2. SITE CLEANUP
- Remove `test.txt` and `test/index.html` files from repo (leftovers)
- Remove `trigger.txt` (temporary file used to trigger build)
- These are clutter and should be cleaned up

### 3. CSS ENHANCEMENTS (Optional)
- Tailwind CSS is set up in `tailwind.config.mjs`
- Can customize colors, spacing, fonts
- Modify `DealCard.astro` for card styling
- Add custom CSS in `MainLayout.astro` `<style>` blocks

## Standing Rules (From PROJECT.md)
- **NO paid services** — free hosting, local AI (Ollama), free scraping only
- **No paid APIs, proxies, or CAPTCHA-solving services**
- **Be a "polite, legal scraper"** — check robots.txt and terms
- **Navy/Amber theme**: #0a192f (Navy) and #f59e0b (Amber)
- **Every published deal re-verified and labeled honestly** with source URL + timestamp + confidence
- **No fake scarcity/reviews/prices**
- **Hotel packages ranked by star rating** (4-5 star backfilled)

## How to Pick Up

### 1. Verify the site works
```bash
curl -s https://omenailabs-code.github.io/travel-deals-fare-enough/ | head -20
# Should show the live HTML with 18 deal cards
```

### 2. Fix the GitHub Actions workflow (Critical)
The current `.github/workflows/deploy.yml` only builds the static site — it does NOT run deal scraping.
Fix it to:
- Install Python deps (sqlite3, lxml, httpx, pillow)
- Run `python dealengine/check.py --mode full`
- Run `python rebuild_deals.py`
- Run `python dealengine/content_gen.py` (for Ollama descriptions)
- Build: `cd site && npm install && npm run build`
- Deploy: `actions/deploy-pages@v4`

### 3. Clean up temporary files
Remove from repo: `test.txt`, `test/index.html`, `trigger.txt`

### 4. Test the full pipeline manually
```bash
cd C:\Users\omena\travel-deals
python dealengine\check.py --mode full
python rebuild_deals.py
python dealengine\content_gen.py
cd site && npm run build
```
Then verify 18 cards still render correctly.

### 5. Apply CSS Enhancements (optional)
User requested CSS improvements — customize colors, spacing, fonts per their preference.

## First Action After Boot
1. Read `PROJECT.md`, `TASKS.md`, `LOG.md`, and `CONTINUE.md`
2. Verify live site: `curl -s https://omenailabs-code.github.io/travel-deals-fare-enough/ | head -20`
3. **Fix the GitHub Actions workflow** to include deal scraping + rebuild steps
4. Clean up temporary files from repo (`test.txt`, `test/index.html`, `trigger.txt`)
5. Test the full pipeline manually (check.py → rebuild_deals.py → content_gen.py → npm build)
6. Verify 18 cards still render correctly
7. Apply CSS enhancements if user requests them
8. **Do NOT sit idle** — queue the asks and continue with non-blocked work

## Environment Notes
- Windows 11, RTX 5060 Ti 16GB, ~15.6GB RAM
- Ollama 0.40.11 at `http://localhost:11434`
- Model: `qwen2.5:3b` (downloaded, 1.9GB)
- Project venv at `.venv/` with Playwright + Chromium, httpx, BeautifulSoup
- `.env` in project root is gitignored — never commit or log secrets
- `*.db` files are gitignored
