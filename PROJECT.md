# PROJECT.md — Travel Deals Business (state)

## Current state (rewrite every 20 steps)
- Phase 0 (Setup) nearly complete. Blocked on owner: brand approval (NEEDS OWNER #1 in TASKS.md).
- After brand approval: lock name, claim handles, enter Phase 1 (deal engine).

## Brand
Candidates checked 2026-10-31 (RDAP .com registry lookup; YouTube/X handle 404 = likely available):

| Name | .com | YouTube | X | Notes |
|---|---|---|---|---|
| FareFable | likely available (RDAP 404) | likely available | likely available | Recommended: brandable, deal-story vibe |
| FareHarvest | likely available (RDAP 404) | likely available | likely available | Literal, trustworthy |
| GlitchAir | likely available (RDAP 404) | appears taken (200) | appears taken (200) | Niche fit for mistake fares, weaker handle story |

Instagram/TikTok/Pinterest handle checks are unreliable via bot (login walls) — verify manually at account setup.
Decision: PENDING OWNER.

## Machine audit (2026-10-31)
- Windows 11 (build 26200), AMD64
- GPU: NVIDIA GeForce RTX 5060 Ti, 16 GB VRAM, driver 591.55
- RAM: ~15.6 GB | Disk C: 953 GB total, ~655 GB free
- Ollama 0.40.11 on localhost:11434: `qwen3.8:latest` = 27.3B Q4_K_M GGUF, llama.cpp runner, 262k context, vision + tools. **Hermes itself runs on this local model.** Also on disk: `VladimirGav/qwen3.8-27B-14GB-IQ4` (IQ4_XS).
- Comfy Desktop (ComfyUI) installed at %LOCALAPPDATA%\Programs\Comfy Desktop — confirm API port + model cache before first content engine run.
- git 2.53.0, node v26.12.1, npm 12.0.2, ffmpeg (7.x build n9.0.1), Python 3.14.9
- Playwright was missing → project venv created at `.venv/` with playwright + Chromium, httpx, beautifulsoup4 (deal research/verification stack).

## Tool plan (free/OSS only; anything paid = hard stop)
- Present: Ollama, Comfy Desktop, ffmpeg, git, node, python, Hermes browser
- Installed this session: Playwright + Chromium, httpx, BeautifulSoup (in `.venv/`)
- To verify at runtime: Comfy Desktop API port and generation models
- Data sources (Phase 1; all need owner-approved accounts = NEEDS OWNER): Amadeus Self-Service (free tier), Kiwi Tequila, Travelpayouts
- Hosting: Cloudflare Pages free tier; domain purchase = hard stop, queued

## KPIs
- Baselines TBD; numeric targets set at end of week 2 and recorded here (per prompt).
- Most important quality metric: % of published deals still bookable at 24 hours.

## Credentials
- `.env` in project root, gitignored, never committed or logged. Currently empty.
