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

## First action after boot
Confirm the phase / exit-criteria / next-task line, list the open NEEDS OWNER items with a one-line recommendation and cost for each, then ask the owner to react to the design preview and to answer NEEDS OWNER #2/#3. Do not sit idle — queue the asks at the top of TASKS.md and continue with non-blocked work (e.g., Travelpayouts adapter scaffold with mocked responses, deal→site template wiring, picking the 20-route baseline list).
