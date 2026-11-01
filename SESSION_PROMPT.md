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
- Remote: **NOT YET CONFIGURED** (no GitHub/cloud remote)

## What's Pending

### 1. FREE HOSTING DEPLOYMENT (User wants it completely free)
Options (all free, all require a free account signup):
- **GitHub Pages** — Free (unlimited bandwidth), push to GitHub repo → auto-deploy. Easiest option.
- **Cloudflare Pages** — Free (100K requests/day), requires Cloudflare account. Fast CDN.
- **Netlify** — Free (100GB bandwidth/month), requires Netlify account. Drag-and-drop or connect GitHub.
- **Vercel** — Free tier (100GB), requires Vercel account. Good for static sites.

**User hasn't chosen yet — ask which platform.**

### 2. TWICE-DAILY DATA UPDATES
- Set up cron job or Windows scheduled task
- Run `python dealengine/check.py --mode full` twice daily (e.g., 6 AM and 6 PM)
- This regenerates `deals.json` with fresh scraped deals
- On deployment, site rebuilds from updated JSON
- For static hosting: need a build trigger (GitHub Actions, Cloudflare Worker, etc.)

### 3. CSS ENHANCEMENTS
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
cd C:\Users\omena\travel-deals\site
npm install   # if node_modules missing
npm run build  # should produce dist/ with 18 cards
```

### 2. Verify data
```bash
cd C:\Users\omena\travel-deals
python rebuild_deals.py   # should show 15 packages + 3 flights
```

### 3. Deploy to Free Hosting (ask user)
Once user chooses a platform:

**GitHub Pages (recommended):**
```bash
cd C:\Users\omena\travel-deals
# Create repo and push
gh repo create travel-deals-fare-enough --source=. --private=false
git remote add origin https://github.com/<username>/travel-deals-fare-enough.git
git push -u origin master
# Then enable GitHub Pages in repo Settings → Pages
```

**OR Cloudflare Pages:**
- Create free Cloudflare account
- Connect GitHub repo
- Build command: `cd site && npm install && npm run build`
- Output: `site/dist`
- Deploy

**OR Netlify:**
- Create free Netlify account
- Drag-and-drop the `site/dist` folder
- OR connect GitHub repo

### 4. Set Up Twice-Daily Updates
```bash
# Windows: Set up a scheduled task or cron
# Run: python C:\Users\omena\travel-deals\dealengine\check.py --mode full
# Schedule: twice daily (6 AM and 6 PM)
# Output: updates deals.json, triggers rebuild
```

### 5. Apply CSS Enhancements
- Modify `site/src/components/DealCard.astro` for card styling
- Modify `site/src/layouts/MainLayout.astro` for global styles
- Add custom CSS in `<style>` blocks
- Tweak `site/tailwind.config.mjs` for theme changes

## First Action After Boot
1. Read `PROJECT.md`, `TASKS.md`, `LOG.md`, and `CONTINUE.md`
2. State current phase and next task
3. **Ask user which FREE hosting platform they prefer** (GitHub Pages / Cloudflare Pages / Netlify / Vercel)
4. Set up the chosen platform and push the site
5. Verify the live URL is working
6. Set up twice-daily automated data updates (cron/scheduled task)
7. Apply any CSS enhancements requested by user
8. **Do NOT sit idle** — queue the asks and continue with non-blocked work

## Environment Notes
- Windows 11, RTX 5060 Ti 16GB, ~15.6GB RAM
- Ollama 0.40.11 at `http://localhost:11434`
- Model: `qwen2.5:3b` (downloaded, 1.9GB)
- Project venv at `.venv/` with Playwright + Chromium, httpx, BeautifulSoup
- `.env` in project root is gitignored — never commit or log secrets
- `*.db` files are gitignored
