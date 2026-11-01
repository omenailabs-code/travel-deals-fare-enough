# Fare Enough — Travel Deals Platform

A free travel deals platform that aggregates and verifies the best flight and vacation package deals.

## Features
- Real-time deal aggregation from multiple sources
- Star-rated hotel packages (4-5 star verified)
- Flight deals with confidence scores
- Unique AI-generated descriptions for each deal
- Navy/Amber themed UI with Tailwind CSS

## Setup

```bash
cd site
npm install
npm run build
```

## Twice-Daily Updates

The site uses GitHub Actions for automated deployments:
- Runs at 6 AM and 6 PM UTC (twice daily)
- Regenerates deals.json with fresh data
- Auto-builds and deploys to GitHub Pages

## Monetization

This site is designed for monetization:
- Add Google AdSense for display ads
- Use affiliate links (Travelpayouts, etc.)
- Sell premium deals or membership

## Tech Stack
- **Astro 5.x** — Static site framework
- **Tailwind CSS** — Navy (#0a192f) / Amber (#f59e0b) theme
- **Ollama qwen2.5:3b** — Free local AI for deal descriptions
- **SQLite** — Deal database
- **GitHub Pages** — Free hosting
