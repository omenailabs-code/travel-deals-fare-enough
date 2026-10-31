# LOG.md — history

## 2026-10-31
- Phase 0 kickoff. Machine audited: RTX 5060 Ti 16GB, ~15.6GB RAM, ~655GB disk free; Ollama 0.40.11 serving qwen3.8 27B Q4_K_M (Hermes runs on it); Comfy Desktop, ffmpeg, git, node, python present; Playwright missing.
- Created state files (PROJECT/TASKS/LOG/IDEAS) + copied master prompt to PROMPT.md; git init + first commit.
- Brand candidates checked via RDAP + handle lookups: FareFable (domain, YT, X likely available), FareHarvest (same), GlitchAir (domain available; YT/X appear taken).
- Created project venv (.venv) with Playwright + Chromium, httpx, BeautifulSoup for the deal research/verification stack.
- Prompt review notes: (1) 90-day baseline vs day-one Phase 1 exit is contradictory -> bootstrap baselines with 2–3 weeks, lower-confidence labels early; (2) Meta/TikTok API access needs app review (long lead) -> start early, Buffer/Metricool free tier as initial route; (3) all data-source and social accounts are hard stops -> queued as NEEDS OWNER.
- Built homepage design preview v1 at site/index.html (single self-contained HTML): dark navy #0a0f1e + amber #ffb224 + teal verified accents; Space Grotesk display / Inter body; sections = sticky header, hero with email capture + featured live-deal card (LIVE badge, delta below median, confidence dots), deals grid with filter chips and 4 deal states (Verified/Flash/Mistake may-be-cancelled/Expired-archived), category tiles, 3-step trust section, newsletter band, footer with affiliate disclosure. Verified: rendered in Chromium at 1264px and 390px, screenshots checked for layout defects — clean. Sample deals labeled "design preview" in ribbon + footer. Brand = placeholder FareFable pending owner approval.
