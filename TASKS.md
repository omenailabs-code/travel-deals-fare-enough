# TASKS.md — queue

## NEEDS OWNER
1. **Brand approval** — pick one: FareFable (recommended: domain + YT + X likely available), FareHarvest, GlitchAir.
2. (Phase 1) Approve free-tier data-source account signups: Amadeus Self-Service, Kiwi Tequila, Travelpayouts. Requires your email; no cost.
3. (Phase 1–2) Approve domain purchase + Cloudflare Pages hosting for the chosen name.
4. (Phase 3–4) Approve social account creation + API access (Meta app, TikTok, YouTube, X); fallback route: Buffer/Metricool free tier.

## Phase 0 — Setup
- [x] Audit machine (2026-10-31, results in PROJECT.md)
- [x] Create repo + state files (PROJECT/TASKS/LOG/IDEAS + PROMPT.md master copy)
- [x] Tool inventory + install list
- [x] Project venv: Playwright + Chromium, httpx, BeautifulSoup
- [x] Three brand candidates with domain + handle availability (RDAP-verified)
- [ ] Owner approves brand → then enter Phase 1

## Phase 1 — Deal engine (blocked on NEEDS OWNER #1, #2)
- [ ] Apply for free API tiers (owner-approved)
- [ ] Baseline price store in SQLite — bootstrap with 2–3 weeks of observation; early deals get lower confidence labels (see prompt-review note: 90-day baseline vs day one)
- [ ] Anomaly detection: >=40% below median, below lowest-normal by clear margin, known error-fare patterns
- [ ] Live verification step (exact dates, taxes, baggage, cancellation terms) + confidence score 1–5
- Exit: 20 verified deals stored, each with source URL, timestamp, confidence score

## Phase 2 — Website (blocked on NEEDS OWNER #3)
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
