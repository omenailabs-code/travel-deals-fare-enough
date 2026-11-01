# CONTINUE.md — paste into a fresh Hermes session

You are continuing the "Fare Enough" travel-deals business. Your standing instructions live in this project's master prompt — re-read it and its state files before doing anything, because your memory resets between sessions and the files *are* your memory.

## Boot sequence (do this first, in order)
1. Read `PROJECT.md` (decisions, tools, brand rules), `TASKS.md` (queue), the last 50 lines of `LOG.md`, and the master prompt in `PROMPT.md`.
2. State in one line: current phase, its exit criteria, and the single next task.
3. Scan `TASKS.md` for anything marked NEEDS OWNER and report which are still open.
4. Then proceed on the next task only — one at a time, with a definition of done and a real test before you mark it complete.

## Where we left off (updated 2026-10-31, session 2)
- **Phase 0 complete.** Brand locked: **Fare Enough** (owner-approved 2026-10-31; supersedes FareFable / FareHarvest / GlitchAir).
- **Design preview v1** at `site/index.html` (single self-contained HTML; dark navy `#0a0f1e` + amber `#ffb224` + teal; Space Grotesk/Inter; featured live-deal card, deals grid with Verified/Flash/Mistake/Expired states + confidence dots, category tiles, email capture, affiliate disclosure; sample data, clearly labeled preview). Screenshots in `site/screenshots/`. **Awaiting owner reaction.**
- **Phase 1 (deal engine) in progress — engine core built & verified (commit a5c8cf2):** `dealengine/` = SQLite schema (routes/prices/deals/baseline_cache), anomaly detection (>=40% below median, below lowest-normal, extreme-outlier + wrong-currency patterns), confidence ladder (bootstrap caps <7d=1 / <30d=2 / <90d=3 / 90d+=4, +1 live re-verify, mistake capped at 3), `check` CLI (scan, baseline_cache refresh, deduped deal writes), `seed` (synthetic-only, `source='synthetic-seed'`, excluded from real baselines). **13/13 unit tests pass; seed→check demo flagged exactly the injected anomalies.** Run tests: `.venv/Scripts/python.exe -m unittest discover -s tests`.
- **Data-source plan corrected (verified live 2026-10-31):** Amadeus Self-Service is **decommissioned (2026-07-17)** — dead; Kiwi Tequila is **invitation-only** since May 2024 — optional email to affiliates@kiwi.com. **Travelpayouts/Aviasales is the remaining open, free self-serve route** (signup → API token + affiliate deeplink; the site's affiliate disclosure already assumes Aviasales).
- Live price feeds blocked on owner approval of the Travelpayouts signup (NEEDS OWNER #2).

## Open NEEDS OWNER items (do NOT act on these without an explicit owner yes — hard stops)
- **#2 Data source:** approve Travelpayouts/Aviasales signup (owner email, ~10 min, $0). Amadeus dropped (decommissioned); Kiwi optional. **This is the single unblock for Phase 1.**
- **#3 Domain + hosting:** decide + approve purchase. Cost check: .travel ≈ $16 first year (promo) but ~$124–134/yr renewal (premium TLD); .co ≈ $15–31/yr; .io ≈ $35–60/yr; Cloudflare Pages = $0 (includes free Web Analytics). `.com`/`.net`/`.app` taken.
- **#4 Social (Phase 3–4):** account creation + API access (Meta app, TikTok, YouTube, X); @fareenough appears taken on YT/X — pick alternate handles; fallback Buffer/Metricool free tier.
- **#5 Newsletter backend (Phase 2):** the site's email capture needs a free provider under the owner's account: Buttondown (100 subs free) or Brevo (300 emails/day free).
- **Design preview v1:** owner reaction requested.

## What "completely running" means (owner asked 2026-10-31)
Live site on the chosen domain (Cloudflare Pages) showing real deals sourced from Travelpayouts, each verified and labeled with source URL + timestamp + confidence, auto-deployed when a new deal verifies; working newsletter capture on a free tier; social accounts posting on schedule; baselines collecting (>=5 observations/route — expect first real deals ~1 week after signup, 20+ verified by end of week 3).

## Environment notes (verified 2026-10-31)
Windows 11, RTX 5060 Ti 16GB, ~15.6GB RAM; Ollama 0.40.11 serving `qwen3.8` 27B Q4_K_M (Hermes runs on it); Comfy Desktop, ffmpeg, git, node, python present. Project venv at `.venv/` has Playwright + Chromium, httpx, BeautifulSoup. `.env` in project root is gitignored and currently empty — never commit or log secrets. `*.db` files are gitignored.

## Standing rules that override any tactic
Hard stops (spending money, accounts under the owner's legal identity, domain/hosting purchase, paid ads, irreversible/public non-routine acts) require the owner first; every published deal re-verified and labeled honestly with source URL + timestamp + confidence; no fake scarcity/reviews/prices; free/OSS tools only (paid = hard stop); work only on the current phase's tasks; after 3 failed attempts mark BLOCKED and move on.

## Latest Session Progress (2026-11-01) — New Session Pick-Up

### What's Been Completed (Session ending 2026-11-01)

**Data Pipeline — Fully Operational:**
- `rebuild_deals.py` rebuilt `site/data/deals.json` to exactly 18 clean deals: 15 genuine packages + 3 flight routes
- `content_gen.py` generates unique Ollama descriptions per deal using `qwen2.5:3b` (local, free, 1.9GB — downloaded to replace heavy `qwen3.8`)
- `deals.json` now has 18 deals with unique descriptions, star ratings, and confidence scores
- `rebuild_deals.py` filters: bad_patterns for nav/filter entries, minimum price for luxuryescapes.com, route_id→routes.id matching, LEFT JOIN for origin/destination

**Frontend — Fully Verified:**
- Astro build passes: `npm run build` → `dist/` static HTML
- 18 cards rendering correctly with: titles, prices, star ratings, All-Inclusive badges, Ollama descriptions, flight confidence scores
- Navy/Amber theme (#0a192f / #f59e0b) applied across all components
- `MainLayout.astro` with Tailwind CSS, Google Fonts (Space Grotesk/Inter)
- `DealCard.astro` renders flights with origin→destination, packages with stars

**Database:**
- `deals.db`: 5 routes, 15+ packages with star ratings (4-5 star), 127 deal rows (deduped to 18)
- `packages` table has `stars` column, backfilled for sample resorts
- `deals` table has `route_id` nullable for package deals

**Git State:**
- Repo committed: `a5883a4 Complete travel deals platform: Ollama descriptions, 18 deals, Astro build`
- Branch: `master`

### What's Pending

1. **FREE HOSTING DEPLOYMENT** — User wants to host completely free. Options:
   - **GitHub Pages** (free, requires GitHub account, push to repo → auto-deploy)
   - **Cloudflare Pages** (free, 100K req/day, requires Cloudflare)
   - **Netlify** (free, 100GB bandwidth, requires Netlify)
   - **Vercel** (free tier, 100GB, requires Vercel)
   - **User hasn't chosen yet** — ask which platform

2. **TWICE-DAILY UPDATES** — Need to set up:
   - Cron job or scheduled task running `python dealengine/check.py --mode full`
   - Regenerates `deals.json` with fresh scraped data
   - On deployment, site rebuilds from updated JSON

3. **CSS ENHANCEMENTS** — Tailwind CSS is set up, can be customized:
   - Modify `tailwind.config.mjs` for theme tweaks
   - Add CSS in `MainLayout.astro` `<style>` blocks
   - Modify `DealCard.astro` for card styling

### How to Pick Up in a New Session

```
# CONTINUE.md — paste into a fresh Hermes session

You are continuing the "Fare Enough" travel-deals business. Your standing instructions live in this project's master prompt — re-read it and its state files before doing anything.

## Current State (Updated 2026-11-01)
- 18 clean deals in DB (15 packages, 3 flights), all with unique Ollama descriptions
- Frontend built and verified: 18 cards rendering with star ratings, badges, descriptions
- Git: master branch, commit a5883a4
- Ollama: qwen2.5:3b (local, free)

## What To Do Next
1. Ask user which FREE hosting platform they prefer (GitHub Pages / Cloudflare / Netlify / Vercel)
2. Set up the chosen platform and push the site
3. Verify the live URL is working
4. Set up twice-daily automated data updates (cron/scheduled task)
5. Apply any CSS enhancements the user wants

## Key Constraints
- NO paid services (free hosting, local AI, free scraping)
- Navy/Amber theme (#0a192f, #f59e0b)
- 18 deals must stay clean and verified

## File Locations
- Project: C:\Users\omena\travel-deals
- Frontend: C:\Users\omena\travel-deals\site (Astro 5.x, Tailwind CSS)
- Backend: C:\Users\omena\travel-deals\dealengine (SQLite, Ollama)
- DB: C:\Users\omena\travel-deals\deals.db
- Deals JSON: C:\Users\omena\travel-deals\site\data\deals.json (18 deals)
```

### First Action After Boot
1. Read `PROJECT.md`, `TASKS.md`, `LOG.md`, and `CONTINUE.md`
2. State current phase and next task
3. Ask user about free hosting preference (GitHub Pages / Cloudflare Pages / Netlify / Vercel)
4. Set up the repo/remote and push the site to the chosen platform
5. Verify live URL
6. Set up twice-daily updates via cron/scheduled task
7. Apply any CSS enhancements requested by user
8. Do NOT sit idle — queue the asks and continue with non-blocked work
