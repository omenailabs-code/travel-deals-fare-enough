# TASKS.md — queue

## NEEDS OWNER
> Queued for owner reply 2026-10-31 (session 2) — #2 and #3 unblock Phase 1; reply in chat or edit this file.
1. ~~Brand approval~~ ✅ **Done — "Fare Enough"** (owner, 2026-10-31). Domain fareenough.travel free; .com/.net/.app taken. YT/X @fareenough appear taken.
2. (Phase 1) Approve free-tier data-source account signups: Amadeus Self-Service, Kiwi Tequila, Travelpayouts. Requires your email; no cost. **Rec: approve — needed before any real price data flows in; signups take ~10 min and use your email only.**
3. (Phase 1–2) Approve domain purchase + Cloudflare Pages hosting. **Cost check 2026-10-31:** .travel = ~$16 first year (promo) but ~$124–134/yr renewal (premium TLD); .co = ~$15–31/yr; .io = ~$35–60/yr. Cloudflare Pages = $0. **Rec: fareenough.travel for brand fit if the ~$130/yr renewal is acceptable, otherwise fareenough.co (cheapest, same name).**
4. (Phase 3–4) Approve social account creation + API access (Meta app, TikTok, YouTube, X); fallback route: Buffer/Metricool free tier.

## Phase 0 — Setup
- [x] Audit machine (2026-10-31, results in PROJECT.md)
- [x] Create repo + state files (PROJECT/TASKS/LOG/IDEAS + PROMPT.md master copy)
- [x] Tool inventory + install list
- [x] Project venv: Playwright + Chromium, httpx, BeautifulSoup
- [x] Three brand candidates with domain + handle availability (RDAP-verified)
- [x] Owner approves brand → **Fare Enough** (2026-10-31); Phase 1 may start (still needs NEEDS OWNER #2 for data-source signups)

## Phase 1 — Deal engine (blocked on NEEDS OWNER #2)
- [ ] Apply for free API tiers (owner-approved)
- [x] Engine scaffolding (2026-10-31): `dealengine/` — SQLite schema (routes/prices/deals/baseline_cache), anomaly detection (>=40% below median, below lowest-normal, extreme-outlier + wrong-currency patterns), confidence ladder (bootstrap caps, mistake cap 3, +1 live re-verify), `check` CLI (scan + baseline_cache refresh + deal writes, deduped), `seed` (synthetic-only, excluded from real data). Tests: 13/13 pass; seed→check demo correctly flagged 3/3 injected anomalies.
- [ ] Data-source adapters for approved APIs (Amadeus/Kiwi/Travelpayouts) plugging into `prices` — after #2
- [ ] Baseline price store in SQLite — bootstrap with 2–3 weeks of observation; early deals get lower confidence labels (see prompt-review note: 90-day baseline vs day one)
- [ ] Anomaly detection: >=40% below median, below lowest-normal by clear margin, known error-fare patterns
- [ ] Live verification step (exact dates, taxes, baggage, cancellation terms) + confidence score 1–5
- Exit: 20 verified deals stored, each with source URL, timestamp, confidence score

## Phase 2 — Website (blocked on NEEDS OWNER #3)
- [x] Homepage design preview v1 — `site/index.html` (2026-10-31): dark navy + amber identity, Space Grotesk/Inter, featured live-deal card, deals grid with Verified/Flash/Mistake/Expired states + confidence dots, category tiles, how-it-works, email capture, affiliate disclosure. Sample data, clearly labeled as design preview. Brand = Fare Enough (renamed 2026-10-31 after owner approval).
- [ ] Owner reacts to design preview v1 → iterate (we propose, owner reacts, we iterate)
- [ ] Astro/Next static site, Git repo, free hosting; deal template, route/destination pages, email capture, affiliate links + disclosure, privacy page
- [ ] Automation: verified deal -> DB write -> page build -> deploy -> sitemap ping, no manual step
- Exit: site live; new verified deal reaches the site with no manual step; Lighthouse > 90

## Phase 3 — Content engine
- [ ] ComfyUI workflows as named JSON; video template per deal type; captions (Whisper) + voiceover; assets.csv rights ledger
- Exit: 10 finished videos that pass Auditor + rights check

## Phase 4 — Social launch (blocked on NEEDS OWNER #4)
- [ ] Account setup (approved), API access, posting calendar per platform table
- Exit: 14 days of posts published on schedule on every connected platform

## Phase 5 — Monetization
- [ ] Affiliate program approvals, newsletter + lead magnet, premium alerts waitlist, sponsorship media kit
- Exit: >=2 revenue streams live and tracked per stream

## Phase 6 — Scale
- [ ] SEO page generation, more data sources, partnerships, small paid-ads test (owner approval + fixed budget)
- Exit: weekly growth in traffic, subscribers and revenue for 4 weeks running

## IDEAS
See IDEAS.md (parking lot; reviewed at weekly planning only).
