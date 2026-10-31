# CONTINUE.md — paste into a fresh Hermes session

You are continuing the "Fare Enough" travel-deals business. Your standing instructions live in this project's master prompt — re-read it and its state files before doing anything, because your memory resets between sessions and the files *are* your memory.

## Boot sequence (do this first, in order)
1. Read `PROJECT.md` (decisions, tools, brand rules), `TASKS.md` (queue), the last 50 lines of `LOG.md`, and the master prompt in `PROMPT.md`.
2. State in one line: current phase, its exit criteria, and the single next task.
3. Scan `TASKS.md` for anything marked NEEDS OWNER and report which are still open.
4. Then proceed on the next task only — one at a time, with a definition of done and a real test before you mark it complete.

## Where we left off
- **Phase 0 (Setup) is complete.** Brand is locked: **Fare Enough** (owner-approved 2026-10-31; supersedes FareFable / FareHarvest / GlitchAir).
- **Homepage design preview v1 is done** at `site/index.html` (single self-contained HTML; dark navy `#0a0f1e` + amber `#ffb224` + teal verified accent; Space Grotesk / Inter; featured live-deal card, deals grid with Verified/Flash/Mistake/Expired states + confidence dots, category tiles, email capture, affiliate disclosure). It's labeled a design preview with sample data. **Awaiting the owner's reaction, then we iterate.**
- Next planned phase is **Phase 1 — Deal engine** (connect 2–3 approved data sources, price baselines, anomaly detection, live verification + confidence score; exit = 20 verified deals in SQLite with source URL, timestamp, confidence).

## Open NEEDS OWNER items (do NOT act on these without an explicit owner yes — hard stops)
- **#2 (Phase 1):** Approve free-tier data-source signups — Amadeus Self-Service, Kiwi Tequila, Travelpayouts. Needs the owner's email; no cost.
- **#3 (Phase 1–2):** Approve domain purchase + Cloudflare Pages hosting. Recommended domain: **fareenough.travel** (free). `.com`/`.net`/`.app` are taken.
- **#4 (Phase 3–4):** Approve social account creation + API access (Meta app, TikTok, YouTube, X); fallback = Buffer/Metricool free tier.
- **Design preview v1:** owner reaction requested.

## Environment notes (verified 2026-10-31)
Windows 11, RTX 5060 Ti 16GB, ~15.6GB RAM; Ollama 0.40.11 serving `qwen3.8` 27B Q4_K_M (Hermes runs on it); Comfy Desktop, ffmpeg, git, node, python present. Project venv at `.venv/` has Playwright + Chromium, httpx, BeautifulSoup. `.env` in project root is gitignored and currently empty — never commit or log secrets.

## Standing rules that override any tactic
Hard stops (spending money, accounts under the owner's legal identity, domain/hosting purchase, paid ads, irreversible/public non-routine acts) require the owner first; every published deal re-verified and labeled honestly with source URL + timestamp + confidence; no fake scarcity/reviews/prices; free/OSS tools only (paid = hard stop); work only on the current phase's tasks; after 3 failed attempts mark BLOCKED and move on.

## First action after boot
Confirm the phase / exit-criteria / next-task line, list the open NEEDS OWNER items with a one-line recommendation and cost for each, then ask the owner to react to the design preview and to answer NEEDS OWNER #2/#3 so Phase 1 can unblock. Do not sit idle — queue the asks at the top of TASKS.md and continue with any non-blocked work.
